import math
from functools import lru_cache

import pygame

from acts.act_three.presentation.enemies.lantern_warden.lantern_warden_animation import WARDEN_ATTACK_IMPACT_MS
from acts.act_three.presentation.enemies.lantern_warden.lantern_warden_effects import _firefly_texture
from presentation.layout import ACT_THREE_TILE_SIZE


@lru_cache(maxsize=1)
def _lantern_sprite():
    sprite = pygame.Surface((30, 42), pygame.SRCALPHA)
    pygame.draw.arc(sprite, (115, 117, 67), (9, 2, 12, 14), 0, math.pi, 2)
    pygame.draw.polygon(sprite, (39, 43, 28), ((8, 13), (22, 13), (26, 18), (23, 35), (7, 35), (4, 18)))
    pygame.draw.polygon(sprite, (121, 145, 53, 170), ((9, 18), (21, 18), (20, 32), (10, 32)))
    pygame.draw.polygon(sprite, (223, 230, 135), ((15, 17), (19, 25), (17, 30), (12, 31), (11, 26), (14, 24)))
    pygame.draw.line(sprite, (75, 79, 43), (8, 17), (9, 33), 2)
    pygame.draw.line(sprite, (75, 79, 43), (22, 17), (21, 33), 2)
    pygame.draw.line(sprite, (139, 135, 76), (6, 17), (24, 17), 2)
    pygame.draw.line(sprite, (139, 135, 76), (7, 35), (23, 35), 3)
    return sprite


def draw_soul_procession(context, enemy, current_time):
    preparing = enemy.prepared_attack_mode == "soul_procession" and bool(enemy.attack_targets)
    targets = enemy.attack_targets if preparing else enemy.attack_effect_positions
    if not targets or (not preparing and enemy.attack_effect_mode != "soul_procession"):
        return
    elapsed = current_time - enemy.attack_animation_started_at - WARDEN_ATTACK_IMPACT_MS
    if not preparing and not -WARDEN_ATTACK_IMPACT_MS <= elapsed < 900:
        return
    center = targets[0]
    if not any(cell in context.floor.visible_cells for cell in targets):
        return
    size = ACT_THREE_TILE_SIZE
    surface = context.view_surface
    center_point = ((center[0] + 0.5) * size - context.camera_x, (center[1] + 0.5) * size - context.camera_y)
    effect = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    progress = ((current_time % 1800) / 1800 * 0.22) if preparing else min(1.0, max(0.0, elapsed / 480))
    alpha = 210 if preparing else round(240 * max(0.0, 1 - max(0, elapsed - 480) / 420))
    for index, (dx, dy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        length = max((abs(x - center[0]) for x, y in targets if (x - center[0]) * dx > 0 and (y - center[1]) * dy > 0), default=0)
        if not length:
            continue
        distance = length * (1 - progress)
        point = (center_point[0] + dx * distance * size, center_point[1] + dy * distance * size)
        pygame.draw.line(effect, (116, 143, 55, round(alpha * 0.3)), center_point, point, 2)
        for trail in range(5, -1, -1):
            drift = trail * 0.11
            trail_point = (round(point[0] + dx * size * drift), round(point[1] + dy * size * drift - 15 - math.sin(current_time / 310 + index) * 3))
            glow = _firefly_texture(7).copy()
            weight = round(alpha * (1 - trail / 7))
            glow.fill((weight, weight, weight), special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(glow, glow.get_rect(center=trail_point), special_flags=pygame.BLEND_RGB_ADD)
        lantern = _lantern_sprite().copy()
        lantern.set_alpha(alpha)
        effect.blit(lantern, lantern.get_rect(midbottom=(round(point[0]), round(point[1] - 5))))
    if not preparing and elapsed >= 0:
        radius = max(3, round(size * (0.12 + min(1.0, elapsed / 900) * 0.8)))
        pygame.draw.ellipse(effect, (210, 226, 126, alpha), (center_point[0] - radius, center_point[1] - radius * 0.5, radius * 2, radius), 3)
    surface.blit(effect, (0, 0))
