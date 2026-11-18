import math
from functools import lru_cache

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE, ACT_THREE_VIEW_X, ACT_THREE_VIEW_WIDTH
from acts.act_three.presentation.piercing_trial import screen_position
from acts.act_three.presentation.piercing_trial_effects import glow, center
from acts.act_three.presentation.ability_unlock_banner import draw_unlock_banner
from acts.act_three.presentation.trial_door import door_frames


@lru_cache(maxsize=17)
def tile(level):
    size = ACT_THREE_TILE_SIZE
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    t = level / 16
    inset = size * .09
    rect = pygame.Rect(round(inset), round(inset), round(size - inset * 2), round(size - inset * 2))
    pygame.draw.rect(image, (26 + round(44 * t), 25 + round(30 * t), 22 + round(12 * t), 220), rect, border_radius=4)
    tint = (76 + round(112 * t), 68 + round(82 * t), 49 + round(37 * t), 240)
    pygame.draw.rect(image, tint, rect, 2, border_radius=4)
    pygame.draw.rect(image, (83, 74, 50, 120), rect.inflate(-8, -8), 1, border_radius=2)
    cx = cy = size // 2
    radius = round(size * .12)
    pygame.draw.polygon(image, tint, [(cx, cy - radius), (cx + radius, cy), (cx, cy + radius), (cx - radius, cy)], 2)
    if level:
        aura = glow(size // 2, (199, 149, 61))
        aura.set_alpha(round(150 * t))
        image.blit(aura, (0, 0))
        pygame.draw.line(image, (231, 202, 129, round(230 * t)), (cx - 3, cy), (cx + 3, cy), 2)
    return image


def draw_rune(context, trial, now):
    size = ACT_THREE_TILE_SIZE
    marker = pygame.Surface((size, size), pygame.SRCALPHA)
    phase = trial["phase"]
    elapsed = now - trial["started"]
    active = phase in ("active", "awakening", "completion", "complete")
    strength = .4 + .1 * math.sin(now / 900)
    if active:
        strength = .75 + .08 * math.sin(now / 650)
    if phase == "awakening":
        strength *= min(1, elapsed / 300)
    if phase == "extinguishing":
        strength = .4 + .4 * max(0, 1 - elapsed / 650)
    tint = (206, 173, 99, round(230 * strength))
    dim = (136, 111, 67, round(170 * strength))
    def point(x, y):
        return size * (.5 + x), size * (.53 + y * .65)
    paths = [
        [(-.31, -.12), (-.31, -.28), (-.12, -.34)],
        [(.12, -.34), (.31, -.28), (.31, -.12)],
        [(.31, .12), (.31, .28), (.12, .34)],
        [(-.12, .34), (-.31, .28), (-.31, .12)],
        [(-.19, -.22), (.19, -.22), (.16, .12), (0, .3), (-.16, .12), (-.19, -.22)],
    ]
    for path in paths:
        pygame.draw.lines(marker, dim, False, [point(x, y) for x, y in path], 3)
        pygame.draw.lines(marker, tint, False, [point(x, y) for x, y in path], 1)
    pygame.draw.lines(marker, tint, False, [point(0, -.14), point(0, .12)], 2)
    pygame.draw.lines(marker, tint, False, [point(-.1, -.03), point(.1, -.03)], 2)
    for index in range(8):
        progress = (now / 1700 + index / 8) % 1
        side = -1 if index % 2 else 1
        x, y = point(side * (.32 - progress * .11), .31 - progress * .62)
        alpha = round(140 * strength * math.sin(progress * math.pi))
        pygame.draw.line(marker, (229, 198, 126, alpha), (x, y), (x, y + 3), 1)
    if active or phase == "extinguishing":
        aura = glow(size // 2, (190, 142, 56))
        aura.set_alpha(round(110 * strength))
        marker.blit(aura, (0, 0))
    context.view_surface.blit(marker, screen_position(context, trial["start"]))


def draw_ground(context):
    trial = context.floor.shield_trial
    if trial is None:
        return
    now = pygame.time.get_ticks()
    phase = trial["phase"]
    elapsed = now - trial["started"]
    frame = min(7, elapsed // 80) if phase == "opening" else (0 if phase == "closed" else 7)
    context.view_surface.blit(door_frames()[frame], screen_position(context, trial["door"]))
    if phase in ("closed", "opening"):
        return
    draw_rune(context, trial, now)
    if phase == "ready":
        return
    for index, cell in enumerate(trial["cells"]):
        reveal = 1
        delay = (3 - index // 4) * 125 + (index % 4) * 35
        if phase == "awakening":
            reveal = max(0, min(1, (elapsed - delay) / 450))
        elif phase == "extinguishing":
            reveal = max(0, 1 - elapsed / 550)
        if reveal <= 0:
            continue
        sprite = tile(round(trial["levels"][index] * 16))
        position = screen_position(context, cell)
        if reveal < 1:
            sprite = sprite.copy()
            sprite.set_alpha(round(255 * reveal))
        context.view_surface.blit(sprite, position)
        if phase == "awakening" and 0 < reveal < 1:
            image = pygame.Surface((ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE), pygame.SRCALPHA)
            alpha = round(130 * math.sin(reveal * math.pi))
            inset = round(ACT_THREE_TILE_SIZE * .09)
            y = round(inset + reveal * (ACT_THREE_TILE_SIZE - inset * 2))
            pygame.draw.line(image, (227, 198, 121, alpha), (inset, y), (ACT_THREE_TILE_SIZE - inset, y), 2)
            context.view_surface.blit(image, position)
        elapsed = now - trial["pulse"].get(index, -1000)
        if 0 <= elapsed < 400:
            pulse = glow(ACT_THREE_TILE_SIZE // 2, (215, 174, 86))
            pulse.set_alpha(round(180 * (1 - elapsed / 400)))
            context.view_surface.blit(pulse, screen_position(context, cell))


def draw_overlay(context):
    trial = context.floor.shield_trial
    if trial is None or trial.get("completed") is None:
        return
    now = pygame.time.get_ticks()
    elapsed = now - trial["completed"]
    if not 0 <= elapsed < 4200:
        return
    surface = context.view_surface
    size = ACT_THREE_TILE_SIZE
    px, py = center(context, trial["completion_origin"])
    energy = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for number, cell in enumerate(trial["cells"]):
        sx, sy = center(context, cell)
        t = (elapsed - number * 28) / 1150
        if 0 < t < 1:
            eased = t * t * (3 - 2 * t)
            x = sx + (px - sx) * eased
            y = sy + (py - sy) * eased - math.sin(t * math.pi) * size * .6
            alpha = round(210 * math.sin(t * math.pi))
            pygame.draw.line(energy, (218, 185, 107, alpha), (x, y), (x, y + 6), 2)
    impact = max(0, min(1, (elapsed - 1200) / 1900))
    if 0 < impact < 1:
        aura = glow(size, (211, 168, 74))
        aura.set_alpha(round(220 * math.sin(impact * math.pi)))
        energy.blit(aura, (round(px - size), round(py - size * 1.3)))
        for index in range(24):
            angle = index * 2.399
            x = px + math.cos(angle) * size * .55 * (1 - impact)
            y = py + math.sin(angle) * size * .2 - impact * size * 1.4
            pygame.draw.line(energy, (235, 211, 155, round(180 * math.sin(impact * math.pi))), (x, y), (x, y + 5), 2)
    surface.blit(energy, (0, 0))
    draw_unlock_banner(surface, elapsed - 700, "SHIELD CHARGE", (237, 220, 164), (193, 165, 103), (23, 21, 14))


def draw_hint(screen, trial, font, top):
    if trial is None or trial["phase"] != "active":
        return
    text = font.render("[Q] Invoke light beneath your feet", True, (213, 194, 141))
    rect = text.get_rect(midtop=(ACT_THREE_VIEW_X + ACT_THREE_VIEW_WIDTH // 2, top))
    pygame.draw.rect(screen, (22, 21, 16), rect.inflate(16, 6))
    screen.blit(text, rect)
