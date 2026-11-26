import pygame
import resource_store as resources

from presentation.layout import ACT_THREE_TILE_SIZE, PROJECT_ROOT


def load_chest_frames():
    root = PROJECT_ROOT / "assets" / "maps" / "act_3" / "environment_objects" / "crypt_iron_chest"
    return tuple(
        pygame.transform.scale(resources.load_image(root / name).convert_alpha(), (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE))
        for name in ("closed.png", "opening_01.png", "opening_02.png", "open.png")
    )


def draw_chests(context, frames, current_time):
    for chest in context.floor.chests:
        cell = chest.column, chest.row
        if cell not in context.floor.explored_cells:
            continue
        index = 0
        if chest.is_open:
            elapsed = max(0, current_time - chest.open_animation_started_at)
            index = min(3, 1 + elapsed // 130)
        context.view_surface.blit(frames[index], (
            chest.column * ACT_THREE_TILE_SIZE - context.camera_x,
            chest.row * ACT_THREE_TILE_SIZE - context.camera_y,
        ))
