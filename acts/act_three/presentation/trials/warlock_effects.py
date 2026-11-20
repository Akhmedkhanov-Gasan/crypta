import math
from functools import lru_cache

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.trials.warlock import sprites
from acts.act_three.presentation.trials.archer_effects import center
from acts.act_three.presentation.ability_unlock_banner import draw_unlock_banner
from acts.act_three.presentation.trials.apparitions import ease, reveal_mask


@lru_cache(maxsize=4)
def apparition(index, size):
    image = pygame.transform.smoothscale(sprites()[index], (size, size))
    image.fill((144, 99, 169, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return image


def seal_fragment(index, size, reveal, opacity):
    image = apparition(index, size).copy()
    mask = pygame.transform.smoothscale(reveal_mask(round(max(0, min(1, reveal)) * 127)), image.get_size())
    image.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    image.set_alpha(round(max(0, min(255, opacity))))
    return image


def draw_body_rite(context, now):
    trial = context.floor.curse_trial
    if trial is None or trial["phase"] != "body_rite":
        return
    elapsed = now - trial["started"]
    size = ACT_THREE_TILE_SIZE
    surface = context.view_surface
    px, py = center(context, trial["return_cell"])
    fade = max(0, min(1, elapsed / 400, (4900 - elapsed) / 900))
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    layer.fill((9, 3, 15, round(100 * fade)))
    if elapsed < 400:
        layer.fill((6, 3, 10, round(255 * (1 - elapsed / 400))))
    release = ease((elapsed - 2800) / 1500)
    reveal = max(0, min(1, (elapsed - 400) / 900))
    mask_size = round(size * 2.3)
    mask = seal_fragment(1, mask_size, reveal * (1 - release), 150 * fade * (1 - release))
    mask_y = py - size * (1.8 + .12 * math.sin(elapsed / 950))
    layer.blit(mask, (round(px - mask_size / 2), round(mask_y)))
    clasp = max(0, min(1, (elapsed - 950) / 600))
    clasp = clasp * clasp * (3 - 2 * clasp)
    for index, side in ((0, -1), (2, 1)):
        image = seal_fragment(index, size, reveal * (1 - release), 165 * fade * (1 - release))
        x = px + side * size * (1.45 - clasp * .92)
        y = py - size * .7
        layer.blit(image, (round(x - size / 2), round(y - size / 2)))
    impact = max(0, 1 - abs(elapsed - 1450) / 180)
    if impact:
        flash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        flash.fill((91, 41, 111, round(36 * impact)))
        layer.blit(flash, (0, 0))
    surface.blit(layer, (0, 0))
    draw_unlock_banner(surface, elapsed - 1400, "CURSE", (218, 183, 232), (177, 126, 195), (19, 8, 25))
