import math

import pygame

from acts.act_two.consumables import SCROLL_OF_ARCANE_IMPULSE
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


_ARCANE_IMPULSE_EFFECT_MS = 420


def _cell_center(position):
    return (
        MAP_OFFSET_X + position[0] * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + position[1] * TILE_SIZE + TILE_SIZE // 2,
    )


def draw_scroll_effect(screen, game_state, current_time: int) -> None:
    state = game_state.player.act_two
    if (
        state.scroll_effect_kind != SCROLL_OF_ARCANE_IMPULSE
        or state.scroll_effect_origin is None
        or state.scroll_effect_target is None
    ):
        return
    elapsed = current_time - state.scroll_effect_started_at
    if not 0 <= elapsed < _ARCANE_IMPULSE_EFFECT_MS:
        return

    origin = _cell_center(state.scroll_effect_origin)
    target = _cell_center(state.scroll_effect_target)
    travel = min(1.0, elapsed / 300)
    eased_travel = 1 - (1 - travel) ** 2
    head = (
        round(origin[0] + (target[0] - origin[0]) * eased_travel),
        round(origin[1] + (target[1] - origin[1]) * eased_travel),
    )
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    if travel < 1:
        distance = math.dist(origin, head)
        if distance > 0:
            direction = (
                (head[0] - origin[0]) / distance,
                (head[1] - origin[1]) / distance,
            )
            trail_start = (
                round(head[0] - direction[0] * min(42, distance)),
                round(head[1] - direction[1] * min(42, distance)),
            )
            pygame.draw.line(
                overlay,
                (139, 18, 35, 105),
                trail_start,
                head,
                11,
            )
            pygame.draw.line(
                overlay,
                (255, 62, 76, 220),
                trail_start,
                head,
                4,
            )
        pygame.draw.circle(overlay, (255, 169, 155, 255), head, 5)
        pygame.draw.circle(overlay, (255, 38, 55, 210), head, 10, width=3)
    else:
        impact = (elapsed - 300) / 120
        radius = round(7 + impact * 22)
        alpha = round(220 * (1 - impact))
        pygame.draw.circle(
            overlay,
            (255, 44, 62, alpha),
            target,
            radius,
            width=3,
        )
    screen.blit(overlay, (0, 0))


__all__ = ["draw_scroll_effect"]
