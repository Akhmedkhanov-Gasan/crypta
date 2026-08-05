
import math

import pygame

from acts.act_three.presentation.combat_effects import (
    _PLAYER_DEATH_COLLAPSE_END_MS,
    _PLAYER_DEATH_FALL_END_MS,
    _PLAYER_DEATH_MESSAGE_FADE_MS,
    _PLAYER_DEATH_MESSAGE_START_MS,
    _draw_berserker_death_foreground,
    _draw_assassin_death_foreground,
    _draw_archer_death_foreground,
    _draw_paladin_death_foreground,
    _draw_warlock_death_foreground,
    _draw_summoner_death_foreground,
    _player_death_elapsed,
    _player_death_camera_offset,
    _player_death_sprite_offset,
    _player_hit_camera_offset,
)
from acts.act_three.presentation.view import (
    _camera_position,
    _view_position,
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
from presentation.hud import wrap_text
from presentation.layout import (
    ACT_THREE_TILE_SIZE,
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
_OLD_MAN_APPEAR_START_MS = 4300
_OLD_MAN_APPEAR_FRAME_MS = 700
_OLD_MAN_FADE_IN_MS = 1250
_OLD_MAN_DIALOGUE_START_MS = 8500
_OLD_MAN_DEFEAT_MESSAGE_START_MS = 11200
_OLD_MAN_LINES = {
    "berserker": (
        "Still the red field drinks, and still it leaves you thirsty."
    ),
    "paladin": (
        "Where thy gold has gone to root, no morning dares to follow."
    ),
    "assassin": (
        "Hush now; the shadow has forgotten which of you it wore."
    ),
    "archer": (
        "Far flew thy wanting; the horizon kept no wound."
    ),
    "warlock": (
        "Twice-worn was thy shadow; neither face remembered dawn."
    ),
    "summoner": (
        "The empty hand remembers what the grave would not keep."
    ),
}


def _draw_old_man_death_scene(
    screen,
    game_state,
    fonts,
    assets,
    current_time,
    corpse_position,
):
    elapsed = _player_death_elapsed(
        game_state.player,
        current_time,
    )
    old_man_cell = game_state.player.old_man_position
    if (
        elapsed is None
        or elapsed < _OLD_MAN_APPEAR_START_MS
        or old_man_cell is None
    ):
        return

    appearance_elapsed = elapsed - _OLD_MAN_APPEAR_START_MS
    frame_index = min(
        5,
        appearance_elapsed // _OLD_MAN_APPEAR_FRAME_MS,
    )
    fade_progress = min(1, appearance_elapsed / _OLD_MAN_FADE_IN_MS)
    fade_progress = fade_progress * fade_progress * (3 - 2 * fade_progress)
    sprite_alpha = round(255 * fade_progress)

    camera_x, camera_y = _camera_position(game_state.floor)
    hit_camera_x, hit_camera_y = _player_hit_camera_offset(
        game_state.player,
        current_time,
    )
    death_camera_x, death_camera_y = _player_death_camera_offset(
        game_state.player,
        current_time,
    )
    camera_x += hit_camera_x + death_camera_x
    camera_y += hit_camera_y + death_camera_y
    old_man_position = _view_position(
        old_man_cell[0],
        old_man_cell[1],
        camera_x,
        camera_y,
    )
    old_man_position = (
        ACT_THREE_VIEW_X + old_man_position[0],
        ACT_THREE_VIEW_Y + old_man_position[1],
    )

    player_subclass = game_state.player.subclass
    screen.blit(
        assets[f"player_{player_subclass}_death_1"],
        corpse_position,
    )

    old_man_sprite = assets[
        f"old_man_appearance_{frame_index}"
    ]
    if old_man_cell[0] < game_state.floor.player_column:
        old_man_sprite = pygame.transform.flip(
            old_man_sprite,
            True,
            False,
        )

    if fade_progress < 1:
        for echo_index in range(3, 0, -1):
            echo = old_man_sprite.copy()
            echo.fill(
                (34, 31, 39, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            echo.set_alpha(
                round(sprite_alpha * (0.08 + echo_index * 0.045))
            )
            screen.blit(
                echo,
                (
                    old_man_position[0],
                    old_man_position[1] - echo_index * 3,
                ),
            )

        mote_surface = pygame.Surface(
            (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
            pygame.SRCALPHA,
        )
        for mote_index in range(12):
            phase = (
                appearance_elapsed / 900 + mote_index * 0.137
            ) % 1
            mote_x = round(
                ACT_THREE_TILE_SIZE // 2
                + math.sin(mote_index * 2.3) * (8 + phase * 18)
            )
            mote_y = round(
                ACT_THREE_TILE_SIZE - 5 - phase * 54
            )
            pygame.draw.circle(
                mote_surface,
                (
                    168,
                    162,
                    154,
                    round(125 * math.sin(math.pi * phase) * fade_progress),
                ),
                (mote_x, mote_y),
                1,
            )
        screen.blit(mote_surface, old_man_position)

    visible_sprite = old_man_sprite.copy()
    visible_sprite.set_alpha(sprite_alpha)
    screen.blit(visible_sprite, old_man_position)

    if elapsed < _OLD_MAN_DIALOGUE_START_MS:
        return

    dialogue_elapsed = elapsed - _OLD_MAN_DIALOGUE_START_MS
    fade_in = min(1, dialogue_elapsed / 550)
    dialogue_alpha = round(255 * fade_in)
    center_x = ACT_THREE_VIEW_X + ACT_THREE_VIEW_WIDTH // 2
    line_y = ACT_THREE_VIEW_Y + ACT_THREE_VIEW_HEIGHT - 58
    for line in wrap_text(
        fonts["narrative"],
        _OLD_MAN_LINES[player_subclass],
        ACT_THREE_VIEW_WIDTH - 110,
    ):
        line_surface = fonts["narrative"].render(
            line,
            True,
            (220, 210, 193),
        )
        line_surface.set_alpha(dialogue_alpha)
        line_rectangle = line_surface.get_rect(
            center=(center_x, line_y),
        )
        shadow_surface = fonts["narrative"].render(
            line,
            True,
            (5, 4, 6),
        )
        shadow_surface.set_alpha(dialogue_alpha)
        screen.blit(shadow_surface, line_rectangle.move(2, 2))
        screen.blit(line_surface, line_rectangle)
        line_y += 30


def _draw_defeat_sequence(
    screen,
    game_state,
    fonts,
    assets,
    current_time,
):
    elapsed = _player_death_elapsed(
        game_state.player,
        current_time,
    )
    if elapsed is None:
        return False

    fade_progress = min(
        1,
        max(
            0,
            (elapsed - _PLAYER_DEATH_COLLAPSE_END_MS)
            / (
                _PLAYER_DEATH_MESSAGE_START_MS
                - _PLAYER_DEATH_COLLAPSE_END_MS
            ),
        ),
    )
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
    grayscale.set_alpha(round(220 * fade_progress))
    screen.blit(grayscale, view_rectangle)

    defeat_overlay = pygame.Surface(
        (ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT),
        pygame.SRCALPHA,
    )
    defeat_overlay.fill((3, 4, 7, round(78 * fade_progress)))
    vignette_alpha = round(112 * fade_progress)
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

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if 0 <= impact_elapsed < 360:
        impact_progress = impact_elapsed / 360
        impact_pulse = math.sin(math.pi * impact_progress)
        impact_overlay = pygame.Surface(
            (ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT),
            pygame.SRCALPHA,
        )
        impact_colors = {
            "berserker": (43, 5, 6),
            "paladin": (76, 61, 22),
            "assassin": (10, 21, 48),
            "archer": (30, 45, 20),
            "warlock": (45, 12, 58),
            "summoner": (12, 51, 55),
        }
        impact_color = impact_colors.get(
            game_state.player.subclass,
            (24, 23, 28),
        )
        impact_overlay.fill(
            (*impact_color, round(62 * impact_pulse)),
        )
        screen.blit(
            impact_overlay,
            (ACT_THREE_VIEW_X, ACT_THREE_VIEW_Y),
        )

    if game_state.player.subclass in (
        "berserker",
        "paladin",
        "assassin",
        "archer",
        "warlock",
        "summoner",
    ):
        camera_x, camera_y = _camera_position(game_state.floor)
        hit_camera_x, hit_camera_y = _player_hit_camera_offset(
            game_state.player,
            current_time,
        )
        death_camera_x, death_camera_y = _player_death_camera_offset(
            game_state.player,
            current_time,
        )
        camera_x += hit_camera_x + death_camera_x
        camera_y += hit_camera_y + death_camera_y
        effect_position = _view_position(
            game_state.floor.player_column,
            game_state.floor.player_row,
            camera_x,
            camera_y,
        )
        death_offset_x, death_offset_y = _player_death_sprite_offset(
            game_state.player,
            current_time,
        )
        effect_position = (
            ACT_THREE_VIEW_X + effect_position[0] + death_offset_x,
            ACT_THREE_VIEW_Y + effect_position[1] + death_offset_y,
        )
        if game_state.player.subclass == "berserker":
            _draw_berserker_death_foreground(
                screen,
                assets,
                effect_position,
                game_state.player,
                current_time,
            )
        elif game_state.player.subclass == "paladin":
            _draw_paladin_death_foreground(
                screen,
                assets,
                effect_position,
                game_state.player,
                current_time,
            )
        elif game_state.player.subclass == "assassin":
            _draw_assassin_death_foreground(
                screen,
                assets,
                effect_position,
                game_state.player,
                current_time,
            )
        elif game_state.player.subclass == "archer":
            _draw_archer_death_foreground(
                screen,
                assets,
                effect_position,
                game_state.player,
                current_time,
            )
        elif game_state.player.subclass == "warlock":
            _draw_warlock_death_foreground(
                screen,
                assets,
                effect_position,
                game_state.player,
                current_time,
            )
        else:
            _draw_summoner_death_foreground(
                screen,
                assets,
                effect_position,
                game_state.player,
                current_time,
            )

    if game_state.player.subclass in _OLD_MAN_LINES:
        _draw_old_man_death_scene(
            screen,
            game_state,
            fonts,
            assets,
            current_time,
            effect_position,
        )

    message_start = (
        _OLD_MAN_DEFEAT_MESSAGE_START_MS
        if game_state.player.subclass in _OLD_MAN_LINES
        else _PLAYER_DEATH_MESSAGE_START_MS
    )
    message_progress = min(
        1,
        max(
            0,
            (elapsed - message_start)
            / _PLAYER_DEATH_MESSAGE_FADE_MS,
        ),
    )
    if message_progress <= 0:
        return True

    message_progress = message_progress * message_progress
    message_alpha = round(255 * message_progress)
    center_x = ACT_THREE_VIEW_X + ACT_THREE_VIEW_WIDTH // 2
    title_y = ACT_THREE_VIEW_Y + 82

    defeat_titles = {
        "berserker": "RAGE EXTINGUISHED",
        "paladin": "THE LIGHT FADES",
        "assassin": "THE SHADOW FALLS",
        "archer": "THE HUNT ENDS",
        "warlock": "THE PACT IS BROKEN",
        "summoner": "THE BOND IS SEVERED",
    }
    defeat_title = defeat_titles.get(
        game_state.player.subclass,
        "DEFEAT",
    )
    title_colors = {
        "berserker": (205, 207, 213),
        "paladin": (218, 196, 126),
        "assassin": (150, 177, 220),
        "archer": (174, 190, 132),
        "warlock": (190, 145, 207),
        "summoner": (134, 202, 202),
    }
    title_surface = fonts["title"].render(
        defeat_title,
        True,
        title_colors.get(
            game_state.player.subclass,
            (205, 207, 213),
        ),
    )
    title_surface.set_alpha(message_alpha)
    title_rectangle = title_surface.get_rect(
        center=(center_x, title_y),
    )
    title_shadow = fonts["title"].render(
        defeat_title,
        True,
        (12, 8, 10),
    )
    title_shadow.set_alpha(message_alpha)
    screen.blit(title_shadow, title_rectangle.move(2, 3))
    screen.blit(title_surface, title_rectangle)

    defeat_surface = fonts["sidebar_heading"].render(
        "DEFEAT",
        True,
        (126, 128, 135),
    )
    defeat_surface.set_alpha(message_alpha)
    screen.blit(
        defeat_surface,
        defeat_surface.get_rect(
            center=(center_x, title_y + 48),
        ),
    )

    restart_surface = fonts["sidebar_numbers"].render(
        "PRESS R TO RESTART",
        True,
        (154, 157, 165),
    )
    restart_surface.set_alpha(message_alpha)
    screen.blit(
        restart_surface,
        restart_surface.get_rect(
            center=(center_x, title_y + 78),
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
            assets,
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
