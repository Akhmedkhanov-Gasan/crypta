import math
from functools import lru_cache

import pygame


@lru_cache(maxsize=128)
def _outline(sprite):
    mask = pygame.mask.from_surface(sprite, 32)
    width, height = sprite.get_size()
    outer = pygame.mask.Mask((width + 2, height + 2))
    for offset in ((0, 1), (2, 1), (1, 0), (1, 2)):
        outer.draw(mask, offset)
    outer.erase(mask, (1, 1))
    return outer.to_surface(setcolor=(202, 181, 134, 150), unsetcolor=(0, 0, 0, 0))


def draw_ground_sprite(screen, sprite, position, current_time):
    outline = _outline(sprite).copy()
    outline.set_alpha(round(100 + 25 * math.sin(current_time / 650)))
    screen.blit(outline, (position[0] - 1, position[1] - 1))
    screen.blit(sprite, position)
