import math

import pygame

from acts.act_three.presentation.berserker.effect_brushes import crescent, envelope, mist, polygon, spark
from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.settings import WARLOCK_DEMON_FORM_TRANSFORM_MS


VOID = ((25, 16, 36), (104, 47, 139), (212, 159, 229))
PACT = ((34, 12, 30), (141, 31, 66), (235, 128, 150))


def _soul_thread(layer, source, target, phase, palette=VOID):
    dx, dy = target[0] - source[0], target[1] - source[1]
    distance = max(1, math.hypot(dx, dy))
    opacity = envelope(phase) ** 0.7
    for index in range(12):
        travel = min(1, max(0, phase * 1.5 - index * 0.035))
        arc = math.sin(travel * math.pi) * (10 + index % 3 * 3)
        x = source[0] + dx * travel - dy / distance * arc
        y = source[1] + dy * travel + dx / distance * arc - math.sin(travel * math.pi) * 9
        mist(layer, (x, y), 8 + index % 3, palette[1], opacity * 0.5)
        if index % 3 == 0:
            spark(layer, (x, y), (dx / distance, dy / distance), palette[2], opacity * 0.85, 3)


def draw_madness_status(surface, position, width, now, turns, font=None):
    size = ACT_THREE_TILE_SIZE
    layer = pygame.Surface((size * width + 32, size + 40), pygame.SRCALPHA)
    center = layer.get_width() / 2, 18
    pulse = 0.65 + 0.2 * math.sin(now / 160)
    mist(layer, center, 17, PACT[1], 0.65)
    for side in (-1, 1):
        shape = ((center[0] + side * 3, 23), (center[0] + side * 12, 14),
                 (center[0] + side * 8, 6), (center[0] + side * 7, 16))
        polygon(layer, shape, (171, 51, 101, round(220 * pulse)))
        pygame.draw.aaline(layer, (225, 133, 177, round(220 * pulse)), shape[0], shape[1])
    polygon(layer, ((center[0], 11), (center[0] + 3, 18), (center[0], 25), (center[0] - 3, 18)),
            (179, 99, 192, 235))
    for index in range(3):
        angle = now / 600 + index * math.tau / 3
        point = center[0] + math.cos(angle) * 17, center[1] + math.sin(angle) * 8
        spark(layer, point, (-math.sin(angle), math.cos(angle)), PACT[2], 0.55, 1)
    if font is not None:
        text = font.render(str(turns), True, (217, 176, 197))
        layer.blit(text, (round(center[0] - text.get_width() / 2), 30))
    surface.blit(layer, (round(position[0] - 16), round(position[1] - 35)))


def draw_madness_cast(surface, origin_position, target_position, phase):
    size = ACT_THREE_TILE_SIZE
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    source = origin_position[0] + size / 2, origin_position[1] + size / 2
    target = target_position[0] + size / 2, target_position[1] + size * 0.3
    _soul_thread(layer, source, target, phase, PACT)
    mist(layer, target, 20, PACT[1], envelope(phase) * 0.65)
    surface.blit(layer, (0, 0))


def draw_demon_rune_aura(surface, player, position, now, transform_phase=None):
    rune = player.act_three.warlock_demon_rune
    if rune not in ("rune_of_eternal_form", "rune_of_blood_pact"):
        return False
    if (transform_phase is None and player.warlock_demon_form_target_active is not None
            and 0 <= now - player.warlock_demon_form_started_at < WARLOCK_DEMON_FORM_TRANSFORM_MS):
        return True
    size = ACT_THREE_TILE_SIZE
    extent = size * 3
    layer = pygame.Surface((extent, extent), pygame.SRCALPHA)
    center = extent / 2, extent * 0.69
    palette = PACT if rune == "rune_of_blood_pact" else VOID
    heat = min(1, player.act_three.warlock_blood_attacks / 9) if palette == PACT else 0.3
    strength = envelope(transform_phase) ** 0.65 if transform_phase is not None else 0.65 + heat * 0.3
    for side in (-1, 1):
        for index in range(9):
            phase = (now / (1800 - heat * 500) + index / 9 + side * 0.15) % 1
            x = center[0] + side * size * (0.3 + math.sin(phase * 4 + index) * 0.09)
            y = center[1] - phase * size * 0.95
            mist(layer, (x, y), size * (0.19 + phase * 0.09), palette[0], envelope(phase) * strength)
            mist(layer, (x, y + 4), size * 0.16, palette[1], envelope(phase) * strength * 0.75)
            if index % 3 == 0:
                spark(layer, (x, y), (-side * 0.15, -0.7), palette[2], envelope(phase) * strength * 0.8, 2)
        angle = -0.4 if side > 0 else math.pi + 0.4
        crescent(layer, (center[0] + side * size * 0.08, center[1] - size * 0.36), size * 0.46,
                 angle + math.sin(now / 1600) * 0.12, 1.5, size * 0.13, strength * 0.65, palette, flatten=1.1)
    if transform_phase is not None:
        for index in range(15):
            angle = index * 2.399
            radius = size * (0.85 * (1 - transform_phase) + 0.12)
            point = (center[0] + math.cos(angle) * radius,
                     center[1] - size * 0.3 + math.sin(angle) * radius * 0.8)
            spark(layer, point, (-math.cos(angle), -math.sin(angle)), palette[2], strength * 0.8, 3)
    elif palette == PACT:
        phase = (now - player.act_three.warlock_last_demon_attack_at) / 400
        if 0 < phase < 1:
            mist(layer, (center[0], center[1] - size * 0.35), size * 0.36, palette[1], envelope(phase) * 0.65)
            for side in (-1, 1):
                crescent(layer, center, size * (0.32 + phase * 0.3), phase * math.pi + (math.pi if side < 0 else 0),
                         1.5, size * 0.12, envelope(phase) * 0.75, palette)
    surface.blit(layer, (round(position[0] + size / 2 - center[0]),
                         round(position[1] + size * 0.83 - center[1])))
    return True


def draw_warlock_rune_links(surface, player, position, camera_x, camera_y, now):
    size = ACT_THREE_TILE_SIZE
    if not any(0 <= now - entry[-1] < 900 for entry in (
            *player.act_three.warlock_curse_transfers, *player.act_three.warlock_madness_attacks)):
        return
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for x1, y1, x2, y2, started in player.act_three.warlock_curse_transfers:
        phase = (now - started) / 800
        if 0 < phase < 1:
            _soul_thread(layer, ((x1 + 0.5) * size - camera_x, (y1 + 0.4) * size - camera_y),
                         ((x2 + 0.5) * size - camera_x, (y2 + 0.4) * size - camera_y), phase)
    for x1, y1, x2, y2, started in player.act_three.warlock_madness_attacks:
        phase = (now - started) / 420
        if 0 < phase < 1:
            source = (x1 + 0.5) * size - camera_x, (y1 + 0.5) * size - camera_y
            target = (x2 + 0.5) * size - camera_x, (y2 + 0.5) * size - camera_y
            _soul_thread(layer, source, target, phase, PACT)
            crescent(layer, target, size * 0.28, math.atan2(y2 - y1, x2 - x1) + phase,
                     1.8, size * 0.15, envelope(phase), PACT, flatten=0.85)
    surface.blit(layer, (0, 0))
