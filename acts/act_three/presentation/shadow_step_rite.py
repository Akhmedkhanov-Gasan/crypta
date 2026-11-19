import math

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.piercing_trial_effects import center
from acts.act_three.presentation.trial_rite_shapes import ease, envelope, relief, ribbon
from acts.act_three.presentation.ability_unlock_banner import draw_unlock_banner


def draw_completion(context, trial, elapsed):
    if not 0 <= elapsed < 3400:
        return
    size = ACT_THREE_TILE_SIZE
    px, py = center(context, trial["final"])
    strength = envelope(elapsed, 3400)
    opening = ease(elapsed / 1000) * (1 - ease((elapsed - 1800) / 900))
    layer = pygame.Surface(context.view_surface.get_size(), pygame.SRCALPHA)
    layer.fill((8, 5, 15, round(80 * strength)))
    for side in (-1, 1):
        for index in range(3):
            points = []
            for step in range(16):
                t = step / 15
                x = px + side * size * (1.7 * (1 - t) + .1)
                y = py + size * (.32 + math.sin(t * math.pi + index) * .15) - t * size * .45
                points.append((x, y))
            ribbon(layer, points, size * (.04 + index * .015), (31 + index * 5, 20, 45 + index * 5), 170 * strength)
    slit = [(px - size * opening * .22, py + size * .43), (px - size * opening * .12, py - size * .25),
            (px - size * opening * .2, py - size * .65), (px, py - size * 1.8),
            (px + size * opening * .19, py - size * .55), (px + size * opening * .09, py - size * .15), (px + size * opening * .22, py + size * .43)]
    if opening > .01:
        relief(layer, slit, (8, 5, 13), (117, 84, 147), strength)
        pygame.draw.line(layer, (188, 161, 207, round(150 * strength * opening)), (px, py - size * 1.6), (px, py + size * .2), 1)
    converge = ease((elapsed - 450) / 1100)
    for side in (-1, 1):
        x = px + side * size * (.9 - converge * .63)
        y = py - size * (.15 + converge * .45)
        blade = [(x, y - size * .75), (x + side * size * .11, y - size * .18), (x, y), (x - side * size * .07, y - size * .2)]
        relief(layer, blade, (39, 33, 52), (171, 158, 188), strength * (1 - ease((elapsed - 2000) / 800)))
        pygame.draw.line(layer, (113, 87, 140, round(210 * strength)), (x - size * .13, y), (x + size * .13, y), 3)
    context.view_surface.blit(layer, (0, 0))
    draw_unlock_banner(context.view_surface, elapsed, "SHADOW STEP", (213, 193, 235), (166, 140, 192), (15, 10, 22))
