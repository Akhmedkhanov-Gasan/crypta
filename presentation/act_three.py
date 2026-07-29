import math
from functools import lru_cache

import pygame

from game.state import EnemyBehaviorState
from levels import FLOOR_CONFIGS
from presentation.hud import get_event_color, wrap_text
from presentation.layout import (
    ACT_THREE_FRAME_X,
    ACT_THREE_FRAME_Y,
    ACT_THREE_SIDEBAR_HEIGHT,
    ACT_THREE_SIDEBAR_WIDTH,
    ACT_THREE_SIDEBAR_X,
    ACT_THREE_SIDEBAR_Y,
    ACT_THREE_TILE_SIZE,
    ACT_THREE_VIEW_HEIGHT,
    ACT_THREE_VIEW_WIDTH,
    ACT_THREE_VIEW_X,
    ACT_THREE_VIEW_Y,
)
from settings import (
    CLASS_ABILITY_KILLS,
    ASSASSIN_ULTIMATE_OUTRO_MS,
    ASSASSIN_ULTIMATE_PRELUDE_MS,
    ASSASSIN_TELEPORT_CHARGES,
    ASSASSIN_ULTIMATE_CHARGES,
    ASSASSIN_ULTIMATE_STEP_MS,
    ARCHER_EMPOWERED_SHOT_PROJECTILE_MS,
    ARCHER_EMPOWERED_SHOT_CHARGES,
    ARCHER_BARRAGE_ZONE_CHARGES,
    ARCHER_LEAP_CHARGES,
    ARCHER_LEAP_DURATION_MS,
    BERSERKER_RAGE_CRITICAL_HEALTH_RATIO,
    BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER,
    BERSERKER_RAGE_INJURED_HEALTH_RATIO,
    BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER,
    BERSERKER_CRUSHING_LEAP_CHARGES,
    BERSERKER_CRUSHING_LEAP_IMPACT_MS,
    BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
    BERSERKER_LAST_RAGE_CHARGES,
    DANGER_BORDER_COLOR,
    HEALTH_BAR_BACKGROUND,
    HEALTH_BAR_COLOR,
    PALADIN_HOLY_HAND_CHARGES,
    PALADIN_HOLY_HAND_EFFECT_MS,
    PALADIN_HOLY_SHIELD_CHARGES,
    PALADIN_HOLY_SHIELD_DAMAGE_BONUS,
    PALADIN_SHIELD_CHARGE_CHARGES,
    PALADIN_SHIELD_CHARGE_TRAVEL_MS,
    TEXT_COLOR,
    WARLOCK_CURSE_CHARGES,
    WARLOCK_SOUL_EXCHANGE_CHARGES,
    WARLOCK_SOUL_EXCHANGE_TRAVEL_MS,
)


_TORCH_LIGHT_SURFACE = None
_IDLE_FRAME_SEQUENCE = (0, 1, 2, 1)
_IDLE_TIMELINE_CYCLE_COUNT = 4
_MOVE_FRAME_COUNT = 2
_MOVE_FRAME_DURATION_MS = 90
_ATTACK_FRAME_DURATION_MS = 240
_TELEPORT_CAMERA_DURATION_MS = 480
_TELEPORT_EFFECT_DURATION_MS = 600
_ARCHER_BARRAGE_SHOT_EFFECT_MS = 360
_TOP_VOID_CORNER_Y_OFFSET = 47
_TOP_VOID_CORNER_X_OFFSETS = {
    "wall_corner_top_left": -18,
    "wall_corner_top_right": 18,
}
_TOP_VOID_DOUBLE_CORNER_CROP_WIDTH = 24


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


def _draw_tile_markers(
    view_surface,
    positions,
    camera_x,
    camera_y,
    color,
):
    marker_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    marker_surface.fill((*color, 74))
    pygame.draw.rect(
        marker_surface,
        (*color, 210),
        marker_surface.get_rect(),
        width=3,
    )

    for column, row in positions:
        view_surface.blit(
            marker_surface,
            _view_position(
                column,
                row,
                camera_x,
                camera_y,
            ),
        )


def _draw_archer_barrage_zone_cells(
    view_surface,
    cell_sprite,
    positions,
    camera_x,
    camera_y,
    current_time,
    preview=False,
):
    if not positions:
        return

    pulse = (math.sin(current_time * 0.008) + 1) / 2
    zone_sprite = cell_sprite.copy()
    zone_sprite.set_alpha(
        round(
            (78 if preview else 118)
            + pulse * (22 if preview else 42)
        )
    )
    for column, row in positions:
        view_surface.blit(
            zone_sprite,
            _view_position(
                column,
                row,
                camera_x,
                camera_y,
            ),
        )


def _draw_health_bar(
    surface,
    left,
    top,
    health,
    maximum_health,
    color,
):
    bar_width = ACT_THREE_TILE_SIZE - 14
    bar_height = 5
    health_ratio = max(0, health / maximum_health)
    pygame.draw.rect(
        surface,
        HEALTH_BAR_BACKGROUND,
        (left + 7, top + 56, bar_width, bar_height),
    )
    pygame.draw.rect(
        surface,
        color,
        (
            left + 7,
            top + 56,
            round(bar_width * health_ratio),
            bar_height,
        ),
    )


def _stable_text_seed(text):
    seed = 2166136261

    for character in text:
        seed ^= ord(character)
        seed = (seed * 16777619) & 0xFFFFFFFF

    return seed


def _next_idle_random(state):
    state = (
        state * 1664525 + 1013904223
    ) & 0xFFFFFFFF
    return state, state


@lru_cache(maxsize=None)
def _idle_timeline(identity_seed):
    state = identity_seed & 0xFFFFFFFF
    timeline = []

    for _ in range(_IDLE_TIMELINE_CYCLE_COUNT):
        state, neutral_roll = _next_idle_random(state)
        state, inhale_roll = _next_idle_random(state)
        state, full_breath_roll = _next_idle_random(state)
        state, exhale_roll = _next_idle_random(state)
        durations = (
            2800 + neutral_roll % 2001,
            650 + inhale_roll % 301,
            1200 + full_breath_roll % 1201,
            650 + exhale_roll % 301,
        )
        timeline.extend(
            zip(_IDLE_FRAME_SEQUENCE, durations)
        )

    total_duration = sum(
        duration for _, duration in timeline
    )
    return tuple(timeline), total_duration


def _idle_frame(current_time, identity_seed):
    timeline, total_duration = _idle_timeline(
        identity_seed
    )
    phase_offset = (
        identity_seed * 2654435761
    ) % total_duration
    elapsed = (
        current_time + phase_offset
    ) % total_duration

    for frame_index, duration in timeline:
        if elapsed < duration:
            return frame_index

        elapsed -= duration

    return 0


def _movement_frame(current_time, started_at):
    return (
        (current_time - started_at) // _MOVE_FRAME_DURATION_MS
    ) % _MOVE_FRAME_COUNT


def _draw_attack_impact_flash(
    surface,
    position,
    current_time,
    started_at,
    flash_color,
):
    elapsed = current_time - started_at
    if not 0 <= elapsed < _ATTACK_FRAME_DURATION_MS:
        return

    progress = elapsed / _ATTACK_FRAME_DURATION_MS
    visibility = math.sin(math.pi * progress)
    center = (
        position[0] + ACT_THREE_TILE_SIZE // 2,
        position[1] + ACT_THREE_TILE_SIZE // 2,
    )
    radius = round(7 + visibility * 9)
    alpha = round(190 * visibility)
    flash_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    local_center = (
        center[0] - position[0],
        center[1] - position[1],
    )
    pygame.draw.circle(
        flash_surface,
        (*flash_color, alpha),
        local_center,
        radius,
        width=2,
    )
    pygame.draw.line(
        flash_surface,
        (235, 255, 235, alpha),
        (local_center[0] - radius, local_center[1] + radius // 2),
        (local_center[0] + radius, local_center[1] - radius // 2),
        width=2,
    )
    surface.blit(flash_surface, position)


def _draw_archer_projectile(
    surface,
    arrow_sprite,
    origin,
    destination,
    progress,
    empowered=False,
    current_time=0,
):
    direction = math.atan2(
        destination[1] - origin[1],
        destination[0] - origin[0],
    )
    rotation = -math.degrees(direction) - 45
    arrow_position = (
        round(origin[0] + (destination[0] - origin[0]) * progress),
        round(origin[1] + (destination[1] - origin[1]) * progress),
    )

    for trail_progress, trail_alpha in (
        (progress - 0.18, 38),
        (progress - 0.10, 78),
    ):
        if trail_progress <= 0:
            continue
        trail_position = (
            round(origin[0] + (destination[0] - origin[0]) * trail_progress),
            round(origin[1] + (destination[1] - origin[1]) * trail_progress),
        )
        trail = pygame.transform.rotate(arrow_sprite, rotation).copy()
        trail.set_alpha(trail_alpha)
        surface.blit(trail, trail.get_rect(center=trail_position))

    if empowered:
        effect_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        travel_dx = destination[0] - origin[0]
        travel_dy = destination[1] - origin[1]
        travel_length = max(1, math.hypot(travel_dx, travel_dy))
        direction_x = travel_dx / travel_length
        direction_y = travel_dy / travel_length
        normal_x = -travel_dy / travel_length
        normal_y = travel_dx / travel_length

        trail_start_progress = max(0, progress - 0.34)
        trail_start = (
            round(origin[0] + travel_dx * trail_start_progress),
            round(origin[1] + travel_dy * trail_start_progress),
        )
        for width, color in (
            (12, (20, 135, 85, 24)),
            (7, (40, 220, 125, 48)),
            (3, (125, 255, 180, 145)),
            (1, (235, 255, 240, 225)),
        ):
            pygame.draw.line(
                effect_surface,
                color,
                trail_start,
                arrow_position,
                width=width,
            )

        for wave_index, (wave_color, wave_alpha) in enumerate(
            (
                ((75, 235, 135), 115),
                ((145, 255, 190), 70),
            )
        ):
            points = []
            for point_index in range(15):
                wave_progress = max(
                    0,
                    progress - 0.31 + point_index * 0.021,
                )
                wave_x = origin[0] + travel_dx * wave_progress
                wave_y = origin[1] + travel_dy * wave_progress
                wave = math.sin(
                    current_time * 0.014
                    + point_index * 0.82
                    + wave_index * math.pi
                ) * (3.5 + wave_index * 2)
                points.append(
                    (
                        round(wave_x + normal_x * wave),
                        round(wave_y + normal_y * wave),
                    )
                )
            if len(points) > 1:
                pygame.draw.lines(
                    effect_surface,
                    (*wave_color, wave_alpha),
                    False,
                    points,
                    width=1 if wave_index else 2,
                )

        for particle_index in range(9):
            particle_progress = progress - 0.035 - particle_index * 0.032
            if particle_progress <= 0:
                continue
            particle_wave = math.sin(
                current_time * 0.021 + particle_index * 2.15
            ) * (2 + particle_index * 0.45)
            particle_position = (
                round(
                    origin[0]
                    + travel_dx * particle_progress
                    + normal_x * particle_wave
                ),
                round(
                    origin[1]
                    + travel_dy * particle_progress
                    + normal_y * particle_wave
                ),
            )
            particle_alpha = max(30, 185 - particle_index * 17)
            particle_radius = 2 if particle_index < 3 else 1
            pygame.draw.circle(
                effect_surface,
                (155, 255, 195, particle_alpha),
                particle_position,
                particle_radius,
            )

        pulse = (math.sin(current_time * 0.025) + 1) / 2
        for radius, alpha in (
            (13, round(18 + pulse * 10)),
            (8, round(30 + pulse * 14)),
            (4, round(65 + pulse * 25)),
        ):
            pygame.draw.circle(
                effect_surface,
                (75, 245, 145, alpha),
                arrow_position,
                radius,
            )

        ring_angle = current_time * 0.012
        for angle_offset in (-0.9, 0.9):
            ring_length = 9
            ring_center = (
                round(
                    arrow_position[0]
                    - direction_x * 4
                    + normal_x * math.sin(ring_angle + angle_offset) * 5
                ),
                round(
                    arrow_position[1]
                    - direction_y * 4
                    + normal_y * math.sin(ring_angle + angle_offset) * 5
                ),
            )
            ring_end = (
                round(ring_center[0] + normal_x * ring_length),
                round(ring_center[1] + normal_y * ring_length),
            )
            pygame.draw.line(
                effect_surface,
                (205, 255, 220, 155),
                ring_center,
                ring_end,
                width=1,
            )

        if progress > 0.82:
            impact_progress = min(1, (progress - 0.82) / 0.18)
            impact_visibility = math.sin(math.pi * impact_progress)
            impact_radius = round(5 + impact_progress * 12)
            pygame.draw.circle(
                effect_surface,
                (
                    95,
                    255,
                    160,
                    round(150 * impact_visibility),
                ),
                destination,
                impact_radius,
                width=2,
            )
            for ray_index in range(6):
                ray_angle = ray_index * math.tau / 6 + direction
                ray_start = (
                    round(
                        destination[0]
                        + math.cos(ray_angle) * 4
                    ),
                    round(
                        destination[1]
                        + math.sin(ray_angle) * 4
                    ),
                )
                ray_end = (
                    round(
                        destination[0]
                        + math.cos(ray_angle) * impact_radius
                    ),
                    round(
                        destination[1]
                        + math.sin(ray_angle) * impact_radius
                    ),
                )
                pygame.draw.line(
                    effect_surface,
                    (
                        220,
                        255,
                        225,
                        round(175 * impact_visibility),
                    ),
                    ray_start,
                    ray_end,
                    width=1,
                )

        surface.blit(effect_surface, (0, 0))

    arrow = pygame.transform.rotate(arrow_sprite, rotation)
    surface.blit(arrow, arrow.get_rect(center=arrow_position))


def _draw_warlock_orb(
    surface,
    origin,
    destination,
    progress,
    current_time,
):
    orb_position = (
        round(
            origin[0]
            + (destination[0] - origin[0]) * progress
        ),
        round(
            origin[1]
            + (destination[1] - origin[1]) * progress
        ),
    )
    effect_surface = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    trail_start_progress = max(0, progress - 0.34)
    trail_start = (
        round(
            origin[0]
            + (destination[0] - origin[0])
            * trail_start_progress
        ),
        round(
            origin[1]
            + (destination[1] - origin[1])
            * trail_start_progress
        ),
    )
    for width, color in (
        (10, (72, 18, 112, 32)),
        (6, (126, 35, 188, 68)),
        (2, (211, 105, 255, 175)),
    ):
        pygame.draw.line(
            effect_surface,
            color,
            trail_start,
            orb_position,
            width=width,
        )

    pulse = (math.sin(current_time * 0.028) + 1) / 2
    for radius, color in (
        (10, (86, 20, 142, round(38 + pulse * 20))),
        (7, (144, 42, 222, round(95 + pulse * 35))),
        (4, (210, 105, 255, 235)),
        (2, (246, 220, 255, 255)),
    ):
        pygame.draw.circle(
            effect_surface,
            color,
            orb_position,
            radius,
        )

    for particle_index in range(5):
        angle = (
            current_time * 0.012
            + particle_index * math.tau / 5
        )
        particle_position = (
            round(orb_position[0] + math.cos(angle) * 9),
            round(orb_position[1] + math.sin(angle) * 7),
        )
        pygame.draw.circle(
            effect_surface,
            (225, 125, 255, 170),
            particle_position,
            1,
        )

    if progress > 0.78:
        impact_progress = min(
            1,
            (progress - 0.78) / 0.22,
        )
        impact_visibility = math.sin(
            math.pi * impact_progress
        )
        pygame.draw.circle(
            effect_surface,
            (
                205,
                75,
                255,
                round(190 * impact_visibility),
            ),
            destination,
            round(7 + impact_progress * 13),
            width=2,
        )

    surface.blit(effect_surface, (0, 0))


def _draw_assassin_slash_particles(
    surface,
    position,
    progress,
    identity_seed,
    strike_index,
):
    particle_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    center = ACT_THREE_TILE_SIZE // 2
    visibility = math.sin(math.pi * progress)
    alpha = round(245 * visibility)
    slash_patterns = (
        ((-1.10, 25, -5), (-0.28, 19, 4), (0.62, 22, 0)),
        ((-0.55, 22, -7), (0.38, 28, 4), (1.18, 18, 1)),
        ((-1.38, 18, 3), (-0.72, 27, -4), (0.20, 24, 5)),
        ((-0.92, 29, 5), (0.02, 18, -5), (0.82, 26, 2)),
        ((-0.35, 20, -4), (0.56, 25, 5), (1.36, 19, -1)),
    )
    slash_pattern = slash_patterns[strike_index % len(slash_patterns)]
    for slash_index, (base_angle, length, offset) in enumerate(
        slash_pattern
    ):
        angle = (
            base_angle
            + math.sin(progress * math.tau + slash_index) * 0.16
            + (identity_seed % 11) * 0.01
        )
        bend = 5 + slash_index * 2
        start = (
            round(center + math.cos(angle) * offset - math.cos(angle) * length / 2),
            round(center + math.sin(angle) * offset - math.sin(angle) * length / 2),
        )
        end = (
            round(center + math.cos(angle) * offset + math.cos(angle) * length / 2),
            round(center + math.sin(angle) * offset + math.sin(angle) * length / 2),
        )
        middle = (
            round((start[0] + end[0]) / 2 - math.sin(angle) * bend),
            round((start[1] + end[1]) / 2 + math.cos(angle) * bend),
        )
        pygame.draw.line(
            particle_surface,
            (65, 145, 255, alpha // 3),
            start,
            middle,
            width=8,
        )
        pygame.draw.line(
            particle_surface,
            (65, 145, 255, alpha // 3),
            middle,
            end,
            width=8,
        )
        pygame.draw.line(
            particle_surface,
            (185, 230, 255, alpha),
            start,
            middle,
            width=2,
        )
        pygame.draw.line(
            particle_surface,
            (220, 245, 255, alpha),
            middle,
            end,
            width=2,
        )
        for shard_index, shard_side in enumerate((-1, 1)):
            shard_origin = (
                end[0] + round(math.cos(angle + math.pi / 2) * shard_side * 4),
                end[1] + round(math.sin(angle + math.pi / 2) * shard_side * 4),
            )
            shard_end = (
                shard_origin[0] + round(math.cos(angle + shard_side) * (5 + shard_index * 2)),
                shard_origin[1] + round(math.sin(angle + shard_side) * (5 + shard_index * 2)),
            )
            pygame.draw.line(
                particle_surface,
                (125, 205, 255, alpha),
                shard_origin,
                shard_end,
                width=2,
            )
    surface.blit(particle_surface, position)


def _enemy_sprite(
    assets,
    enemy,
    current_time,
    visual_seed,
):
    if (
        enemy.type in (
            "archer",
            "brute",
            "sentinel",
        )
        and 0 <= current_time - enemy.attack_animation_started_at
        < _ATTACK_FRAME_DURATION_MS
    ):
        return assets[f"enemy_{enemy.type}_attack"]

    if (
        enemy.type == "priest"
        and 0 <= current_time - enemy.attack_animation_started_at
        < _ATTACK_FRAME_DURATION_MS
    ):
        return assets["priest_heal_cast"]

    if (
        enemy.type in (
            "archer",
            "brute",
            "priest",
            "sentinel",
        )
        and 0 <= current_time - enemy.movement_animation_started_at
        < _MOVE_FRAME_COUNT * _MOVE_FRAME_DURATION_MS
    ):
        return assets[
            f"enemy_{enemy.type}_walk_{_movement_frame(
                current_time,
                enemy.movement_animation_started_at,
            )}"
        ]

    if (
        enemy.type == "sentinel"
        and enemy.shield_turns > 0
    ):
        return assets["sentinel_guard"]

    if (
        enemy.type == "priest"
        and enemy.behavior_state
        is EnemyBehaviorState.PREPARING_HEAL
        and enemy.heal_target is not None
        and enemy.heal_target.health > 0
    ):
        return assets["priest_heal_cast"]

    if enemy.type in (
        "archer",
        "brute",
        "sentinel",
        "priest",
    ):
        identity_seed = (
            visual_seed
            ^ _stable_text_seed(
                f"{enemy.type}:{enemy.name}"
            )
        )
        frame_index = _idle_frame(
            current_time,
            identity_seed,
        )
        return assets[
            f"enemy_{enemy.type}_idle_{frame_index}"
        ]

    return assets.get(
        f"enemy_{enemy.type}",
        assets["enemy_brute"],
    )


def _draw_healing_aura(
    surface,
    left,
    top,
    current_time,
    identity_seed,
):
    margin = 12
    effect_size = ACT_THREE_TILE_SIZE + margin * 2
    aura_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    phase = (
        current_time + identity_seed % 1700
    ) / 620
    pulse = (math.sin(phase) + 1) / 2
    center_x = effect_size // 2
    center_y = effect_size // 2 - 1

    for radius, base_alpha in (
        (ACT_THREE_TILE_SIZE // 2 + 8, 12),
        (ACT_THREE_TILE_SIZE // 2 + 3, 20),
        (ACT_THREE_TILE_SIZE // 2 - 2, 28),
    ):
        alpha = round(base_alpha + pulse * 12)
        pygame.draw.circle(
            aura_surface,
            (42, 205, 94, alpha),
            (center_x, center_y),
            radius,
            width=4,
        )

    ring_width = round(
        ACT_THREE_TILE_SIZE * (0.58 + pulse * 0.10)
    )
    ring_height = 10 + round(pulse * 3)
    pygame.draw.ellipse(
        aura_surface,
        (74, 245, 130, 105),
        (
            center_x - ring_width // 2,
            margin + ACT_THREE_TILE_SIZE - 15,
            ring_width,
            ring_height,
        ),
        width=2,
    )

    for mote_index in range(5):
        mote_phase = (
            phase * (0.72 + mote_index * 0.08)
            + mote_index * 1.7
        )
        mote_x = center_x + round(
            math.sin(mote_phase) * (19 + mote_index % 2 * 7)
        )
        mote_y = (
            margin
            + ACT_THREE_TILE_SIZE
            - 8
            - round(
                (
                    (current_time / 18)
                    + mote_index * 13
                    + identity_seed % 31
                )
                % 52
            )
        )
        mote_size = 2 + mote_index % 2
        pygame.draw.rect(
            aura_surface,
            (100, 255, 152, 125),
            (
                mote_x,
                mote_y,
                mote_size,
                mote_size,
            ),
        )

    surface.blit(
        aura_surface,
        (left - margin, top - margin),
    )


def _draw_warlock_curse_aura(
    surface,
    left,
    top,
    current_time,
    identity_seed,
):
    margin = 10
    effect_size = ACT_THREE_TILE_SIZE + margin * 2
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    center = (
        effect_size // 2,
        margin + ACT_THREE_TILE_SIZE // 2,
    )
    pulse = (math.sin(current_time * 0.012) + 1) / 2

    for ring_index in range(2):
        pygame.draw.ellipse(
            effect_surface,
            (
                177 + ring_index * 35,
                45,
                235,
                round(75 + pulse * 45 - ring_index * 20),
            ),
            (
                3 + ring_index * 5,
                5 + ring_index * 4,
                effect_size - 6 - ring_index * 10,
                effect_size - 10 - ring_index * 8,
            ),
            width=2,
        )

    rotation = (
        current_time * 0.004
        + (identity_seed % 97) / 97
    )
    for rune_index in range(6):
        angle = rotation + rune_index * math.tau / 6
        rune_position = (
            round(center[0] + math.cos(angle) * 29),
            round(center[1] + math.sin(angle) * 25),
        )
        rune_alpha = round(155 + pulse * 80)
        pygame.draw.line(
            effect_surface,
            (218, 98, 255, rune_alpha),
            (rune_position[0] - 2, rune_position[1]),
            (rune_position[0] + 2, rune_position[1]),
            width=1,
        )
        pygame.draw.line(
            effect_surface,
            (218, 98, 255, rune_alpha),
            (rune_position[0], rune_position[1] - 2),
            (rune_position[0], rune_position[1] + 2),
            width=1,
        )

    pygame.draw.circle(
        effect_surface,
        (121, 28, 180, round(24 + pulse * 20)),
        center,
        22,
    )
    surface.blit(
        effect_surface,
        (left - margin, top - margin),
    )


def _draw_rogue_idle_particles(
    surface,
    left,
    top,
    current_time,
    identity_seed,
    subclass,
):
    particle_colors = {
        "archer": (
            (57, 111, 42),
            (125, 184, 87),
            (65, 108, 48),
        ),
        "assassin": (
            (35, 72, 132),
            (76, 137, 225),
            (38, 77, 142),
        ),
    }
    glow_color, mote_color, trail_color = (
        particle_colors[subclass]
    )
    effect_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )

    for mote_index in range(3):
        phase = (
            current_time / 2300
            + mote_index / 3
            + (identity_seed % 97) / 97
        ) % 1
        visibility = math.sin(math.pi * phase)
        drift = math.sin(
            phase * math.tau + mote_index * 1.9
        )
        mote_x = round(
            ACT_THREE_TILE_SIZE // 2
            + (-14, 10, 17)[mote_index]
            + drift * 3
        )
        mote_y = round(
            ACT_THREE_TILE_SIZE - 12 - phase * 43
        )
        mote_size = 1 + (mote_index == 1)
        glow_alpha = round(50 * visibility)
        alpha = round(175 * visibility)
        pygame.draw.circle(
            effect_surface,
            (*glow_color, glow_alpha),
            (mote_x, mote_y),
            2,
        )
        pygame.draw.rect(
            effect_surface,
            (*mote_color, alpha),
            (
                mote_x,
                mote_y,
                mote_size,
                mote_size,
            ),
        )

        if mote_size > 1:
            pygame.draw.rect(
                effect_surface,
                (*trail_color, alpha // 2),
                (mote_x, mote_y + mote_size, 1, 2),
            )

    surface.blit(effect_surface, (left, top))


def _draw_assassin_invisibility_effect(
    surface,
    left,
    top,
    current_time,
    identity_seed,
):
    margin = 7
    effect_size = ACT_THREE_TILE_SIZE + margin * 2
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    center_x = margin + ACT_THREE_TILE_SIZE // 2
    center_y = margin + ACT_THREE_TILE_SIZE // 2 - 5

    for spark_index in range(5):
        phase = (
            current_time / 1050
            + spark_index * math.tau / 5
            + (identity_seed % 127) / 127
        )
        spark_x = center_x + round(math.cos(phase) * 27)
        spark_y = center_y + round(math.sin(phase) * 22)
        pulse = (math.sin(phase * 1.7) + 1) / 2
        spark_alpha = round(115 + pulse * 80)
        pygame.draw.circle(
            effect_surface,
            (35, 92, 164, spark_alpha // 3),
            (spark_x, spark_y),
            3,
        )
        pygame.draw.circle(
            effect_surface,
            (105, 195, 255, spark_alpha),
            (spark_x, spark_y),
            1,
        )

    surface.blit(
        effect_surface,
        (left - margin, top - margin),
    )


def _draw_berserker_rage_effect(
    surface,
    left,
    top,
    current_time,
    rage_stage,
):
    if rage_stage <= 0:
        return

    margin = 9
    effect_size = ACT_THREE_TILE_SIZE + margin * 2
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    pulse = (math.sin(current_time * 0.012) + 1) / 2
    center_x = effect_size // 2
    center_y = margin + ACT_THREE_TILE_SIZE // 2
    aura_alpha = round(
        (34 if rage_stage == 1 else 58) + pulse * 24
    )
    aura_rect = pygame.Rect(
        margin + (7 if rage_stage == 1 else 3),
        margin + (5 if rage_stage == 1 else 1),
        ACT_THREE_TILE_SIZE - (14 if rage_stage == 1 else 6),
        ACT_THREE_TILE_SIZE - (10 if rage_stage == 1 else 2),
    )
    pygame.draw.ellipse(
        effect_surface,
        (188, 25, 21, aura_alpha),
        aura_rect,
        width=2,
    )
    pygame.draw.ellipse(
        effect_surface,
        (105, 9, 12, aura_alpha // 2),
        aura_rect.inflate(8, 5),
        width=3,
    )

    particle_count = 3 if rage_stage == 1 else 6
    for particle_index in range(particle_count):
        phase = (
            current_time / (980 if rage_stage == 1 else 720)
            + particle_index / particle_count
        ) % 1
        side = -1 if particle_index % 2 == 0 else 1
        drift = math.sin(
            phase * math.tau + particle_index * 1.7
        )
        particle_x = round(
            center_x
            + side * (16 + particle_index % 3 * 5)
            + drift * 3
        )
        particle_y = round(
            margin + ACT_THREE_TILE_SIZE - 7 - phase * 49
        )
        visibility = math.sin(math.pi * phase)
        particle_alpha = round(
            (130 if rage_stage == 1 else 205) * visibility
        )
        pygame.draw.circle(
            effect_surface,
            (218, 34, 25, particle_alpha // 3),
            (particle_x, particle_y),
            3 if rage_stage == 1 else 4,
        )
        pygame.draw.circle(
            effect_surface,
            (255, 74, 43, particle_alpha),
            (particle_x, particle_y),
            1 if rage_stage == 1 else 2,
        )

    surface.blit(
        effect_surface,
        (left - margin, top - margin),
    )


def _draw_berserker_last_rage_effect(
    surface,
    left,
    top,
    current_time,
):
    margin = 13
    effect_size = ACT_THREE_TILE_SIZE + margin * 2
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    center = (
        effect_size // 2,
        margin + ACT_THREE_TILE_SIZE // 2,
    )
    pulse = (math.sin(current_time * 0.016) + 1) / 2

    for ring_index in range(3):
        ring_inset = ring_index * 5
        ring_rect = pygame.Rect(
            margin - 5 + ring_inset,
            margin - 7 + ring_inset,
            ACT_THREE_TILE_SIZE + 10 - ring_inset * 2,
            ACT_THREE_TILE_SIZE + 12 - ring_inset * 2,
        )
        pygame.draw.ellipse(
            effect_surface,
            (
                225,
                24 + ring_index * 8,
                18,
                round(42 + pulse * 35),
            ),
            ring_rect,
            width=2,
        )

    rotation = current_time * 0.004
    for particle_index in range(8):
        angle = rotation + particle_index * math.tau / 8
        radius_x = 31 + math.sin(angle * 1.7) * 4
        radius_y = 27 + math.cos(angle * 1.4) * 3
        particle_x = round(
            center[0] + math.cos(angle) * radius_x
        )
        particle_y = round(
            center[1] + math.sin(angle) * radius_y
        )
        particle_alpha = round(175 + pulse * 70)
        pygame.draw.circle(
            effect_surface,
            (255, 35, 20, particle_alpha // 3),
            (particle_x, particle_y),
            4,
        )
        pygame.draw.circle(
            effect_surface,
            (255, 105, 55, particle_alpha),
            (particle_x, particle_y),
            2,
        )

    vertical_alpha = round(34 + pulse * 28)
    pygame.draw.line(
        effect_surface,
        (255, 28, 18, vertical_alpha),
        (center[0], margin - 2),
        (center[0], effect_size - margin + 2),
        width=3,
    )
    surface.blit(
        effect_surface,
        (left - margin, top - margin),
    )


def _draw_paladin_holy_hand_glow(
    surface,
    sprite,
    left,
    top,
    elapsed,
):
    progress = min(
        1,
        max(0, elapsed / PALADIN_HOLY_HAND_EFFECT_MS),
    )
    visibility = math.sin(math.pi * progress)
    if visibility <= 0:
        return

    glow_alpha = round(185 * visibility)
    mask = pygame.mask.from_surface(sprite)
    glow = mask.to_surface(
        setcolor=(255, 211, 82, glow_alpha),
        unsetcolor=(0, 0, 0, 0),
    )
    radius = 2 + round(2 * visibility)
    for offset_x, offset_y in (
        (-radius, 0),
        (radius, 0),
        (0, -radius),
        (0, radius),
        (-radius, -radius),
        (radius, -radius),
        (-radius, radius),
        (radius, radius),
    ):
        surface.blit(
            glow,
            (left + offset_x, top + offset_y),
        )

    effect_surface = pygame.Surface(
        (
            ACT_THREE_TILE_SIZE + 20,
            ACT_THREE_TILE_SIZE + 20,
        ),
        pygame.SRCALPHA,
    )
    pulse = (math.sin(elapsed * 0.025) + 1) / 2
    pygame.draw.ellipse(
        effect_surface,
        (
            255,
            220,
            104,
            round((55 + pulse * 55) * visibility),
        ),
        (4, 5, ACT_THREE_TILE_SIZE + 12, ACT_THREE_TILE_SIZE + 8),
        width=2,
    )
    for spark_index in range(7):
        phase = (
            progress * 1.7
            + spark_index / 7
        ) % 1
        angle = (
            spark_index * math.tau / 7
            + elapsed * 0.004
        )
        spark_x = (
            10
            + ACT_THREE_TILE_SIZE // 2
            + round(math.cos(angle) * (24 + 3 * pulse))
        )
        spark_y = (
            10
            + ACT_THREE_TILE_SIZE
            - round(phase * 52)
        )
        spark_alpha = round(
            220
            * math.sin(math.pi * phase)
            * visibility
        )
        pygame.draw.circle(
            effect_surface,
            (255, 231, 139, spark_alpha),
            (spark_x, spark_y),
            2,
        )
    surface.blit(
        effect_surface,
        (left - 10, top - 10),
    )


def _draw_paladin_holy_shield_aura(
    surface,
    sprite,
    left,
    top,
    current_time,
):
    margin = 13
    effect_size = ACT_THREE_TILE_SIZE + margin * 2
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    pulse = (math.sin(current_time * 0.009) + 1) / 2
    center = (
        effect_size // 2,
        margin + ACT_THREE_TILE_SIZE // 2,
    )

    for ring_index in range(3):
        inset = ring_index * 4
        pygame.draw.ellipse(
            effect_surface,
            (
                255,
                214 + ring_index * 8,
                96 + ring_index * 28,
                round((75 - ring_index * 16) + pulse * 35),
            ),
            (
                3 + inset,
                1 + inset,
                effect_size - 6 - inset * 2,
                effect_size - 2 - inset * 2,
            ),
            width=2,
        )

    pygame.draw.line(
        effect_surface,
        (255, 238, 164, round(45 + pulse * 45)),
        (center[0], margin - 5),
        (center[0], effect_size - margin + 5),
        width=2,
    )
    for particle_index in range(8):
        angle = (
            current_time * 0.0028
            + particle_index * math.tau / 8
        )
        particle_x = round(
            center[0] + math.cos(angle) * 31
        )
        particle_y = round(
            center[1] + math.sin(angle) * 27
        )
        particle_alpha = round(145 + pulse * 90)
        pygame.draw.circle(
            effect_surface,
            (255, 226, 120, particle_alpha // 3),
            (particle_x, particle_y),
            4,
        )
        pygame.draw.circle(
            effect_surface,
            (255, 244, 196, particle_alpha),
            (particle_x, particle_y),
            1,
        )

    surface.blit(
        effect_surface,
        (left - margin, top - margin),
    )

    mask = pygame.mask.from_surface(sprite)
    outline = mask.to_surface(
        setcolor=(255, 218, 105, round(70 + pulse * 45)),
        unsetcolor=(0, 0, 0, 0),
    )
    for offset in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        surface.blit(
            outline,
            (left + offset[0], top + offset[1]),
        )


def get_act_three_cell_from_position(game_state, game_position):
    mouse_x, mouse_y = game_position
    if not (
        ACT_THREE_VIEW_X <= mouse_x < ACT_THREE_VIEW_X + ACT_THREE_VIEW_WIDTH
        and ACT_THREE_VIEW_Y <= mouse_y < ACT_THREE_VIEW_Y + ACT_THREE_VIEW_HEIGHT
    ):
        return None

    camera_x, camera_y = _camera_position(game_state.floor)
    column = (
        mouse_x - ACT_THREE_VIEW_X + camera_x
    ) // ACT_THREE_TILE_SIZE
    row = (
        mouse_y - ACT_THREE_VIEW_Y + camera_y
    ) // ACT_THREE_TILE_SIZE
    return (column, row)


def _draw_assassin_ultimate_effect(
    surface,
    origin_position,
    target_position,
    current_time,
    started_at,
    identity_seed,
):
    elapsed = current_time - started_at
    if not 0 <= elapsed < ASSASSIN_ULTIMATE_STEP_MS:
        return

    progress = elapsed / ASSASSIN_ULTIMATE_STEP_MS
    visibility = math.sin(math.pi * progress)
    origin = (
        origin_position[0] + ACT_THREE_TILE_SIZE // 2,
        origin_position[1] + ACT_THREE_TILE_SIZE // 2,
    )
    target = (
        target_position[0] + ACT_THREE_TILE_SIZE // 2,
        target_position[1] + ACT_THREE_TILE_SIZE // 2,
    )
    effect_surface = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    trail_end = (
        round(origin[0] + (target[0] - origin[0]) * min(1, progress * 1.35)),
        round(origin[1] + (target[1] - origin[1]) * min(1, progress * 1.35)),
    )
    alpha = round(220 * visibility)
    pygame.draw.line(
        effect_surface,
        (72, 155, 255, alpha // 3),
        origin,
        trail_end,
        width=9,
    )
    pygame.draw.line(
        effect_surface,
        (170, 225, 255, alpha),
        origin,
        trail_end,
        width=2,
    )
    for spark_index in range(4):
        phase = (
            progress * math.tau * 2
            + spark_index * math.tau / 4
            + (identity_seed % 31) / 31
        )
        spark_progress = min(1, progress * 1.4)
        spark_x = round(
            origin[0]
            + (target[0] - origin[0]) * spark_progress
            + math.cos(phase) * 8
        )
        spark_y = round(
            origin[1]
            + (target[1] - origin[1]) * spark_progress
            + math.sin(phase) * 8
        )
        pygame.draw.circle(
            effect_surface,
            (115, 205, 255, alpha),
            (spark_x, spark_y),
            2,
        )

    surface.blit(effect_surface, (0, 0))


def _draw_teleport_effect(
    surface,
    position,
    current_time,
    started_at,
    identity_seed,
):
    elapsed = current_time - started_at
    if not 0 <= elapsed < _TELEPORT_EFFECT_DURATION_MS:
        return

    margin = 18
    effect_size = ACT_THREE_TILE_SIZE + margin * 2
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    center = (effect_size // 2, effect_size // 2)
    progress = elapsed / _TELEPORT_EFFECT_DURATION_MS
    pulse = math.sin(math.pi * progress)
    radius = round(12 + progress * 23)
    alpha = round(210 * pulse)
    pygame.draw.circle(
        effect_surface,
        (40, 92, 185, alpha // 3),
        center,
        radius,
        width=5,
    )
    pygame.draw.circle(
        effect_surface,
        (115, 205, 255, alpha),
        center,
        max(4, radius - 6),
        width=2,
    )

    for spark_index in range(6):
        angle = (
            spark_index * math.tau / 6
            + progress * math.tau * 1.5
            + (identity_seed % 17) / 17
        )
        inner_radius = max(3, radius - 8)
        outer_radius = radius + 5 + spark_index % 3 * 3
        start = (
            center[0] + round(math.cos(angle) * inner_radius),
            center[1] + round(math.sin(angle) * inner_radius),
        )
        end = (
            center[0] + round(math.cos(angle) * outer_radius),
            center[1] + round(math.sin(angle) * outer_radius),
        )
        pygame.draw.line(
            effect_surface,
            (102, 190, 255, alpha),
            start,
            end,
            width=2,
        )

    surface.blit(
        effect_surface,
        (position[0] - margin, position[1] - margin),
    )


def _draw_warlock_idle_flashes(
    surface,
    left,
    top,
    current_time,
    identity_seed,
):
    margin = 8
    effect_surface = pygame.Surface(
        (
            ACT_THREE_TILE_SIZE + margin * 2,
            ACT_THREE_TILE_SIZE + margin * 2,
        ),
        pygame.SRCALPHA,
    )
    anchors = (
        (14, 14),
        (58, 24),
        (18, 43),
        (52, 47),
    )

    for flash_index, (anchor_x, anchor_y) in enumerate(
        anchors
    ):
        phase = (
            current_time / 1900
            + flash_index * 0.27
            + (identity_seed % 113) / 113
        ) % 1

        if phase > 0.30:
            continue

        flash_progress = phase / 0.30
        visibility = math.sin(math.pi * flash_progress)
        alpha = round(190 * visibility)
        drift = round(
            math.sin(
                flash_progress * math.pi
                + flash_index
            )
            * 3
        )
        start = (
            margin + anchor_x + drift,
            margin + anchor_y - round(flash_progress * 5),
        )
        points = (
            start,
            (start[0] - 3, start[1] - 4),
            (start[0] + 2, start[1] - 7),
            (start[0], start[1] - 11),
        )
        pygame.draw.lines(
            effect_surface,
            (84, 29, 145, alpha // 3),
            False,
            points,
            3,
        )
        pygame.draw.lines(
            effect_surface,
            (192, 99, 255, alpha),
            False,
            points,
            1,
        )
        pygame.draw.circle(
            effect_surface,
            (218, 143, 255, alpha),
            start,
            1,
        )

    surface.blit(
        effect_surface,
        (left - margin, top - margin),
    )


def _draw_warlock_demon_aura(
    surface,
    left,
    top,
    current_time,
):
    margin = 9
    effect_surface = pygame.Surface(
        (
            ACT_THREE_TILE_SIZE + margin * 2,
            ACT_THREE_TILE_SIZE + margin * 2,
        ),
        pygame.SRCALPHA,
    )
    pulse = 0.5 + 0.5 * math.sin(current_time / 420)
    outer_alpha = round(34 + pulse * 18)
    inner_alpha = round(54 + pulse * 22)
    pygame.draw.ellipse(
        effect_surface,
        (92, 24, 190, outer_alpha),
        (margin + 3, margin + 3, 58, 58),
        width=4,
    )
    pygame.draw.ellipse(
        effect_surface,
        (190, 54, 255, inner_alpha),
        (margin + 8, margin + 7, 48, 52),
        width=2,
    )
    pygame.draw.circle(
        effect_surface,
        (210, 86, 255, round(42 + pulse * 18)),
        (margin + 32, margin + 47),
        4,
    )
    surface.blit(
        effect_surface,
        (left - margin, top - margin),
    )


def _draw_warlock_demon_overlay(
    surface,
    assets,
    current_time,
):
    overlay = pygame.Surface(
        (ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT),
        pygame.SRCALPHA,
    )
    pulse = 0.5 + 0.5 * math.sin(current_time / 520)
    overlay.fill((8, 2, 18, round(38 + pulse * 14)))
    left_edge = assets["warlock_demon_edge_left"].copy()
    right_edge = assets["warlock_demon_edge_right"].copy()
    edge_alpha = round(218 + pulse * 25)
    left_edge.set_alpha(edge_alpha)
    right_edge.set_alpha(edge_alpha)
    overlay.blit(left_edge, (0, 0))
    overlay.blit(
        right_edge,
        (ACT_THREE_VIEW_WIDTH - right_edge.get_width(), 0),
    )
    surface.blit(overlay, (0, 0))


def _draw_summoner_idle_lights(
    surface,
    left,
    top,
    current_time,
    identity_seed,
):
    margin = 7
    effect_surface = pygame.Surface(
        (
            ACT_THREE_TILE_SIZE + margin * 2,
            ACT_THREE_TILE_SIZE + margin * 2,
        ),
        pygame.SRCALPHA,
    )
    center_x = margin + ACT_THREE_TILE_SIZE // 2
    center_y = margin + ACT_THREE_TILE_SIZE // 2 - 5

    for light_index in range(5):
        phase = (
            current_time / 1050
            + light_index * math.tau / 5
            + (identity_seed % 127) / 127
        )
        light_x = center_x + round(math.cos(phase) * 27)
        light_y = center_y + round(math.sin(phase) * 22)
        pulse = (math.sin(phase * 1.7) + 1) / 2
        alpha = round(115 + pulse * 80)
        pygame.draw.circle(
            effect_surface,
            (35, 126, 137, alpha // 3),
            (light_x, light_y),
            3,
        )
        pygame.draw.circle(
            effect_surface,
            (105, 229, 231, alpha),
            (light_x, light_y),
            1,
        )

    surface.blit(
        effect_surface,
        (left - margin, top - margin),
    )


def _draw_sentinel_vulnerable_side(
    surface,
    enemy,
    left,
    top,
):
    if (
        enemy.type != "sentinel"
        or enemy.shield_turns <= 0
        or enemy.shield_direction is None
    ):
        return

    vulnerable_direction = (
        -enemy.shield_direction[0],
        -enemy.shield_direction[1],
    )
    inset = 7
    edge_offset = 4
    opening_lines = {
        (0, -1): (
            (left + inset, top + edge_offset),
            (
                left + ACT_THREE_TILE_SIZE - inset,
                top + edge_offset,
            ),
        ),
        (0, 1): (
            (
                left + inset,
                top + ACT_THREE_TILE_SIZE - edge_offset,
            ),
            (
                left + ACT_THREE_TILE_SIZE - inset,
                top + ACT_THREE_TILE_SIZE - edge_offset,
            ),
        ),
        (-1, 0): (
            (left + edge_offset, top + inset),
            (
                left + edge_offset,
                top + ACT_THREE_TILE_SIZE - inset,
            ),
        ),
        (1, 0): (
            (
                left + ACT_THREE_TILE_SIZE - edge_offset,
                top + inset,
            ),
            (
                left + ACT_THREE_TILE_SIZE - edge_offset,
                top + ACT_THREE_TILE_SIZE - inset,
            ),
        ),
    }
    opening_line = opening_lines.get(
        vulnerable_direction
    )

    if opening_line is not None:
        pygame.draw.line(
            surface,
            (235, 185, 75),
            opening_line[0],
            opening_line[1],
            3,
        )


def _get_torch_light_surface():
    global _TORCH_LIGHT_SURFACE

    if _TORCH_LIGHT_SURFACE is not None:
        return _TORCH_LIGHT_SURFACE

    radius = 112
    light_surface = pygame.Surface(
        (radius * 2, radius * 2)
    )
    light_surface.fill((0, 0, 0))

    for current_radius in range(radius, 0, -2):
        proximity = 1 - current_radius / radius
        intensity = proximity**1.8
        color = (
            round(35 * intensity),
            round(17 * intensity),
            round(5 * intensity),
        )
        pygame.draw.circle(
            light_surface,
            color,
            (radius, radius),
            current_radius,
        )

    _TORCH_LIGHT_SURFACE = light_surface
    return _TORCH_LIGHT_SURFACE


def _draw_act_three_world(
    screen,
    game_state,
    assets,
    current_time,
):
    floor = game_state.floor
    dungeon_map = floor.map
    view_surface = pygame.Surface(
        (ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT)
    )
    view_surface.fill((5, 5, 8))
    camera_x, camera_y = _camera_position(floor)
    teleport_origin = game_state.player.teleport_camera_origin
    transition_started_at = (
        game_state.player.teleport_transition_started_at
    )
    if teleport_origin is not None and transition_started_at:
        transition_elapsed = current_time - transition_started_at
        if transition_elapsed < _TELEPORT_CAMERA_DURATION_MS:
            transition_progress = transition_elapsed / _TELEPORT_CAMERA_DURATION_MS
            transition_progress = (
                transition_progress
                * transition_progress
                * (3 - 2 * transition_progress)
            )
            start_camera = _camera_position(floor, teleport_origin)
            camera_x = round(
                start_camera[0]
                + (camera_x - start_camera[0]) * transition_progress
            )
            camera_y = round(
                start_camera[1]
                + (camera_y - start_camera[1]) * transition_progress
            )
    exchange_player_origin = (
        game_state.player.warlock_soul_exchange_player_origin
    )
    exchange_enemy_origin = (
        game_state.player.warlock_soul_exchange_enemy_origin
    )
    exchange_enemy_name = (
        game_state.player.warlock_soul_exchange_enemy_name
    )
    exchange_started_at = (
        game_state.player.warlock_soul_exchange_started_at
    )
    exchange_elapsed = current_time - exchange_started_at
    exchange_active = (
        game_state.player.subclass == "warlock"
        and exchange_player_origin is not None
        and exchange_enemy_origin is not None
        and exchange_enemy_name is not None
        and exchange_started_at > 0
        and 0
        <= exchange_elapsed
        < WARLOCK_SOUL_EXCHANGE_TRAVEL_MS
    )
    exchange_progress = min(
        1,
        max(
            0,
            exchange_elapsed
            / WARLOCK_SOUL_EXCHANGE_TRAVEL_MS,
        ),
    )
    exchange_eased_progress = (
        exchange_progress
        * exchange_progress
        * (3 - 2 * exchange_progress)
    )
    first_column = max(0, camera_x // ACT_THREE_TILE_SIZE)
    first_row = max(0, camera_y // ACT_THREE_TILE_SIZE)
    last_column = min(
        len(dungeon_map[0]),
        math.ceil(
            (camera_x + ACT_THREE_VIEW_WIDTH)
            / ACT_THREE_TILE_SIZE
        ),
    )
    last_row = min(
        len(dungeon_map),
        math.ceil(
            (camera_y + ACT_THREE_VIEW_HEIGHT)
            / ACT_THREE_TILE_SIZE
        ),
    )

    for row in range(first_row, last_row):
        for column in range(first_column, last_column):
            tile_position = _view_position(
                column,
                row,
                camera_x,
                camera_y,
            )

            if dungeon_map[row][column] == "#":
                if _is_exposed_top_wall(
                    dungeon_map,
                    column,
                    row,
                ):
                    view_surface.blit(
                        assets[
                            _wall_top_sprite_name(
                                dungeon_map,
                                column,
                                row,
                                floor.visual_seed,
                            )
                        ],
                        tile_position,
                    )
                continue

            view_surface.blit(
                assets[
                    _floor_sprite_name(
                        column,
                        row,
                        floor.visual_seed,
                    )
                ],
                tile_position,
            )
            _draw_floor_boundaries(
                view_surface,
                assets,
                dungeon_map,
                column,
                row,
                tile_position,
            )

    for row in range(first_row, last_row):
        for column in range(first_column, last_column):
            corner_names = _top_void_corner_sprite_names(
                dungeon_map,
                column,
                row,
            )
            if not corner_names:
                continue

            corner_x, corner_y = _view_position(
                column,
                row,
                camera_x,
                camera_y,
            )
            uses_double_corner = len(corner_names) == 2

            for corner_name in corner_names:
                corner_sprite = assets[corner_name]
                source_area = None
                source_x = 0

                if uses_double_corner:
                    if corner_name == "wall_corner_top_left":
                        source_x = 0
                    else:
                        source_x = (
                            corner_sprite.get_width()
                            - _TOP_VOID_DOUBLE_CORNER_CROP_WIDTH
                        )
                    source_area = pygame.Rect(
                        source_x,
                        0,
                        _TOP_VOID_DOUBLE_CORNER_CROP_WIDTH,
                        corner_sprite.get_height(),
                    )

                view_surface.blit(
                    corner_sprite,
                    (
                        corner_x
                        + _TOP_VOID_CORNER_X_OFFSETS.get(
                            corner_name,
                            0,
                        )
                        + source_x,
                        corner_y + _TOP_VOID_CORNER_Y_OFFSET,
                    ),
                    source_area,
                )

    _draw_archer_barrage_zone_cells(
        view_surface,
        assets["archer_barrage_zone_cell"],
        game_state.player.archer_barrage_zone_cells,
        camera_x,
        camera_y,
        current_time,
    )
    if game_state.player.archer_barrage_zone_aiming:
        _draw_archer_barrage_zone_cells(
            view_surface,
            assets["archer_barrage_zone_cell"],
            game_state.player.archer_barrage_zone_preview_cells,
            camera_x,
            camera_y,
            current_time,
            preview=True,
        )
    if game_state.player.berserker_crushing_leap_aiming:
        _draw_archer_barrage_zone_cells(
            view_surface,
            assets["berserker_crushing_leap_area"],
            game_state.player.berserker_crushing_leap_preview_cells,
            camera_x,
            camera_y,
            current_time,
            preview=True,
        )
    if game_state.player.paladin_shield_charge_aiming:
        _draw_tile_markers(
            view_surface,
            game_state.player.paladin_shield_charge_preview_cells,
            camera_x,
            camera_y,
            (241, 192, 70),
        )
    berserker_impact_elapsed = (
        current_time
        - game_state.player.berserker_crushing_leap_started_at
    )
    if (
        game_state.player.berserker_crushing_leap_origin is not None
        and (
            BERSERKER_CRUSHING_LEAP_TRAVEL_MS
            <= berserker_impact_elapsed
            < (
                BERSERKER_CRUSHING_LEAP_TRAVEL_MS
                + BERSERKER_CRUSHING_LEAP_IMPACT_MS
            )
        )
    ):
        _draw_archer_barrage_zone_cells(
            view_surface,
            assets["berserker_crushing_leap_area"],
            game_state.player.berserker_crushing_leap_preview_cells,
            camera_x,
            camera_y,
            current_time,
        )

    attack_positions = [
        position
        for enemy in floor.enemies
        if enemy.health > 0
        for position in enemy.attack_targets
    ]
    _draw_tile_markers(
        view_surface,
        attack_positions,
        camera_x,
        camera_y,
        (190, 48, 45),
    )
    _draw_tile_markers(
        view_surface,
        game_state.player_attack_targets,
        camera_x,
        camera_y,
        (210, 152, 42),
    )

    living_enemies = [
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
    ]
    healing_aura_seeds = {}

    for enemy in living_enemies:
        heal_target = enemy.heal_target

        if (
            enemy.type == "priest"
            and enemy.behavior_state
            is EnemyBehaviorState.PREPARING_HEAL
            and heal_target is not None
            and heal_target.health > 0
        ):
            link_seed = (
                floor.visual_seed
                ^ _stable_text_seed(
                    f"heal:{enemy.name}:{heal_target.name}"
                )
            )
            healing_aura_seeds[id(enemy)] = link_seed
            healing_aura_seeds[id(heal_target)] = (
                link_seed ^ 0x9E3779B9
            )

    stairs_sprite = (
        assets["stairs_open"]
        if not living_enemies
        else assets["stairs_locked"]
    )
    view_surface.blit(
        stairs_sprite,
        _view_position(
            floor.stairs_column,
            floor.stairs_row,
            camera_x,
            camera_y,
        ),
    )

    for potion in floor.potions:
        view_surface.blit(
            assets["potion"],
            _view_position(
                potion.column,
                potion.row,
                camera_x,
                camera_y,
            ),
        )

    for chest in floor.chests:
        sprite_name = (
            "chest_open" if chest.is_open else "chest_closed"
        )
        chest_position = _view_position(
            chest.column,
            chest.row,
            camera_x,
            camera_y,
        )
        view_surface.blit(assets[sprite_name], chest_position)

        if chest.loot_available:
            view_surface.blit(assets["coin"], chest_position)

    for column, row in floor.dropped_keys:
        view_surface.blit(
            assets["key"],
            _view_position(
                column,
                row,
                camera_x,
                camera_y,
            ),
        )

    for column, row in floor.torches:
        view_surface.blit(
            assets["torch_base"],
            _view_position(
                column,
                row,
                camera_x,
                camera_y,
            ),
        )

    for enemy in living_enemies:
        aura_seed = healing_aura_seeds.get(id(enemy))

        if aura_seed is None:
            continue

        aura_position = _view_position(
            enemy.column,
            enemy.row,
            camera_x,
            camera_y,
        )
        _draw_healing_aura(
            view_surface,
            aura_position[0],
            aura_position[1],
            current_time,
            aura_seed,
        )

    for enemy in sorted(
        living_enemies,
        key=lambda living_enemy: living_enemy.row,
    ):
        enemy_position = _view_position(
            enemy.column,
            enemy.row,
            camera_x,
            camera_y,
        )
        if (
            exchange_active
            and enemy.name == exchange_enemy_name
        ):
            exchange_enemy_start = _view_position(
                exchange_enemy_origin[0],
                exchange_enemy_origin[1],
                camera_x,
                camera_y,
            )
            exchange_enemy_end = _view_position(
                exchange_player_origin[0],
                exchange_player_origin[1],
                camera_x,
                camera_y,
            )
            enemy_position = (
                round(
                    exchange_enemy_start[0]
                    + (
                        exchange_enemy_end[0]
                        - exchange_enemy_start[0]
                    )
                    * exchange_eased_progress
                ),
                round(
                    exchange_enemy_start[1]
                    + (
                        exchange_enemy_end[1]
                        - exchange_enemy_start[1]
                    )
                    * exchange_eased_progress
                ),
            )
        enemy_sprite = _enemy_sprite(
            assets,
            enemy,
            current_time,
            floor.visual_seed,
        )
        if enemy.curse_turns > 0:
            _draw_warlock_curse_aura(
                view_surface,
                enemy_position[0],
                enemy_position[1],
                current_time,
                floor.visual_seed
                ^ _stable_text_seed(
                    f"curse:{enemy.name}"
                ),
            )
        if (
            exchange_active
            and enemy.name == exchange_enemy_name
        ):
            _draw_warlock_curse_aura(
                view_surface,
                enemy_position[0],
                enemy_position[1],
                current_time,
                floor.visual_seed
                ^ _stable_text_seed(
                    f"exchange:enemy:{enemy.name}"
                ),
            )
        view_surface.blit(enemy_sprite, enemy_position)
        _draw_sentinel_vulnerable_side(
            view_surface,
            enemy,
            enemy_position[0],
            enemy_position[1],
        )

        if enemy.is_aggro:
            pygame.draw.rect(
                view_surface,
                DANGER_BORDER_COLOR,
                (
                    enemy_position[0] + 3,
                    enemy_position[1] + 3,
                    ACT_THREE_TILE_SIZE - 6,
                    ACT_THREE_TILE_SIZE - 6,
                ),
                width=2,
                border_radius=5,
            )

        _draw_health_bar(
            view_surface,
            enemy_position[0],
            enemy_position[1],
            enemy.health,
            enemy.max_health,
            HEALTH_BAR_COLOR,
        )

    player_subclass = game_state.player.subclass

    if player_subclass not in (
        "berserker",
        "paladin",
        "assassin",
        "archer",
        "warlock",
        "summoner",
    ):
        player_subclass = "berserker"

    movement_elapsed = (
        current_time
        - game_state.player.movement_animation_started_at
    )
    attack_elapsed = (
        current_time
        - game_state.player.attack_animation_started_at
    )
    leap_origin = game_state.player.archer_leap_origin
    leap_started_at = game_state.player.archer_leap_started_at
    leap_elapsed = current_time - leap_started_at
    leap_active = (
        player_subclass == "archer"
        and leap_origin is not None
        and leap_started_at > 0
        and 0 <= leap_elapsed < ARCHER_LEAP_DURATION_MS
    )
    berserker_leap_origin = (
        game_state.player.berserker_crushing_leap_origin
    )
    berserker_leap_started_at = (
        game_state.player.berserker_crushing_leap_started_at
    )
    berserker_leap_elapsed = (
        current_time - berserker_leap_started_at
    )
    berserker_leap_travel_active = (
        player_subclass == "berserker"
        and berserker_leap_origin is not None
        and berserker_leap_started_at > 0
        and 0
        <= berserker_leap_elapsed
        < BERSERKER_CRUSHING_LEAP_TRAVEL_MS
    )
    berserker_leap_impact_active = (
        player_subclass == "berserker"
        and berserker_leap_origin is not None
        and (
            BERSERKER_CRUSHING_LEAP_TRAVEL_MS
            <= berserker_leap_elapsed
            < (
                BERSERKER_CRUSHING_LEAP_TRAVEL_MS
                + BERSERKER_CRUSHING_LEAP_IMPACT_MS
            )
        )
    )
    shield_charge_origin = (
        game_state.player.paladin_shield_charge_origin
    )
    shield_charge_started_at = (
        game_state.player.paladin_shield_charge_started_at
    )
    shield_charge_elapsed = (
        current_time - shield_charge_started_at
    )
    shield_charge_active = (
        player_subclass == "paladin"
        and shield_charge_origin is not None
        and shield_charge_started_at > 0
        and 0
        <= shield_charge_elapsed
        < PALADIN_SHIELD_CHARGE_TRAVEL_MS
    )
    if shield_charge_active:
        player_sprite = assets[
            "player_paladin_shield_charge"
        ]
    elif berserker_leap_travel_active:
        player_sprite = assets[
            "player_berserker_crushing_leap"
        ]
    elif berserker_leap_impact_active:
        player_sprite = assets[
            "player_berserker_crushing_leap_impact"
        ]
    elif leap_active:
        player_sprite = assets["player_archer_leap"]
    elif (
        player_subclass in (
            "assassin",
            "archer",
            "berserker",
            "paladin",
            "warlock",
            "summoner",
        )
        and 0 <= attack_elapsed < _ATTACK_FRAME_DURATION_MS
    ):
        if (
            player_subclass == "warlock"
            and game_state.player.warlock_demon_form_active
        ):
            player_sprite = assets["player_warlock_demon_attack"]
        else:
            player_sprite = assets[
                f"player_{player_subclass}_attack"
            ]
    elif (
        player_subclass in (
            "assassin",
            "archer",
            "berserker",
            "paladin",
            "warlock",
            "summoner",
        )
        and 0 <= movement_elapsed < (
            _MOVE_FRAME_COUNT * _MOVE_FRAME_DURATION_MS
        )
    ):
        movement_frame = _movement_frame(
            current_time,
            game_state.player.movement_animation_started_at,
        )
        if (
            player_subclass == "warlock"
            and game_state.player.warlock_demon_form_active
        ):
            player_sprite = assets[
                f"player_warlock_demon_walk_{movement_frame}"
            ]
        else:
            player_sprite = assets[
                f"player_{player_subclass}_walk_{movement_frame}"
            ]
    else:
        player_frame = _idle_frame(
            current_time,
            (
                floor.visual_seed
                ^ _stable_text_seed(
                    f"player:{player_subclass}"
                )
            ),
        )
        if (
            player_subclass == "warlock"
            and game_state.player.warlock_demon_form_active
        ):
            player_sprite = assets[
                f"player_warlock_demon_idle_{player_frame}"
            ]
        else:
            player_sprite = assets[
                f"player_{player_subclass}_idle_{player_frame}"
            ]
    player_position = _view_position(
        floor.player_column,
        floor.player_row,
        camera_x,
        camera_y,
    )
    leap_progress = 0.0
    leap_start_position = None
    leap_end_position = player_position
    shield_charge_progress = 0.0
    shield_charge_start_position = None
    if exchange_active:
        exchange_player_start = _view_position(
            exchange_player_origin[0],
            exchange_player_origin[1],
            camera_x,
            camera_y,
        )
        exchange_player_end = _view_position(
            exchange_enemy_origin[0],
            exchange_enemy_origin[1],
            camera_x,
            camera_y,
        )
        player_position = (
            round(
                exchange_player_start[0]
                + (
                    exchange_player_end[0]
                    - exchange_player_start[0]
                )
                * exchange_eased_progress
            ),
            round(
                exchange_player_start[1]
                + (
                    exchange_player_end[1]
                    - exchange_player_start[1]
                )
                * exchange_eased_progress
            ),
        )
    elif shield_charge_active:
        shield_charge_progress = min(
            1,
            shield_charge_elapsed
            / PALADIN_SHIELD_CHARGE_TRAVEL_MS,
        )
        eased_progress = (
            shield_charge_progress
            * shield_charge_progress
            * (3 - 2 * shield_charge_progress)
        )
        shield_charge_start_position = _view_position(
            shield_charge_origin[0],
            shield_charge_origin[1],
            camera_x,
            camera_y,
        )
        player_position = (
            round(
                shield_charge_start_position[0]
                + (
                    leap_end_position[0]
                    - shield_charge_start_position[0]
                )
                * eased_progress
            ),
            round(
                shield_charge_start_position[1]
                + (
                    leap_end_position[1]
                    - shield_charge_start_position[1]
                )
                * eased_progress
            ),
        )
        if floor.player_column < shield_charge_origin[0]:
            player_sprite = pygame.transform.flip(
                player_sprite,
                True,
                False,
            )
    elif leap_active:
        leap_progress = min(
            1,
            leap_elapsed / ARCHER_LEAP_DURATION_MS,
        )
        eased_progress = 1 - (1 - leap_progress) ** 3
        leap_start_position = _view_position(
            leap_origin[0],
            leap_origin[1],
            camera_x,
            camera_y,
        )
        player_position = (
            round(
                leap_start_position[0]
                + (leap_end_position[0] - leap_start_position[0])
                * eased_progress
            ),
            round(
                leap_start_position[1]
                + (leap_end_position[1] - leap_start_position[1])
                * eased_progress
                - math.sin(math.pi * leap_progress) * 8
            ),
        )
    elif berserker_leap_travel_active:
        leap_progress = min(
            1,
            berserker_leap_elapsed
            / BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
        )
        eased_progress = 1 - (1 - leap_progress) ** 3
        leap_start_position = _view_position(
            berserker_leap_origin[0],
            berserker_leap_origin[1],
            camera_x,
            camera_y,
        )
        player_position = (
            round(
                leap_start_position[0]
                + (
                    leap_end_position[0]
                    - leap_start_position[0]
                )
                * eased_progress
            ),
            round(
                leap_start_position[1]
                + (
                    leap_end_position[1]
                    - leap_start_position[1]
                )
                * eased_progress
                - math.sin(math.pi * leap_progress) * 13
            ),
        )
    if player_subclass in ("archer", "assassin"):
        player_sprite = player_sprite.copy()
        light_color = (
            (15, 16, 10)
            if player_subclass == "archer"
            else (10, 12, 18)
        )
        player_sprite.fill(
            light_color,
            special_flags=pygame.BLEND_RGB_ADD,
        )

    if game_state.player.invisibility_turns > 0:
        player_sprite = player_sprite.copy()
        player_sprite.set_alpha(105)
    else:
        player_sprite = player_sprite.copy()
        player_sprite.set_alpha(255)

    if (
        player_subclass == "assassin"
        and game_state.player.ultimate_animation_active
    ):
        ultimate_elapsed_for_player = (
            current_time - game_state.player.ultimate_animation_started_at
        )
        player_sprite = assets["player_assassin_attack"].copy()
        fade_progress = min(1, max(0, ultimate_elapsed_for_player) / 700)
        player_sprite.set_alpha(round(220 * (1 - fade_progress)))

    ultimate_target_enemies = []
    ultimate_step_started_at = 0
    ultimate_elapsed = 0
    if (
        player_subclass == "assassin"
        and game_state.player.ultimate_targets
    ):
        ultimate_target_enemies = [
            enemy
            for target_name in game_state.player.ultimate_targets
            for enemy in floor.enemies
            if enemy.name == target_name
        ]
        if game_state.player.ultimate_animation_active:
            ultimate_elapsed = (
                current_time
                - game_state.player.ultimate_animation_started_at
            )
            ultimate_step_started_at = (
                game_state.player.ultimate_animation_started_at
            )

    if (
        player_subclass == "assassin"
        and game_state.player.invisibility_turns > 0
    ):
        _draw_assassin_invisibility_effect(
            view_surface,
            player_position[0],
            player_position[1],
            current_time,
            floor.visual_seed
            ^ _stable_text_seed("assassin:invisibility"),
        )

    if (
        player_subclass == "berserker"
        and game_state.player.health > 0
    ):
        last_rage_is_active = (
            game_state.player.berserker_last_rage_turns > 0
        )
        if last_rage_is_active:
            _draw_berserker_last_rage_effect(
                view_surface,
                player_position[0],
                player_position[1],
                current_time,
            )
        berserker_health_ratio = (
            game_state.player.health
            / game_state.player.max_health
        )
        if (
            last_rage_is_active
            or berserker_health_ratio
            <= BERSERKER_RAGE_CRITICAL_HEALTH_RATIO
        ):
            berserker_rage_stage = 2
        elif (
            berserker_health_ratio
            <= BERSERKER_RAGE_INJURED_HEALTH_RATIO
        ):
            berserker_rage_stage = 1
        else:
            berserker_rage_stage = 0
        _draw_berserker_rage_effect(
            view_surface,
            player_position[0],
            player_position[1],
            current_time,
            berserker_rage_stage,
        )

    holy_hand_elapsed = (
        current_time
        - game_state.player.paladin_holy_hand_started_at
    )
    if (
        player_subclass == "paladin"
        and game_state.player.paladin_holy_hand_started_at > 0
        and 0
        <= holy_hand_elapsed
        < PALADIN_HOLY_HAND_EFFECT_MS
    ):
        _draw_paladin_holy_hand_glow(
            view_surface,
            player_sprite,
            player_position[0],
            player_position[1],
            holy_hand_elapsed,
        )

    if (
        player_subclass == "paladin"
        and game_state.player.paladin_holy_shield_turns > 0
    ):
        _draw_paladin_holy_shield_aura(
            view_surface,
            player_sprite,
            player_position[0],
            player_position[1],
            current_time,
        )

    if exchange_active:
        _draw_warlock_curse_aura(
            view_surface,
            player_position[0],
            player_position[1],
            current_time,
            floor.visual_seed
            ^ _stable_text_seed("exchange:warlock"),
        )

    if leap_active and leap_start_position is not None:
        for lag, alpha in (
            (0.12, 105),
            (0.24, 65),
            (0.36, 30),
        ):
            ghost_progress = max(0, leap_progress - lag)
            ghost_eased_progress = 1 - (1 - ghost_progress) ** 3
            ghost_position = (
                round(
                    leap_start_position[0]
                    + (
                        leap_end_position[0]
                        - leap_start_position[0]
                    )
                    * ghost_eased_progress
                ),
                round(
                    leap_start_position[1]
                    + (
                        leap_end_position[1]
                        - leap_start_position[1]
                    )
                    * ghost_eased_progress
                    - math.sin(math.pi * ghost_progress) * 8
                ),
            )
            ghost_sprite = player_sprite.copy()
            ghost_sprite.fill(
                (15, 55, 35),
                special_flags=pygame.BLEND_RGB_ADD,
            )
            ghost_sprite.set_alpha(alpha)
            view_surface.blit(ghost_sprite, ghost_position)

    if (
        berserker_leap_travel_active
        and leap_start_position is not None
    ):
        for lag, alpha in (
            (0.10, 125),
            (0.21, 78),
            (0.32, 38),
        ):
            ghost_progress = max(0, leap_progress - lag)
            ghost_eased_progress = (
                1 - (1 - ghost_progress) ** 3
            )
            ghost_position = (
                round(
                    leap_start_position[0]
                    + (
                        leap_end_position[0]
                        - leap_start_position[0]
                    )
                    * ghost_eased_progress
                ),
                round(
                    leap_start_position[1]
                    + (
                        leap_end_position[1]
                        - leap_start_position[1]
                    )
                    * ghost_eased_progress
                    - math.sin(math.pi * ghost_progress) * 13
                ),
            )
            ghost_sprite = player_sprite.copy()
            ghost_sprite.fill(
                (62, 10, 8),
                special_flags=pygame.BLEND_RGB_ADD,
            )
            ghost_sprite.set_alpha(alpha)
            view_surface.blit(ghost_sprite, ghost_position)

    if (
        shield_charge_active
        and shield_charge_start_position is not None
    ):
        for lag, alpha in (
            (0.09, 125),
            (0.18, 78),
            (0.28, 38),
        ):
            ghost_progress = max(
                0,
                shield_charge_progress - lag,
            )
            ghost_eased_progress = (
                ghost_progress
                * ghost_progress
                * (3 - 2 * ghost_progress)
            )
            ghost_position = (
                round(
                    shield_charge_start_position[0]
                    + (
                        leap_end_position[0]
                        - shield_charge_start_position[0]
                    )
                    * ghost_eased_progress
                ),
                round(
                    shield_charge_start_position[1]
                    + (
                        leap_end_position[1]
                        - shield_charge_start_position[1]
                    )
                    * ghost_eased_progress
                ),
            )
            ghost_sprite = player_sprite.copy()
            ghost_sprite.fill(
                (72, 49, 8),
                special_flags=pygame.BLEND_RGB_ADD,
            )
            ghost_sprite.set_alpha(alpha)
            view_surface.blit(
                ghost_sprite,
                ghost_position,
            )

    view_surface.blit(player_sprite, player_position)

    active_barrage_shots = []
    for barrage_shot in game_state.player.archer_barrage_shots:
        if barrage_shot.started_at <= 0:
            active_barrage_shots.append(barrage_shot)
            continue

        barrage_elapsed = (
            current_time - barrage_shot.started_at
        )
        if not (
            0
            <= barrage_elapsed
            < _ARCHER_BARRAGE_SHOT_EFFECT_MS
        ):
            continue

        active_barrage_shots.append(barrage_shot)
        barrage_progress = min(
            1,
            barrage_elapsed
            / ARCHER_EMPOWERED_SHOT_PROJECTILE_MS,
        )
        ghost_visibility = math.sin(
            math.pi
            * min(
                1,
                barrage_elapsed
                / _ARCHER_BARRAGE_SHOT_EFFECT_MS,
            )
        )
        ghost_sprite = assets["player_archer_attack"].copy()
        ghost_sprite.fill(
            (18, 75, 42),
            special_flags=pygame.BLEND_RGB_ADD,
        )
        ghost_sprite.set_alpha(
            round(145 * ghost_visibility)
        )
        ghost_position = _view_position(
            barrage_shot.origin[0],
            barrage_shot.origin[1],
            camera_x,
            camera_y,
        )
        view_surface.blit(ghost_sprite, ghost_position)

        if (
            barrage_elapsed
            < ARCHER_EMPOWERED_SHOT_PROJECTILE_MS
        ):
            target_position = _view_position(
                barrage_shot.target[0],
                barrage_shot.target[1],
                camera_x,
                camera_y,
            )
            _draw_archer_projectile(
                view_surface,
                assets["archer_empowered_shot_arrow"],
                (
                    ghost_position[0]
                    + ACT_THREE_TILE_SIZE // 2,
                    ghost_position[1]
                    + ACT_THREE_TILE_SIZE // 2,
                ),
                (
                    target_position[0]
                    + ACT_THREE_TILE_SIZE // 2,
                    target_position[1]
                    + ACT_THREE_TILE_SIZE // 2,
                ),
                barrage_progress,
                empowered=True,
                current_time=current_time,
            )

    game_state.player.archer_barrage_shots = (
        active_barrage_shots
    )

    if (
        player_subclass == "archer"
        and leap_origin is not None
        and leap_started_at > 0
        and leap_elapsed >= ARCHER_LEAP_DURATION_MS
    ):
        game_state.player.archer_leap_origin = None
        game_state.player.archer_leap_started_at = 0
    if (
        player_subclass == "berserker"
        and berserker_leap_origin is not None
        and berserker_leap_started_at > 0
        and berserker_leap_elapsed
        >= (
            BERSERKER_CRUSHING_LEAP_TRAVEL_MS
            + BERSERKER_CRUSHING_LEAP_IMPACT_MS
        )
    ):
        game_state.player.berserker_crushing_leap_origin = None
        game_state.player.berserker_crushing_leap_started_at = 0
        game_state.player.berserker_crushing_leap_preview_cells.clear()
    if (
        player_subclass == "paladin"
        and shield_charge_origin is not None
        and shield_charge_started_at > 0
        and shield_charge_elapsed
        >= PALADIN_SHIELD_CHARGE_TRAVEL_MS
    ):
        game_state.player.paladin_shield_charge_origin = None
        game_state.player.paladin_shield_charge_started_at = 0
    if (
        player_subclass == "warlock"
        and exchange_player_origin is not None
        and exchange_enemy_origin is not None
        and exchange_started_at > 0
        and exchange_elapsed
        >= WARLOCK_SOUL_EXCHANGE_TRAVEL_MS
    ):
        game_state.player.warlock_soul_exchange_player_origin = None
        game_state.player.warlock_soul_exchange_enemy_origin = None
        game_state.player.warlock_soul_exchange_enemy_name = None
        game_state.player.warlock_soul_exchange_started_at = 0

    empowered_target = game_state.player.archer_empowered_shot_target
    empowered_started_at = game_state.player.archer_empowered_shot_started_at
    empowered_elapsed = current_time - empowered_started_at
    ordinary_target = (
        game_state.player_attack_targets[0]
        if game_state.player_attack_targets
        else None
    )
    ordinary_elapsed = current_time - game_state.player.attack_animation_started_at
    if (
        player_subclass == "archer"
        and empowered_target is not None
        and empowered_started_at
        and 0 <= empowered_elapsed < ARCHER_EMPOWERED_SHOT_PROJECTILE_MS
    ):
        target_position = _view_position(
            empowered_target[0],
            empowered_target[1],
            camera_x,
            camera_y,
        )
        origin = (
            player_position[0] + ACT_THREE_TILE_SIZE // 2,
            player_position[1] + ACT_THREE_TILE_SIZE // 2,
        )
        destination = (
            target_position[0] + ACT_THREE_TILE_SIZE // 2,
            target_position[1] + ACT_THREE_TILE_SIZE // 2,
        )
        progress = min(1, empowered_elapsed / ARCHER_EMPOWERED_SHOT_PROJECTILE_MS)
        _draw_archer_projectile(
            view_surface,
            assets["archer_empowered_shot_arrow"],
            origin,
            destination,
            progress,
            empowered=True,
            current_time=current_time,
        )
    elif (
        player_subclass == "archer"
        and empowered_target is not None
        and empowered_started_at
        and empowered_elapsed >= ARCHER_EMPOWERED_SHOT_PROJECTILE_MS
    ):
        game_state.player.archer_empowered_shot_target = None
        game_state.player.archer_empowered_shot_started_at = 0

    if (
        player_subclass == "archer"
        and empowered_target is None
        and ordinary_target is not None
        and 0 <= ordinary_elapsed < _ATTACK_FRAME_DURATION_MS
    ):
        target_position = _view_position(
            ordinary_target[0],
            ordinary_target[1],
            camera_x,
            camera_y,
        )
        origin = (
            player_position[0] + ACT_THREE_TILE_SIZE // 2,
            player_position[1] + ACT_THREE_TILE_SIZE // 2,
        )
        destination = (
            target_position[0] + ACT_THREE_TILE_SIZE // 2,
            target_position[1] + ACT_THREE_TILE_SIZE // 2,
        )
        _draw_archer_projectile(
            view_surface,
            assets["archer_empowered_shot_arrow"],
            origin,
            destination,
            min(1, ordinary_elapsed / _ATTACK_FRAME_DURATION_MS),
        )
    elif (
        player_subclass == "warlock"
        and ordinary_target is not None
        and 0 <= ordinary_elapsed < _ATTACK_FRAME_DURATION_MS
    ):
        target_position = _view_position(
            ordinary_target[0],
            ordinary_target[1],
            camera_x,
            camera_y,
        )
        _draw_warlock_orb(
            view_surface,
            (
                player_position[0] + ACT_THREE_TILE_SIZE // 2,
                player_position[1] + ACT_THREE_TILE_SIZE // 2,
            ),
            (
                target_position[0] + ACT_THREE_TILE_SIZE // 2,
                target_position[1] + ACT_THREE_TILE_SIZE // 2,
            ),
            min(
                1,
                ordinary_elapsed / _ATTACK_FRAME_DURATION_MS,
            ),
            current_time,
        )

    if (
        teleport_origin is not None
        and transition_started_at
    ):
        _draw_teleport_effect(
            view_surface,
            _view_position(
                teleport_origin[0],
                teleport_origin[1],
                camera_x,
                camera_y,
            ),
            current_time,
            transition_started_at,
            floor.visual_seed ^ _stable_text_seed("teleport:origin"),
        )
        _draw_teleport_effect(
            view_surface,
            player_position,
            current_time,
            transition_started_at,
            floor.visual_seed ^ _stable_text_seed("teleport:arrival"),
        )
        if (
            current_time - transition_started_at
            >= _TELEPORT_EFFECT_DURATION_MS
        ):
            game_state.player.teleport_camera_origin = None
            game_state.player.teleport_transition_started_at = 0

    if (
        player_subclass in ("assassin", "archer", "warlock")
        and 0 <= attack_elapsed < _ATTACK_FRAME_DURATION_MS
    ):
        flash_color = {
            "archer": (80, 230, 120),
            "warlock": (195, 70, 245),
            "assassin": (155, 215, 255),
        }[player_subclass]
        for column, row in game_state.player_attack_targets:
            _draw_attack_impact_flash(
                view_surface,
                _view_position(
                    column,
                    row,
                    camera_x,
                    camera_y,
                ),
                current_time,
                game_state.player.attack_animation_started_at,
                flash_color,
            )

    ultimate_target_counts = {}
    for target_name in game_state.player.ultimate_targets:
        ultimate_target_counts[target_name] = (
            ultimate_target_counts.get(target_name, 0) + 1
        )
    if (
        player_subclass == "assassin"
        and (game_state.player.ultimate_aiming
             or game_state.player.ultimate_animation_active)
    ):
        mark_font = pygame.font.Font(None, 22)
        for enemy in floor.enemies:
            mark_count = ultimate_target_counts.get(enemy.name, 0)
            if enemy.health <= 0 or not mark_count:
                continue
            enemy_position = _view_position(
                enemy.column,
                enemy.row,
                camera_x,
                camera_y,
            )
            mark_surface = mark_font.render(
                f"\u00d7{mark_count}",
                True,
                (245, 210, 120),
            )
            mark_rectangle = mark_surface.get_rect(
                midbottom=(
                    enemy_position[0] + ACT_THREE_TILE_SIZE // 2,
                    enemy_position[1] - 3,
                ),
            )
            view_surface.blit(mark_surface, mark_rectangle)

    if (
        player_subclass == "assassin"
        and game_state.player.ultimate_animation_active
        and ultimate_target_enemies
    ):
        impact_elapsed = (
            current_time - game_state.player.ultimate_animation_started_at
        )
        darkness_fade_out_start = (
            ASSASSIN_ULTIMATE_PRELUDE_MS
            + len(ultimate_target_enemies) * ASSASSIN_ULTIMATE_STEP_MS
        )
        fade_in = min(1, impact_elapsed / ASSASSIN_ULTIMATE_PRELUDE_MS)
        fade_out = min(
            1,
            max(0, (impact_elapsed - darkness_fade_out_start)
                / ASSASSIN_ULTIMATE_OUTRO_MS),
        )
        ultimate_darkness = pygame.Surface(
            (ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT),
            pygame.SRCALPHA,
        )
        darkness_alpha = round(110 * fade_in * (1 - fade_out))
        ultimate_darkness.fill((0, 0, 0, darkness_alpha))
        view_surface.blit(ultimate_darkness, (0, 0))

        slash_elapsed = impact_elapsed - ASSASSIN_ULTIMATE_PRELUDE_MS
        if 0 <= slash_elapsed < (
            len(ultimate_target_enemies) * ASSASSIN_ULTIMATE_STEP_MS
        ):
            target_index = min(
                len(ultimate_target_enemies) - 1,
                slash_elapsed // ASSASSIN_ULTIMATE_STEP_MS,
            )
            target_enemy = ultimate_target_enemies[target_index]
            target_position = _view_position(
                target_enemy.column,
                target_enemy.row,
                camera_x,
                camera_y,
            )
            step_elapsed = slash_elapsed % ASSASSIN_ULTIMATE_STEP_MS
            slash_progress = step_elapsed / ASSASSIN_ULTIMATE_STEP_MS
            variant_index = (
                game_state.player.ultimate_visual_variants[target_index]
                if target_index
                < len(game_state.player.ultimate_visual_variants)
                else target_index % 3
            )
            slash_sprite = assets[
                f"assassin_ultimate_slash_{variant_index}"
            ].copy()
            slash_visibility = min(
                1,
                slash_progress * 5,
                (1 - slash_progress) * 5,
            )
            slash_sprite.set_alpha(round(255 * slash_visibility))
            slash_position = (
                target_position[0]
                + ACT_THREE_TILE_SIZE // 2
                - slash_sprite.get_width() // 2,
                target_position[1]
                + ACT_THREE_TILE_SIZE // 2
                - slash_sprite.get_height() // 2,
            )
            view_surface.blit(slash_sprite, slash_position)

    if player_subclass in ("archer", "assassin"):
        _draw_rogue_idle_particles(
            view_surface,
            player_position[0],
            player_position[1],
            current_time,
            (
                floor.visual_seed
                ^ _stable_text_seed(
                    f"player:{player_subclass}:motes"
                )
            ),
            player_subclass,
        )
    elif player_subclass == "warlock":
        if game_state.player.warlock_demon_form_active:
            _draw_warlock_demon_aura(
                view_surface,
                player_position[0],
                player_position[1],
                current_time,
            )
        _draw_warlock_idle_flashes(
            view_surface,
            player_position[0],
            player_position[1],
            current_time,
            (
                floor.visual_seed
                ^ _stable_text_seed(
                    "player:warlock:flashes"
                )
            ),
        )
    elif player_subclass == "summoner":
        _draw_summoner_idle_lights(
            view_surface,
            player_position[0],
            player_position[1],
            current_time,
            (
                floor.visual_seed
                ^ _stable_text_seed(
                    "player:summoner:lights"
                )
            ),
        )

    if (
        player_subclass == "warlock"
        and game_state.player.warlock_demon_form_active
    ):
        _draw_warlock_demon_overlay(
            view_surface,
            assets,
            current_time,
        )

    darkness = pygame.Surface(
        (ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT),
        pygame.SRCALPHA,
    )
    darkness.fill((0, 0, 8, 38))
    view_surface.blit(darkness, (0, 0))
    torch_light = pygame.Surface(
        (ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT)
    )
    torch_light.fill((0, 0, 0))
    light_surface = _get_torch_light_surface()
    light_radius = light_surface.get_width() // 2

    for column, row in floor.torches:
        torch_x, torch_y = _view_position(
            column,
            row,
            camera_x,
            camera_y,
        )
        torch_light.blit(
            light_surface,
            (
                torch_x
                + ACT_THREE_TILE_SIZE // 2
                - light_radius,
                torch_y
                + ACT_THREE_TILE_SIZE // 2
                - light_radius,
            ),
            special_flags=pygame.BLEND_RGB_ADD,
        )

    view_surface.blit(
        torch_light,
        (0, 0),
        special_flags=pygame.BLEND_RGB_ADD,
    )

    for torch_index, (column, row) in enumerate(floor.torches):
        flame_frame = (
            current_time // 145 + torch_index
        ) % 3
        view_surface.blit(
            assets[f"torch_flame_{flame_frame}"],
            _view_position(
                column,
                row,
                camera_x,
                camera_y,
            ),
        )

    screen.blit(
        view_surface,
        (ACT_THREE_VIEW_X, ACT_THREE_VIEW_Y),
    )
    screen.blit(
        assets["gameplay_frame"],
        (ACT_THREE_FRAME_X, ACT_THREE_FRAME_Y),
    )


def _draw_label(surface, font, text, color, position):
    surface.blit(font.render(text, True, color), position)


def get_act_three_sidebar_tab_rectangles():
    tabs_x = ACT_THREE_SIDEBAR_X + 30
    tabs_y = ACT_THREE_SIDEBAR_Y + 118
    tabs_width = ACT_THREE_SIDEBAR_WIDTH - 60
    gap = 6
    tab_width = (tabs_width - gap) // 2

    return {
        "stats": pygame.Rect(tabs_x, tabs_y, tab_width, 30),
        "inventory": pygame.Rect(
            tabs_x + tab_width + gap,
            tabs_y,
            tab_width,
            30,
        ),
    }


def get_act_three_log_panel_rect():
    return pygame.Rect(
        ACT_THREE_SIDEBAR_X + 35,
        ACT_THREE_SIDEBAR_Y + 524,
        ACT_THREE_SIDEBAR_WIDTH - 70,
        90,
    )


def get_act_three_log_arrow_rectangles():
    log_panel = get_act_three_log_panel_rect()
    arrow_size = 18
    return {
        "older": pygame.Rect(
            log_panel.right - arrow_size - 6,
            log_panel.y + 10,
            arrow_size,
            arrow_size,
        ),
        "newer": pygame.Rect(
            log_panel.right - arrow_size - 6,
            log_panel.bottom - arrow_size - 10,
            arrow_size,
            arrow_size,
        ),
    }


def _draw_act_three_sidebar(
    screen,
    game_state,
    fonts,
    assets,
):
    screen.blit(
        assets["sidebar_panel"],
        (ACT_THREE_SIDEBAR_X, ACT_THREE_SIDEBAR_Y),
    )
    player = game_state.player
    content_x = ACT_THREE_SIDEBAR_X + 30
    content_width = ACT_THREE_SIDEBAR_WIDTH - 60
    display_font = fonts["sidebar_display"]
    heading_font = fonts["sidebar_heading"]
    text_font = fonts["sidebar_text"]
    numbers_font = fonts["sidebar_numbers"]
    dim_color = (139, 132, 142)
    muted_border = (70, 63, 76)
    panel_fill = (18, 16, 23)
    subclass_name, accent_color = {
        "paladin": ("PALADIN", (206, 168, 80)),
        "assassin": ("ASSASSIN", (69, 130, 221)),
        "archer": ("ARCHER", (105, 151, 76)),
        "warlock": ("WARLOCK", (176, 91, 232)),
        "summoner": ("SUMMONER", (77, 184, 193)),
        "berserker": ("BERSERKER", (205, 68, 58)),
    }.get(
        player.subclass,
        ("BERSERKER", (205, 68, 58)),
    )

    header_x = ACT_THREE_SIDEBAR_X + 34
    header_y = ACT_THREE_SIDEBAR_Y + 21
    class_surface = display_font.render(
        subclass_name,
        True,
        accent_color,
    )
    screen.blit(class_surface, (header_x, header_y))
    level_x = min(
        header_x + class_surface.get_width() + 12,
        ACT_THREE_SIDEBAR_X + ACT_THREE_SIDEBAR_WIDTH - 66,
    )
    level_label = text_font.render("LVL", True, dim_color)
    level_label_rectangle = level_label.get_rect(
        topleft=(level_x, header_y + 7),
    )
    screen.blit(level_label, level_label_rectangle)
    level_number = numbers_font.render("1", True, TEXT_COLOR)
    screen.blit(
        level_number,
        level_number.get_rect(
            midleft=(
                level_label_rectangle.right + 5,
                level_label_rectangle.centery,
            ),
        ),
    )
    hp_bar_position = (
        ACT_THREE_SIDEBAR_X + 23,
        ACT_THREE_SIDEBAR_Y + 48,
    )
    screen.blit(assets["assassin_hp_bar"], hp_bar_position)
    hp_ratio = max(0, min(1, player.health / player.max_health))
    hp_inner_left = hp_bar_position[0] + 27
    hp_inner_top = hp_bar_position[1] + 14
    hp_inner_width = 204
    hp_inner_height = 14
    missing_hp_rectangle = pygame.Rect(
        hp_inner_left + round(hp_inner_width * hp_ratio),
        hp_inner_top,
        round(hp_inner_width * (1 - hp_ratio)),
        hp_inner_height,
    )
    if missing_hp_rectangle.width > 0:
        pygame.draw.rect(
            screen,
            (42, 20, 27),
            missing_hp_rectangle,
        )
    hp_text = f"HP {player.health}/{player.max_health}"
    hp_surface = numbers_font.render(hp_text, True, TEXT_COLOR)
    screen.blit(
        hp_surface,
        hp_surface.get_rect(
            center=(
                hp_bar_position[0] + 129,
                hp_bar_position[1] + 21,
            ),
        ),
    )

    tab_rectangles = get_act_three_sidebar_tab_rectangles()
    tab_labels = {
        "stats": "Stats",
        "inventory": "Inventory",
    }
    for tab_name, tab_rectangle in tab_rectangles.items():
        is_active = game_state.sidebar_tab == tab_name
        pygame.draw.rect(
            screen,
            (27, 23, 32) if is_active else (16, 14, 20),
            tab_rectangle,
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            accent_color if is_active else muted_border,
            tab_rectangle,
            width=1,
            border_radius=3,
        )
        if is_active:
            pygame.draw.rect(
                screen,
                accent_color,
                (
                    tab_rectangle.x + 8,
                    tab_rectangle.bottom - 3,
                    tab_rectangle.width - 16,
                    2,
                ),
            )

        tab_surface = text_font.render(
            tab_labels[tab_name],
            True,
            TEXT_COLOR if is_active else dim_color,
        )
        screen.blit(
            tab_surface,
            tab_surface.get_rect(center=tab_rectangle.center),
        )

    tab_content_panel = pygame.Rect(
        content_x,
        tab_rectangles["stats"].bottom + 8,
        content_width,
        108,
    )
    pygame.draw.rect(
        screen,
        (12, 11, 16),
        tab_content_panel,
        border_radius=4,
    )
    pygame.draw.rect(
        screen,
        (50, 45, 56),
        tab_content_panel,
        width=1,
        border_radius=4,
    )
    tab_content_top = tab_content_panel.y + 7
    if game_state.sidebar_tab == "inventory":
        inventory = (
            ("sidebar_potion", player.potion_count),
            ("sidebar_coin", player.gold_count),
            ("sidebar_key", player.key_count),
        )
        slot_size = 48
        slot_gap = 10
        grid_width = slot_size * 3 + slot_gap * 2
        grid_x = content_x + (content_width - grid_width) // 2
        for slot_index in range(6):
            slot = pygame.Rect(
                grid_x + (slot_index % 3) * (slot_size + slot_gap),
                tab_content_top + (slot_index // 3) * (slot_size + 5),
                slot_size,
                slot_size,
            )
            pygame.draw.rect(screen, panel_fill, slot, border_radius=3)
            pygame.draw.rect(
                screen,
                muted_border,
                slot,
                width=1,
                border_radius=3,
            )
            if slot_index >= len(inventory):
                continue
            asset_name, count = inventory[slot_index]
            item = assets[asset_name]
            screen.blit(
                item,
                item.get_rect(center=slot.center),
            )
            count_badge = pygame.Rect(
                slot.right - 19,
                slot.bottom - 18,
                16,
                15,
            )
            pygame.draw.rect(
                screen,
                (12, 11, 15),
                count_badge,
                border_radius=3,
            )
            count_surface = numbers_font.render(
                str(count),
                True,
                TEXT_COLOR,
            )
            screen.blit(
                count_surface,
                count_surface.get_rect(center=count_badge.center),
            )
    else:
        damage_bonus = None
        damage_bonus_color = (225, 69, 55)
        if player.subclass == "berserker":
            health_ratio = player.health / player.max_health
            if (
                player.berserker_last_rage_turns > 0
                or health_ratio
                <= BERSERKER_RAGE_CRITICAL_HEALTH_RATIO
            ):
                rage_multiplier = (
                    BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER
                )
            elif (
                health_ratio
                <= BERSERKER_RAGE_INJURED_HEALTH_RATIO
            ):
                rage_multiplier = (
                    BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER
                )
            else:
                rage_multiplier = 1.0

            bonus_minimum = (
                math.ceil(player.damage_min * rage_multiplier)
                - player.damage_min
            )
            bonus_maximum = (
                math.ceil(player.damage_max * rage_multiplier)
                - player.damage_max
            )
            damage_bonus = (
                f"+{bonus_minimum}"
                if bonus_minimum == bonus_maximum
                else f"+{bonus_minimum}-{bonus_maximum}"
            )
        elif (
            player.subclass == "paladin"
            and player.paladin_holy_shield_turns > 0
        ):
            damage_bonus = (
                f"+{PALADIN_HOLY_SHIELD_DAMAGE_BONUS}"
            )
            damage_bonus_color = (242, 197, 78)

        stats = (
            (
                "Damage",
                f"{player.damage_min}-{player.damage_max}",
                damage_bonus,
            ),
            (
                "Critical chance",
                f"{round(player.crit_chance * 100)}%",
                None,
            ),
            (
                "Dodge chance",
                f"{round(player.dodge_chance * 100)}%",
                None,
            ),
        )
        for stat_index, (label, value, bonus) in enumerate(stats):
            stat_y = tab_content_top + stat_index * 29
            _draw_label(
                screen,
                text_font,
                label,
                dim_color,
                (content_x + 5, stat_y),
            )
            value_surface = numbers_font.render(value, True, TEXT_COLOR)
            value_right = content_x + content_width - 5
            if bonus is not None:
                bonus_surface = numbers_font.render(
                    bonus,
                    True,
                    damage_bonus_color,
                )
                screen.blit(
                    bonus_surface,
                    (
                        value_right - bonus_surface.get_width(),
                        stat_y,
                    ),
                )
                value_right -= bonus_surface.get_width() + 7
            screen.blit(
                value_surface,
                (
                    value_right - value_surface.get_width(),
                    stat_y,
                ),
            )
            if stat_index < len(stats) - 1:
                pygame.draw.line(
                    screen,
                    (51, 46, 56),
                    (content_x + 5, stat_y + 23),
                    (content_x + content_width - 5, stat_y + 23),
                )

    ability_y = ACT_THREE_SIDEBAR_Y + 270
    _draw_label(
        screen,
        heading_font,
        "Abilities",
        TEXT_COLOR,
        (content_x, ability_y),
    )

    pygame.draw.line(
        screen,
        muted_border,
        (content_x + 92, ability_y + 13),
        (content_x + content_width, ability_y + 15),
    )
    invisibility_charge_ratio = max(
        0,
        min(1, player.ability_kill_charge / CLASS_ABILITY_KILLS),
    )
    teleport_charge_ratio = max(
        0,
        min(1, player.teleport_charge / ASSASSIN_TELEPORT_CHARGES),
    )
    ultimate_charge_ratio = max(
        0,
        min(1, player.ultimate_charge / ASSASSIN_ULTIMATE_CHARGES),
    )
    if player.subclass == "archer":
        empowered_charge_ratio = max(
            0,
            min(
                1,
                player.archer_empowered_shot_charge
                / ARCHER_EMPOWERED_SHOT_CHARGES,
            ),
        )
        leap_charge_ratio = max(
            0,
            min(
                1,
                player.archer_leap_charge
                / ARCHER_LEAP_CHARGES,
            ),
        )
        barrage_charge_ratio = max(
            0,
            min(
                1,
                player.archer_barrage_zone_charge
                / ARCHER_BARRAGE_ZONE_CHARGES,
            ),
        )
        regular_abilities = (
            (
                "archer_empowered_shot",
                "Empowered Shot",
                empowered_charge_ratio,
                accent_color,
            ),
            (
                "archer_leap",
                "Leap",
                leap_charge_ratio,
                accent_color,
            ),
            (
                "archer_barrage_zone",
                "Barrage Zone",
                barrage_charge_ratio,
                accent_color,
            ),
        )
    elif player.subclass == "berserker":
        crushing_leap_charge_ratio = max(
            0,
            min(
                1,
                player.berserker_crushing_leap_charge
                / BERSERKER_CRUSHING_LEAP_CHARGES,
            ),
        )
        last_rage_charge_ratio = max(
            0,
            min(
                1,
                player.berserker_last_rage_charge
                / BERSERKER_LAST_RAGE_CHARGES,
            ),
        )
        regular_abilities = (
            (
                "berserker_rage",
                "Rage",
                1.0,
                (220, 72, 58),
            ),
            (
                "berserker_crushing_leap",
                "Crushing Leap",
                crushing_leap_charge_ratio,
                (220, 72, 58),
            ),
            (
                "berserker_last_rage",
                (
                    f"Last Rage ({player.berserker_last_rage_turns})"
                    if player.berserker_last_rage_turns > 0
                    else "Last Rage"
                ),
                (
                    1.0
                    if player.berserker_last_rage_turns > 0
                    else last_rage_charge_ratio
                ),
                (245, 54, 45),
            ),
        )
    elif player.subclass == "paladin":
        holy_hand_charge_ratio = max(
            0,
            min(
                1,
                player.paladin_holy_hand_charge
                / PALADIN_HOLY_HAND_CHARGES,
            ),
        )
        shield_charge_ratio = max(
            0,
            min(
                1,
                player.paladin_shield_charge_charge
                / PALADIN_SHIELD_CHARGE_CHARGES,
            ),
        )
        holy_shield_charge_ratio = max(
            0,
            min(
                1,
                player.paladin_holy_shield_charge
                / PALADIN_HOLY_SHIELD_CHARGES,
            ),
        )
        regular_abilities = (
            (
                "paladin_holy_hand",
                "Holy Hand",
                holy_hand_charge_ratio,
                (239, 194, 78),
            ),
            (
                "paladin_shield_charge",
                "Shield Charge",
                shield_charge_ratio,
                (239, 194, 78),
            ),
            (
                "paladin_holy_shield",
                (
                    f"Holy Shield ({player.paladin_holy_shield_turns})"
                    if player.paladin_holy_shield_turns > 0
                    else "Holy Shield"
                ),
                (
                    1.0
                    if player.paladin_holy_shield_turns > 0
                    else holy_shield_charge_ratio
                ),
                (255, 219, 116),
            ),
        )
    elif player.subclass == "warlock":
        curse_charge_ratio = max(
            0,
            min(
                1,
                player.warlock_curse_charge
                / WARLOCK_CURSE_CHARGES,
            ),
        )
        soul_exchange_charge_ratio = max(
            0,
            min(
                1,
                player.warlock_soul_exchange_charge
                / WARLOCK_SOUL_EXCHANGE_CHARGES,
            ),
        )
        regular_abilities = (
            (
                "warlock_curse",
                "Curse",
                curse_charge_ratio,
                (198, 91, 238),
            ),
            (
                "warlock_soul_exchange",
                "Soul Exchange",
                soul_exchange_charge_ratio,
                (184, 78, 224),
            ),
            (
                "warlock_demon_form",
                "Demon Form",
                0.0,
                (220, 67, 194),
            ),
        )
    else:
        regular_abilities = (
            (
                "assassin_invisibility",
                "Invisibility",
                invisibility_charge_ratio,
                accent_color,
            ),
            (
                "assassin_teleport",
                "Teleport",
                teleport_charge_ratio,
                accent_color,
            ),
            (
                "assassin_killing_spree",
                "Killing Spree",
                ultimate_charge_ratio,
                (205, 68, 74),
            ),
        )
    card_y = ability_y + 30
    card_width = content_width
    card_height = 64
    for index, (asset_name, name, charge_ratio, ability_color) in enumerate(
        regular_abilities
    ):
        card = pygame.Rect(
            content_x,
            card_y + index * (card_height + 7),
            card_width,
            card_height,
        )
        pygame.draw.rect(screen, panel_fill, card, border_radius=4)
        pygame.draw.rect(
            screen,
            muted_border,
            card,
            width=1,
            border_radius=4,
        )
        icon = assets[asset_name]
        screen.blit(icon, (card.x + 7, card.y + 6))
        text_x = card.x + 61
        _draw_label(
            screen,
            text_font,
            name,
            ability_color,
            (text_x, card.y + 7),
        )
        key_badge = pygame.Rect(card.right - 29, card.y + 7, 20, 20)
        is_passive = player.subclass == "berserker" and index == 0
        if is_passive:
            key_badge = pygame.Rect(
                card.right - 69,
                card.y + 7,
                60,
                20,
            )
        pygame.draw.rect(screen, (32, 28, 38), key_badge, border_radius=3)
        pygame.draw.rect(
            screen,
            muted_border,
            key_badge,
            width=1,
            border_radius=3,
        )
        key_font = (
            fonts["sidebar_log"]
            if is_passive
            else numbers_font
        )
        key_surface = key_font.render(
            "PASSIVE" if is_passive else str(index + 1),
            True,
            (237, 104, 89) if is_passive else TEXT_COLOR,
        )
        screen.blit(key_surface, key_surface.get_rect(center=key_badge.center))
        last_rage_is_active = (
            asset_name == "berserker_last_rage"
            and player.berserker_last_rage_turns > 0
        )
        holy_shield_is_active = (
            asset_name == "paladin_holy_shield"
            and player.paladin_holy_shield_turns > 0
        )
        demon_form_is_active = (
            asset_name == "warlock_demon_form"
            and player.warlock_demon_form_active
        )
        status = (
            "ALWAYS ACTIVE"
            if is_passive
            else (
                "ACTIVE"
                if demon_form_is_active
                else (
                    "READY"
                    if asset_name == "warlock_demon_form"
                    else (
                        f"{player.paladin_holy_shield_turns} TURNS"
                        if holy_shield_is_active
                        else (
                            f"{player.berserker_last_rage_turns} TURNS"
                            if last_rage_is_active
                            else (
                                "READY"
                                if charge_ratio >= 1
                                else f"{round(charge_ratio * 100)}%"
                            )
                        )
                    )
                )
            )
        )
        _draw_label(
            screen,
            text_font if charge_ratio >= 1 else numbers_font,
            status,
            dim_color,
            (text_x, card.y + 27),
        )
        charge_bar = pygame.Rect(
            text_x,
            card.y + 48,
            card.right - text_x - 10,
            6,
        )
        pygame.draw.rect(screen, (43, 37, 48), charge_bar, border_radius=2)
        if charge_ratio > 0:
            pygame.draw.rect(
                screen,
                ability_color if is_passive else accent_color,
                (
                    charge_bar.x,
                    charge_bar.y,
                    round(charge_bar.width * charge_ratio),
                    charge_bar.height,
                ),
                border_radius=2,
            )

    log_panel = get_act_three_log_panel_rect()
    pygame.draw.rect(screen, (12, 11, 16), log_panel, border_radius=4)
    pygame.draw.rect(
        screen,
        (50, 45, 56),
        log_panel,
        width=1,
        border_radius=4,
    )
    log_font = fonts.get("sidebar_log", text_font)
    visible_line_count = 4
    max_log_scroll = max(
        0,
        len(game_state.combat_log) - visible_line_count,
    )
    game_state.log_scroll_offset = max(
        0,
        min(game_state.log_scroll_offset, max_log_scroll),
    )
    end_index = len(game_state.combat_log) - game_state.log_scroll_offset
    start_index = max(0, end_index - visible_line_count)
    log_messages = game_state.combat_log[start_index:end_index]
    arrow_rectangles = get_act_three_log_arrow_rectangles()
    for arrow_name, arrow_rectangle in arrow_rectangles.items():
        pygame.draw.rect(
            screen,
            (25, 22, 31),
            arrow_rectangle,
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            (70, 63, 76),
            arrow_rectangle,
            width=1,
            border_radius=3,
        )
        center_x = arrow_rectangle.centerx
        center_y = arrow_rectangle.centery
        if arrow_name == "older":
            points = (
                (center_x, center_y - 5),
                (center_x - 5, center_y + 3),
                (center_x + 5, center_y + 3),
            )
        else:
            points = (
                (center_x - 5, center_y - 3),
                (center_x + 5, center_y - 3),
                (center_x, center_y + 5),
            )
        pygame.draw.polygon(screen, (177, 166, 184), points)

    rendered_lines = []
    for message in log_messages:
        compact_message = message
        if "Hero hits " in compact_message and " for " in compact_message:
            attacker, amount = compact_message.rstrip(".").split(
                " for ",
                1,
            )
            compact_message = (
                attacker.replace("Hero hits ", "Hit ")
                + " "
                + amount
            )
        compact_message = compact_message.replace(
            " prepares melee at ",
            " prepares ",
        )
        compact_message = compact_message.replace(
            " is defeated.",
            " defeated",
        )
        for wrapped_line in wrap_text(
            log_font,
            compact_message,
            log_panel.width - 48,
        ):
            rendered_lines.append((wrapped_line, get_event_color(message)))

    for line_index, (visible_message, message_color) in enumerate(
        rendered_lines[:4]
    ):
        _draw_label(
            screen,
            log_font,
            visible_message,
            message_color,
            (log_panel.x + 10, log_panel.y + 8 + line_index * 17),
        )


def draw_act_three_gameplay(
    screen,
    game_state,
    fonts,
    assets,
    current_time,
):
    screen.fill((7, 6, 10))
    floor_config = FLOOR_CONFIGS[game_state.floor_index]
    floor_label = (
        f"ACT III  /  FLOOR {floor_config['act_floor']}"
    )
    _draw_label(
        screen,
        fonts["sidebar_text"],
        floor_label,
        (139, 132, 142),
        (ACT_THREE_VIEW_X, 62),
    )
    _draw_act_three_world(
        screen,
        game_state,
        assets,
        current_time,
    )
    _draw_act_three_sidebar(
        screen,
        game_state,
        fonts,
        assets,
    )

    if game_state.player.health <= 0 or game_state.game_won:
        overlay = pygame.Surface(
            (ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, 170))
        screen.blit(
            overlay,
            (ACT_THREE_VIEW_X, ACT_THREE_VIEW_Y),
        )
        message = (
            "VICTORY - PRESS R TO RESTART"
            if game_state.game_won
            else "DEFEAT - PRESS R TO RESTART"
        )
        message_surface = fonts["heading"].render(
            message,
            True,
            TEXT_COLOR,
        )
        screen.blit(
            message_surface,
            message_surface.get_rect(
                center=(
                    ACT_THREE_VIEW_X
                    + ACT_THREE_VIEW_WIDTH // 2,
                    ACT_THREE_VIEW_Y
                    + ACT_THREE_VIEW_HEIGHT // 2,
                )
            ),
        )
