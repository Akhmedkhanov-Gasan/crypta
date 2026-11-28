from functools import lru_cache

import pygame
import resource_store as resources

from acts.act_three.bloody_altar.runtime import altar_position
from acts.act_three.bloody_altar.world_effects import draw_foreground_effects, draw_ground_glow
from presentation.layout import ACT_THREE_TILE_SIZE


FRAME_COUNT = 64
FRAME_DURATION_MS = 50
SHEET_COLUMNS = 8
SPRITE_SIZE = 64
ASSET_DIRECTORY = "assets/sprites/act_3/environment/bloody_altar"


@lru_cache(maxsize=1)
def _layers():
    size = ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE
    base = resources.load_image(f"{ASSET_DIRECTORY}/base_v2.png").convert_alpha()
    sheet = resources.load_image(f"{ASSET_DIRECTORY}/effects_v2_sheet.png").convert_alpha()
    overlays = tuple(pygame.transform.scale(sheet.subsurface((
        index % SHEET_COLUMNS * SPRITE_SIZE, index // SHEET_COLUMNS * SPRITE_SIZE,
        SPRITE_SIZE, SPRITE_SIZE,
    )), size) for index in range(FRAME_COUNT))
    return pygame.transform.scale(base, size), overlays


@lru_cache(maxsize=128)
def _effect_frame(index, fraction):
    overlays = _layers()[1]
    if fraction == 0:
        return overlays[index]
    weight = round(255 * fraction / 16)
    image = overlays[index].copy()
    image.fill((255 - weight,) * 4, special_flags=pygame.BLEND_RGBA_MULT)
    following = overlays[(index + 1) % FRAME_COUNT].copy()
    following.fill((weight,) * 4, special_flags=pygame.BLEND_RGBA_MULT)
    image.blit(following, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return image


@lru_cache(maxsize=1)
def world_frames():
    base, overlays = _layers()
    frames = []
    for overlay in overlays:
        frame = base.copy()
        frame.blit(overlay, (0, 0))
        frames.append(frame)
    return tuple(frames)


def draw_world_altar(context, current_time):
    position = altar_position(context.floor)
    if position is None or position not in context.floor.visible_cells:
        return
    point = (position[0] * ACT_THREE_TILE_SIZE - context.camera_x,
             position[1] * ACT_THREE_TILE_SIZE - context.camera_y)
    base = _layers()[0]
    if context.floor.act_three_bloody_altar["claimed"]:
        inactive = base.copy()
        inactive.fill((105, 105, 105, 255), special_flags=pygame.BLEND_RGBA_MULT)
        context.view_surface.blit(inactive, point)
        return
    draw_ground_glow(context.view_surface, point, current_time, ACT_THREE_TILE_SIZE)
    context.view_surface.blit(base, point)
    index = current_time // FRAME_DURATION_MS % FRAME_COUNT
    fraction = current_time % FRAME_DURATION_MS * 16 // FRAME_DURATION_MS
    context.view_surface.blit(_effect_frame(index, fraction), point)
    draw_foreground_effects(context.view_surface, point, current_time, ACT_THREE_TILE_SIZE)
