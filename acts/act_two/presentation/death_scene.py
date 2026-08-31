import pygame

from presentation.camera import camera_render_rectangle
from presentation.hud import wrap_text
from presentation.layout import (
    ACT_TWO_VIEW_HEIGHT,
    ACT_TWO_VIEW_WIDTH,
    ACT_TWO_VIEW_X,
    ACT_TWO_VIEW_Y,
)
from settings import TILE_SIZE


ACT_TWO_OLD_MAN_APPEAR_MS = 2500
ACT_TWO_OLD_MAN_KNEEL_MS = 3700
ACT_TWO_OLD_MAN_DIALOGUE_MS = 4800

_OLD_MAN_LINES = {
    "warrior": "Strength is loud. What waits below is patient.",
    "rogue": "You can hide from beasts. Not from the road below.",
    "mage": "You touch the dark, child. You do not yet see it.",
}


def _smoothstep(progress):
    progress = max(0, min(1, progress))
    return progress * progress * (3 - 2 * progress)


def draw_act_two_death_dialogue_overlay(
    screen,
    game_state,
    fonts,
    current_time,
    camera,
):
    player = game_state.player

    if (
            player.health > 0
            or player.death_animation_started_at < 0
            or player.player_class not in _OLD_MAN_LINES
            or player.act_two.death_score_open
    ):
        return

    elapsed = max(
        0,
        current_time - player.death_animation_started_at,
    )

    if player.act_two.death_dialogue_skipped:
        elapsed = max(
            elapsed,
            ACT_TWO_OLD_MAN_DIALOGUE_MS + 420,
        )

    if elapsed < ACT_TWO_OLD_MAN_DIALOGUE_MS:
        return

    view_rectangle = camera_render_rectangle(
        pygame.Rect(
            ACT_TWO_VIEW_X,
            ACT_TWO_VIEW_Y,
            ACT_TWO_VIEW_WIDTH,
            ACT_TWO_VIEW_HEIGHT,
        ),
        camera.zoom,
    )

    dialogue_progress = _smoothstep(
        (elapsed - ACT_TWO_OLD_MAN_DIALOGUE_MS) / 420
    )

    dialogue_font = fonts["heading"]
    dialogue_text = _OLD_MAN_LINES[player.player_class]

    horizontal_padding = 32
    vertical_padding = 22
    maximum_text_width = view_rectangle.width - 220

    lines = wrap_text(
        dialogue_font,
        dialogue_text,
        maximum_text_width,
    )

    line_height = dialogue_font.get_linesize()
    rendered_lines = [
        dialogue_font.render(
            line,
            True,
            (232, 225, 207),
        )
        for line in lines
    ]

    text_width = max(
        line_surface.get_width()
        for line_surface in rendered_lines
    )
    text_height = line_height * len(rendered_lines)

    panel_width = text_width + horizontal_padding * 2
    panel_height = text_height + vertical_padding * 2

    panel = pygame.Surface(
        (panel_width, panel_height),
        pygame.SRCALPHA,
    )
    panel.fill((5, 7, 10, 232))

    pygame.draw.rect(
        panel,
        (112, 101, 82, 230),
        panel.get_rect(),
        width=2,
        border_radius=5,
    )
    pygame.draw.rect(
        panel,
        (32, 29, 25, 230),
        panel.get_rect().inflate(-8, -8),
        width=1,
        border_radius=3,
    )

    panel_rectangle = panel.get_rect(
        midbottom=(
            view_rectangle.centerx,
            view_rectangle.bottom - 160,
        )
    )

    text_y = vertical_padding

    for line, line_surface in zip(lines, rendered_lines):
        shadow = dialogue_font.render(
            line,
            True,
            (0, 0, 0),
        )

        line_rectangle = line_surface.get_rect(
            centerx=panel_width // 2,
            y=text_y,
        )

        panel.blit(
            shadow,
            line_rectangle.move(2, 3),
        )
        panel.blit(
            line_surface,
            line_rectangle,
        )

        text_y += line_height

    panel.set_alpha(
        round(255 * dialogue_progress)
    )

    previous_clip = screen.get_clip()
    screen.set_clip(view_rectangle)
    screen.blit(panel, panel_rectangle)
    screen.set_clip(previous_clip)
    screen.set_clip(previous_clip)


def _draw_old_man(
    screen,
    game_state,
    sprites,
    elapsed,
    view_rectangle,
    camera=None,
):
    old_man_cell = game_state.player.old_man_position
    if elapsed < ACT_TWO_OLD_MAN_APPEAR_MS or old_man_cell is None:
        return
    appearance_elapsed = elapsed - ACT_TWO_OLD_MAN_APPEAR_MS
    fade = _smoothstep(appearance_elapsed / 720)
    sprite_name = (
        "old_man_standing"
        if elapsed < ACT_TWO_OLD_MAN_KNEEL_MS
        else "old_man_kneeling"
    )
    sprite = sprites[sprite_name].copy()
    if old_man_cell[0] < game_state.floor.player_column:
        sprite = pygame.transform.flip(sprite, True, False)
    sprite.set_alpha(round(255 * fade))
    if camera is None:
        position = (
            view_rectangle.x
            + old_man_cell[0] * TILE_SIZE
            - (sprite.get_width() - TILE_SIZE) // 2,
            view_rectangle.y
            + old_man_cell[1] * TILE_SIZE
            - (sprite.get_height() - TILE_SIZE),
        )
        echo_distance = 3
    else:
        render_scale = camera.zoom
        source_width, source_height = sprite.get_size()
        sprite = pygame.transform.scale(
            sprite,
            (
                source_width * render_scale,
                source_height * render_scale,
            ),
        )
        position = (
            view_rectangle.x
            + round(
                (old_man_cell[0] * TILE_SIZE - camera.x)
                * render_scale
            )
            - (sprite.get_width() - TILE_SIZE * render_scale) // 2,
            view_rectangle.y
            + round(
                (old_man_cell[1] * TILE_SIZE - camera.y)
                * render_scale
            )
            - (sprite.get_height() - TILE_SIZE * render_scale),
        )
        echo_distance = 3 * render_scale
    for echo_index in range(2, 0, -1):
        echo = sprite.copy()
        echo.set_alpha(round(42 * fade / echo_index))
        screen.blit(
            echo,
            (position[0], position[1] - echo_index * echo_distance),
        )
    screen.blit(sprite, position)


def draw_act_two_death_scene(
    screen,
    game_state,
    fonts,
    sprites,
    current_time,
    view_rectangle,
    camera=None,
):
    player = game_state.player
    if player.health > 0 or player.death_animation_started_at < 0:
        return

    elapsed = max(0, current_time - player.death_animation_started_at)
    fade = _smoothstep((elapsed - 600) / 1900)
    if fade > 0:
        view_copy = screen.subsurface(view_rectangle).copy()
        grayscale = pygame.transform.grayscale(view_copy)
        grayscale.set_alpha(round(185 * fade))
        screen.blit(grayscale, view_rectangle)
        darkness = pygame.Surface(view_rectangle.size, pygame.SRCALPHA)
        darkness.fill((3, 5, 7, round(58 * fade)))
        screen.blit(darkness, view_rectangle)

    previous_clip = screen.get_clip()
    screen.set_clip(view_rectangle)
    _draw_old_man(
        screen,
        game_state,
        sprites,
        elapsed,
        view_rectangle,
        camera,
    )
    screen.set_clip(previous_clip)
