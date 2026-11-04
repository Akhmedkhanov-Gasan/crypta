import math
import random
from functools import lru_cache

import pygame

from acts.act_three.awakening.dialogue import ARRIVAL_REVEAL_MS, BLACKOUT_MS


def _smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


@lru_cache(maxsize=2)
def _mist_texture(size):
    noise = random.Random(731)
    texture = pygame.Surface((128, 80), pygame.SRCALPHA)
    for _ in range(48):
        radius = noise.randint(9, 26)
        pygame.draw.ellipse(
            texture, (47, 49, 58, noise.randint(18, 62)),
            (noise.randint(-24, 128), noise.randint(-20, 80), radius * 3, radius),
        )
    texture = pygame.transform.gaussian_blur(texture, 6)
    return pygame.transform.smoothscale(texture, (round(size[0] * 1.5), round(size[1] * 1.5)))


def _draw_mist(screen, elapsed, strength):
    if strength <= 0:
        return
    mist = _mist_texture(screen.get_size())
    width, height = screen.get_size()
    for index in range(2):
        mist.set_alpha(round(strength * (100 - index * 35)))
        x = -width * 0.25 + math.sin(elapsed / 4800 + index * 2.1) * width * 0.12
        y = -height * 0.25 + math.cos(elapsed / 6200 + index * 1.7) * height * 0.1
        screen.blit(mist, (round(x), round(y)))


def _draw_darkness(screen, center, aperture, total_darkness):
    width, height = screen.get_size()
    reach = math.hypot(max(center[0], width - center[0]), max(center[1], height - center[1]))
    work_size = (max(1, width // 4), max(1, height // 4))
    radius = max(1.0, reach * (0.025 + aperture * 3.2) / 4)
    layer = pygame.Surface(work_size, pygame.SRCALPHA)
    layer.fill((2, 3, 6, 255))
    for index in range(40, -1, -1):
        fraction = index / 40
        extent = max(1, round(radius * fraction))
        alpha = round(255 * _smooth((fraction - 0.26) / 0.74))
        pygame.draw.ellipse(layer, (2, 3, 6, alpha), (round(center[0] / 4) - extent, round(center[1] / 4) - extent, extent * 2, extent * 2))
    layer = pygame.transform.smoothscale(layer, (width, height))
    screen.blit(layer, (0, 0))
    if total_darkness > 0:
        layer.fill((2, 3, 6, round(255 * total_darkness)))
        screen.blit(layer, (0, 0))


def draw_world_transition(screen, elapsed, center, revealing=False):
    if revealing:
        progress = _smooth((elapsed - 450) / (ARRIVAL_REVEAL_MS - 450))
        aperture = progress
        desaturation = (1.0 - progress) * 0.65
        obscurity = 1.0 - progress
        total_darkness = 1.0 - _smooth((elapsed - 220) / 500)
        breath = math.sin(progress * math.pi) * 0.012
    else:
        progress = _smooth((elapsed - 450) / (BLACKOUT_MS - 1250))
        aperture = 1.0 - progress
        desaturation = _smooth(elapsed / 1800)
        obscurity = progress
        total_darkness = _smooth((elapsed - BLACKOUT_MS + 1100) / 400)
        breath = progress * 0.035
    frame = screen.copy()
    if desaturation > 0:
        gray = pygame.transform.grayscale(frame)
        gray.set_alpha(round(230 * desaturation))
        frame.blit(gray, (0, 0))
        frame.fill(
            (round(255 - desaturation * 37), round(255 - desaturation * 30), round(255 - desaturation * 16)),
            special_flags=pygame.BLEND_RGB_MULT,
        )
    if obscurity > 0.01:
        reduction = 1.0 + obscurity * 4.0
        soft = pygame.transform.smoothscale(frame, (max(1, round(frame.get_width() / reduction)), max(1, round(frame.get_height() / reduction))))
        soft = pygame.transform.smoothscale(soft, frame.get_size())
        soft.set_alpha(round(150 * obscurity))
        frame.blit(soft, (0, 0))
    scale = 1.0 + breath
    zoomed = pygame.transform.smoothscale(frame, (round(frame.get_width() * scale), round(frame.get_height() * scale)))
    screen.blit(zoomed, (round(center[0] * (1.0 - scale)), round(center[1] * (1.0 - scale))))
    _draw_mist(screen, elapsed, math.sin(progress * math.pi) * 0.85)
    _draw_darkness(screen, center, aperture, total_darkness)
