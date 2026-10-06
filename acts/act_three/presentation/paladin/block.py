import math

import pygame

from acts.act_three.presentation.player_motion import (
    assassin_hurt_direction,
    movement_frame_for_progress,
)


PALADIN_BLOCK_DURATION_MS = 320


def paladin_block_progress(player, current_time):
    started_at = player.impact_block_started_at
    elapsed = current_time - started_at

    if (
        player.subclass != "paladin"
        or player.health <= 0
        or started_at < 0
        or not 0 <= elapsed < PALADIN_BLOCK_DURATION_MS
    ):
        return None

    return elapsed / PALADIN_BLOCK_DURATION_MS


def paladin_block_frame(player, current_time):
    progress = paladin_block_progress(player, current_time)

    if progress is None:
        return None

    started_at = player.impact_block_started_at

    if (
        player.hit_animation_started_at >= started_at
        or player.dodge_animation_started_at >= started_at
        or player.attack_animation_started_at > started_at
        or player.movement_animation_started_at > started_at
    ):
        return None

    return movement_frame_for_progress(progress, 8)


def paladin_block_sprite(player, assets, current_time):
    frame = paladin_block_frame(player, current_time)

    if frame is None:
        return None

    direction = assassin_hurt_direction(
        player.impact_block_direction
    )
    return assets[
        f"player_paladin_block_{direction}_{frame}"
    ]


def draw_player_block_effect(
    surface,
    player,
    center,
    current_time,
    size,
    damage_font,
):
    if player.subclass != "paladin":
        from presentation.world import draw_impact_block_effect

        draw_impact_block_effect(
            surface,
            player,
            center,
            current_time,
            size,
        )
        return

    started_at = player.impact_block_started_at
    elapsed = current_time - started_at

    if (
        player.health <= 0
        or started_at < 0
        or not 0 <= elapsed < 800
    ):
        return

    if elapsed < 480:
        progress = elapsed / 480
        visibility = (1.0 - progress) ** 1.2
        flash = max(0.0, 1.0 - elapsed / 140)
        direction_x, direction_y = player.impact_block_direction

        effect = pygame.Surface(
            (size * 3, size * 3),
            pygame.SRCALPHA,
        )
        middle = size * 1.5
        cx = round(middle + direction_x * size * 0.32)
        cy = round(middle + direction_y * size * 0.32)
        radius = max(6, round(size * (0.25 + flash * 0.07)))
        alpha = round(255 * visibility)

        for scale, color, opacity in (
            (1.65, (40, 23, 57), 100),
            (1.30, (96, 65, 118), 110),
            (1.00, (180, 151, 91), 130),
        ):
            pygame.draw.circle(
                effect,
                (*color, round(opacity * visibility)),
                (cx, cy),
                max(1, round(radius * scale)),
            )

        ring_radius = round(size * (0.28 + progress * 0.42))
        pygame.draw.circle(
            effect,
            (189, 166, 118, round(190 * visibility)),
            (cx, cy),
            ring_radius,
            max(1, size // 32),
        )

        points = (
            (cx, cy - radius),
            (cx + radius, cy - radius // 2),
            (cx + radius * 3 // 4, cy + radius // 2),
            (cx, cy + radius),
            (cx - radius * 3 // 4, cy + radius // 2),
            (cx - radius, cy - radius // 2),
        )

        pygame.draw.polygon(
            effect,
            (34, 21, 46, round(195 * visibility)),
            points,
        )
        pygame.draw.polygon(
            effect,
            (154, 121, 163, alpha),
            points,
            max(3, size // 16),
        )
        pygame.draw.polygon(
            effect,
            (245, 227, 177, alpha),
            points,
            max(1, size // 40),
        )

        cross_length = round(radius * (0.55 + flash * 0.30))
        cross_color = (255, 243, 209, alpha)
        cross_width = max(1, size // 32)

        pygame.draw.line(
            effect,
            cross_color,
            (cx, cy - cross_length),
            (cx, cy + cross_length),
            cross_width,
        )
        pygame.draw.line(
            effect,
            cross_color,
            (cx - cross_length, cy),
            (cx + cross_length, cy),
            cross_width,
        )

        for index in range(12):
            angle = index * math.tau / 12
            speed = 0.35 + (index % 3) * 0.10
            distance = radius + size * speed * progress
            length = size * (0.07 + flash * 0.06) * visibility
            spark_x = cx + math.cos(angle) * distance
            spark_y = cy + math.sin(angle) * distance

            pygame.draw.line(
                effect,
                (250, 230, 176, alpha),
                (round(spark_x), round(spark_y)),
                (
                    round(spark_x + math.cos(angle) * length),
                    round(spark_y + math.sin(angle) * length),
                ),
                max(1, size // 32),
            )

        surface.blit(
            effect,
            (
                round(center[0] - middle),
                round(center[1] - middle),
            ),
        )

    text_progress = elapsed / 800
    text_alpha = round(
        255 * min(1.0, (1.0 - text_progress) / 0.4)
    )
    text_center = (
        round(center[0]),
        round(center[1] - size * 0.65 - size * 0.25 * text_progress),
    )

    label = damage_font.render(
        "BLOCKED",
        True,
        (255, 231, 173),
    )
    outline = damage_font.render(
        "BLOCKED",
        True,
        (20, 10, 28),
    )
    label.set_alpha(text_alpha)
    outline.set_alpha(text_alpha)
    text_rect = label.get_rect(center=text_center)

    for offset in (
        (-1, -1),
        (0, -1),
        (1, -1),
        (-1, 0),
        (1, 0),
        (-1, 1),
        (0, 1),
        (1, 1),
    ):
        surface.blit(outline, text_rect.move(*offset))

    surface.blit(label, text_rect)
