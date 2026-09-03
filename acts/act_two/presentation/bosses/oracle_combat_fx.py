import math
from functools import lru_cache

import pygame
import resource_store as resources

from acts.act_two.presentation.bosses.oracle_balance import (
    IMPACT_MS,
)
from presentation.layout import (
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    PROJECT_ROOT,
)
from settings import TILE_SIZE


@lru_cache(maxsize=1)
def _load_effects():
    root = (
        PROJECT_ROOT
        / "assets/sprites/act_2/bosses/oracle"
    )
    result = {"sphere": [], "fire": []}

    for index in range(3):
        source = resources.load_image(
            str(
                root
                / "projectiles"
                / f"projectiles_{index:02d}.png"
            ),
        ).convert_alpha()
        result["sphere"].append(
            pygame.transform.scale(source, (TILE_SIZE, TILE_SIZE)),
        )

    for index in range(5):
        source = resources.load_image(
            str(
                root
                / "blackfire"
                / f"blackfire_{index:02d}.png"
            ),
        ).convert_alpha()
        result["fire"].append(
            pygame.transform.scale(source, (TILE_SIZE, TILE_SIZE)),
        )

    return result


def _state(floor):
    state = floor.oracle_combat
    if state is None or state.caster.health <= 0:
        return None
    return state


def _cell_center(position):
    return pygame.Vector2(
        (position[0] + 0.5) * TILE_SIZE,
        (position[1] + 0.5) * TILE_SIZE,
    )


def _eye_position(caster):
    size = TILE_SIZE * 3
    origin = pygame.Vector2(
        (caster.column - 1) * TILE_SIZE,
        (caster.row - 1) * TILE_SIZE,
    )
    pivot = pygame.Vector2(size * 0.5, size * 0.625)
    eye = pygame.Vector2(size * 0.5, size / 3)

    return (
        origin
        + pivot
        + (eye - pivot).rotate(-caster.oracle_head_angle)
    )


def _flight_progress(state, current_time):
    return max(
        0.0,
        min(
            1.0,
            (current_time - state.started_at)
            / max(1, state.impact_at - state.started_at),
        ),
    )


def _sphere_position(state, current_time, path):
    start = _eye_position(state.caster)
    target = _cell_center(path[-1])
    progress = _flight_progress(state, current_time)
    return start.lerp(target, progress)


def _fire_cells(state, current_time):
    cells = list(state.ground_fire.cells)

    if (
        state.kind == "line"
        and state.phase == "flight"
        and current_time >= state.started_at
    ):
        progress = _flight_progress(state, current_time)
        paths = state.paths or (state.cells,)

        cells.extend(
            position
            for path in paths
            for position in path[:int(len(path) * progress)]
        )

    return tuple(dict.fromkeys(cells))


def oracle_attack_lights(floor, current_time):
    state = _state(floor)
    if state is None:
        return []

    result = []

    if (
        state.phase == "flight"
        and state.kind != "radial"
        and current_time >= state.started_at
    ):
        for path in state.paths or (state.cells,):
            if not path:
                continue

            position = _sphere_position(
                state,
                current_time,
                path,
            )
            result.append(
                (
                    position.x / TILE_SIZE,
                    position.y / TILE_SIZE,
                    1.0,
                    170,
                    (16, 4, 3),
                ),
            )

    for column, row in _fire_cells(state, current_time):
        result.append(
            (
                column + 0.5,
                row + 0.5,
                0.8,
                180,
                (13, 3, 2),
            ),
        )

    return result


def _draw_fire_sprites(
    screen,
    sprites,
    cells,
    current_time,
    alpha,
):
    for column, row in cells:
        frame = (
            (current_time + column * 71 + row * 113) // 120
        ) % 5
        sprite = sprites["fire"][frame]

        if alpha < 255:
            sprite = sprite.copy()
            sprite.set_alpha(alpha)

        screen.blit(
            sprite,
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )


def draw_oracle_blackfire(screen, floor, current_time):
    state = _state(floor)
    if state is None:
        return

    sprites = _load_effects()
    live_cells = _fire_cells(state, current_time)

    if live_cells:
        _draw_fire_sprites(
            screen,
            sprites,
            live_cells,
            current_time,
            255,
        )

    ground_fire = state.ground_fire
    impact_age = (
        current_time - ground_fire.impact_started_at
    )

    if (
        ground_fire.impact_started_at >= 0
        and 0 <= impact_age < IMPACT_MS
    ):
        alpha = round(
            255 * (1.0 - impact_age / IMPACT_MS)
        )
        _draw_fire_sprites(
            screen,
            sprites,
            ground_fire.impact_cells,
            current_time,
            alpha,
        )


def _draw_marker(screen, position, current_time, delayed):
    column, row = position
    rectangle = pygame.Rect(
        MAP_OFFSET_X + column * TILE_SIZE + 2,
        MAP_OFFSET_Y + row * TILE_SIZE + 2,
        TILE_SIZE - 4,
        TILE_SIZE - 4,
    )
    pulse = (math.sin(current_time / 160) + 1.0) / 2
    color = (
        (183, 98, 75)
        if delayed
        else (179, 66, 75)
    )

    patch = pygame.Surface(rectangle.size, pygame.SRCALPHA)
    patch.fill((*color, round(22 + pulse * 22)))
    screen.blit(patch, rectangle)

    pygame.draw.rect(
        screen,
        (10, 5, 9),
        rectangle.inflate(2, 2),
        2,
    )
    pygame.draw.rect(screen, color, rectangle, 1)

    radius = 5 if delayed else 8
    pygame.draw.circle(
        screen,
        color,
        rectangle.center,
        radius,
        1,
    )
    if delayed:
        pygame.draw.circle(
            screen,
            (213, 135, 107),
            rectangle.center,
            2,
        )


def _draw_radial_charge(screen, state, current_time):
    if (
        state.kind != "radial"
        or state.phase not in ("warning", "flight")
    ):
        return

    center = (
        MAP_OFFSET_X
        + round((state.caster.column + 0.5) * TILE_SIZE),
        MAP_OFFSET_Y
        + round((state.caster.row + 0.5) * TILE_SIZE),
    )
    pulse = (math.sin(current_time / 90) + 1.0) / 2
    base_radius = round(TILE_SIZE * (2.15 + pulse * 0.18))
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

    for index in range(3):
        radius = base_radius - index * 9
        alpha = round(55 + pulse * 45 - index * 12)

        pygame.draw.circle(
            overlay,
            (128, 28, 31, max(15, alpha)),
            center,
            radius,
            2,
        )

    for index in range(12):
        angle = (
            index * math.tau / 12
            + current_time / 850
        )
        distance = base_radius - 5 - index % 3 * 7
        point = (
            round(center[0] + math.cos(angle) * distance),
            round(center[1] + math.sin(angle) * distance),
        )
        radius = 2 if index % 3 == 0 else 1

        pygame.draw.circle(
            overlay,
            (177, 58, 48, round(115 + pulse * 80)),
            point,
            radius,
        )

    screen.blit(overlay, (0, 0))


def _draw_impact_effect(
    screen,
    cells,
    started_at,
    current_time,
    offset,
):
    age = current_time - started_at

    if started_at < 0 or not 0 <= age < IMPACT_MS:
        return

    progress = age / IMPACT_MS
    radius = round(5 + progress * 18)
    color = (
        round(167 * (1.0 - progress)),
        round(66 * (1.0 - progress)),
        round(61 * (1.0 - progress)),
    )

    for cell_index, cell in enumerate(cells):
        position = _cell_center(cell) + offset
        center = (round(position.x), round(position.y))

        pygame.draw.circle(
            screen,
            color,
            center,
            radius,
            max(1, round(3 * (1.0 - progress))),
        )

        for index in range(6):
            angle = (
                index * math.tau / 6
                + cell_index * 0.7
            )
            distance = radius * (0.7 + index % 2 * 0.3)
            point = (
                round(
                    position.x
                    + math.cos(angle) * distance
                ),
                round(
                    position.y
                    + math.sin(angle) * distance
                ),
            )
            pygame.draw.circle(
                screen,
                color,
                point,
                1,
            )


def draw_oracle_attack_fx(screen, floor, current_time):
    state = _state(floor)
    if state is None:
        return

    offset = pygame.Vector2(MAP_OFFSET_X, MAP_OFFSET_Y)

    _draw_radial_charge(
        screen,
        state,
        current_time,
    )

    warning_visible = (
        state.phase == "warning"
        or (
            state.phase == "flight"
            and current_time < state.started_at
        )
    )

    if warning_visible:
        for position in state.cells:
            if position in floor.visible_cells:
                _draw_marker(
                    screen,
                    position,
                    current_time,
                    False,
                )

    if (
        state.phase == "flight"
        and state.kind != "radial"
        and state.started_at <= current_time < state.impact_at
    ):
        sprites = _load_effects()

        for path in state.paths or (state.cells,):
            if not path:
                continue

            for index in range(4, -1, -1):
                sample_time = current_time - index * 35

                if sample_time < state.started_at:
                    continue

                position = (
                    _sphere_position(
                        state,
                        sample_time,
                        path,
                    )
                    + offset
                )
                frame = (sample_time // 85) % 3
                sprite = sprites["sphere"][frame].copy()
                sprite.set_alpha(
                    255
                    if index == 0
                    else 95 - index * 15
                )

                if index == 0:
                    pulse = (
                        1.0
                        + math.sin(current_time / 55) * 0.06
                    )
                    size = max(
                        1,
                        round(TILE_SIZE * pulse),
                    )
                    sprite = pygame.transform.scale(
                        sprite,
                        (size, size),
                    )

                screen.blit(
                    sprite,
                    sprite.get_rect(
                        center=(
                            round(position.x),
                            round(position.y),
                        ),
                    ),
                )

    _draw_impact_effect(
        screen,
        state.impact_cells or state.cells,
        state.impact_fx_at,
        current_time,
        offset,
    )

    _draw_impact_effect(
        screen,
        state.ground_fire.impact_cells,
        state.ground_fire.impact_started_at,
        current_time,
        offset,
    )
