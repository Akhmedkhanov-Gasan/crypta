import math

import pygame


def ease(value):
    value = max(0, min(1, value))
    return value * value * (3 - 2 * value)


def envelope(elapsed, duration):
    return max(0, min(1, elapsed / 300, (duration - elapsed) / 650))


def relief(surface, points, fill, edge, strength, width=2):
    alpha = round(255 * max(0, min(1, strength)))
    pygame.draw.polygon(surface, (*fill, alpha), points)
    pygame.draw.lines(surface, (*edge, round(alpha * .8)), True, points, width)


def ribbon(surface, points, width, color, alpha):
    upper = []
    lower = []
    for index, (x, y) in enumerate(points):
        thickness = width * math.sin(index / (len(points) - 1) * math.pi)
        upper.append((x, y - thickness))
        lower.append((x, y + thickness))
    pygame.draw.polygon(surface, (*color, round(alpha)), upper + list(reversed(lower)))
