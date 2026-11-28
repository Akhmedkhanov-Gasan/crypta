from functools import lru_cache
import math

import pygame


@lru_cache(maxsize=16)
def _glow(size, color):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    for index in range(32, 0, -1):
        fraction = index / 32
        bounds = pygame.Rect(0, 0, max(1, round(size[0] * fraction)), max(1, round(size[1] * fraction)))
        bounds.center = size[0] // 2, size[1] // 2
        pygame.draw.ellipse(surface, (*color, round(140 * (1 - fraction) ** 2)), bounds)
    return surface


def _light(surface, center, size, strength, color):
    glow = _glow(size, color).copy()
    glow.set_alpha(round(255 * strength))
    surface.blit(glow, glow.get_rect(center=(round(center[0]), round(center[1]))))


def draw_ground_glow(surface, point, current_time, tile_size):
    size = tile_size * 2
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    center = tile_size, round(tile_size * 1.32)
    pulse = 0.7 + 0.3 * math.sin(current_time / 530)
    _light(layer, center, (round(tile_size * 1.65), round(tile_size * 0.7)), pulse, (172, 10, 30))
    ring = pygame.Rect(0, 0, round(tile_size * 1.18), round(tile_size * 0.4))
    ring.center = center
    angle = current_time / 2500
    for index in range(3):
        start = angle + index * math.tau / 3
        pygame.draw.arc(layer, (167, 23, 39, round(60 + 45 * pulse)), ring,
                        start, start + 0.85, max(1, round(tile_size / 64)))
    surface.blit(layer, (point[0] - tile_size // 2, point[1] - tile_size // 2))


def draw_foreground_effects(surface, point, current_time, tile_size):
    size = tile_size * 2
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    bowl = tile_size, tile_size * 0.94
    pulse = (math.sin(current_time / 460) + 1) / 2
    _light(layer, bowl, (round(tile_size * 0.76), round(tile_size * 0.3)),
           0.65 + 0.35 * pulse, (218, 13, 36))
    seal = tile_size, tile_size * 1.24
    _light(layer, seal, (round(tile_size * 0.38), round(tile_size * 0.44)),
           0.5 + 0.5 * pulse, (225, 14, 35))
    for index in range(2):
        progress = (current_time / 1800 + index * 0.5) % 1
        radius = tile_size * (0.06 + progress * 0.19)
        ring = pygame.Rect(0, 0, max(2, round(radius * 2)), max(2, round(radius * 0.47)))
        ring.center = round(bowl[0]), round(bowl[1])
        alpha = round(175 * math.sin(progress * math.pi))
        pygame.draw.arc(layer, (223, 34, 48, alpha), ring, 0.2, 2.7, max(1, round(tile_size / 64)))
    for index in range(5):
        progress = (current_time / 2700 + index * 0.2) % 1
        phase = current_time / 900 + index * 2.1
        x = bowl[0] + math.sin(phase) * tile_size * (0.07 + progress * 0.1)
        y = bowl[1] - progress * tile_size * 0.52
        width = round(tile_size * (0.21 + progress * 0.22))
        _light(layer, (x, y), (width, max(2, round(width * 0.6))),
               math.sin(progress * math.pi) * 0.48, (125, 16, 33))
    for index in range(9):
        progress = (current_time / (1900 + index * 110) + index * 0.173) % 1
        phase = current_time / 650 + index * 2.4
        x = bowl[0] + math.sin(index * 1.8) * tile_size * 0.26
        x += math.sin(phase) * tile_size * 0.035
        y = bowl[1] - progress * tile_size * (0.35 + index % 3 * 0.1)
        strength = math.sin(progress * math.pi)
        _light(layer, (x, y), (max(3, tile_size // 10),) * 2, strength * 0.8, (221, 23, 44))
        pygame.draw.circle(layer, (245, 62, 70, round(215 * strength)),
                           (round(x), round(y)), max(1, round(tile_size / 80)))
    surface.blit(layer, (point[0] - tile_size // 2, point[1] - tile_size // 2))
