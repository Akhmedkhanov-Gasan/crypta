import math

import pygame

from acts.act_two.presentation import draw_act_two_player_actor
from acts.act_two.presentation.enemies import (
    draw_act_two_attack_markers,
    draw_act_two_enemy,
)
from acts.act_two.presentation.environment import (
    draw_dungeon as _draw_act_two_dungeon,
    draw_frame as _draw_act_two_map_frame,
)
from acts.act_two.presentation.items import (
    draw_chest as _draw_act_two_chest,
    draw_coin as _draw_act_two_coin,
    draw_key as _draw_act_two_key,
    draw_potion as _draw_act_two_potion,
    draw_stairs as _draw_act_two_stairs,
)
from presentation.layout import (
    MAP_HEIGHT,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    MAP_WIDTH,
)
from settings import (
    ATTACK_WARNING_COLOR,
    DANGER_BORDER_COLOR,
    DANGER_TILE_COLOR,
    GRID_COLOR,
    HEALTH_BAR_BACKGROUND,
    HEALTH_BAR_COLOR,
    PLAYER_ATTACK_BORDER_COLOR,
    PLAYER_ATTACK_TILE_COLOR,
    PLAYER_HEALTH_BAR_COLOR,
    TILE_SIZE,
)


ACT_ONE_FLOOR_COLOR = (24, 25, 31)
ACT_ONE_FLOOR_ALT_COLOR = (27, 28, 35)
ACT_ONE_WALL_COLOR = (49, 48, 56)
ACT_ONE_WALL_ALT_COLOR = (54, 52, 61)
ACT_ONE_GRID_COLOR = (15, 16, 21)
ACT_ONE_STONE_LIGHT = (67, 64, 73)
ACT_ONE_STONE_SHADOW = (18, 18, 24)
ACT_ONE_IRON = (42, 43, 51)
ACT_ONE_IRON_LIGHT = (78, 76, 85)
ACT_ONE_GOLD = (164, 124, 50)
ACT_ONE_GOLD_LIGHT = (226, 184, 82)
ACT_ONE_BLOOD = (112, 38, 45)
ACT_ONE_PLAYER_CLOAK = (58, 65, 76)
ACT_ONE_PLAYER_EDGE = (116, 132, 145)
ACT_ONE_PLAYER_FACE = (174, 165, 151)
ACT_ONE_HEALTH_HIGH = (70, 176, 105)
ACT_ONE_HEALTH_MID = (219, 171, 66)
ACT_ONE_HEALTH_LOW = (200, 57, 65)
ACT_ONE_MOVE_DURATIONS = {
    "hero": 170,
    "goblin": 135,
    "archer": 205,
    "brute": 235,
    "warden": 360,
}
ACT_ONE_ENEMY_DEATH_DURATION_MS = 820
ACT_ONE_BOSS_DEATH_DURATION_MS = 1450
_ACT_ONE_RUNE_SURFACES = {}


def _act_one_enemy_color(color, is_aggro):
    factor = 0.78 if is_aggro else 0.56
    return tuple(max(28, round(channel * factor)) for channel in color)


def _draw_act_one_glow(screen, center, color, radius=18):
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for current_radius in range(radius, 2, -3):
        progress = 1 - current_radius / radius
        alpha = round(5 + 21 * progress * progress)
        pygame.draw.circle(
            glow,
            (*color, alpha),
            (radius, radius),
            current_radius,
        )
    screen.blit(glow, (center[0] - radius, center[1] - radius))


def _draw_act_one_shadow(screen, center_x, center_y, width=22):
    shadow = pygame.Surface((width + 8, 10), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (4, 4, 7, 145), shadow.get_rect())
    screen.blit(shadow, (center_x - shadow.get_width() // 2, center_y + 7))


def _draw_act_one_healing_effect(
    screen,
    center_x,
    center_y,
    current_time,
    effect_started_at,
):
    duration = 720
    elapsed = current_time - effect_started_at
    if effect_started_at <= 0 or not 0 <= elapsed < duration:
        return False

    progress = elapsed / duration
    visibility = 1 - progress
    effect_size = 64
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    effect_center = effect_size // 2

    ring_radius = round(10 + progress * 18)
    pygame.draw.circle(
        effect_surface,
        (67, 207, 126, round(190 * visibility)),
        (effect_center, effect_center + 2),
        ring_radius,
        width=2,
    )
    pygame.draw.ellipse(
        effect_surface,
        (91, 230, 145, round(145 * visibility)),
        (
            effect_center - 14 - round(progress * 7),
            effect_center + 12,
            28 + round(progress * 14),
            7,
        ),
        width=2,
    )

    particle_offsets = (-12, -7, -2, 4, 9, 13)
    for particle_index, offset_x in enumerate(particle_offsets):
        particle_delay = particle_index * 38
        particle_elapsed = max(0, elapsed - particle_delay)
        particle_progress = min(1, particle_elapsed / 470)
        if particle_elapsed <= 0 or particle_progress >= 1:
            continue
        particle_visibility = 1 - particle_progress
        drift = -1 if particle_index % 2 else 1
        particle_x = (
            effect_center
            + offset_x
            + round(drift * particle_progress * 4)
        )
        particle_y = effect_center + 12 - round(particle_progress * 34)
        pygame.draw.rect(
            effect_surface,
            (95, 235, 151, round(220 * particle_visibility)),
            (particle_x, particle_y, 2, 3),
        )

    symbol_alpha = round(235 * max(0, 1 - progress * 1.35))
    symbol_y = effect_center - 16 - round(progress * 7)
    pygame.draw.line(
        effect_surface,
        (141, 244, 174, symbol_alpha),
        (effect_center - 4, symbol_y),
        (effect_center + 4, symbol_y),
        2,
    )
    pygame.draw.line(
        effect_surface,
        (141, 244, 174, symbol_alpha),
        (effect_center, symbol_y - 4),
        (effect_center, symbol_y + 4),
        2,
    )

    screen.blit(
        effect_surface,
        (center_x - effect_center, center_y - effect_center),
    )
    return True


def _act_one_hit_reaction(
    column,
    row,
    current_time,
    hit_started_at,
    hit_origin,
):
    duration = 380
    elapsed = current_time - hit_started_at
    if hit_started_at < 0 or not 0 <= elapsed < duration:
        return False, 0, 0, False

    offset_x = 0
    offset_y = 0
    recoil_duration = 210
    if elapsed < recoil_duration:
        recoil_progress = elapsed / recoil_duration
        recoil = math.sin(math.pi * recoil_progress)
        direction_x = 0
        direction_y = 1
        if hit_origin is not None:
            difference_x = column - hit_origin[0]
            difference_y = row - hit_origin[1]
            if abs(difference_x) >= abs(difference_y):
                direction_x = 1 if difference_x >= 0 else -1
                direction_y = 0
            else:
                direction_x = 0
                direction_y = 1 if difference_y >= 0 else -1
        offset_x = round(direction_x * 4 * recoil)
        offset_y = round(direction_y * 4 * recoil)

    return True, offset_x, offset_y, elapsed < 170


def _draw_act_one_hit_effect(
    screen,
    center_x,
    center_y,
    current_time,
    hit_started_at,
):
    elapsed = current_time - hit_started_at
    duration = 380
    if hit_started_at < 0 or not 0 <= elapsed < duration:
        return

    progress = elapsed / duration
    visibility = 1 - progress
    effect_size = 58
    effect_center = effect_size // 2
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    ring_radius = round(9 + progress * 16)
    pygame.draw.circle(
        effect_surface,
        (205, 61, 67, round(175 * visibility)),
        (effect_center, effect_center),
        ring_radius,
        width=2,
    )

    ray_length = round(7 + progress * 8)
    ray_start = round(8 + progress * 5)
    ray_alpha = round(210 * visibility)
    for direction_x, direction_y in (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (1, 1),
    ):
        start = (
            effect_center + direction_x * ray_start,
            effect_center + direction_y * ray_start,
        )
        end = (
            effect_center + direction_x * ray_length,
            effect_center + direction_y * ray_length,
        )
        pygame.draw.line(
            effect_surface,
            (235, 112, 107, ray_alpha),
            start,
            end,
            2,
        )

    screen.blit(
        effect_surface,
        (center_x - effect_center, center_y - effect_center),
    )


def _act_one_dodge_reaction(
    column,
    row,
    current_time,
    dodge_started_at,
    dodge_origin,
):
    duration = 420
    elapsed = current_time - dodge_started_at
    if (
        dodge_origin is None
        or dodge_started_at < 0
        or not 0 <= elapsed < duration
    ):
        return False, 0, 0

    incoming_x = column - dodge_origin[0]
    incoming_y = row - dodge_origin[1]
    length = math.hypot(incoming_x, incoming_y)
    if length == 0:
        incoming_x, incoming_y = 0, 1
    else:
        incoming_x /= length
        incoming_y /= length
    dodge_x = -incoming_y
    dodge_y = incoming_x
    if (column + row) % 2:
        dodge_x *= -1
        dodge_y *= -1
    dodge_amount = math.sin(math.pi * elapsed / duration) * 7
    return True, round(dodge_x * dodge_amount), round(dodge_y * dodge_amount)


def _draw_act_one_dodge_effect(
    screen,
    center_x,
    center_y,
    current_time,
    dodge_started_at,
    dodge_origin,
    dodge_offset_x,
    dodge_offset_y,
):
    elapsed = current_time - dodge_started_at
    duration = 420
    if (
        dodge_origin is None
        or dodge_started_at < 0
        or not 0 <= elapsed < duration
    ):
        return

    progress = elapsed / duration
    visibility = 1 - progress
    effect = pygame.Surface((68, 68), pygame.SRCALPHA)
    effect_center = 34
    base_x = effect_center - dodge_offset_x
    base_y = effect_center - dodge_offset_y
    for echo_index, echo_scale in enumerate((0.35, 0.7)):
        echo_x = round(base_x + dodge_offset_x * echo_scale)
        echo_y = round(base_y + dodge_offset_y * echo_scale)
        echo_alpha = round((74 - echo_index * 24) * visibility)
        pygame.draw.polygon(
            effect,
            (92, 112, 130, echo_alpha),
            (
                (echo_x, echo_y - 9),
                (echo_x + 7, echo_y + 8),
                (echo_x - 7, echo_y + 8),
            ),
        )
        pygame.draw.circle(
            effect,
            (145, 164, 177, echo_alpha),
            (echo_x, echo_y - 5),
            5,
            width=2,
        )

    streak_alpha = round(180 * max(0.0, 1 - progress * 2.2))
    incoming_x = center_x - (
        MAP_OFFSET_X + dodge_origin[0] * TILE_SIZE + TILE_SIZE // 2
    )
    incoming_y = center_y - (
        MAP_OFFSET_Y + dodge_origin[1] * TILE_SIZE + TILE_SIZE // 2
    )
    length = math.hypot(incoming_x, incoming_y)
    if length:
        incoming_x /= length
        incoming_y /= length
        pygame.draw.line(
            effect,
            (197, 211, 221, streak_alpha),
            (
                round(base_x - incoming_x * 14),
                round(base_y - incoming_y * 14),
            ),
            (
                round(base_x + incoming_x * 10),
                round(base_y + incoming_y * 10),
            ),
            2,
        )
    screen.blit(
        effect,
        (center_x - effect_center, center_y - effect_center),
    )


def _draw_act_one_critical_hit_effect(
    screen,
    center_x,
    center_y,
    current_time,
    hit_started_at,
):
    duration = 480
    elapsed = current_time - hit_started_at
    if hit_started_at < 0 or not 0 <= elapsed < duration:
        return

    progress = elapsed / duration
    visibility = 1 - progress
    effect = pygame.Surface((72, 72), pygame.SRCALPHA)
    effect_center = 36
    ray_length = round(13 + progress * 18)
    for ray_index in range(8):
        angle = ray_index * math.tau / 8 + 0.18
        inner = 6 + (ray_index % 2) * 3
        pygame.draw.line(
            effect,
            (246, 218, 145, round(245 * visibility)),
            (
                round(effect_center + math.cos(angle) * inner),
                round(effect_center + math.sin(angle) * inner),
            ),
            (
                round(effect_center + math.cos(angle) * ray_length),
                round(effect_center + math.sin(angle) * ray_length),
            ),
            3 if ray_index % 2 == 0 else 2,
        )
    pygame.draw.circle(
        effect,
        (255, 246, 219, round(210 * visibility)),
        (effect_center, effect_center),
        round(5 + progress * 12),
        width=2,
    )
    screen.blit(
        effect,
        (center_x - effect_center, center_y - effect_center),
    )


def _act_one_attack_lunge(
    column,
    row,
    target,
    current_time,
    attack_started_at,
):
    duration = 260
    elapsed = current_time - attack_started_at
    if (
        target is None
        or attack_started_at <= 0
        or not 0 <= elapsed < duration
    ):
        return 0, 0

    direction_x = target[0] - column
    direction_y = target[1] - row
    if direction_x:
        direction_x = 1 if direction_x > 0 else -1
    if direction_y:
        direction_y = 1 if direction_y > 0 else -1

    lunge = math.sin(math.pi * elapsed / duration)
    return (
        round(direction_x * 5 * lunge),
        round(direction_y * 5 * lunge),
    )


def _act_one_movement_offset(
    column,
    row,
    origin,
    current_time,
    movement_started_at,
    actor_kind="hero",
):
    duration = ACT_ONE_MOVE_DURATIONS.get(actor_kind, 170)
    elapsed = current_time - movement_started_at
    if (
        origin is None
        or movement_started_at <= 0
        or not 0 <= elapsed < duration
    ):
        return 0, 0

    progress = elapsed / duration
    if actor_kind in ("archer", "brute", "warden"):
        eased_progress = progress * progress * (3 - 2 * progress)
    else:
        eased_progress = 1 - (1 - progress) ** 3
    remaining = 1 - eased_progress
    offset_x = round((origin[0] - column) * TILE_SIZE * remaining)
    offset_y = round((origin[1] - row) * TILE_SIZE * remaining)
    lift_by_kind = {
        "hero": 2,
        "goblin": 5,
        "archer": 0,
        "brute": 1,
        "warden": 0,
    }
    step_lift = round(
        math.sin(math.pi * progress)
        * lift_by_kind.get(actor_kind, 2)
    )

    direction_x = column - origin[0]
    direction_y = row - origin[1]
    if actor_kind == "goblin":
        sway = round(math.sin(math.pi * progress) * 2)
        offset_x += -direction_y * sway
        offset_y += direction_x * sway
    elif actor_kind in ("brute", "warden") and progress > 0.72:
        landing_progress = (progress - 0.72) / 0.28
        offset_y += round(math.sin(math.pi * landing_progress) * 2)

    return offset_x, offset_y - step_lift


def _act_one_movement_progress(
    origin,
    current_time,
    movement_started_at,
    actor_kind,
):
    duration = ACT_ONE_MOVE_DURATIONS.get(actor_kind, 170)
    elapsed = current_time - movement_started_at
    if (
        origin is None
        or movement_started_at <= 0
        or not 0 <= elapsed < duration
    ):
        return None
    return elapsed / duration


def _draw_act_one_movement_accent(
    screen,
    center_x,
    center_y,
    column,
    row,
    origin,
    current_time,
    movement_started_at,
    actor_kind,
):
    progress = _act_one_movement_progress(
        origin,
        current_time,
        movement_started_at,
        actor_kind,
    )
    if progress is None:
        return

    direction_x = column - origin[0]
    direction_y = row - origin[1]
    effect = pygame.Surface((54, 54), pygame.SRCALPHA)
    effect_center = 27
    visibility = math.sin(math.pi * progress)

    if actor_kind == "hero":
        trail_alpha = round(75 * visibility)
        for spread in (-3, 3):
            pygame.draw.line(
                effect,
                (83, 94, 108, trail_alpha),
                (
                    effect_center - direction_x * 5 - direction_y * spread,
                    effect_center - direction_y * 5 + direction_x * spread,
                ),
                (
                    effect_center - direction_x * 13 - direction_y * spread,
                    effect_center - direction_y * 13 + direction_x * spread,
                ),
                2,
            )
    elif actor_kind == "goblin":
        trail_alpha = round(95 * visibility)
        for spread in (-4, 3):
            pygame.draw.line(
                effect,
                (91, 109, 72, trail_alpha),
                (
                    effect_center - direction_x * 7 - direction_y * spread,
                    effect_center - direction_y * 7 + direction_x * spread,
                ),
                (
                    effect_center - direction_x * 15 - direction_y * spread,
                    effect_center - direction_y * 15 + direction_x * spread,
                ),
            )
    elif actor_kind == "archer":
        pygame.draw.line(
            effect,
            (102, 82, 91, round(65 * visibility)),
            (
                effect_center - direction_x * 5,
                effect_center - direction_y * 5,
            ),
            (
                effect_center - direction_x * 14,
                effect_center - direction_y * 14,
            ),
            2,
        )
    elif actor_kind in ("brute", "warden") and progress > 0.58:
        landing_visibility = math.sin(
            math.pi * (progress - 0.58) / 0.42
        )
        dust_color = (
            113,
            103,
            91,
            round((85 if actor_kind == "brute" else 65) * landing_visibility),
        )
        pygame.draw.ellipse(
            effect,
            dust_color,
            (effect_center - 15, effect_center + 8, 30, 7),
            width=2,
        )
        if actor_kind == "warden":
            pygame.draw.circle(
                effect,
                (143, 72, 150, round(55 * landing_visibility)),
                (effect_center, effect_center + 9),
                12,
                width=1,
            )

    screen.blit(
        effect,
        (round(center_x - effect_center), round(center_y - effect_center)),
    )


def draw_act_one_player_attack_effect(
    screen,
    act_number,
    column,
    row,
    target,
    current_time,
    attack_started_at,
    critical=False,
):
    duration = 360 if critical else 280
    elapsed = current_time - attack_started_at
    if (
        act_number >= 2
        or target is None
        or attack_started_at <= 0
        or not 0 <= elapsed < duration
    ):
        return

    progress = elapsed / duration
    visibility = max(0.0, 1 - progress)
    direction_x = target[0] - column
    direction_y = target[1] - row
    length = math.hypot(direction_x, direction_y)
    if length == 0:
        return
    direction_x /= length
    direction_y /= length
    perpendicular_x = -direction_y
    perpendicular_y = direction_x

    player_center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    player_center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
    target_center_x = MAP_OFFSET_X + target[0] * TILE_SIZE + TILE_SIZE // 2
    target_center_y = MAP_OFFSET_Y + target[1] * TILE_SIZE + TILE_SIZE // 2
    lunge = math.sin(math.pi * min(1.0, elapsed / 260))
    hand_x = player_center_x + direction_x * (8 + 5 * lunge)
    hand_y = player_center_y + direction_y * (8 + 5 * lunge)

    effect_left = round(min(player_center_x, target_center_x) - 24)
    effect_top = round(min(player_center_y, target_center_y) - 24)
    effect_right = round(max(player_center_x, target_center_x) + 24)
    effect_bottom = round(max(player_center_y, target_center_y) + 24)
    effect_surface = pygame.Surface(
        (effect_right - effect_left, effect_bottom - effect_top),
        pygame.SRCALPHA,
    )
    hand_x -= effect_left
    hand_y -= effect_top
    target_center_x -= effect_left
    target_center_y -= effect_top
    blade_alpha = round((255 if critical else 220) * visibility)
    pygame.draw.line(
        effect_surface,
        (91, 98, 108, round(165 * visibility)),
        (round(hand_x), round(hand_y)),
        (
            round(hand_x + direction_x * 13),
            round(hand_y + direction_y * 13),
        ),
        3,
    )
    pygame.draw.line(
        effect_surface,
        (
            255 if critical else 226,
            242 if critical else 217,
            205 if critical else 194,
            blade_alpha,
        ),
        (
            round(target_center_x - perpendicular_x * 11 - direction_x * 4),
            round(target_center_y - perpendicular_y * 11 - direction_y * 4),
        ),
        (
            round(target_center_x + perpendicular_x * 11 + direction_x * 3),
            round(target_center_y + perpendicular_y * 11 + direction_y * 3),
        ),
        4 if critical else 3,
    )
    pygame.draw.line(
        effect_surface,
        (164, 124, 50, round(145 * visibility)),
        (
            round(target_center_x - perpendicular_x * 9 - direction_x * 8),
            round(target_center_y - perpendicular_y * 9 - direction_y * 8),
        ),
        (
            round(target_center_x + perpendicular_x * 9 - direction_x * 1),
            round(target_center_y + perpendicular_y * 9 - direction_y * 1),
        ),
        2,
    )
    if critical:
        pygame.draw.line(
            effect_surface,
            (246, 199, 92, round(210 * visibility)),
            (
                round(target_center_x - perpendicular_x * 9 + direction_x * 7),
                round(target_center_y - perpendicular_y * 9 + direction_y * 7),
            ),
            (
                round(target_center_x + perpendicular_x * 9 - direction_x * 7),
                round(target_center_y + perpendicular_y * 9 - direction_y * 7),
            ),
            3,
        )
        pygame.draw.circle(
            effect_surface,
            (255, 231, 167, round(155 * visibility)),
            (round(target_center_x), round(target_center_y)),
            round(5 + progress * 10),
            width=2,
        )

    spark_alpha = round(235 * max(0.0, 1 - progress * 1.7))
    spark_center = (
        round(target_center_x - direction_x * 5),
        round(target_center_y - direction_y * 5),
    )
    spark_length = round(4 + progress * 7)
    for spark_x, spark_y in (
        (perpendicular_x, perpendicular_y),
        (-perpendicular_x, -perpendicular_y),
        (direction_x, direction_y),
    ):
        pygame.draw.line(
            effect_surface,
            (239, 197, 102, spark_alpha),
            spark_center,
            (
                round(spark_center[0] + spark_x * spark_length),
                round(spark_center[1] + spark_y * spark_length),
            ),
            2,
        )

    screen.blit(effect_surface, (effect_left, effect_top))


def draw_act_one_pickup_effect(
    screen,
    act_number,
    kind,
    origin,
    current_time,
    effect_started_at,
):
    duration = 650
    elapsed = current_time - effect_started_at
    if (
        act_number >= 2
        or kind not in ("potion", "gold", "key")
        or origin is None
        or effect_started_at < 0
        or not 0 <= elapsed < duration
    ):
        return

    progress = elapsed / duration
    center_x = MAP_OFFSET_X + origin[0] * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + origin[1] * TILE_SIZE + TILE_SIZE // 2
    effect_size = 72
    effect_center = effect_size // 2
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    colors = {
        "potion": ((72, 207, 128), (139, 240, 172)),
        "gold": (ACT_ONE_GOLD, ACT_ONE_GOLD_LIGHT),
        "key": ((174, 130, 48), (239, 197, 91)),
    }
    base_color, bright_color = colors[kind]

    pull_progress = min(1.0, progress / 0.62)
    particle_radius = 24 * (1 - pull_progress)
    particle_alpha = round(210 * (1 - pull_progress))
    for particle_index in range(8):
        angle = particle_index * math.tau / 8 + progress * 0.8
        particle_x = round(effect_center + math.cos(angle) * particle_radius)
        particle_y = round(effect_center + math.sin(angle) * particle_radius)
        pygame.draw.circle(
            effect_surface,
            (*bright_color, particle_alpha),
            (particle_x, particle_y),
            1 if particle_index % 3 else 2,
        )

    ring_alpha = round(145 * max(0.0, 1 - progress * 1.8))
    ring_radius = max(3, round(19 * (1 - pull_progress) + 3))
    pygame.draw.circle(
        effect_surface,
        (*base_color, ring_alpha),
        (effect_center, effect_center),
        ring_radius,
        width=2,
    )

    symbol_visibility = math.sin(math.pi * min(1.0, progress * 1.05))
    symbol_alpha = round(235 * symbol_visibility)
    symbol_y = effect_center - round(progress * 17)
    if kind == "potion":
        pygame.draw.rect(
            effect_surface,
            (*base_color, symbol_alpha),
            (effect_center - 4, symbol_y - 4, 8, 10),
            border_radius=3,
        )
        pygame.draw.rect(
            effect_surface,
            (*bright_color, symbol_alpha),
            (effect_center - 2, symbol_y - 8, 4, 4),
        )
        pygame.draw.line(
            effect_surface,
            (*bright_color, symbol_alpha),
            (effect_center, symbol_y - 2),
            (effect_center, symbol_y + 4),
            2,
        )
    elif kind == "gold":
        pygame.draw.circle(
            effect_surface,
            (*base_color, symbol_alpha),
            (effect_center, symbol_y),
            6,
        )
        pygame.draw.circle(
            effect_surface,
            (*bright_color, symbol_alpha),
            (effect_center, symbol_y),
            4,
            width=1,
        )
        pygame.draw.line(
            effect_surface,
            (*bright_color, symbol_alpha),
            (effect_center, symbol_y - 3),
            (effect_center, symbol_y + 3),
        )
    else:
        pygame.draw.circle(
            effect_surface,
            (*bright_color, symbol_alpha),
            (effect_center - 5, symbol_y),
            4,
            width=2,
        )
        pygame.draw.line(
            effect_surface,
            (*base_color, symbol_alpha),
            (effect_center - 1, symbol_y),
            (effect_center + 8, symbol_y),
            3,
        )
        pygame.draw.line(
            effect_surface,
            (*bright_color, symbol_alpha),
            (effect_center + 5, symbol_y),
            (effect_center + 5, symbol_y + 4),
            2,
        )

    screen.blit(
        effect_surface,
        (center_x - effect_center, center_y - effect_center),
    )


def _lighter(color, amount):
    return tuple(min(255, channel + amount) for channel in color)


def _draw_act_one_goblin(screen, x, y, size, color, is_aggro):
    center_x = x + size // 2
    eye_color = (229, 79, 64) if is_aggro else (116, 92, 61)
    pygame.draw.ellipse(
        screen,
        (17, 19, 22),
        (x + 3, y + 9, size - 6, size - 7),
    )
    pygame.draw.polygon(
        screen,
        color,
        [
            (x + 1, y + 5),
            (x + 7, y + 8),
            (x + 6, y + 2),
            (center_x, y + 5),
            (x + size - 6, y + 2),
            (x + size - 7, y + 8),
            (x + size - 1, y + 5),
            (x + size - 5, y + 13),
            (x + 5, y + 13),
        ],
    )
    pygame.draw.ellipse(
        screen,
        _lighter(color, 18),
        (x + 5, y + 5, size - 10, 10),
    )
    pygame.draw.rect(screen, eye_color, (center_x - 4, y + 9, 2, 1))
    pygame.draw.rect(screen, eye_color, (center_x + 3, y + 9, 2, 1))
    pygame.draw.line(
        screen,
        (105, 104, 103),
        (x + size - 3, y + 11),
        (x + size + 2, y + 6),
        2,
    )
    pygame.draw.line(
        screen,
        (72, 51, 35),
        (x + size - 4, y + 13),
        (x + size - 1, y + 10),
        2,
    )


def _draw_act_one_brute(screen, x, y, size, color, is_aggro):
    center_x = x + size // 2
    eye_color = (233, 75, 55) if is_aggro else (104, 73, 52)
    pygame.draw.rect(screen, (16, 16, 20), (x + 4, y + 8, size - 8, 12))
    pygame.draw.circle(screen, color, (x + 4, y + 11), 5)
    pygame.draw.circle(screen, color, (x + size - 4, y + 11), 5)
    pygame.draw.polygon(
        screen,
        color,
        [
            (x + 5, y + 7),
            (x + 8, y + 3),
            (x + size - 8, y + 3),
            (x + size - 5, y + 7),
            (x + size - 6, y + size),
            (x + 6, y + size),
        ],
    )
    pygame.draw.rect(
        screen,
        _lighter(color, 20),
        (center_x - 5, y + 2, 10, 7),
        border_radius=3,
    )
    pygame.draw.rect(screen, eye_color, (center_x - 3, y + 5, 2, 1))
    pygame.draw.rect(screen, eye_color, (center_x + 2, y + 5, 2, 1))
    pygame.draw.line(
        screen,
        (59, 39, 31),
        (x + 5, y + 15),
        (x + size - 5, y + 15),
        2,
    )
    pygame.draw.rect(screen, (38, 32, 31), (x + 1, y + 15, 6, 5))
    pygame.draw.rect(screen, (38, 32, 31), (x + size - 7, y + 15, 6, 5))
    pygame.draw.line(
        screen,
        (92, 67, 43),
        (x + size - 2, y + 10),
        (x + size + 3, y + 19),
        2,
    )
    pygame.draw.polygon(
        screen,
        (76, 78, 82),
        [
            (x + size - 3, y + 5),
            (x + size + 4, y + 7),
            (x + size + 2, y + 13),
            (x + size - 3, y + 10),
        ],
    )
    pygame.draw.line(
        screen,
        (130, 126, 123),
        (x + size - 2, y + 6),
        (x + size + 2, y + 8),
    )


def _draw_act_one_archer(screen, x, y, size, color, is_aggro):
    center_x = x + size // 2
    eye_color = (218, 94, 65) if is_aggro else (88, 110, 83)
    pygame.draw.polygon(
        screen,
        (17, 20, 22),
        [
            (center_x, y),
            (x + size - 4, y + 8),
            (x + size - 3, y + size),
            (x + 3, y + size),
            (x + 4, y + 8),
        ],
    )
    pygame.draw.polygon(
        screen,
        color,
        [
            (center_x, y + 1),
            (x + size - 6, y + 8),
            (x + size - 5, y + size - 1),
            (x + 5, y + size - 1),
            (x + 6, y + 8),
        ],
    )
    pygame.draw.circle(
        screen,
        _lighter(color, 20),
        (center_x, y + 7),
        6,
    )
    pygame.draw.circle(screen, (18, 23, 24), (center_x, y + 8), 4)
    pygame.draw.rect(screen, eye_color, (center_x - 2, y + 7, 1, 1))
    pygame.draw.rect(screen, eye_color, (center_x + 2, y + 7, 1, 1))
    bow_rectangle = pygame.Rect(x - 3, y + 3, 10, 18)
    pygame.draw.arc(
        screen,
        (128, 93, 52),
        bow_rectangle,
        -1.45,
        1.45,
        2,
    )
    pygame.draw.line(
        screen,
        (91, 77, 58),
        (x + 2, y + 4),
        (x + 2, y + 20),
    )
    pygame.draw.line(
        screen,
        (151, 143, 119),
        (x + 1, y + 12),
        (x + size - 1, y + 12),
    )
    pygame.draw.polygon(
        screen,
        (151, 143, 119),
        [
            (x + size - 1, y + 12),
            (x + size - 5, y + 10),
            (x + size - 5, y + 14),
        ],
    )


def _draw_act_one_warden(screen, x, y, size, color, is_aggro):
    center_x = x + size // 2
    rune_color = (213, 91, 112) if is_aggro else (123, 82, 129)
    pygame.draw.polygon(
        screen,
        (16, 15, 21),
        [
            (center_x, y - 2),
            (x + size - 2, y + 8),
            (x + size - 4, y + size + 1),
            (x + 4, y + size + 1),
            (x + 2, y + 8),
        ],
    )
    pygame.draw.polygon(
        screen,
        color,
        [
            (center_x, y + 1),
            (x + size - 4, y + 8),
            (x + size - 6, y + size),
            (x + 6, y + size),
            (x + 4, y + 8),
        ],
    )
    pygame.draw.polygon(
        screen,
        _lighter(color, 24),
        [
            (center_x, y - 3),
            (center_x + 3, y + 3),
            (x + size - 3, y),
            (x + size - 6, y + 7),
            (x + 6, y + 7),
            (x + 3, y),
            (center_x - 3, y + 3),
        ],
    )
    pygame.draw.rect(screen, (19, 16, 25), (center_x - 5, y + 6, 10, 5))
    pygame.draw.rect(screen, rune_color, (center_x - 3, y + 8, 2, 1))
    pygame.draw.rect(screen, rune_color, (center_x + 2, y + 8, 2, 1))
    pygame.draw.line(
        screen,
        rune_color,
        (center_x, y + 13),
        (center_x, y + 18),
        2,
    )
    pygame.draw.line(screen, rune_color, (center_x - 3, y + 15), (center_x, y + 18))
    pygame.draw.line(screen, rune_color, (center_x + 3, y + 15), (center_x, y + 18))
    pygame.draw.line(
        screen,
        (88, 81, 98),
        (x + size + 1, y + 3),
        (x + size + 1, y + size),
        2,
    )
    pygame.draw.circle(screen, rune_color, (x + size + 1, y + 3), 3, width=1)


def _draw_act_one_enemy(screen, enemy, x, y, size, color):
    _draw_act_one_shadow(
        screen,
        x + size // 2,
        y + size // 2,
        size,
    )
    drawers = {
        "goblin": _draw_act_one_goblin,
        "brute": _draw_act_one_brute,
        "archer": _draw_act_one_archer,
        "warden": _draw_act_one_warden,
    }
    drawer = drawers.get(enemy["type"], _draw_act_one_goblin)
    drawer(screen, x, y, size, color, enemy["is_aggro"])


def _draw_act_one_enemy_death(
    screen,
    enemy,
    current_time,
    color,
):
    started_at = enemy.get("death_animation_started_at", -1)
    is_boss = enemy["type"] == "warden"
    duration = (
        ACT_ONE_BOSS_DEATH_DURATION_MS
        if is_boss
        else ACT_ONE_ENEMY_DEATH_DURATION_MS
    )
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < duration:
        return

    progress = elapsed / duration
    center_x = (
        MAP_OFFSET_X + enemy["column"] * TILE_SIZE + TILE_SIZE // 2
    )
    center_y = (
        MAP_OFFSET_Y + enemy["row"] * TILE_SIZE + TILE_SIZE // 2
    )
    pulse = math.sin(math.pi * min(1, progress * 1.6))

    if is_boss:
        aura = pygame.Surface((112, 112), pygame.SRCALPHA)
        aura_center = 56
        for ring_index in range(3):
            ring_progress = min(
                1,
                progress * 1.2 + ring_index * 0.09,
            )
            radius = round(14 + ring_progress * 34)
            alpha = round(
                max(0, 115 - ring_progress * 105 - ring_index * 18)
            )
            pygame.draw.circle(
                aura,
                (148, 54, 164, alpha),
                (aura_center, aura_center),
                radius,
                width=2,
            )
        screen.blit(
            aura,
            (center_x - aura_center, center_y - aura_center),
        )

    body_end = 0.66 if is_boss else 0.58
    if progress < body_end:
        body_progress = progress / body_end
        body_canvas_size = 52
        body = pygame.Surface(
            (body_canvas_size, body_canvas_size),
            pygame.SRCALPHA,
        )
        body_size = TILE_SIZE - (TILE_SIZE // 5) * 2
        body_x = (body_canvas_size - body_size) // 2
        body_y = 10
        if elapsed < 105:
            body_color = (225, 215, 207)
        else:
            darkness = max(0.18, 0.72 - body_progress * 0.54)
            body_color = tuple(
                max(12, round(channel * darkness))
                for channel in color
            )
        _draw_act_one_enemy(
            body,
            enemy,
            body_x,
            body_y,
            body_size,
            body_color,
        )
        collapse = body_progress * body_progress
        collapsed_height = max(
            4,
            round(body_canvas_size * (1 - collapse * 0.78)),
        )
        collapsed_width = round(
            body_canvas_size * (1 + collapse * 0.14)
        )
        body = pygame.transform.smoothscale(
            body,
            (collapsed_width, collapsed_height),
        )
        body.set_alpha(round(255 * (1 - body_progress ** 2)))
        screen.blit(
            body,
            (
                center_x - collapsed_width // 2,
                center_y + 17 - collapsed_height,
            ),
        )

    particle_count = 22 if is_boss else 11
    if enemy.get("hit_critical", False):
        particle_count += 5
    seed = (
        enemy["column"] * 97
        + enemy["row"] * 193
        + sum(ord(character) for character in enemy["type"])
    )
    for particle_index in range(particle_count):
        delay = (particle_index % 7) * (28 if is_boss else 22)
        particle_elapsed = elapsed - delay
        particle_duration = duration - delay
        if particle_elapsed < 0 or particle_duration <= 0:
            continue
        particle_progress = min(1, particle_elapsed / particle_duration)
        if particle_progress >= 1:
            continue

        angle_degrees = (seed * 13 + particle_index * 137) % 360
        angle = math.radians(angle_degrees)
        distance = (
            (18 if is_boss else 11)
            + (particle_index % 5) * 2
        ) * particle_progress
        drift_x = math.cos(angle) * distance
        drift_y = (
            math.sin(angle) * distance * 0.65
            - (12 if is_boss else 7) * particle_progress
            + 15 * particle_progress * particle_progress
        )
        particle_alpha = round(210 * (1 - particle_progress) ** 1.4)
        particle_size = (
            3
            if is_boss and particle_index % 4 == 0
            else 2
            if particle_index % 3 == 0
            else 1
        )
        particle_color = (
            (178, 79, 185, particle_alpha)
            if is_boss and particle_index % 3 == 0
            else (105, 100, 109, particle_alpha)
            if particle_index % 2 == 0
            else (48, 43, 53, particle_alpha)
        )
        particle = pygame.Surface(
            (particle_size, particle_size),
            pygame.SRCALPHA,
        )
        particle.fill(particle_color)
        screen.blit(
            particle,
            (
                round(center_x + drift_x - particle_size / 2),
                round(center_y + drift_y - particle_size / 2),
            ),
        )

    if enemy.get("hit_critical", False) and progress < 0.48:
        critical_visibility = 1 - progress / 0.48
        spark = pygame.Surface((64, 64), pygame.SRCALPHA)
        spark_center = 32
        for spark_index in range(4):
            angle = math.radians(25 + spark_index * 90)
            inner = round(5 + progress * 9)
            outer = round(15 + progress * 18)
            pygame.draw.line(
                spark,
                (226, 185, 100, round(180 * critical_visibility)),
                (
                    spark_center + round(math.cos(angle) * inner),
                    spark_center + round(math.sin(angle) * inner),
                ),
                (
                    spark_center + round(math.cos(angle) * outer),
                    spark_center + round(math.sin(angle) * outer),
                ),
                2,
            )
        screen.blit(
            spark,
            (center_x - spark_center, center_y - spark_center),
        )


def _act_one_tile_noise(column, row, visual_seed, salt=0):
    return (
        column * 73856093
        ^ row * 19349663
        ^ visual_seed * 83492791
        ^ salt * 2654435761
    ) & 0x7FFFFFFF




def _draw_act_one_crack(screen, x, y, variant, wall=False):
    crack_color = (25, 24, 30) if wall else (13, 14, 18)
    faint_edge = (62, 58, 66) if wall else (42, 41, 48)
    crack_paths = (
        ((6, 8), (13, 13), (11, 20), (18, 25)),
        ((25, 5), (19, 11), (22, 17), (14, 23), (16, 28)),
        ((7, 24), (13, 18), (20, 20), (26, 13)),
        ((5, 13), (12, 15), (17, 9), (25, 11), (28, 6)),
    )
    path = crack_paths[variant % len(crack_paths)]
    points = [(x + point_x, y + point_y) for point_x, point_y in path]
    pygame.draw.lines(screen, faint_edge, False, points, 2)
    pygame.draw.lines(screen, crack_color, False, points)
    branch_index = min(2, len(path) - 2)
    branch_x, branch_y = path[branch_index]
    branch_direction = -1 if variant % 2 else 1
    pygame.draw.line(
        screen,
        crack_color,
        (x + branch_x, y + branch_y),
        (x + branch_x + branch_direction * 5, y + branch_y + 5),
    )


def _draw_act_one_wall_rune(screen, x, y, variant):
    rune_kind = variant % 5
    rune_surface = _ACT_ONE_RUNE_SURFACES.get(rune_kind)
    if rune_surface is None:
        large_surface = pygame.Surface((48, 48), pygame.SRCALPHA)
        color = (
            (129, 91, 161, 220)
            if rune_kind % 2
            else (82, 111, 153, 220)
        )
        dim_color = (*color[:3], 135)

        def draw_stroke(points, width=4, stroke_color=color):
            pygame.draw.lines(
                large_surface,
                stroke_color,
                False,
                points,
                width,
            )
            pygame.draw.aalines(
                large_surface,
                stroke_color,
                False,
                points,
            )

        if rune_kind == 0:
            draw_stroke(((11, 7), (5, 24), (13, 41)), 5)
            draw_stroke(((21, 7), (10, 24), (22, 41)), 4)
            draw_stroke(((27, 8), (39, 23), (27, 40)), 4)
            pygame.draw.circle(large_surface, color, (27, 23), 4)
        elif rune_kind == 1:
            pygame.draw.arc(
                large_surface,
                color,
                (5, 4, 35, 39),
                math.radians(105),
                math.radians(270),
                4,
            )
            draw_stroke(((14, 39), (23, 19), (39, 7)), 4)
            draw_stroke(((23, 19), (35, 31)), 3, dim_color)
            pygame.draw.circle(large_surface, color, (29, 17), 4)
        elif rune_kind == 2:
            draw_stroke(((24, 7), (24, 41)), 4)
            pygame.draw.arc(
                large_surface,
                color,
                (4, 5, 40, 28),
                math.radians(15),
                math.radians(165),
                4,
            )
            draw_stroke(((9, 16), (24, 29), (39, 16)), 3)
            pygame.draw.circle(large_surface, color, (24, 7), 4, 2)
            pygame.draw.circle(large_surface, color, (12, 32), 3)
            pygame.draw.circle(large_surface, color, (36, 32), 3)
        elif rune_kind == 3:
            pygame.draw.arc(
                large_surface,
                color,
                (6, 7, 35, 34),
                math.radians(55),
                math.radians(305),
                5,
            )
            pygame.draw.arc(
                large_surface,
                dim_color,
                (15, 15, 21, 20),
                math.radians(205),
                math.radians(535),
                3,
            )
            pygame.draw.circle(large_surface, color, (27, 24), 4)
        else:
            draw_stroke(((6, 35), (16, 10), (22, 31), (41, 17)), 5)
            pygame.draw.arc(
                large_surface,
                color,
                (20, 7, 23, 34),
                math.radians(255),
                math.radians(455),
                4,
            )
            pygame.draw.circle(large_surface, color, (31, 31), 4)

        rune_surface = pygame.transform.smoothscale(
            large_surface,
            (24, 24),
        )
        _ACT_ONE_RUNE_SURFACES[rune_kind] = rune_surface

    glow = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.circle(
        glow,
        (89, 64, 119, 15),
        (15, 15),
        13,
    )
    screen.blit(glow, (x + 1, y + 1))
    screen.blit(rune_surface, (x + 4, y + 4))


def _draw_act_one_cold_brazier(screen, x, y, variant):
    center_x = x + TILE_SIZE // 2
    center_y = y + TILE_SIZE // 2 + 2
    pygame.draw.line(
        screen,
        (72, 69, 76),
        (center_x, center_y - 10),
        (center_x, center_y - 3),
        2,
    )
    pygame.draw.line(
        screen,
        (35, 35, 42),
        (center_x - 7, center_y - 2),
        (center_x + 7, center_y - 2),
        2,
    )
    pygame.draw.polygon(
        screen,
        (24, 24, 29),
        (
            (center_x - 7, center_y - 1),
            (center_x + 7, center_y - 1),
            (center_x + 4, center_y + 5),
            (center_x - 4, center_y + 5),
        ),
    )
    pygame.draw.line(
        screen,
        (86, 80, 79),
        (center_x - 5, center_y),
        (center_x + 5, center_y),
    )
    if variant % 2:
        pygame.draw.circle(
            screen,
            (37, 35, 38),
            (center_x - 2, center_y - 2),
            2,
        )


def _act_one_wall_is_exposed(dungeon_map, column, row):
    for column_change, row_change in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        neighbor_column = column + column_change
        neighbor_row = row + row_change
        if (
            0 <= neighbor_row < len(dungeon_map)
            and 0 <= neighbor_column < len(dungeon_map[neighbor_row])
            and dungeon_map[neighbor_row][neighbor_column] != "#"
        ):
            return True
    return False


def _draw_act_one_particles(
    screen,
    dungeon_map,
    floor_number,
    visual_seed,
    current_time,
):
    if not dungeon_map:
        return
    particle_surface = pygame.Surface(
        (MAP_WIDTH, MAP_HEIGHT),
        pygame.SRCALPHA,
    )
    column_count = len(dungeon_map[0])
    row_count = len(dungeon_map)
    for particle_index in range(18 + floor_number * 5):
        noise = _act_one_tile_noise(
            particle_index,
            floor_number,
            visual_seed,
            83,
        )
        column = noise % column_count
        row = (noise // max(1, column_count)) % row_count
        if dungeon_map[row][column] == "#":
            continue
        cycle = ((current_time / 10) + noise % 997) % 997 / 997
        particle_x = (
            column * TILE_SIZE
            + 4
            + (noise // 17) % (TILE_SIZE - 8)
            + round(math.sin(current_time / 900 + particle_index) * 2)
        )
        particle_y = (
            row * TILE_SIZE
            + TILE_SIZE
            - 4
            - round(cycle * (TILE_SIZE + 8))
        )
        alpha = round((8 + floor_number * 3) * math.sin(math.pi * cycle))
        pygame.draw.circle(
            particle_surface,
            (151, 145, 137, alpha),
            (particle_x, particle_y),
            1,
        )
    screen.blit(particle_surface, (MAP_OFFSET_X, MAP_OFFSET_Y))




def draw_act_one_atmosphere(
    screen,
    act_number,
    player_column,
    player_row,
    dungeon_map=None,
    floor_number=1,
    visual_seed=0,
    current_time=0,
):
    if act_number >= 2:
        return

    overlay = pygame.Surface((MAP_WIDTH, MAP_HEIGHT), pygame.SRCALPHA)
    depth_alpha = max(0, floor_number - 1) * 12
    if depth_alpha:
        overlay.fill((1, 2, 5, depth_alpha))
    for inset, alpha, width in (
        (0, 74, 24),
        (22, 43, 20),
        (42, 22, 18),
    ):
        pygame.draw.rect(
            overlay,
            (2, 3, 7, alpha + max(0, floor_number - 1) * 8),
            (
                inset,
                inset,
                MAP_WIDTH - inset * 2,
                MAP_HEIGHT - inset * 2,
            ),
            width=width,
        )
    screen.blit(overlay, (MAP_OFFSET_X, MAP_OFFSET_Y))

    player_center = (
        MAP_OFFSET_X + player_column * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + player_row * TILE_SIZE + TILE_SIZE // 2,
    )
    _draw_act_one_glow(screen, player_center, (72, 94, 116), 52)
    if dungeon_map is not None:
        _draw_act_one_particles(
            screen,
            dungeon_map,
            floor_number,
            visual_seed,
            current_time,
        )


def draw_dungeon(
    screen,
    dungeon_map,
    act_number,
    sprites,
    floor_number=1,
    visual_seed=0,
    floor_decor_excluded_positions=(),
):
    if act_number == 2:
        _draw_act_two_dungeon(
            screen,
            dungeon_map,
            sprites,
            floor_number,
            visual_seed,
            floor_decor_excluded_positions,
        )
        return

    for row_index, row in enumerate(dungeon_map):
        for column_index, tile in enumerate(row):
            x = MAP_OFFSET_X + column_index * TILE_SIZE
            y = MAP_OFFSET_Y + row_index * TILE_SIZE
            tile_rectangle = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            if act_number >= 2:
                texture_name = "wall" if tile in ("#", "S") else "floor"
                screen.blit(sprites[texture_name], tile_rectangle)
                if tile == "C":
                    screen.blit(sprites["pillar"], tile_rectangle)
            else:
                variation = (column_index * 7 + row_index * 11) % 5
                if tile == "#":
                    color = (
                        ACT_ONE_WALL_ALT_COLOR
                        if variation in (0, 3)
                        else ACT_ONE_WALL_COLOR
                    )
                    pygame.draw.rect(screen, color, tile_rectangle)
                    pygame.draw.line(
                        screen,
                        ACT_ONE_STONE_LIGHT,
                        (x + 2, y + 2),
                        (x + TILE_SIZE - 3, y + 2),
                    )
                    pygame.draw.line(
                        screen,
                        ACT_ONE_STONE_SHADOW,
                        (x + 2, y + TILE_SIZE - 2),
                        (x + TILE_SIZE - 2, y + TILE_SIZE - 2),
                        2,
                    )
                    seam_x = x + (11 if row_index % 2 else 20)
                    pygame.draw.line(
                        screen,
                        (35, 34, 41),
                        (seam_x, y + 4),
                        (seam_x, y + 13),
                    )
                else:
                    color = (
                        ACT_ONE_FLOOR_ALT_COLOR
                        if variation == 0
                        else ACT_ONE_FLOOR_COLOR
                    )
                    pygame.draw.rect(screen, color, tile_rectangle)
                    pygame.draw.line(
                        screen,
                        (34, 35, 42),
                        (x + 3, y + 3),
                        (x + TILE_SIZE - 4, y + 3),
                    )
                    if variation == 0:
                        pygame.draw.line(
                            screen,
                            (39, 39, 47),
                            (x + 9, y + 19),
                            (x + 16, y + 16),
                        )
                        pygame.draw.line(
                            screen,
                            (17, 18, 23),
                            (x + 16, y + 16),
                            (x + 22, y + 21),
                        )

                detail_noise = _act_one_tile_noise(
                    column_index,
                    row_index,
                    visual_seed,
                    floor_number,
                )
                crack_frequency = max(7, 12 - floor_number)
                has_rune = tile == "#" and detail_noise % 73 == 7
                has_brazier = (
                    tile == "#"
                    and detail_noise % 47 == 11
                    and _act_one_wall_is_exposed(
                        dungeon_map,
                        column_index,
                        row_index,
                    )
                )
                if (
                    detail_noise % crack_frequency == 0
                    and not has_rune
                    and not has_brazier
                ):
                    _draw_act_one_crack(
                        screen,
                        x,
                        y,
                        (detail_noise // crack_frequency) % 4,
                        wall=tile == "#",
                    )

                if tile == "#":
                    if has_rune:
                        _draw_act_one_wall_rune(
                            screen,
                            x,
                            y,
                            detail_noise // 73,
                        )
                    elif has_brazier:
                        _draw_act_one_cold_brazier(
                            screen,
                            x,
                            y,
                            detail_noise // 47,
                        )

            grid_color = ACT_ONE_GRID_COLOR if act_number < 2 else GRID_COLOR
            pygame.draw.rect(screen, grid_color, tile_rectangle, 1)


def draw_map_frame(screen, act_number):
    if act_number < 2:
        outer_rectangle = pygame.Rect(
            MAP_OFFSET_X - 5,
            MAP_OFFSET_Y - 5,
            MAP_WIDTH + 10,
            MAP_HEIGHT + 10,
        )
        pygame.draw.rect(screen, (10, 10, 14), outer_rectangle, width=5)
        pygame.draw.rect(screen, ACT_ONE_IRON, outer_rectangle, width=2)
        pygame.draw.line(
            screen,
            ACT_ONE_IRON_LIGHT,
            outer_rectangle.topleft,
            outer_rectangle.topright,
        )
        for corner in (
            outer_rectangle.topleft,
            outer_rectangle.topright,
            outer_rectangle.bottomleft,
            outer_rectangle.bottomright,
        ):
            pygame.draw.circle(screen, (20, 20, 25), corner, 4)
            pygame.draw.circle(screen, (89, 84, 81), corner, 2)
        return

    if act_number == 2:
        _draw_act_two_map_frame(screen)
        return

    outer_rectangle = pygame.Rect(
        MAP_OFFSET_X - 4,
        MAP_OFFSET_Y - 4,
        MAP_WIDTH + 8,
        MAP_HEIGHT + 8,
    )
    frame_color = (72, 68, 78)
    pygame.draw.rect(screen, (8, 10, 14), outer_rectangle.inflate(6, 6), width=5)
    pygame.draw.rect(screen, frame_color, outer_rectangle, width=3)
    pygame.draw.rect(
        screen,
        (30, 27, 34),
        outer_rectangle.inflate(-6, -6),
        width=1,
    )


def _draw_act_one_warden_telegraph(
    screen,
    column,
    row,
    mode,
    current_time,
    sweep_is_horizontal=False,
):
    left = MAP_OFFSET_X + column * TILE_SIZE
    top = MAP_OFFSET_Y + row * TILE_SIZE
    center = (left + TILE_SIZE // 2, top + TILE_SIZE // 2)
    pulse = (math.sin(current_time / 125) + 1) / 2
    tile_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

    if mode == "cross":
        tile_overlay.fill((92, 17, 27, round(54 + pulse * 28)))
        line_color = (218, 54, 66, round(150 + pulse * 80))
        pygame.draw.line(
            tile_overlay,
            line_color,
            (3, TILE_SIZE // 2),
            (TILE_SIZE - 3, TILE_SIZE // 2),
            2,
        )
        pygame.draw.line(
            tile_overlay,
            line_color,
            (TILE_SIZE // 2, 3),
            (TILE_SIZE // 2, TILE_SIZE - 3),
            2,
        )
        pygame.draw.circle(
            tile_overlay,
            (245, 104, 105, round(175 + pulse * 70)),
            (TILE_SIZE // 2, TILE_SIZE // 2),
            4,
            width=1,
        )
    elif mode == "sweep":
        tile_overlay.fill((91, 39, 12, round(48 + pulse * 25)))
        sweep_color = (232, 119, 49, round(155 + pulse * 85))
        offset = round(pulse * 5) - 2
        if sweep_is_horizontal:
            pygame.draw.line(
                tile_overlay,
                sweep_color,
                (2, TILE_SIZE // 2 + offset),
                (TILE_SIZE - 2, TILE_SIZE // 2 + offset),
                3,
            )
            pygame.draw.line(
                tile_overlay,
                (255, 190, 89, 150),
                (8, TILE_SIZE // 2 - 5 + offset),
                (TILE_SIZE - 8, TILE_SIZE // 2 - 5 + offset),
            )
        else:
            pygame.draw.line(
                tile_overlay,
                sweep_color,
                (TILE_SIZE // 2 + offset, 2),
                (TILE_SIZE // 2 + offset, TILE_SIZE - 2),
                3,
            )
            pygame.draw.line(
                tile_overlay,
                (255, 190, 89, 150),
                (TILE_SIZE // 2 - 5 + offset, 8),
                (TILE_SIZE // 2 - 5 + offset, TILE_SIZE - 8),
            )
    else:
        tile_overlay.fill((52, 19, 70, round(50 + pulse * 28)))
        rune_color = (179, 82, 205, round(160 + pulse * 85))
        radius = round(8 + pulse * 3)
        pygame.draw.circle(
            tile_overlay,
            rune_color,
            (TILE_SIZE // 2, TILE_SIZE // 2),
            radius,
            width=2,
        )
        pygame.draw.polygon(
            tile_overlay,
            rune_color,
            [
                (TILE_SIZE // 2, 5),
                (TILE_SIZE - 5, TILE_SIZE // 2),
                (TILE_SIZE // 2, TILE_SIZE - 5),
                (5, TILE_SIZE // 2),
            ],
            width=1,
        )
        pygame.draw.circle(
            tile_overlay,
            (230, 139, 244, round(180 + pulse * 70)),
            (TILE_SIZE // 2, TILE_SIZE // 2),
            2,
        )

    screen.blit(tile_overlay, (left, top))
    pygame.draw.rect(
        screen,
        (122, 47, 59) if mode == "cross" else (
            (145, 77, 37) if mode == "sweep" else (100, 53, 122)
        ),
        (left, top, TILE_SIZE, TILE_SIZE),
        width=1,
    )


def draw_attack_markers(
    screen,
    enemies,
    act_number=2,
    current_time=0,
    visible_cells=None,
    player_position=None,
    foreground=False,
):
    if act_number == 2:
        draw_act_two_attack_markers(
            screen,
            enemies,
            current_time,
            visible_cells,
            player_position,
            foreground,
        )
        return

    for enemy in enemies:
        if enemy["health"] <= 0:
            continue

        attack_mode = enemy.get("prepared_attack_mode")
        uses_warden_telegraph = (
            act_number < 2
            and enemy["type"] == "warden"
            and attack_mode in ("cross", "sweep", "runes")
        )
        attack_targets = enemy["attack_targets"]
        if not attack_targets:
            continue

        target_rows = {row for _, row in attack_targets}
        sweep_is_horizontal = len(target_rows) == 1
        for column, row in attack_targets:
            if foreground:
                continue
            if uses_warden_telegraph:
                _draw_act_one_warden_telegraph(
                    screen,
                    column,
                    row,
                    attack_mode,
                    current_time,
                    sweep_is_horizontal,
                )
                continue

            target_rectangle = pygame.Rect(
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
            )
            pygame.draw.rect(screen, DANGER_TILE_COLOR, target_rectangle)
            pygame.draw.rect(
                screen,
                DANGER_BORDER_COLOR,
                target_rectangle,
                width=3,
            )


def _draw_act_one_warden_attack_impact(
    screen,
    column,
    row,
    mode,
    progress,
    sweep_is_horizontal,
):
    left = MAP_OFFSET_X + column * TILE_SIZE
    top = MAP_OFFSET_Y + row * TILE_SIZE
    effect = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    visibility = max(0, 1 - progress)
    center = TILE_SIZE // 2

    if mode == "cross":
        color = (255, 95, 96, round(235 * visibility))
        width = 4 if progress < 0.35 else 2
        pygame.draw.line(effect, color, (1, center), (TILE_SIZE - 1, center), width)
        pygame.draw.line(effect, color, (center, 1), (center, TILE_SIZE - 1), width)
        pygame.draw.circle(
            effect,
            (255, 207, 177, round(210 * visibility)),
            (center, center),
            round(4 + progress * 10),
            width=2,
        )
    elif mode == "sweep":
        color = (255, 152, 59, round(240 * visibility))
        travel = round(progress * TILE_SIZE)
        if sweep_is_horizontal:
            pygame.draw.line(effect, color, (0, center), (travel, center), 5)
            pygame.draw.line(
                effect,
                (255, 224, 156, round(190 * visibility)),
                (0, center - 4),
                (travel, center - 4),
                2,
            )
        else:
            pygame.draw.line(effect, color, (center, 0), (center, travel), 5)
            pygame.draw.line(
                effect,
                (255, 224, 156, round(190 * visibility)),
                (center - 4, 0),
                (center - 4, travel),
                2,
            )
    else:
        color = (218, 101, 240, round(230 * visibility))
        radius = round(3 + progress * 14)
        pygame.draw.circle(effect, color, (center, center), radius, width=3)
        pygame.draw.polygon(
            effect,
            (247, 178, 255, round(205 * visibility)),
            [(center, 2), (TILE_SIZE - 2, center), (center, TILE_SIZE - 2), (2, center)],
            width=2,
        )

    screen.blit(effect, (left, top))


def _draw_act_one_warden_phase_transition(
    screen,
    warden,
    current_time,
    font,
):
    elapsed = current_time - warden.phase_transition_started_at
    duration = 1150
    if warden.phase_transition_started_at < 0 or not 0 <= elapsed < duration:
        return

    progress = elapsed / duration
    pulse = math.sin(math.pi * progress)
    arena_overlay = pygame.Surface((MAP_WIDTH, MAP_HEIGHT), pygame.SRCALPHA)
    arena_overlay.fill((37, 6, 47, round(72 * pulse)))
    screen.blit(arena_overlay, (MAP_OFFSET_X, MAP_OFFSET_Y))

    center_x = MAP_OFFSET_X + warden.column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + warden.row * TILE_SIZE + TILE_SIZE // 2
    aura = pygame.Surface((112, 112), pygame.SRCALPHA)
    aura_center = 56
    for ring_index in range(3):
        radius = round(16 + progress * 30 + ring_index * 8)
        pygame.draw.circle(
            aura,
            (190, 67, 202, round((165 - ring_index * 35) * pulse)),
            (aura_center, aura_center),
            radius,
            width=2,
        )
    screen.blit(aura, (center_x - aura_center, center_y - aura_center))

    if font is not None:
        title_alpha = round(255 * min(1, progress * 5) * min(1, (1 - progress) * 4))
        title = font.render(
            "THE WARDEN UNBOUND",
            True,
            (226, 151, 220),
        )
        title.set_alpha(title_alpha)
        screen.blit(
            title,
            title.get_rect(
                center=(
                    MAP_OFFSET_X + MAP_WIDTH // 2,
                    MAP_OFFSET_Y + 55,
                )
            ),
        )


def _draw_act_one_warden_reposition_telegraph(
    screen,
    warden,
    current_time,
):
    target = warden.warden_reposition_target
    if target is None or warden.health <= 0:
        return

    origin_center = (
        MAP_OFFSET_X + warden.column * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + warden.row * TILE_SIZE + TILE_SIZE // 2,
    )
    target_center = (
        MAP_OFFSET_X + target[0] * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + target[1] * TILE_SIZE + TILE_SIZE // 2,
    )
    pulse = (math.sin(current_time / 105) + 1) / 2
    effect = pygame.Surface(
        (MAP_WIDTH, MAP_HEIGHT),
        pygame.SRCALPHA,
    )
    local_origin = (
        origin_center[0] - MAP_OFFSET_X,
        origin_center[1] - MAP_OFFSET_Y,
    )
    local_target = (
        target_center[0] - MAP_OFFSET_X,
        target_center[1] - MAP_OFFSET_Y,
    )

    segment_count = 7
    for segment_index in range(segment_count):
        if segment_index % 2:
            continue
        start_progress = segment_index / segment_count
        end_progress = min(
            1,
            (segment_index + 0.7) / segment_count,
        )
        start = (
            round(
                local_origin[0]
                + (local_target[0] - local_origin[0]) * start_progress
            ),
            round(
                local_origin[1]
                + (local_target[1] - local_origin[1]) * start_progress
            ),
        )
        end = (
            round(
                local_origin[0]
                + (local_target[0] - local_origin[0]) * end_progress
            ),
            round(
                local_origin[1]
                + (local_target[1] - local_origin[1]) * end_progress
            ),
        )
        pygame.draw.line(
            effect,
            (166, 73, 180, round(90 + pulse * 65)),
            start,
            end,
            2,
        )

    radius = round(9 + pulse * 4)
    pygame.draw.circle(
        effect,
        (190, 90, 203, round(155 + pulse * 75)),
        local_target,
        radius,
        width=2,
    )
    pygame.draw.polygon(
        effect,
        (229, 151, 220, round(150 + pulse * 85)),
        [
            (local_target[0], local_target[1] - 7),
            (local_target[0] + 7, local_target[1]),
            (local_target[0], local_target[1] + 7),
            (local_target[0] - 7, local_target[1]),
        ],
        width=2,
    )
    screen.blit(effect, (MAP_OFFSET_X, MAP_OFFSET_Y))


def draw_act_one_boss_effects(
    screen,
    enemies,
    act_number,
    current_time,
    font=None,
):
    if act_number >= 2:
        return

    warden = next(
        (enemy for enemy in enemies if enemy.type == "warden"),
        None,
    )
    if warden is None:
        return

    _draw_act_one_warden_reposition_telegraph(
        screen,
        warden,
        current_time,
    )

    _draw_act_one_warden_phase_transition(
        screen,
        warden,
        current_time,
        font,
    )

    elapsed = current_time - warden.attack_animation_started_at
    duration = 460
    if (
        warden.attack_animation_started_at <= 0
        or not 0 <= elapsed < duration
        or warden.attack_effect_mode not in ("cross", "sweep", "runes")
        or not warden.attack_effect_positions
    ):
        return

    progress = elapsed / duration
    target_rows = {row for _, row in warden.attack_effect_positions}
    sweep_is_horizontal = len(target_rows) == 1
    if warden.attack_effect_mode == "sweep":
        columns = [column for column, _ in warden.attack_effect_positions]
        rows = [row for _, row in warden.attack_effect_positions]
        visibility = max(0, 1 - progress)
        travel_progress = min(1, progress * 1.65)
        glow_color = (177, 69, 24)
        core_color = (
            255,
            180,
            77,
        )
        if sweep_is_horizontal:
            start_x = MAP_OFFSET_X + min(columns) * TILE_SIZE
            end_x = MAP_OFFSET_X + (max(columns) + 1) * TILE_SIZE
            sweep_y = MAP_OFFSET_Y + rows[0] * TILE_SIZE + TILE_SIZE // 2
            current_end_x = round(
                start_x + (end_x - start_x) * travel_progress
            )
            pygame.draw.line(
                screen,
                glow_color,
                (start_x, sweep_y),
                (current_end_x, sweep_y),
                max(2, round(8 * visibility)),
            )
            pygame.draw.line(
                screen,
                core_color,
                (start_x, sweep_y),
                (current_end_x, sweep_y),
                max(1, round(3 * visibility)),
            )
        else:
            sweep_x = MAP_OFFSET_X + columns[0] * TILE_SIZE + TILE_SIZE // 2
            start_y = MAP_OFFSET_Y + min(rows) * TILE_SIZE
            end_y = MAP_OFFSET_Y + (max(rows) + 1) * TILE_SIZE
            current_end_y = round(
                start_y + (end_y - start_y) * travel_progress
            )
            pygame.draw.line(
                screen,
                glow_color,
                (sweep_x, start_y),
                (sweep_x, current_end_y),
                max(2, round(8 * visibility)),
            )
            pygame.draw.line(
                screen,
                core_color,
                (sweep_x, start_y),
                (sweep_x, current_end_y),
                max(1, round(3 * visibility)),
            )
        return

    for column, row in warden.attack_effect_positions:
        _draw_act_one_warden_attack_impact(
            screen,
            column,
            row,
            warden.attack_effect_mode,
            progress,
            sweep_is_horizontal,
        )


def draw_player_attack_markers(screen, attack_targets):
    for column, row in attack_targets:
        target_rectangle = pygame.Rect(
            MAP_OFFSET_X + column * TILE_SIZE,
            MAP_OFFSET_Y + row * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(
            screen,
            PLAYER_ATTACK_TILE_COLOR,
            target_rectangle,
        )
        pygame.draw.rect(
            screen,
            PLAYER_ATTACK_BORDER_COLOR,
            target_rectangle,
            width=3,
        )


def draw_player(
    screen,
    column,
    row,
    health,
    max_health,
    player_class,
    act_number,
    sprites,
    invisibility_turns,
    current_time=0,
    potion_effect_started_at=0,
    hit_animation_started_at=-1,
    hit_origin=None,
    attack_animation_started_at=0,
    attack_target=None,
    movement_animation_started_at=0,
    movement_origin=None,
    dodge_animation_started_at=-1,
    dodge_origin=None,
    death_animation_started_at=-1,
    hit_damage=0,
    damage_font=None,
    act_two_facing_direction=(0, 1),
    act_two_blocked_movement_started_at=-1,
    act_two_blocked_movement_direction=(0, 1),
):
    if act_number == 2 and player_class is not None:
        draw_act_two_player_actor(
            screen,
            sprites,
            column,
            row,
            health,
            max_health,
            player_class,
            invisibility_turns,
            current_time,
            movement_animation_started_at,
            movement_origin,
            potion_effect_started_at,
            hit_animation_started_at,
            hit_origin,
            death_animation_started_at,
            hit_damage,
            damage_font,
            act_two_facing_direction,
            act_two_blocked_movement_started_at,
            act_two_blocked_movement_direction,
            attack_animation_started_at,
            attack_target,
        )
        return

    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
    movement_offset_x = 0
    movement_offset_y = 0
    movement_progress = None
    cloak_drag_x = 0
    cloak_drag_y = 0
    hit_effect_active = False
    hit_flash_active = False
    dodge_effect_active = False
    dodge_offset_x = 0
    dodge_offset_y = 0
    if act_number < 2:
        movement_offset_x, movement_offset_y = (
            _act_one_movement_offset(
                column,
                row,
                movement_origin,
                current_time,
                movement_animation_started_at,
                "hero",
            )
        )
        movement_progress = _act_one_movement_progress(
            movement_origin,
            current_time,
            movement_animation_started_at,
            "hero",
        )
        if movement_progress is not None:
            cloak_drag = round(
                math.sin(math.pi * movement_progress) * 3
            )
            cloak_drag_x = (
                movement_origin[0] - column
            ) * cloak_drag
            cloak_drag_y = (
                movement_origin[1] - row
            ) * cloak_drag
        center_x += movement_offset_x
        center_y += movement_offset_y
        attack_offset_x, attack_offset_y = _act_one_attack_lunge(
            column,
            row,
            attack_target,
            current_time,
            attack_animation_started_at,
        )
        center_x += attack_offset_x
        center_y += attack_offset_y
        (
            hit_effect_active,
            recoil_x,
            recoil_y,
            hit_flash_active,
        ) = _act_one_hit_reaction(
            column,
            row,
            current_time,
            hit_animation_started_at,
            hit_origin,
        )
        center_x += recoil_x
        center_y += recoil_y
        if not hit_effect_active:
            (
                dodge_effect_active,
                dodge_offset_x,
                dodge_offset_y,
            ) = _act_one_dodge_reaction(
                column,
                row,
                current_time,
                dodge_animation_started_at,
                dodge_origin,
            )
            center_x += dodge_offset_x
            center_y += dodge_offset_y
    if act_number >= 2 and player_class is not None:
        player_sprite = sprites[f"player_{player_class}"]

        if invisibility_turns > 0:
            player_sprite = player_sprite.copy()
            player_sprite.set_alpha(90)

        screen.blit(
            player_sprite,
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
    else:
        cloak_color = ACT_ONE_PLAYER_CLOAK
        edge_color = ACT_ONE_PLAYER_EDGE
        face_color = ACT_ONE_PLAYER_FACE
        if hit_flash_active:
            flash_is_bright = (
                (current_time - hit_animation_started_at) // 45
            ) % 2 == 0
            if flash_is_bright:
                cloak_color = (211, 204, 199)
                edge_color = (244, 231, 216)
                face_color = (255, 242, 224)
            else:
                cloak_color = (126, 47, 55)
                edge_color = (211, 81, 82)
                face_color = (231, 166, 149)

        if dodge_effect_active:
            _draw_act_one_dodge_effect(
                screen,
                center_x,
                center_y,
                current_time,
                dodge_animation_started_at,
                dodge_origin,
                dodge_offset_x,
                dodge_offset_y,
            )
        _draw_act_one_movement_accent(
            screen,
            center_x,
            center_y,
            column,
            row,
            movement_origin,
            current_time,
            movement_animation_started_at,
            "hero",
        )
        _draw_act_one_shadow(screen, center_x, center_y)
        pygame.draw.polygon(
            screen,
            (18, 20, 26),
            [
                (center_x, center_y - 12),
                (center_x + 9, center_y - 3),
                (
                    center_x + 11 + cloak_drag_x,
                    center_y + 10 + cloak_drag_y,
                ),
                (
                    center_x - 11 + cloak_drag_x,
                    center_y + 10 + cloak_drag_y,
                ),
                (center_x - 9, center_y - 3),
            ],
        )
        pygame.draw.polygon(
            screen,
            cloak_color,
            [
                (center_x, center_y - 10),
                (center_x + 7, center_y - 2),
                (
                    center_x + 8 + cloak_drag_x,
                    center_y + 8 + cloak_drag_y,
                ),
                (
                    center_x - 8 + cloak_drag_x,
                    center_y + 8 + cloak_drag_y,
                ),
                (center_x - 7, center_y - 2),
            ],
        )
        pygame.draw.circle(
            screen,
            edge_color,
            (center_x, center_y - 5),
            7,
        )
        pygame.draw.circle(
            screen,
            (25, 29, 37),
            (center_x, center_y - 4),
            5,
        )
        pygame.draw.line(
            screen,
            edge_color,
            (center_x - 7, center_y + 1),
            (center_x - 8, center_y + 7),
            2,
        )
        pygame.draw.line(
            screen,
            (82, 94, 107),
            (center_x, center_y + 1),
            (center_x, center_y + 7),
        )
        pygame.draw.circle(
            screen,
            ACT_ONE_GOLD,
            (center_x, center_y + 1),
            1,
        )
        pygame.draw.rect(
            screen,
            face_color,
            (center_x - 3, center_y - 5, 2, 1),
        )
        pygame.draw.rect(
            screen,
            face_color,
            (center_x + 2, center_y - 5, 2, 1),
        )

        if act_number < 2:
            _draw_act_one_healing_effect(
                screen,
                center_x,
                center_y,
                current_time,
                potion_effect_started_at,
            )
            if hit_effect_active:
                _draw_act_one_hit_effect(
                    screen,
                    center_x,
                    center_y,
                    current_time,
                    hit_animation_started_at,
                )

    health_ratio = health / max_health
    bar_x = MAP_OFFSET_X + column * TILE_SIZE + 4 + movement_offset_x
    bar_y = (
        MAP_OFFSET_Y
        + (row + 1) * TILE_SIZE
        - 5
        + movement_offset_y
    )
    bar_width = TILE_SIZE - 8
    bar_height = 4

    pygame.draw.rect(
        screen,
        HEALTH_BAR_BACKGROUND,
        (bar_x, bar_y, bar_width, bar_height),
    )
    player_health_color = PLAYER_HEALTH_BAR_COLOR
    if act_number < 2:
        if health_ratio > 0.6:
            player_health_color = ACT_ONE_HEALTH_HIGH
        elif health_ratio > 0.3:
            player_health_color = ACT_ONE_HEALTH_MID
        else:
            player_health_color = ACT_ONE_HEALTH_LOW

    pygame.draw.rect(
        screen,
        (
            (230, 69, 74)
            if hit_effect_active
            else player_health_color
        ),
        (bar_x, bar_y, int(bar_width * health_ratio), bar_height),
    )












def draw_enemy(
    screen,
    enemy,
    act_number,
    sprites,
    current_time=0,
    damage_font=None,
):
    if act_number >= 2:
        draw_act_two_enemy(
            screen,
            enemy,
            sprites,
            current_time,
            damage_font,
        )
        return

    padding = TILE_SIZE // 5
    column = enemy["column"]
    row = enemy["row"]
    x = MAP_OFFSET_X + column * TILE_SIZE + padding
    y = MAP_OFFSET_Y + row * TILE_SIZE + padding
    size = TILE_SIZE - padding * 2
    color = (
        enemy["color"]
        if enemy["is_aggro"]
        else enemy["sleeping_color"]
    )
    if enemy["health"] <= 0:
        _draw_act_one_enemy_death(
            screen,
            enemy,
            current_time,
            _act_one_enemy_color(color, enemy["is_aggro"]),
        )
        return

    color = _act_one_enemy_color(color, enemy["is_aggro"])
    movement_offset_x, movement_offset_y = _act_one_movement_offset(
        column,
        row,
        enemy.get("movement_origin"),
        current_time,
        enemy.get("movement_animation_started_at", 0),
        enemy["type"],
    )
    x += movement_offset_x
    y += movement_offset_y
    hit_animation_started_at = enemy.get(
        "hit_animation_started_at",
        -1,
    )
    (
        hit_effect_active,
        recoil_x,
        recoil_y,
        hit_flash_active,
    ) = _act_one_hit_reaction(
        column,
        row,
        current_time,
        hit_animation_started_at,
        enemy.get("hit_origin"),
    )
    x += recoil_x
    y += recoil_y
    if hit_flash_active:
        flash_is_bright = (
            (current_time - hit_animation_started_at) // 45
        ) % 2 == 0
        color = (
            (224, 216, 207)
            if flash_is_bright
            else (171, 54, 61)
        )

    _draw_act_one_movement_accent(
        screen,
        x + size // 2,
        y + size // 2,
        column,
        row,
        enemy.get("movement_origin"),
        current_time,
        enemy.get("movement_animation_started_at", 0),
        enemy["type"],
    )
    if (
        enemy["type"] == "warden"
        and enemy.get("second_phase_announced", False)
    ):
        aura = pygame.Surface((48, 48), pygame.SRCALPHA)
        aura_pulse = (math.sin(current_time / 120) + 1) / 2
        pygame.draw.circle(
            aura,
            (165, 49, 177, round(55 + aura_pulse * 45)),
            (24, 24),
            round(14 + aura_pulse * 3),
            width=3,
        )
        pygame.draw.circle(
            aura,
            (218, 73, 111, round(35 + aura_pulse * 35)),
            (24, 24),
            round(19 + aura_pulse * 2),
            width=2,
        )
        screen.blit(
            aura,
            (x + size // 2 - 24, y + size // 2 - 24),
        )

    _draw_act_one_enemy(screen, enemy, x, y, size, color)
    if hit_effect_active:
        _draw_act_one_hit_effect(
            screen,
            x + size // 2,
            y + size // 2,
            current_time,
            enemy["hit_animation_started_at"],
        )
        if enemy.get("hit_critical", False):
            _draw_act_one_critical_hit_effect(
                screen,
                x + size // 2,
                y + size // 2,
                current_time,
                enemy["hit_animation_started_at"],
            )

    health_ratio = enemy["health"] / enemy["max_health"]
    bar_x = MAP_OFFSET_X + column * TILE_SIZE + 4 + movement_offset_x
    bar_y = (
        MAP_OFFSET_Y
        + (row + 1) * TILE_SIZE
        - 5
        + movement_offset_y
    )
    bar_width = TILE_SIZE - 8
    pygame.draw.rect(
        screen,
        HEALTH_BAR_BACKGROUND,
        (bar_x, bar_y, bar_width, 4),
    )
    pygame.draw.rect(
        screen,
        (236, 75, 78) if hit_effect_active else HEALTH_BAR_COLOR,
        (bar_x, bar_y, int(bar_width * health_ratio), 4),
    )

    if enemy["attack_targets"]:
        warning_x = (
            MAP_OFFSET_X
            + column * TILE_SIZE
            + TILE_SIZE // 2
            + movement_offset_x
        )
        warning_top = (
            MAP_OFFSET_Y
            + row * TILE_SIZE
            + 8
            + movement_offset_y
        )
        pygame.draw.line(
            screen,
            ATTACK_WARNING_COLOR,
            (warning_x, warning_top),
            (warning_x, warning_top + 9),
            3,
        )
        pygame.draw.circle(
            screen,
            ATTACK_WARNING_COLOR,
            (warning_x, warning_top + 14),
            2,
        )


def draw_key(screen, column, row, act_number, sprites):
    if act_number >= 2:
        _draw_act_two_key(screen, column, row, sprites)
        return

    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2

    _draw_act_one_glow(screen, (center_x, center_y), (132, 91, 28), 17)
    pygame.draw.circle(
        screen,
        (16, 14, 13),
        (center_x - 7, center_y + 1),
        7,
        width=3,
    )
    pygame.draw.circle(
        screen,
        ACT_ONE_GOLD,
        (center_x - 7, center_y),
        6,
        width=2,
    )
    pygame.draw.circle(
        screen,
        ACT_ONE_GOLD_LIGHT,
        (center_x - 7, center_y),
        3,
        width=1,
    )
    pygame.draw.line(
        screen,
        ACT_ONE_GOLD,
        (center_x - 1, center_y),
        (center_x + 12, center_y),
        3,
    )
    pygame.draw.line(
        screen,
        ACT_ONE_GOLD_LIGHT,
        (center_x, center_y - 1),
        (center_x + 10, center_y - 1),
    )
    pygame.draw.line(
        screen,
        ACT_ONE_GOLD,
        (center_x + 7, center_y),
        (center_x + 7, center_y + 5),
        2,
    )
    pygame.draw.line(
        screen,
        ACT_ONE_GOLD,
        (center_x + 11, center_y),
        (center_x + 11, center_y + 4),
        2,
    )


def draw_boss_door(screen, column, row, is_open):
    cell_x = MAP_OFFSET_X + column * TILE_SIZE
    cell_y = MAP_OFFSET_Y + row * TILE_SIZE
    frame_color = (115, 75, 130)

    pygame.draw.rect(
        screen,
        frame_color,
        (cell_x + 3, cell_y + 2, TILE_SIZE - 6, TILE_SIZE - 4),
        width=3,
        border_radius=3,
    )

    if is_open:
        return

    pygame.draw.rect(
        screen,
        (55, 35, 62),
        (cell_x + 7, cell_y + 5, TILE_SIZE - 14, TILE_SIZE - 7),
        border_radius=2,
    )
    pygame.draw.line(
        screen,
        frame_color,
        (cell_x + TILE_SIZE // 2, cell_y + 7),
        (cell_x + TILE_SIZE // 2, cell_y + TILE_SIZE - 5),
        2,
    )
    pygame.draw.circle(
        screen,
        ATTACK_WARNING_COLOR,
        (cell_x + TILE_SIZE // 2, cell_y + TILE_SIZE // 2),
        3,
    )


def draw_potion(screen, column, row, act_number, sprites):
    if act_number >= 2:
        _draw_act_two_potion(screen, column, row, sprites)
        return

    cell_x = MAP_OFFSET_X + column * TILE_SIZE
    cell_y = MAP_OFFSET_Y + row * TILE_SIZE
    potion_sprite = sprites.get("act_one_potion")
    if potion_sprite is not None:
        center = (
            cell_x + TILE_SIZE // 2,
            cell_y + TILE_SIZE // 2,
        )
        _draw_act_one_glow(screen, center, (190, 35, 45), 16)
        screen.blit(
            potion_sprite,
            potion_sprite.get_rect(center=center),
        )
        return

    bottle_rectangle = pygame.Rect(
        cell_x + TILE_SIZE // 2 - 6,
        cell_y + 11,
        12,
        17,
    )

    _draw_act_one_glow(
        screen,
        (cell_x + TILE_SIZE // 2, cell_y + 19),
        (190, 35, 45),
        16,
    )
    pygame.draw.rect(
        screen,
        (12, 18, 20),
        bottle_rectangle.inflate(4, 3).move(1, 2),
        border_radius=5,
    )
    pygame.draw.rect(
        screen,
        (129, 20, 31),
        bottle_rectangle,
        border_radius=4,
    )
    pygame.draw.rect(
        screen,
        (255, 112, 105),
        (bottle_rectangle.x + 3, bottle_rectangle.y + 8, 3, 6),
        border_radius=1,
    )
    pygame.draw.rect(
        screen,
        ACT_ONE_IRON_LIGHT,
        (cell_x + TILE_SIZE // 2 - 4, cell_y + 7, 8, 5),
        border_radius=1,
    )
    pygame.draw.line(
        screen,
        (137, 134, 129),
        (cell_x + TILE_SIZE // 2 - 2, cell_y + 8),
        (cell_x + TILE_SIZE // 2 + 2, cell_y + 8),
    )


def draw_coin(screen, column, row, act_number, sprites):
    if act_number >= 2:
        _draw_act_two_coin(screen, column, row, sprites)
        return

    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2

    _draw_act_one_glow(screen, (center_x, center_y), (133, 88, 24), 15)
    pygame.draw.ellipse(
        screen,
        (12, 11, 12),
        (center_x - 8, center_y - 5, 17, 13),
    )
    pygame.draw.circle(
        screen,
        ACT_ONE_GOLD,
        (center_x, center_y),
        7,
    )
    pygame.draw.circle(
        screen,
        ACT_ONE_GOLD_LIGHT,
        (center_x, center_y),
        5,
        width=1,
    )
    pygame.draw.line(
        screen,
        (90, 60, 25),
        (center_x, center_y - 3),
        (center_x, center_y + 3),
        2,
    )




def _draw_act_one_chest_opening_effect(
    screen,
    cell_x,
    cell_y,
    current_time,
    effect_started_at,
):
    duration = 680
    elapsed = current_time - effect_started_at
    if effect_started_at < 0 or not 0 <= elapsed < duration:
        return

    progress = elapsed / duration
    visibility = 1 - progress
    effect = pygame.Surface((64, 64), pygame.SRCALPHA)
    center = 32
    burst = math.sin(math.pi * min(1.0, progress * 1.45))
    pygame.draw.polygon(
        effect,
        (210, 155, 54, round(52 * burst)),
        (
            (center - 15, center + 7),
            (center - 7, center - 23),
            (center + 7, center - 23),
            (center + 15, center + 7),
        ),
    )
    pygame.draw.circle(
        effect,
        (237, 194, 91, round(145 * visibility)),
        (center, center + 2),
        round(8 + progress * 19),
        width=2,
    )
    for spark_index in range(7):
        angle = -math.pi + spark_index * math.pi / 6
        spark_distance = 7 + progress * (14 + spark_index % 3 * 3)
        spark_x = round(center + math.cos(angle) * spark_distance)
        spark_y = round(
            center
            + 2
            + math.sin(angle) * spark_distance
            + progress * progress * 13
        )
        pygame.draw.circle(
            effect,
            (244, 202, 101, round(220 * visibility)),
            (spark_x, spark_y),
            1 if spark_index % 2 else 2,
        )
    screen.blit(effect, (cell_x - 16, cell_y - 16))


def draw_chest(screen, chest, act_number, sprites, current_time=0):
    cell_x = MAP_OFFSET_X + chest["column"] * TILE_SIZE
    cell_y = MAP_OFFSET_Y + chest["row"] * TILE_SIZE

    if act_number >= 2:
        _draw_act_two_chest(screen, chest, sprites)
        return

    if chest["is_open"]:
        effect_started_at = chest.get("open_animation_started_at", -1)
        elapsed = current_time - effect_started_at
        opening_progress = 1.0
        shake_x = 0
        if effect_started_at >= 0 and 0 <= elapsed < 680:
            opening_progress = min(1.0, elapsed / 230)
            opening_progress = 1 - (1 - opening_progress) ** 3
            if elapsed < 120:
                shake_x = -1 if (elapsed // 24) % 2 else 1
            _draw_act_one_chest_opening_effect(
                screen,
                cell_x,
                cell_y,
                current_time,
                effect_started_at,
            )
        chest_x = cell_x + shake_x
        lid_y = cell_y + 10 - round(opening_progress * 3)
        _draw_act_one_shadow(
            screen,
            chest_x + TILE_SIZE // 2,
            cell_y + TILE_SIZE // 2,
            25,
        )
        pygame.draw.rect(
            screen,
            (45, 31, 28),
            (chest_x + 4, cell_y + 17, TILE_SIZE - 8, 10),
            border_radius=2,
        )
        pygame.draw.rect(
            screen,
            (134, 94, 37),
            (chest_x + 8, cell_y + 16, TILE_SIZE - 16, 3),
        )
        pygame.draw.rect(
            screen,
            (66, 43, 34),
            (chest_x + 5, lid_y, TILE_SIZE - 10, 7),
            border_radius=2,
        )
        pygame.draw.line(
            screen,
            ACT_ONE_IRON_LIGHT,
            (chest_x + 5, cell_y + 16),
            (chest_x + TILE_SIZE - 5, cell_y + 16),
            2,
        )
        if effect_started_at >= 0 and 0 <= elapsed < 300:
            lock_fall = min(1.0, elapsed / 300)
            pygame.draw.rect(
                screen,
                ACT_ONE_GOLD,
                (
                    chest_x + TILE_SIZE // 2 - 2 + round(lock_fall * 5),
                    cell_y + 17 + round(lock_fall * lock_fall * 9),
                    4,
                    5,
                ),
                border_radius=1,
            )
        return

    _draw_act_one_shadow(
        screen,
        cell_x + TILE_SIZE // 2,
        cell_y + TILE_SIZE // 2,
        26,
    )
    pygame.draw.rect(
        screen,
        (31, 28, 30),
        (cell_x + 3, cell_y + 8, TILE_SIZE - 6, 20),
        border_radius=3,
    )
    pygame.draw.rect(
        screen,
        (73, 46, 35),
        (cell_x + 5, cell_y + 10, TILE_SIZE - 10, 16),
        border_radius=2,
    )
    pygame.draw.line(
        screen,
        (117, 75, 48),
        (cell_x + 6, cell_y + 11),
        (cell_x + TILE_SIZE - 7, cell_y + 11),
    )
    pygame.draw.rect(
        screen,
        ACT_ONE_IRON,
        (cell_x + TILE_SIZE // 2 - 3, cell_y + 8, 6, 20),
    )
    pygame.draw.rect(
        screen,
        ACT_ONE_GOLD,
        (cell_x + TILE_SIZE // 2 - 2, cell_y + 16, 4, 6),
        border_radius=1,
    )


def draw_stairs(
    screen,
    column,
    row,
    is_open,
    act_number,
    sprites,
):
    if act_number >= 2:
        _draw_act_two_stairs(screen, column, row, is_open, sprites)
        return

    cell_x = MAP_OFFSET_X + column * TILE_SIZE
    cell_y = MAP_OFFSET_Y + row * TILE_SIZE
    center = (cell_x + TILE_SIZE // 2, cell_y + TILE_SIZE // 2)
    if is_open:
        _draw_act_one_glow(screen, center, (89, 100, 132), 20)
    frame_color = (103, 104, 115) if is_open else (60, 59, 67)
    pygame.draw.arc(
        screen,
        frame_color,
        (cell_x + 6, cell_y + 4, TILE_SIZE - 12, 23),
        0,
        3.14159,
        3,
    )
    pygame.draw.line(
        screen,
        frame_color,
        (cell_x + 6, cell_y + 15),
        (cell_x + 6, cell_y + 28),
        3,
    )
    pygame.draw.line(
        screen,
        frame_color,
        (cell_x + TILE_SIZE - 6, cell_y + 15),
        (cell_x + TILE_SIZE - 6, cell_y + 28),
        3,
    )
    pygame.draw.rect(
        screen,
        (11, 12, 17),
        (cell_x + 9, cell_y + 14, TILE_SIZE - 18, 14),
    )
    for step_number in range(3):
        step_y = cell_y + 20 + step_number * 4
        inset = step_number * 2
        pygame.draw.line(
            screen,
            frame_color,
            (cell_x + 9 - inset, step_y),
            (cell_x + TILE_SIZE - 9 + inset, step_y),
            2,
        )
