from functools import lru_cache

import pygame

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
        source = pygame.image.load(
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


def draw_oracle_statue(screen, enemy, sprites):
    states = _load_head_states()
    size = TILE_SIZE * 3

    position = (
        MAP_OFFSET_X + (enemy.column - 1) * TILE_SIZE,
        MAP_OFFSET_Y + (enemy.row - 1) * TILE_SIZE,
    )
    screen.blit(sprites["oracle_base"], position)

    progress = max(0.0, min(1.0, enemy.oracle_eye_progress))

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

    if progress >= 1.0 and enemy.oracle_cast_amount > 0:
        head = _blend_heads(
            head,
            states["cast"],
            enemy.oracle_cast_amount,
        )

    angle = enemy.oracle_head_angle
    pivot = pygame.Vector2(size * 0.5, size * 0.625)
    local_center = pygame.Vector2(size * 0.5, size * 0.5)
    world_pivot = pygame.Vector2(position) + pivot

    rotated_center = (
        world_pivot
        + (local_center - pivot).rotate(-angle)
    )

    if abs(angle) > 0.001:
        enlarged = pygame.transform.scale(
            head,
            (
                size * HEAD_RENDER_SCALE,
                size * HEAD_RENDER_SCALE,
            ),
        )
        rotated = pygame.transform.rotate(enlarged, angle)
        head = pygame.transform.smoothscale(
            rotated,
            (
                max(
                    1,
                    round(rotated.get_width() / HEAD_RENDER_SCALE),
                ),
                max(
                    1,
                    round(rotated.get_height() / HEAD_RENDER_SCALE),
                ),
            ),
        )

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
