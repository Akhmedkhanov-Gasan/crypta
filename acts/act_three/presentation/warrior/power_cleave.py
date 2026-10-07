import math

import pygame

from acts.act_two.abilities import (
    get_warrior_aftershock_cells,
    get_warrior_cleave_cells,
)


def _cleave_colors(subclass):
    if subclass == "paladin":
        return (
            (47, 26, 59, 112),
            (191, 150, 77, 220),
            (255, 226, 157, 245),
        )

    return (
        (92, 17, 20, 112),
        (218, 53, 42, 220),
        (255, 166, 91, 245),
    )


def _cell_rectangle(
    column,
    row,
    camera_x,
    camera_y,
    tile_size,
):
    return pygame.Rect(
        column * tile_size - camera_x,
        row * tile_size - camera_y,
        tile_size,
        tile_size,
    )


def draw_power_cleave_targeting(
    surface,
    game_state,
    camera_x,
    camera_y,
    current_time,
    tile_size,
):
    player = game_state.player
    direction = (
        player.act_two.selected_ability_direction
    )

    if (
        player.player_class != "warrior"
        or player.subclass not in ("berserker", "paladin")
        or not player.directional_ability_aiming
        or direction is None
    ):
        return

    cells = get_warrior_cleave_cells(
        game_state.floor,
        direction[0],
        direction[1],
    )
    if not cells:
        return

    aftershock_cells = (
        get_warrior_aftershock_cells(
            game_state.floor,
            direction[0],
            direction[1],
        )
        if player.selected_rune_id == "rune_of_aftershock"
        else []
    )

    fill_color, border_color, light_color = (
        _cleave_colors(player.subclass)
    )
    pulse = (
        0.5
        + 0.5 * math.sin(current_time * 0.011)
    )
    overlay = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )

    player_center = (
        game_state.floor.player_column * tile_size
        - camera_x
        + tile_size // 2,
        game_state.floor.player_row * tile_size
        - camera_y
        + tile_size // 2,
    )
    direction_x, direction_y = direction
    perpendicular_x = -direction_y
    perpendicular_y = direction_x

    for index, (column, row) in enumerate(cells):
        rectangle = _cell_rectangle(
            column,
            row,
            camera_x,
            camera_y,
            tile_size,
        )
        center_cell = index == 0
        inset = 4 if center_cell else 7

        pygame.draw.rect(
            overlay,
            (
                fill_color[0],
                fill_color[1],
                fill_color[2],
                round(
                    fill_color[3]
                    + pulse * 34
                ),
            ),
            rectangle.inflate(-inset, -inset),
            border_radius=max(3, tile_size // 12),
        )
        pygame.draw.rect(
            overlay,
            (
                border_color[0],
                border_color[1],
                border_color[2],
                round(
                    border_color[3]
                    + pulse * 25
                ),
            ),
            rectangle.inflate(-3, -3),
            width=3 if center_cell else 2,
            border_radius=max(3, tile_size // 12),
        )

        chevron_center = rectangle.center
        chevron_back = (
            round(
                chevron_center[0]
                - direction_x * tile_size * 0.14
            ),
            round(
                chevron_center[1]
                - direction_y * tile_size * 0.14
            ),
        )
        chevron_left = (
            round(
                chevron_back[0]
                + perpendicular_x * tile_size * 0.12
            ),
            round(
                chevron_back[1]
                + perpendicular_y * tile_size * 0.12
            ),
        )
        chevron_right = (
            round(
                chevron_back[0]
                - perpendicular_x * tile_size * 0.12
            ),
            round(
                chevron_back[1]
                - perpendicular_y * tile_size * 0.12
            ),
        )
        chevron_tip = (
            round(
                chevron_center[0]
                + direction_x * tile_size * 0.17
            ),
            round(
                chevron_center[1]
                + direction_y * tile_size * 0.17
            ),
        )

        pygame.draw.lines(
            overlay,
            light_color,
            False,
            (
                chevron_left,
                chevron_tip,
                chevron_right,
            ),
            max(2, tile_size // 22),
        )

    center_distance = tile_size * (
        0.88 + pulse * 0.06
    )
    arc_center = (
        player_center[0]
        + direction_x * center_distance,
        player_center[1]
        + direction_y * center_distance,
    )
    arc_points = []

    for index in range(17):
        position = -1 + index / 8
        across = position * tile_size * 1.16
        forward_bow = (
            1 - position * position
        ) * tile_size * 0.27
        arc_points.append(
            (
                round(
                    arc_center[0]
                    + perpendicular_x * across
                    + direction_x * forward_bow
                ),
                round(
                    arc_center[1]
                    + perpendicular_y * across
                    + direction_y * forward_bow
                ),
            )
        )

    pygame.draw.lines(
        overlay,
        (
            fill_color[0],
            fill_color[1],
            fill_color[2],
            round(150 + pulse * 35),
        ),
        False,
        arc_points,
        max(7, tile_size // 7),
    )
    pygame.draw.lines(
        overlay,
        (
            border_color[0],
            border_color[1],
            border_color[2],
            round(210 + pulse * 35),
        ),
        False,
        arc_points,
        max(3, tile_size // 13),
    )
    pygame.draw.lines(
        overlay,
        light_color,
        False,
        arc_points,
        max(1, tile_size // 32),
    )

    for column, row in aftershock_cells:
        rectangle = _cell_rectangle(
            column,
            row,
            camera_x,
            camera_y,
            tile_size,
        )
        pygame.draw.rect(
            overlay,
            (
                border_color[0],
                border_color[1],
                border_color[2],
                round(42 + pulse * 28),
            ),
            rectangle.inflate(-9, -9),
            border_radius=max(3, tile_size // 12),
        )
        pygame.draw.rect(
            overlay,
            (
                light_color[0],
                light_color[1],
                light_color[2],
                round(125 + pulse * 65),
            ),
            rectangle.inflate(-6, -6),
            width=2,
            border_radius=max(3, tile_size // 12),
        )

    surface.blit(overlay, (0, 0))
