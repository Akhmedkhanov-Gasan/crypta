import math

import pygame

from acts.act_three.presentation.berserker.effect_brushes import mist
from presentation.layout import ACT_THREE_TILE_SIZE


def draw_soul_devourer_aura(surface, position, spirit, now):
    if not spirit["devourer"] or spirit["souls"] <= 0:
        return
    souls = spirit["souls"]
    power = 1 - math.exp(-souls / 5)
    margin = 60
    size = ACT_THREE_TILE_SIZE + margin * 2
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size / 2, size / 2
    radius = 27 + power * 18
    pulse = 0.5 + 0.5 * math.sin(now / 1000)
    mist(layer, (cx, cy + 7), 30 + power * 6, (15, 111, 126), 0.2 + power * 0.25)
    for side in (-1, 1):
        points = []
        for index in range(57):
            progress = index / 56
            angle = progress * math.pi * 1.3 + now / 3100 + side
            x = cx + side * (radius * (0.65 + math.sin(progress * math.pi) * 0.35)) + math.sin(angle) * 5
            y = cy + 31 - progress * (62 + power * 15)
            points.append((round(x), round(y)))
        for index in range(len(points) - 1):
            fade = math.sin((index + 0.5) / 56 * math.pi)
            pygame.draw.line(layer, (21, 143, 159, round((35 + power * 30) * fade)), points[index], points[index + 1], 6 + round(power * 6))
            pygame.draw.line(layer, (72, 215, 212, round((65 + power * 50) * fade)), points[index], points[index + 1], 2 + round(power * 2))
            pygame.draw.aaline(layer, (183, 255, 237, round((115 + power * 80) * fade)), points[index], points[index + 1])
    for index in range(2 + min(4, souls // 2)):
        rx = round(radius + index * 3)
        ring = pygame.Rect(round(cx - rx), round(cy + 17 - index), rx * 2, 18 + index * 3)
        angle = now / 4300 + index * 1.9
        pygame.draw.arc(layer, (98, 231, 218, round(95 + power * 65)), ring, angle, angle + 2.15, 2)
        pygame.draw.arc(layer, (45, 155, 179, round(65 + power * 55)), ring.inflate(4, 4), angle + math.pi, angle + math.pi + 1.4, 2)
    crown_radius = round(11 + power * 7)
    crown = pygame.Rect(round(cx - crown_radius), round(cy - 36 - power * 7), crown_radius * 2, 12)
    for index in range(2 + min(4, souls)):
        angle = index * math.tau / (2 + min(4, souls)) - now / 5800
        pygame.draw.arc(layer, (161, 252, 231, round(125 + pulse * 45 + power * 40)), crown, angle, angle + 0.7, 2)
    for index in range(6 + min(16, souls * 2)):
        phase = (now / (4200 + index % 3 * 350) + index * 0.173) % 1
        angle = index * 2.399 + now / 9500
        x = cx + math.cos(angle) * radius * (0.7 + phase * 0.25)
        y = cy + 29 - phase * (61 + power * 20)
        alpha = round(math.sin(phase * math.pi) ** 2 * (120 + power * 95))
        point = round(x), round(y)
        pygame.draw.circle(layer, (45, 177, 187, alpha // 5), point, 4)
        pygame.draw.circle(layer, (177, 255, 235, alpha), point, 1 + (index % 5 == 0 and souls >= 4))
    surface.blit(layer, (round(position[0] - margin), round(position[1] - margin)))


def draw_soul_feast(surface, position, spirit, camera_x, camera_y, now):
    elapsed = now - spirit["soul_at"]
    origin = spirit.get("soul_origin")
    if not spirit["devourer"] or origin is None or not 0 <= elapsed < 1100:
        return
    tile = ACT_THREE_TILE_SIZE
    start = (origin[0] + 0.5) * tile - camera_x, (origin[1] + 0.5) * tile - camera_y
    end = position[0] + tile / 2, position[1] + tile * 0.42
    left = math.floor(min(start[0], end[0]) - 40)
    top = math.floor(min(start[1], end[1]) - 75)
    width = math.ceil(abs(start[0] - end[0]) + 80)
    height = math.ceil(abs(start[1] - end[1]) + 115)
    layer = pygame.Surface((width, height), pygame.SRCALPHA)
    life = elapsed / 1100
    for index in range(14):
        progress = max(0, min(1, life * 1.65 - index * 0.027))
        fade = math.sin(progress * math.pi)
        if fade <= 0:
            continue
        curve = math.sin(progress * math.pi)
        x = start[0] + (end[0] - start[0]) * progress + math.sin(index * 2.399 + progress * 4) * curve * 10
        y = start[1] + (end[1] - start[1]) * progress - curve * (20 + index % 4 * 5)
        point = round(x - left), round(y - top)
        mist(layer, point, 8 + index % 3, (27, 168, 176), fade * 0.65)
        pygame.draw.circle(layer, (190, 255, 234, round(240 * fade)), point, 2)
    if life > 0.25:
        wave = (life - 0.25) / 0.75
        radius = 9 + round(wave * 39)
        ring = pygame.Rect(round(end[0] - left - radius), round(end[1] - top - radius * 0.6), radius * 2, round(radius * 1.2))
        pygame.draw.ellipse(layer, (132, 252, 220, round(180 * math.sin(wave * math.pi))), ring, 2)
    surface.blit(layer, (left, top))
