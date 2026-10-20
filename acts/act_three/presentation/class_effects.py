import math

import pygame


from presentation.layout import ACT_THREE_TILE_SIZE


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
    margin = 18
    effect_surface = pygame.Surface(
        (
            ACT_THREE_TILE_SIZE + margin * 2,
            ACT_THREE_TILE_SIZE + margin * 2,
        ),
        pygame.SRCALPHA,
    )
    center_x = margin + ACT_THREE_TILE_SIZE // 2
    center_y = margin + ACT_THREE_TILE_SIZE // 2 - 3
    seed_offset = (
        identity_seed % 997
    ) / 997

    symbol_specs = (
        (-27, -17, 0, False, 0.00),
        (26, -8, 1, False, 0.19),
        (-24, 13, 2, False, 0.38),
        (24, 18, 3, False, 0.57),
        (2, -28, 3, False, 0.76),
        (-8, -6, 0, True, 0.31),
        (8, 7, 1, True, 0.68),
    )

    for (
        offset_x,
        offset_y,
        symbol_type,
        on_body,
        phase_offset,
    ) in symbol_specs:
        phase = (
            current_time / 3400
            + seed_offset
            + phase_offset
        ) % 1

        if phase >= 0.64:
            continue

        life = phase / 0.64
        visibility = math.sin(math.pi * life) ** 1.6
        drift_x = round(
            math.sin(
                life * math.pi * 2
                + phase_offset * math.tau
            )
            * 1.5
        )
        drift_y = -round(life * 5)

        symbol_x = (
            center_x
            + offset_x
            + drift_x
        )
        symbol_y = (
            center_y
            + offset_y
            + drift_y
        )
        size = 3 if on_body else 4
        maximum_alpha = 68 if on_body else 145
        alpha = round(maximum_alpha * visibility)

        pygame.draw.circle(
            effect_surface,
            (
                25,
                116,
                124,
                max(1, alpha // 6),
            ),
            (symbol_x, symbol_y),
            size + 3,
        )

        symbol_color = (
            111,
            229,
            219,
            alpha,
        )
        highlight_color = (
            188,
            255,
            243,
            min(255, alpha + 28),
        )

        if symbol_type == 0:
            eye_rect = pygame.Rect(
                symbol_x - size,
                symbol_y - 2,
                size * 2 + 1,
                5,
            )
            pygame.draw.arc(
                effect_surface,
                symbol_color,
                eye_rect,
                math.pi,
                math.tau,
                width=1,
            )
            pygame.draw.arc(
                effect_surface,
                symbol_color,
                eye_rect,
                0,
                math.pi,
                width=1,
            )
            pygame.draw.circle(
                effect_surface,
                highlight_color,
                (symbol_x, symbol_y),
                1,
            )

        elif symbol_type == 1:
            crescent_rect = pygame.Rect(
                symbol_x - size,
                symbol_y - size,
                size * 2 + 1,
                size * 2 + 1,
            )
            pygame.draw.arc(
                effect_surface,
                symbol_color,
                crescent_rect,
                0.55,
                5.35,
                width=1,
            )
            pygame.draw.circle(
                effect_surface,
                highlight_color,
                (
                    symbol_x + size - 1,
                    symbol_y - 1,
                ),
                1,
            )

        elif symbol_type == 2:
            rune_points = (
                (symbol_x, symbol_y - size),
                (symbol_x + size, symbol_y),
                (symbol_x, symbol_y + size),
                (symbol_x - size, symbol_y),
            )
            pygame.draw.lines(
                effect_surface,
                symbol_color,
                True,
                rune_points,
                width=1,
            )
            pygame.draw.circle(
                effect_surface,
                highlight_color,
                (symbol_x, symbol_y),
                1,
            )

        else:
            seal_rect = pygame.Rect(
                symbol_x - size,
                symbol_y - size,
                size * 2 + 1,
                size * 2 + 1,
            )
            pygame.draw.arc(
                effect_surface,
                symbol_color,
                seal_rect,
                0.15,
                2.25,
                width=1,
            )
            pygame.draw.arc(
                effect_surface,
                symbol_color,
                seal_rect,
                3.35,
                5.65,
                width=1,
            )
            pygame.draw.circle(
                effect_surface,
                highlight_color,
                (symbol_x, symbol_y),
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
