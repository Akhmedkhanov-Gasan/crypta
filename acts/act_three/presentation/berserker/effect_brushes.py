from functools import lru_cache
import math

import pygame
import pygame.gfxdraw


BLOOD = ((39, 17, 25), (131, 34, 43), (241, 165, 122))
ASH = ((40, 34, 30), (125, 96, 63), (236, 213, 161))


def envelope(phase):
    return max(0.0, math.sin(math.pi * min(1.0, max(0.0, phase))))


@lru_cache(maxsize=96)
def _smoke_brush(radius, color):
    size = radius * 2 + 1
    brush = pygame.Surface((size, size), pygame.SRCALPHA)
    for y in range(size):
        for x in range(size):
            nx, ny = (x - radius) / radius, (y - radius) / radius
            distance = math.hypot(nx, ny)
            if distance >= 1:
                continue
            grain = (math.sin(nx * 11 + ny * 5) * math.cos(ny * 13 - nx * 4) + 1) * 0.5
            density = (1 - distance) ** 1.7 * (0.5 + grain * 0.5)
            brush.set_at((x, y), (*color, round(205 * density)))
    return brush


def mist(layer, position, radius, color, opacity):
    radius = max(2, min(36, round(radius)))
    brush = _smoke_brush(radius, color)
    brush.set_alpha(round(max(0, min(1, opacity)) * 255))
    layer.blit(brush, (round(position[0] - radius), round(position[1] - radius)))


def polygon(layer, points, color):
    points = [(round(x), round(y)) for x, y in points]
    if len(set(points)) < 3:
        return
    pygame.gfxdraw.filled_polygon(layer, points, color)
    pygame.gfxdraw.aapolygon(layer, points, color)


def spark(layer, position, velocity, color, opacity, length=4):
    x, y = position
    alpha = round(255 * max(0, min(1, opacity)))
    mist(layer, position, 5, color, opacity * 0.38)
    end = round(x - velocity[0] * length), round(y - velocity[1] * length)
    pygame.draw.line(layer, (*color, alpha), (round(x), round(y)), end, 1)
    pygame.draw.circle(layer, (249, 215, 175, round(alpha * 0.8)), (round(x), round(y)), 1)


def crescent(layer, center, radius, angle, span, width, opacity, palette=BLOOD, flatten=0.55):
    if opacity <= 0:
        return
    outer, inner, edge = [], [], []
    for index in range(33):
        t = index / 32
        theta = angle - (1 - t) * span
        taper = math.sin(math.pi * t) ** 0.7 * width * (0.3 + t)
        r = radius + math.sin(t * math.pi) * width * 0.14
        outer.append((center[0] + math.cos(theta) * r, center[1] + math.sin(theta) * r * flatten))
        inner.append((center[0] + math.cos(theta) * (r - taper),
                      center[1] + math.sin(theta) * (r - taper) * flatten))
        edge.append((center[0] + math.cos(theta) * (r - taper * 0.22),
                     center[1] + math.sin(theta) * (r - taper * 0.22) * flatten))
    polygon(layer, outer + list(reversed(inner)), (*palette[1], round(165 * opacity)))
    polygon(layer, outer[11:] + list(reversed(edge[11:])), (*palette[2], round(210 * opacity)))
    for index in range(10, 31):
        alpha = round(205 * opacity * (index / 32) ** 1.5)
        pygame.draw.aaline(layer, (*palette[2], alpha), outer[index], outer[index + 1])
    tip = outer[-3]
    mist(layer, tip, 8, palette[1], opacity * 0.5)


def draw_storm(layer, center, tile, time, strength, palette=BLOOD, stored=0.0):
    for side in (-1, 1):
        for stream in range(3):
            phase = time / 1050 + stream * 2.1 + side * 0.6
            height = tile * (0.57 + stream * 0.13 + math.sin(phase) * 0.09)
            base_x = center[0] + side * tile * (0.23 + stream * 0.075)
            left, right, core = [], [], []
            for index in range(25):
                t = index / 24
                sway = math.sin(t * 5.5 - phase * 2) * tile * 0.06 * t
                x = base_x + side * tile * 0.12 * t + sway
                y = center[1] - height * t
                width = tile * 0.075 * math.sin(math.pi * t) ** 0.7 * (1 - t * 0.65)
                left.append((x - width, y))
                right.append((x + width, y))
                core.append((x + side * width * 0.32, y))
            opacity = strength * (0.55 + 0.12 * math.sin(phase + stream))
            polygon(layer, left + list(reversed(right)), (*palette[1], round(145 * opacity)))
            polygon(layer, core[6:] + list(reversed(right[6:])), (*palette[2], round(76 * opacity)))
            mist(layer, (base_x, center[1] - height * 0.3), tile * 0.27, palette[1], strength * 0.65)
        for index in range(9):
            phase = (time / (1500 + index * 67) + index * 0.173) % 1
            fade = envelope(phase) ** 1.4 * strength
            x = center[0] + side * tile * (0.28 + phase * 0.14)
            x += math.sin(phase * 6 + index * 1.7 + time / 1300) * tile * 0.07
            y = center[1] - phase * tile * (0.9 + index % 3 * 0.1)
            mist(layer, (x, y), tile * (0.16 + phase * 0.1), palette[0], fade * 0.85)
            mist(layer, (x + side * 2, y + 4), tile * 0.18, palette[1], fade * 0.8)
        for index in range(3):
            phase = (time / 1300 + index / 3 + (side + 1) * 0.11) % 1
            x = center[0] + side * tile * (0.3 + 0.15 * phase)
            y = center[1] - phase * tile * 0.95
            drift = math.sin(phase * 6 + index) * 3
            spark(layer, (x + drift, y), (side * 0.17, -0.8), palette[2],
                  envelope(phase) * strength * (0.45 + stored * 0.3), 2)
    for index in range(5):
        theta = index * 2.4 + time / 3900
        x = center[0] + math.cos(theta) * tile * 0.35
        y = center[1] + math.sin(theta) * tile * 0.09
        mist(layer, (x, y), tile * 0.25, palette[1], strength * 0.12)


def shock_dust(layer, center, tile, phase, opacity, palette=BLOOD):
    for index in range(19):
        angle = index * 2.399
        distance = tile * (0.35 + phase * (0.5 + index % 4 * 0.1))
        x = center[0] + math.cos(angle) * distance
        y = center[1] + math.sin(angle) * distance * 0.46
        mist(layer, (x, y), 9 + index % 4 * 2, palette[0], opacity * 0.48)
        if index % 3 == 0:
            spark(layer, (x, y - envelope(phase) * 8), (math.cos(angle), math.sin(angle) * 0.6),
                  palette[2], opacity * 0.65, 2)
