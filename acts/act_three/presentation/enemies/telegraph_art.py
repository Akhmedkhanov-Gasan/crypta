from functools import lru_cache
import math

import pygame


_SCALE = 3
_PALETTES = {
    "goblin": (190, 112, 115),
    "brute": (139, 48, 52),
    "archer": (55, 104, 65),
    "sentinel": (100, 104, 109),
    "priest": (151, 186, 145),
    "priest_ghost": (128, 183, 48),
}


def _polygon(surface, color, points):
    pygame.draw.polygon(surface, color, [
        (round(x * _SCALE), round(y * _SCALE)) for x, y in points
    ])


def _disc(surface, color, center, radius):
    pygame.draw.circle(
        surface,
        color,
        (round(center[0] * _SCALE), round(center[1] * _SCALE)),
        max(1, round(radius * _SCALE)),
    )


def _bezier(points, progress):
    start, first, second, end = (pygame.Vector2(point) for point in points)
    remaining = 1 - progress
    return (
        start * remaining ** 3
        + first * (3 * remaining ** 2 * progress)
        + second * (3 * remaining * progress ** 2)
        + end * progress ** 3
    )


def _ribbon(surface, points, color, width, taper=True):
    centers = [_bezier(points, index / 32) for index in range(33)]
    left = []
    right = []
    for index, center in enumerate(centers):
        tangent = centers[min(32, index + 1)] - centers[max(0, index - 1)]
        if tangent.length_squared() == 0:
            continue
        tangent = tangent.normalize()
        normal = pygame.Vector2(-tangent.y, tangent.x)
        strength = math.sin(math.pi * index / 32) ** 0.7 if taper else 1
        offset = normal * max(0.04, width * strength / 2)
        left.append(center + offset)
        right.append(center - offset)
    if len(left) > 1:
        _polygon(surface, color, left + right[::-1])


def _crescent(surface, center, radius, start, sweep, color, width, squash=0.86):
    outer = []
    inner = []
    for index in range(49):
        progress = index / 48
        angle = start + progress * sweep
        thickness = width * math.sin(progress * math.pi) ** 0.7
        for points, distance in ((outer, radius + thickness / 2), (inner, radius - thickness / 2)):
            points.append((
                center[0] + math.cos(angle) * distance,
                center[1] + math.sin(angle) * distance * squash,
            ))
    _polygon(surface, color, outer + inner[::-1])


def _finish(surface, size):
    return pygame.transform.smoothscale(surface, (size, size))


@lru_cache(maxsize=8)
def ground_marker(size, strength):
    surface = pygame.Surface((size * _SCALE, size * _SCALE), pygame.SRCALPHA)
    center = (size / 2, size / 2)
    for layer in range(18):
        radius = size * (0.49 - layer * 0.013)
        opacity = round(5 + layer * 2 + min(strength, 4) * 3)
        points = []
        for index in range(96):
            angle = index * math.tau / 96
            x = math.cos(angle)
            y = math.sin(angle)
            points.append((
                center[0] + math.copysign(abs(x) ** 0.72, x) * radius,
                center[1] + math.copysign(abs(y) ** 0.72, y) * radius,
            ))
        _polygon(surface, (14, 13, 17, opacity), points)
    return _finish(surface, size)


def _claws(surface, center, radius, color, glow):
    x, y = center
    for index in range(3):
        offset = (index - 1) * radius * 0.5
        points = (
            (x + offset - radius * 0.35, y + radius * 0.8),
            (x + offset - radius * 0.65, y + radius * 0.1),
            (x + offset - radius * 0.15, y - radius * 0.65),
            (x + offset + radius * 0.45, y - radius * (0.7 - abs(index - 1) * 0.15)),
        )
        _ribbon(surface, points, glow, radius * 0.24)
        _ribbon(surface, points, color, radius * 0.15)


def _impact(surface, center, radius, color, glow):
    x, y = center
    for index in range(5):
        angle = index * math.tau / 5 + 0.15
        _crescent(surface, center, radius * 0.88, angle, 0.94, glow, radius * 0.32)
        _crescent(surface, center, radius * 0.88, angle + 0.08, 0.78, color, radius * 0.11)
        direction = pygame.Vector2(math.cos(angle + 0.46), math.sin(angle + 0.46) * 0.86)
        side = pygame.Vector2(-direction.y, direction.x)
        origin = pygame.Vector2(x, y)
        _ribbon(surface, (
            origin + direction * radius * 0.13,
            origin + direction * radius * 0.5 + side * radius * 0.1,
            origin + direction * radius * 0.55 - side * radius * 0.13,
            origin + direction * radius * 0.74,
        ), color, radius * 0.09)
    _disc(surface, glow, center, radius * 0.2)


def _shield(surface, center, radius, color, glow, counter):
    x, y = center
    left = ((x, y - radius * 0.64), (x - radius * 1.05, y - radius * 1.04),
            (x - radius * 0.9, y + radius * 0.28), (x, y + radius * 0.94))
    right = tuple((2 * x - point[0], point[1]) for point in left)
    silhouette = [_bezier(left, index / 32) for index in range(33)]
    silhouette += [_bezier(right, index / 32) for index in range(32, -1, -1)]
    _polygon(surface, (34, 35, 37, 130), silhouette)
    for points in (left, right):
        _ribbon(surface, points, glow, radius * 0.24)
        _ribbon(surface, points, color, radius * 0.09, False)
    _ribbon(surface, ((x, y - radius * 0.45), (x - radius * 0.13, y),
                     (x + radius * 0.13, y + radius * 0.2), (x, y + radius * 0.58)),
            color, radius * 0.11)
    if counter:
        _crescent(surface, center, radius * 1.12, 0.2, 2.7, color, radius * 0.1)


def _seal(surface, center, radius, color, glow, phase):
    x, y = center
    for index in range(3):
        angle = index * math.tau / 3 - math.pi / 2
        _crescent(surface, center, radius * 0.91, angle + 0.2, 1.7, glow, radius * 0.19)
        _crescent(surface, center, radius * 0.91, angle + 0.28, 1.54, color, radius * 0.065)
        bead = (x + math.cos(angle) * radius * 0.91, y + math.sin(angle) * radius * 0.78)
        _disc(surface, glow, bead, radius * 0.13)
        _disc(surface, color, bead, radius * 0.055)
    for side in (-1, 1):
        _ribbon(surface, ((x, y - radius * 0.7), (x + side * radius * 0.78, y - radius * 0.1),
                         (x + side * radius * 0.32, y + radius * 0.25), (x, y + radius * 0.64)),
                color, radius * 0.11)
    _disc(surface, (*color[:3], round(125 + phase * 60)), center, radius * 0.1)


@lru_cache(maxsize=384)
def sigil_marker(size, enemy_type, mode, frame, lane):
    surface = pygame.Surface((size * _SCALE, size * _SCALE), pygame.SRCALPHA)
    rgb = _PALETTES.get(enemy_type, (177, 144, 126))
    phase = 0.5 + 0.5 * math.sin(frame * math.tau / 32)
    color = (*rgb, round(190 + phase * 35))
    glow = (*rgb, round(30 + phase * 14))
    radius = size * (0.31 - min(lane, 4) * 0.035)
    center = (size / 2, size / 2)
    if enemy_type == "goblin":
        _claws(surface, center, radius, color, glow)
    elif enemy_type == "brute":
        _impact(surface, center, radius, color, glow)
    elif enemy_type == "sentinel":
        _shield(surface, center, radius, color, glow, mode == "shield_counter")
    elif enemy_type == "archer":
        for angle in (0.15, math.pi + 0.15):
            _crescent(surface, center, radius, angle, 2.18, glow, radius * 0.27)
            _crescent(surface, center, radius, angle + 0.08, 2.02, color, radius * 0.09)
        if mode == "ranged":
            _disc(surface, glow, center, radius * 0.24)
            _disc(surface, color, center, radius * 0.075)
    elif enemy_type == "priest_ghost":
        for index in range(3):
            angle = index * math.tau / 3 + math.sin(frame * math.tau / 32) * 0.16
            _crescent(surface, center, radius * (0.7 + index * 0.12), angle, 2.3, glow, radius * 0.3)
            _crescent(surface, center, radius * (0.7 + index * 0.12), angle + 0.1, 2.1, color, radius * 0.12)
    else:
        _seal(surface, center, radius, color, glow, phase)
    return _finish(surface, size)


@lru_cache(maxsize=192)
def direction_marker(tile_size, enemy_type, frame, emphasis=False):
    size = tile_size * 2
    surface = pygame.Surface((size * _SCALE, size * _SCALE), pygame.SRCALPHA)
    rgb = _PALETTES.get(enemy_type, (177, 144, 126))
    pulse = 0.5 + 0.5 * math.sin(frame * math.tau / 32)
    x = size / 2
    y = size / 2 - tile_size * ((0.25 if emphasis else 0.49) + pulse * 0.015)
    reach = tile_size * (0.42 if emphasis else 0.25)
    left = ((x, y + reach * 0.42), (x - reach * 0.2, y - reach * 0.2),
            (x - reach * 0.65, y - reach * 0.55), (x - reach * 0.8, y - reach * 0.66))
    right = tuple((2 * x - point[0], point[1]) for point in left)
    silhouette = [_bezier(left, index / 24) for index in range(25)]
    silhouette.append(pygame.Vector2(x, y - reach * 0.22))
    silhouette += [_bezier(right, index / 24) for index in range(24, -1, -1)]
    _polygon(surface, (9, 10, 13, 235), [(x + (p.x - x) * 1.2, y + (p.y - y) * 1.2) for p in silhouette])
    _polygon(surface, (*rgb, round(210 + pulse * 35)), silhouette)
    for points in (left, right):
        _ribbon(surface, points, (*(min(220, channel + 38) for channel in rgb), 150), tile_size * 0.015)
    _crescent(surface, (x, y - reach * 0.17), reach * 0.67, math.pi * 1.08, math.pi * 0.84,
              (*rgb, 65), tile_size * 0.022)
    return _finish(surface, size)


@lru_cache(maxsize=384)
def threat_band(size, enemy_type, frame, radius_step, angle_step):
    surface = pygame.Surface((size * _SCALE, size * _SCALE), pygame.SRCALPHA)
    rgb = _PALETTES.get(enemy_type, (177, 144, 126))
    pulse = 0.5 + 0.5 * math.sin(frame * math.tau / 32)
    center = (size / 2, size / 2)
    radius = size * radius_step / 500
    angle = angle_step * math.tau / 96
    for width, color in (
        (size * 0.085, (*rgb, 19)),
        (size * 0.042, (7, 8, 12, 220)),
        (size * 0.021, (*rgb, round(177 + pulse * 35))),
    ):
        _crescent(surface, center, radius, angle - 2.65, 5.3, color, width, 1)
    _crescent(surface, center, radius - size * 0.033, angle - 1.1, 2.2,
              (*rgb, 47), size * 0.012, 1)
    return _finish(surface, size)


@lru_cache(maxsize=192)
def attacker_badge(size, enemy_type, mode, frame):
    surface = pygame.Surface((size * _SCALE, size * _SCALE), pygame.SRCALPHA)
    rgb = _PALETTES.get(enemy_type, (177, 144, 126))
    center = (size / 2, size / 2)
    _disc(surface, (*rgb, 26), center, size * 0.49)
    _disc(surface, (9, 11, 15, 240), center, size * 0.43)
    _crescent(surface, center, size * 0.44, -2.6, 5.2, (*rgb, 145), size * 0.025, 1)
    badge = _finish(surface, size)
    glyph = sigil_marker(size * 2, enemy_type, mode, frame, 0)
    crop_size = round(size * 1.4)
    cropped = glyph.subsurface(glyph.get_rect().inflate(crop_size - size * 2, crop_size - size * 2))
    glyph = pygame.transform.smoothscale(cropped, (round(size * 0.8), round(size * 0.8)))
    badge.blit(glyph, glyph.get_rect(center=(size // 2, size // 2)))
    return badge


@lru_cache(maxsize=32)
def shield_bash_sweep(tile_size, frame):
    size = tile_size * 2
    surface = pygame.Surface((size * _SCALE, size * _SCALE), pygame.SRCALPHA)
    rgb = _PALETTES["sentinel"]
    pulse = 0.5 + 0.5 * math.sin(frame * math.tau / 32)
    x = size / 2
    y = size / 2
    left = ((x - tile_size * 0.1, y - tile_size * 0.42),
            (x - tile_size * 0.42, y - tile_size * 0.12),
            (x - tile_size * 0.39, y + tile_size * 0.31),
            (x, y + tile_size * 0.82))
    right = tuple((2 * x - point[0], point[1]) for point in left)
    outline = [_bezier(left, index / 32) for index in range(33)]
    outline += [_bezier(right, index / 32) for index in range(32, -1, -1)]
    _polygon(surface, (29, 30, 33, round(60 + pulse * 20)), outline)
    for curve in (left, right):
        _ribbon(surface, curve, (*rgb, 26), tile_size * 0.12)
        _ribbon(surface, curve, (7, 9, 14, 200), tile_size * 0.055)
        _ribbon(surface, curve, (*rgb, round(155 + pulse * 45)), tile_size * 0.026)
    for index in range(2):
        offset = index * tile_size * 0.22
        _ribbon(surface, ((x - tile_size * 0.27, y + offset),
                         (x - tile_size * 0.18, y + tile_size * 0.26 + offset),
                         (x + tile_size * 0.18, y + tile_size * 0.26 + offset),
                         (x + tile_size * 0.27, y + offset)),
                (*rgb, round(106 + pulse * 40)), tile_size * 0.065)
    return _finish(surface, size)
