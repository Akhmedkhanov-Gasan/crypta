from functools import lru_cache
from pathlib import Path

import pygame
import resource_store as resources

from presentation.layout import ACT_THREE_TILE_SIZE


@lru_cache(maxsize=1)
def door_frames():
    root = Path(__file__).resolve().parents[4] / "assets/maps/act_3/trials/trial_door"
    size = ACT_THREE_TILE_SIZE
    return [pygame.transform.scale(resources.load_image(str(root / f"shadow_step_door_open_{index:02d}.png")).convert_alpha(), (size, size)) for index in range(1, 9)]
