from functools import lru_cache
import math

import pygame

from acts.act_one.warden_intro import (
    ARCHER_APPEAR_END_MS,
    ARCHER_APPEAR_START_MS,
    DIALOGUE_END_MS,
    DIALOGUE_START_MS,
    SKIP_HOLD_MS,
    WARDEN_LINE,
    warden_intro_active,
)
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


def _progress(value, start, end):
    if value <= start:
        return 0.0
    if value >= end:
        return 1.0

    progress = (value - start) / (end - start)
    return progress * progress * (3.0 - 2.0 * progress)


@lru_cache(maxsize=4)
def _cinematic_frame(size):
    surface = pygame.Surface(
        size,
        pygame.SRCALPHA,
    )
    width, height = size

    pygame.draw.rect(
        surface,
        (0, 0, 0, 212),
        (0, 0, width, 42),
    )
    pygame.draw.rect(
        surface,
        (0, 0, 0, 222),
        (0, height - 72, width, 72),
    )
    pygame.draw.rect(
        surface,
        (0, 0, 0, 58),
        (0, 42, 34, height - 114),
    )
    pygame.draw.rect(
        surface,
        (0, 0, 0, 58),
        (width - 34, 42, 34, height - 114),
    )

    return surface


def draw_warden_intro_world(
    screen,
    floor,
    current_time,
):
    if not warden_intro_active(floor):
        return

    state = floor.act_one_warden_intro
    spawn_progress = _progress(
        state.elapsed,
        ARCHER_APPEAR_START_MS,
        ARCHER_APPEAR_END_MS,
    )

    if spawn_progress <= 0.0:
        return

    pulse = (
        math.sin(current_time / 95) + 1.0
    ) / 2.0

    for enemy in floor.enemies:
        if (
            not enemy.boss_group
            or enemy.type != "archer"
        ):
            continue

        effect = pygame.Surface(
            (48, 54),
            pygame.SRCALPHA,
        )
        fade = math.sin(
            math.pi * min(
                1.0,
                spawn_progress,
            )
        )
        center_x = 24
        floor_y = 45

        for layer in range(4):
            layer_progress = (
                spawn_progress
                + layer * 0.13
            ) % 1.0
            radius_x = round(
                6 + layer_progress * 13
            )
            radius_y = round(
                4 + layer_progress * 9
            )
            alpha = round(
                (66 - layer * 9)
                * fade
            )

            pygame.draw.ellipse(
                effect,
                (
                    29 + layer * 4,
                    20,
                    37 + layer * 5,
                    alpha,
                ),
                (
                    center_x - radius_x,
                    floor_y
                    - radius_y
                    - round(pulse * 3),
                    radius_x * 2,
                    radius_y * 2,
                ),
                width=2,
            )

        pygame.draw.line(
            effect,
            (
                104,
                52,
                91,
                round(90 * fade),
            ),
            (
                center_x,
                floor_y,
            ),
            (
                center_x,
                12 - round(pulse * 3),
            ),
            2,
        )

        screen.blit(
            effect,
            (
                MAP_OFFSET_X
                + enemy.column * TILE_SIZE
                + TILE_SIZE // 2
                - effect.get_width() // 2,
                MAP_OFFSET_Y
                + enemy.row * TILE_SIZE
                + TILE_SIZE // 2
                - effect.get_height() // 2,
            ),
        )


def draw_warden_intro_overlay(
    screen,
    floor,
    title_font,
    text_font,
):
    if not warden_intro_active(floor):
        return

    state = floor.act_one_warden_intro
    screen.blit(
        _cinematic_frame(
            screen.get_size()
        ),
        (0, 0),
    )

    if (
        DIALOGUE_START_MS
        <= state.elapsed
        < DIALOGUE_END_MS
    ):
        fade_in = _progress(
            state.elapsed,
            DIALOGUE_START_MS,
            DIALOGUE_START_MS + 320,
        )
        fade_out = 1.0 - _progress(
            state.elapsed,
            DIALOGUE_END_MS - 420,
            DIALOGUE_END_MS,
        )
        alpha = round(
            255 * min(fade_in, fade_out)
        )

        title = title_font.render(
            "CRYPT WARDEN",
            True,
            (159, 111, 169),
        )
        line = text_font.render(
            WARDEN_LINE,
            True,
            (223, 214, 218),
        )
        title.set_alpha(alpha)
        line.set_alpha(alpha)

        screen.blit(
            title,
            title.get_rect(
                center=(
                    screen.get_width() // 2,
                    screen.get_height() - 51,
                ),
            ),
        )
        screen.blit(
            line,
            line.get_rect(
                center=(
                    screen.get_width() // 2,
                    screen.get_height() - 25,
                ),
            ),
        )

    skip = text_font.render(
        "HOLD SPACE TO SKIP",
        True,
        (115, 108, 116),
    )
    skip.set_alpha(155)
    skip_rectangle = skip.get_rect(
        top=12,
        right=screen.get_width() - 18,
    )
    screen.blit(
        skip,
        skip_rectangle,
    )

    if state.skip_held_ms > 0:
        progress = min(
            1.0,
            state.skip_held_ms / SKIP_HOLD_MS,
        )
        bar = pygame.Rect(
            skip_rectangle.left,
            skip_rectangle.bottom + 4,
            skip_rectangle.width,
            2,
        )
        pygame.draw.rect(
            screen,
            (44, 40, 47),
            bar,
        )
        pygame.draw.rect(
            screen,
            (145, 91, 154),
            (
                bar.x,
                bar.y,
                round(bar.width * progress),
                bar.height,
            ),
        )
