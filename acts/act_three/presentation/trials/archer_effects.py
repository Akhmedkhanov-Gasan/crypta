import math
from functools import lru_cache

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE


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
    from acts.act_three.presentation.trials.archer_rite import draw_completion as draw_rite

    draw_rite(context, trial, now)
