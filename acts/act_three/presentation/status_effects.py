import math

import pygame


from presentation.layout import ACT_THREE_TILE_SIZE
from settings import PALADIN_HOLY_HAND_EFFECT_MS


_TORCH_LIGHT_SURFACE = None
_IDLE_FRAME_SEQUENCE = (0, 1, 2, 1)
_IDLE_TIMELINE_CYCLE_COUNT = 4
_MOVE_FRAME_COUNT = 2
_MOVE_FRAME_DURATION_MS = 90
_ATTACK_FRAME_DURATION_MS = 240
_FAMILIAR_MOVE_DURATION_MS = 180
_TELEPORT_CAMERA_DURATION_MS = 480
_TELEPORT_EFFECT_DURATION_MS = 600
_ARCHER_BARRAGE_SHOT_EFFECT_MS = 360
_TOP_VOID_CORNER_Y_OFFSET = 47
_TOP_VOID_CORNER_X_OFFSETS = {
    "wall_corner_top_left": -18,
    "wall_corner_top_right": 18,
}
_TOP_VOID_DOUBLE_CORNER_CROP_WIDTH = 24

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
