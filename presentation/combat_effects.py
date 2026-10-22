import pygame


def draw_impact_block_effect(
    screen,
    player,
    center,
    current_time,
    size,
):
    elapsed = current_time - player.impact_block_started_at
    if (
        player.health <= 0
        or player.impact_block_started_at < 0
        or not 0 <= elapsed < 480
    ):
        return

    progress = elapsed / 480
    alpha = round(255 * (1 - progress))
    effect = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    radius = max(6, round(size * (0.38 + progress * 0.12)))
    cx = cy = size
    points = (
        (cx - radius, cy - radius),
        (cx, cy - radius - radius // 3),
        (cx + radius, cy - radius),
        (cx + radius, cy),
        (cx + radius // 2, cy + radius),
        (cx, cy + radius + radius // 3),
        (cx - radius // 2, cy + radius),
        (cx - radius, cy),
    )

    pygame.draw.polygon(effect, (80, 130, 185, alpha // 2), points)
    pygame.draw.polygon(
        effect,
        (225, 238, 255, alpha),
        points,
        width=max(1, size // 16),
    )
    pygame.draw.line(
        effect,
        (255, 210, 110, alpha),
        (cx, cy - radius),
        (cx, cy + radius),
        width=max(1, size // 16),
    )
    screen.blit(
        effect,
        (round(center[0] - size), round(center[1] - size)),
    )
