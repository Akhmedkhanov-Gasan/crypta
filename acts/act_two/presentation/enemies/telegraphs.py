import math

import pygame

from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE
from acts.act_two.presentation.enemies.timing import (
    attack_telegraph_is_visible,
)
from acts.act_two.presentation.enemies.telegraph_styles import (
    draw_attack_lane,
    draw_attack_tile_base,
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
    attack_mode,
    lane,
):
    draw_attack_lane(
        screen,
        column,
        row,
        current_time,
        lane,
        enemy_type,
        attack_mode,
        is_player_cell,
    )


def _draw_archer_telegraph(
    screen,
    enemy,
    target,
    enemy_is_visible,
    current_time,
    lane=0,
):
    source = pygame.Vector2(
        MAP_OFFSET_X
        + enemy["column"] * TILE_SIZE
        + TILE_SIZE // 2,
        MAP_OFFSET_Y
        + enemy["row"] * TILE_SIZE
        + TILE_SIZE // 2,
    )
    destination = pygame.Vector2(
        MAP_OFFSET_X
        + target[0] * TILE_SIZE
        + TILE_SIZE // 2,
        MAP_OFFSET_Y
        + target[1] * TILE_SIZE
        + TILE_SIZE // 2,
    )

    direction = destination - source

    if direction.length_squared() == 0:
        return


    direction = direction.normalize()
    perpendicular = pygame.Vector2(
        -direction.y,
        direction.x,
    )

    pulse = (
        math.sin(current_time / 105)
        + 1
    ) / 2

    overlay = pygame.Surface(
        screen.get_size(),
        pygame.SRCALPHA,
    )


    lane_offsets = (0, -5, 5, -9, 9)
    lane_offset = lane_offsets[
        min(lane, len(lane_offsets) - 1)
    ]

    target_edge = (
        destination
        - direction * (TILE_SIZE * 0.46)
        + perpendicular * lane_offset
    )

    arrow_tip = (
        target_edge
        + direction * (8 + pulse * 2)
    )
    arrow_back = (
        arrow_tip
        - direction * 10
    )

    arrow_points = (
        arrow_tip,
        arrow_back + perpendicular * 6,
        arrow_back - perpendicular * 6,
    )
    outline_points = (
        arrow_tip + direction * 2,
        arrow_back + perpendicular * 8,
        arrow_back - perpendicular * 8,
    )

    pygame.draw.polygon(
        overlay,
        (10, 29, 12, 220),
        outline_points,
    )

    pygame.draw.polygon(
        overlay,
        (
            106,
            229,
            78,
            round(220 + pulse * 35),
        ),
        arrow_points,
    )

    pygame.draw.line(
        overlay,
        (
            205,
            255,
            176,
            round(225 + pulse * 30),
        ),
        arrow_back,
        arrow_tip,
        2,
    )

    feather_center = (
        arrow_back
        - direction * 2
    )

    pygame.draw.line(
        overlay,
        (
            106,
            229,
            78,
            round(190 + pulse * 55),
        ),
        feather_center,
        feather_center + perpendicular * 4,
        2,
    )
    pygame.draw.line(
        overlay,
        (
            106,
            229,
            78,
            round(190 + pulse * 55),
        ),
        feather_center,
        feather_center - perpendicular * 4,
        2,
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

_MAX_TELEGRAPH_LANES = 5


def _collect_attack_entries(
    enemies,
    current_time,
    visible_cells,
):
    entries = []

    for source_order, enemy in enumerate(enemies):
        if enemy["health"] <= 0:
            continue

        if not attack_telegraph_is_visible(
            enemy,
            current_time,
        ):
            continue

        targets = tuple(
            position
            for position in enemy["attack_targets"]
            if (
                visible_cells is None
                or position in visible_cells
            )
        )

        if not targets:
            continue

        entries.append(
            {
                "enemy": enemy,
                "source_order": source_order,
                "targets": targets,
                "target_set": frozenset(targets),
                "lane": 0,
            }
        )

    for entry in entries:
        occupied_lanes = {
            previous_entry["lane"]
            for previous_entry in entries
            if (
                previous_entry is not entry
                and previous_entry["source_order"]
                < entry["source_order"]
                and previous_entry["target_set"]
                & entry["target_set"]
            )
        }

        entry["lane"] = next(
            (
                lane
                for lane in range(_MAX_TELEGRAPH_LANES)
                if lane not in occupied_lanes
            ),
            _MAX_TELEGRAPH_LANES - 1,
        )

    return entries


def _group_attack_entries_by_cell(entries):
    entries_by_cell = {}

    for entry in entries:
        for position in entry["targets"]:
            entries_by_cell.setdefault(
                position,
                [],
            ).append(entry)

    return entries_by_cell


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

    entries = _collect_attack_entries(
        enemies,
        current_time,
        visible_cells,
    )
    entries_by_cell = _group_attack_entries_by_cell(
        entries,
    )

    if not foreground:
        for (column, row), cell_entries in entries_by_cell.items():
            draw_attack_tile_base(
                screen,
                column,
                row,
                len(cell_entries),
                current_time,
            )

        return

    for (column, row), cell_entries in entries_by_cell.items():
        for entry in cell_entries:
            enemy = entry["enemy"]

            _draw_attack_foreground(
                screen,
                column,
                row,
                current_time,
                (column, row) == player_position,
                enemy["type"],
                enemy.get("prepared_attack_mode"),
                entry["lane"],
            )


    for entry in entries:
        enemy = entry["enemy"]

        if (
            enemy["type"] != "archer"
            or enemy.get("prepared_attack_mode") != "ranged"
        ):
            continue

        attack_targets = entry["targets"]
        direct_target = (
            player_position
            if player_position in attack_targets
            else attack_targets[0]
        )

        enemy_is_visible = (
            visible_cells is None
            or (
                enemy["column"],
                enemy["row"],
            )
            in visible_cells
        )

        _draw_archer_telegraph(
            screen,
            enemy,
            direct_target,
            enemy_is_visible,
            current_time,
            entry["lane"],
        )
