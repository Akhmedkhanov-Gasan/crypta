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
    seed_phase = (
        identity_seed % 997
    ) / 997 * math.tau
    breath = (
        0.5
        + 0.5
        * math.sin(
            current_time / 920
            + seed_phase
        )
    )

    ground_rect = pygame.Rect(
        center_x - 29,
        center_y + 19,
        58,
        17,
    )
    pygame.draw.ellipse(
        effect_surface,
        (
            11,
            62,
            68,
            round(26 + breath * 18),
        ),
        ground_rect,
    )
    pygame.draw.ellipse(
        effect_surface,
        (
            52,
            187,
            184,
            round(54 + breath * 38),
        ),
        ground_rect,
        width=1,
    )

    ground_phase = (
        seed_phase
        + current_time / 4700
    )
    for arc_index in range(3):
        arc_rect = ground_rect.inflate(
            -arc_index * 9,
            -arc_index * 3,
        )
        arc_alpha = round(
            78
            + breath * 45
            - arc_index * 12
        )
        arc_start = (
            ground_phase
            + arc_index * 1.8
        )
        pygame.draw.arc(
            effect_surface,
            (
                91,
                229,
                218,
                arc_alpha,
            ),
            arc_rect,
            arc_start,
            arc_start + 0.9,
            width=2 if arc_index == 0 else 1,
        )
        pygame.draw.arc(
            effect_surface,
            (
                56,
                156,
                165,
                arc_alpha,
            ),
            arc_rect,
            arc_start + math.pi,
            arc_start + math.pi + 0.72,
            width=1,
        )

    orbit_specs = (
        (31, 23, 1.15, 0.0),
        (26, 19, 0.82, 2.1),
        (21, 16, 0.64, 4.0),
    )
    orbit_phase = (
        seed_phase
        + current_time / 5600
    )

    for (
        radius_x,
        radius_y,
        arc_length,
        phase_offset,
    ) in orbit_specs:
        orbit_rect = pygame.Rect(
            center_x - radius_x,
            center_y - radius_y,
            radius_x * 2,
            radius_y * 2,
        )
        start_angle = orbit_phase + phase_offset
        alpha = round(
            62
            + breath * 42
            + (31 - radius_x) * 2
        )
        pygame.draw.arc(
            effect_surface,
            (
                45,
                149,
                158,
                alpha // 2,
            ),
            orbit_rect.inflate(4, 4),
            start_angle - 0.08,
            start_angle + arc_length + 0.08,
            width=3,
        )
        pygame.draw.arc(
            effect_surface,
            (
                106,
                226,
                216,
                alpha,
            ),
            orbit_rect,
            start_angle,
            start_angle + arc_length,
            width=1,
        )
        pygame.draw.arc(
            effect_surface,
            (
                66,
                184,
                189,
                alpha,
            ),
            orbit_rect,
            start_angle + math.pi,
            start_angle + math.pi + arc_length * 0.72,
            width=1,
        )

    rune_phase = (
        seed_phase
        - current_time / 6900
    )
    for rune_index in range(3):
        angle = (
            rune_phase
            + rune_index * math.tau / 3
        )
        rune_x = (
            center_x
            + round(math.cos(angle) * 27)
        )
        rune_y = (
            center_y
            + round(math.sin(angle) * 19)
            + round(
                math.sin(
                    current_time / 780
                    + rune_index * 1.7
                )
                * 2
            )
        )
        rune_pulse = (
            0.5
            + 0.5
            * math.sin(
                current_time / 830
                + rune_index * 2.2
                + seed_phase
            )
        )
        rune_alpha = round(
            105 + rune_pulse * 75
        )
        pygame.draw.circle(
            effect_surface,
            (
                29,
                115,
                124,
                rune_alpha // 4,
            ),
            (rune_x, rune_y),
            7,
        )
        rune_rect = pygame.Rect(
            rune_x - 5,
            rune_y - 5,
            10,
            10,
        )
        pygame.draw.arc(
            effect_surface,
            (
                124,
                244,
                229,
                rune_alpha,
            ),
            rune_rect,
            angle + 0.35,
            angle + 4.45,
            width=2,
        )
        pygame.draw.circle(
            effect_surface,
            (
                190,
                255,
                244,
                min(255, rune_alpha + 45),
            ),
            (
                rune_x
                + round(math.cos(angle) * 4),
                rune_y
                + round(math.sin(angle) * 4),
            ),
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
