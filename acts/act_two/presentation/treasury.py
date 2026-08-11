import math

import pygame

from acts.act_two.state import TreasuryTrialPhase
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


def _cell_top_left(position):
    return (
        MAP_OFFSET_X + position[0] * TILE_SIZE,
        MAP_OFFSET_Y + position[1] * TILE_SIZE,
    )


def _draw_statue_glow(screen, position, active, current_time):
    pulse = (math.sin(current_time / 310) + 1) / 2
    color = (162, 38, 34) if active else (205, 137, 52)
    center = 48
    glow = pygame.Surface((96, 96), pygame.SRCALPHA)
    for radius, alpha in (
        (42, 6),
        (32, 10),
        (22, 16),
    ):
        pygame.draw.circle(
            glow,
            (*color, round(alpha * (0.8 + pulse * 0.2))),
            (center, center),
            radius,
        )
    left, top = _cell_top_left(position)
    screen.blit(glow, (left - 32, top - 32))


def _draw_reward_effect(screen, position, current_time):
    pulse = (math.sin(current_time / 180) + 1) / 2
    left, top = _cell_top_left(position)
    center_x = left + TILE_SIZE // 2
    center_y = top + TILE_SIZE // 2
    effect = pygame.Surface((64, 64), pygame.SRCALPHA)
    local_center = (32, 32)
    for radius, alpha in (
        (24, 12),
        (17, 22),
        (10, 38),
    ):
        pygame.draw.circle(
            effect,
            (219, 178, 72, round(alpha * (0.75 + pulse * 0.25))),
            local_center,
            radius,
        )
    shard_y = 32 - round(pulse * 2)
    pygame.draw.polygon(
        effect,
        (255, 237, 153, 245),
        (
            (32, shard_y - 8),
            (37, shard_y),
            (32, shard_y + 8),
            (27, shard_y),
        ),
    )
    pygame.draw.polygon(
        effect,
        (255, 255, 224, 255),
        (
            (32, shard_y - 5),
            (34, shard_y),
            (32, shard_y + 4),
            (30, shard_y),
        ),
    )
    orbit = 13 + pulse * 2
    for index in range(4):
        angle = index * math.tau / 4 + current_time / 700
        pygame.draw.circle(
            effect,
            (255, 214, 102, 180),
            (
                round(32 + math.cos(angle) * orbit),
                round(32 + math.sin(angle) * orbit),
            ),
            1,
        )
    screen.blit(effect, (center_x - 32, center_y - 32))


def draw_act_two_treasury(
    screen,
    treasury,
    sprites,
    visible_cells,
    current_time,
) -> None:
    if treasury is None:
        return

    active = treasury.phase is TreasuryTrialPhase.ACTIVE
    door_position = treasury.door_position
    if active and door_position in visible_cells:
        orientation = treasury.door_orientation
        screen.blit(
            sprites[f"treasury_gate_{orientation}"],
            _cell_top_left(door_position),
        )

    statue_names = ("knight", "hooded")
    for position, statue_name in zip(
        treasury.statue_positions,
        statue_names,
    ):
        if position not in visible_cells:
            continue
        _draw_statue_glow(screen, position, active, current_time)
        state_suffix = "_red" if active else ""
        screen.blit(
            sprites[f"treasury_guardian_{statue_name}{state_suffix}"],
            _cell_top_left(position),
        )

    chest_position = treasury.chest_position
    if chest_position not in visible_cells:
        return
    if treasury.phase in (
        TreasuryTrialPhase.DORMANT,
        TreasuryTrialPhase.ACTIVE,
    ):
        screen.blit(
            sprites["treasury_chest"],
            _cell_top_left(chest_position),
        )
    elif treasury.phase is TreasuryTrialPhase.REWARD_AVAILABLE:
        _draw_reward_effect(screen, chest_position, current_time)


__all__ = ["draw_act_two_treasury"]
