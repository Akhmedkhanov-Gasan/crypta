import math
from functools import lru_cache

import pygame
import resource_store as resources

from presentation.layout import ACT_THREE_TILE_SIZE, ASSET_ROOT


DURATION_MS = 3400
_DEFAULT_PALETTE = ((45, 42, 52), (145, 137, 148))
_PALETTES = {
    "berserker": ((70, 19, 23), (162, 78, 66)),
    "paladin": ((62, 50, 38), (168, 148, 112)),
    "assassin": ((40, 31, 52), (135, 118, 151)),
    "archer": ((36, 49, 25), (128, 145, 87)),
    "warlock": ((52, 27, 66), (151, 107, 167)),
    "summoner": ((24, 50, 56), (104, 153, 156)),
}
_MOTION = {
    "berserker": (1.8, 7, 1.2),
    "paladin": (.7, 3, .65),
    "assassin": (1.3, 12, .9),
    "archer": (1.1, 15, 1.1),
    "warlock": (1.5, 8, .8),
    "summoner": (.9, 6, .75),
}


def load_level_up_assets():
    directory = ASSET_ROOT / "act_3" / "player" / "level_up"
    art = {}
    for subclass in _PALETTES:
        source = resources.load_image(directory / f"{subclass}.png").convert_alpha()
        bounds = source.get_bounding_rect()
        if bounds.width and bounds.height:
            source = source.subsurface(bounds).copy()
        size = source.get_rect().fit(pygame.Rect(0, 0, 148, 148)).size
        image = pygame.transform.smoothscale(source, size)
        image.fill((210, 200, 205, 255), special_flags=pygame.BLEND_RGBA_MULT)
        ground = pygame.transform.smoothscale(image, (166, 45))
        ground.fill((125, 117, 130, 255), special_flags=pygame.BLEND_RGBA_MULT)
        art[subclass] = {"image": image, "ground": ground}
    return {"level_up_art": art}


def _color(color, alpha):
    return (*color, max(0, min(255, round(alpha))))


@lru_cache(maxsize=12)
def _mist(color):
    image = pygame.Surface((64, 64), pygame.SRCALPHA)
    for radius in range(31, 0, -1):
        pygame.draw.circle(image, _color(color, 75 * (1 - radius / 32) ** 2), (32, 32), radius)
    return image


def _puff(surface, position, size, color, opacity):
    image = pygame.transform.smoothscale(_mist(color), size)
    image.set_alpha(max(0, min(255, round(255 * opacity))))
    surface.blit(image, image.get_rect(center=(round(position[0]), round(position[1]))))


def _timing(player, now):
    elapsed = now - player.act_three.level_up_effect_started_at
    if player.act_three.level_up_effect_started_at < 0 or not 0 <= elapsed < DURATION_MS or player.health <= 0:
        return None
    progress = elapsed / DURATION_MS
    fade_in = min(1, elapsed / 650)
    fade_in = fade_in * fade_in * (3 - 2 * fade_in)
    fade_out = min(1, (DURATION_MS - elapsed) / 1150)
    fade_out = fade_out * fade_out * (3 - 2 * fade_out)
    return progress, fade_in * fade_out


def draw_level_up_ground(surface, player, position, now, assets):
    timing = _timing(player, now)
    if timing is None:
        return
    progress, opacity = timing
    dark = _PALETTES.get(player.subclass, _DEFAULT_PALETTE)[0]
    speed = _MOTION.get(player.subclass, (1, 6, 1))[0]
    image = pygame.Surface((300, 140), pygame.SRCALPHA)
    center = (150, 70)
    _puff(image, center, (225, 79), (12, 9, 16), opacity)
    art = assets["level_up_art"].get(player.subclass)
    if art is not None:
        ground = art["ground"].copy()
        ground.set_alpha(round(110 * opacity))
        image.blit(ground, ground.get_rect(center=center))
    for index in range(15):
        angle = index * 2.399 + progress * speed
        distance = 18 + index % 5 * 13 + math.sin(progress * math.pi) * 9
        x = center[0] + math.cos(angle) * distance
        y = center[1] + math.sin(angle) * distance * .23
        width = 58 + index % 4 * 13
        breath = .65 + .35 * math.sin(index * 1.7 + progress * math.tau)
        _puff(image, (x, y), (width, 28 + index % 3 * 7), dark, opacity * breath)
    surface.blit(image, (round(position[0] + ACT_THREE_TILE_SIZE / 2 - center[0]),
                         round(position[1] + ACT_THREE_TILE_SIZE - 4 - center[1])))


def _draw_apparition(surface, art, feet, progress, opacity, speed):
    source = art["image"]
    breath = 1 + math.sin(progress * math.tau * 1.4) * .025
    expansion = .91 + .12 * (1 - (1 - progress) ** 3)
    width = round(source.get_width() * expansion * breath)
    height = round(source.get_height() * expansion / breath)
    image = pygame.transform.smoothscale(source, (width, height))
    x = round(feet[0] - width / 2)
    y = round(feet[1] + 15 - height - math.sin(progress * math.pi) * 5)
    echo = pygame.transform.smoothscale(image, (width + 8, height + 6))
    echo.set_alpha(round(23 * opacity * math.sin(progress * math.pi)))
    surface.blit(echo, (x - 4 + round(math.sin(progress * 8) * 3), y - 3))
    reveal = min(1.2, progress / .27 * 1.2)
    dissolve = max(0, (progress - .64) / .36)
    for row in range(0, height, 2):
        depth = row / height
        visibility = max(0, min(1, (reveal - (1 - depth)) * 6))
        erosion = max(0, 1 - dissolve * (1.1 + .45 * math.sin(row * .39)))
        alpha = round(157 * opacity * visibility * erosion)
        if alpha <= 0:
            continue
        strip = image.subsurface((0, row, width, min(2, height - row))).copy()
        strip.set_alpha(alpha)
        wave = math.sin(row * .10 - progress * 9 * speed) * (1.1 + dissolve * 3)
        surface.blit(strip, (x + round(wave), y + row - round(dissolve * (1 - depth) * 10)))


def _draw_embers(surface, feet, progress, opacity, dark, light, motion):
    speed, drift, rise = motion
    for index in range(30):
        phase = (progress * speed + index / 30) % 1
        angle = index * 2.399
        x = feet[0] + math.cos(angle) * (21 + index % 6 * 8)
        x += math.sin(phase * 4 + angle) * drift
        y = feet[1] + math.sin(angle) * 9 - phase * (24 + index % 4 * 8) * rise
        strength = opacity * math.sin(phase * math.pi) ** 2
        if index % 3 == 0:
            _puff(surface, (x, y), (25, 19), dark, strength * .8)
        color = light if index % 4 == 0 else dark
        pygame.draw.circle(surface, _color(color, 155 * strength), (round(x), round(y)), 1)
    for index in range(7):
        phase = (progress * .6 + index / 7) % 1
        x = feet[0] + math.sin(index * 2.4 + progress * 3) * (28 + index * 4)
        y = feet[1] + 5 - phase * 28
        _puff(surface, (x, y), (65, 33), dark, opacity * math.sin(phase * math.pi) * .8)


def _draw_label(surface, player, feet, progress, opacity, color, font):
    label_opacity = opacity * min(1, max(0, (progress - .12) / .18))
    label = f"LEVEL {player.level}"
    if player.act_three.level_up_effect_amount > 1:
        label += f"  (+{player.act_three.level_up_effect_amount})"
    text = font.render(label, True, color)
    shadow = font.render(label, True, (13, 9, 16))
    text.set_alpha(round(225 * label_opacity))
    shadow.set_alpha(round(235 * label_opacity))
    rect = text.get_rect(midbottom=(round(feet[0]), round(feet[1] - 133 - progress * 8)))
    surface.blit(shadow, rect.move(0, 2))
    surface.blit(text, rect)


def draw_level_up_foreground(surface, player, position, now, font, assets):
    timing = _timing(player, now)
    if timing is None:
        return
    progress, opacity = timing
    dark, light = _PALETTES.get(player.subclass, _DEFAULT_PALETTE)
    motion = _MOTION.get(player.subclass, (1, 6, 1))
    image = pygame.Surface((360, 340), pygame.SRCALPHA)
    feet = (180, 245)
    art = assets["level_up_art"].get(player.subclass)
    if art is not None:
        _draw_apparition(image, art, feet, progress, opacity, motion[0])
    _draw_embers(image, feet, progress, opacity, dark, light, motion)
    _draw_label(image, player, feet, progress, opacity, light, font)
    surface.blit(image, (round(position[0] + ACT_THREE_TILE_SIZE / 2 - feet[0]),
                         round(position[1] + ACT_THREE_TILE_SIZE - 4 - feet[1])))
