import math

import pygame


def _ellipse(surface, color, center, radius_x, radius_y, width=0):
    radius_x = max(1, round(radius_x))
    radius_y = max(1, round(radius_y))
    pygame.draw.ellipse(
        surface,
        color,
        (round(center[0]) - radius_x, round(center[1]) - radius_y, radius_x * 2, radius_y * 2),
        width,
    )


def _crystal(surface, color, center, angle, length, width):
    x, y = center
    dx, dy = math.cos(angle), math.sin(angle)
    pygame.draw.polygon(
        surface,
        color,
        (
            (round(x + dx * length), round(y + dy * length)),
            (round(x - dy * width), round(y + dx * width)),
            (round(x - dx * length * 0.65), round(y - dy * length * 0.65)),
            (round(x + dy * width), round(y - dx * width)),
        ),
    )


def draw_burst_charge(surface, center, size, progress, primary, highlight):
    fade = math.sin(math.pi * progress)
    for index in range(5):
        angle = index * math.tau / 5 + progress * 3
        radius = size * (0.31 - progress * 0.24)
        point = (
            center[0] + math.cos(angle) * radius,
            center[1] + math.sin(angle) * radius * 0.5,
        )
        _ellipse(surface, (*primary, round(95 * fade)), point, 6, 4)
        _crystal(surface, (*highlight, round(210 * fade)), point, angle, 4, 2)


def draw_warlock_burst(surface, center, size, progress, primary, highlight, seed):
    x, y = center
    expansion = 1 - (1 - progress) ** 2
    fade = (1 - progress) ** 1.25
    ground = (x, y + size * 0.16)
    radius = size * (0.13 + 0.43 * expansion)
    _ellipse(surface, (21, 8, 30, round(205 * fade)), ground, radius, radius * 0.49)
    _ellipse(surface, (*primary, round(190 * fade)), ground, radius, radius * 0.49, 2)

    for index in range(9):
        angle = seed + index * math.tau / 9
        distance = size * (0.06 + expansion * (0.19 + index % 3 * 0.04))
        puff = (
            x + math.cos(angle) * distance,
            y + math.sin(angle) * distance * 0.52 - size * progress * (0.23 + index % 4 * 0.07),
        )
        puff_radius = size * (0.065 + 0.09 * expansion) * (0.75 + index % 3 * 0.15)
        _ellipse(surface, (28, 11, 40, round(195 * fade)), puff, puff_radius, puff_radius * 0.84)
        _ellipse(
            surface, (*primary, round(92 * fade)),
            (puff[0], puff[1] - puff_radius * 0.24), puff_radius * 0.65, puff_radius * 0.42,
        )

    flash = max(0.0, 1 - progress / 0.32)
    if flash > 0:
        core = (x, y - size * 0.06)
        _ellipse(surface, (*primary, round(190 * flash)), core, size * 0.26, size * 0.24)
        _crystal(surface, (*highlight, round(245 * flash)), core, math.pi / 2, size * 0.20, size * 0.10)

    for index in range(11):
        angle = seed + index * 2.39996
        distance = size * expansion * (0.27 + index % 5 * 0.065)
        shard = (
            x + math.cos(angle) * distance,
            y + math.sin(angle) * distance * 0.48 - size * math.sin(progress * math.pi) * 0.27,
        )
        length = size * (0.05 + index % 3 * 0.02) * fade
        _crystal(surface, (*highlight, round(230 * fade)), shard, angle, length, length * 0.33)


def draw_summoner_burst(surface, center, size, progress, primary, highlight, seed):
    x, y = center
    bloom = 1 - (1 - progress) ** 2
    fade = (1 - progress) ** 0.85
    radius = size * (0.14 + bloom * 0.40)
    ground = (x, y + size * 0.16)
    _ellipse(surface, (*primary, round(67 * fade)), ground, radius, radius * 0.50)
    _ellipse(surface, (*highlight, round(152 * fade)), ground, radius, radius * 0.50, 2)

    for index in range(7):
        angle = seed + index * math.tau / 7 + progress * 3.7
        petal = (
            x + math.cos(angle) * radius * 0.72,
            y + math.sin(angle) * radius * 0.46 - size * progress * 0.39,
        )
        length = size * (0.075 + bloom * 0.065) * fade
        _ellipse(surface, (*primary, round(86 * fade)), petal, length * 1.28, length)
        _crystal(surface, (*highlight, round(207 * fade)), petal, angle, length, length * 0.40)

    for index in range(12):
        angle = seed + index * 2.39996 - progress * (2.4 + index % 3 * 0.6)
        orbit = radius * (0.38 + index % 5 * 0.15)
        mote = (
            x + math.cos(angle) * orbit,
            y + math.sin(angle) * orbit * 0.47 - size * progress * (0.23 + index % 4 * 0.14),
        )
        _ellipse(surface, (*highlight, round(216 * fade)), mote, 1 + index % 2, 1 + index % 2)

    flash = max(0.0, 1 - progress / 0.45)
    if flash > 0:
        core = (x, y - size * (0.05 + progress * 0.33))
        _ellipse(surface, (*primary, round(131 * flash)), core, size * 0.19, size * 0.21)
        _crystal(surface, (*highlight, round(240 * flash)), core, math.pi / 2, size * 0.17, size * 0.075)
