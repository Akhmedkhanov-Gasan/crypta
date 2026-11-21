import math
from functools import lru_cache

import pygame


_ANIMATIONS = {}
_PADDING = 18


@lru_cache(maxsize=12)
def _frame_effects(frame, accent, padding):
    mask = pygame.mask.from_surface(frame, 24)
    outline = mask.outline(2)
    size = (frame.get_width() + padding * 2, frame.get_height() + padding * 2)
    rim = pygame.Surface(size, pygame.SRCALPHA)
    color = tuple(min(255, round(channel * 0.75 + 65)) for channel in accent)
    points = [(x + padding, y + padding) for x, y in outline]
    if len(points) > 2:
        pygame.draw.lines(rim, (*color, 190), True, points, 2)
    glow = pygame.transform.gaussian_blur(rim, 7)
    shadow = pygame.Surface(size, pygame.SRCALPHA)
    silhouette = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
    mask.to_surface(silhouette, setcolor=(0, 0, 0, 190), unsetcolor=(0, 0, 0, 0))
    shadow.blit(silhouette, (padding, padding))
    shadow = pygame.transform.gaussian_blur(shadow, 5)
    return rim, glow, shadow, outline, color


def draw_selection_card(screen, card, frame, rectangle, accent, identity, hovered, pressed, render_scale=1.0):
    now = pygame.time.get_ticks()
    previous = _ANIMATIONS.get(identity, (now - 16, 0.0, 0.0))
    elapsed = max(0, min(40, now - previous[0]))
    hover, depression = previous[1:]
    if now - previous[0] > 250:
        hover, depression = 0.0, 0.0
    hover += (float(hovered) - hover) * (1.0 - math.exp(-elapsed / 85))
    depression += (float(pressed and hovered) - depression) * (1.0 - math.exp(-elapsed / 45))
    _ANIMATIONS[identity] = (now, hover, depression)
    image = card.copy()
    if depression > 0.01:
        shade = round(255 - depression * 25)
        image.fill((shade, shade, shade, 255), special_flags=pygame.BLEND_RGBA_MULT)
    offset = (0, round((depression * 4 - hover * 2) * render_scale))
    destination = rectangle.move(offset)
    padding = max(1, round(_PADDING * render_scale))
    rim, glow, shadow, outline, color = _frame_effects(frame, accent, padding)
    effect_rect = destination.inflate(padding * 2, padding * 2)
    shadow.set_alpha(round(180 - depression * 75))
    screen.blit(shadow, effect_rect.move(0, round((6 - depression * 4) * render_scale)))
    pulse = 0.88 + math.sin(now / 650) * 0.12
    glow.set_alpha(round(hover * (175 + depression * 65) * pulse))
    screen.blit(glow, effect_rect)
    screen.blit(image, destination)
    rim.set_alpha(round(hover * (100 + depression * 100)))
    screen.blit(rim, effect_rect)
    if hover > 0.05 and outline:
        sparks = pygame.Surface(effect_rect.size, pygame.SRCALPHA)
        for index in range(3):
            point_index = (now // 32 + index * len(outline) // 3) % len(outline)
            for trail in range(4):
                x, y = outline[(point_index - trail * 2) % len(outline)]
                point = (padding + x, padding + y)
                pygame.draw.circle(sparks, (*color, round(hover * (175 - trail * 38))), point, 1)
        screen.blit(sparks, effect_rect)
    return offset
