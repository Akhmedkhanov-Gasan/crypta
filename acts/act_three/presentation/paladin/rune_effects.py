import math

import pygame

from acts.act_three.abilities.paladin_runes import crusade_active
from acts.act_three.presentation.berserker.effect_brushes import crescent, envelope, mist, polygon, spark
from presentation.layout import ACT_THREE_TILE_SIZE


IRON = ((27, 26, 34), (113, 100, 81), (228, 211, 166))
FAITH = ((31, 23, 36), (139, 104, 83), (243, 214, 164))


def _faith_currents(layer, center, size, time, strength):
    for side in (-1, 1):
        for index in range(5):
            phase = (time / 1450 + index / 5 + side * 0.13) % 1
            opacity = envelope(phase) * strength
            x = center[0] + side * size * (0.42 - phase * 0.2)
            y = center[1] - phase * size * 0.85
            mist(layer, (x, y), size * (0.16 + phase * 0.08), FAITH[0], opacity * 0.8)
            mist(layer, (x, y), size * 0.15, FAITH[1], opacity * 0.55)
            spark(layer, (x + math.sin(phase * 6 + index) * 3, y), (-side * 0.18, -0.7),
                  FAITH[2], opacity * 0.8, 2)
    for index in range(2):
        angle = time / 1700 + index * math.pi
        crescent(layer, (center[0], center[1] - size * 0.35), size * 0.38,
                 angle, 1.35, size * 0.1, strength * 0.35, FAITH, flatten=0.9)


def draw_crusade_activation(surface, position, elapsed, duration, size):
    phase = elapsed / duration
    if not 0 <= phase < 1:
        return
    extent = size * 3
    layer = pygame.Surface((extent, extent), pygame.SRCALPHA)
    center = extent / 2, extent * 0.68
    strength = envelope(phase) ** 0.65
    _faith_currents(layer, center, size, elapsed * 1.5, strength)
    for index in range(18):
        travel = (phase * 1.8 + index / 18) % 1
        angle = index * 2.399 + phase
        radius = size * (0.9 * (1 - travel) + 0.08)
        x = center[0] + math.cos(angle) * radius
        y = center[1] - size * 0.35 + math.sin(angle) * radius * 0.65
        spark(layer, (x, y), (-math.cos(angle), -math.sin(angle)), FAITH[2],
              envelope(travel) * strength * 0.85, 3)
    mist(layer, (center[0], center[1] - size * 0.4), size * 0.38, FAITH[1], strength * 0.6)
    surface.blit(layer, (round(position[0] + size / 2 - center[0]),
                         round(position[1] + size * 0.82 - center[1])))


def draw_paladin_rune_effects(surface, player, position, camera_x, camera_y, now):
    size = ACT_THREE_TILE_SIZE
    if crusade_active(player):
        extent = size * 3
        layer = pygame.Surface((extent, extent), pygame.SRCALPHA)
        center = extent / 2, extent * 0.68
        _faith_currents(layer, center, size, now, 0.85)
        attack_phase = (now - player.attack_animation_started_at) / 280
        if 0 <= attack_phase < 1:
            crescent(layer, (center[0], center[1] - size * 0.3), size * 0.61,
                     attack_phase * 3.1, 1.9, size * 0.16, envelope(attack_phase), FAITH)
        surface.blit(layer, (round(position[0] + size / 2 - center[0]),
                             round(position[1] + size * 0.82 - center[1])))
    block_phase = (now - player.act_three.paladin_rune_block_started_at) / 520
    if player.act_three.paladin_rune_block_started_at >= 0 and 0 <= block_phase < 1:
        layer = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        x, y = size, size
        opacity = envelope(block_phase) ** 0.6
        shape = ((x - 14, y - 20), (x, y - 25), (x + 14, y - 20),
                 (x + 11, y + 3), (x, y + 17), (x - 11, y + 3))
        polygon(layer, shape, (35, 32, 41, round(150 * opacity)))
        polygon(layer, (shape[0], shape[1], (x, y + 12), shape[-1]), (164, 146, 112, round(145 * opacity)))
        pygame.draw.aalines(layer, (228, 211, 166, round(220 * opacity)), True, shape)
        for index in range(9):
            angle = index * 2.399
            point = (x + math.cos(angle) * size * block_phase * 0.55,
                     y + math.sin(angle) * size * block_phase * 0.45 - 4)
            spark(layer, point, (math.cos(angle), math.sin(angle)), IRON[2], opacity * 0.85, 3)
        surface.blit(layer, (round(position[0] - size * 0.5), round(position[1] - size * 0.45)))
    for column, row, collision, started_at in player.act_three.paladin_ram_impacts:
        phase = (now - started_at) / 480
        if not 0 < phase < 1:
            continue
        layer = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        center = size, size
        opacity = envelope(phase)
        for index in range(12 if collision else 7):
            angle = index * 2.399
            radius = size * phase * (0.7 if collision else 0.45)
            point = (center[0] + math.cos(angle) * radius,
                     center[1] + math.sin(angle) * radius * 0.7 - envelope(phase) * 8)
            mist(layer, point, 11, IRON[0], opacity * 0.5)
            spark(layer, point, (math.cos(angle), math.sin(angle)), IRON[2], opacity * 0.8, 4)
        surface.blit(layer, (round(column * size - camera_x - size / 2),
                             round(row * size - camera_y - size / 2)))
    if player.act_three.paladin_ultimate_rune == "rune_of_redeeming_sanctuary" and player.paladin_sacred_ground_lightnings:
        healing_layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for lightning in player.paladin_sacred_ground_lightnings:
            if lightning.started_at <= 0:
                continue
            phase = (now - lightning.started_at) / 520
            if not 0 < phase < 1:
                continue
            source = ((lightning.target[0] + 0.5) * size - camera_x,
                      (lightning.target[1] + 0.5) * size - camera_y)
            target = position[0] + size * 0.5, position[1] + size * 0.4
            for index in range(4):
                travel = min(1, phase * 1.3 + index * 0.065)
                point = (source[0] + (target[0] - source[0]) * travel,
                         source[1] + (target[1] - source[1]) * travel - math.sin(travel * math.pi) * size * 0.3)
                mist(healing_layer, point, 6, (177, 180, 140), envelope(phase) * 0.5)
                spark(healing_layer, point, (0, -0.2), (224, 218, 178), envelope(phase) * 0.8, 1)
        surface.blit(healing_layer, (0, 0))
