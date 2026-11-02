import pygame

from acts.act_two.presentation.awakening_timing import AWAKENING_OLD_MAN_DIALOGUE_START_MS
from settings import TILE_SIZE


def awakening_recovery_sprite(sprites, elapsed):
    progress = max(0.0, min(1.0, (elapsed - AWAKENING_OLD_MAN_DIALOGUE_START_MS) / 700))
    progress = progress * progress * (3.0 - 2.0 * progress)
    kneeling = sprites["player_unawakened_kneeling"].copy()
    standing = sprites["player_unawakened_standing"].copy()
    if progress <= 0:
        return kneeling
    if progress >= 1:
        return standing
    sprite = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    kneeling.set_alpha(round(255 * (1.0 - progress)))
    standing.set_alpha(round(255 * progress))
    sprite.blit(kneeling, (0, -round(progress * 2)))
    sprite.blit(standing, (0, 0))
    return sprite
