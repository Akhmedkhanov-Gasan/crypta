import math

import pygame

from acts.act_three.presentation.berserker.effect_brushes import crescent, envelope, mist, polygon, spark
from acts.act_three.rune_master.definitions import CATACLYSM_RADIUS
from presentation.layout import ACT_THREE_TILE_SIZE


SPIRIT = ((15, 30, 35), (25, 111, 119), (153, 232, 221))


def draw_totem_aura(surface, position, player, now):
    size = ACT_THREE_TILE_SIZE
    layer = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    center = size, size * 0.88
    pulse = 0.45 + 0.15 * math.sin(now / 310)
    mist(layer, center, size * 0.3, SPIRIT[1], pulse)
    for index in range(5):
        phase = (now / 1700 + index / 5) % 1
        point = (center[0] + math.sin(index * 2.4 + phase * 3) * size * 0.17,
                 center[1] + size * 0.24 - phase * size * 0.52)
        spark(layer, point, (0, -0.4), SPIRIT[2], envelope(phase) * 0.55, 1)
    surface.blit(layer, (round(position[0] - size / 2), round(position[1] - size * 0.45)))


def draw_possession_mark(surface, position, width, now, actions, font=None):
    size = ACT_THREE_TILE_SIZE
    layer = pygame.Surface((width * size + 32, size + 40), pygame.SRCALPHA)
    center = layer.get_width() / 2, 17
    mist(layer, center, 19, SPIRIT[1], 0.65)
    for side in (-1, 1):
        wing = ((center[0], center[1] + 4), (center[0] + side * 16, center[1] - 5),
                (center[0] + side * 11, center[1] + 6), (center[0] + side * 5, center[1] + 8))
        polygon(layer, wing, (49, 143, 148, 210))
        pygame.draw.aaline(layer, (166, 236, 222, 235), wing[0], wing[1])
    polygon(layer, ((center[0], 8), (center[0] + 4, 17), (center[0], 25), (center[0] - 4, 17)), (159, 223, 209, 235))
    if font is not None:
        text = font.render(str(actions), True, (157, 226, 214))
        layer.blit(text, (round(center[0] - text.get_width() / 2), 30))
    surface.blit(layer, (round(position[0] - 16), round(position[1] - 35)))


def draw_summoner_rune_effects(surface, game_state, position, camera_x, camera_y, now):
    player = game_state.player
    size = ACT_THREE_TILE_SIZE
    if player.act_three.summoner_absorption_attacks > 0:
        layer = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
        center = size * 1.5, size * 1.95
        for side in (-1, 1):
            for index in range(6):
                phase = (now / 1600 + index / 6 + side * 0.1) % 1
                x = center[0] + side * size * (0.28 + math.sin(phase * 5 + index) * 0.08)
                y = center[1] - phase * size * 0.85
                mist(layer, (x, y), size * 0.2, SPIRIT[0], envelope(phase) * 0.7)
                mist(layer, (x, y), size * 0.15, SPIRIT[1], envelope(phase) * 0.55)
                if index % 2 == 0:
                    spark(layer, (x, y), (-side * 0.2, -0.5), SPIRIT[2], envelope(phase) * 0.75, 2)
            crescent(layer, (center[0], center[1] - size * 0.35), size * 0.42,
                     (0 if side > 0 else math.pi) + math.sin(now / 1100) * 0.2,
                     1.5, size * 0.12, 0.4, SPIRIT, flatten=0.95)
        surface.blit(layer, (round(position[0] + size / 2 - center[0]),
                             round(position[1] + size * 0.82 - center[1])))
    familiar = player.summoner_familiar_position
    if player.summoner_true_form_active and player.act_three.summoner_ultimate_rune == "rune_of_cataclysm" and familiar is not None:
        layer = pygame.Surface((size * 6, size * 6), pygame.SRCALPHA)
        center = size * 3, size * 3
        for dy in range(-CATACLYSM_RADIUS, CATACLYSM_RADIUS + 1):
            for dx in range(-CATACLYSM_RADIUS, CATACLYSM_RADIUS + 1):
                if max(abs(dx), abs(dy)) != CATACLYSM_RADIUS:
                    continue
                pulse = 0.18 + 0.09 * math.sin(now / 300 + dx + dy * 1.7)
                point = center[0] + dx * size, center[1] + dy * size
                mist(layer, point, 13, (130, 43, 59), pulse)
        surface.blit(layer, (round((familiar[0] + 0.5) * size - camera_x - center[0]),
                             round((familiar[1] + 0.6) * size - camera_y - center[1])))
    origin = player.act_three.summoner_cataclysm_position
    elapsed = now - player.act_three.summoner_cataclysm_started_at
    if origin is None or not 0 <= elapsed < 850:
        return
    phase = elapsed / 850
    opacity = envelope(phase) ** 0.6
    extent = size * 7
    layer = pygame.Surface((extent, extent), pygame.SRCALPHA)
    center = extent / 2, extent / 2
    radius = size * (0.3 + 2.35 * (1 - (1 - phase) ** 3))
    for index in range(3):
        crescent(layer, center, radius - index * 6, phase * 3 + index * math.tau / 3,
                 2.4, size * 0.3, opacity * (0.8 - index * 0.15), SPIRIT, flatten=0.65)
    for index in range(32):
        angle = index * 2.399
        distance = size * phase * (1.4 + index % 4 * 0.3)
        point = (center[0] + math.cos(angle) * distance,
                 center[1] + math.sin(angle) * distance * 0.65 - envelope(phase) * size * 0.35)
        mist(layer, point, 15 + index % 5 * 2, SPIRIT[0], opacity * 0.65)
        if index % 2 == 0:
            spark(layer, point, (math.cos(angle), math.sin(angle)), SPIRIT[2], opacity * 0.9, 5)
    mist(layer, (center[0], center[1] - size * 0.2), size * 0.5, SPIRIT[1], opacity * 0.85)
    if phase < 0.17:
        mist(layer, center, size * 0.28, (222, 255, 237), (1 - phase / 0.17) * 0.95)
    surface.blit(layer, (round((origin[0] + 0.5) * size - camera_x - center[0]),
                         round((origin[1] + 0.6) * size - camera_y - center[1])))
