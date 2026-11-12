import math
from functools import lru_cache
from weakref import WeakKeyDictionary

import pygame

from presentation.movement import smoothstep


TEMPERING_DURATION_MS = 1450
QUENCH_MS = 520
FILL_DELAY_MS = 140
FILL_DURATION_MS = 1150

_TEMPERING_STARTS = WeakKeyDictionary()


def start_tempering(floor, current_time):
    _TEMPERING_STARTS[floor] = current_time


def stop_tempering(floor):
    _TEMPERING_STARTS.pop(floor, None)


def tempering_elapsed(floor, current_time):
    started_at = _TEMPERING_STARTS.get(floor)
    if started_at is None:
        return None

    elapsed = max(0, current_time - started_at)
    if elapsed >= TEMPERING_DURATION_MS:
        stop_tempering(floor)
        return None
    return elapsed


def animated_forge_rank(rank, elapsed):
    if elapsed is None:
        return rank
    progress = smoothstep((elapsed - FILL_DELAY_MS) / FILL_DURATION_MS)
    return max(0, rank - 1) + progress


@lru_cache(maxsize=32)
def _glow(radius, color):
    surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for ring in range(radius, 0, -1):
        alpha = round(255 * (1 - ring / radius) ** 2)
        pygame.draw.circle(surface, (*color, alpha), (radius, radius), ring)
    return surface


def _draw_glow(screen, center, radius, color, alpha):
    glow = _glow(radius, color).copy()
    glow.set_alpha(round(max(0, min(255, alpha))))
    screen.blit(glow, glow.get_rect(center=center))


def draw_tempering(screen, sprite, rectangle, elapsed):
    heat = smoothstep(elapsed / QUENCH_MS) * (
        1 - smoothstep((elapsed - QUENCH_MS) / 400)
    )
    center_x, center_y = rectangle.center
    if heat > 0:
        _draw_glow(screen, rectangle.center, 86, (221, 72, 23), heat * 180)
        heated_sprite = sprite.copy()
        heated_sprite.fill((145, 51, 15, 0), special_flags=pygame.BLEND_RGBA_ADD)
        heated_sprite.set_alpha(round(heat * 180))
        screen.blit(heated_sprite, rectangle)

    since_quench = elapsed - QUENCH_MS
    if since_quench < 0:
        return

    flash = 1 - smoothstep(since_quench / 170)
    if flash > 0:
        _draw_glow(screen, rectangle.center, 72, (224, 181, 255), flash * 215)

    for index in range(6):
        age = since_quench - index * 45
        if 0 <= age < 700:
            progress = age / 700
            drift = math.sin(index * 2.4) * (14 + progress * 30)
            center = (
                round(center_x + drift),
                round(center_y + 12 - progress * 79),
            )
            radius = 18 + int(progress * 5) * 4
            alpha = math.sin(math.pi * progress) * 105
            _draw_glow(screen, center, radius, (158, 151, 185), alpha)

    particles = pygame.Surface((320, 250), pygame.SRCALPHA)
    origin = (160, 132)
    for index in range(28):
        lifetime = 390 + index % 6 * 70
        if since_quench >= lifetime:
            continue
        seconds = since_quench / 1000
        progress = since_quench / lifetime
        angle = -math.pi / 2 + math.sin(index * 2.4) * 1.5
        speed = 54 + index % 9 * 15
        x = origin[0] + math.cos(angle) * speed * seconds
        y = origin[1] + math.sin(angle) * speed * seconds + 104 * seconds**2
        alpha = round(255 * (1 - progress) ** 1.4)
        color = (248, 171, 74) if index % 3 else (230, 194, 255)
        head = (round(x), round(y))
        tail = (
            round(x - math.cos(angle) * speed * 0.04),
            round(y - (math.sin(angle) * speed + 208 * seconds) * 0.04),
        )
        pygame.draw.line(particles, (*color, alpha // 2), tail, head)
        pygame.draw.circle(particles, (*color, alpha), head, 1 + (index % 5 == 0))
    screen.blit(particles, (center_x - origin[0], center_y - origin[1]))


def draw_forge_fill_glow(screen, rectangle, filled_width, elapsed):
    if elapsed is None or filled_width <= 0:
        return

    strength = smoothstep(elapsed / 230) * (
        1 - smoothstep((elapsed - 1100) / 350)
    )
    edge = rectangle.left + filled_width
    previous_clip = screen.get_clip()
    screen.set_clip(previous_clip.clip(
        pygame.Rect(rectangle.left, rectangle.top, filled_width, rectangle.height)
    ))
    try:
        _draw_glow(
            screen, (edge - 3, rectangle.centery), 30, (221, 162, 255), strength * 235,
        )
    finally:
        screen.set_clip(previous_clip)
