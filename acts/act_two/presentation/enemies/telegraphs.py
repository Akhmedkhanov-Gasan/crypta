import math

import pygame

from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


def _draw_attack_tile(screen, column, row, current_time):
    left = MAP_OFFSET_X + column * TILE_SIZE
    top = MAP_OFFSET_Y + row * TILE_SIZE
    phase = (column * 0.73) + (row * 0.41)
    pulse = (math.sin(current_time / 105 + phase) + 1) / 2
    marker = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    marker.fill((126, 9, 18, round(50 + pulse * 35)))

    stripe_alpha = round(46 + pulse * 34)
    stripe_offset = round((current_time / 55 + column + row) % 8)
    for offset in range(-TILE_SIZE, TILE_SIZE * 2, 8):
        pygame.draw.line(
            marker,
            (222, 48, 43, stripe_alpha),
            (offset + stripe_offset, TILE_SIZE - 2),
            (offset + stripe_offset + TILE_SIZE, 2),
            1,
        )

    pygame.draw.rect(
        marker,
        (238, 55, 48, round(155 + pulse * 85)),
        (1, 1, TILE_SIZE - 2, TILE_SIZE - 2),
        width=2,
    )
    pygame.draw.rect(
        marker,
        (86, 7, 13, 205),
        (4, 4, TILE_SIZE - 8, TILE_SIZE - 8),
        width=1,
    )
    screen.blit(marker, (left, top))


def _draw_attack_foreground(
    screen,
    column,
    row,
    current_time,
    is_player_cell,
):
    left = MAP_OFFSET_X + column * TILE_SIZE
    top = MAP_OFFSET_Y + row * TILE_SIZE
    phase = (column * 0.73) + (row * 0.41)
    pulse = (math.sin(current_time / 105 + phase) + 1) / 2
    marker = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    inset = 2 + round(pulse)
    arm = 8
    color = (255, 76, 60, round(205 + pulse * 50))
    shadow = (38, 3, 7, 225)

    corner_segments = (
        ((inset, inset + arm), (inset, inset), (inset + arm, inset)),
        (
            (TILE_SIZE - inset - arm, inset),
            (TILE_SIZE - inset, inset),
            (TILE_SIZE - inset, inset + arm),
        ),
        (
            (inset, TILE_SIZE - inset - arm),
            (inset, TILE_SIZE - inset),
            (inset + arm, TILE_SIZE - inset),
        ),
        (
            (TILE_SIZE - inset - arm, TILE_SIZE - inset),
            (TILE_SIZE - inset, TILE_SIZE - inset),
            (TILE_SIZE - inset, TILE_SIZE - inset - arm),
        ),
    )
    for points in corner_segments:
        pygame.draw.lines(marker, shadow, False, points, 4)
        pygame.draw.lines(marker, color, False, points, 2)

    if is_player_cell:
        badge_center_x = TILE_SIZE // 2
        badge_top = 1
        badge_points = (
            (badge_center_x, badge_top),
            (badge_center_x + 6, badge_top + 6),
            (badge_center_x, badge_top + 12),
            (badge_center_x - 6, badge_top + 6),
        )
        pygame.draw.polygon(marker, (34, 3, 7, 240), badge_points)
        pygame.draw.polygon(marker, color, badge_points, width=2)
        pygame.draw.line(
            marker,
            (255, 226, 201, 255),
            (badge_center_x, badge_top + 3),
            (badge_center_x, badge_top + 7),
            2,
        )
        pygame.draw.circle(
            marker,
            (255, 226, 201, 255),
            (badge_center_x, badge_top + 9),
            1,
        )

    screen.blit(marker, (left, top))


def _draw_archer_telegraph(
    screen,
    enemy,
    target,
    enemy_is_visible,
    current_time,
):
    source = pygame.Vector2(
        MAP_OFFSET_X + enemy["column"] * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + enemy["row"] * TILE_SIZE + TILE_SIZE // 2,
    )
    destination = pygame.Vector2(
        MAP_OFFSET_X + target[0] * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + target[1] * TILE_SIZE + TILE_SIZE // 2,
    )
    direction = destination - source
    if direction.length_squared() == 0:
        return
    direction = direction.normalize()
    end = destination - direction * 11
    start = source + direction * 13
    if not enemy_is_visible:
        start = end - direction * 26

    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    distance = max(1, (end - start).length())
    pulse = (math.sin(current_time / 95) + 1) / 2
    step = 11
    segment_length = 6
    travel = (current_time / 18) % step
    while travel < distance:
        segment_start = start + direction * travel
        segment_end = start + direction * min(
            distance,
            travel + segment_length,
        )
        pygame.draw.line(
            overlay,
            (255, 79, 51, round(145 + pulse * 75)),
            segment_start,
            segment_end,
            2,
        )
        travel += step

    perpendicular = pygame.Vector2(-direction.y, direction.x)
    arrow_back = end - direction * 8
    pygame.draw.polygon(
        overlay,
        (255, 93, 59, round(205 + pulse * 50)),
        (
            end,
            arrow_back + perpendicular * 5,
            arrow_back - perpendicular * 5,
        ),
    )
    screen.blit(overlay, (0, 0))


def draw_act_two_attack_markers(
    screen,
    enemies,
    current_time=0,
    visible_cells=None,
    player_position=None,
    foreground=False,
):
    for enemy in enemies:
        if enemy["health"] <= 0:
            continue

        attack_targets = enemy["attack_targets"]
        if visible_cells is not None:
            attack_targets = [
                position
                for position in attack_targets
                if position in visible_cells
            ]
        if not attack_targets:
            continue

        enemy_is_visible = (
            visible_cells is None
            or (enemy["column"], enemy["row"]) in visible_cells
        )
        if (
            not foreground
            and enemy["type"] == "archer"
            and enemy.get("prepared_attack_mode") == "ranged"
        ):
            direct_target = (
                player_position
                if player_position in attack_targets
                else attack_targets[0]
            )
            _draw_archer_telegraph(
                screen,
                enemy,
                direct_target,
                enemy_is_visible,
                current_time,
            )

        for column, row in attack_targets:
            if foreground:
                _draw_attack_foreground(
                    screen,
                    column,
                    row,
                    current_time,
                    (column, row) == player_position,
                )
            else:
                _draw_attack_tile(screen, column, row, current_time)
