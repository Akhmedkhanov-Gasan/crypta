import pygame

from presentation.hud import wrap_text
from presentation.layout import ACT_TWO_RENDER_SCALE
from settings import TILE_SIZE


ACT_TWO_OLD_MAN_APPEAR_MS = 2500
ACT_TWO_OLD_MAN_KNEEL_MS = 3700
ACT_TWO_OLD_MAN_DIALOGUE_MS = 4800
ACT_TWO_DEFEAT_MESSAGE_MS = 6900
ACT_TWO_DEFEAT_FADE_MS = 520

_OLD_MAN_LINES = {
    "warrior": "Strength is loud. What waits below is patient.",
    "rogue": "You can hide from beasts. Not from the road below.",
    "mage": "You touch the dark, child. You do not yet see it.",
}
_DEFEAT_TITLES = {
    "warrior": "THE BLADE FALLS",
    "rogue": "THE SHADOW BREAKS",
    "mage": "THE SPARK FADES",
}


def _smoothstep(progress):
    progress = max(0, min(1, progress))
    return progress * progress * (3 - 2 * progress)


def _draw_old_man(
    screen,
    game_state,
    fonts,
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
        source_width, source_height = sprite.get_size()
        sprite = pygame.transform.scale(
            sprite,
            (
                source_width * ACT_TWO_RENDER_SCALE,
                source_height * ACT_TWO_RENDER_SCALE,
            ),
        )
        position = (
            view_rectangle.x
            + round(
                (old_man_cell[0] * TILE_SIZE - camera.x)
                * ACT_TWO_RENDER_SCALE
            )
            - (sprite.get_width() - TILE_SIZE * ACT_TWO_RENDER_SCALE) // 2,
            view_rectangle.y
            + round(
                (old_man_cell[1] * TILE_SIZE - camera.y)
                * ACT_TWO_RENDER_SCALE
            )
            - (sprite.get_height() - TILE_SIZE * ACT_TWO_RENDER_SCALE),
        )
        echo_distance = 6
    for echo_index in range(2, 0, -1):
        echo = sprite.copy()
        echo.set_alpha(round(42 * fade / echo_index))
        screen.blit(
            echo,
            (position[0], position[1] - echo_index * echo_distance),
        )
    screen.blit(sprite, position)

    if elapsed < ACT_TWO_OLD_MAN_DIALOGUE_MS:
        return
    dialogue_progress = _smoothstep(
        (elapsed - ACT_TWO_OLD_MAN_DIALOGUE_MS) / 420
    )
    line_y = view_rectangle.bottom - 46
    for line in wrap_text(
        fonts["text"],
        _OLD_MAN_LINES[game_state.player.player_class],
        view_rectangle.width - 100,
    ):
        line_surface = fonts["text"].render(line, True, (218, 211, 197))
        line_surface.set_alpha(round(255 * dialogue_progress))
        rectangle = line_surface.get_rect(
            center=(view_rectangle.centerx, line_y)
        )
        shadow = fonts["text"].render(line, True, (4, 5, 7))
        shadow.set_alpha(round(255 * dialogue_progress))
        screen.blit(shadow, rectangle.move(2, 2))
        screen.blit(line_surface, rectangle)
        line_y += 23


def draw_act_two_death_scene(
    screen,
    game_state,
    fonts,
    sprites,
    current_time,
    view_rectangle,
    class_color,
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
        fonts,
        sprites,
        elapsed,
        view_rectangle,
        camera,
    )
    screen.set_clip(previous_clip)

    message_progress = _smoothstep(
        (elapsed - ACT_TWO_DEFEAT_MESSAGE_MS) / ACT_TWO_DEFEAT_FADE_MS
    )
    if message_progress <= 0:
        return
    alpha = round(255 * message_progress)
    center_x = view_rectangle.centerx
    title_text = _DEFEAT_TITLES[player.player_class]
    title = fonts["title"].render(title_text, True, class_color)
    title.set_alpha(alpha)
    title_rectangle = title.get_rect(
        center=(center_x, view_rectangle.y + 76)
    )
    title_shadow = fonts["title"].render(title_text, True, (8, 5, 7))
    title_shadow.set_alpha(alpha)
    screen.blit(title_shadow, title_rectangle.move(2, 3))
    screen.blit(title, title_rectangle)

    restart = fonts["controls"].render(
        "PRESS R TO RESTART",
        True,
        (170, 174, 176),
    )
    restart.set_alpha(alpha)
    screen.blit(
        restart,
        restart.get_rect(center=(center_x, view_rectangle.y + 116)),
    )
