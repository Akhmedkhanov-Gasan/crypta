import pygame

from acts.act_three.altar import get_upgrade_altar_cells
from presentation.layout import (
    ACT_THREE_TILE_SIZE,
    ACT_THREE_VIEW_HEIGHT,
    ACT_THREE_VIEW_WIDTH,
)

def _tile_is_floor(dungeon_map, column, row):
    return (
        0 <= row < len(dungeon_map)
        and 0 <= column < len(dungeon_map[0])
        and dungeon_map[row][column] != "#"
    )


def _floor_sprite_name(column, row, visual_seed):
    variation = (
        column * 73856093
        ^ row * 19349663
        ^ visual_seed
    ) % 100

    if variation < 12:
        return "floor_damp"
    if variation < 34:
        return "floor_cracked"
    return "floor_base"


def _wall_top_sprite_name(
    dungeon_map,
    column,
    row,
    visual_seed,
):
    floor_continues_left = _tile_is_floor(
        dungeon_map,
        column - 1,
        row + 1,
    )
    floor_continues_right = _tile_is_floor(
        dungeon_map,
        column + 1,
        row + 1,
    )

    if not floor_continues_left and floor_continues_right:
        return "wall_top_turn_left"
    if floor_continues_left and not floor_continues_right:
        return "wall_top_turn_right"

    return (
        "wall_top_variant"
        if (column * 13 + row * 29 + visual_seed) % 7 == 0
        else "wall_top"
    )


def _is_exposed_top_wall(dungeon_map, column, row):
    return (
        dungeon_map[row][column] == "#"
        and _tile_is_floor(dungeon_map, column, row + 1)
    )


def _draw_floor_boundaries(
    view_surface,
    assets,
    dungeon_map,
    column,
    row,
    tile_position,
):
    has_bottom_boundary = not _tile_is_floor(
        dungeon_map,
        column,
        row + 1,
    )
    has_left_boundary = not _tile_is_floor(
        dungeon_map,
        column - 1,
        row,
    )
    has_right_boundary = not _tile_is_floor(
        dungeon_map,
        column + 1,
        row,
    )

    if (
        has_bottom_boundary
        and has_left_boundary
        and not has_right_boundary
    ):
        boundary_names = ["wall_corner_bottom_left"]
    elif (
        has_bottom_boundary
        and has_right_boundary
        and not has_left_boundary
    ):
        boundary_names = ["wall_corner_bottom_right"]
    else:
        boundary_names = []

        if has_bottom_boundary:
            boundary_names.append("wall_bottom")
        if has_left_boundary:
            boundary_names.append("wall_left")
        if has_right_boundary:
            boundary_names.append("wall_right")

    for boundary_name in boundary_names:
        view_surface.blit(
            assets[boundary_name],
            tile_position,
        )


def _top_void_corner_sprite_names(
    dungeon_map,
    column,
    row,
):
    if (
        not _tile_is_floor(dungeon_map, column, row)
        or _tile_is_floor(dungeon_map, column, row + 1)
    ):
        return ()

    floor_continues_below_left = _tile_is_floor(
        dungeon_map,
        column - 1,
        row + 1,
    )
    floor_continues_below_right = _tile_is_floor(
        dungeon_map,
        column + 1,
        row + 1,
    )

    if (
        floor_continues_below_left
        and floor_continues_below_right
    ):
        return (
            "wall_corner_top_left",
            "wall_corner_top_right",
        )
    if (
        floor_continues_below_left
        and not floor_continues_below_right
    ):
        return ("wall_corner_top_left",)
    if (
        not floor_continues_below_left
        and floor_continues_below_right
    ):
        return ("wall_corner_top_right",)
    return ()


def _camera_position(floor, player_position=None):
    world_width = len(floor.map[0]) * ACT_THREE_TILE_SIZE
    world_height = len(floor.map) * ACT_THREE_TILE_SIZE
    player_column, player_row = (
        (floor.player_column, floor.player_row)
        if player_position is None
        else player_position
    )
    target_x = (
        player_column * ACT_THREE_TILE_SIZE
        + ACT_THREE_TILE_SIZE // 2
        - ACT_THREE_VIEW_WIDTH // 2
    )
    target_y = (
        player_row * ACT_THREE_TILE_SIZE
        + ACT_THREE_TILE_SIZE // 2
        - ACT_THREE_VIEW_HEIGHT // 2
    )

    return (
        max(
            0,
            min(target_x, world_width - ACT_THREE_VIEW_WIDTH),
        ),
        max(
            0,
            min(target_y, world_height - ACT_THREE_VIEW_HEIGHT),
        ),
    )


def _view_position(column, row, camera_x, camera_y):
    return (
        column * ACT_THREE_TILE_SIZE - camera_x,
        row * ACT_THREE_TILE_SIZE - camera_y,
    )


def _line_of_sight(
    dungeon_map,
    origin,
    target,
    blockers=(),
    transparent_cells=(),
):
    """Return whether a grid ray can reach target without crossing a wall."""
    x0, y0 = origin
    x1, y1 = target
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    step_x = 1 if x0 < x1 else -1
    step_y = 1 if y0 < y1 else -1
    error = dx - dy

    while (x0, y0) != (x1, y1):
        if (
            (x0, y0) != origin
            and (
                (
                    dungeon_map[y0][x0] == "#"
                    and (x0, y0) not in transparent_cells
                )
                or (x0, y0) in blockers
            )
        ):
            return False
        doubled_error = error * 2
        if doubled_error > -dy:
            error -= dy
            x0 += step_x
        if doubled_error < dx:
            error += dx
            y0 += step_y

    return True


def _get_act_three_visibility(floor):
    """Calculate current sight and remember cells seen earlier."""
    origin = (floor.player_column, floor.player_row)
    visible = set()
    map_height = len(floor.map)
    map_width = len(floor.map[0])
    altar_cells = get_upgrade_altar_cells(floor)
    closed_doors = set()
    if floor.boss_door is not None and not floor.boss_fight_started:
        closed_doors.add(floor.boss_door)

    for row in range(map_height):
        for column in range(map_width):
            if _line_of_sight(
                floor.map,
                origin,
                (column, row),
                closed_doors,
                altar_cells,
            ):
                visible.add((column, row))

    if visible.intersection(altar_cells):
        visible.update(altar_cells)

    floor.explored_cells.update(visible)
    floor.visible_cells = visible
    return visible


def _draw_fog_of_war(
    view_surface,
    floor,
    camera_x,
    camera_y,
):
    visible = floor.visible_cells
    fog = pygame.Surface(
        (ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT),
        pygame.SRCALPHA,
    )
    # Keep the non-playable area visibly textured when the fixed logical
    # viewport is wider than a map. Unexplored map cells remain fully hidden.
    fog.fill((0, 0, 0, 208))

    for row in range(len(floor.map)):
        for column in range(len(floor.map[0])):
            position = (column, row)
            if position in visible:
                pygame.draw.rect(
                    fog,
                    (0, 0, 0, 0),
                    (*_view_position(column, row, camera_x, camera_y),
                     ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
                )
            elif position in floor.explored_cells:
                pygame.draw.rect(
                    fog,
                    (0, 0, 0, 178),
                    (*_view_position(column, row, camera_x, camera_y),
                     ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
                )
            else:
                pygame.draw.rect(
                    fog,
                    (0, 0, 0, 255),
                    (*_view_position(column, row, camera_x, camera_y),
                     ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
                )

    view_surface.blit(fog, (0, 0))
