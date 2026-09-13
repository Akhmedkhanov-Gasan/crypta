from functools import lru_cache
import math

import pygame

from acts.act_three.presentation.camera import (
    act_three_camera_position,
    act_three_centered_camera_position,
    act_three_world_view_size,
)
from acts.act_three.settings import (
    ACT_THREE_CURRENT_REVEAL_ALPHA,
    ACT_THREE_EXPLORED_FOG_ALPHA,
    ACT_THREE_FOG_INNER_RADIUS_TILES,
    ACT_THREE_FOG_OUTER_RADIUS_TILES,
    ACT_THREE_VISION_RADIUS_TILES,
)
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
    if player_position is not None:
        return act_three_centered_camera_position(
            floor,
            player_position,
        )

    return act_three_camera_position()


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
    floor.act_three_exploration_origins.add(origin)
    visible = set()
    radius_squared = ACT_THREE_VISION_RADIUS_TILES ** 2
    map_height = len(floor.map)
    map_width = len(floor.map[0])
    altar_cells = get_upgrade_altar_cells(floor)
    closed_doors = set()
    if floor.boss_door is not None and not floor.boss_fight_started:
        closed_doors.add(floor.boss_door)

    for row in range(map_height):
        for column in range(map_width):
            delta_x = column - origin[0]
            delta_y = row - origin[1]

            if (
                    delta_x * delta_x + delta_y * delta_y
                    > radius_squared
            ):
                continue

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


def _fog_shape_points(
    center,
    radius,
    distortion,
):
    points = []

    for point_index in range(96):
        angle = math.tau * point_index / 96
        variation = (
            math.sin(angle * 3 + 0.7) * 0.48
            + math.sin(angle * 7 + 1.9) * 0.31
            + math.sin(angle * 13 + 0.2) * 0.21
        )
        current_radius = max(
            1,
            radius + variation * distortion,
        )

        points.append(
            (
                round(
                    center[0]
                    + math.cos(angle) * current_radius
                ),
                round(
                    center[1]
                    + math.sin(angle) * current_radius
                ),
            )
        )

    return points


@lru_cache(maxsize=8)
def _fog_reveal_surface(inner_radius, outer_radius):
    distortion = max(
        6,
        round(ACT_THREE_TILE_SIZE * 0.18),
    )
    padding = outer_radius + distortion + 2
    size = padding * 2
    center = (padding, padding)

    reveal = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )

    radius_span = max(
        1,
        outer_radius - inner_radius,
    )

    for radius in range(
        outer_radius,
        inner_radius,
        -3,
    ):
        progress = (
            outer_radius - radius
        ) / radius_span
        progress = progress * progress * (3 - 2 * progress)
        alpha = round(
            ACT_THREE_CURRENT_REVEAL_ALPHA
            * progress
        )

        pygame.draw.polygon(
            reveal,
            (0, 0, 0, alpha),
            _fog_shape_points(
                center,
                radius,
                distortion,
            ),
        )

    pygame.draw.polygon(
        reveal,
        (
            0,
            0,
            0,
            ACT_THREE_CURRENT_REVEAL_ALPHA,
        ),
        _fog_shape_points(
            center,
            inner_radius,
            distortion,
        ),
    )

    return reveal


@lru_cache(maxsize=8)
def _explored_fog_surface(
    inner_radius,
    outer_radius,
    explored_alpha,
):
    size = outer_radius * 2 + 2
    center = (outer_radius + 1, outer_radius + 1)
    reveal = pygame.Surface((size, size), pygame.SRCALPHA)
    reveal.fill((0, 0, 0, 255))

    radius_span = max(1, outer_radius - inner_radius)

    for radius in range(outer_radius, inner_radius, -1):
        progress = (outer_radius - radius) / radius_span
        progress = progress * progress * (3 - 2 * progress)
        alpha = round(
            255 - (255 - explored_alpha) * progress
        )

        pygame.draw.circle(
            reveal,
            (0, 0, 0, alpha),
            center,
            radius,
        )

    pygame.draw.circle(
        reveal,
        (0, 0, 0, explored_alpha),
        center,
        inner_radius,
    )

    return reveal


def _draw_fog_of_war(
    view_surface,
    floor,
    camera_x,
    camera_y,
    player_position,
):
    fog = pygame.Surface(
        view_surface.get_size(),
        pygame.SRCALPHA,
    )
    fog.fill((0, 0, 0, 255))

    inner_radius = round(
        ACT_THREE_TILE_SIZE
        * ACT_THREE_FOG_INNER_RADIUS_TILES
    )
    outer_radius = round(
        ACT_THREE_TILE_SIZE
        * ACT_THREE_FOG_OUTER_RADIUS_TILES
    )

    explored_reveal = _explored_fog_surface(
        inner_radius,
        outer_radius,
        ACT_THREE_EXPLORED_FOG_ALPHA,
    )

    for column, row in floor.act_three_exploration_origins:
        center_x = (
            column * ACT_THREE_TILE_SIZE
            - camera_x
            + ACT_THREE_TILE_SIZE // 2
        )
        center_y = (
            row * ACT_THREE_TILE_SIZE
            - camera_y
            + ACT_THREE_TILE_SIZE // 2
        )

        fog.blit(
            explored_reveal,
            (
                center_x - explored_reveal.get_width() // 2,
                center_y - explored_reveal.get_height() // 2,
            ),
            special_flags=pygame.BLEND_RGBA_MIN,
        )

    current_reveal = _fog_reveal_surface(
        inner_radius,
        outer_radius,
    )
    player_center = (
        round(player_position[0] + ACT_THREE_TILE_SIZE / 2),
        round(player_position[1] + ACT_THREE_TILE_SIZE / 2),
    )

    fog.blit(
        current_reveal,
        (
            player_center[0] - current_reveal.get_width() // 2,
            player_center[1] - current_reveal.get_height() // 2,
        ),
        special_flags=pygame.BLEND_RGBA_SUB,
    )

    view_surface.blit(fog, (0, 0))
