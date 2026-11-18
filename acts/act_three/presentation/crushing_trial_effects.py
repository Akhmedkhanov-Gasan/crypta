import math
from functools import lru_cache

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.piercing_trial_effects import center, glow
from acts.act_three.presentation.ability_unlock_banner import draw_unlock_banner


@lru_cache(maxsize=1)
def fissures():
    paths = []
    for index in range(9):
        angle = index * 2.399
        points = [(0, 0)]
        for step in range(1, 6):
            radius = step * (.13 + (index % 3) * .015)
            bend = angle + math.sin(index * 7 + step * 3) * .24
            points.append((math.cos(bend) * radius, math.sin(bend) * radius * .45))
        paths.append(points)
    return paths


def draw_completion(context, trial, now):
    elapsed = now - trial["completed"]
    if not 0 <= elapsed < 4400:
        return
    surface = context.view_surface
    size = ACT_THREE_TILE_SIZE
    px, py = center(context, trial["completion_origin"])
    py += size * .29
    energy = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    darkness = max(0, min(1, elapsed / 450, (3400 - elapsed) / 1300))
    energy.fill((12, 5, 4, round(58 * darkness)))
    for number, cell in enumerate(trial["plates"]):
        sx, sy = center(context, cell)
        for index in range(4):
            progress = (elapsed - number * 35 - index * 100) / 1050
            if not 0 < progress < 1:
                continue
            t = progress * progress * (3 - 2 * progress)
            x = sx + (px - sx) * t
            y = sy + (py - sy) * t - math.sin(progress * math.pi) * size * .5
            alpha = round(205 * math.sin(progress * math.pi))
            pygame.draw.line(energy, (177, 99, 62, alpha), (x, y), (x - (px - sx) * .018, y + 4), 2)
            pygame.draw.circle(energy, (232, 165, 101, alpha), (round(x), round(y)), 1)
    impact = elapsed - 1350
    if 0 <= impact < 2400:
        progress = impact / 2400
        strength = (1 - progress) ** 1.6
        aura = glow(size, (162, 62, 31))
        aura.set_alpha(round(220 * strength))
        energy.blit(aura, (round(px - size), round(py - size * 1.3)))
        reveal = min(1, impact / 240)
        for points in fissures():
            visible = max(2, min(len(points), round(2 + reveal * 4)))
            vertices = [(px + x * size, py + y * size) for x, y in points[:visible]]
            pygame.draw.lines(energy, (67, 28, 20, round(190 * strength)), False, vertices, 5)
            pygame.draw.lines(energy, (180, 85, 45, round(220 * strength)), False, vertices, 2)
            pygame.draw.lines(energy, (235, 166, 98, round(165 * strength)), False, vertices, 1)
        for index in range(36):
            t = (impact - (index % 6) * 35) / 1700
            if not 0 < t < 1:
                continue
            angle = index * 2.399
            distance = size * (.18 + index % 7 * .085) * (1 - (1 - t) ** 3)
            x = px + math.cos(angle) * distance
            y = py + math.sin(angle) * distance * .4 - math.sin(t * math.pi) * size * (.12 + index % 4 * .08)
            alpha = round(190 * (1 - t) ** 1.5)
            radius = 2 + index % 3
            pygame.draw.circle(energy, (65, 53, 46, round(alpha * .4)), (round(x), round(y + 4)), radius * 3)
            color = (194, 105, 60, alpha) if index % 4 == 0 else (102, 88, 74, alpha)
            pygame.draw.polygon(energy, color, [(x - radius, y), (x, y - radius * 1.5), (x + radius, y + radius), (x - radius * .5, y + radius)])
    surface.blit(energy, (0, 0))
    banner_elapsed = elapsed - 850
    draw_unlock_banner(surface, banner_elapsed, "CRUSHING LEAP", (235, 185, 139), (192, 114, 83), (28, 12, 10))
    if 0 <= banner_elapsed < 3400:
        alpha = round(200 * max(0, min(1, banner_elapsed / 320, (3400 - banner_elapsed) / 700)))
        ornament = pygame.Surface((min(surface.get_width(), 420), 92), pygame.SRCALPHA)
        middle = ornament.get_width() // 2
        for side in (-1, 1):
            points = [(middle + side * 28, 85), (middle + side * 52, 81), (middle + side * 142, 81), (middle + side * 180, 72)]
            pygame.draw.lines(ornament, (150, 85, 55, alpha), False, points, 1)
        pygame.draw.polygon(ornament, (208, 132, 84, alpha), [(middle, 78), (middle + 5, 84), (middle, 90), (middle - 5, 84)])
        surface.blit(ornament, ((surface.get_width() - ornament.get_width()) // 2, 24))
