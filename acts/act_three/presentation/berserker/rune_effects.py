import math

import pygame

from acts.act_three.rune_master.definitions import DEVASTATION_ANIMATION_MS, SECOND_WIND_CAP
from acts.act_three.presentation.berserker.effect_brushes import (
    ASH, BLOOD, crescent, draw_storm, envelope, mist, polygon, shock_dust, spark,
)
from presentation.layout import ACT_THREE_TILE_SIZE


def draw_spin_sweep(surface, position, camera_x, camera_y, phase, size, devastation=False):
    opacity = envelope(phase) ** 0.6
    if opacity <= 0:
        return
    extent = size * (4 if devastation else 3)
    layer = pygame.Surface((extent, extent), pygame.SRCALPHA)
    center = extent / 2, extent / 2
    radius = size * ((0.65 + 0.8 * (1 - (1 - phase) ** 3)) if devastation else 0.66)
    angle = phase * math.tau * (1.4 if devastation else 2.1)
    shock_dust(layer, center, size, phase, opacity * (0.9 if devastation else 0.45))
    for side in (0, math.pi):
        for trail in (2, 1, 0):
            crescent(layer, center, radius - trail * 4, angle + side - trail * 0.15,
                     2.9, size * (0.32 if devastation else 0.24), opacity * (0.16 if trail else 0.95))
    if devastation:
        neighbors = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
        for index, (dx, dy) in enumerate(neighbors):
            local = (phase - index * 0.025) / 0.72
            visibility = envelope(local) * opacity
            point = center[0] + dx * size, center[1] + dy * size
            angle = math.atan2(dy, dx) + local * 1.1
            crescent(layer, point, size * 0.3, angle, 1.7,
                     size * 0.21, visibility * 0.85, flatten=0.8)
            mist(layer, point, size * 0.26, BLOOD[0], visibility * 0.65)
    surface.blit(layer, (round(position[0] - camera_x + size * 0.5 - center[0]),
                         round(position[1] - camera_y + size * 0.74 - center[1])))


def draw_devastation(surface, position, camera_x, camera_y, elapsed, size):
    if 0 <= elapsed < DEVASTATION_ANIMATION_MS:
        draw_spin_sweep(surface, position, camera_x, camera_y,
                        elapsed / DEVASTATION_ANIMATION_MS, size, devastation=True)


def _draw_blood_cuts(surface, player, camera_x, camera_y, now, size):
    for column, row, started_at in player.act_three.berserker_blood_cuts:
        phase = (now - started_at - 140) / 480
        if not 0 < phase < 1:
            continue
        layer = pygame.Surface((size, size), pygame.SRCALPHA)
        opacity = envelope(phase) ** 0.7
        for index in range(2):
            x, y = size * (0.39 + index * 0.14), size * 0.43
            length = size * (0.19 + min(1, phase * 4) * 0.12)
            points = ((x - length * 0.65, y + length), (x - 1, y - 2),
                      (x + length * 0.7, y - length), (x + 2, y + 3))
            mist(layer, (x, y), size * 0.16, BLOOD[1], opacity * 0.35)
            polygon(layer, points, (141, 27, 43, round(200 * opacity)))
            pygame.draw.aaline(layer, (229, 145, 121, round(205 * opacity)), points[0], points[2])
            for drop in range(4):
                spread = (drop - 1.5) * size * 0.07
                point = x + spread + phase * spread, y + phase * (9 + drop * 4)
                pygame.draw.circle(layer, (131, 20, 36, round(180 * opacity)),
                                   (round(point[0]), round(point[1])), 1)
        surface.blit(layer, (round(column * size - camera_x), round(row * size - camera_y)))


def draw_rage_aura(surface, position, now, strength=1.0, palette=BLOOD, stored=0.0, release=None):
    size = ACT_THREE_TILE_SIZE
    extent = size * 3
    layer = pygame.Surface((extent, extent), pygame.SRCALPHA)
    center = extent / 2, extent * 0.7
    draw_storm(layer, center, size, now, strength, palette, stored)
    if release is not None:
        opacity = envelope(release)
        for index in range(14):
            angle = index * 2.399 + release * 0.6
            radius = size * (0.7 * (1 - release) + 0.08)
            point = (center[0] + math.cos(angle) * radius,
                     center[1] - size * 0.3 + math.sin(angle) * radius * 0.7)
            spark(layer, point, (-math.cos(angle), -math.sin(angle)), palette[2], opacity * 0.9, 2)
        mist(layer, (center[0], center[1] - size * 0.3), size * 0.36, palette[1], opacity * 0.4)
    surface.blit(layer, (round(position[0] + size / 2 - center[0]),
                         round(position[1] + size * 0.83 - center[1])))


def draw_berserker_rune_effects(surface, player, player_position, camera_x, camera_y, now):
    _draw_blood_cuts(surface, player, camera_x, camera_y, now, ACT_THREE_TILE_SIZE)
    rune = player.act_three.berserker_rage_rune
    active = player.berserker_last_rage_hits > 0
    release = (now - player.act_three.berserker_rage_released_at) / 650
    releasing = player.act_three.berserker_rage_released_at >= 0 and 0 <= release < 1
    if rune not in ("rune_of_second_wind", "rune_of_death_wish") or not (active or releasing):
        return False
    palette = ASH if rune == "rune_of_second_wind" else BLOOD
    stored = min(1, player.act_three.berserker_deferred_healing / max(1, player.max_health * SECOND_WIND_CAP))
    activation = max(0.0, min(1.0, (now - player.berserker_last_rage_started_at) / 350))
    strength = (0.75 + stored * 0.25) * (0.12 + activation * 0.88) if active else (1 - release) * 0.8
    draw_rage_aura(surface, player_position, now, strength, palette, stored,
                   release if releasing and not active and palette == ASH else None)
    return active
