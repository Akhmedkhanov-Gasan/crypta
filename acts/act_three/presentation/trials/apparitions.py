import math
from functools import lru_cache
from pathlib import Path

import pygame
import resource_store as resources

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.trials.archer_effects import center
from acts.act_three.presentation.ability_unlock_banner import draw_unlock_banner


def ease(value):
    value = max(0, min(1, value))
    return value * value * (3 - 2 * value)


@lru_cache(maxsize=20)
def texture(kind, width, height, blurred=False):
    folders = {"assassin": "assassin_shadow_step", "archer": "archer_piercing_trial", "berserker": "berserker_crushing_leap", "paladin": "paladin_shield_charge", "summoner": "summoner_release_familiar"}
    root = Path(__file__).resolve().parents[4] / "assets/maps/act_3/trials"
    image = resources.load_image(str(root / folders[kind] / f"{kind}.png")).convert_alpha()
    if blurred:
        image = pygame.transform.smoothscale(image, (18, 18))
    return pygame.transform.smoothscale(image, (width, height))


@lru_cache(maxsize=5)
def smoke(kind):
    image = texture(kind, 192, 192)
    patch = image.subsurface((0, 100, 192, 92)).copy()
    patch.fill((65, 57, 68, 255), special_flags=pygame.BLEND_RGBA_MULT)
    feather = pygame.Surface((32, 32), pygame.SRCALPHA)
    for y in range(32):
        vertical = math.sin(math.pi * y / 31) ** 1.6
        for x in range(32):
            horizontal = math.sin(math.pi * x / 31) ** .7
            feather.set_at((x, y), (255, 255, 255, round(255 * vertical * horizontal)))
    patch.blit(pygame.transform.smoothscale(feather, patch.get_size()), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return pygame.transform.smoothscale(patch, (320, 74))


@lru_cache(maxsize=128)
def reveal_mask(step):
    mask = pygame.Surface((1, 64), pygame.SRCALPHA)
    reveal = step / 127
    for row in range(64):
        depth = row / 63
        visibility = ease((reveal - (1 - depth) * .58) / .38)
        mask.set_at((0, row), (255, 255, 255, round(255 * visibility)))
    return mask


def apparition(layer, kind, position, dimensions, opacity, reveal, clock, drift=1, spread=0):
    if opacity <= 0 or reveal <= 0:
        return
    width, height = dimensions
    image = texture(kind, width, height).copy()
    mask = pygame.transform.smoothscale(reveal_mask(round(max(0, min(1, reveal)) * 127)), (width, height))
    image.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    breathing = 1 + math.sin(clock * .0014) * drift * .0015
    target_width = max(1, round(width * breathing + spread * 1.2))
    image = pygame.transform.smoothscale(image, (target_width, height))
    image.set_alpha(round(max(0, min(255, opacity))))
    wave = math.sin(clock * .0011) * drift * .35
    layer.blit(image, (round(position[0] - target_width / 2 + wave), round(position[1] - height / 2)))


def ground_veil(layer, kind, px, py, size, strength, elapsed, outward=False):
    image = smoke(kind)
    for side in (-1, 1):
        movement = ease(elapsed / 1400)
        distance = (.3 + movement * .7) if outward else (1 - movement) * .9
        width = round(size * (2.5 + .35 * math.sin(elapsed / 1700 + side)))
        height = round(size * .65)
        patch = pygame.transform.smoothscale(image, (width, height))
        patch.set_alpha(round(150 * strength))
        if side < 0:
            patch = pygame.transform.flip(patch, True, False)
        layer.blit(patch, (round(px + side * size * distance - width / 2), round(py - height * .45)))


def shadow_rite(layer, px, py, size, elapsed, strength):
    merge = ease((elapsed - 180) / 1350)
    release = ease((elapsed - 2050) / 1000)
    reveal = min(1, elapsed / 900) * (1 - release)
    ground_veil(layer, "assassin", px, py + size * .35, size, strength * (1 - release), elapsed)
    for side in (-1, 1):
        position = (px + side * size * (1.15 * (1 - merge)), py - size * (.4 + merge * .15))
        apparition(layer, "assassin", position, (round(size * 2.55), round(size * 3.05)),
                   66 * strength * (1 - merge) * (1 - release), reveal, elapsed + side * 400, 5)
    position = px, py - size * (.2 + merge * .45) + size * release * .25
    apparition(layer, "assassin", position, (round(size * 2.55), round(size * 3.05)),
               164 * strength * (1 - release), reveal, elapsed, 3 + release * 8)


def hunter_rite(layer, px, py, size, elapsed, strength):
    unfold = ease((elapsed - 100) / 1150)
    withdraw = ease((elapsed - 1900) / 1200)
    reveal = min(1, elapsed / 900) * (1 - withdraw * .8)
    dimensions = round(size * 3.45), round(size * 2.8)
    position = px, py - size * (.55 + withdraw * .3)
    ground_veil(layer, "archer", px, py + size * .3, size, strength * .8 * (1 - withdraw), elapsed, True)
    apparition(layer, "archer", position, dimensions, 151 * strength * (1 - withdraw),
               reveal, elapsed, 2.5 + withdraw * 5, size * .35 * (1 - unfold))
    for side in (-1, 1):
        apparition(layer, "archer", (px + side * size * .12 * (1 - unfold), position[1] + size * .04),
                   dimensions, 29 * strength * math.sin(unfold * math.pi), reveal, elapsed + side * 350, 4)


def ancestor_rite(layer, px, py, size, elapsed, strength):
    rise = ease((elapsed - 120) / 1550)
    release = ease((elapsed - 2850) / 1200)
    impact = max(0, 1 - abs(elapsed - 1600) / 340)
    weight = math.sin(max(0, elapsed - 1550) / 36) * size * .025 * max(0, 1 - max(0, elapsed - 1550) / 480)
    position = px + weight, py + size * (.25 - rise * .9 + release * .2)
    dimensions = round(size * 3.45), round(size * 3.15)
    ground_veil(layer, "berserker", px, py + size * .35, size, strength * (1 - release), elapsed - 500, True)
    apparition(layer, "berserker", position, dimensions, (149 + impact * 37) * strength * (1 - release),
               min(1, elapsed / 1400) * (1 - release), elapsed, 1.1 + release * 4)
    if impact > 0:
        image = texture("berserker", round(size * 3.45), round(size * 3.15), True).copy()
        image.fill((145, 72, 42, 255), special_flags=pygame.BLEND_RGBA_MULT)
        image.set_alpha(round(90 * impact))
        layer.blit(image, (round(position[0] - image.get_width() / 2), round(position[1] - image.get_height() / 2)))


def cathedral_rite(layer, px, py, size, elapsed, strength):
    form = ease((elapsed - 100) / 1400)
    release = ease((elapsed - 2700) / 1200)
    dimensions = round(size * 3.1), round(size * 3.35)
    position = px, py - size * (.15 + form * .55) - release * size * .15
    ground_veil(layer, "paladin", px, py + size * .35, size, strength * .7 * (1 - release), elapsed)
    soft = texture("paladin", *dimensions, True).copy()
    soft.set_alpha(round(70 * strength * form * (1 - release)))
    layer.blit(soft, (round(position[0] - soft.get_width() / 2), round(position[1] - soft.get_height() / 2)))
    apparition(layer, "paladin", position, dimensions, 170 * strength * (1 - release),
               min(1, elapsed / 1150) * (1 - release * .85), elapsed, 1.4 + release * 3,
               size * .2 * (1 - form))


STYLES = {
    "assassin": (3400, "SHADOW STEP", (213, 193, 235), (166, 140, 192), (10, 6, 16), shadow_rite, 650),
    "archer": (3400, "PIERCING SHOT", (208, 216, 174), (158, 171, 136), (7, 12, 9), hunter_rite, 800),
    "berserker": (4400, "CRUSHING LEAP", (235, 185, 139), (192, 114, 83), (17, 8, 6), ancestor_rite, 850),
    "paladin": (4200, "SHIELD CHARGE", (237, 220, 164), (193, 165, 103), (17, 14, 9), cathedral_rite, 700),
}


def draw_rite(context, kind, elapsed, origin):
    duration, title, title_color, subtitle_color, shade, draw, delay = STYLES[kind]
    if not 0 <= elapsed < duration:
        return
    strength = max(0, min(1, elapsed / 400, (duration - elapsed) / 650))
    layer = pygame.Surface(context.view_surface.get_size(), pygame.SRCALPHA)
    layer.fill((*shade, round(86 * strength)))
    px, py = center(context, origin)
    draw(layer, px, py, ACT_THREE_TILE_SIZE, elapsed, strength)
    context.view_surface.blit(layer, (0, 0))
    banner_elapsed = (elapsed - delay) * 3400 / (duration - delay)
    draw_unlock_banner(context.view_surface, banner_elapsed, title, title_color, subtitle_color, shade)
