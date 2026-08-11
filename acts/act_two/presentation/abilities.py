import math

import pygame

from acts.act_two.abilities import get_warrior_cleave_cells
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


_CLEAVE_EFFECT_DURATION_MS = 460


def draw_act_two_ability_preview(
    screen,
    game_state,
    current_time: int,
) -> None:
    player = game_state.player
    direction = player.act_two.selected_ability_direction
    if (
        player.player_class != "warrior"
        or not player.directional_ability_aiming
        or direction is None
    ):
        return

    cells = get_warrior_cleave_cells(
        game_state.floor,
        direction[0],
        direction[1],
    )
    pulse = 0.5 + 0.5 * math.sin(current_time / 115)
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    for index, (column, row) in enumerate(cells):
        rectangle = pygame.Rect(
            MAP_OFFSET_X + column * TILE_SIZE,
            MAP_OFFSET_Y + row * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        center_cell = index == 0
        pygame.draw.rect(
            overlay,
            (
                170,
                28,
                34,
                round((82 if center_cell else 54) + pulse * 36),
            ),
            rectangle.inflate(-4, -4),
        )
        pygame.draw.rect(
            overlay,
            (255, 91, 72, round(175 + pulse * 70)),
            rectangle.inflate(-2, -2),
            width=3 if center_cell else 2,
        )
        pygame.draw.line(
            overlay,
            (255, 177, 113, round(115 + pulse * 90)),
            (
                rectangle.centerx - direction[0] * 7,
                rectangle.centery - direction[1] * 7,
            ),
            (
                rectangle.centerx + direction[0] * 8,
                rectangle.centery + direction[1] * 8,
            ),
            2,
        )
    screen.blit(overlay, (0, 0))


def draw_act_two_power_cleave_effect(
    screen,
    game_state,
    current_time: int,
) -> None:
    player = game_state.player
    started_at = player.act_two.ability_effect_started_at
    if player.player_class != "warrior" or started_at <= 0:
        return

    elapsed = current_time - started_at
    if not 0 <= elapsed < _CLEAVE_EFFECT_DURATION_MS:
        return

    progress = elapsed / _CLEAVE_EFFECT_DURATION_MS
    direction_x, direction_y = player.act_two.ability_effect_direction
    perpendicular_x, perpendicular_y = -direction_y, direction_x
    origin_x = (
        MAP_OFFSET_X
        + game_state.floor.player_column * TILE_SIZE
        + TILE_SIZE // 2
    )
    origin_y = (
        MAP_OFFSET_Y
        + game_state.floor.player_row * TILE_SIZE
        + TILE_SIZE // 2
    )
    sweep_progress = min(1.0, max(0.0, (progress - 0.08) / 0.56))
    fade = max(0.0, 1.0 - progress)
    reach = TILE_SIZE * (0.65 + sweep_progress * 0.65)
    half_width = TILE_SIZE * (0.35 + sweep_progress * 1.0)
    center_x = origin_x + direction_x * reach
    center_y = origin_y + direction_y * reach
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

    arc_points = []
    for point_index in range(13):
        position = -1.0 + point_index / 6
        across = position * half_width
        bow = (1.0 - position * position) * TILE_SIZE * 0.45
        arc_points.append(
            (
                round(
                    center_x
                    + perpendicular_x * across
                    + direction_x * bow
                ),
                round(
                    center_y
                    + perpendicular_y * across
                    + direction_y * bow
                ),
            )
        )

    pygame.draw.lines(
        overlay,
        (112, 9, 17, round(155 * fade)),
        False,
        arc_points,
        13,
    )
    pygame.draw.lines(
        overlay,
        (218, 35, 42, round(235 * fade)),
        False,
        arc_points,
        7,
    )
    pygame.draw.lines(
        overlay,
        (255, 133, 92, round(245 * fade)),
        False,
        arc_points,
        2,
    )

    for spark_index in range(7):
        spread = -1.0 + spark_index / 3
        spark_x = center_x + perpendicular_x * spread * half_width * 0.8
        spark_y = center_y + perpendicular_y * spread * half_width * 0.8
        spark_length = 5 + round(13 * sweep_progress)
        pygame.draw.line(
            overlay,
            (244, 68, 49, round(210 * fade)),
            (round(spark_x), round(spark_y)),
            (
                round(spark_x + direction_x * spark_length),
                round(spark_y + direction_y * spark_length),
            ),
            2,
        )
    screen.blit(overlay, (0, 0))
