import math

import pygame

from acts.act_three.presentation.view import _view_position

from presentation.layout import ACT_THREE_TILE_SIZE
from settings import HEALTH_BAR_BACKGROUND


_TORCH_LIGHT_SURFACE = None
_IDLE_FRAME_SEQUENCE = (0, 1, 2, 1)
_IDLE_TIMELINE_CYCLE_COUNT = 4
_MOVE_FRAME_COUNT = 2
_MOVE_FRAME_DURATION_MS = 90
_ATTACK_FRAME_DURATION_MS = 240
_FAMILIAR_MOVE_DURATION_MS = 180
_TELEPORT_CAMERA_DURATION_MS = 480
_TELEPORT_EFFECT_DURATION_MS = 600
_ARCHER_BARRAGE_SHOT_EFFECT_MS = 360
_TOP_VOID_CORNER_Y_OFFSET = 47
_TOP_VOID_CORNER_X_OFFSETS = {
    "wall_corner_top_left": -18,
    "wall_corner_top_right": 18,
}
_TOP_VOID_DOUBLE_CORNER_CROP_WIDTH = 24

def _draw_tile_markers(
    view_surface,
    positions,
    camera_x,
    camera_y,
    color,
):
    marker_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    marker_surface.fill((*color, 74))
    pygame.draw.rect(
        marker_surface,
        (*color, 210),
        marker_surface.get_rect(),
        width=3,
    )

    for column, row in positions:
        view_surface.blit(
            marker_surface,
            _view_position(
                column,
                row,
                camera_x,
                camera_y,
            ),
        )


def _draw_archer_barrage_zone_cells(
    view_surface,
    cell_sprite,
    positions,
    camera_x,
    camera_y,
    current_time,
    preview=False,
):
    if not positions:
        return

    pulse = (math.sin(current_time * 0.008) + 1) / 2
    zone_sprite = cell_sprite.copy()
    zone_sprite.set_alpha(
        round(
            (78 if preview else 118)
            + pulse * (22 if preview else 42)
        )
    )
    for column, row in positions:
        view_surface.blit(
            zone_sprite,
            _view_position(
                column,
                row,
                camera_x,
                camera_y,
            ),
        )


def _draw_health_bar(
    surface,
    left,
    top,
    health,
    maximum_health,
    color,
):
    bar_width = ACT_THREE_TILE_SIZE - 14
    bar_height = 5
    health_ratio = max(0, health / maximum_health)
    pygame.draw.rect(
        surface,
        HEALTH_BAR_BACKGROUND,
        (left + 7, top + 56, bar_width, bar_height),
    )
    pygame.draw.rect(
        surface,
        color,
        (
            left + 7,
            top + 56,
            round(bar_width * health_ratio),
            bar_height,
        ),
    )
