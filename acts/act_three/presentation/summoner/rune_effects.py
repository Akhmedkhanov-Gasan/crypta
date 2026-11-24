import math

import pygame

from acts.act_three.presentation.berserker.effect_brushes import envelope, mist, spark
from acts.act_three.presentation.summoner.binding_effects import draw_absorption_effect, draw_possession_aura
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


def draw_possession_mark(surface, position, width, now, actions=None, font=None, height=1):
    draw_possession_aura(surface, position, width, height, now)
    size = ACT_THREE_TILE_SIZE
    scale = 3
    layer = pygame.Surface((26 * scale, 22 * scale), pygame.SRCALPHA)
    pulse = 0.5 + 0.5 * math.sin(now / 680)
    alpha = round(185 + pulse * 60)
    center = (13 * scale, 11 * scale)
    pygame.draw.circle(layer, (35, 151, 156, 36), center, 10 * scale)
    pygame.draw.circle(layer, (75, 196, 190, 65), center, 7 * scale)
    oval = pygame.Rect(6 * scale, 5 * scale, 14 * scale, 12 * scale)
    pygame.draw.arc(layer, (135, 236, 220, alpha), oval, 0.35, math.pi - 0.35, scale + 1)
    pygame.draw.arc(layer, (87, 200, 194, alpha), oval, math.pi + 0.35, math.tau - 0.35, scale + 1)
    pygame.draw.ellipse(layer, (190, 255, 238, alpha), (12 * scale, 8 * scale, 2 * scale, 6 * scale))
    symbol = pygame.transform.smoothscale(layer, (26, 22))
    surface.blit(symbol, (round(position[0] + width * size / 2 - 13),
                          round(position[1] - 20 + math.sin(now / 950) * 1.5)))


def draw_summoner_rune_effects(surface, game_state, position, camera_x, camera_y, now):
    draw_absorption_effect(surface, game_state, position, camera_x, camera_y, now)
