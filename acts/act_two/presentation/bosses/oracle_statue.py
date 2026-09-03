import math
from functools import lru_cache

import pygame
import resource_store as resources

from acts.act_two.presentation.bosses.oracle_death import (
    draw_oracle_death_sprite,
)
from acts.act_two.presentation.bosses.oracle_phase_transition import (
    DETACH_END_MS,
    DETACH_START_MS,
    TREMOR_START_MS,
)
from presentation.layout import (
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    PROJECT_ROOT,
)
from settings import TILE_SIZE


HEAD_RENDER_SCALE = 4


@lru_cache(maxsize=1)
def _load_head_states():
    root = (
        PROJECT_ROOT
        / "assets/sprites/act_2/bosses/oracle/idle"
    )
    size = TILE_SIZE * 3
    images = {}

    for name, filename in (
        ("closed", "oracle_head_closed_eye.png"),
        ("half", "oracle_head_half_open_eye.png"),
        ("open", "oracle_head.png"),
        ("eye", "oracle_eye_idle.png"),
        ("cast_eye", "oracle_eye_cast.png"),
    ):
        source = resources.load_image(
            str(root / filename)
        ).convert_alpha()
        images[name] = pygame.transform.scale(
            source,
            (size, size),
        )

    half = images["eye"].copy()
    half.blit(images["half"], (0, 0))

    opened = images["eye"].copy()
    opened.blit(images["open"], (0, 0))

    casting = images["cast_eye"].copy()
    casting.blit(images["open"], (0, 0))

    return {
        "closed": images["closed"].premul_alpha(),
        "half": half.premul_alpha(),
        "open": opened.premul_alpha(),
        "cast": casting.premul_alpha(),
    }


@lru_cache(maxsize=1)
def _load_phase_two_heads():
    root = (
        PROJECT_ROOT
        / "assets/sprites/act_2/bosses/oracle/idle/head"
    )
    size = TILE_SIZE * 2
    body = pygame.transform.scale(
        resources.load_image(
            str(root / "head_alone.png")
        ).convert_alpha(),
        (size, size),
    )
    states = {}

    for name, filename in (
        ("idle", "head_alone_eye_idle.png"),
        ("cast", "head_alone_eye_cast.png"),
        ("shockwave", "head_alone_eye_shockwave.png"),
    ):
        eye = pygame.transform.scale(
            resources.load_image(
                str(root / filename)
            ).convert_alpha(),
            (size, size),
        )
        image = eye.copy()
        image.blit(body, (0, 0))
        states[name] = image.premul_alpha()

    return states


def _blend_heads(first, second, progress):
    progress = max(0.0, min(1.0, progress))
    progress = progress * progress * (3.0 - 2.0 * progress)
    weight = round(255 * progress)

    if weight == 0:
        return first
    if weight == 255:
        return second

    result = first.copy()
    result.fill(
        (255 - weight,) * 4,
        special_flags=pygame.BLEND_RGBA_MULT,
    )

    overlay = second.copy()
    overlay.fill(
        (weight,) * 4,
        special_flags=pygame.BLEND_RGBA_MULT,
    )
    result.blit(
        overlay,
        (0, 0),
        special_flags=pygame.BLEND_RGBA_ADD,
    )

    return result


def _rotated_sprite(image, angle):
    if abs(angle) <= 0.001:
        return image

    enlarged = pygame.transform.scale(
        image,
        (
            image.get_width() * HEAD_RENDER_SCALE,
            image.get_height() * HEAD_RENDER_SCALE,
        ),
    )
    rotated = pygame.transform.rotate(
        enlarged,
        angle,
    )

    return pygame.transform.smoothscale(
        rotated,
        (
            max(
                1,
                round(
                    rotated.get_width()
                    / HEAD_RENDER_SCALE
                ),
            ),
            max(
                1,
                round(
                    rotated.get_height()
                    / HEAD_RENDER_SCALE
                ),
            ),
        ),
    )


def _draw_detachment_effect(
    screen,
    enemy,
    base_position,
):
    elapsed = enemy.oracle_phase_elapsed

    if not (
        DETACH_START_MS - 260
        <= elapsed
        < DETACH_END_MS + 500
    ):
        return

    center = (
        base_position[0] + TILE_SIZE * 1.5,
        base_position[1] + TILE_SIZE * 1.85,
    )
    layer = pygame.Surface(
        (220, 220),
        pygame.SRCALPHA,
    )
    local_center = (110, 110)
    progress = max(
        0.0,
        min(
            1.0,
            (elapsed - DETACH_START_MS + 260)
            / (DETACH_END_MS - DETACH_START_MS + 760),
        ),
    )
    pulse = math.sin(math.pi * progress)
    radius = round(18 + progress * 74)

    pygame.draw.circle(
        layer,
        (113, 27, 31, round(110 * pulse)),
        local_center,
        radius,
        max(2, round(7 - progress * 4)),
    )

    for index in range(18):
        angle = (
            index * math.tau / 18
            + elapsed / 900
        )
        distance = (
            14
            + progress * (34 + index % 5 * 8)
        )
        x = round(
            local_center[0]
            + math.cos(angle) * distance
        )
        y = round(
            local_center[1]
            + math.sin(angle) * distance * 0.65
        )
        length = 3 + index % 4

        pygame.draw.line(
            layer,
            (
                137 + index % 3 * 12,
                30,
                34,
                round(150 * pulse),
            ),
            (x, y),
            (
                round(x + math.cos(angle) * length),
                round(y + math.sin(angle) * length),
            ),
            2,
        )

    screen.blit(
        layer,
        layer.get_rect(
            center=(
                round(center[0]),
                round(center[1]),
            ),
        ),
    )


def _draw_phase_one_head(
    screen,
    enemy,
    base_position,
):
    states = _load_head_states()
    size = TILE_SIZE * 3
    progress = max(
        0.0,
        min(1.0, enemy.oracle_eye_progress),
    )

    if progress < 0.4:
        head = _blend_heads(
            states["closed"],
            states["half"],
            progress / 0.4,
        )
    elif progress < 0.6:
        head = states["half"]
    else:
        head = _blend_heads(
            states["half"],
            states["open"],
            (progress - 0.6) / 0.4,
        )

    if (
        progress >= 1.0
        and enemy.oracle_cast_amount > 0
    ):
        head = _blend_heads(
            head,
            states["cast"],
            enemy.oracle_cast_amount,
        )

    angle = enemy.oracle_head_angle
    offset_x = 0
    offset_y = 0

    if enemy.oracle_phase == 0:
        intensity = max(
            0.0,
            min(
                1.0,
                (
                    enemy.oracle_phase_elapsed
                    - TREMOR_START_MS
                )
                / (
                    DETACH_START_MS
                    - TREMOR_START_MS
                ),
            ),
        )
        offset_x = round(
            math.sin(
                enemy.oracle_phase_elapsed / 240
            )
            * 1.5
            * intensity
        )
        offset_y = round(
            math.sin(
                enemy.oracle_phase_elapsed / 320
            )
            * 0.8
            * intensity
        )
        angle += (
            math.sin(
                enemy.oracle_phase_elapsed / 420
            )
            * 0.7
            * intensity
        )

    pivot = pygame.Vector2(
        size * 0.5,
        size * 0.625,
    )
    local_center = pygame.Vector2(
        size * 0.5,
        size * 0.5,
    )
    world_pivot = (
        pygame.Vector2(base_position)
        + pivot
        + pygame.Vector2(offset_x, offset_y)
    )
    rotated_center = (
        world_pivot
        + (local_center - pivot).rotate(-angle)
    )
    head = _rotated_sprite(head, angle)

    screen.blit(
        head,
        head.get_rect(
            center=(
                round(rotated_center.x),
                round(rotated_center.y),
            ),
        ),
        special_flags=pygame.BLEND_PREMULTIPLIED,
    )


def _draw_phase_two_head(
    screen,
    enemy,
    current_time,
):
    states = _load_phase_two_heads()
    eye_state = enemy.oracle_phase_two_eye

    if eye_state not in states:
        eye_state = "idle"

    head = states[eye_state]
    column = (
        enemy.oracle_render_column
        if enemy.oracle_render_column is not None
        else enemy.column
    )
    row = (
        enemy.oracle_render_row
        if enemy.oracle_render_row is not None
        else enemy.row
    )

    hover_x = 0.0
    hover_y = 0.0
    angle = 0.0

    if enemy.oracle_phase == 2:
        hover_x = (
                math.sin(current_time / 480) * 1.0
                + math.sin(current_time / 730) * 0.35
        )
        hover_y = (
                math.sin(current_time / 560) * 1.5
                + math.sin(current_time / 890) * 0.45
        )
        angle = (
                math.sin(current_time / 700) * 0.8
                + math.sin(current_time / 1100) * 0.25
        )
    else:
        intensity = max(
            0.0,
            min(
                1.0,
                (
                        enemy.oracle_phase_elapsed
                        - DETACH_START_MS
                )
                / (
                        DETACH_END_MS
                        - DETACH_START_MS
                ),
            ),
        )
        hover_x = (
                math.sin(
                    enemy.oracle_phase_elapsed / 260
                )
                * 1.2
                * intensity
        )
        hover_y = (
                math.sin(
                    enemy.oracle_phase_elapsed / 330
                )
                * 1.0
                * intensity
        )
        angle = (
                math.sin(
                    enemy.oracle_phase_elapsed / 390
                )
                * 1.2
                * intensity
        )

    center = (
        MAP_OFFSET_X
        + column * TILE_SIZE
        + TILE_SIZE
        + hover_x,
        MAP_OFFSET_Y
        + row * TILE_SIZE
        + TILE_SIZE
        + hover_y,
    )
    head = _rotated_sprite(head, angle)

    screen.blit(
        head,
        head.get_rect(
            center=(
                round(center[0]),
                round(center[1]),
            ),
        ),
        special_flags=pygame.BLEND_PREMULTIPLIED,
    )


def draw_oracle_statue(
    screen,
    enemy,
    sprites,
    current_time,
):
    base_column = (
        enemy.oracle_base_column
        if enemy.oracle_base_column is not None
        else enemy.column
    )
    base_row = (
        enemy.oracle_base_row
        if enemy.oracle_base_row is not None
        else enemy.row
    )
    base_position = (
        MAP_OFFSET_X
        + (base_column - 1) * TILE_SIZE,
        MAP_OFFSET_Y
        + (base_row - 1) * TILE_SIZE,
    )

    screen.blit(
        sprites["oracle_base"],
        base_position,
    )

    if draw_oracle_death_sprite(
        screen,
        enemy,
    ):
        return

    if enemy.oracle_phase == 0:
        _draw_detachment_effect(
            screen,
            enemy,
            base_position,
        )

    if (
        enemy.oracle_phase == 1
        or (
            enemy.oracle_phase == 0
            and not enemy.oracle_phase_detached
        )
    ):
        _draw_phase_one_head(
            screen,
            enemy,
            base_position,
        )
    else:
        _draw_phase_two_head(
            screen,
            enemy,
            current_time,
        )
