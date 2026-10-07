import math
from dataclasses import dataclass
from typing import Any

import pygame

from acts.act_three.presentation.assassin import (
    killing_spree_camera_position,
)
from acts.act_three.presentation.berserker import (
    crushing_leap_camera_offset,
    last_rage_camera_offset,
)
from acts.act_three.presentation.camera import (
    act_three_world_view_size,
    update_act_three_camera,
)
from acts.act_three.presentation.combat_effects import (
    _player_death_camera_offset,
    _player_hit_camera_offset,
)
from acts.act_three.presentation.player_locomotion import (
    sample_player_locomotion,
)
from acts.act_three.presentation.view import (
    _camera_position,
    _get_act_three_visibility,
)
from acts.act_three.settings import (
    ASSASSIN_SHADOW_STEP_DURATION_MS,
    BERSERKER_CRUSHING_LEAP_IMPACT_MS,
    BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
    BERSERKER_LAST_RAGE_ANIMATION_MS,
)
from acts.act_three.presentation.paladin.shield_charge import (
    shield_charge_camera_offset,
)
from presentation.layout import ACT_THREE_TILE_SIZE


@dataclass(frozen=True, slots=True)
class WorldRenderContext:
    floor: Any
    view_surface: pygame.Surface
    view_width: int
    view_height: int
    camera_x: int
    camera_y: int
    first_column: int
    first_row: int
    last_column: int
    last_row: int
    tile_assets: dict
    locomotion_pose: Any
    teleport_origin: Any
    transition_started_at: int


def create_world_render_context(
    game_state,
    assets,
    current_time,
):
    floor = game_state.floor
    dungeon_map = floor.map
    view_width, view_height = act_three_world_view_size(floor)

    locomotion_pose = sample_player_locomotion(
        game_state.player,
        floor,
        current_time,
        ACT_THREE_TILE_SIZE,
    )
    camera_player_position = locomotion_pose.position

    killing_spree_camera = killing_spree_camera_position(
        game_state.player,
        floor,
        current_time,
    )
    if killing_spree_camera is not None:
        camera_player_position = killing_spree_camera

    update_act_three_camera(
        floor,
        current_time,
        player_position=camera_player_position,
        cinematic=killing_spree_camera is not None,
    )
    _get_act_three_visibility(floor)

    view_surface = pygame.Surface((view_width, view_height))
    view_surface.fill((0, 0, 0))

    camera_x, camera_y = _camera_position(floor)
    teleport_origin = game_state.player.teleport_camera_origin
    transition_started_at = (
        game_state.player.teleport_transition_started_at
    )

    if teleport_origin is not None and transition_started_at:
        transition_elapsed = current_time - transition_started_at
        if transition_elapsed < ASSASSIN_SHADOW_STEP_DURATION_MS:
            transition_progress = (
                transition_elapsed
                / ASSASSIN_SHADOW_STEP_DURATION_MS
            )
            transition_progress = (
                transition_progress
                * transition_progress
                * (3 - 2 * transition_progress)
            )
            start_camera = _camera_position(
                floor,
                teleport_origin,
            )
            camera_x = round(
                start_camera[0]
                + (
                    camera_x
                    - start_camera[0]
                )
                * transition_progress
            )
            camera_y = round(
                start_camera[1]
                + (
                    camera_y
                    - start_camera[1]
                )
                * transition_progress
            )

    hit_camera_x, hit_camera_y = _player_hit_camera_offset(
        game_state.player,
        current_time,
    )
    death_camera_x, death_camera_y = _player_death_camera_offset(
        game_state.player,
        current_time,
    )
    crushing_leap_camera_x, crushing_leap_camera_y = (
        crushing_leap_camera_offset(
            (
                current_time
                - game_state.player.berserker_crushing_leap_started_at
            ),
            BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
            BERSERKER_CRUSHING_LEAP_IMPACT_MS,
        )
    )
    shield_charge_camera_x, shield_charge_camera_y = (
        shield_charge_camera_offset(
            (
                current_time
                - game_state.player.paladin_shield_charge_started_at
            )
        )
    )
    last_rage_camera_x, last_rage_camera_y = (
        last_rage_camera_offset(
            (
                current_time
                - game_state.player.berserker_last_rage_started_at
            ),
            BERSERKER_LAST_RAGE_ANIMATION_MS,
        )
    )

    camera_x += (
        hit_camera_x
        + death_camera_x
        + crushing_leap_camera_x
        + shield_charge_camera_x
        + last_rage_camera_x
    )
    camera_y += (
        hit_camera_y
        + death_camera_y
        + crushing_leap_camera_y
        + shield_charge_camera_y
        + last_rage_camera_y
    )

    first_column = max(
        0,
        camera_x // ACT_THREE_TILE_SIZE,
    )
    first_row = max(
        0,
        camera_y // ACT_THREE_TILE_SIZE,
    )
    last_column = min(
        len(dungeon_map[0]),
        math.ceil(
            (camera_x + view_width)
            / ACT_THREE_TILE_SIZE
        ),
    )
    last_row = min(
        len(dungeon_map),
        math.ceil(
            (camera_y + view_height)
            / ACT_THREE_TILE_SIZE
        ),
    )

    tile_assets = assets
    floor_tiles = assets.get(
        "tmx_tiles_by_floor",
        {},
    ).get(game_state.floor_index)

    if floor_tiles is not None:
        tile_assets = {
            **assets,
            "tmx_tiles": floor_tiles,
        }

    return WorldRenderContext(
        floor=floor,
        view_surface=view_surface,
        view_width=view_width,
        view_height=view_height,
        camera_x=camera_x,
        camera_y=camera_y,
        first_column=first_column,
        first_row=first_row,
        last_column=last_column,
        last_row=last_row,
        tile_assets=tile_assets,
        locomotion_pose=locomotion_pose,
        teleport_origin=teleport_origin,
        transition_started_at=transition_started_at,
    )
