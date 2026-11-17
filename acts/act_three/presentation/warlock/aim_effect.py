import math

import pygame

from acts.act_three.combat.warlock_aim import valid_warlock_aim_target
from acts.act_three.presentation.view import _view_position


def draw_warlock_aim_effect(surface, game_state, camera_x, camera_y, current_time, tile_size):
    player = game_state.player
    target = player.warlock_aim_target
    if not player.warlock_basic_aiming or not valid_warlock_aim_target(game_state, target):
        return

    left, top = _view_position(*target, camera_x, camera_y)
    size = round(tile_size * 1.5)
    middle = size // 2
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    pulse = (1 + math.sin(current_time / 155)) * 0.5
    radius = tile_size * (0.35 + pulse * 0.025)
    diameter = round(radius * 2)
    ring = pygame.Rect(0, 0, diameter, diameter)
    ring.center = (middle, middle)

    def polar(angle, distance):
        return (
            round(middle + math.cos(angle) * distance),
            round(middle + math.sin(angle) * distance),
        )

    pygame.draw.circle(
        layer, (50, 15, 74, round(22 + 18 * pulse)), ring.center, round(radius + 6)
    )
    rotation = current_time / 1400
    for index in range(4):
        angle = rotation + index * math.pi / 2
        start, end = angle + 0.27, angle + 1.30
        pygame.draw.arc(layer, (29, 10, 42, 230), ring, start, end, 5)
        pygame.draw.arc(layer, (161, 76, 223, round(164 + 60 * pulse)), ring, start, end, 2)

        shard = (
            polar(angle, radius + 7),
            polar(angle + 0.15, radius + 1),
            polar(angle, radius - 9),
            polar(angle - 0.15, radius + 1),
        )
        pygame.draw.polygon(layer, (38, 13, 52, 245), shard)
        pygame.draw.polygon(layer, (220, 145, 252, 235), shard, width=1)

        mote = polar(-rotation * 1.3 + index * math.pi / 2, radius + 11)
        pygame.draw.circle(layer, (196, 112, 246, round(105 + 120 * pulse)), mote, 2)

    surface.blit(layer, (left + tile_size // 2 - middle, top + tile_size // 2 - middle))
