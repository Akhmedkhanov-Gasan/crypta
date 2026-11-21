import math
from functools import lru_cache

import pygame


def illuminated_art(source, strength):
    image = source.copy()
    light = source.copy()
    gain = round(78 * max(0, min(1, strength)))
    light.fill((gain, gain, gain, 255), special_flags=pygame.BLEND_RGBA_MULT)
    image.blit(light, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    return image


def blend_art(base, active, strength):
    weight = round(255 * max(0, min(1, strength)))
    image = base.copy()
    image.fill((255 - weight,) * 4, special_flags=pygame.BLEND_RGBA_MULT)
    light = active.copy()
    light.fill((weight,) * 4, special_flags=pygame.BLEND_RGBA_MULT)
    image.blit(light, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return image


def sample_subpixel_card(source, position):
    x, y = position
    left, top = math.floor(x), math.floor(y)
    width, height = source.get_width() // 4 - 4, source.get_height() // 4 - 4
    crop = pygame.Rect(
        8 - round((x - left) * 4), 8 - round((y - top) * 4),
        (width + 1) * 4, (height + 1) * 4,
    )
    image = pygame.transform.smoothscale(source.subsurface(crop), (width + 1, height + 1))
    return image, (left, top)


def draw_subpixel_card(screen, source, position, alpha, highlighted_source=None, highlight=0):
    image, point = sample_subpixel_card(source, position)
    if highlighted_source is not None and highlight > 0:
        lit, _ = sample_subpixel_card(highlighted_source, position)
        image = blend_art(image, lit, highlight)
    image.set_alpha(alpha)
    screen.blit(image, point)


@lru_cache(maxsize=1)
def _mist_puff():
    surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    for y in range(64):
        for x in range(64):
            distance = math.hypot((x - 31.5) / 32, (y - 31.5) / 32)
            alpha = round(40 * max(0, 1 - distance * distance) ** 3)
            surface.set_at((x, y), (140, 100, 172, alpha))
    return surface


def draw_card_mist(screen, bounds, strength, current_time, seed):
    if strength <= 0:
        return
    layer = pygame.Surface((bounds.width + 64, bounds.height + 64), pygame.SRCALPHA)
    for index in range(14):
        phase = current_time / 1500 + index * 2.4 + seed * 1.7
        x = 32 + bounds.width * (0.18 + 0.64 * ((index * 0.618) % 1))
        y = 32 + bounds.height * (0.12 + 0.76 * ((index * 0.382) % 1))
        x += math.sin(phase) * 15
        y += math.cos(phase * 0.8) * 13
        width = 112 + index % 4 * 8
        height = round(width * 0.68)
        puff = _scaled_puff(width, height)
        layer.blit(puff, puff.get_rect(center=(round(x), round(y))))
    layer.set_alpha(round(255 * strength))
    screen.blit(layer, (bounds.x - 32, bounds.y - 32))


@lru_cache(maxsize=8)
def _scaled_puff(width, height):
    return pygame.transform.smoothscale(_mist_puff(), (width, height))


@lru_cache(maxsize=1)
def _confirmation_glint():
    image = pygame.Surface((64, 64), pygame.SRCALPHA)
    for y in range(64):
        for x in range(64):
            radius = math.hypot((x - 31.5) / 32, (y - 31.5) / 32)
            alpha = round(110 * max(0, 1 - radius) ** 2)
            image.set_at((x, y), (247, 217, 158, alpha))
    return image


def draw_confirmation_light(screen, bounds, progress):
    strength = math.sin(math.pi * progress)
    if strength <= 0:
        return
    layer = pygame.Surface(bounds.size, pygame.SRCALPHA)
    size = max(1, round(bounds.width * 0.9))
    glow = pygame.transform.smoothscale(_confirmation_glint(), (size, size))
    glow.set_alpha(round(255 * strength))
    center = bounds.width // 2, round(bounds.height * 0.28)
    layer.blit(glow, glow.get_rect(center=center))
    for index in range(10):
        angle = index * math.tau / 10 + 0.3
        radius = bounds.width * (0.12 + 0.25 * progress)
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * radius * 0.65
        alpha = round(210 * strength)
        pygame.draw.circle(layer, (247, 223, 170, alpha), (round(x), round(y)),
                           max(1, round(bounds.width / 140)))
    screen.blit(layer, bounds)
