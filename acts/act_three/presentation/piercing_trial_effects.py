import math
from functools import lru_cache

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.ability_unlock_banner import draw_unlock_banner


def center(context, cell):
    size = ACT_THREE_TILE_SIZE
    return (cell[0] + .5) * size - context.camera_x, (cell[1] + .5) * size - context.camera_y


@lru_cache(maxsize=8)
def glow(size, color):
    image = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    for radius in range(size, 0, -1):
        alpha = round(100 * (1 - radius / size) ** 2)
        pygame.draw.circle(image, (*color, alpha), (size, size), radius)
    return image


def draw_target_effects(context, trial, now):
    size = ACT_THREE_TILE_SIZE
    for impact in trial.get("target_impacts", []):
        elapsed = now - impact["started"]
        if not 0 <= elapsed < 1100:
            continue
        progress = elapsed / 1100
        x, y = center(context, impact["position"])
        image = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
        middle = size * 1.5
        tint = (158, 70, 47) if impact["wrong"] else (139, 165, 105)
        flash = glow(size // 2, tint)
        flash.set_alpha(round(255 * max(0, 1 - elapsed / 260)))
        image.blit(flash, (middle - size // 2, middle - size // 2))
        dx, dy = impact["direction"]
        for index in range(13):
            angle = index * 2.399
            distance = size * (.15 + (index % 5) * .055) * (1 - (1 - progress) ** 3)
            px = middle + math.cos(angle) * distance + dx * size * progress * .12
            py = middle + math.sin(angle) * distance * .5 + dy * size * progress * .08 - math.sin(progress * math.pi) * size * .16
            shard = max(2, round(size * (.025 + .008 * (index % 3))))
            alpha = round(220 * (1 - progress) ** 1.4)
            color = (116, 119, 99, alpha) if index % 3 else (*tint, alpha)
            pygame.draw.polygon(image, color, [(px, py - shard), (px + shard, py + 1), (px - shard * .6, py + shard)])
            pygame.draw.circle(image, (46, 43, 38, round(65 * math.sin(progress * math.pi))), (round(px), round(py + 4)), shard * 2)
        context.view_surface.blit(image, (round(x - middle), round(y - middle)))


def draw_completion(context, trial, now):
    if trial["phase"] != "complete":
        return
    elapsed = now - trial["completed"]
    if not 0 <= elapsed < 3400:
        return
    size = ACT_THREE_TILE_SIZE
    surface = context.view_surface
    player = (context.floor.player_column, context.floor.player_row)
    px, py = center(context, player)
    energy = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for target in trial["targets"]:
        sx, sy = center(context, target["position"])
        for index in range(6):
            progress = max(0, min(1, (elapsed - 140 - index * 85) / 1100))
            if not 0 < progress < 1:
                continue
            t = progress * progress * (3 - 2 * progress)
            x = sx + (px - sx) * t
            y = sy + (py - sy) * t - math.sin(progress * math.pi) * size * .55
            alpha = round(170 * math.sin(progress * math.pi))
            pygame.draw.line(energy, (151, 173, 111, alpha), (x, y), (x - (px - sx) * .025, y + 5), 2)
    pulse = max(0, 1 - abs(elapsed - 1450) / 850)
    aura = glow(size, (107, 137, 76))
    aura.set_alpha(round(210 * pulse))
    energy.blit(aura, (round(px - size), round(py - size * 1.25)))
    for index in range(16):
        t = max(0, min(1, (elapsed - 1100 - index * 20) / 1350))
        if 0 < t < 1:
            x = px + math.sin(index * 2.399) * size * .35 * (1 - t)
            y = py - size * t * 1.1
            pygame.draw.line(energy, (161, 180, 122, round(155 * math.sin(t * math.pi))), (x, y), (x, y + 5), 2)
    surface.blit(energy, (0, 0))
    draw_unlock_banner(surface, elapsed, "PIERCING SHOT", (208, 216, 174), (158, 171, 136), (10, 15, 12))
