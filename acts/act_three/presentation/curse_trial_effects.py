import math
from functools import lru_cache

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.curse_trial import sprites
from acts.act_three.presentation.piercing_trial_effects import center
from acts.act_three.presentation.ability_unlock_banner import draw_unlock_banner


@lru_cache(maxsize=4)
def apparition(index, size):
    image = pygame.transform.smoothscale(sprites()[index], (size, size))
    image.fill((144, 99, 169, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return image


def draw_body_rite(context, now):
    trial = context.floor.curse_trial
    if trial is None or trial["phase"] != "body_rite":
        return
    elapsed = now - trial["started"]
    size = ACT_THREE_TILE_SIZE
    surface = context.view_surface
    px, py = center(context, trial["return_cell"])
    feet = py + size * .32
    fade = max(0, min(1, elapsed / 400, (4900 - elapsed) / 900))
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    layer.fill((9, 3, 15, round(100 * fade)))
    if elapsed < 400:
        layer.fill((6, 3, 10, round(255 * (1 - elapsed / 400))))
    gathering = max(0, min(1, elapsed / 1550))
    release = max(0, min(1, (elapsed - 2400) / 1700))
    intensity = fade * (1 - release)
    for index in range(7):
        angle = index * math.tau / 7 + .2
        points = []
        widths = []
        for step in range(18):
            t = step / 17
            radius = size * (2.3 - gathering * .7) * (1 - t)
            bend = angle + math.sin(t * 5 + index + elapsed / 1400) * .32
            x = px + math.cos(bend) * radius
            y = feet + math.sin(bend) * radius * .42 - math.sin(t * math.pi) * size * .1
            points.append((x, y))
            widths.append(size * .085 * math.sin(t * math.pi) * intensity)
        upper = [(x, y - width) for (x, y), width in zip(points, widths)]
        lower = [(x, y + width) for (x, y), width in reversed(list(zip(points, widths))) ]
        pygame.draw.polygon(layer, (23, 10, 32, round(195 * intensity)), upper + lower)
        pygame.draw.lines(layer, (101, 57, 124, round(80 * intensity)), False, points[3:15], 2)
    reveal = max(0, min(1, (elapsed - 400) / 900))
    mask_size = round(size * 2.3)
    mask = apparition(1, mask_size).copy()
    mask.set_alpha(round(130 * reveal * (1 - release)))
    mask_y = py - size * (1.8 + .12 * math.sin(elapsed / 950))
    layer.blit(mask, (round(px - mask_size / 2), round(mask_y)))
    clasp = max(0, min(1, (elapsed - 950) / 600))
    clasp = clasp * clasp * (3 - 2 * clasp)
    for index, side in ((0, -1), (2, 1)):
        image = apparition(index, size).copy()
        image.set_alpha(round(165 * reveal * (1 - release)))
        x = px + side * size * (1.45 - clasp * .92)
        y = py - size * .7
        layer.blit(image, (round(x - size / 2), round(y - size / 2)))
    seal_reveal = max(0, min(1, (elapsed - 1200) / 400))
    seal_strength = seal_reveal * fade * (1 - release * .7)
    if seal_strength > 0:
        paths = [
            [(-.65, -.1), (-.43, -.38), (-.2, -.25), (0, -.56), (.2, -.25), (.43, -.38), (.65, -.1)],
            [(-.65, .1), (-.42, .35), (-.18, .28), (0, .55), (.18, .28), (.42, .35), (.65, .1)],
            [(-.29, -.18), (0, .25), (.29, -.18)],
            [(0, -.29), (0, .4)],
        ]
        for path in paths:
            points = [(px + x * size, feet + y * size * .5) for x, y in path]
            pygame.draw.lines(layer, (49, 18, 62, round(185 * seal_strength)), False, points, 6)
            pygame.draw.lines(layer, (159, 99, 185, round(220 * seal_strength)), False, points, 2)
            pygame.draw.lines(layer, (211, 172, 218, round(130 * seal_strength)), False, points, 1)
    impact = max(0, 1 - abs(elapsed - 1450) / 180)
    if impact:
        flash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        flash.fill((91, 41, 111, round(36 * impact)))
        layer.blit(flash, (0, 0))
    surface.blit(layer, (0, 0))
    draw_unlock_banner(surface, elapsed - 1400, "CURSE", (218, 183, 232), (177, 126, 195), (19, 8, 25))
