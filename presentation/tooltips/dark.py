from functools import lru_cache

import pygame

from presentation.tooltips.renderer import draw_tooltip as draw_shared_tooltip


@lru_cache(maxsize=64)
def _panel_background(size, scale, padding, title_height):
    panel = pygame.Surface(size, pygame.SRCALPHA)
    width, height = size
    stroke = max(1, round(scale))
    cut = min(max(2, round(4 * scale)), width // 2, height // 2)
    corners = (
        (cut, 0), (width - cut - 1, 0),
        (width - 1, cut), (width - 1, height - cut - 1),
        (width - cut - 1, height - 1), (cut, height - 1),
        (0, height - cut - 1), (0, cut),
    )
    pygame.draw.polygon(panel, (11, 11, 11, 255), corners)
    for y in range(cut, height - cut):
        light = round(7 * (1 - y / max(1, height - 1)))
        pygame.draw.line(
            panel, (13 + light, 13 + light, 13 + light, 255),
            (stroke, y), (width - stroke - 1, y),
        )
    pygame.draw.polygon(panel, (76, 76, 76, 255), corners, width=stroke)
    inset = stroke * 2
    inner = panel.get_rect().inflate(-inset * 2, -inset * 2)
    if inner.width > 0 and inner.height > 0:
        pygame.draw.rect(panel, (33, 33, 33, 255), inner, width=stroke, border_radius=cut)
    pygame.draw.line(
        panel, (110, 110, 110, 255),
        (cut + stroke, stroke), (width - cut - stroke - 1, stroke),
        width=stroke,
    )
    divider_y = padding + title_height + max(1, round(4 * scale))
    left, right = padding, width - padding - 1
    middle = (left + right) // 2
    radius = max(1, round(2 * scale))
    for x in range(left, right + 1):
        strength = 1 - abs(x - middle) / max(1, (right - left) / 2)
        light = round(24 * max(0, strength))
        pygame.draw.line(
            panel, (38 + light, 38 + light, 38 + light, 255),
            (x, divider_y), (x, divider_y + stroke - 1),
        )
    pygame.draw.polygon(panel, (104, 104, 104, 255), (
        (middle, divider_y - radius), (middle + radius, divider_y),
        (middle, divider_y + radius), (middle - radius, divider_y),
    ))
    return panel


def _draw_panel(panel, scale, padding, title_height):
    panel.blit(_panel_background(panel.get_size(), scale, padding, title_height), (0, 0))


def draw_tooltip(screen, content, anchor, *, scale=1.0, above=False, opacity=1.0):
    draw_shared_tooltip(
        screen, content, anchor,
        scale=scale,
        above=above,
        opacity=opacity,
        title_color=(216, 216, 216),
        body_color=(190, 190, 190),
        panel_renderer=_draw_panel,
    )
