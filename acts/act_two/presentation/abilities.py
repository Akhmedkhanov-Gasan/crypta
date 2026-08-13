import math

import pygame

from acts.act_two.abilities import (
    get_mage_arcane_cells,
    get_warrior_cleave_cells,
)
from logic import get_enemy_occupied_positions
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


_CLEAVE_EFFECT_DURATION_MS = 460
_ARCANE_BURST_EFFECT_DURATION_MS = 620


def _cell_center(column, row):
    return (
        MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2,
    )


def _draw_mage_preview(
    screen,
    game_state,
    direction,
    current_time,
):
    cells = get_mage_arcane_cells(
        game_state.floor,
        direction[0],
        direction[1],
    )
    pulse = 0.5 + 0.5 * math.sin(current_time / 105)
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    player_center = _cell_center(
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    targeted_positions = {
        position
        for enemy in game_state.floor.enemies
        if enemy.health > 0
        for position in get_enemy_occupied_positions(enemy)
    }

    if cells:
        centers = [_cell_center(column, row) for column, row in cells]
        pygame.draw.line(
            overlay,
            (33, 88, 178, round(70 + pulse * 34)),
            player_center,
            centers[-1],
            9,
        )
        pygame.draw.line(
            overlay,
            (92, 184, 255, round(170 + pulse * 65)),
            player_center,
            centers[-1],
            2,
        )
        for index, ((column, row), center) in enumerate(
            zip(cells, centers)
        ):
            rectangle = pygame.Rect(
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
            )
            pygame.draw.rect(
                overlay,
                (23, 68, 151, round(42 + pulse * 28)),
                rectangle.inflate(-4, -4),
            )
            pygame.draw.rect(
                overlay,
                (79, 169, 248, round(115 + pulse * 82)),
                rectangle.inflate(-2, -2),
                width=2,
            )
            chevron_offset = round(
                ((current_time / 95 + index * 6) % 12) - 6
            )
            chevron_center = (
                center[0] + direction[0] * chevron_offset,
                center[1] + direction[1] * chevron_offset,
            )
            perpendicular = (-direction[1], direction[0])
            chevron_tip = (
                chevron_center[0] + direction[0] * 6,
                chevron_center[1] + direction[1] * 6,
            )
            chevron_back = (
                chevron_center[0] - direction[0] * 4,
                chevron_center[1] - direction[1] * 4,
            )
            pygame.draw.lines(
                overlay,
                (174, 226, 255, round(155 + pulse * 90)),
                False,
                (
                    (
                        chevron_back[0] + perpendicular[0] * 4,
                        chevron_back[1] + perpendicular[1] * 4,
                    ),
                    chevron_tip,
                    (
                        chevron_back[0] - perpendicular[0] * 4,
                        chevron_back[1] - perpendicular[1] * 4,
                    ),
                ),
                2,
            )
            if (column, row) in targeted_positions:
                pygame.draw.rect(
                    overlay,
                    (211, 244, 255, round(205 + pulse * 50)),
                    rectangle.inflate(-5, -5),
                    width=3,
                )

        endpoint = centers[-1]
        endpoint_radius = round(8 + pulse * 2)
        pygame.draw.polygon(
            overlay,
            (183, 232, 255, round(205 + pulse * 50)),
            (
                (endpoint[0], endpoint[1] - endpoint_radius),
                (endpoint[0] + endpoint_radius, endpoint[1]),
                (endpoint[0], endpoint[1] + endpoint_radius),
                (endpoint[0] - endpoint_radius, endpoint[1]),
            ),
            width=2,
        )
    else:
        blocked_center = (
            player_center[0] + direction[0] * TILE_SIZE,
            player_center[1] + direction[1] * TILE_SIZE,
        )
        radius = round(8 + pulse * 2)
        pygame.draw.circle(
            overlay,
            (64, 108, 160, round(120 + pulse * 80)),
            blocked_center,
            radius,
            width=2,
        )
        pygame.draw.line(
            overlay,
            (166, 203, 230, round(160 + pulse * 80)),
            (blocked_center[0] - 5, blocked_center[1] - 5),
            (blocked_center[0] + 5, blocked_center[1] + 5),
            2,
        )
        pygame.draw.line(
            overlay,
            (166, 203, 230, round(160 + pulse * 80)),
            (blocked_center[0] + 5, blocked_center[1] - 5),
            (blocked_center[0] - 5, blocked_center[1] + 5),
            2,
        )

    pygame.draw.circle(
        overlay,
        (118, 205, 255, round(130 + pulse * 90)),
        player_center,
        round(10 + pulse * 2),
        width=2,
    )
    screen.blit(overlay, (0, 0))


def draw_act_two_ability_preview(
    screen,
    game_state,
    current_time: int,
) -> None:
    player = game_state.player
    direction = player.act_two.selected_ability_direction
    if (
        player.player_class not in ("warrior", "mage")
        or not player.directional_ability_aiming
        or direction is None
    ):
        return

    if player.player_class == "mage":
        _draw_mage_preview(
            screen,
            game_state,
            direction,
            current_time,
        )
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


def draw_act_two_arcane_burst_effect(
    screen,
    game_state,
    current_time: int,
) -> None:
    player = game_state.player
    started_at = player.act_two.ability_effect_started_at
    if player.player_class != "mage" or started_at <= 0:
        return

    elapsed = current_time - started_at
    if not 0 <= elapsed < _ARCANE_BURST_EFFECT_DURATION_MS:
        return

    progress = elapsed / _ARCANE_BURST_EFFECT_DURATION_MS
    direction = player.act_two.ability_effect_direction
    cells = list(player.act_two.ability_effect_cells)
    origin = _cell_center(
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    staff_center = (
        origin[0] + direction[0] * 11 - direction[1] * 5,
        origin[1] + direction[1] * 11 - 9,
    )
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    charge_progress = min(1.0, progress / 0.22)
    charge_visibility = max(0.0, 1.0 - max(0.0, progress - 0.2) / 0.18)
    for ring_index in range(3):
        radius = round(
            17
            - charge_progress * 10
            + ring_index * 3
        )
        pygame.draw.circle(
            overlay,
            (
                57 + ring_index * 22,
                135 + ring_index * 24,
                255,
                round((125 - ring_index * 25) * charge_visibility),
            ),
            staff_center,
            max(2, radius),
            width=2,
        )
    pygame.draw.circle(
        overlay,
        (202, 243, 255, round(245 * charge_visibility)),
        staff_center,
        max(2, round(2 + charge_progress * 4)),
    )

    travel = max(0.0, min(1.0, (progress - 0.18) / 0.55))
    fade = max(0.0, min(1.0, (1.0 - progress) / 0.18))
    if cells and travel > 0:
        endpoint = _cell_center(cells[-1][0], cells[-1][1])
        head = (
            round(origin[0] + (endpoint[0] - origin[0]) * travel),
            round(origin[1] + (endpoint[1] - origin[1]) * travel),
        )
        traveled_pixels = math.dist(origin, head)
        trail_length = min(traveled_pixels, TILE_SIZE * 2.25)
        trail_start = (
            round(head[0] - direction[0] * trail_length),
            round(head[1] - direction[1] * trail_length),
        )
        pygame.draw.line(
            overlay,
            (27, 67, 183, round(90 * fade)),
            trail_start,
            head,
            15,
        )
        pygame.draw.line(
            overlay,
            (49, 132, 255, round(195 * fade)),
            trail_start,
            head,
            8,
        )
        pygame.draw.line(
            overlay,
            (178, 231, 255, round(255 * fade)),
            trail_start,
            head,
            3,
        )
        pygame.draw.circle(
            overlay,
            (68, 154, 255, round(135 * fade)),
            head,
            12,
        )
        pygame.draw.circle(
            overlay,
            (218, 248, 255, round(255 * fade)),
            head,
            5,
        )

        enemy_positions = set(
            player.act_two.ability_effect_hit_positions
        )
        cell_count = len(cells)
        for index, (column, row) in enumerate(cells, start=1):
            arrival = index / cell_count
            impact_age = travel - arrival
            if not 0 <= impact_age < 0.24:
                continue
            impact_progress = impact_age / 0.24
            visibility = (1.0 - impact_progress) * fade
            center = _cell_center(column, row)
            hit_enemy = (column, row) in enemy_positions
            radius = round(
                (5 if hit_enemy else 3)
                + impact_progress * (18 if hit_enemy else 11)
            )
            pygame.draw.circle(
                overlay,
                (
                    118,
                    205,
                    255,
                    round((235 if hit_enemy else 155) * visibility),
                ),
                center,
                radius,
                width=3 if hit_enemy else 2,
            )
            if hit_enemy:
                for spark_index in range(6):
                    angle = spark_index * math.tau / 6
                    spark_length = 7 + round(impact_progress * 12)
                    pygame.draw.line(
                        overlay,
                        (189, 236, 255, round(225 * visibility)),
                        center,
                        (
                            round(center[0] + math.cos(angle) * spark_length),
                            round(center[1] + math.sin(angle) * spark_length),
                        ),
                        2,
                    )

        if travel >= 0.94:
            collapse = min(1.0, (travel - 0.94) / 0.06)
            radius = round(15 - collapse * 8)
            pygame.draw.polygon(
                overlay,
                (193, 239, 255, round(240 * fade)),
                (
                    (endpoint[0], endpoint[1] - radius),
                    (endpoint[0] + radius, endpoint[1]),
                    (endpoint[0], endpoint[1] + radius),
                    (endpoint[0] - radius, endpoint[1]),
                ),
                width=2,
            )
    elif not cells and progress > 0.18:
        fizzle = max(0.0, 1.0 - (progress - 0.18) / 0.35)
        blocked = (
            origin[0] + direction[0] * TILE_SIZE,
            origin[1] + direction[1] * TILE_SIZE,
        )
        pygame.draw.circle(
            overlay,
            (91, 154, 220, round(190 * fizzle)),
            blocked,
            round(5 + (1 - fizzle) * 10),
            width=2,
        )

    screen.blit(overlay, (0, 0))
