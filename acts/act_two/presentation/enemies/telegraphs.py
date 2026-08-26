import math

import pygame

from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE
from acts.act_two.presentation.enemies.timing import (
    attack_telegraph_is_visible,
)

def _draw_standard_attack_tile(screen, column, row, current_time):
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


def _draw_brute_attack_tile(screen, column, row, current_time):
    left = MAP_OFFSET_X + column * TILE_SIZE
    top = MAP_OFFSET_Y + row * TILE_SIZE
    phase = (column * 0.61) + (row * 0.37)
    pulse = (math.sin(current_time / 82 + phase) + 1) / 2
    overflow = 2
    marker_size = TILE_SIZE + overflow * 2
    marker = pygame.Surface(
        (marker_size, marker_size),
        pygame.SRCALPHA,
    )
    marker.fill((105, 0, 8, round(82 + pulse * 48)))

    glow_alpha = round(118 + pulse * 92)
    pygame.draw.rect(
        marker,
        (255, 32, 35, glow_alpha),
        (1, 1, marker_size - 2, marker_size - 2),
        width=4,
        border_radius=3,
    )
    pygame.draw.rect(
        marker,
        (255, 103, 69, round(170 + pulse * 80)),
        (5, 5, marker_size - 10, marker_size - 10),
        width=2,
        border_radius=2,
    )

    center = marker_size // 2
    radius = 5 + round(pulse * 3)
    pygame.draw.circle(
        marker,
        (57, 0, 5, 220),
        (center, center),
        radius + 3,
        width=2,
    )
    pygame.draw.line(
        marker,
        (255, 142, 91, 235),
        (center - radius, center),
        (center + radius, center),
        3,
    )
    pygame.draw.line(
        marker,
        (255, 142, 91, 235),
        (center, center - radius),
        (center, center + radius),
        3,
    )
    screen.blit(marker, (left - overflow, top - overflow))


def _draw_archer_attack_tile(screen, column, row, current_time):
    left = MAP_OFFSET_X + column * TILE_SIZE
    top = MAP_OFFSET_Y + row * TILE_SIZE
    phase = (column * 0.73) + (row * 0.41)
    pulse = (math.sin(current_time / 105 + phase) + 1) / 2
    marker = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    inset = max(6, TILE_SIZE // 5)
    size = TILE_SIZE - inset * 2
    color = (255, 128, 54, round(180 + pulse * 70))
    fill = (134, 40, 8, round(45 + pulse * 35))

    pygame.draw.rect(
        marker,
        fill,
        (inset, inset, size, size),
        border_radius=4,
    )
    pygame.draw.rect(
        marker,
        color,
        (inset, inset, size, size),
        width=2,
        border_radius=4,
    )
    center = TILE_SIZE // 2
    pygame.draw.circle(
        marker,
        color,
        (center, center),
        max(3, size // 4),
        width=1,
    )
    pygame.draw.circle(marker, color, (center, center), 2)
    screen.blit(marker, (left, top))


def _draw_attack_foreground(
    screen,
    column,
    row,
    current_time,
    is_player_cell,
    enemy_type,
):
    left = MAP_OFFSET_X + column * TILE_SIZE
    top = MAP_OFFSET_Y + row * TILE_SIZE
    phase = (column * 0.73) + (row * 0.41)
    pulse = (math.sin(current_time / 105 + phase) + 1) / 2
    marker = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    if enemy_type == "brute":
        inset = 1 + round(pulse)
        arm = 11
        color = (255, 47, 42, round(220 + pulse * 35))
        shadow_width = 5
        line_width = 3
    elif enemy_type == "archer":
        inset = max(7, TILE_SIZE // 5) + round(pulse)
        arm = 5
        color = (255, 142, 61, round(195 + pulse * 60))
        shadow_width = 3
        line_width = 1
    else:
        inset = 2 + round(pulse)
        arm = 8
        color = (255, 76, 60, round(205 + pulse * 50))
        shadow_width = 4
        line_width = 2
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
        pygame.draw.lines(
            marker,
            shadow,
            False,
            points,
            shadow_width,
        )
        pygame.draw.lines(
            marker,
            color,
            False,
            points,
            line_width,
        )

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

def _draw_priest_heal_telegraph(
    screen,
    priest,
    target,
    priest_is_visible,
    current_time,
):
    target_center = pygame.Vector2(
        MAP_OFFSET_X
        + target.column * TILE_SIZE
        + TILE_SIZE // 2,
        MAP_OFFSET_Y
        + target.row * TILE_SIZE
        + TILE_SIZE // 2,
    )
    source_center = pygame.Vector2(
        MAP_OFFSET_X
        + priest.column * TILE_SIZE
        + TILE_SIZE // 2,
        MAP_OFFSET_Y
        + priest.row * TILE_SIZE
        + TILE_SIZE // 2,
    )

    overlay = pygame.Surface(
        screen.get_size(),
        pygame.SRCALPHA,
    )
    pulse = (math.sin(current_time / 125) + 1) / 2
    radius = round(TILE_SIZE * 0.42 + pulse * 4)
    center = (
        round(target_center.x),
        round(target_center.y),
    )

    pygame.draw.circle(
        overlay,
        (44, 188, 111, round(35 + pulse * 35)),
        center,
        radius,
    )
    pygame.draw.circle(
        overlay,
        (91, 238, 151, round(185 + pulse * 65)),
        center,
        radius,
        width=2,
    )

    aura_rectangle = pygame.Rect(
        0,
        0,
        radius * 2,
        radius * 2,
    )
    aura_rectangle.center = center

    rotation = current_time / 420
    for arc_index in range(3):
        start_angle = rotation + arc_index * math.tau / 3
        pygame.draw.arc(
            overlay,
            (148, 255, 190, round(180 + pulse * 70)),
            aura_rectangle,
            start_angle,
            start_angle + 0.75,
            3,
        )

    cross_size = 5
    pygame.draw.line(
        overlay,
        (211, 255, 226, 245),
        (center[0] - cross_size, center[1]),
        (center[0] + cross_size, center[1]),
        2,
    )
    pygame.draw.line(
        overlay,
        (211, 255, 226, 245),
        (center[0], center[1] - cross_size),
        (center[0], center[1] + cross_size),
        2,
    )

    direction = target_center - source_center
    if direction.length_squared() > 0:
        direction = direction.normalize()
        line_end = target_center - direction * (radius + 2)

        if priest_is_visible:
            line_start = source_center + direction * 13
        else:
            line_start = line_end - direction * TILE_SIZE

        line_length = max(1, (line_end - line_start).length())
        travel = (current_time / 22) % 10

        while travel < line_length:
            point = line_start + direction * travel
            pygame.draw.circle(
                overlay,
                (106, 239, 160, round(170 + pulse * 70)),
                (round(point.x), round(point.y)),
                2,
            )
            travel += 10

    screen.blit(overlay, (0, 0))

def _draw_priest_heal_telegraphs(
    screen,
    enemies,
    visible_cells,
    current_time,
):
    for priest in enemies:
        target = priest.heal_target

        if (
            priest.type != "priest"
            or priest.health <= 0
            or target is None
            or target.health <= 0
        ):
            continue

        target_position = (
            target.column,
            target.row,
        )

        if (
            visible_cells is not None
            and target_position not in visible_cells
        ):
            continue

        priest_is_visible = (
            visible_cells is None
            or (priest.column, priest.row) in visible_cells
        )

        _draw_priest_heal_telegraph(
            screen,
            priest,
            target,
            priest_is_visible,
            current_time,
        )


def draw_act_two_attack_markers(
    screen,
    enemies,
    current_time=0,
    visible_cells=None,
    player_position=None,
    foreground=False,
):
    if foreground:
        _draw_priest_heal_telegraphs(
            screen,
            enemies,
            visible_cells,
            current_time,
        )
    draw_order = {
        "brute": 0,
        "archer": 2,
    }
    ordered_enemies = sorted(
        enemies,
        key=lambda enemy: draw_order.get(enemy["type"], 1),
    )
    for enemy in ordered_enemies:
        if enemy["health"] <= 0:
            continue
        if not attack_telegraph_is_visible(
            enemy,
            current_time,
        ):
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
                    enemy["type"],
                )
            elif enemy["type"] == "brute":
                _draw_brute_attack_tile(
                    screen,
                    column,
                    row,
                    current_time,
                )
            elif enemy["type"] == "archer":
                _draw_archer_attack_tile(
                    screen,
                    column,
                    row,
                    current_time,
                )
            else:
                _draw_standard_attack_tile(
                    screen,
                    column,
                    row,
                    current_time,
                )
