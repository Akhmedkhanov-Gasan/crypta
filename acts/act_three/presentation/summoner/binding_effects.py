import math

import pygame

from acts.act_three.presentation.berserker.effect_brushes import crescent, envelope, mist, polygon, spark
from presentation.layout import ACT_THREE_TILE_SIZE


SPIRIT = ((12, 28, 33), (27, 137, 145), (175, 245, 226))


def spirit_wings(layer, center, size, now, strength):
    spread = 0.9 + math.sin(now / 550) * 0.05
    for side in (-1, 1):
        for index in range(7):
            offset = index / 6
            root = center[0] + side * size * 0.12, center[1] + size * offset * 0.2
            tip = (center[0] + side * size * (0.47 + offset * 0.13) * spread,
                   center[1] - size * (0.48 - offset * 0.59) + math.sin(now / 420 + index) * 2)
            bend = (center[0] + side * size * 0.34, center[1] - size * (0.3 - offset * 0.45))
            mist(layer, tip, size * 0.12, SPIRIT[1], strength * 0.32)
            polygon(layer, (root, (bend[0], bend[1] - size * 0.06), tip,
                            (bend[0], bend[1] + size * 0.08)), (*SPIRIT[0], round(170 * strength)))
            polygon(layer, (root, bend, tip, (bend[0], bend[1] + size * 0.035)),
                    (46, 159 + index * 5, 162 + index * 5, round(100 * strength)))
            pygame.draw.aaline(layer, (*SPIRIT[2], round(125 * strength)), bend, tip)


def draw_absorption_effect(surface, game_state, position, camera_x, camera_y, now):
    player = game_state.player
    state = player.act_three
    if state.summoner_absorption_attacks <= 0:
        return
    size = ACT_THREE_TILE_SIZE
    layer = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
    center = size * 1.5, size * 1.45
    spirit_wings(layer, center, size, now, 0.65)
    for index in range(16):
        phase = (now / 1500 + index / 16) % 1
        angle = index * 2.399 + phase * 1.1
        point = (center[0] + math.cos(angle) * size * (0.3 + phase * 0.12),
                 center[1] + size * (0.6 - phase * 1.1))
        mist(layer, point, 9, SPIRIT[0], envelope(phase) * 0.6)
        if index % 3 == 0:
            spark(layer, point, (0.15, -0.9), SPIRIT[2], envelope(phase) * 0.7, 2)
    crescent(layer, (center[0], center[1] + size * 0.47), size * 0.37,
             now / 1300, 3.5, 5, 0.65, SPIRIT, flatten=0.32)
    surface.blit(layer, (round(position[0] + size / 2 - center[0]),
                         round(position[1] + size * 0.4 - center[1])))
    elapsed = now - state.summoner_rune_started_at
    origin = state.summoner_absorption_origin
    if origin is None or not 0 <= elapsed < 800:
        return
    progress = elapsed / 800
    start = (origin[0] + 0.5) * size - camera_x, (origin[1] + 0.5) * size - camera_y
    destination = position[0] + size / 2, position[1] + size * 0.4
    for index in range(22):
        phase = max(0, min(1, progress * 1.65 - index / 36))
        amount = phase * phase * (3 - 2 * phase)
        angle = phase * math.tau * 1.5 + index * 2.399
        radius = (1 - phase) * size * 0.38
        point = (start[0] + (destination[0] - start[0]) * amount + math.cos(angle) * radius,
                 start[1] + (destination[1] - start[1]) * amount + math.sin(angle) * radius * 0.5)
        glow = pygame.Surface((48, 48), pygame.SRCALPHA)
        mist(glow, (24, 24), 19, SPIRIT[0], envelope(progress) * 0.8)
        mist(glow, (24, 24), 10, SPIRIT[1], envelope(progress) * 0.8)
        spark(glow, (24, 24), (math.cos(angle), math.sin(angle)), SPIRIT[2], envelope(progress), 3)
        surface.blit(glow, (round(point[0] - 24), round(point[1] - 24)))


def draw_familiar_recall(surface, game_state, position, assets, camera_x, camera_y, now):
    state = game_state.player.act_three
    origin = state.summoner_recall_position
    elapsed = now - state.summoner_recall_started_at
    if origin is None or state.summoner_recall_floor != game_state.floor_index or not 0 <= elapsed < 620:
        return
    size = ACT_THREE_TILE_SIZE
    phase = elapsed / 620
    start = (origin[0] + 0.5) * size - camera_x, (origin[1] + 0.65) * size - camera_y
    destination = position[0] + size / 2, position[1] + size * 0.45
    if state.summoner_recall_totem:
        sprite = assets.get("summoner_totem_idle")
        if sprite is not None:
            sprite = sprite.copy()
            sprite.set_alpha(round(255 * (1 - min(1, phase * 2.3)) ** 2))
            surface.blit(sprite, (round(start[0] - size / 2), round(start[1] - size * 0.65)))
    for index in range(16):
        offset = index / 24
        travel = max(0, min(1, phase * 1.65 - offset))
        angle = index * 2.399 + phase * 5
        swirl = size * 0.32 * (1 - travel)
        point = (start[0] + (destination[0] - start[0]) * travel + math.cos(angle) * swirl,
                 start[1] + (destination[1] - start[1]) * travel - math.sin(travel * math.pi) * size * 0.5
                 + math.sin(angle) * swirl * 0.45)
        layer = pygame.Surface((56, 56), pygame.SRCALPHA)
        opacity = envelope(phase) * (0.6 + index % 3 * 0.15)
        mist(layer, (28, 28), 20, SPIRIT[0], opacity)
        mist(layer, (28, 28), 11, SPIRIT[1], opacity * 0.7)
        spark(layer, (28, 28), (math.cos(angle), -0.6), SPIRIT[2], opacity, 3)
        surface.blit(layer, (round(point[0] - 28), round(point[1] - 28)))


def draw_possession_aura(surface, position, width, height, now):
    size = ACT_THREE_TILE_SIZE
    margin = 20
    layer_size = (width * size + margin * 2, height * size + margin * 2)
    scale = 2
    layer = pygame.Surface((layer_size[0] * scale, layer_size[1] * scale), pygame.SRCALPHA)
    cx = margin + width * size / 2
    floor_y = margin + height * size - 8
    radius = width * size * 0.32
    oval = pygame.Rect(round((cx - radius) * scale), round((floor_y - 5) * scale),
                       round(radius * 2 * scale), 10 * scale)
    pulse = 0.5 + 0.5 * math.sin(now / 900)
    pygame.draw.ellipse(layer, (26, 119, 130, round(23 + pulse * 14)), oval.inflate(12 * scale, 6 * scale))
    for angle in (0.3 + now / 4900, 3.5 + now / 4900):
        pygame.draw.arc(layer, (110, 224, 208, round(115 + pulse * 45)), oval, angle, angle + 2.1, 2 * scale)
    ribbon_height = min(height * size * 0.76, 110)
    for side in (-1, 1):
        points = []
        for index in range(49):
            progress = index / 48
            sway = math.sin(progress * math.tau * 0.9 + now / 1400 + side) * 5
            x = cx + side * (width * size * (0.27 + 0.08 * math.sin(progress * math.pi)) + sway)
            y = floor_y - progress * ribbon_height
            points.append((round(x * scale), round(y * scale)))
        for index in range(len(points) - 1):
            visibility = math.sin((index + 0.5) / 48 * math.pi)
            pygame.draw.line(layer, (35, 151, 161, round(35 * visibility)), points[index], points[index + 1], 7 * scale)
            pygame.draw.line(layer, (69, 200, 193, round(65 * visibility)), points[index], points[index + 1], 3 * scale)
            pygame.draw.aaline(layer, (158, 244, 225, round(150 * visibility)), points[index], points[index + 1])
    for index in range(7):
        phase = (now / 3000 + index * 0.17) % 1
        opacity = math.sin(phase * math.pi) ** 2
        side = -1 if index % 2 == 0 else 1
        x = cx + side * (width * size * 0.35 + math.sin(phase * math.pi) * 3)
        y = floor_y - phase * ribbon_height
        point = (round(x * scale), round(y * scale))
        pygame.draw.circle(layer, (47, 160, 163, round(35 * opacity)), point, 5 * scale)
        pygame.draw.circle(layer, (107, 214, 203, round(90 * opacity)), point, 2 * scale)
        pygame.draw.circle(layer, (189, 255, 235, round(200 * opacity)), point, scale)
    layer = pygame.transform.smoothscale(layer, layer_size)
    surface.blit(layer, (round(position[0] - margin), round(position[1] - margin)))
