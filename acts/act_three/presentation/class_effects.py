import math

import pygame


from presentation.layout import (
    ACT_THREE_TILE_SIZE,
    ACT_THREE_VIEW_HEIGHT,
    ACT_THREE_VIEW_WIDTH,
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
    pulse = 0.5 + 0.5 * math.sin(
        current_time / 520
    )
    overlay.fill(
        (
            8,
            2,
            18,
            round(38 + pulse * 14),
        )
    )
    surface.blit(
        overlay,
        (0, 0),
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


def _draw_summoner_bond_pentagram(
    surface,
    left,
    top,
    current_time,
):
    margin = 22
    effect_surface = pygame.Surface(
        (
            ACT_THREE_TILE_SIZE + margin * 2,
            ACT_THREE_TILE_SIZE + margin * 2,
        ),
        pygame.SRCALPHA,
    )
    center = (
        margin + ACT_THREE_TILE_SIZE // 2,
        margin + ACT_THREE_TILE_SIZE // 2 + 8,
    )
    pulse = 0.5 + 0.5 * math.sin(current_time / 260)
    radius = 27 + round(pulse * 2)
    glow_color = (54, 239, 227, round(55 + pulse * 35))
    line_color = (109, 255, 244, round(175 + pulse * 65))
    pygame.draw.circle(
        effect_surface,
        glow_color,
        center,
        radius + 4,
        width=3,
    )
    pygame.draw.circle(
        effect_surface,
        line_color,
        center,
        radius,
        width=1,
    )
    surface.blit(effect_surface, (left - margin, top - margin))


def _draw_summoner_familiar_attack_glow(
    surface,
    left,
    top,
    current_time,
):
    margin = 12
    effect_surface = pygame.Surface(
        (
            ACT_THREE_TILE_SIZE + margin * 2,
            ACT_THREE_TILE_SIZE + margin * 2,
        ),
        pygame.SRCALPHA,
    )
    center = (
        margin + ACT_THREE_TILE_SIZE // 2,
        margin + 35,
    )
    pulse = 0.5 + 0.5 * math.sin(current_time / 55)
    alpha = round(90 + pulse * 85)
    pygame.draw.circle(
        effect_surface,
        (26, 238, 225, alpha // 4),
        center,
        15 + round(pulse * 3),
    )
    pygame.draw.circle(
        effect_surface,
        (92, 255, 243, alpha),
        center,
        10 + round(pulse * 2),
        width=2,
    )
    pygame.draw.arc(
        effect_surface,
        (188, 255, 250, min(255, alpha + 45)),
        (
            center[0] - 16,
            center[1] - 16,
            32,
            32,
        ),
        0.25,
        2.4,
        width=2,
    )
    for spark_index in range(5):
        phase = current_time / 90 + spark_index * math.tau / 5
        spark_x = center[0] + round(math.cos(phase) * 14)
        spark_y = center[1] + round(math.sin(phase) * 10)
        pygame.draw.line(
            effect_surface,
            (164, 255, 248, alpha),
            (spark_x, spark_y),
            (spark_x + round(math.cos(phase) * 3), spark_y + round(math.sin(phase) * 3)),
            width=2,
        )
    surface.blit(
        effect_surface,
        (left - margin, top - margin),
    )
