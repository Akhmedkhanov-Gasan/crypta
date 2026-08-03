"""Load hand-authored Tiled maps into the Act III floor contract."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from enemies import ENEMY_TYPES


def _csv_layer(layer, width, height):
    data = layer.find("data")
    if data is None or data.get("encoding") != "csv":
        raise ValueError("TMX layers must use CSV encoding")
    values = [
        int(value.strip())
        for value in (data.text or "").split(",")
        if value.strip()
    ]
    return [values[row * width : (row + 1) * width] for row in range(height)]


def _entity_name_from_text(name):
    return re.sub(r"[^a-z0-9_]", "_", name.lower()).strip("_")


def _entity_name(obj):
    return _entity_name_from_text(obj.get("name", ""))


def _position(obj, tile_size):
    return (
        int(float(obj.get("x", 0)) // tile_size),
        int(float(obj.get("y", 0)) // tile_size),
    )


def _connector_direction(
    name,
    position,
    width,
    height,
    explicit_direction,
):
    if explicit_direction:
        return explicit_direction.lower()

    normalized_name = _entity_name_from_text(name)
    for direction in ("north", "south", "east", "west"):
        if direction in normalized_name.split("_"):
            return direction

    column, row = position
    if row == 0:
        return "north"
    if row == height - 1:
        return "south"
    if column == 0:
        return "west"
    if column == width - 1:
        return "east"
    return ""


def _connector_width(obj, direction, properties, tile_size):
    if properties.get("width"):
        return max(1, int(properties["width"]))

    object_width = float(obj.get("width", 0))
    object_height = float(obj.get("height", 0))
    pixel_span = (
        object_width
        if direction in ("north", "south")
        else object_height
    )
    return max(1, round(pixel_span / tile_size))


def _blocked(column, row, rectangles, tile_size):
    left = column * tile_size
    top = row * tile_size
    right = left + tile_size
    bottom = top + tile_size
    return any(
        left < x + width
        and right > x
        and top < y + height
        and bottom > y
        for x, y, width, height in rectangles
    )


def _edge(first, second):
    return tuple(sorted((first, second)))


def _overlaps(start, end, other_start, other_end):
    return start < other_end and end > other_start


def _barrier_edges(rectangles, width, height, tile_size):
    """Convert thin Tiled rectangles into forbidden grid transitions."""
    edges = set()

    snap_tolerance = tile_size / 4
    for x, y, rectangle_width, rectangle_height in rectangles:
        if rectangle_height >= rectangle_width:
            center_x = x + rectangle_width / 2
            boundary_column = round(center_x / tile_size)
            boundary_x = boundary_column * tile_size
            if (
                0 <= boundary_column <= width
                and abs(center_x - boundary_x) <= snap_tolerance
            ):
                for row in range(height):
                    if _overlaps(
                        row * tile_size,
                        (row + 1) * tile_size,
                        y,
                        y + rectangle_height,
                    ):
                        edges.add(
                            _edge(
                                (boundary_column - 1, row),
                                (boundary_column, row),
                            )
                        )

        if rectangle_width >= rectangle_height:
            center_y = y + rectangle_height / 2
            boundary_row = round(center_y / tile_size)
            boundary_y = boundary_row * tile_size
            if (
                0 <= boundary_row <= height
                and abs(center_y - boundary_y) <= snap_tolerance
            ):
                for column in range(width):
                    if _overlaps(
                        column * tile_size,
                        (column + 1) * tile_size,
                        x,
                        x + rectangle_width,
                    ):
                        edges.add(
                            _edge(
                                (column, boundary_row - 1),
                                (column, boundary_row),
                            )
                        )

    return edges


def load_tmx_floor(path):
    path = Path(path)
    root = ET.parse(path).getroot()
    width = int(root.get("width", 0))
    height = int(root.get("height", 0))
    tile_size = int(root.get("tilewidth", 32))
    layers = {
        layer.get("name", ""): _csv_layer(layer, width, height)
        for layer in root.findall("layer")
    }
    blocked_rectangles = []
    barrier_rectangles = []
    entities = []
    connectors = []
    for group in root.findall("objectgroup"):
        group_name = group.get("name", "").lower()
        for obj in group.findall("object"):
            if group_name in ("blocked", "collision"):
                blocked_rectangles.append(
                    (
                        float(obj.get("x", 0)),
                        float(obj.get("y", 0)),
                        float(obj.get("width", 0)),
                        float(obj.get("height", 0)),
                    )
                )
            elif group_name == "barriers":
                barrier_rectangles.append(
                    (
                        float(obj.get("x", 0)),
                        float(obj.get("y", 0)),
                        float(obj.get("width", 0)),
                        float(obj.get("height", 0)),
                    )
                )
            elif group_name == "entities":
                properties = {
                    prop.get("name", ""): prop.get("value", "")
                    for prop in obj.findall("./properties/property")
                }
                entities.append(
                    (_entity_name(obj), _position(obj, tile_size), properties)
                )
            elif group_name == "connectors":
                properties = {
                    prop.get("name", ""): prop.get("value", "")
                    for prop in obj.findall("./properties/property")
                }
                position = _position(obj, tile_size)
                direction = _connector_direction(
                    obj.get("name", ""),
                    position,
                    width,
                    height,
                    properties.get("direction", ""),
                )
                connectors.append(
                    {
                        "name": _entity_name(obj),
                        "position": position,
                        "direction": direction,
                        "width": _connector_width(
                            obj,
                            direction,
                            properties,
                            tile_size,
                        ),
                    }
                )

    blocked_layer = layers.get("Blocked", [])
    dungeon_map = [
        [
            (
                "#"
                if (
                    _blocked(
                        column,
                        row,
                        blocked_rectangles,
                        tile_size,
                    )
                    or (
                        row < len(blocked_layer)
                        and column < len(blocked_layer[row])
                        and blocked_layer[row][column] != 0
                    )
                )
                else "."
            )
            for column in range(width)
        ]
        for row in range(height)
    ]
    barriers = _barrier_edges(
        barrier_rectangles,
        width,
        height,
        tile_size,
    )
    by_name = {}
    for name, position, properties in entities:
        by_name.setdefault(name, []).append((position, properties))

    upgrade_altar_markers = by_name.get("upgrade_altar", [])
    upgrade_altar = (
        upgrade_altar_markers[0][0]
        if upgrade_altar_markers
        else None
    )
    if upgrade_altar is not None:
        altar_column, altar_row = upgrade_altar
        for row in range(altar_row, altar_row + 2):
            for column in range(altar_column, altar_column + 2):
                if 0 <= row < height and 0 <= column < width:
                    dungeon_map[row][column] = "#"

    player_markers = (
        by_name.get("player_spawn")
        or by_name.get("spawn")
        or [((1, 1), {})]
    )
    player_start = player_markers[0][0]
    fallback_stairs = next(
        (
            (column, row)
            for row in range(height - 1, -1, -1)
            for column in range(width - 1, -1, -1)
            if dungeon_map[row][column] == "."
        ),
        (1, 1),
    )
    stairs = by_name.get("stairs", [(fallback_stairs, {})])[0][0]
    chests = [
        {"position": position, "contains": props.get("contains", "gold")}
        for position, props in by_name.get("chest", [])
    ]
    torches = [position for position, _ in by_name.get("torch", [])]
    enemies = []
    for name, markers in by_name.items():
        if name != "enemy" and name not in ENEMY_TYPES:
            continue
        for position, props in markers:
            enemies.append(
                {
                    "position": position,
                    "type": (
                        props.get("enemy_type", "goblin")
                        if name == "enemy"
                        else name
                    ),
                    "boss_group": False,
                }
            )
    potions = [position for position, _ in by_name.get("potion", [])]
    return {
        "map": ["".join(row) for row in dungeon_map],
        "player_start": player_start,
        "enemies": enemies,
        "chests": chests,
        "potions": potions,
        "torches": torches,
        "upgrade_altar": upgrade_altar,
        "tile_layers": layers,
        "barriers": barriers,
        "connectors": connectors,
        "width": width,
        "height": height,
        "tile_size": tile_size,
        "source_path": str(path),
        "stairs": stairs,
        "boss_door": None,
        "boss_room": None,
        "boss_columns": [],
        "boss_emitters": [],
        "seal_boss_door_during_fight": False,
        "visual_seed": 1,
    }
