import math
import random

import pygame

from acts.act_two.state import BruteAftershockPhase
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


BRUTE_AFTERSHOCK_EXPLOSION_MS = 520

_CRACK_DARK = (25, 14, 13)
_CRACK_GLOW = (137, 43, 24)
_CRACK_HOT = (240, 105, 45)
_DUST_COLOR = (91, 75, 65)


def _draw_crack_pattern(
    marker,
    column: int,
    row: int,
    glow_alpha: int,
    hot: bool = False,
) -> None:
    randomizer = random.Random(
        column * 92821 + row * 68917
    )
    center = (
        TILE_SIZE // 2,
        TILE_SIZE // 2,
    )

    for branch_index in range(7):
        angle = (
            branch_index * math.tau / 7
            + randomizer.uniform(-0.34, 0.34)
        )
        middle_distance = randomizer.randint(8, 14)
        end_distance = randomizer.randint(19, 29)

        middle = (
            round(
                center[0]
                + math.cos(angle) * middle_distance
            ),
            round(
                center[1]
                + math.sin(angle) * middle_distance
            ),
        )
        bend_angle = angle + randomizer.uniform(-0.38, 0.38)
        end = (
            round(
                middle[0]
                + math.cos(bend_angle)
                * (end_distance - middle_distance)
            ),
            round(
                middle[1]
                + math.sin(bend_angle)
                * (end_distance - middle_distance)
            ),
        )

        pygame.draw.lines(
            marker,
            (*_CRACK_DARK, 225),
            False,
            (center, middle, end),
            4,
        )
        pygame.draw.lines(
            marker,
            (
                *(_CRACK_HOT if hot else _CRACK_GLOW),
                glow_alpha,
            ),
            False,
            (center, middle, end),
            1 if not hot else 2,
        )

        if branch_index % 2 == 0:
            fork_angle = bend_angle + randomizer.choice(
                (-0.65, 0.65)
            )
            fork_length = randomizer.randint(5, 10)
            fork_end = (
                round(
                    middle[0]
                    + math.cos(fork_angle) * fork_length
                ),
                round(
                    middle[1]
                    + math.sin(fork_angle) * fork_length
                ),
            )
            pygame.draw.line(
                marker,
                (*_CRACK_DARK, 210),
                middle,
                fork_end,
                3,
            )
            pygame.draw.line(
                marker,
                (
                    *(_CRACK_HOT if hot else _CRACK_GLOW),
                    glow_alpha,
                ),
                middle,
                fork_end,
                1,
            )


def _draw_warning_cell(
    screen,
    column: int,
    row: int,
    current_time: int,
) -> None:
    left = MAP_OFFSET_X + column * TILE_SIZE
    top = MAP_OFFSET_Y + row * TILE_SIZE
    pulse = (
        math.sin(
            current_time / 145
            + column * 0.71
            + row * 0.39
        )
        + 1
    ) / 2

    marker = pygame.Surface(
        (TILE_SIZE, TILE_SIZE),
        pygame.SRCALPHA,
    )

    pygame.draw.circle(
        marker,
        (73, 20, 13, round(20 + pulse * 24)),
        (TILE_SIZE // 2, TILE_SIZE // 2),
        round(TILE_SIZE * 0.42),
    )

    _draw_crack_pattern(
        marker,
        column,
        row,
        round(105 + pulse * 90),
    )

    center = TILE_SIZE // 2
    pygame.draw.circle(
        marker,
        (226, 80, 34, round(120 + pulse * 100)),
        (center, center),
        round(2 + pulse * 2),
    )

    screen.blit(marker, (left, top))


def _draw_eruption_cell(
    screen,
    column: int,
    row: int,
    elapsed: int,
) -> None:
    progress = min(
        1,
        elapsed / BRUTE_AFTERSHOCK_EXPLOSION_MS,
    )
    visibility = 1 - progress
    left = MAP_OFFSET_X + column * TILE_SIZE
    top = MAP_OFFSET_Y + row * TILE_SIZE

    marker = pygame.Surface(
        (TILE_SIZE, TILE_SIZE),
        pygame.SRCALPHA,
    )
    center = (
        TILE_SIZE // 2,
        TILE_SIZE // 2,
    )

    flash_radius = round(
        5 + progress * TILE_SIZE * 0.46
    )

    pygame.draw.circle(
        marker,
        (
            111,
            29,
            14,
            round(135 * visibility),
        ),
        center,
        flash_radius,
    )
    pygame.draw.circle(
        marker,
        (
            *_CRACK_HOT,
            round(235 * visibility),
        ),
        center,
        flash_radius,
        width=3,
    )

    _draw_crack_pattern(
        marker,
        column,
        row,
        round(255 * visibility),
        hot=True,
    )

    randomizer = random.Random(
        column * 11887 + row * 73127
    )

    for particle_index in range(11):
        angle = (
            particle_index * math.tau / 11
            + randomizer.uniform(-0.2, 0.2)
        )
        distance = (
            5
            + progress
            * randomizer.randint(18, 31)
        )
        lift = (
            math.sin(math.pi * progress)
            * randomizer.randint(5, 15)
        )
        particle_position = (
            round(
                center[0]
                + math.cos(angle) * distance
            ),
            round(
                center[1]
                + math.sin(angle) * distance
                - lift
            ),
        )
        particle_size = (
            3 if particle_index % 4 == 0 else 2
        )
        particle_color = (
            *_DUST_COLOR,
            round(220 * visibility),
        )

        pygame.draw.rect(
            marker,
            particle_color,
            (
                particle_position[0]
                - particle_size // 2,
                particle_position[1]
                - particle_size // 2,
                particle_size,
                particle_size,
            ),
        )

    screen.blit(marker, (left, top))


def draw_brute_aftershocks(
    screen,
    floor,
    current_time: int,
) -> None:
    for aftershock in floor.brute_aftershocks:
        for column, row in aftershock.cells:
            if (column, row) not in floor.visible_cells:
                continue

            if (
                aftershock.phase
                is BruteAftershockPhase.WARNING
            ):
                if (
                    aftershock.warning_visible_at < 0
                    or current_time
                    < aftershock.warning_visible_at
                ):
                    continue

                _draw_warning_cell(
                    screen,
                    column,
                    row,
                    current_time,
                )
                continue

            elapsed = (
                current_time
                - aftershock.eruption_started_at
            )

            if (
                aftershock.eruption_started_at >= 0
                and 0
                <= elapsed
                < BRUTE_AFTERSHOCK_EXPLOSION_MS
            ):
                _draw_eruption_cell(
                    screen,
                    column,
                    row,
                    elapsed,
                )


__all__ = ["draw_brute_aftershocks"]
