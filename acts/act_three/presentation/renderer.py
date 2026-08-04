
import pygame

from acts.act_three.presentation.combat_effects import (
    _PLAYER_DEATH_MESSAGE_FADE_MS,
    _PLAYER_DEATH_MESSAGE_START_MS,
    _player_death_elapsed,
)
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


def _draw_defeat_sequence(
    screen,
    game_state,
    fonts,
    current_time,
):
    elapsed = _player_death_elapsed(
        game_state.player,
        current_time,
    )
    if elapsed is None:
        return False

    fade_progress = min(1, max(0, (elapsed - 120) / 1080))
    fade_progress = (
        fade_progress
        * fade_progress
        * (3 - 2 * fade_progress)
    )
    view_rectangle = pygame.Rect(
        ACT_THREE_VIEW_X,
        ACT_THREE_VIEW_Y,
        ACT_THREE_VIEW_WIDTH,
        ACT_THREE_VIEW_HEIGHT,
    )
    view_copy = screen.subsurface(view_rectangle).copy()
    grayscale = pygame.transform.grayscale(view_copy)
    grayscale.set_alpha(round(205 * fade_progress))
    screen.blit(grayscale, view_rectangle)

    defeat_overlay = pygame.Surface(
        (ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT),
        pygame.SRCALPHA,
    )
    defeat_overlay.fill((3, 4, 7, round(70 * fade_progress)))
    vignette_alpha = round(95 * fade_progress)
    for inset, alpha_scale in (
        (0, 1.0),
        (8, 0.68),
        (18, 0.34),
    ):
        pygame.draw.rect(
            defeat_overlay,
            (0, 0, 0, round(vignette_alpha * alpha_scale)),
            (
                inset,
                inset,
                ACT_THREE_VIEW_WIDTH - inset * 2,
                ACT_THREE_VIEW_HEIGHT - inset * 2,
            ),
            width=10,
        )
    screen.blit(
        defeat_overlay,
        (ACT_THREE_VIEW_X, ACT_THREE_VIEW_Y),
    )

    message_progress = min(
        1,
        max(
            0,
            (elapsed - _PLAYER_DEATH_MESSAGE_START_MS)
            / _PLAYER_DEATH_MESSAGE_FADE_MS,
        ),
    )
    if message_progress <= 0:
        return True

    message_progress = message_progress * message_progress
    message_alpha = round(255 * message_progress)
    center_x = ACT_THREE_VIEW_X + ACT_THREE_VIEW_WIDTH // 2
    title_y = ACT_THREE_VIEW_Y + 82

    title_surface = fonts["title"].render(
        "DEFEAT",
        True,
        (205, 207, 213),
    )
    title_surface.set_alpha(message_alpha)
    title_rectangle = title_surface.get_rect(
        center=(center_x, title_y),
    )
    title_shadow = fonts["title"].render(
        "DEFEAT",
        True,
        (12, 8, 10),
    )
    title_shadow.set_alpha(message_alpha)
    screen.blit(title_shadow, title_rectangle.move(2, 3))
    screen.blit(title_surface, title_rectangle)

    restart_surface = fonts["sidebar_numbers"].render(
        "PRESS R TO RESTART",
        True,
        (154, 157, 165),
    )
    restart_surface.set_alpha(message_alpha)
    screen.blit(
        restart_surface,
        restart_surface.get_rect(
            center=(center_x, title_y + 52),
        ),
    )
    return True


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
        fonts,
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

    if game_state.player.health <= 0:
        if _draw_defeat_sequence(
            screen,
            game_state,
            fonts,
            current_time,
        ):
            return

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
