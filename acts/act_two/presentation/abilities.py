import math

import pygame

from acts.act_two.abilities import (
    get_mage_arcane_burst_cells,
    get_mage_arcane_cells,
    get_warrior_aftershock_cells,
    get_warrior_cleave_cells,
    is_valid_mage_arcane_burst_target,
)
from logic import get_enemy_occupied_positions
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


_CLEAVE_EFFECT_DURATION_MS = 760
_CLEAVE_PRIMARY_EFFECT_MS = 460
_AFTERSHOCK_START_MS = 330
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
    mage_target: tuple[int, int] | None = None,
) -> None:
    player = game_state.player
    direction = player.act_two.selected_ability_direction
    if (
        player.player_class not in ("warrior", "mage")
        or not player.directional_ability_aiming
    ):
        return

    if player.player_class == "mage":
        _draw_mage_target_preview(
            screen, game_state, mage_target, current_time
        )
        return

    if direction is None:
        return

    cells = get_warrior_cleave_cells(
        game_state.floor,
        direction[0],
        direction[1],
    )
    aftershock_cells = (
        get_warrior_aftershock_cells(
            game_state.floor,
            direction[0],
            direction[1],
        )
        if player.act_two.selected_rune_id == "rune_of_aftershock"
        else []
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

    for column, row in aftershock_cells:
        rectangle = pygame.Rect(
            MAP_OFFSET_X + column * TILE_SIZE,
            MAP_OFFSET_Y + row * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(
            overlay,
            (179, 72, 25, round(48 + pulse * 28)),
            rectangle.inflate(-7, -7),
        )
        pygame.draw.rect(
            overlay,
            (255, 172, 88, round(145 + pulse * 75)),
            rectangle.inflate(-4, -4),
            width=2,
        )
        perpendicular = (-direction[1], direction[0])
        for slash_offset in (-5, 5):
            slash_center = (
                rectangle.centerx + perpendicular[0] * slash_offset,
                rectangle.centery + perpendicular[1] * slash_offset,
            )
            pygame.draw.line(
                overlay,
                (255, 220, 155, round(165 + pulse * 80)),
                (
                    slash_center[0] - direction[0] * 8,
                    slash_center[1] - direction[1] * 8,
                ),
                (
                    slash_center[0] + direction[0] * 8,
                    slash_center[1] + direction[1] * 8,
                ),
                2,
            )
    screen.blit(overlay, (0, 0))


def _draw_mage_target_preview(
    screen,
    game_state,
    target: tuple[int, int] | None,
    current_time: int,
) -> None:
    if not is_valid_mage_arcane_burst_target(game_state, target):
        return

    cells = (
        [target]
        if (
            game_state.player.act_two.selected_rune_id
            == "rune_of_concentration"
        )
        else get_mage_arcane_burst_cells(game_state.floor, target)
    )
    pulse = 0.5 + 0.5 * math.sin(current_time / 105)
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    player_center = _cell_center(
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    target_center = _cell_center(*target)
    pygame.draw.line(
        overlay,
        (82, 168, 255, round(95 + pulse * 65)),
        player_center,
        target_center,
        2,
    )

    for position in cells:
        center_cell = position == target
        rectangle = pygame.Rect(
            MAP_OFFSET_X + position[0] * TILE_SIZE,
            MAP_OFFSET_Y + position[1] * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(
            overlay,
            (
                45,
                105,
                225,
                round((88 if center_cell else 48) + pulse * 34),
            ),
            rectangle.inflate(-4, -4),
        )
        pygame.draw.rect(
            overlay,
            (147, 218, 255, round(175 + pulse * 70)),
            rectangle.inflate(-2, -2),
            width=3 if center_cell else 2,
        )
        if not center_cell:
            direction = (
                position[0] - target[0],
                position[1] - target[1],
            )
            pygame.draw.line(
                overlay,
                (203, 241, 255, round(170 + pulse * 70)),
                (
                    rectangle.centerx - direction[0] * 5,
                    rectangle.centery - direction[1] * 5,
                ),
                (
                    rectangle.centerx + direction[0] * 9,
                    rectangle.centery + direction[1] * 9,
                ),
                2,
            )

    pygame.draw.circle(
        overlay,
        (209, 244, 255, round(210 + pulse * 45)),
        target_center,
        round(7 + pulse * 2),
        width=2,
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

    progress = min(1.0, elapsed / _CLEAVE_PRIMARY_EFFECT_MS)
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

    if (
        player.act_two.selected_rune_id == "rune_of_aftershock"
        and elapsed >= _AFTERSHOCK_START_MS
    ):
        aftershock_elapsed = elapsed - _AFTERSHOCK_START_MS
        aftershock_progress = min(1.0, aftershock_elapsed / 210)
        aftershock_fade = max(0.0, 1.0 - aftershock_elapsed / 410)
        aftershock_center_x = (
            origin_x
            + direction_x
            * TILE_SIZE
            * (1.45 + aftershock_progress * 0.55)
        )
        aftershock_center_y = (
            origin_y
            + direction_y
            * TILE_SIZE
            * (1.45 + aftershock_progress * 0.55)
        )
        aftershock_points = []
        for point_index in range(11):
            position = -1.0 + point_index / 5
            across = position * TILE_SIZE * 0.72
            bow = (1.0 - position * position) * TILE_SIZE * 0.25
            aftershock_points.append(
                (
                    round(
                        aftershock_center_x
                        + perpendicular_x * across
                        + direction_x * bow
                    ),
                    round(
                        aftershock_center_y
                        + perpendicular_y * across
                        + direction_y * bow
                    ),
                )
            )
        pygame.draw.lines(
            overlay,
            (206, 39, 47, round(205 * aftershock_fade)),
            False,
            aftershock_points,
            5,
        )
        pygame.draw.lines(
            overlay,
            (255, 169, 112, round(230 * aftershock_fade)),
            False,
            aftershock_points,
            2,
        )

        for column, row in player.act_two.ability_effect_aftershock_positions:
            impact_center = _cell_center(column, row)
            impact_radius = round(6 + aftershock_progress * 18)
            pygame.draw.circle(
                overlay,
                (226, 48, 43, round(175 * aftershock_fade)),
                impact_center,
                impact_radius,
                width=4,
            )
            pygame.draw.circle(
                overlay,
                (255, 192, 111, round(235 * aftershock_fade)),
                impact_center,
                max(3, impact_radius - 4),
                width=2,
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

    effect_kind = player.act_two.ability_effect_kind
    target = player.act_two.ability_effect_target
    if target is None:
        return

    elapsed = current_time - started_at
    if not 0 <= elapsed < _ARCANE_BURST_EFFECT_DURATION_MS:
        return

    progress = elapsed / _ARCANE_BURST_EFFECT_DURATION_MS

    origin = _cell_center(
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    target_center = _cell_center(*target)
    staff_center = (origin[0] + 7, origin[1] - 9)
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    charge_progress = min(1.0, progress / 0.2)
    charge_visibility = max(
        0.0,
        1.0 - max(0.0, progress - 0.17) / 0.2,
    )
    for ring_index in range(3):
        radius = round(18 - charge_progress * 11 + ring_index * 3)
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

    travel = max(0.0, min(1.0, (progress - 0.13) / 0.28))
    if travel > 0:
        head = (
            round(origin[0] + (target_center[0] - origin[0]) * travel),
            round(origin[1] + (target_center[1] - origin[1]) * travel),
        )
        trail_start_progress = max(0.0, travel - 0.28)
        trail_start = (
            round(
                origin[0]
                + (target_center[0] - origin[0]) * trail_start_progress
            ),
            round(
                origin[1]
                + (target_center[1] - origin[1]) * trail_start_progress
            ),
        )
        pygame.draw.line(
            overlay,
            (27, 67, 183, 100),
            trail_start,
            head,
            13,
        )
        pygame.draw.line(
            overlay,
            (49, 132, 255, 210),
            trail_start,
            head,
            7,
        )
        pygame.draw.line(
            overlay,
            (188, 236, 255, 255),
            trail_start,
            head,
            2,
        )
        pygame.draw.circle(
            overlay,
            (68, 154, 255, 150),
            head,
            10,
        )
        pygame.draw.circle(
            overlay,
            (218, 248, 255, 255),
            head,
            4,
        )

    impact_progress = max(0.0, min(1.0, (progress - 0.38) / 0.62))
    if impact_progress > 0:
        visibility = 1.0 - impact_progress
        radius = round(5 + impact_progress * TILE_SIZE * 0.9)
        pygame.draw.circle(
            overlay,
            (75, 151, 255, round(220 * visibility)),
            target_center,
            radius,
            width=3,
        )
        pygame.draw.circle(
            overlay,
            (188, 236, 255, round(245 * visibility)),
            target_center,
            max(3, round(radius * 0.58)),
            width=2,
        )
        arm_length = round(TILE_SIZE * (0.35 + impact_progress * 0.95))
        impact_directions = (
            ()
            if effect_kind == "concentration_release"
            else ((0, -1), (1, 0), (0, 1), (-1, 0))
        )
        for direction in impact_directions:
            endpoint = (
                target_center[0] + direction[0] * arm_length,
                target_center[1] + direction[1] * arm_length,
            )
            perpendicular = (-direction[1], direction[0])
            pygame.draw.line(
                overlay,
                (54, 124, 245, round(150 * visibility)),
                target_center,
                endpoint,
                9,
            )
            pygame.draw.line(
                overlay,
                (194, 239, 255, round(245 * visibility)),
                target_center,
                endpoint,
                3,
            )
            for spark_index in (-1, 0, 1):
                spark_center = (
                    endpoint[0] + perpendicular[0] * spark_index * 4,
                    endpoint[1] + perpendicular[1] * spark_index * 4,
                )
                spark_end = (
                    spark_center[0] + direction[0] * (6 + abs(spark_index) * 3),
                    spark_center[1] + direction[1] * (6 + abs(spark_index) * 3),
                )
                pygame.draw.line(
                    overlay,
                    (160, 225, 255, round(220 * visibility)),
                    spark_center,
                    spark_end,
                    2,
                )

        core_radius = round(9 + impact_progress * 12)
        pygame.draw.polygon(
            overlay,
            (215, 247, 255, round(250 * visibility)),
            (
                (target_center[0], target_center[1] - core_radius),
                (target_center[0] + core_radius, target_center[1]),
                (target_center[0], target_center[1] + core_radius),
                (target_center[0] - core_radius, target_center[1]),
            ),
            width=3,
        )

        hit_positions = set(player.act_two.ability_effect_hit_positions)
        for position in hit_positions:
            if position not in player.act_two.ability_effect_cells:
                continue
            center = _cell_center(*position)
            pygame.draw.circle(
                overlay,
                (226, 250, 255, round(235 * visibility)),
                center,
                round(5 + impact_progress * 14),
                width=2,
            )

    screen.blit(overlay, (0, 0))
