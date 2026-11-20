import math

import pygame


def draw_arrow_flight(surface, origin, destination, progress, *, phantom=False, power=1.0):
    progress = max(0.0, min(1.0, progress))
    dx, dy = destination[0] - origin[0], destination[1] - origin[1]
    distance = math.hypot(dx, dy)
    if distance < 1:
        return
    ux, uy = dx / distance, dy / distance
    nx, ny = -uy, ux
    head = (origin[0] + dx * progress, origin[1] + dy * progress)
    size = 1.0 + (power - 1.0) * 0.25
    pad = round(65 * size)
    layer = pygame.Surface((pad * 2, pad * 2), pygame.SRCALPHA)

    def point(back, side=0):
        return (round(pad - ux * back * size + nx * side * size), round(pad - uy * back * size + ny * side * size))

    metal = (179, 201, 214) if phantom else (216, 207, 181)
    edge = (223, 233, 239) if phantom else (245, 237, 210)
    shaft = (89, 115, 132) if phantom else (108, 91, 76)
    feather = (91, 111, 143) if phantom else (62, 57, 70)
    opacity = 205 if phantom else 245
    for index in range(15):
        back = 19 + index * 2.4
        side = math.sin(index * 0.48 + progress * 5) * (0.6 + index * 0.18)
        alpha = round((1 - index / 15) ** 2 * (85 if phantom else 38) * power)
        pygame.draw.circle(layer, (*metal, min(150, alpha)), point(back, side), 1 if index > 5 else 2)
    pygame.draw.line(layer, (10, 12, 18, opacity), point(24), point(-9), 4)
    pygame.draw.line(layer, (*shaft, opacity), point(23), point(-4), 2)
    pygame.draw.line(layer, (*metal, opacity), point(16, -0.6), point(-4, -0.6), 1)
    tip = (point(-12), point(-1, 3.5), point(3), point(-1, -3.5))
    pygame.draw.polygon(layer, (*metal, opacity), tip)
    pygame.draw.line(layer, (*edge, opacity), point(-12), point(1), 1)
    pygame.draw.line(layer, (42, 49, 59, opacity), point(-1, 3.5), point(3), 1)
    for sign in (-1, 1):
        pygame.draw.polygon(layer, (*feather, opacity), (
            point(16), point(22, sign * 4), point(29, sign * 4.5), point(24),
        ))
        pygame.draw.line(layer, (*metal, round(opacity * 0.7)), point(18), point(27, sign * 3), 1)
    if power > 1:
        for sign in (-1, 1):
            points = [point(12 + index * 3, sign * (3 + math.sin(index * 0.55) * 2)) for index in range(10)]
            pygame.draw.lines(layer, (*metal, 85), False, points, 1)
    surface.blit(layer, (round(head[0]) - pad, round(head[1]) - pad))


def draw_arrow_impact(surface, center, progress, *, phantom=False):
    progress = max(0.0, min(1.0, progress))
    layer = pygame.Surface((80, 80), pygame.SRCALPHA)
    color = (176, 198, 220) if phantom else (219, 206, 172)
    for index in range(7):
        angle = index * 2.399
        distance = 3 + progress * (11 + index % 3 * 4)
        start = (round(40 + math.cos(angle) * distance), round(40 + math.sin(angle) * distance * 0.65))
        end = (round(start[0] + math.cos(angle) * (3 - progress * 2)), round(start[1] + math.sin(angle) * (3 - progress * 2)))
        pygame.draw.line(layer, (*color, round(210 * (1 - progress))), start, end, 1)
    surface.blit(layer, (round(center[0]) - 40, round(center[1]) - 40))
