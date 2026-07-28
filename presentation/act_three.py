import math
from functools import lru_cache

import pygame

from game.state import EnemyBehaviorState
from levels import FLOOR_CONFIGS
from presentation.hud import fit_text_to_width
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
    DANGER_BORDER_COLOR,
    HEALTH_BAR_BACKGROUND,
    HEALTH_BAR_COLOR,
    PLAYER_HEALTH_BAR_COLOR,
    TEXT_COLOR,
)


_TORCH_LIGHT_SURFACE = None
_IDLE_FRAME_SEQUENCE = (0, 1, 2, 1)
_IDLE_TIMELINE_CYCLE_COUNT = 4
_MOVE_FRAME_COUNT = 2
_MOVE_FRAME_DURATION_MS = 90
_ATTACK_FRAME_DURATION_MS = 240
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


def _camera_position(floor):
    world_width = len(floor.map[0]) * ACT_THREE_TILE_SIZE
    world_height = len(floor.map) * ACT_THREE_TILE_SIZE
    target_x = (
        floor.player_column * ACT_THREE_TILE_SIZE
        + ACT_THREE_TILE_SIZE // 2
        - ACT_THREE_VIEW_WIDTH // 2
    )
    target_y = (
        floor.player_row * ACT_THREE_TILE_SIZE
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
        enemy_sprite = _enemy_sprite(
            assets,
            enemy,
            current_time,
            floor.visual_seed,
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
    if (
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
        player_sprite = assets[
            f"player_{player_subclass}_walk_"
            f"{_movement_frame(current_time, game_state.player.movement_animation_started_at)}"
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
        player_sprite = assets[
            f"player_{player_subclass}_idle_{player_frame}"
        ]
    player_position = _view_position(
        floor.player_column,
        floor.player_row,
        camera_x,
        camera_y,
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

    view_surface.blit(player_sprite, player_position)

    if (
        player_subclass in ("assassin", "archer")
        and 0 <= attack_elapsed < _ATTACK_FRAME_DURATION_MS
    ):
        flash_color = (
            (80, 230, 120)
            if player_subclass == "archer"
            else (155, 215, 255)
        )
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

    _draw_health_bar(
        view_surface,
        player_position[0],
        player_position[1],
        game_state.player.health,
        game_state.player.max_health,
        PLAYER_HEALTH_BAR_COLOR,
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
    floor_config = FLOOR_CONFIGS[game_state.floor_index]
    content_x = ACT_THREE_SIDEBAR_X + 24
    content_width = ACT_THREE_SIDEBAR_WIDTH - 48
    heading_font = fonts["sidebar_heading"]
    text_font = fonts["sidebar_text"]
    dim_color = (139, 132, 142)
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

    _draw_label(
        screen,
        heading_font,
        subclass_name,
        accent_color,
        (content_x, ACT_THREE_SIDEBAR_Y + 18),
    )
    floor_label = (
        f"ACT III  /  FLOOR {floor_config['act_floor']}"
    )
    _draw_label(
        screen,
        text_font,
        floor_label,
        dim_color,
        (content_x, ACT_THREE_SIDEBAR_Y + 52),
    )
    health_bar = pygame.Rect(
        content_x,
        ACT_THREE_SIDEBAR_Y + 75,
        content_width,
        12,
    )
    pygame.draw.rect(
        screen,
        (29, 16, 20),
        health_bar,
        border_radius=3,
    )
    pygame.draw.rect(
        screen,
        (168, 48, 50),
        (
            health_bar.x,
            health_bar.y,
            round(
                health_bar.width
                * player.health
                / player.max_health
            ),
            health_bar.height,
        ),
        border_radius=3,
    )

    section_y = ACT_THREE_SIDEBAR_Y + 122
    _draw_label(
        screen,
        heading_font,
        "CHARACTER",
        TEXT_COLOR,
        (content_x, section_y),
    )
    stats = (
        f"HP       {player.health}/{player.max_health}",
        f"DAMAGE   {player.damage_min}-{player.damage_max}",
        f"CRIT     {round(player.crit_chance * 100)}%",
        f"DODGE    {round(player.dodge_chance * 100)}%",
    )

    for line_index, line in enumerate(stats):
        _draw_label(
            screen,
            text_font,
            line,
            dim_color,
            (content_x, section_y + 35 + line_index * 25),
        )

    inventory_y = section_y + 145
    _draw_label(
        screen,
        heading_font,
        "INVENTORY",
        TEXT_COLOR,
        (content_x, inventory_y),
    )
    inventory_line = (
        f"Potions {player.potion_count}   "
        f"Gold {player.gold_count}   "
        f"Keys {player.key_count}"
    )
    _draw_label(
        screen,
        text_font,
        inventory_line,
        dim_color,
        (content_x, inventory_y + 35),
    )

    ability_y = inventory_y + 76
    _draw_label(
        screen,
        heading_font,
        {
            "rogue": "INVISIBILITY",
            "mage": "ARCANE BURST",
            "warrior": "POWER STRIKE",
        }.get(player.player_class, "ABILITY"),
        accent_color,
        (content_x, ability_y),
    )
    if (
        player.player_class == "rogue"
        and player.invisibility_turns > 0
    ):
        ability_status = (
            f"ACTIVE  {player.invisibility_turns} TURNS"
        )
    else:
        ability_status = (
            "READY"
            if player.ability_kill_charge >= 2
            else f"{player.ability_kill_charge}/2 KILLS"
        )
    _draw_label(
        screen,
        text_font,
        ability_status,
        dim_color,
        (content_x, ability_y + 35),
    )

    events_y = ability_y + 78
    _draw_label(
        screen,
        heading_font,
        "RECENT EVENTS",
        TEXT_COLOR,
        (content_x, events_y),
    )

    for line_index, message in enumerate(
        game_state.combat_log[-4:]
    ):
        visible_message = fit_text_to_width(
            text_font,
            message,
            content_width,
        )
        _draw_label(
            screen,
            text_font,
            visible_message,
            dim_color,
            (
                content_x,
                events_y + 34 + line_index * 23,
            ),
        )

    controls_y = ACT_THREE_SIDEBAR_Y + 548
    controls = (
        "MOVE  WASD / ARROWS",
        "ABILITY  E     POTION  H",
        "WAIT  SPACE",
    )

    for line_index, line in enumerate(controls):
        _draw_label(
            screen,
            text_font,
            line,
            dim_color,
            (content_x, controls_y + line_index * 24),
        )


def draw_act_three_gameplay(
    screen,
    game_state,
    fonts,
    assets,
    current_time,
):
    screen.fill((7, 6, 10))
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
