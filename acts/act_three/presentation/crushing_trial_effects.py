import math
from functools import lru_cache

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.piercing_trial_effects import center
from acts.act_three.presentation.trial_rite_shapes import ease, envelope, relief
from acts.act_three.presentation.ability_unlock_banner import draw_unlock_banner


@lru_cache(maxsize=1)
def fissures():
    paths = []
    for index in range(9):
        angle = index * 2.399
        points = [(0, 0)]
        for step in range(1, 6):
            radius = step * (.13 + (index % 3) * .015)
            bend = angle + math.sin(index * 7 + step * 3) * .24
            points.append((math.cos(bend) * radius, math.sin(bend) * radius * .45))
        paths.append(points)
    return paths


def draw_completion(context, trial, now):
    elapsed = now - trial["completed"]
    if not 0 <= elapsed < 4400:
        return
    size = ACT_THREE_TILE_SIZE
    surface = context.view_surface
    px, py = center(context, trial["completion_origin"])
    feet = py + size * .3
    strength = envelope(elapsed, 4400)
    rise = ease((elapsed - 250) / 950)
    collapse = ease((elapsed - 1400) / 450)
    fade = 1 - ease((elapsed - 2600) / 1400)
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    layer.fill((16, 7, 5, round(82 * strength)))
    for index, cell in enumerate(trial["plates"]):
        sx, sy = center(context, cell)
        t = ease((elapsed - index * 55) / 950)
        if 0 < t < 1:
            points = [(sx, sy), (sx + (px - sx) * .45, sy + (feet - sy) * .6), (sx + (px - sx) * t, sy + (feet - sy) * t)]
            pygame.draw.lines(layer, (81, 39, 25, round(150 * strength * (1 - t))), False, points, 5)
            pygame.draw.lines(layer, (165, 88, 48, round(130 * strength * (1 - t))), False, points, 1)
    for side in (-1, 1):
        for index in range(3):
            x = px + side * size * (.5 + index * .2 + (1 - rise) * .3)
            y = feet - size * rise * (.3 + index * .26) + size * collapse * (.35 + index * .14)
            width = size * (.22 - index * .025)
            height = size * (.55 + index * .1)
            points = [(x - width, y - height * .6), (x + width * .4, y - height),
                      (x + width, y - height * .38), (x + width * .75, y + height * .2), (x - width * .7, y)]
            relief(layer, points, (49 + index * 5, 40, 33), (130, 99, 70), strength * fade * .8)
            pygame.draw.line(layer, (185, 101, 57, round(120 * strength * fade)), points[1], points[3], 1)
    impact = elapsed - 1450
    if impact >= 0:
        reveal = ease(impact / 400)
        for index, path in enumerate(fissures()):
            vertices = [(px + x * size * 1.5 * reveal, feet + y * size * 1.5 * reveal) for x, y in path]
            pygame.draw.lines(layer, (31, 18, 13, round(230 * strength * fade)), False, vertices, 7)
            pygame.draw.lines(layer, (150, 65, 35, round(220 * strength * fade)), False, vertices, 2)
            pygame.draw.lines(layer, (215, 137, 75, round(140 * strength * fade)), False, vertices[:4], 1)
        pressure = max(0, 1 - impact / 500)
        for side in (-1, 1):
            points = [(px + side * size * (.3 + reveal * 1.2), feet - size * .1),
                      (px + side * size * (.65 + reveal * 1.3), feet - size * .3),
                      (px + side * size * (.7 + reveal * 1.4), feet + size * .15)]
            relief(layer, points, (58, 39, 27), (104, 64, 37), pressure * strength * .45, 1)
    surface.blit(layer, (0, 0))
    draw_unlock_banner(surface, elapsed - 850, "CRUSHING LEAP", (235, 185, 139), (192, 114, 83), (28, 12, 10))
