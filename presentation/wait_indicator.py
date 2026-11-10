import math

import pygame


WAIT_EFFECT_DURATION_MS = 900


def draw_wait_indicator(surface, center_x, top, current_time, started_at):
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < WAIT_EFFECT_DURATION_MS:
        return

    progress = elapsed / WAIT_EFFECT_DURATION_MS
    fade = min(1.0, elapsed / 100) * min(1.0, (1 - progress) / 0.22)
    effect = pygame.Surface((34, 22), pygame.SRCALPHA)
    for dot_index in range(3):
        dot_phase = max(0.0, min(1.0, (elapsed - dot_index * 90) / 310))
        lift = round(math.sin(dot_phase * math.pi) * 4)
        center = (9 + dot_index * 8, 14 - lift)
        pygame.draw.circle(
            effect,
            (16, 13, 18, round(190 * fade)),
            (center[0] + 1, center[1] + 1),
            3,
        )
        pygame.draw.circle(
            effect,
            (220, 210, 190, round(245 * fade)),
            center,
            2,
        )

    surface.blit(effect, (center_x - effect.get_width() // 2, top))
