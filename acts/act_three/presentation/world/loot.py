import math

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE
from systems.ground_items import DROPPED_ITEM_FLIGHT_MS
from acts.act_three.presentation.items.ground_highlight import draw_ground_sprite


def draw_loot_drops(context, sprites, current_time, pile_sprites=()):
    floor = context.floor
    tile_size = ACT_THREE_TILE_SIZE
    grouped = {}
    for item in floor.dropped_consumables:
        elapsed = current_time - item.thrown_at
        if not 0 <= elapsed < DROPPED_ITEM_FLIGHT_MS or item.destination not in floor.visible_cells:
            continue
        grouped.setdefault(item.destination, []).append(item)

    for destination, items in grouped.items():
        item = items[-1]
        elapsed = current_time - item.thrown_at
        column, row = item.destination
        x = column * tile_size - context.camera_x + tile_size // 2
        y = row * tile_size - context.camera_y + tile_size // 2
        progress = elapsed / DROPPED_ITEM_FLIGHT_MS
        lift = 20 * math.sin(math.pi * progress) + 8 * (1 - progress)
        size = round(tile_size * (0.72 + 0.28 * progress))
        if len(items) > 1 and pile_sprites:
            source = pile_sprites[hash((floor.visual_seed, destination)) % len(pile_sprites)]
        else:
            source = sprites[item.kind]
        sprite = pygame.transform.scale(source, (size, size))
        draw_ground_sprite(context.view_surface, sprite, sprite.get_rect(center=(x, round(y - lift))).topleft, current_time)

        if progress < 0.7:
            motes = pygame.Surface((36, 24), pygame.SRCALPHA)
            alpha = round(150 * (1 - progress / 0.7))
            spread = round(10 * progress)
            for dx, dy, radius in ((-7, 5, 1), (2, 1, 2), (8, 8, 1)):
                pygame.draw.circle(
                    motes, (228, 189, 121, alpha),
                    (18 + dx + (spread if dx > 0 else -spread), 12 + dy - spread),
                    radius,
                )
            context.view_surface.blit(motes, motes.get_rect(center=(x, round(y - lift))))
