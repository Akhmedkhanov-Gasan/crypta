
import pygame

from acts.act_three.presentation.altar_menu import (
    draw_upgrade_altar_menu,
)
from acts.act_three.presentation.sidebar import (
    _draw_act_three_sidebar,
    _draw_label,
)

from acts.act_three.presentation.world import _draw_act_three_world
from levels import FLOOR_CONFIGS
from presentation.layout import (
    ACT_THREE_VIEW_HEIGHT,
    ACT_THREE_VIEW_WIDTH,
    ACT_THREE_VIEW_X,
    ACT_THREE_VIEW_Y,
)
from settings import TEXT_COLOR


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


def draw_act_three_gameplay(
    screen,
    game_state,
    fonts,
    assets,
    current_time,
):
    screen.fill((7, 6, 10))
    floor_config = FLOOR_CONFIGS[game_state.floor_index]
    floor_label = (
        f"ACT III  /  FLOOR {floor_config['act_floor']}"
    )
    _draw_label(
        screen,
        fonts["sidebar_text"],
        floor_label,
        (139, 132, 142),
        (ACT_THREE_VIEW_X, 62),
    )
    _draw_act_three_world(
        screen,
        game_state,
        assets,
        current_time,
    )
    _draw_act_three_sidebar(
        screen,
        game_state,
        fonts,
        assets,
    )
    if game_state.upgrade_altar_menu_open:
        draw_upgrade_altar_menu(
            screen,
            game_state,
            fonts,
            assets,
        )

    if game_state.player.health <= 0 or game_state.game_won:
        overlay = pygame.Surface(
            (ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, 170))
        screen.blit(
            overlay,
            (ACT_THREE_VIEW_X, ACT_THREE_VIEW_Y),
        )
        message = (
            "VICTORY - PRESS R TO RESTART"
            if game_state.game_won
            else "DEFEAT - PRESS R TO RESTART"
        )
        message_surface = fonts["heading"].render(
            message,
            True,
            TEXT_COLOR,
        )
        screen.blit(
            message_surface,
            message_surface.get_rect(
                center=(
                    ACT_THREE_VIEW_X
                    + ACT_THREE_VIEW_WIDTH // 2,
                    ACT_THREE_VIEW_Y
                    + ACT_THREE_VIEW_HEIGHT // 2,
                )
            ),
        )
