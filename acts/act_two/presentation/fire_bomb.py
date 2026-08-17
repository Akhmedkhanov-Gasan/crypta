import math

import pygame

from acts.act_two.consumables import (
    fire_bomb_zone_cells,
    is_valid_fire_bomb_target,
)
from acts.act_two.settings import FIRE_BOMB_FLIGHT_MS, FIRE_FRAME_MS
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


_IMPACT_EFFECT_MS = 320


def _cell_center(position):
    return (
        MAP_OFFSET_X + position[0] * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + position[1] * TILE_SIZE + TILE_SIZE // 2,
    )


def _arc_point(origin, target, progress):
    origin_x, origin_y = _cell_center(origin)
    target_x, target_y = _cell_center(target)
    distance = math.hypot(target_x - origin_x, target_y - origin_y)
    arc_height = max(30, min(82, round(distance * 0.28)))
    return (
        round(origin_x + (target_x - origin_x) * progress),
        round(
            origin_y
            + (target_y - origin_y) * progress
            - 4 * arc_height * progress * (1 - progress)
        ),
    )


def _draw_dashed_trajectory(screen, origin, target):
    points = [
        _arc_point(origin, target, step / 28)
        for step in range(29)
    ]
    for step in range(0, 28, 4):
        pygame.draw.line(
            screen,
            (245, 207, 116),
            points[step],
            points[min(step + 2, 28)],
            width=1,
        )
        pygame.draw.circle(
            screen,
            (255, 236, 174),
            points[step],
            1,
        )


def draw_fire_bomb_targeting(screen, game_state, target):
    player = game_state.player
    if (
        not player.act_two.fire_bomb_aiming
        or not is_valid_fire_bomb_target(game_state, target)
    ):
        return

    zone_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    zone_surface.fill((194, 62, 28, 66))
    pygame.draw.rect(
        zone_surface,
        (255, 143, 52, 205),
        zone_surface.get_rect(),
        width=1,
    )
    for column, row in fire_bomb_zone_cells(
        game_state.floor.map,
        target,
    ):
        screen.blit(
            zone_surface,
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )

    target_center = _cell_center(target)
    pygame.draw.circle(screen, (255, 226, 146), target_center, 4, width=1)
    _draw_dashed_trajectory(
        screen,
        (
            game_state.floor.player_column,
            game_state.floor.player_row,
        ),
        target,
    )


def draw_fire_zones(screen, game_state, sprites, current_time):
    for zone in game_state.floor.fire_zones:
        elapsed = current_time - zone.created_at
        if elapsed < FIRE_BOMB_FLIGHT_MS:
            continue
        for column, row in zone.cells:
            if (column, row) not in game_state.floor.visible_cells:
                continue
            phase_offset = (column * 3 + row * 5) % 4
            frame_index = (
                current_time // FIRE_FRAME_MS + phase_offset
            ) % 4
            screen.blit(
                sprites[f"fire_{frame_index}"],
                (
                    MAP_OFFSET_X + column * TILE_SIZE,
                    MAP_OFFSET_Y + row * TILE_SIZE,
                ),
            )


def draw_fire_bomb_flight(screen, game_state, sprites, current_time):
    for zone in game_state.floor.fire_zones:
        elapsed = current_time - zone.created_at
        if elapsed < 0:
            continue
        if elapsed < FIRE_BOMB_FLIGHT_MS:
            progress = elapsed / FIRE_BOMB_FLIGHT_MS
            center = _arc_point(zone.origin, zone.center, progress)
            angle = -round(progress * 540)
            sprite = pygame.transform.rotate(sprites["fire_bomb"], angle)
            screen.blit(sprite, sprite.get_rect(center=center))
            continue

        impact_elapsed = elapsed - FIRE_BOMB_FLIGHT_MS
        if impact_elapsed >= _IMPACT_EFFECT_MS:
            continue
        progress = impact_elapsed / _IMPACT_EFFECT_MS
        center = _cell_center(zone.center)
        radius = 4 + round(progress * 17)
        alpha = round(220 * (1 - progress))
        effect = pygame.Surface((48, 48), pygame.SRCALPHA)
        effect_center = (24, 24)
        pygame.draw.circle(
            effect,
            (255, 149, 46, alpha),
            effect_center,
            radius,
            width=2,
        )
        for shard_index in range(6):
            angle = shard_index * math.tau / 6 + 0.35
            distance = 5 + progress * 13
            shard = (
                round(effect_center[0] + math.cos(angle) * distance),
                round(effect_center[1] + math.sin(angle) * distance),
            )
            pygame.draw.rect(
                effect,
                (255, 210, 111, alpha),
                (shard[0] - 1, shard[1] - 1, 2, 2),
            )
        screen.blit(
            effect,
            (center[0] - effect_center[0], center[1] - effect_center[1]),
        )


__all__ = [
    "draw_fire_bomb_flight",
    "draw_fire_bomb_targeting",
    "draw_fire_zones",
]
