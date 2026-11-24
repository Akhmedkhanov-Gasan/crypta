from functools import lru_cache
from pathlib import Path

import resource_store as resources


MAP_DIRECTORY = Path(__file__).resolve().parents[2] / "assets/maps/act_3"
ENVIRONMENT_OBJECTS_TILESET_PATH = (
    MAP_DIRECTORY / "EnvironmentObjects" / "environment_objects.tsx"
).resolve()
TILED_GID_MASK = 0x0FFFFFFF


def tileset_tile_count(root, atlas_size=None):
    count = max(
        int(root.get("tilecount", 0)),
        max((int(tile.get("id", 0)) + 1 for tile in root.findall("tile")), default=0),
    )
    if atlas_size is not None:
        width, height = atlas_size
        tile_width = int(root.get("tilewidth", 64))
        tile_height = int(root.get("tileheight", 64))
        margin = int(root.get("margin", 0))
        spacing = int(root.get("spacing", 0))
        columns = max(0, (width - margin * 2 + spacing) // (tile_width + spacing))
        rows = max(0, (height - margin * 2 + spacing) // (tile_height + spacing))
        count = max(count, columns * rows)
    return count


@lru_cache(maxsize=1)
def tileset_catalog():
    paths = sorted([
        *resources.glob_resources(MAP_DIRECTORY, "*.tsx"),
        *resources.glob_resources(MAP_DIRECTORY / "torches", "*.tsx"),
    ])
    paths.append(ENVIRONMENT_OBJECTS_TILESET_PATH)
    paths.append(MAP_DIRECTORY / "EnvironmentObjects" / "lantern_warden_room_props" / "lantern_warden_room_props.tsx")
    paths.extend(sorted(resources.glob_resources(MAP_DIRECTORY / "runes", "*.tsx")))
    catalog = {}
    first_gid = 1
    for path in paths:
        root = resources.load_xml(path).getroot()
        image = root.find("image")
        atlas_size = None
        if image is not None and image.get("source"):
            atlas_size = resources.load_image(path.parent / image.get("source")).get_size()
        count = tileset_tile_count(root, atlas_size)
        if count <= 0:
            raise ValueError(f"Tileset has no tiles: {path}")
        catalog[path.resolve()] = (first_gid, root)
        first_gid += count
    return catalog


def normalize_tile_layers(layers, map_root, map_path):
    catalog = tileset_catalog()
    used_tile_ids = {
        gid & TILED_GID_MASK
        for layer in layers.values()
        for row in layer
        for gid in row
        if gid
    }
    tilesets = sorted(map_root.findall("tileset"), key=lambda node: int(node.get("firstgid", 1)))
    ranges = []
    for index, node in enumerate(tilesets):
        source = node.get("source")
        if not source:
            raise ValueError(f"Act Three requires external tilesets: {map_path}")
        path = (map_path.parent / source).resolve()
        if path not in catalog:
            first_gid = int(node.get("firstgid", 1))
            next_gid = int(tilesets[index + 1].get("firstgid", 1)) if index + 1 < len(tilesets) else float("inf")
            if not any(first_gid <= tile_id < next_gid for tile_id in used_tile_ids):
                continue
            raise ValueError(f"Tileset must be in the Act Three map catalog: {path}")
        ranges.append((int(node.get("firstgid", 1)), catalog[path][0]))
    ranges.sort(reverse=True)
    for layer in layers.values():
        for row in layer:
            for index, gid in enumerate(row):
                if not gid:
                    continue
                flags = gid & ~TILED_GID_MASK
                tile_id = gid & TILED_GID_MASK
                for source_first, target_first in ranges:
                    if tile_id >= source_first:
                        row[index] = flags | (target_first + tile_id - source_first)
                        break
                else:
                    raise ValueError(f"Invalid tile ID {tile_id}: {map_path}")
