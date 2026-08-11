import math

import pygame

from acts.act_two.presentation import draw_act_two_player_actor
from acts.act_two.settings import (
    FLOOR_DECOR_CLUSTER_PERCENT,
    FLOOR_DECOR_CLUSTER_SIZE_TILES,
    FLOOR_DECOR_DENSE_PERCENT,
    FLOOR_DECOR_MIN_SPACING_TILES,
    FLOOR_DECOR_SPARSE_PERCENT,
    FLOOR_DECOR_VARIANT_WEIGHTS,
    FLOOR_TILE_VARIANT_WEIGHTS,
    WALL_DECOR_MIN_SPACING_TILES,
    WALL_OVERLAY_MIN_SPACING_TILES,
    WALL_OVERLAY_VARIANT_WEIGHTS,
    WALL_TILE_VARIANT_WEIGHTS,
    WALL_TORCH_MIN_SPACING_TILES,
    WALL_WEAR_REPEAT_MIN_SPACING_TILES,
)
from presentation.layout import (
    ACT_TWO_VIEW_HEIGHT,
    ACT_TWO_VIEW_WIDTH,
    ACT_TWO_VIEW_X,
    ACT_TWO_VIEW_Y,
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
ACT_TWO_GRID_COLOR = (20, 22, 28)
ACT_TWO_MORTAR_DARK = (17, 20, 25)
ACT_TWO_MORTAR_LIGHT = (56, 61, 66)
ACT_TWO_DAMP = (20, 49, 53)
ACT_TWO_RUNE = (61, 116, 123)
ACT_TWO_HIT_FEEDBACK_MS = 650
ACT_TWO_HIT_REACTION_MS = 230
ACT_TWO_ENEMY_ATTACK_FRAME_MS = 240
ACT_TWO_DEATH_IMPACT_MS = 150
ACT_TWO_DEATH_SETTLE_MS = 430
ACT_TWO_DEATH_BURST_MS = 360
ACT_TWO_GOBLIN_DEATH_MS = 920
ACT_TWO_ARCHER_DEATH_MS = 880
ACT_TWO_BRUTE_DEATH_MS = 1120
ACT_TWO_SENTINEL_DEATH_MS = 1060
ACT_TWO_PRIEST_DEATH_MS = 1040
ACT_TWO_CLASS_EFFECT_COLORS = {
    "warrior": (218, 76, 54),
    "rogue": (161, 73, 202),
    "mage": (61, 146, 216),
}
ACT_TWO_EXPOSED_WALL_SPRITES = {
    "wall_torch",
    "wall_chains",
    "wall_iron_shackle",
    "wall_skull_niche",
}
ACT_TWO_WEAR_WALL_SPRITES = {
    "wall_broken",
    "wall_damp",
}
ACT_TWO_SPACED_WALL_SPRITES = {
    "wall_chains",
    "wall_iron_shackle",
    "wall_skull_niche",
}
ACT_TWO_WALL_OVERLAY_BASE_SPRITES = {
    "wall",
    "wall_broken",
    "wall_damp",
}


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


def draw_act_two_player_attack_effect(
    screen,
    act_number,
    column,
    row,
    target,
    player_class,
    current_time,
    attack_started_at,
    critical=False,
):
    duration = 390 if critical else 310
    elapsed = current_time - attack_started_at
    if (
        act_number != 2
        or target is None
        or player_class not in ACT_TWO_CLASS_EFFECT_COLORS
        or attack_started_at <= 0
        or not 0 <= elapsed < duration
    ):
        return

    progress = elapsed / duration
    visibility = max(0, 1 - progress)
    impact = math.sin(math.pi * min(1, progress * 1.45))
    direction_x = target[0] - column
    direction_y = target[1] - row
    length = max(1, math.hypot(direction_x, direction_y))
    direction_x /= length
    direction_y /= length
    perpendicular_x = -direction_y
    perpendicular_y = direction_x
    origin = (
        MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2,
    )
    destination = (
        MAP_OFFSET_X + target[0] * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + target[1] * TILE_SIZE + TILE_SIZE // 2,
    )
    color = ACT_TWO_CLASS_EFFECT_COLORS[player_class]
    effect = pygame.Surface((MAP_WIDTH, MAP_HEIGHT), pygame.SRCALPHA)
    local_origin = (
        origin[0] - MAP_OFFSET_X,
        origin[1] - MAP_OFFSET_Y,
    )
    local_destination = (
        destination[0] - MAP_OFFSET_X,
        destination[1] - MAP_OFFSET_Y,
    )

    if player_class == "warrior":
        strike_delay = 60
        if elapsed < strike_delay:
            return
        strike_progress = min(
            1.0,
            (elapsed - strike_delay) / (duration - strike_delay),
        )
        visibility = max(0.0, 1 - strike_progress)
        impact = math.sin(
            math.pi * min(1.0, strike_progress * 1.55)
        )
        if abs(direction_y) > 0.5 and abs(direction_x) < 0.5:
            flash_start = (
                round(local_origin[0] + direction_x * 12),
                round(local_origin[1] + direction_y * 12),
            )
            flash_tip = (
                round(
                    local_destination[0]
                    + direction_x * (5 + impact * 5)
                ),
                round(
                    local_destination[1]
                    + direction_y * (5 + impact * 5)
                ),
            )
            flash_width = 4 + round(impact * 4)
            flash_base_left = (
                round(flash_start[0] - perpendicular_x * 2),
                round(flash_start[1] - perpendicular_y * 2),
            )
            flash_base_right = (
                round(flash_start[0] + perpendicular_x * 2),
                round(flash_start[1] + perpendicular_y * 2),
            )
            flash_tip_left = (
                round(
                    flash_tip[0]
                    - direction_x * 7
                    - perpendicular_x * flash_width
                ),
                round(
                    flash_tip[1]
                    - direction_y * 7
                    - perpendicular_y * flash_width
                ),
            )
            flash_tip_right = (
                round(
                    flash_tip[0]
                    - direction_x * 7
                    + perpendicular_x * flash_width
                ),
                round(
                    flash_tip[1]
                    - direction_y * 7
                    + perpendicular_y * flash_width
                ),
            )
            pygame.draw.polygon(
                effect,
                (205, 37, 48, round(210 * visibility)),
                (
                    flash_base_left,
                    flash_tip_left,
                    flash_tip,
                    flash_tip_right,
                    flash_base_right,
                ),
            )
            pygame.draw.line(
                effect,
                (255, 111, 88, round(250 * visibility)),
                flash_start,
                flash_tip,
                2,
            )
        else:
            sweep_center = (
                local_destination[0] - round(direction_x * 5),
                local_destination[1] - round(direction_y * 5),
            )
            sweep_length = 15 + round(impact * 5)
            arc_points = []
            for point_index in range(9):
                arc_position = -1.0 + point_index / 4
                across = arc_position * sweep_length
                forward_curve = (
                    (1 - arc_position * arc_position)
                    * (7 + round(impact * 5))
                    - 3
                )
                arc_points.append(
                    (
                        round(
                            sweep_center[0]
                            + perpendicular_x * across
                            + direction_x * forward_curve
                        ),
                        round(
                            sweep_center[1]
                            + perpendicular_y * across
                            + direction_y * forward_curve
                        ),
                    )
                )
            pygame.draw.lines(
                effect,
                (205, 37, 48, round(225 * visibility)),
                False,
                arc_points,
                7 if critical else 5,
            )
            pygame.draw.lines(
                effect,
                (255, 111, 88, round(250 * visibility)),
                False,
                arc_points,
                2,
            )
        for spark_index in range(6 if critical else 4):
            angle = spark_index * math.tau / (6 if critical else 4)
            distance = 6 + strike_progress * 16
            spark_end = (
                round(local_destination[0] + math.cos(angle) * distance),
                round(local_destination[1] + math.sin(angle) * distance),
            )
            pygame.draw.line(
                effect,
                (242, 72, 58, round(205 * visibility)),
                local_destination,
                spark_end,
                2,
            )
    elif player_class == "rogue":
        strike_delay = 35
        if elapsed < strike_delay:
            return
        strike_progress = min(
            1.0,
            (elapsed - strike_delay) / (duration - strike_delay),
        )
        visibility = max(0.0, 1 - strike_progress)
        downward_stab = direction_y > 0.5 and abs(direction_x) < 0.5
        upward_stab = direction_y < -0.5 and abs(direction_x) < 0.5
        travel = min(1, strike_progress * 2.2)
        trail_reach = min(travel, 0.75)
        trail_end = (
            round(
                local_origin[0]
                + (local_destination[0] - local_origin[0]) * trail_reach
            ),
            round(
                local_origin[1]
                + (local_destination[1] - local_origin[1]) * trail_reach
            ),
        )
        if travel > 0.4 and not downward_stab and not upward_stab:
            pygame.draw.line(
                effect,
                (*color, round(105 * visibility)),
                (
                    round(local_origin[0] + direction_x * 13),
                    round(local_origin[1] + direction_y * 13),
                ),
                trail_end,
                2,
            )
        slash_center = (
            local_destination[0] - direction_x * 5,
            local_destination[1] - direction_y * 5,
        )
        slash_span = 4 if downward_stab else 9
        slash_depth = 1 if downward_stab else 3
        if upward_stab:
            slash_start = (
                round(
                    local_origin[0]
                    + direction_x * 12
                    + perpendicular_x * 7
                ),
                round(
                    local_origin[1]
                    + direction_y * 12
                    + perpendicular_y * 7
                ),
            )
            full_slash_end = (
                round(
                    local_destination[0]
                    - direction_x * 6
                    + perpendicular_x * 4
                ),
                round(
                    local_destination[1]
                    - direction_y * 6
                    + perpendicular_y * 4
                ),
            )
            thrust_growth = min(1.0, strike_progress * 2.7)
            slash_end = (
                round(
                    slash_start[0]
                    + (full_slash_end[0] - slash_start[0])
                    * thrust_growth
                ),
                round(
                    slash_start[1]
                    + (full_slash_end[1] - slash_start[1])
                    * thrust_growth
                ),
            )
        else:
            slash_start = (
                round(
                    slash_center[0]
                    - perpendicular_x * slash_span
                    - direction_x * slash_depth
                ),
                round(
                    slash_center[1]
                    - perpendicular_y * slash_span
                    - direction_y * slash_depth
                ),
            )
            slash_end = (
                round(
                    slash_center[0]
                    + perpendicular_x * slash_span
                    + direction_x * slash_depth
                ),
                round(
                    slash_center[1]
                    + perpendicular_y * slash_span
                    + direction_y * slash_depth
                ),
            )
        pygame.draw.line(
            effect,
            (
                113,
                42,
                149,
                round((80 if downward_stab else 165) * visibility),
            ),
            slash_start,
            slash_end,
            (
                2
                if downward_stab
                else (3 if upward_stab else (5 if critical else 4))
            ),
        )
        pygame.draw.line(
            effect,
            (
                222,
                143,
                246,
                round((150 if downward_stab else 225) * visibility),
            ),
            slash_start,
            slash_end,
            1 if downward_stab or upward_stab else 2,
        )
        if upward_stab:
            pygame.draw.circle(
                effect,
                (235, 187, 255, round(190 * visibility)),
                slash_end,
                2 if critical else 1,
            )
    else:
        release_progress = max(0.0, (progress - 0.16) / 0.58)
        travel = min(1.0, release_progress)
        staff_origin = (
            local_origin[0] + direction_x * 10,
            local_origin[1]
            + direction_y * 10
            - (10 if abs(direction_x) > 0.5 else 0),
        )
        orb_center = (
            round(
                staff_origin[0]
                + (
                    local_destination[0]
                    - staff_origin[0]
                )
                * travel
            ),
            round(
                staff_origin[1]
                + (
                    local_destination[1]
                    - staff_origin[1]
                )
                * travel
            ),
        )
        if release_progress > 0:
            trail_start = (
                round(orb_center[0] - direction_x * (8 + travel * 8)),
                round(orb_center[1] - direction_y * (8 + travel * 8)),
            )
            pygame.draw.line(
                effect,
                (*color, round(135 * visibility)),
                trail_start,
                orb_center,
                5,
            )
            pygame.draw.circle(
                effect,
                (52, 118, 255, round(105 * visibility)),
                orb_center,
                9 if critical else 7,
            )
            pygame.draw.circle(
                effect,
                (76, 169, 255, round(235 * visibility)),
                orb_center,
                6 if critical else 5,
            )
            pygame.draw.circle(
                effect,
                (193, 238, 255, round(255 * visibility)),
                (
                    round(orb_center[0] - direction_x * 1 - perpendicular_x * 1),
                    round(orb_center[1] - direction_y * 1 - perpendicular_y * 1),
                ),
                2,
            )
        if travel >= 0.92:
            rune_radius = round(7 + progress * (12 if critical else 8))
            pygame.draw.circle(
                effect,
                (*color, round(190 * visibility)),
                local_destination,
                rune_radius,
                width=2,
            )
            pygame.draw.polygon(
                effect,
                (174, 226, 255, round(210 * visibility)),
                (
                    (local_destination[0], local_destination[1] - rune_radius),
                    (local_destination[0] + rune_radius, local_destination[1]),
                    (local_destination[0], local_destination[1] + rune_radius),
                    (local_destination[0] - rune_radius, local_destination[1]),
                ),
                width=1,
            )

    if critical:
        pygame.draw.circle(
            effect,
            (255, 221, 132, round(175 * visibility)),
            local_destination,
            round(8 + progress * 18),
            width=2,
        )
    screen.blit(effect, (MAP_OFFSET_X, MAP_OFFSET_Y))


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


def draw_act_two_pickup_effect(
    screen,
    act_number,
    sprites,
    kind,
    origin,
    current_time,
    effect_started_at,
):
    duration = 760
    elapsed = current_time - effect_started_at
    if (
        act_number != 2
        or kind not in ("potion", "gold", "key")
        or origin is None
        or effect_started_at < 0
        or not 0 <= elapsed < duration
    ):
        return

    progress = elapsed / duration
    center_x = MAP_OFFSET_X + origin[0] * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + origin[1] * TILE_SIZE + TILE_SIZE // 2
    effect_size = 80
    effect_center = effect_size // 2
    effect = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    colors = {
        "potion": ((183, 46, 59), (255, 126, 126)),
        "gold": ((194, 137, 31), (255, 226, 91)),
        "key": ((151, 110, 42), (240, 197, 94)),
    }
    sprite_names = {
        "potion": "potion",
        "gold": "coin",
        "key": "key",
    }
    base_color, bright_color = colors[kind]

    pull_progress = max(
        0.0,
        min(1.0, (progress - 0.12) / 0.42),
    )
    pull_progress = pull_progress * pull_progress * (
        3 - 2 * pull_progress
    )
    item_size = max(6, round(28 - pull_progress * 21))
    item_alpha = round(
        255
        * max(0.0, 1 - max(0.0, progress - 0.48) / 0.18)
    )
    item_y = effect_center - round(math.sin(progress * math.pi) * 6)
    item_sprite = pygame.transform.scale(
        sprites[sprite_names[kind]],
        (item_size, item_size),
    )
    item_sprite.set_alpha(item_alpha)

    orbit_radius = 18 * (1 - pull_progress) + 3
    orbit_alpha = round(180 * max(0.0, 1 - progress / 0.58))
    for particle_index in range(8):
        angle = particle_index * math.tau / 8 + progress * 3.2
        particle_position = (
            round(effect_center + math.cos(angle) * orbit_radius),
            round(item_y + math.sin(angle) * orbit_radius * 0.58),
        )
        pygame.draw.circle(
            effect,
            (*bright_color, orbit_alpha),
            particle_position,
            2 if particle_index % 3 == 0 else 1,
        )

    ring_progress = max(0.0, min(1.0, (progress - 0.3) / 0.42))
    if ring_progress > 0:
        ring_radius = round(4 + ring_progress * 22)
        ring_alpha = round(190 * (1 - ring_progress))
        pygame.draw.circle(
            effect,
            (*base_color, ring_alpha),
            (effect_center, effect_center),
            ring_radius,
            width=3,
        )
        pygame.draw.circle(
            effect,
            (*bright_color, round(ring_alpha * 0.75)),
            (effect_center, effect_center),
            max(2, ring_radius - 4),
            width=1,
        )
        for spark_index in range(6):
            angle = spark_index * math.tau / 6
            spark_start_distance = 5 + ring_progress * 10
            spark_end_distance = spark_start_distance + 5
            pygame.draw.line(
                effect,
                (*bright_color, ring_alpha),
                (
                    round(
                        effect_center
                        + math.cos(angle) * spark_start_distance
                    ),
                    round(
                        effect_center
                        + math.sin(angle) * spark_start_distance
                    ),
                ),
                (
                    round(
                        effect_center
                        + math.cos(angle) * spark_end_distance
                    ),
                    round(
                        effect_center
                        + math.sin(angle) * spark_end_distance
                    ),
                ),
                2,
            )

    item_position = item_sprite.get_rect(
        center=(effect_center, item_y)
    )
    effect.blit(item_sprite, item_position)
    screen.blit(
        effect,
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


def _act_two_floor_sprite_name(
    column,
    row,
    visual_seed,
    floor_number,
):
    total_weight = sum(
        weight for _, weight in FLOOR_TILE_VARIANT_WEIGHTS
    )
    if total_weight <= 0:
        return "floor"

    noise = _act_one_tile_noise(
        column,
        row,
        visual_seed,
        floor_number + 307,
    )
    selection = noise % total_weight
    for sprite_name, weight in FLOOR_TILE_VARIANT_WEIGHTS:
        if selection < weight:
            return sprite_name
        selection -= weight
    return "floor"


def _act_two_mix_noise(noise):
    noise ^= noise >> 16
    noise = (noise * 0x7FEB352D) & 0xFFFFFFFF
    noise ^= noise >> 15
    noise = (noise * 0x846CA68B) & 0xFFFFFFFF
    noise ^= noise >> 16
    return noise


def _act_two_floor_decor_candidate_sprite_name(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
    excluded_positions=(),
):
    if (
        dungeon_map[row][column] != "."
        or (column, row) in excluded_positions
    ):
        return None

    cluster_size = max(1, FLOOR_DECOR_CLUSTER_SIZE_TILES)
    cluster_noise = _act_two_mix_noise(
        _act_one_tile_noise(
            column // cluster_size,
            row // cluster_size,
            visual_seed,
            floor_number + 941,
        )
    )
    in_decor_cluster = (
        cluster_noise % 100 < FLOOR_DECOR_CLUSTER_PERCENT
    )
    placement_percent = (
        FLOOR_DECOR_DENSE_PERCENT
        if in_decor_cluster
        else FLOOR_DECOR_SPARSE_PERCENT
    )
    placement_noise = _act_two_mix_noise(
        _act_one_tile_noise(
            column,
            row,
            visual_seed,
            floor_number + 977,
        )
    )
    if placement_noise % 100 >= placement_percent:
        return None

    total_weight = sum(
        weight for _, weight in FLOOR_DECOR_VARIANT_WEIGHTS
    )
    if total_weight <= 0:
        return None
    selection = (placement_noise // 100) % total_weight
    for sprite_name, weight in FLOOR_DECOR_VARIANT_WEIGHTS:
        if selection < weight:
            return sprite_name
        selection -= weight
    return None


def _act_two_floor_decor_priority(
    column,
    row,
    visual_seed,
    floor_number,
):
    return _act_two_mix_noise(
        _act_one_tile_noise(
            column,
            row,
            visual_seed,
            floor_number + 1013,
        )
    )


def _act_two_floor_decor_sprite_name(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
    excluded_positions=(),
):
    selected_sprite = _act_two_floor_decor_candidate_sprite_name(
        dungeon_map,
        column,
        row,
        visual_seed,
        floor_number,
        excluded_positions,
    )
    if selected_sprite is None:
        return None

    radius = max(0, FLOOR_DECOR_MIN_SPACING_TILES - 1)
    current_rank = (
        _act_two_floor_decor_priority(
            column,
            row,
            visual_seed,
            floor_number,
        ),
        row,
        column,
    )
    for neighbor_row in range(
        max(0, row - radius),
        min(len(dungeon_map), row + radius + 1),
    ):
        for neighbor_column in range(
            max(0, column - radius),
            min(len(dungeon_map[neighbor_row]), column + radius + 1),
        ):
            if neighbor_column == column and neighbor_row == row:
                continue
            if _act_two_floor_decor_candidate_sprite_name(
                dungeon_map,
                neighbor_column,
                neighbor_row,
                visual_seed,
                floor_number,
                excluded_positions,
            ) is None:
                continue
            neighbor_rank = (
                _act_two_floor_decor_priority(
                    neighbor_column,
                    neighbor_row,
                    visual_seed,
                    floor_number,
                ),
                neighbor_row,
                neighbor_column,
            )
            if neighbor_rank < current_rank:
                return None
    return selected_sprite


def _act_two_wall_candidate_sprite_name(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
):
    total_weight = sum(
        weight for _, weight in WALL_TILE_VARIANT_WEIGHTS
    )
    if total_weight <= 0:
        return "wall"

    noise = _act_one_tile_noise(
        column,
        row,
        visual_seed,
        floor_number + 509,
    )
    # Avalanche the coordinate hash before applying small percentage buckets.
    # Straight corridor coordinates otherwise over-favor a few modulo values.
    noise = _act_two_mix_noise(noise)
    selection = noise % total_weight
    selected_sprite = "wall"
    for sprite_name, weight in WALL_TILE_VARIANT_WEIGHTS:
        if selection < weight:
            selected_sprite = sprite_name
            break
        selection -= weight

    if (
        selected_sprite in ACT_TWO_EXPOSED_WALL_SPRITES
        and not _act_one_wall_is_exposed(dungeon_map, column, row)
    ):
        return "wall"
    return selected_sprite


def _act_two_wall_variant_priority(
    column,
    row,
    visual_seed,
    floor_number,
):
    return _act_two_mix_noise(
        _act_one_tile_noise(
            column,
            row,
            visual_seed,
            floor_number + 829,
        )
    )


def _act_two_wall_variant_wins_spacing(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
    selected_sprite,
    radius,
    competing_sprites,
):
    current_rank = (
        _act_two_wall_variant_priority(
            column,
            row,
            visual_seed,
            floor_number,
        ),
        row,
        column,
    )
    for neighbor_row in range(
        max(0, row - radius),
        min(len(dungeon_map), row + radius + 1),
    ):
        for neighbor_column in range(
            max(0, column - radius),
            min(len(dungeon_map[neighbor_row]), column + radius + 1),
        ):
            if neighbor_column == column and neighbor_row == row:
                continue
            if dungeon_map[neighbor_row][neighbor_column] != "#":
                continue
            neighbor_sprite = _act_two_wall_candidate_sprite_name(
                dungeon_map,
                neighbor_column,
                neighbor_row,
                visual_seed,
                floor_number,
            )
            if neighbor_sprite not in competing_sprites:
                continue
            neighbor_rank = (
                _act_two_wall_variant_priority(
                    neighbor_column,
                    neighbor_row,
                    visual_seed,
                    floor_number,
                ),
                neighbor_row,
                neighbor_column,
            )
            if neighbor_rank < current_rank:
                return False
    return True


def _act_two_wall_sprite_name(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
):
    selected_sprite = _act_two_wall_candidate_sprite_name(
        dungeon_map,
        column,
        row,
        visual_seed,
        floor_number,
    )
    if selected_sprite in ACT_TWO_WEAR_WALL_SPRITES:
        if not _act_two_wall_variant_wins_spacing(
            dungeon_map,
            column,
            row,
            visual_seed,
            floor_number,
            selected_sprite,
            WALL_WEAR_REPEAT_MIN_SPACING_TILES - 1,
            {selected_sprite},
        ):
            return "wall"
    elif selected_sprite in ACT_TWO_SPACED_WALL_SPRITES:
        if not _act_two_wall_variant_wins_spacing(
            dungeon_map,
            column,
            row,
            visual_seed,
            floor_number,
            selected_sprite,
            WALL_DECOR_MIN_SPACING_TILES - 1,
            ACT_TWO_SPACED_WALL_SPRITES,
        ):
            return "wall"
    elif selected_sprite == "wall_torch":
        if not _act_two_wall_variant_wins_spacing(
            dungeon_map,
            column,
            row,
            visual_seed,
            floor_number,
            selected_sprite,
            WALL_TORCH_MIN_SPACING_TILES - 1,
            {"wall_torch"},
        ):
            return "wall"
    return selected_sprite


def _act_two_wall_overlay_candidate_sprite_name(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
):
    if (
        dungeon_map[row][column] != "#"
        or not _act_one_wall_is_exposed(dungeon_map, column, row)
    ):
        return None
    base_sprite = _act_two_wall_sprite_name(
        dungeon_map,
        column,
        row,
        visual_seed,
        floor_number,
    )
    if base_sprite not in ACT_TWO_WALL_OVERLAY_BASE_SPRITES:
        return None

    total_weight = sum(
        weight for _, weight in WALL_OVERLAY_VARIANT_WEIGHTS
    )
    if total_weight <= 0:
        return None
    noise = _act_two_mix_noise(
        _act_one_tile_noise(
            column,
            row,
            visual_seed,
            floor_number + 1097,
        )
    )
    selection = noise % total_weight
    for sprite_name, weight in WALL_OVERLAY_VARIANT_WEIGHTS:
        if selection < weight:
            return sprite_name
        selection -= weight
    return None


def _act_two_wall_overlay_priority(
    column,
    row,
    visual_seed,
    floor_number,
):
    return _act_two_mix_noise(
        _act_one_tile_noise(
            column,
            row,
            visual_seed,
            floor_number + 1129,
        )
    )


def _act_two_wall_overlay_wins_spacing(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
    radius,
    competing_sprites=None,
):
    current_rank = (
        _act_two_wall_overlay_priority(
            column,
            row,
            visual_seed,
            floor_number,
        ),
        row,
        column,
    )
    for neighbor_row in range(
        max(0, row - radius),
        min(len(dungeon_map), row + radius + 1),
    ):
        for neighbor_column in range(
            max(0, column - radius),
            min(len(dungeon_map[neighbor_row]), column + radius + 1),
        ):
            if neighbor_column == column and neighbor_row == row:
                continue
            if dungeon_map[neighbor_row][neighbor_column] != "#":
                continue
            neighbor_sprite = (
                _act_two_wall_overlay_candidate_sprite_name(
                    dungeon_map,
                    neighbor_column,
                    neighbor_row,
                    visual_seed,
                    floor_number,
                )
            )
            if neighbor_sprite is None:
                continue
            if (
                competing_sprites is not None
                and neighbor_sprite not in competing_sprites
            ):
                continue
            neighbor_rank = (
                _act_two_wall_overlay_priority(
                    neighbor_column,
                    neighbor_row,
                    visual_seed,
                    floor_number,
                ),
                neighbor_row,
                neighbor_column,
            )
            if neighbor_rank < current_rank:
                return False
    return True


def _act_two_wall_overlay_sprite_name(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
):
    selected_sprite = _act_two_wall_overlay_candidate_sprite_name(
        dungeon_map,
        column,
        row,
        visual_seed,
        floor_number,
    )
    if selected_sprite is None:
        return None

    if not _act_two_wall_overlay_wins_spacing(
        dungeon_map,
        column,
        row,
        visual_seed,
        floor_number,
        max(0, WALL_OVERLAY_MIN_SPACING_TILES - 1),
    ):
        return None
    return selected_sprite


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


def _act_two_open_neighbor(dungeon_map, column, row, dc, dr):
    neighbor_column = column + dc
    neighbor_row = row + dr
    return (
        0 <= neighbor_row < len(dungeon_map)
        and 0 <= neighbor_column < len(dungeon_map[neighbor_row])
        and dungeon_map[neighbor_row][neighbor_column] != "#"
    )


def _draw_act_two_floor_detail(screen, x, y, noise, floor_number):
    if noise % 11 == 0:
        stain = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.ellipse(
            stain,
            (*ACT_TWO_DAMP, 34 + floor_number * 5),
            (4 + noise % 7, 16 + noise % 5, 19, 8),
        )
        pygame.draw.ellipse(
            stain,
            (47, 69, 66, 22),
            (8 + noise % 4, 18 + noise % 3, 11, 3),
        )
        screen.blit(stain, (x, y))

    if noise % max(7, 12 - floor_number) == 2:
        _draw_act_one_crack(
            screen,
            x,
            y,
            noise // 7,
        )

    if noise % 41 == 9:
        pygame.draw.circle(
            screen,
            (42, 49, 48),
            (x + 7 + noise % 17, y + 7 + (noise // 17) % 17),
            1,
        )
        pygame.draw.circle(
            screen,
            (29, 42, 42),
            (x + 11 + noise % 13, y + 12 + (noise // 13) % 13),
            1,
        )


def _draw_act_two_wall_detail(
    screen,
    dungeon_map,
    column,
    row,
    x,
    y,
    noise,
    allow_decor=True,
):
    if _act_two_open_neighbor(dungeon_map, column, row, 0, 1):
        pygame.draw.line(
            screen,
            ACT_TWO_MORTAR_DARK,
            (x + 1, y + TILE_SIZE - 2),
            (x + TILE_SIZE - 2, y + TILE_SIZE - 2),
            3,
        )
        pygame.draw.line(
            screen,
            ACT_TWO_MORTAR_LIGHT,
            (x + 2, y + TILE_SIZE - 5),
            (x + TILE_SIZE - 3, y + TILE_SIZE - 5),
        )
    if _act_two_open_neighbor(dungeon_map, column, row, 1, 0):
        pygame.draw.line(
            screen,
            ACT_TWO_MORTAR_DARK,
            (x + TILE_SIZE - 2, y + 2),
            (x + TILE_SIZE - 2, y + TILE_SIZE - 2),
            2,
        )
    if _act_two_open_neighbor(dungeon_map, column, row, -1, 0):
        pygame.draw.line(
            screen,
            ACT_TWO_MORTAR_LIGHT,
            (x + 2, y + 3),
            (x + 2, y + TILE_SIZE - 3),
        )

    if not allow_decor:
        return

    if noise % 37 == 4:
        rune = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pulse_color = (*ACT_TWO_RUNE, 112)
        center_x = 10 + noise % 12
        pygame.draw.line(rune, pulse_color, (center_x, 8), (center_x, 23), 1)
        pygame.draw.lines(
            rune,
            pulse_color,
            False,
            ((center_x - 5, 12), (center_x, 17), (center_x + 5, 11)),
            1,
        )
        screen.blit(rune, (x, y))
    elif noise % 17 == 3:
        _draw_act_one_crack(screen, x, y, noise // 17, wall=True)


def _draw_act_two_motes(
    screen,
    dungeon_map,
    floor_number,
    visual_seed,
    current_time,
):
    if not dungeon_map:
        return
    column_count = len(dungeon_map[0])
    row_count = len(dungeon_map)
    map_width = column_count * TILE_SIZE
    map_height = row_count * TILE_SIZE
    motes = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
    area_scale = (column_count * row_count) / (25 * 15)
    mote_count = round((24 + floor_number * 7) * area_scale)
    for mote_index in range(mote_count):
        noise = _act_one_tile_noise(
            mote_index,
            floor_number,
            visual_seed,
            211,
        )
        column = noise % column_count
        row = (noise // column_count) % row_count
        if dungeon_map[row][column] == "#":
            continue
        cycle = ((current_time / 13) + noise % 1201) % 1201 / 1201
        mote_x = (
            column * TILE_SIZE
            + 4
            + (noise // 19) % (TILE_SIZE - 8)
            + round(math.sin(current_time / 1150 + mote_index) * 4)
        )
        mote_y = (
            row * TILE_SIZE
            + TILE_SIZE
            - round(cycle * (TILE_SIZE + 12))
        )
        alpha = round(34 * math.sin(math.pi * cycle))
        color = (
            (91, 139, 144, alpha)
            if mote_index % 4
            else (152, 137, 119, alpha)
        )
        pygame.draw.circle(motes, color, (mote_x, mote_y), 1)
    screen.blit(motes, (MAP_OFFSET_X, MAP_OFFSET_Y))


def _draw_act_two_rune_glows(
    screen,
    dungeon_map,
    floor_number,
    visual_seed,
    current_time,
):
    if not dungeon_map:
        return
    pulse = (math.sin(current_time / 480) + 1) / 2
    for row, tiles in enumerate(dungeon_map):
        for column, tile in enumerate(tiles):
            if tile != "#" or not _act_one_wall_is_exposed(
                dungeon_map,
                column,
                row,
            ):
                continue
            noise = _act_one_tile_noise(
                column,
                row,
                visual_seed,
                floor_number + 101,
            )
            if noise % 37 != 4:
                continue
            center = (
                MAP_OFFSET_X + column * TILE_SIZE + 10 + noise % 12,
                MAP_OFFSET_Y + row * TILE_SIZE + 16,
            )
            _draw_act_one_glow(
                screen,
                center,
                (49, 119, 126),
                round(21 + pulse * 5),
            )
            pygame.draw.circle(
                screen,
                (93, 153, 155),
                center,
                1,
            )


def _draw_act_two_torch_lights(
    screen,
    dungeon_map,
    floor_number,
    visual_seed,
    current_time,
):
    if not dungeon_map:
        return

    for row, tiles in enumerate(dungeon_map):
        for column, tile in enumerate(tiles):
            if tile != "#":
                continue
            if _act_two_wall_sprite_name(
                dungeon_map,
                column,
                row,
                visual_seed,
                floor_number,
            ) != "wall_torch":
                continue

            noise = _act_one_tile_noise(
                column,
                row,
                visual_seed,
                floor_number + 613,
            )
            flicker = (
                math.sin(current_time / 92 + noise % 17)
                + math.sin(current_time / 157 + noise % 29) * 0.45
            )
            center = (
                MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2,
                MAP_OFFSET_Y + row * TILE_SIZE + 12,
            )
            _draw_act_one_glow(
                screen,
                center,
                (196, 82, 24),
                round(50 + flicker * 3),
            )
            _draw_act_one_glow(
                screen,
                center,
                (244, 151, 47),
                round(27 + flicker * 2),
            )
            pygame.draw.circle(
                screen,
                (255, 201, 91),
                center,
                1,
            )


def _draw_act_two_brazier_lights(
    screen,
    dungeon_map,
    floor_number,
    visual_seed,
    current_time,
):
    if not dungeon_map:
        return

    for row, tiles in enumerate(dungeon_map):
        for column, tile in enumerate(tiles):
            if tile != "B":
                continue

            noise = _act_one_tile_noise(
                column,
                row,
                visual_seed,
                floor_number + 1181,
            )
            flicker = (
                math.sin(current_time / 106 + noise % 19)
                + math.sin(current_time / 181 + noise % 31) * 0.4
            )
            center = (
                MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2,
                MAP_OFFSET_Y + row * TILE_SIZE + 12,
            )
            _draw_act_one_glow(
                screen,
                center,
                (175, 61, 19),
                round(62 + flicker * 4),
            )
            _draw_act_one_glow(
                screen,
                center,
                (242, 131, 37),
                round(34 + flicker * 2),
            )
            pygame.draw.circle(screen, (255, 215, 109), center, 2)


def draw_act_two_atmosphere(
    screen,
    act_number,
    player_column,
    player_row,
    dungeon_map=None,
    floor_number=1,
    visual_seed=0,
    current_time=0,
):
    if act_number != 2:
        return

    map_width = len(dungeon_map[0]) * TILE_SIZE
    map_height = len(dungeon_map) * TILE_SIZE

    player_center = (
        player_column * TILE_SIZE + TILE_SIZE // 2,
        player_row * TILE_SIZE + TILE_SIZE // 2,
    )
    darkness = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
    darkness.fill((3, 6, 11, 76 + (floor_number - 1) * 10))
    for radius, alpha in ((146, 54), (112, 38), (78, 21), (46, 8)):
        pygame.draw.circle(
            darkness,
            (8, 13, 18, alpha),
            player_center,
            radius,
        )
    screen.blit(darkness, (MAP_OFFSET_X, MAP_OFFSET_Y))

    _draw_act_two_torch_lights(
        screen,
        dungeon_map,
        floor_number,
        visual_seed,
        current_time,
    )
    _draw_act_two_brazier_lights(
        screen,
        dungeon_map,
        floor_number,
        visual_seed,
        current_time,
    )

    _draw_act_two_rune_glows(
        screen,
        dungeon_map,
        floor_number,
        visual_seed,
        current_time,
    )

    world_player_center = (
        MAP_OFFSET_X + player_center[0],
        MAP_OFFSET_Y + player_center[1],
    )
    _draw_act_one_glow(screen, world_player_center, (55, 102, 111), 62)

    fog = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
    for band_index in range(5):
        noise = _act_one_tile_noise(
            band_index,
            floor_number,
            visual_seed,
            307,
        )
        drift = round(
            math.sin(current_time / 2200 + band_index * 1.7) * 34
        )
        fog_y = 52 + (noise % max(1, map_height - 104))
        fog_x = -90 + (noise % 130) + drift
        pygame.draw.ellipse(
            fog,
            (53, 69, 72, 8 + floor_number * 2),
            (fog_x, fog_y, 360 + noise % 150, 34 + noise % 24),
        )
        pygame.draw.ellipse(
            fog,
            (73, 78, 80, 5 + floor_number),
            (fog_x + 230, fog_y + 11, 390, 28),
        )
    screen.blit(fog, (MAP_OFFSET_X, MAP_OFFSET_Y))

    _draw_act_two_motes(
        screen,
        dungeon_map,
        floor_number,
        visual_seed,
        current_time,
    )


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
    for row_index, row in enumerate(dungeon_map):
        for column_index, tile in enumerate(row):
            x = MAP_OFFSET_X + column_index * TILE_SIZE
            y = MAP_OFFSET_Y + row_index * TILE_SIZE
            tile_rectangle = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            if act_number >= 2:
                is_wall = tile in ("#", "S")
                if is_wall:
                    if act_number == 2:
                        texture_name = (
                            "wall_secret"
                            if tile == "S"
                            else _act_two_wall_sprite_name(
                                dungeon_map,
                                column_index,
                                row_index,
                                visual_seed,
                                floor_number,
                            )
                        )
                    else:
                        texture_name = "wall"
                elif act_number == 2:
                    texture_name = (
                        "floor"
                        if tile in ("r", "R", "G", "H", "P", "T")
                        else _act_two_floor_sprite_name(
                            column_index,
                            row_index,
                            visual_seed,
                            floor_number,
                        )
                    )
                else:
                    texture_name = "floor"
                screen.blit(sprites[texture_name], tile_rectangle)

                if act_number == 2:
                    detail_noise = _act_one_tile_noise(
                        column_index,
                        row_index,
                        visual_seed,
                        floor_number + 101,
                    )
                    if is_wall:
                        _draw_act_two_wall_detail(
                            screen,
                            dungeon_map,
                            column_index,
                            row_index,
                            x,
                            y,
                            detail_noise,
                            allow_decor=(
                                tile == "#" and texture_name == "wall"
                            ),
                        )
                        wall_overlay_name = (
                            _act_two_wall_overlay_sprite_name(
                                dungeon_map,
                                column_index,
                                row_index,
                                visual_seed,
                                floor_number,
                            )
                            if tile == "#"
                            else None
                        )
                        if wall_overlay_name is not None:
                            wall_overlay = sprites[wall_overlay_name]
                            if (
                                wall_overlay_name == "decor_wall_cobweb"
                                and detail_noise & 1
                            ):
                                wall_overlay = pygame.transform.flip(
                                    wall_overlay,
                                    True,
                                    False,
                                )
                            screen.blit(wall_overlay, tile_rectangle)
                    else:
                        if (
                            tile not in ("r", "R", "G", "H", "P", "T")
                            and texture_name not in {
                                "floor_fissure",
                                "floor_fissure_cross",
                                "floor_puddle",
                                "floor_rubble_heavy",
                                "floor_drain",
                                "floor_burial_seal",
                            }
                        ):
                            _draw_act_two_floor_detail(
                                screen,
                                x,
                                y,
                                detail_noise,
                                floor_number,
                            )
                        if tile == ".":
                            floor_decor_name = (
                                _act_two_floor_decor_sprite_name(
                                    dungeon_map,
                                    column_index,
                                    row_index,
                                    visual_seed,
                                    floor_number,
                                    floor_decor_excluded_positions,
                                )
                            )
                            if floor_decor_name is not None:
                                screen.blit(
                                    sprites[floor_decor_name],
                                    tile_rectangle,
                                )

                if tile == "C":
                    screen.blit(
                        sprites["pillar"],
                        tile_rectangle,
                    )
                elif act_number == 2 and tile == "B":
                    screen.blit(
                        sprites["decor_floor_boss_brazier"],
                        tile_rectangle,
                    )
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
            grid_color = (
                ACT_ONE_GRID_COLOR
                if act_number < 2
                else ACT_TWO_GRID_COLOR
                if act_number == 2
                else GRID_COLOR
            )
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
        outer_rectangle = pygame.Rect(
            ACT_TWO_VIEW_X - 4,
            ACT_TWO_VIEW_Y - 4,
            ACT_TWO_VIEW_WIDTH + 8,
            ACT_TWO_VIEW_HEIGHT + 8,
        )
        pygame.draw.rect(
            screen,
            (8, 10, 14),
            outer_rectangle.inflate(6, 6),
            width=5,
        )
        pygame.draw.rect(screen, (58, 76, 79), outer_rectangle, width=3)
        pygame.draw.rect(
            screen,
            (30, 27, 34),
            outer_rectangle.inflate(-6, -6),
            width=1,
        )
        pygame.draw.line(
            screen,
            (99, 112, 108),
            outer_rectangle.topleft,
            outer_rectangle.topright,
        )
        for corner in (
            outer_rectangle.topleft,
            outer_rectangle.topright,
            outer_rectangle.bottomleft,
            outer_rectangle.bottomright,
        ):
            pygame.draw.circle(screen, (13, 17, 21), corner, 5)
            pygame.draw.circle(screen, (75, 92, 92), corner, 2)
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


def _draw_act_two_attack_tile(
    screen,
    column,
    row,
    current_time,
):
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


def _draw_act_two_attack_foreground(
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


def _draw_act_two_archer_telegraph(
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


def draw_attack_markers(
    screen,
    enemies,
    act_number=2,
    current_time=0,
    visible_cells=None,
    player_position=None,
    foreground=False,
):
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
        if act_number == 2 and visible_cells is not None:
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
            act_number == 2
            and not foreground
            and enemy["type"] == "archer"
            and enemy.get("prepared_attack_mode") == "ranged"
        ):
            direct_target = (
                player_position
                if player_position in attack_targets
                else attack_targets[0]
            )
            _draw_act_two_archer_telegraph(
                screen,
                enemy,
                direct_target,
                enemy_is_visible,
                current_time,
            )

        target_rows = {row for _, row in attack_targets}
        sweep_is_horizontal = len(target_rows) == 1

        for column, row in attack_targets:
            if act_number == 2:
                if foreground:
                    _draw_act_two_attack_foreground(
                        screen,
                        column,
                        row,
                        current_time,
                        (column, row) == player_position,
                    )
                else:
                    _draw_act_two_attack_tile(
                        screen,
                        column,
                        row,
                        current_time,
                    )
                continue

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


def draw_oracle_projectiles(
    screen,
    projectiles,
    sprites,
):
    for projectile in projectiles:
        sprite_name = (
            "oracle_projectile_homing"
            if projectile["kind"] == "homing"
            else "oracle_projectile"
        )
        projectile_left = (
            MAP_OFFSET_X + projectile["column"] * TILE_SIZE
        )
        projectile_top = (
            MAP_OFFSET_Y + projectile["row"] * TILE_SIZE
        )
        screen.blit(
            sprites[sprite_name],
            (projectile_left, projectile_top),
        )


def draw_oracle_emitters(
    screen,
    emitters,
    is_active,
    sprites,
):
    if not is_active:
        return

    for column, row in emitters:
        left = MAP_OFFSET_X + column * TILE_SIZE
        top = MAP_OFFSET_Y + row * TILE_SIZE
        screen.blit(
            sprites["charged_pillar"],
            (left, top),
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


def _act_two_hit_offset(enemy, elapsed):
    if elapsed >= ACT_TWO_HIT_REACTION_MS:
        return (0, 0)
    origin = enemy.get("hit_origin")
    direction_x = 0
    direction_y = -1
    if origin is not None:
        direction_x = enemy["column"] - origin[0]
        direction_y = enemy["row"] - origin[1]
        direction_length = max(1, math.hypot(direction_x, direction_y))
        direction_x /= direction_length
        direction_y /= direction_length
    progress = elapsed / ACT_TWO_HIT_REACTION_MS
    recoil = math.sin(math.pi * progress)
    distance = 8 if enemy.get("hit_critical", False) else 5
    return (
        round(direction_x * distance * recoil),
        round(direction_y * distance * recoil),
    )


def _draw_act_two_damage_number(
    screen,
    enemy,
    current_time,
    damage_font,
):
    started_at = enemy.get("hit_animation_started_at", -1)
    elapsed = current_time - started_at
    if (
        damage_font is None
        or started_at < 0
        or enemy.get("hit_blocked", False)
        or not 0 <= elapsed < ACT_TWO_HIT_FEEDBACK_MS
    ):
        return
    progress = elapsed / ACT_TWO_HIT_FEEDBACK_MS
    alpha = round(255 * min(1, (1 - progress) * 2.4))
    critical = enemy.get("hit_critical", False)
    text = (
        f"{enemy.get('hit_damage', 0)}!"
        if critical
        else str(enemy.get("hit_damage", 0))
    )
    color = (
        (255, 213, 91)
        if critical
        else (241, 233, 218)
    )
    number = damage_font.render(text, True, color)
    number.set_alpha(alpha)
    shadow = damage_font.render(text, True, (13, 8, 11))
    shadow.set_alpha(alpha)
    center_x = (
        MAP_OFFSET_X
        + enemy["column"] * TILE_SIZE
        + TILE_SIZE // 2
    )
    top = (
        MAP_OFFSET_Y
        + enemy["row"] * TILE_SIZE
        - 7
        - round(progress * 14)
    )
    rectangle = number.get_rect(midbottom=(center_x, top))
    screen.blit(shadow, rectangle.move(1, 2))
    screen.blit(number, rectangle)


def _draw_act_two_enemy_death(
    screen,
    enemy,
    standing_sprite,
    corpse_sprite,
    current_time,
    damage_font,
):
    started_at = enemy.get("death_animation_started_at", -1)
    elapsed = (
        max(0, current_time - started_at)
        if started_at >= 0
        else ACT_TWO_DEATH_SETTLE_MS
    )
    tile_position = (
        MAP_OFFSET_X + enemy["column"] * TILE_SIZE,
        MAP_OFFSET_Y + enemy["row"] * TILE_SIZE,
    )
    center = (
        tile_position[0] + TILE_SIZE // 2,
        tile_position[1] + TILE_SIZE // 2,
    )

    if elapsed < ACT_TWO_DEATH_IMPACT_MS:
        progress = elapsed / ACT_TWO_DEATH_IMPACT_MS
        recoil_x, recoil_y = _act_two_hit_offset(enemy, elapsed)
        body_height = max(
            22,
            round(TILE_SIZE * (1 - progress * 0.18)),
        )
        body = pygame.transform.scale(
            standing_sprite,
            (TILE_SIZE, body_height),
        )
        body_position = body.get_rect(
            midbottom=(
                center[0] + recoil_x,
                tile_position[1] + TILE_SIZE - 2 + recoil_y,
            )
        )
        screen.blit(body, body_position)
        flash = body.copy()
        flash.fill(
            (235, 224, 207, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        flash.set_alpha(round(205 * (1 - progress)))
        screen.blit(flash, body_position)
    else:
        settle_progress = min(
            1,
            (elapsed - ACT_TWO_DEATH_IMPACT_MS)
            / (ACT_TWO_DEATH_SETTLE_MS - ACT_TWO_DEATH_IMPACT_MS),
        )
        lift = round((1 - settle_progress) * 5)
        shadow = pygame.Surface((28, 7), pygame.SRCALPHA)
        pygame.draw.ellipse(
            shadow,
            (5, 6, 8, round(105 + settle_progress * 45)),
            shadow.get_rect(),
        )
        screen.blit(
            shadow,
            (
                center[0] - 14,
                tile_position[1] + TILE_SIZE - 8,
            ),
        )
        screen.blit(
            corpse_sprite,
            (tile_position[0], tile_position[1] - lift),
        )

    if elapsed < ACT_TWO_DEATH_BURST_MS:
        burst_progress = elapsed / ACT_TWO_DEATH_BURST_MS
        visibility = 1 - burst_progress
        effect_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
            enemy.get("hit_attacker_class"),
            (157, 74, 61),
        )
        burst = pygame.Surface(
            (TILE_SIZE * 2, TILE_SIZE * 2),
            pygame.SRCALPHA,
        )
        burst_center = TILE_SIZE
        pygame.draw.circle(
            burst,
            (*effect_color, round(135 * visibility)),
            (burst_center, burst_center + 5),
            round(5 + burst_progress * 14),
            width=2,
        )
        for particle_index in range(6):
            angle = (
                particle_index * math.tau / 6
                + enemy["column"] * 0.31
                + enemy["row"] * 0.19
            )
            distance = 5 + burst_progress * 17
            particle_position = (
                round(burst_center + math.cos(angle) * distance),
                round(burst_center + 5 + math.sin(angle) * distance * 0.5),
            )
            pygame.draw.circle(
                burst,
                (*effect_color, round(210 * visibility)),
                particle_position,
                2 if particle_index % 2 == 0 else 1,
            )
        screen.blit(
            burst,
            (center[0] - burst_center, center[1] - burst_center),
        )

    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )


def _draw_act_two_goblin_hit_feedback(
    screen,
    enemy,
    sprite,
    position,
    current_time,
    damage_font,
):
    started_at = enemy.get("hit_animation_started_at", -1)
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < ACT_TWO_HIT_FEEDBACK_MS:
        screen.blit(sprite, position)
        return

    reaction_progress = min(1, elapsed / ACT_TWO_HIT_REACTION_MS)
    reaction = math.sin(math.pi * reaction_progress)
    offset_x, offset_y = _act_two_hit_offset(enemy, elapsed)
    center = (
        position[0] + TILE_SIZE // 2 + offset_x,
        position[1] + TILE_SIZE // 2 + offset_y,
    )
    pygame.draw.ellipse(
        screen,
        (5, 6, 9),
        (center[0] - 10, position[1] + TILE_SIZE - 7, 20, 6),
    )

    sprite_width = round(TILE_SIZE * (1 + reaction * 0.13))
    sprite_height = round(TILE_SIZE * (1 - reaction * 0.16))
    reacted_sprite = pygame.transform.scale(
        sprite,
        (sprite_width, max(20, sprite_height)),
    )
    sprite_position = reacted_sprite.get_rect(center=center)
    screen.blit(reacted_sprite, sprite_position)

    if elapsed < ACT_TWO_HIT_REACTION_MS:
        flash = reacted_sprite.copy()
        flash.fill(
            (230, 218, 198, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        flash.set_alpha(round(215 * (1 - reaction_progress)))
        screen.blit(flash, sprite_position)

        effect_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
            enemy.get("hit_attacker_class"),
            (190, 84, 67),
        )
        particle_count = 9 if enemy.get("hit_critical", False) else 6
        particle_layer = pygame.Surface(
            (TILE_SIZE * 2, TILE_SIZE * 2),
            pygame.SRCALPHA,
        )
        particle_center = TILE_SIZE
        visibility = 1 - reaction_progress
        for particle_index in range(particle_count):
            angle = (
                particle_index * math.tau / particle_count
                + enemy["column"] * 0.47
                + enemy["row"] * 0.31
            )
            distance = 5 + reaction_progress * 18
            particle_position = (
                round(particle_center + math.cos(angle) * distance),
                round(particle_center + math.sin(angle) * distance),
            )
            pygame.draw.circle(
                particle_layer,
                (*effect_color, round(230 * visibility)),
                particle_position,
                2 if particle_index % 3 == 0 else 1,
            )
        screen.blit(
            particle_layer,
            (
                center[0] - particle_center,
                center[1] - particle_center,
            ),
        )

    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )


def _draw_act_two_goblin_death(
    screen,
    enemy,
    sprite,
    current_time,
    damage_font,
):
    started_at = enemy.get("death_animation_started_at", -1)
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < ACT_TWO_GOBLIN_DEATH_MS:
        return
    progress = elapsed / ACT_TWO_GOBLIN_DEATH_MS
    center = (
        MAP_OFFSET_X
        + enemy["column"] * TILE_SIZE
        + TILE_SIZE // 2,
        MAP_OFFSET_Y
        + enemy["row"] * TILE_SIZE
        + TILE_SIZE // 2,
    )
    effect_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
        enemy.get("hit_attacker_class"),
        (155, 65, 58),
    )

    stain_alpha = round(75 * min(1, progress * 2.3) * (1 - progress))
    stain = pygame.Surface((38, 16), pygame.SRCALPHA)
    pygame.draw.ellipse(
        stain,
        (61, 17, 21, stain_alpha),
        stain.get_rect(),
    )
    screen.blit(stain, (center[0] - 19, center[1] + 8))

    body_end = 0.64
    if progress < body_end:
        body_progress = progress / body_end
        recoil_x, recoil_y = _act_two_hit_offset(enemy, elapsed)
        body = sprite.copy()
        if elapsed < 115:
            flash = body.copy()
            flash.fill(
                (235, 220, 202, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            flash.set_alpha(round(220 * (1 - elapsed / 115)))
            body.blit(flash, (0, 0))
        else:
            darkness = max(48, round(190 * (1 - body_progress)))
            body.fill(
                (darkness, darkness, darkness, 255),
                special_flags=pygame.BLEND_RGBA_MULT,
            )
        body = pygame.transform.rotozoom(
            body,
            -18 * body_progress,
            1,
        )
        collapsed_height = max(
            5,
            round(body.get_height() * (1 - body_progress * 0.72)),
        )
        body = pygame.transform.smoothscale(
            body,
            (body.get_width(), collapsed_height),
        )
        body.set_alpha(round(255 * (1 - body_progress ** 1.8)))
        body_rectangle = body.get_rect(
            midbottom=(
                center[0] + recoil_x,
                center[1] + 15 + recoil_y,
            )
        )
        screen.blit(body, body_rectangle)

    particle_layer = pygame.Surface((72, 72), pygame.SRCALPHA)
    particle_center = 36
    for particle_index in range(15):
        delay = (particle_index % 5) * 24
        particle_elapsed = elapsed - delay
        if particle_elapsed < 0:
            continue
        particle_progress = min(
            1,
            particle_elapsed / max(1, ACT_TWO_GOBLIN_DEATH_MS - delay),
        )
        angle = math.radians(
            (enemy["column"] * 29 + enemy["row"] * 43 + particle_index * 137)
            % 360
        )
        distance = (8 + particle_index % 5 * 3) * particle_progress
        particle_position = (
            round(particle_center + math.cos(angle) * distance),
            round(
                particle_center
                + math.sin(angle) * distance * 0.65
                - 12 * particle_progress
                + 17 * particle_progress * particle_progress
            ),
        )
        alpha = round(225 * (1 - particle_progress) ** 1.5)
        particle_color = (
            (*effect_color, alpha)
            if particle_index % 3 == 0
            else (74, 55, 54, alpha)
        )
        pygame.draw.circle(
            particle_layer,
            particle_color,
            particle_position,
            2 if particle_index % 4 == 0 else 1,
        )
    screen.blit(
        particle_layer,
        (center[0] - particle_center, center[1] - particle_center),
    )

    signature_visibility = max(0, 1 - progress / 0.72)
    signature = pygame.Surface((64, 64), pygame.SRCALPHA)
    signature_center = 32
    attacker_class = enemy.get("hit_attacker_class")
    if attacker_class == "warrior":
        for spark_index in range(5):
            angle = math.radians(-70 + spark_index * 35)
            inner = 5 + progress * 6
            outer = 13 + progress * 20
            pygame.draw.line(
                signature,
                (235, 91, 53, round(205 * signature_visibility)),
                (
                    round(signature_center + math.cos(angle) * inner),
                    round(signature_center + math.sin(angle) * inner),
                ),
                (
                    round(signature_center + math.cos(angle) * outer),
                    round(signature_center + math.sin(angle) * outer),
                ),
                2,
            )
    elif attacker_class == "rogue":
        slash_extent = round(10 + progress * 15)
        for slope in (-1, 1):
            pygame.draw.line(
                signature,
                (199, 105, 230, round(190 * signature_visibility)),
                (
                    signature_center - slash_extent,
                    signature_center - slash_extent * slope,
                ),
                (
                    signature_center + slash_extent,
                    signature_center + slash_extent * slope,
                ),
                2,
            )
    elif attacker_class == "mage":
        rune_radius = max(3, round(20 * (1 - progress / 0.72)))
        pygame.draw.circle(
            signature,
            (72, 166, 230, round(205 * signature_visibility)),
            (signature_center, signature_center),
            rune_radius,
            width=2,
        )
        pygame.draw.polygon(
            signature,
            (154, 219, 249, round(180 * signature_visibility)),
            (
                (signature_center, signature_center - rune_radius),
                (signature_center + rune_radius, signature_center),
                (signature_center, signature_center + rune_radius),
                (signature_center - rune_radius, signature_center),
            ),
            width=1,
        )
    screen.blit(
        signature,
        (center[0] - signature_center, center[1] - signature_center),
    )

    if enemy.get("hit_critical", False) and progress < 0.45:
        critical_visibility = 1 - progress / 0.45
        pygame.draw.circle(
            screen,
            (255, 204, 83, round(210 * critical_visibility)),
            center,
            round(7 + progress * 25),
            width=2,
        )
    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )


def _draw_act_two_archer_hit_feedback(
    screen,
    enemy,
    sprite,
    position,
    current_time,
    damage_font,
):
    started_at = enemy.get("hit_animation_started_at", -1)
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < ACT_TWO_HIT_FEEDBACK_MS:
        screen.blit(sprite, position)
        return

    reaction_progress = min(1, elapsed / ACT_TWO_HIT_REACTION_MS)
    reaction = math.sin(math.pi * reaction_progress)
    offset_x, offset_y = _act_two_hit_offset(enemy, elapsed)
    offset_x = round(offset_x * 1.45)
    offset_y = round(offset_y * 1.45)
    center = (
        position[0] + TILE_SIZE // 2 + offset_x,
        position[1] + TILE_SIZE // 2 + offset_y,
    )
    origin = enemy.get("hit_origin")
    rotation_direction = 1
    if origin is not None and origin[0] > enemy["column"]:
        rotation_direction = -1
    angle = rotation_direction * reaction * (
        17 if enemy.get("hit_critical", False) else 11
    )
    reacted_sprite = pygame.transform.rotozoom(sprite, angle, 1)
    sprite_position = reacted_sprite.get_rect(center=center)
    pygame.draw.ellipse(
        screen,
        (5, 6, 9),
        (center[0] - 10, position[1] + TILE_SIZE - 7, 20, 6),
    )
    screen.blit(reacted_sprite, sprite_position)

    if elapsed < ACT_TWO_HIT_REACTION_MS:
        flash = reacted_sprite.copy()
        flash.fill(
            (229, 220, 196, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        flash.set_alpha(round(210 * (1 - reaction_progress)))
        screen.blit(flash, sprite_position)

        effect_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
            enemy.get("hit_attacker_class"),
            (176, 118, 58),
        )
        debris = pygame.Surface((64, 64), pygame.SRCALPHA)
        debris_center = 32
        visibility = 1 - reaction_progress
        debris_count = 8 if enemy.get("hit_critical", False) else 5
        for debris_index in range(debris_count):
            angle_radians = (
                debris_index * math.tau / debris_count
                + enemy["row"] * 0.37
            )
            distance = 5 + reaction_progress * 20
            debris_start = (
                round(debris_center + math.cos(angle_radians) * distance),
                round(debris_center + math.sin(angle_radians) * distance),
            )
            debris_end = (
                round(debris_start[0] + math.cos(angle_radians) * 5),
                round(debris_start[1] + math.sin(angle_radians) * 5),
            )
            color = (
                (*effect_color, round(225 * visibility))
                if debris_index % 2 == 0
                else (171, 126, 67, round(210 * visibility))
            )
            pygame.draw.line(
                debris,
                color,
                debris_start,
                debris_end,
                2 if debris_index % 3 == 0 else 1,
            )
        screen.blit(
            debris,
            (center[0] - debris_center, center[1] - debris_center),
        )

    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )


def _draw_act_two_archer_death(
    screen,
    enemy,
    sprite,
    current_time,
    damage_font,
):
    started_at = enemy.get("death_animation_started_at", -1)
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < ACT_TWO_ARCHER_DEATH_MS:
        return
    progress = elapsed / ACT_TWO_ARCHER_DEATH_MS
    fall_progress = min(1, progress / 0.68)
    fall_progress = fall_progress * fall_progress * (3 - 2 * fall_progress)
    center = (
        MAP_OFFSET_X
        + enemy["column"] * TILE_SIZE
        + TILE_SIZE // 2,
        MAP_OFFSET_Y
        + enemy["row"] * TILE_SIZE
        + TILE_SIZE // 2,
    )
    origin = enemy.get("hit_origin")
    fall_direction = 1
    if origin is not None and origin[0] > enemy["column"]:
        fall_direction = -1
    effect_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
        enemy.get("hit_attacker_class"),
        (157, 105, 55),
    )

    shadow = pygame.Surface((38, 14), pygame.SRCALPHA)
    pygame.draw.ellipse(
        shadow,
        (5, 7, 9, round(105 * (1 - progress * 0.65))),
        shadow.get_rect(),
    )
    screen.blit(shadow, (center[0] - 19, center[1] + 8))

    if progress < 0.78:
        body = sprite.copy()
        if elapsed < 100:
            flash = body.copy()
            flash.fill(
                (236, 222, 196, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            flash.set_alpha(round(215 * (1 - elapsed / 100)))
            body.blit(flash, (0, 0))
        else:
            shade = max(55, round(205 * (1 - progress * 0.8)))
            body.fill(
                (shade, shade, shade, 255),
                special_flags=pygame.BLEND_RGBA_MULT,
            )
        body = pygame.transform.rotozoom(
            body,
            fall_direction * 72 * fall_progress,
            1 - fall_progress * 0.08,
        )
        body.set_alpha(round(255 * min(1, (0.78 - progress) * 4.5)))
        body_rectangle = body.get_rect(
            center=(
                center[0] + round(fall_direction * fall_progress * 10),
                center[1] + round(fall_progress * 9),
            )
        )
        screen.blit(body, body_rectangle)

    debris = pygame.Surface((72, 72), pygame.SRCALPHA)
    debris_center = 36
    for debris_index in range(12):
        delay = (debris_index % 4) * 30
        debris_elapsed = elapsed - delay
        if debris_elapsed < 0:
            continue
        debris_progress = min(
            1,
            debris_elapsed / max(1, ACT_TWO_ARCHER_DEATH_MS - delay),
        )
        angle = math.radians(
            (enemy["column"] * 41 + enemy["row"] * 23 + debris_index * 83)
            % 360
        )
        distance = (8 + debris_index % 4 * 4) * debris_progress
        start = (
            round(debris_center + math.cos(angle) * distance),
            round(
                debris_center
                + math.sin(angle) * distance * 0.55
                - 8 * debris_progress
                + 13 * debris_progress * debris_progress
            ),
        )
        length = 5 if debris_index % 3 == 0 else 3
        end = (
            round(start[0] + math.cos(angle) * length),
            round(start[1] + math.sin(angle) * length),
        )
        alpha = round(220 * (1 - debris_progress) ** 1.35)
        color = (
            (*effect_color, alpha)
            if debris_index % 3 == 0
            else (158, 112, 58, alpha)
        )
        pygame.draw.line(debris, color, start, end, 1)
        if debris_index % 4 == 0:
            pygame.draw.circle(debris, color, end, 1)
    screen.blit(
        debris,
        (center[0] - debris_center, center[1] - debris_center),
    )

    signature_visibility = max(0, 1 - progress / 0.7)
    if enemy.get("hit_attacker_class") == "mage":
        rune = pygame.Surface((54, 54), pygame.SRCALPHA)
        radius = max(3, round(17 * signature_visibility))
        pygame.draw.circle(
            rune,
            (78, 174, 232, round(190 * signature_visibility)),
            (27, 27),
            radius,
            width=2,
        )
        screen.blit(rune, (center[0] - 27, center[1] - 27))
    elif enemy.get("hit_attacker_class") == "rogue":
        slash = pygame.Surface((54, 54), pygame.SRCALPHA)
        extent = round(8 + progress * 15)
        pygame.draw.line(
            slash,
            (202, 107, 229, round(190 * signature_visibility)),
            (27 - extent, 27 + extent),
            (27 + extent, 27 - extent),
            2,
        )
        screen.blit(slash, (center[0] - 27, center[1] - 27))
    elif enemy.get("hit_attacker_class") == "warrior":
        shock = pygame.Surface((54, 54), pygame.SRCALPHA)
        pygame.draw.arc(
            shock,
            (232, 89, 51, round(195 * signature_visibility)),
            (7, 19, 40, 22),
            math.radians(195),
            math.radians(345),
            3,
        )
        screen.blit(shock, (center[0] - 27, center[1] - 27))

    if enemy.get("hit_critical", False) and progress < 0.42:
        critical_visibility = 1 - progress / 0.42
        critical = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(
            critical,
            (255, 207, 86, round(205 * critical_visibility)),
            (32, 32),
            round(8 + progress * 24),
            width=2,
        )
        screen.blit(critical, (center[0] - 32, center[1] - 32))
    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )


def _draw_act_two_brute_hit_feedback(
    screen,
    enemy,
    sprite,
    position,
    current_time,
    damage_font,
):
    started_at = enemy.get("hit_animation_started_at", -1)
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < ACT_TWO_HIT_FEEDBACK_MS:
        screen.blit(sprite, position)
        return

    reaction_progress = min(1, elapsed / ACT_TWO_HIT_REACTION_MS)
    reaction = math.sin(math.pi * reaction_progress)
    offset_x, offset_y = _act_two_hit_offset(enemy, elapsed)
    offset_x = round(offset_x * 0.42)
    offset_y = round(offset_y * 0.42)
    shake = round(
        math.sin(elapsed / 17) * 2 * max(0, 1 - reaction_progress)
    )
    center = (
        position[0] + TILE_SIZE // 2 + offset_x + shake,
        position[1] + TILE_SIZE // 2 + offset_y + round(reaction * 3),
    )
    sprite_width = round(TILE_SIZE * (1 + reaction * 0.2))
    sprite_height = round(TILE_SIZE * (1 - reaction * 0.23))
    reacted_sprite = pygame.transform.scale(
        sprite,
        (sprite_width, max(20, sprite_height)),
    )
    sprite_position = reacted_sprite.get_rect(
        midbottom=(center[0], position[1] + TILE_SIZE + offset_y)
    )
    pygame.draw.ellipse(
        screen,
        (4, 5, 7),
        (
            center[0] - 13,
            position[1] + TILE_SIZE - 7,
            26,
            7,
        ),
    )
    screen.blit(reacted_sprite, sprite_position)

    if elapsed < ACT_TWO_HIT_REACTION_MS:
        flash = reacted_sprite.copy()
        flash.fill(
            (237, 211, 181, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        flash.set_alpha(round(205 * (1 - reaction_progress)))
        screen.blit(flash, sprite_position)

        effect_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
            enemy.get("hit_attacker_class"),
            (174, 91, 54),
        )
        impact = pygame.Surface((72, 40), pygame.SRCALPHA)
        impact_center = 36
        visibility = 1 - reaction_progress
        ring_width = round(10 + reaction_progress * 24)
        pygame.draw.arc(
            impact,
            (*effect_color, round(190 * visibility)),
            (
                impact_center - ring_width,
                20 - round(ring_width * 0.28),
                ring_width * 2,
                max(8, round(ring_width * 0.56)),
            ),
            math.pi,
            math.tau,
            2,
        )
        chunk_count = 8 if enemy.get("hit_critical", False) else 5
        for chunk_index in range(chunk_count):
            spread = (chunk_index / max(1, chunk_count - 1) - 0.5) * 38
            chunk_x = round(impact_center + spread * reaction_progress)
            chunk_y = round(
                22
                - math.sin(math.pi * reaction_progress)
                * (5 + chunk_index % 3 * 3)
            )
            pygame.draw.rect(
                impact,
                (118, 91, 70, round(210 * visibility)),
                (chunk_x, chunk_y, 2, 2),
            )
        screen.blit(
            impact,
            (center[0] - impact_center, position[1] + TILE_SIZE - 20),
        )

    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )


def _draw_act_two_brute_death(
    screen,
    enemy,
    sprite,
    current_time,
    damage_font,
):
    started_at = enemy.get("death_animation_started_at", -1)
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < ACT_TWO_BRUTE_DEATH_MS:
        return
    progress = elapsed / ACT_TWO_BRUTE_DEATH_MS
    center = (
        MAP_OFFSET_X
        + enemy["column"] * TILE_SIZE
        + TILE_SIZE // 2,
        MAP_OFFSET_Y
        + enemy["row"] * TILE_SIZE
        + TILE_SIZE // 2,
    )
    effect_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
        enemy.get("hit_attacker_class"),
        (171, 82, 49),
    )
    fall_progress = max(0, min(1, (progress - 0.08) / 0.55))
    fall_progress = fall_progress * fall_progress * (3 - 2 * fall_progress)
    impact_progress = max(0, min(1, (progress - 0.48) / 0.3))

    shadow = pygame.Surface((48, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(
        shadow,
        (4, 5, 7, round(125 * (1 - progress * 0.55))),
        shadow.get_rect(),
    )
    screen.blit(shadow, (center[0] - 24, center[1] + 7))

    if progress < 0.86:
        body = sprite.copy()
        if elapsed < 120:
            flash = body.copy()
            flash.fill(
                (239, 211, 179, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            flash.set_alpha(round(215 * (1 - elapsed / 120)))
            body.blit(flash, (0, 0))
        else:
            shade = max(50, round(210 * (1 - progress * 0.78)))
            body.fill(
                (shade, shade, shade, 255),
                special_flags=pygame.BLEND_RGBA_MULT,
            )
        body_width = round(TILE_SIZE * (1 + fall_progress * 0.28))
        body_height = max(8, round(TILE_SIZE * (1 - fall_progress * 0.58)))
        body = pygame.transform.smoothscale(
            body,
            (body_width, body_height),
        )
        body.set_alpha(round(255 * min(1, (0.86 - progress) * 4)))
        body_rectangle = body.get_rect(
            midbottom=(
                center[0] + round(fall_progress * 3),
                center[1] + 15,
            )
        )
        screen.blit(body, body_rectangle)

    if 0 < impact_progress < 1:
        impact_visibility = math.sin(math.pi * impact_progress)
        impact = pygame.Surface((88, 48), pygame.SRCALPHA)
        impact_center = 44
        ring_width = round(13 + impact_progress * 29)
        pygame.draw.arc(
            impact,
            (*effect_color, round(185 * impact_visibility)),
            (
                impact_center - ring_width,
                18 - round(ring_width * 0.22),
                ring_width * 2,
                max(10, round(ring_width * 0.44)),
            ),
            math.pi,
            math.tau,
            3,
        )
        pygame.draw.line(
            impact,
            (151, 112, 80, round(150 * impact_visibility)),
            (impact_center - ring_width, 21),
            (impact_center + ring_width, 21),
            2,
        )
        screen.blit(impact, (center[0] - impact_center, center[1] - 7))

    debris = pygame.Surface((88, 64), pygame.SRCALPHA)
    debris_center_x = 44
    for chunk_index in range(18):
        delay = (chunk_index % 6) * 28
        chunk_elapsed = elapsed - delay
        if chunk_elapsed < 0:
            continue
        chunk_progress = min(
            1,
            chunk_elapsed / max(1, ACT_TWO_BRUTE_DEATH_MS - delay),
        )
        angle = math.radians(195 + (chunk_index * 151) % 150)
        distance = (9 + chunk_index % 6 * 4) * chunk_progress
        chunk_position = (
            round(debris_center_x + math.cos(angle) * distance),
            round(
                35
                + math.sin(angle) * distance * 0.42
                - 11 * chunk_progress
                + 17 * chunk_progress * chunk_progress
            ),
        )
        alpha = round(215 * (1 - chunk_progress) ** 1.4)
        color = (
            (*effect_color, alpha)
            if chunk_index % 4 == 0
            else (105, 79, 64, alpha)
        )
        size = 3 if chunk_index % 5 == 0 else 2
        pygame.draw.rect(
            debris,
            color,
            (*chunk_position, size, size),
        )
    screen.blit(
        debris,
        (center[0] - debris_center_x, center[1] - 32),
    )

    signature_visibility = max(0, 1 - progress / 0.76)
    signature = pygame.Surface((64, 64), pygame.SRCALPHA)
    attacker_class = enemy.get("hit_attacker_class")
    if attacker_class == "warrior":
        pygame.draw.arc(
            signature,
            (235, 88, 51, round(205 * signature_visibility)),
            (7, 20, 50, 28),
            math.radians(195),
            math.radians(345),
            4,
        )
    elif attacker_class == "rogue":
        extent = round(9 + progress * 19)
        for slope in (-1, 1):
            pygame.draw.line(
                signature,
                (200, 102, 229, round(190 * signature_visibility)),
                (32 - extent, 32 - extent * slope),
                (32 + extent, 32 + extent * slope),
                2,
            )
    elif attacker_class == "mage":
        radius = max(3, round(21 * signature_visibility))
        pygame.draw.circle(
            signature,
            (74, 169, 230, round(195 * signature_visibility)),
            (32, 32),
            radius,
            width=3,
        )
    screen.blit(signature, (center[0] - 32, center[1] - 32))

    if enemy.get("hit_critical", False) and progress < 0.46:
        critical_visibility = 1 - progress / 0.46
        critical = pygame.Surface((72, 72), pygame.SRCALPHA)
        pygame.draw.circle(
            critical,
            (255, 205, 82, round(205 * critical_visibility)),
            (36, 36),
            round(9 + progress * 28),
            width=3,
        )
        screen.blit(critical, (center[0] - 36, center[1] - 36))
    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )


def _draw_act_two_sentinel_hit_feedback(
    screen,
    enemy,
    sprite,
    position,
    current_time,
    damage_font,
):
    started_at = enemy.get("hit_animation_started_at", -1)
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < ACT_TWO_HIT_FEEDBACK_MS:
        screen.blit(sprite, position)
        return

    blocked = enemy.get("hit_blocked", False)
    reaction_progress = min(1, elapsed / ACT_TWO_HIT_REACTION_MS)
    reaction = math.sin(math.pi * reaction_progress)
    offset_x, offset_y = _act_two_hit_offset(enemy, elapsed)
    if blocked:
        offset_x = 0
        offset_y = 0
    else:
        offset_x = round(offset_x * 0.68)
        offset_y = round(offset_y * 0.68)
    center = (
        position[0] + TILE_SIZE // 2 + offset_x,
        position[1] + TILE_SIZE // 2 + offset_y,
    )
    origin = enemy.get("hit_origin")
    rotation_direction = 1
    if origin is not None and origin[0] > enemy["column"]:
        rotation_direction = -1
    angle = 0 if blocked else rotation_direction * reaction * 6
    reacted_sprite = pygame.transform.rotozoom(sprite, angle, 1)
    sprite_position = reacted_sprite.get_rect(center=center)
    pygame.draw.ellipse(
        screen,
        (4, 5, 7),
        (center[0] - 11, position[1] + TILE_SIZE - 7, 22, 6),
    )
    screen.blit(reacted_sprite, sprite_position)

    if elapsed < ACT_TWO_HIT_REACTION_MS:
        flash = reacted_sprite.copy()
        flash_color = (
            (232, 184, 72, 0)
            if blocked
            else (208, 220, 222, 0)
        )
        flash.fill(flash_color, special_flags=pygame.BLEND_RGBA_ADD)
        flash.set_alpha(round(220 * (1 - reaction_progress)))
        screen.blit(flash, sprite_position)

        effect = pygame.Surface((72, 72), pygame.SRCALPHA)
        effect_center = 36
        visibility = 1 - reaction_progress
        effect_color = (
            (239, 190, 73)
            if blocked
            else ACT_TWO_CLASS_EFFECT_COLORS.get(
                enemy.get("hit_attacker_class"),
                (151, 168, 172),
            )
        )
        if blocked:
            shield_radius = round(14 + reaction_progress * 13)
            pygame.draw.arc(
                effect,
                (*effect_color, round(235 * visibility)),
                (
                    effect_center - shield_radius,
                    effect_center - shield_radius,
                    shield_radius * 2,
                    shield_radius * 2,
                ),
                math.radians(-70),
                math.radians(250),
                4,
            )
        spark_count = 11 if blocked else 7
        for spark_index in range(spark_count):
            angle_radians = (
                spark_index * math.tau / spark_count
                + enemy["column"] * 0.23
            )
            inner = 7 + reaction_progress * 8
            outer = inner + 5 + reaction_progress * 9
            start = (
                round(effect_center + math.cos(angle_radians) * inner),
                round(effect_center + math.sin(angle_radians) * inner),
            )
            end = (
                round(effect_center + math.cos(angle_radians) * outer),
                round(effect_center + math.sin(angle_radians) * outer),
            )
            pygame.draw.line(
                effect,
                (*effect_color, round(225 * visibility)),
                start,
                end,
                2 if blocked or spark_index % 3 == 0 else 1,
            )
        screen.blit(
            effect,
            (center[0] - effect_center, center[1] - effect_center),
        )

    if blocked and damage_font is not None:
        progress = elapsed / ACT_TWO_HIT_FEEDBACK_MS
        alpha = round(255 * min(1, (1 - progress) * 2.3))
        label = damage_font.render("BLOCK", True, (245, 199, 83))
        label.set_alpha(alpha)
        label_rectangle = label.get_rect(
            midbottom=(
                center[0],
                position[1] - 6 - round(progress * 12),
            )
        )
        shadow = damage_font.render("BLOCK", True, (16, 10, 7))
        shadow.set_alpha(alpha)
        screen.blit(shadow, label_rectangle.move(1, 2))
        screen.blit(label, label_rectangle)
    else:
        _draw_act_two_damage_number(
            screen,
            enemy,
            current_time,
            damage_font,
        )


def _draw_act_two_sentinel_death(
    screen,
    enemy,
    sprite,
    current_time,
    damage_font,
):
    started_at = enemy.get("death_animation_started_at", -1)
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < ACT_TWO_SENTINEL_DEATH_MS:
        return
    progress = elapsed / ACT_TWO_SENTINEL_DEATH_MS
    collapse_progress = min(1, progress / 0.66)
    collapse_progress = (
        collapse_progress
        * collapse_progress
        * (3 - 2 * collapse_progress)
    )
    center = (
        MAP_OFFSET_X
        + enemy["column"] * TILE_SIZE
        + TILE_SIZE // 2,
        MAP_OFFSET_Y
        + enemy["row"] * TILE_SIZE
        + TILE_SIZE // 2,
    )
    effect_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
        enemy.get("hit_attacker_class"),
        (144, 160, 165),
    )

    shadow = pygame.Surface((44, 16), pygame.SRCALPHA)
    pygame.draw.ellipse(
        shadow,
        (4, 5, 7, round(115 * (1 - progress * 0.6))),
        shadow.get_rect(),
    )
    screen.blit(shadow, (center[0] - 22, center[1] + 8))

    if progress < 0.82:
        body = sprite.copy()
        if elapsed < 110:
            flash = body.copy()
            flash.fill(
                (220, 229, 226, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            flash.set_alpha(round(220 * (1 - elapsed / 110)))
            body.blit(flash, (0, 0))
        else:
            shade = max(58, round(215 * (1 - progress * 0.72)))
            body.fill(
                (shade, shade, shade, 255),
                special_flags=pygame.BLEND_RGBA_MULT,
            )
        body = pygame.transform.rotozoom(
            body,
            -24 * collapse_progress,
            1,
        )
        body_width = round(body.get_width() * (1 + collapse_progress * 0.14))
        body_height = max(
            7,
            round(body.get_height() * (1 - collapse_progress * 0.55)),
        )
        body = pygame.transform.smoothscale(
            body,
            (body_width, body_height),
        )
        body.set_alpha(round(255 * min(1, (0.82 - progress) * 4.2)))
        body_rectangle = body.get_rect(
            midbottom=(
                center[0] + round(collapse_progress * 5),
                center[1] + 15,
            )
        )
        screen.blit(body, body_rectangle)

    shards = pygame.Surface((84, 76), pygame.SRCALPHA)
    shard_center = (42, 38)
    for shard_index in range(16):
        delay = (shard_index % 5) * 27
        shard_elapsed = elapsed - delay
        if shard_elapsed < 0:
            continue
        shard_progress = min(
            1,
            shard_elapsed / max(1, ACT_TWO_SENTINEL_DEATH_MS - delay),
        )
        angle = math.radians(
            (enemy["column"] * 31 + enemy["row"] * 47 + shard_index * 137)
            % 360
        )
        distance = (10 + shard_index % 5 * 4) * shard_progress
        shard_position = (
            round(shard_center[0] + math.cos(angle) * distance),
            round(
                shard_center[1]
                + math.sin(angle) * distance * 0.62
                - 13 * shard_progress
                + 18 * shard_progress * shard_progress
            ),
        )
        alpha = round(225 * (1 - shard_progress) ** 1.35)
        color = (
            (*effect_color, alpha)
            if shard_index % 4 == 0
            else (133, 146, 148, alpha)
        )
        shard_size = 4 if shard_index % 5 == 0 else 3
        pygame.draw.polygon(
            shards,
            color,
            (
                (shard_position[0], shard_position[1] - shard_size),
                (shard_position[0] + shard_size, shard_position[1] + 1),
                (shard_position[0] - 1, shard_position[1] + shard_size),
            ),
        )
    screen.blit(shards, (center[0] - 42, center[1] - 38))

    impact_progress = max(0, min(1, (progress - 0.5) / 0.3))
    if 0 < impact_progress < 1:
        visibility = math.sin(math.pi * impact_progress)
        impact = pygame.Surface((82, 42), pygame.SRCALPHA)
        radius = round(13 + impact_progress * 25)
        pygame.draw.arc(
            impact,
            (151, 169, 172, round(165 * visibility)),
            (41 - radius, 13, radius * 2, 22),
            math.pi,
            math.tau,
            2,
        )
        screen.blit(impact, (center[0] - 41, center[1] - 5))

    signature_visibility = max(0, 1 - progress / 0.74)
    signature = pygame.Surface((68, 68), pygame.SRCALPHA)
    attacker_class = enemy.get("hit_attacker_class")
    if attacker_class == "warrior":
        pygame.draw.arc(
            signature,
            (234, 88, 51, round(200 * signature_visibility)),
            (7, 21, 54, 30),
            math.radians(195),
            math.radians(345),
            4,
        )
    elif attacker_class == "rogue":
        extent = round(9 + progress * 20)
        for slope in (-1, 1):
            pygame.draw.line(
                signature,
                (201, 104, 231, round(190 * signature_visibility)),
                (34 - extent, 34 - extent * slope),
                (34 + extent, 34 + extent * slope),
                2,
            )
    elif attacker_class == "mage":
        radius = max(3, round(22 * signature_visibility))
        pygame.draw.circle(
            signature,
            (73, 171, 232, round(195 * signature_visibility)),
            (34, 34),
            radius,
            width=3,
        )
    screen.blit(signature, (center[0] - 34, center[1] - 34))

    if enemy.get("hit_critical", False) and progress < 0.45:
        visibility = 1 - progress / 0.45
        critical = pygame.Surface((72, 72), pygame.SRCALPHA)
        pygame.draw.circle(
            critical,
            (255, 210, 88, round(205 * visibility)),
            (36, 36),
            round(9 + progress * 28),
            width=3,
        )
        screen.blit(critical, (center[0] - 36, center[1] - 36))
    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )


def _draw_act_two_priest_hit_feedback(
    screen,
    enemy,
    sprite,
    position,
    current_time,
    damage_font,
):
    started_at = enemy.get("hit_animation_started_at", -1)
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < ACT_TWO_HIT_FEEDBACK_MS:
        screen.blit(sprite, position)
        return

    reaction_progress = min(1, elapsed / ACT_TWO_HIT_REACTION_MS)
    reaction = math.sin(math.pi * reaction_progress)
    offset_x, offset_y = _act_two_hit_offset(enemy, elapsed)
    offset_x = round(offset_x * 0.42)
    offset_y = round(offset_y * 0.42 - reaction * 2)
    center = (
        position[0] + TILE_SIZE // 2 + offset_x,
        position[1] + TILE_SIZE // 2 + offset_y,
    )
    origin = enemy.get("hit_origin")
    rotation_direction = -1
    if origin is not None and origin[0] > enemy["column"]:
        rotation_direction = 1
    reacted_sprite = pygame.transform.rotozoom(
        sprite,
        rotation_direction * reaction * 4,
        1 + reaction * 0.025,
    )
    sprite_position = reacted_sprite.get_rect(center=center)
    pygame.draw.ellipse(
        screen,
        (3, 7, 7),
        (center[0] - 10, position[1] + TILE_SIZE - 6, 20, 5),
    )
    screen.blit(reacted_sprite, sprite_position)

    if elapsed < ACT_TWO_HIT_REACTION_MS:
        visibility = 1 - reaction_progress
        flash = reacted_sprite.copy()
        flash.fill((117, 229, 173, 0), special_flags=pygame.BLEND_RGBA_ADD)
        flash.set_alpha(round(205 * visibility))
        screen.blit(flash, sprite_position)

        aura = pygame.Surface((84, 84), pygame.SRCALPHA)
        aura_center = 42
        aura_color = (75, 208, 143)
        class_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
            enemy.get("hit_attacker_class"),
            (189, 234, 204),
        )
        radius = round(17 + reaction_progress * 13)
        for arc_index in range(5):
            start = (
                arc_index * math.tau / 5
                + enemy["row"] * 0.17
                + reaction_progress * 0.35
            )
            pygame.draw.arc(
                aura,
                (*aura_color, round(205 * visibility)),
                (
                    aura_center - radius,
                    aura_center - radius,
                    radius * 2,
                    radius * 2,
                ),
                start,
                start + 0.55,
                2,
            )
        for mote_index in range(10):
            angle = mote_index * math.tau / 10 + enemy["column"] * 0.31
            distance = 10 + reaction_progress * (13 + mote_index % 3 * 3)
            mote = (
                round(aura_center + math.cos(angle) * distance),
                round(aura_center + math.sin(angle) * distance),
            )
            color = class_color if mote_index % 4 == 0 else aura_color
            pygame.draw.circle(
                aura,
                (*color, round(225 * visibility)),
                mote,
                2 if mote_index % 3 == 0 else 1,
            )
        screen.blit(aura, (center[0] - aura_center, center[1] - aura_center))

    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )


def _draw_act_two_priest_death(
    screen,
    enemy,
    sprite,
    current_time,
    damage_font,
):
    started_at = enemy.get("death_animation_started_at", -1)
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < ACT_TWO_PRIEST_DEATH_MS:
        return
    progress = elapsed / ACT_TWO_PRIEST_DEATH_MS
    dissolve_progress = min(1, progress / 0.78)
    dissolve_progress = dissolve_progress * dissolve_progress * (
        3 - 2 * dissolve_progress
    )
    center = (
        MAP_OFFSET_X + enemy["column"] * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + enemy["row"] * TILE_SIZE + TILE_SIZE // 2,
    )
    class_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
        enemy.get("hit_attacker_class"),
        (79, 202, 144),
    )

    shadow = pygame.Surface((36, 12), pygame.SRCALPHA)
    pygame.draw.ellipse(
        shadow,
        (2, 7, 7, round(105 * (1 - dissolve_progress))),
        shadow.get_rect(),
    )
    screen.blit(shadow, (center[0] - 18, center[1] + 10))

    if progress < 0.8:
        body = sprite.copy()
        if elapsed < 120:
            flash = body.copy()
            flash.fill((126, 239, 180, 0), special_flags=pygame.BLEND_RGBA_ADD)
            flash.set_alpha(round(220 * (1 - elapsed / 120)))
            body.blit(flash, (0, 0))
        shade = max(70, round(255 * (1 - dissolve_progress * 0.68)))
        body.fill((shade, shade, shade, 255), special_flags=pygame.BLEND_RGBA_MULT)
        body_width = max(10, round(body.get_width() * (1 - dissolve_progress * 0.16)))
        body_height = max(8, round(body.get_height() * (1 + dissolve_progress * 0.12)))
        body = pygame.transform.smoothscale(body, (body_width, body_height))
        body.set_alpha(round(255 * min(1, (0.8 - progress) * 4.5)))
        body_rectangle = body.get_rect(
            center=(center[0], center[1] - round(dissolve_progress * 9))
        )
        screen.blit(body, body_rectangle)

    magic = pygame.Surface((92, 104), pygame.SRCALPHA)
    magic_center = (46, 61)
    aura_visibility = max(0, 1 - progress / 0.68)
    aura_radius = round(14 + progress * 24)
    for arc_index in range(7):
        start = arc_index * math.tau / 7 + progress * 1.4
        pygame.draw.arc(
            magic,
            (63, 202, 139, round(180 * aura_visibility)),
            (
                magic_center[0] - aura_radius,
                magic_center[1] - aura_radius,
                aura_radius * 2,
                aura_radius * 2,
            ),
            start,
            start + 0.42,
            2,
        )
    for mote_index in range(18):
        delay = (mote_index % 6) * 31
        mote_elapsed = elapsed - delay
        if mote_elapsed < 0:
            continue
        mote_progress = min(
            1,
            mote_elapsed / max(1, ACT_TWO_PRIEST_DEATH_MS - delay),
        )
        angle = math.radians(
            (enemy["column"] * 29 + enemy["row"] * 43 + mote_index * 139)
            % 360
        )
        spread = (5 + mote_index % 5 * 3) * mote_progress
        mote_position = (
            round(magic_center[0] + math.cos(angle) * spread),
            round(
                magic_center[1]
                + math.sin(angle) * spread * 0.35
                - (18 + mote_index % 4 * 5) * mote_progress
            ),
        )
        alpha = round(220 * (1 - mote_progress) ** 1.25)
        color = class_color if mote_index % 5 == 0 else (65, 190, 137)
        radius = 3 if mote_index % 6 == 0 else 2
        pygame.draw.circle(magic, (*color, alpha), mote_position, radius)
    screen.blit(magic, (center[0] - 46, center[1] - 61))

    signature_visibility = max(0, 1 - progress / 0.72)
    signature = pygame.Surface((68, 68), pygame.SRCALPHA)
    attacker_class = enemy.get("hit_attacker_class")
    if attacker_class == "warrior":
        pygame.draw.arc(
            signature,
            (234, 88, 51, round(210 * signature_visibility)),
            (6, 18, 56, 34),
            math.radians(190),
            math.radians(350),
            4,
        )
    elif attacker_class == "rogue":
        extent = round(9 + progress * 19)
        for slope in (-1, 1):
            pygame.draw.line(
                signature,
                (201, 104, 231, round(200 * signature_visibility)),
                (34 - extent, 34 - extent * slope),
                (34 + extent, 34 + extent * slope),
                2,
            )
    elif attacker_class == "mage":
        radius = max(3, round(21 * signature_visibility))
        pygame.draw.circle(
            signature,
            (73, 171, 232, round(205 * signature_visibility)),
            (34, 34),
            radius,
            width=3,
        )
    screen.blit(signature, (center[0] - 34, center[1] - 34))

    if enemy.get("hit_critical", False) and progress < 0.44:
        visibility = 1 - progress / 0.44
        critical = pygame.Surface((72, 72), pygame.SRCALPHA)
        pygame.draw.circle(
            critical,
            (255, 213, 91, round(205 * visibility)),
            (36, 36),
            round(9 + progress * 28),
            width=3,
        )
        screen.blit(critical, (center[0] - 36, center[1] - 36))
    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )


def draw_enemy(
    screen,
    enemy,
    act_number,
    sprites,
    current_time=0,
    damage_font=None,
):
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
    if act_number < 2 and enemy["health"] <= 0:
        _draw_act_one_enemy_death(
            screen,
            enemy,
            current_time,
            _act_one_enemy_color(color, enemy["is_aggro"]),
        )
        return
    if (
        act_number == 2
        and enemy["type"] in (
            "goblin",
            "archer",
            "brute",
            "sentinel",
            "priest",
        )
        and enemy["health"] <= 0
    ):
        standing_sprite_names = {
            "goblin": "goblin",
            "archer": "archer",
            "brute": "brute",
            "sentinel": "sentinel_idle",
            "priest": "priest_idle",
        }
        _draw_act_two_enemy_death(
            screen,
            enemy,
            sprites[standing_sprite_names[enemy["type"]]],
            sprites[f"{enemy['type']}_death"],
            current_time,
            damage_font,
        )
        return

    hit_effect_active = False
    hit_flash_active = False
    movement_offset_x = 0
    movement_offset_y = 0
    if act_number < 2:
        color = _act_one_enemy_color(color, enemy["is_aggro"])
        movement_kind = enemy["type"]
        movement_offset_x, movement_offset_y = (
            _act_one_movement_offset(
                column,
                row,
                enemy.get("movement_origin"),
                current_time,
                enemy.get("movement_animation_started_at", 0),
                movement_kind,
            )
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

    if act_number >= 2 and enemy["type"] == "oracle":
        body_size = TILE_SIZE * 3
        body_left = MAP_OFFSET_X + (column - 1) * TILE_SIZE
        body_top = MAP_OFFSET_Y + (row - 1) * TILE_SIZE
        sprite_name = (
            "oracle_awake"
            if enemy["oracle_awakened"]
            else "oracle_idle"
        )
        screen.blit(
            sprites[sprite_name],
            (body_left, body_top),
        )

        if enemy["is_active"]:
            pygame.draw.rect(
                screen,
                DANGER_BORDER_COLOR,
                (
                    body_left + 2,
                    body_top + 2,
                    body_size - 4,
                    body_size - 4,
                ),
                width=2,
                border_radius=5,
            )

        health_ratio = enemy["health"] / enemy["max_health"]
        bar_x = body_left + 8
        bar_y = body_top + body_size - 7
        bar_width = body_size - 16
        bar_height = 5
        pygame.draw.rect(
            screen,
            HEALTH_BAR_BACKGROUND,
            (bar_x, bar_y, bar_width, bar_height),
        )
        pygame.draw.rect(
            screen,
            HEALTH_BAR_COLOR,
            (
                bar_x,
                bar_y,
                int(bar_width * health_ratio),
                bar_height,
            ),
        )

        if enemy["attack_targets"]:
            warning_x = body_left + body_size // 2
            warning_top = body_top + 8
            pygame.draw.line(
                screen,
                ATTACK_WARNING_COLOR,
                (warning_x, warning_top),
                (warning_x, warning_top + 12),
                4,
            )
            pygame.draw.circle(
                screen,
                ATTACK_WARNING_COLOR,
                (warning_x, warning_top + 19),
                3,
            )

        return

    if act_number < 2:
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
    elif (
        act_number >= 2
        and enemy["type"] in (
            "goblin",
            "brute",
            "archer",
            "sentinel",
            "priest",
        )
    ):
        sprite_name = enemy["type"]

        if enemy["type"] in (
            "goblin",
            "brute",
            "archer",
            "sentinel",
            "priest",
        ):
            attack_started_at = enemy.get(
                "attack_animation_started_at",
                0,
            )
            attack_elapsed = current_time - attack_started_at
            if (
                attack_started_at > 0
                and 0 <= attack_elapsed < ACT_TWO_ENEMY_ATTACK_FRAME_MS
            ):
                sprite_name = (
                    "priest_cast"
                    if (
                        enemy["type"] == "priest"
                        and enemy.get("attack_effect_mode") == "heal"
                    )
                    else f"{enemy['type']}_attack"
                )
        if enemy["type"] == "sentinel" and sprite_name == "sentinel":
            sprite_name = (
                "sentinel_guard"
                if enemy["shield_turns"] > 0
                else "sentinel_idle"
            )
        elif enemy["type"] == "priest" and sprite_name == "priest":
            sprite_name = (
                "priest_cast"
                if (
                    enemy["attack_targets"]
                    or enemy["heal_target"] is not None
                )
                else "priest_idle"
            )
        enemy_sprite = sprites[sprite_name]
        enemy_position = (
            MAP_OFFSET_X + column * TILE_SIZE,
            MAP_OFFSET_Y + row * TILE_SIZE,
        )
        if act_number == 2 and enemy["type"] == "goblin":
            _draw_act_two_goblin_hit_feedback(
                screen,
                enemy,
                enemy_sprite,
                enemy_position,
                current_time,
                damage_font,
            )
        elif act_number == 2 and enemy["type"] == "archer":
            _draw_act_two_archer_hit_feedback(
                screen,
                enemy,
                enemy_sprite,
                enemy_position,
                current_time,
                damage_font,
            )
        elif act_number == 2 and enemy["type"] == "brute":
            _draw_act_two_brute_hit_feedback(
                screen,
                enemy,
                enemy_sprite,
                enemy_position,
                current_time,
                damage_font,
            )
        elif act_number == 2 and enemy["type"] == "sentinel":
            _draw_act_two_sentinel_hit_feedback(
                screen,
                enemy,
                enemy_sprite,
                enemy_position,
                current_time,
                damage_font,
            )
        elif act_number == 2 and enemy["type"] == "priest":
            _draw_act_two_priest_hit_feedback(
                screen,
                enemy,
                enemy_sprite,
                enemy_position,
                current_time,
                damage_font,
            )
        else:
            screen.blit(enemy_sprite, enemy_position)

        if (
            enemy["type"] == "sentinel"
            and enemy["shield_turns"] > 0
        ):
            opening_color = (235, 185, 75)
            tile_left = MAP_OFFSET_X + column * TILE_SIZE
            tile_top = MAP_OFFSET_Y + row * TILE_SIZE
            shield_direction = enemy["shield_direction"]
            vulnerable_direction = (
                -shield_direction[0],
                -shield_direction[1],
            )
            opening_lines = {
                (0, -1): (
                    (tile_left + 5, tile_top + 3),
                    (tile_left + TILE_SIZE - 5, tile_top + 3),
                ),
                (0, 1): (
                    (tile_left + 5, tile_top + TILE_SIZE - 3),
                    (
                        tile_left + TILE_SIZE - 5,
                        tile_top + TILE_SIZE - 3,
                    ),
                ),
                (-1, 0): (
                    (tile_left + 3, tile_top + 5),
                    (tile_left + 3, tile_top + TILE_SIZE - 5),
                ),
                (1, 0): (
                    (tile_left + TILE_SIZE - 3, tile_top + 5),
                    (
                        tile_left + TILE_SIZE - 3,
                        tile_top + TILE_SIZE - 5,
                    ),
                ),
            }
            opening_line = opening_lines.get(
                vulnerable_direction
            )

            if opening_line is not None:
                pygame.draw.line(
                    screen,
                    opening_color,
                    opening_line[0],
                    opening_line[1],
                    3,
                )

        if (
            enemy["type"] == "priest"
            and enemy["heal_target"] is not None
            and enemy["heal_target"]["health"] > 0
        ):
            heal_target = enemy["heal_target"]
            pygame.draw.rect(
                screen,
                (80, 220, 130),
                (
                    MAP_OFFSET_X
                    + heal_target["column"] * TILE_SIZE
                    + 3,
                    MAP_OFFSET_Y
                    + heal_target["row"] * TILE_SIZE
                    + 3,
                    TILE_SIZE - 6,
                    TILE_SIZE - 6,
                ),
                width=2,
                border_radius=4,
            )

        if enemy["is_aggro"]:
            pygame.draw.rect(
                screen,
                DANGER_BORDER_COLOR,
                (
                    MAP_OFFSET_X + column * TILE_SIZE + 2,
                    MAP_OFFSET_Y + row * TILE_SIZE + 2,
                    TILE_SIZE - 4,
                    TILE_SIZE - 4,
                ),
                width=2,
                border_radius=3,
            )
    elif enemy["type"] == "brute":
        corner = 4
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + corner, y),
                (x + size - corner, y),
                (x + size, y + corner),
                (x + size, y + size - corner),
                (x + size - corner, y + size),
                (x + corner, y + size),
                (x, y + size - corner),
                (x, y + corner),
            ],
        )
    elif enemy["type"] == "archer":
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + size // 2, y),
                (x + size, y + size),
                (x, y + size),
            ],
        )
        pygame.draw.line(
            screen,
            tuple(min(255, channel + 38) for channel in color),
            (x + size // 2, y + 4),
            (x + size - 4, y + size - 4),
            2,
        )
    elif enemy["type"] == "warden":
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + size // 2, y),
                (x + size, y + size // 2),
                (x + size // 2, y + size),
                (x, y + size // 2),
            ],
        )
        crown_y = y + size // 4
        pygame.draw.line(
            screen,
            ATTACK_WARNING_COLOR,
            (x + size // 4, crown_y),
            (x + size * 3 // 4, crown_y),
            2,
        )
        pygame.draw.circle(
            screen,
            ATTACK_WARNING_COLOR,
            (x + size // 2, y + size // 2),
            3,
        )
    else:
        pygame.draw.rect(
            screen,
            color,
            (x, y, size, size),
            border_radius=6,
        )
        if act_number < 2:
            pygame.draw.line(
                screen,
                tuple(min(255, channel + 30) for channel in color),
                (x + 4, y + 4),
                (x + size - 5, y + 4),
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
    bar_height = 4

    pygame.draw.rect(
        screen,
        HEALTH_BAR_BACKGROUND,
        (bar_x, bar_y, bar_width, bar_height),
    )
    pygame.draw.rect(
        screen,
        (
            (236, 75, 78)
            if hit_effect_active
            else HEALTH_BAR_COLOR
        ),
        (bar_x, bar_y, int(bar_width * health_ratio), bar_height),
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
        screen.blit(
            sprites["key"],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
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
        screen.blit(
            sprites["potion"],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
        return

    cell_x = MAP_OFFSET_X + column * TILE_SIZE
    cell_y = MAP_OFFSET_Y + row * TILE_SIZE
    bottle_rectangle = pygame.Rect(
        cell_x + TILE_SIZE // 2 - 6,
        cell_y + 11,
        12,
        17,
    )

    _draw_act_one_glow(
        screen,
        (cell_x + TILE_SIZE // 2, cell_y + 19),
        (35, 123, 86),
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
        (30, 87, 69),
        bottle_rectangle,
        border_radius=4,
    )
    pygame.draw.rect(
        screen,
        (76, 184, 126),
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
        screen.blit(
            sprites["coin"],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
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


def draw_breakable_crate(screen, crate, sprites):
    suffix = "_broken" if crate["is_broken"] else ""
    sprite_name = f"breakable_crate_{crate['variant']}{suffix}"
    screen.blit(
        sprites[sprite_name],
        (
            MAP_OFFSET_X + crate["column"] * TILE_SIZE,
            MAP_OFFSET_Y + crate["row"] * TILE_SIZE,
        ),
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
        prefix = (
            "stash"
            if chest.get("appearance", "standard") == "stash"
            else "chest"
        )
        state = "open" if chest["is_open"] else "closed"
        sprite_name = f"{prefix}_{state}"
        screen.blit(sprites[sprite_name], (cell_x, cell_y))
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
        sprite_name = (
            "stairs_open" if is_open else "stairs_locked"
        )
        screen.blit(
            sprites[sprite_name],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
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
