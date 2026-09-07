import math
from functools import lru_cache

import pygame
import resource_store as resources

from presentation.layout import FONT_ROOT


@lru_cache(maxsize=1)
def _skip_fonts():
    path = str(FONT_ROOT / "Almendra-Bold.ttf")
    return (
        resources.load_font(path, 15),
        resources.load_font(path, 21),
    )


def draw_cutscene_skip(screen, controller, current_time):
    if not controller.is_visible(current_time):
        return

    key_font, text_font = _skip_fonts()
    panel = pygame.Surface((270, 64), pygame.SRCALPHA)

    pygame.draw.rect(
        panel,
        (10, 8, 13, 220),
        panel.get_rect(),
        border_radius=16,
    )

    center = (36, 32)
    radius = 25
    color = (226, 202, 150)

    pygame.draw.circle(
        panel,
        (76, 68, 64),
        center,
        radius,
        width=3,
    )

    if controller.holding:
        start = -math.pi / 2
        sweep = math.tau * controller.progress
    else:
        start = current_time / 650
        sweep = math.pi / 2

    if sweep > 0:
        segments = max(2, round(80 * sweep / math.tau))
        points = [
            (
                round(center[0] + math.cos(
                    start + sweep * index / segments
                ) * radius),
                round(center[1] + math.sin(
                    start + sweep * index / segments
                ) * radius),
            )
            for index in range(segments + 1)
        ]
        pygame.draw.lines(panel, color, False, points, 3)

    key_text = key_font.render("SPACE", True, (255, 255, 255))
    panel.blit(key_text, key_text.get_rect(center=center))

    label = text_font.render("Hold to skip", True, (255, 255, 255))
    panel.blit(label, label.get_rect(midleft=(76, 32)))

    screen.blit(
        panel,
        panel.get_rect(
            bottomright=(
                screen.get_width() - 24,
                screen.get_height() - 12,
            ),
        ),
    )
