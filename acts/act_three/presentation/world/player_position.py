import math
from dataclasses import dataclass
from typing import Any

import pygame

from acts.act_three.presentation.berserker import (
    crushing_leap_position,
)
from acts.act_three.presentation.paladin.shield_charge import (
    shield_charge_motion_progress,
)
from acts.act_three.presentation.combat_effects import (
    _player_death_sprite_offset,
)
from acts.act_three.presentation.player_motion import (
    ASSASSIN_SHADOW_STEP_FRAME_COUNT,
)
from acts.act_three.presentation.view import _view_position
from acts.act_three.settings import (
    ARCHER_LEAP_DURATION_MS,
    BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
)
from presentation.layout import ACT_THREE_TILE_SIZE


@dataclass(frozen=True, slots=True)
class PlayerPlacement:
    sprite: pygame.Surface
    position: tuple[int, int]
    leap_progress: float
    leap_start_position: Any
    leap_end_position: tuple[int, int]
    shield_charge_progress: float
    shield_charge_start_position: Any


def calculate_player_placement(
    context,
    player_state,
    player,
    player_sprite,
    current_time,
):
    player_position = (
        round(
            context.locomotion_pose.position[0]
            - context.camera_x
        ),
        round(
            context.locomotion_pose.position[1]
            - context.camera_y
        ),
    )

    if (
        player_state.shadow_step_active
        and player_state.shadow_step_frame
        < ASSASSIN_SHADOW_STEP_FRAME_COUNT // 2
    ):
        player_position = _view_position(
            context.teleport_origin[0],
            context.teleport_origin[1],
            context.camera_x,
            context.camera_y,
        )

    if player_state.death_elapsed is not None:
        death_offset_x, death_offset_y = (
            _player_death_sprite_offset(
                player,
                current_time,
            )
        )
        player_position = (
            player_position[0] + death_offset_x,
            player_position[1] + death_offset_y,
        )

    leap_progress = 0.0
    leap_start_position = None
    leap_end_position = player_position
    shield_charge_progress = 0.0
    shield_charge_start_position = None

    if player_state.shield_charge_active:
        shield_charge_progress = (
            shield_charge_motion_progress(
                player_state.shield_charge_elapsed
            )
        )
        shield_charge_start_position = _view_position(
            player_state.shield_charge_origin[0],
            player_state.shield_charge_origin[1],
            context.camera_x,
            context.camera_y,
        )
        player_position = (
            round(
                shield_charge_start_position[0]
                + (
                    leap_end_position[0]
                    - shield_charge_start_position[0]
                )
                * shield_charge_progress
            ),
            round(
                shield_charge_start_position[1]
                + (
                    leap_end_position[1]
                    - shield_charge_start_position[1]
                )
                * shield_charge_progress
            ),
        )

    elif player_state.leap_active:
        leap_progress = min(
            1,
            player_state.leap_elapsed / ARCHER_LEAP_DURATION_MS,
        )
        eased_progress = 1 - (1 - leap_progress) ** 3
        leap_start_position = _view_position(
            player_state.leap_origin[0],
            player_state.leap_origin[1],
            context.camera_x,
            context.camera_y,
        )
        player_position = (
            round(
                leap_start_position[0]
                + (
                    leap_end_position[0]
                    - leap_start_position[0]
                )
                * eased_progress
            ),
            round(
                leap_start_position[1]
                + (
                    leap_end_position[1]
                    - leap_start_position[1]
                )
                * eased_progress
                - math.sin(math.pi * leap_progress) * 8
            ),
        )
    elif player_state.berserker_leap_travel_active:
        leap_start_position = _view_position(
            player_state.berserker_leap_origin[0],
            player_state.berserker_leap_origin[1],
            context.camera_x,
            context.camera_y,
        )
        player_position = crushing_leap_position(
            leap_start_position,
            leap_end_position,
            player_state.berserker_leap_elapsed,
            BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
            ACT_THREE_TILE_SIZE,
        )

    return PlayerPlacement(
        sprite=player_sprite,
        position=player_position,
        leap_progress=leap_progress,
        leap_start_position=leap_start_position,
        leap_end_position=leap_end_position,
        shield_charge_progress=shield_charge_progress,
        shield_charge_start_position=(
            shield_charge_start_position
        ),
    )
