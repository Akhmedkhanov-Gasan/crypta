import math

import pygame

from acts.act_three.presentation.paladin.attack_effects import (
    draw_paladin_attack_effects,
)
from acts.act_three.presentation.paladin.block import (
    draw_player_block_effect,
)
from acts.act_three.presentation.world.context import (
    create_world_render_context,
)
from acts.act_three.presentation.world.enemies import (
    draw_world_enemies,
)
from acts.act_three.presentation.world.player_state import (
    create_player_render_state,
)
from acts.act_three.presentation.world.player_sprite import (
    select_player_sprite,
)
from acts.act_three.presentation.world.player_position import (
    calculate_player_placement,
)
from acts.act_three.presentation.warlock import (
    WARLOCK_CURSE_CAST_DURATION_MS,
    draw_warlock_curse_cast,
    draw_warlock_demon_smoke,
    draw_warlock_demon_transformation,
)
from acts.act_three.presentation.world.targeting import (
    draw_world_attack_markers,
    draw_world_targeting,
)
from acts.act_three.presentation.world.terrain import (
    draw_world_terrain,
)
from acts.act_three.presentation.camera import (
    act_three_camera_scale,
)
from presentation.map_navigation import draw_map_trail
from acts.act_three.presentation.tile_layers import (
    draw_fading_foreground_layers,
    draw_tile_layers,
    layer_names_by_prefix,
)
from acts.act_three.presentation.atmosphere import (
    draw_lit_atmosphere,
)
from acts.act_three.presentation.color_grading import (
    draw_act_three_color_grading,
)
from acts.act_three.presentation.view import (
    _draw_fog_of_war,
    _view_position,
)

from presentation.layout import (
    ACT_THREE_TILE_SIZE,
    ACT_THREE_VIEW_HEIGHT,
    ACT_THREE_VIEW_WIDTH,
    ACT_THREE_VIEW_X,
    ACT_THREE_VIEW_Y,
)
from acts.act_three.settings import (
    ASSASSIN_SHADOW_STEP_DURATION_MS,
    ARCHER_EMPOWERED_SHOT_PROJECTILE_MS,
    ARCHER_LEAP_DURATION_MS,
    BERSERKER_RAGE_CRITICAL_HEALTH_RATIO,
    BERSERKER_RAGE_INJURED_HEALTH_RATIO,
    BERSERKER_CRUSHING_LEAP_IMPACT_MS,
    BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
    PALADIN_HOLY_HAND_EFFECT_MS,
    PALADIN_SHIELD_CHARGE_TRAVEL_MS,
    BERSERKER_LAST_RAGE_ANIMATION_MS,
)
from settings import HEALTH_BAR_COLOR


_TORCH_LIGHT_SURFACE = None
_IDLE_FRAME_SEQUENCE = (0, 1, 2, 1)
_IDLE_TIMELINE_CYCLE_COUNT = 4
_MOVE_FRAME_COUNT = 2
_MOVE_FRAME_DURATION_MS = 90
_ATTACK_FRAME_DURATION_MS = 240
_FAMILIAR_MOVE_DURATION_MS = 180
_TELEPORT_CAMERA_DURATION_MS = (
    ASSASSIN_SHADOW_STEP_DURATION_MS
)
_ARCHER_BARRAGE_SHOT_EFFECT_MS = 360
_TOP_VOID_CORNER_Y_OFFSET = 47
_TOP_VOID_CORNER_X_OFFSETS = {
    "wall_corner_top_left": -18,
    "wall_corner_top_right": 18,
}
_TOP_VOID_DOUBLE_CORNER_CROP_WIDTH = 24


from presentation.control_effects import draw_player_control_effects
from acts.act_three.presentation.animation import (
    _stable_text_seed,
)
from acts.act_three.presentation.berserker import (
    draw_crushing_leap_impact_effect,
    draw_crushing_leap_travel_effect,
    draw_last_rage_activation_effect,
)
from acts.act_three.presentation.mage import (
    draw_act_three_arcane_burst_effect,
)
from acts.act_three.presentation.class_effects import (
    _draw_summoner_bond_pentagram,
    _draw_summoner_familiar_attack_glow,
    _draw_summoner_idle_lights,
    _draw_warlock_idle_flashes,
)
from acts.act_three.presentation.combat_effects import (
    _draw_archer_projectile,
    _draw_archer_death_echoes,
    _draw_archer_death_impact,
    _draw_attack_impact_flash,
    _draw_assassin_death_echoes,
    _draw_assassin_death_impact,
    _draw_berserker_death_echoes,
    _draw_berserker_death_impact,
    _draw_paladin_death_echoes,
    _draw_paladin_death_impact,
    _draw_warlock_death_echoes,
    _draw_warlock_death_impact,
    _draw_summoner_death_echoes,
    _draw_summoner_death_impact,
    _draw_familiar_hit_feedback,
    _draw_player_hit_feedback,
    _draw_player_hit_vignette,
    _familiar_hit_feedback_active,
    _draw_warlock_orb,
)
from acts.act_three.presentation.lighting import (
    draw_act_three_lighting,
    draw_actor_shadow,
    draw_torch_flame,
)
from acts.act_three.presentation.primitives import (
    _draw_health_bar,
)
from acts.act_three.presentation.status_effects import (
    _draw_assassin_invisibility_effect,
    _draw_berserker_last_rage_effect,
    _draw_berserker_rage_effect,
    _draw_paladin_holy_hand_glow,
    _draw_paladin_holy_shield_aura,
    _draw_rogue_idle_particles,
    _draw_warlock_curse_aura,
    _draw_assassin_idle_smoke,
)
from acts.act_three.presentation.assassin import (
    draw_killing_spree_effects,
    draw_shadow_reflex_feedback,
    draw_killing_spree_final_impacts,
    draw_killing_spree_target_marks,
    killing_spree_player_sprite,
)


def _draw_act_three_world(
    screen,
    game_state,
    fonts,
    assets,
    current_time,
):
    context = create_world_render_context(
        game_state,
        assets,
        current_time,
    )

    floor = context.floor
    view_surface = context.view_surface
    view_width = context.view_width
    view_height = context.view_height
    camera_x = context.camera_x
    camera_y = context.camera_y
    first_column = context.first_column
    first_row = context.first_row
    last_column = context.last_column
    last_row = context.last_row
    tile_assets = context.tile_assets
    locomotion_pose = context.locomotion_pose
    teleport_origin = context.teleport_origin
    transition_started_at = context.transition_started_at

    draw_world_terrain(context)
    draw_world_targeting(
        context,
        game_state,
        assets,
        current_time,
    )
    berserker_impact_elapsed = (
        current_time
        - game_state.player.berserker_crushing_leap_started_at
    )
    if (
        game_state.player.berserker_crushing_leap_origin is not None
    ):
        draw_crushing_leap_impact_effect(
            view_surface,
            (
                floor.player_column,
                floor.player_row,
            ),
            camera_x,
            camera_y,
            (
                berserker_impact_elapsed
                - BERSERKER_CRUSHING_LEAP_TRAVEL_MS
            ),
            BERSERKER_CRUSHING_LEAP_IMPACT_MS,
            ACT_THREE_TILE_SIZE,
        )

    draw_world_attack_markers(
        context,
        game_state,
        current_time,
    )

    draw_world_enemies(
        context,
        game_state,
        fonts,
        assets,
        current_time,
    )

    player_state = create_player_render_state(
        game_state.player,
        teleport_origin,
        transition_started_at,
        current_time,
    )
    player_subclass = player_state.subclass
    attack_elapsed = player_state.attack_elapsed
    leap_origin = player_state.leap_origin
    leap_started_at = player_state.leap_started_at
    leap_elapsed = player_state.leap_elapsed
    leap_active = player_state.leap_active
    berserker_leap_origin = player_state.berserker_leap_origin
    berserker_leap_started_at = (
        player_state.berserker_leap_started_at
    )
    berserker_leap_elapsed = player_state.berserker_leap_elapsed
    berserker_leap_travel_active = (
        player_state.berserker_leap_travel_active
    )
    berserker_leap_impact_active = (
        player_state.berserker_leap_impact_active
    )
    last_rage_elapsed = player_state.last_rage_elapsed
    last_rage_activation_active = (
        player_state.last_rage_activation_active
    )
    shield_charge_origin = player_state.shield_charge_origin
    shield_charge_started_at = player_state.shield_charge_started_at
    shield_charge_elapsed = player_state.shield_charge_elapsed
    shield_charge_active = player_state.shield_charge_active
    shadow_step_active = player_state.shadow_step_active
    player_death_elapsed = player_state.death_elapsed
    player_sprite, walking_sprite_active = select_player_sprite(
        context,
        player_state,
        game_state.player,
        assets,
        current_time,
        _ATTACK_FRAME_DURATION_MS,
    )
    player_placement = calculate_player_placement(
        context,
        player_state,
        game_state.player,
        player_sprite,
        current_time,
    )
    player_sprite = player_placement.sprite
    player_position = player_placement.position
    leap_progress = player_placement.leap_progress
    leap_start_position = player_placement.leap_start_position
    leap_end_position = player_placement.leap_end_position
    shield_charge_progress = (
        player_placement.shield_charge_progress
    )
    shield_charge_start_position = (
        player_placement.shield_charge_start_position
    )
    if berserker_leap_travel_active:
        draw_crushing_leap_travel_effect(
            view_surface,
            player_sprite,
            _view_position(
                berserker_leap_origin[0],
                berserker_leap_origin[1],
                camera_x,
                camera_y,
            ),
            leap_end_position,
            berserker_leap_elapsed,
            BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
            ACT_THREE_TILE_SIZE,
        )
    if player_subclass in ("archer", "assassin"):
        player_sprite = player_sprite.copy()
        light_color = (
            (15, 16, 10)
            if player_subclass == "archer"
            else (10, 12, 18)
        )
        player_sprite.fill(
            light_color,
            special_flags=pygame.BLEND_RGB_ADD,
        )

    if game_state.player.invisibility_turns > 0:
        player_sprite = player_sprite.copy()
        player_sprite.set_alpha(105)
    else:
        player_sprite = player_sprite.copy()
        player_sprite.set_alpha(255)

    if (
        player_subclass == "assassin"
        and game_state.player.ultimate_animation_active
    ):
        killing_spree_sprite = (
            killing_spree_player_sprite(
                game_state.player,
                floor,
                assets,
                current_time,
            )
        )
        if killing_spree_sprite is not None:
            player_sprite = killing_spree_sprite

    player_sprite, player_position = draw_player_control_effects(
        view_surface,
        player_sprite,
        player_position,
        _view_position(
            floor.player_column,
            floor.player_row,
            camera_x,
            camera_y,
        ),
        game_state.player,
        current_time,
        ACT_THREE_TILE_SIZE,
    )

    if (
        player_death_elapsed is None
        and not berserker_leap_travel_active
    ):
        draw_actor_shadow(
            view_surface,
            player_sprite,
            player_position,
            ACT_THREE_TILE_SIZE,
            floor.torches,
            camera_x,
            camera_y,
            (
                "player",
                player_subclass,
                player_sprite.get_size(),
            ),
        )
    if (
        walking_sprite_active
        and not game_state.player.ultimate_animation_active
        and not shield_charge_active
        and not leap_active
        and not berserker_leap_travel_active
        and not berserker_leap_impact_active
        and not shadow_step_active
    ):
        player_position = (
            player_position[0] + locomotion_pose.body_offset[0],
            player_position[1] + locomotion_pose.body_offset[1],
        )
    _draw_player_hit_feedback(
        view_surface,
        player_sprite,
        player_position,
        game_state.player,
        floor.player_column,
        floor.player_row,
        current_time,
        fonts["sidebar_numbers"],
    )
    draw_act_three_arcane_burst_effect(
        view_surface,
        game_state,
        player_position,
        camera_x,
        camera_y,
        ACT_THREE_TILE_SIZE,
        current_time,
    )
    curse_target = (
        game_state.player.warlock_curse_effect_target
    )
    curse_started_at = (
        game_state.player.warlock_curse_started_at
    )
    curse_elapsed = current_time - curse_started_at

    if (
        player_subclass == "warlock"
        and curse_target is not None
        and curse_started_at > 0
        and 0
        <= curse_elapsed
        < WARLOCK_CURSE_CAST_DURATION_MS
    ):
        draw_warlock_curse_cast(
            view_surface,
            player_position,
            _view_position(
                curse_target[0],
                curse_target[1],
                camera_x,
                camera_y,
            ),
            current_time,
            curse_started_at,
        )
    elif (
        curse_target is not None
        and curse_started_at > 0
        and curse_elapsed
        >= WARLOCK_CURSE_CAST_DURATION_MS
    ):
        game_state.player.warlock_curse_effect_target = None
        game_state.player.warlock_curse_started_at = 0
    if last_rage_activation_active:
        draw_last_rage_activation_effect(
            view_surface,
            player_position,
            last_rage_elapsed,
            BERSERKER_LAST_RAGE_ANIMATION_MS,
            ACT_THREE_TILE_SIZE,
        )

    if (
        player_subclass == "assassin"
        and game_state.player.invisibility_turns > 0
    ):
        _draw_assassin_invisibility_effect(
            view_surface,
            player_position[0],
            player_position[1],
            current_time,
            floor.visual_seed
            ^ _stable_text_seed("assassin:invisibility"),
        )

    if (
        player_subclass == "berserker"
        and game_state.player.health > 0
    ):
        last_rage_is_active = (
            game_state.player.berserker_last_rage_turns > 0
        )
        if (
            last_rage_is_active
            and not last_rage_activation_active
        ):
            _draw_berserker_last_rage_effect(
                view_surface,
                player_position[0],
                player_position[1],
                current_time,
            )
        berserker_health_ratio = (
            game_state.player.health
            / game_state.player.max_health
        )
        if last_rage_is_active:
            berserker_rage_stage = 0
        elif (
            berserker_health_ratio
            <= BERSERKER_RAGE_CRITICAL_HEALTH_RATIO
        ):
            berserker_rage_stage = 2
        elif (
            berserker_health_ratio
            <= BERSERKER_RAGE_INJURED_HEALTH_RATIO
        ):
            berserker_rage_stage = 1
        else:
            berserker_rage_stage = 0
        _draw_berserker_rage_effect(
            view_surface,
            player_position[0],
            player_position[1],
            current_time,
            berserker_rage_stage,
        )

    holy_hand_elapsed = (
        current_time
        - game_state.player.paladin_holy_hand_started_at
    )
    if (
        player_subclass == "paladin"
        and game_state.player.paladin_holy_hand_started_at > 0
        and 0
        <= holy_hand_elapsed
        < PALADIN_HOLY_HAND_EFFECT_MS
    ):
        _draw_paladin_holy_hand_glow(
            view_surface,
            player_sprite,
            player_position[0],
            player_position[1],
            holy_hand_elapsed,
        )

    if (
        player_subclass == "paladin"
        and game_state.player.paladin_holy_shield_turns > 0
    ):
        _draw_paladin_holy_shield_aura(
            view_surface,
            player_sprite,
            player_position[0],
            player_position[1],
            current_time,
        )

    if leap_active and leap_start_position is not None:
        for lag, alpha in (
            (0.12, 105),
            (0.24, 65),
            (0.36, 30),
        ):
            ghost_progress = max(0, leap_progress - lag)
            ghost_eased_progress = 1 - (1 - ghost_progress) ** 3
            ghost_position = (
                round(
                    leap_start_position[0]
                    + (
                        leap_end_position[0]
                        - leap_start_position[0]
                    )
                    * ghost_eased_progress
                ),
                round(
                    leap_start_position[1]
                    + (
                        leap_end_position[1]
                        - leap_start_position[1]
                    )
                    * ghost_eased_progress
                    - math.sin(math.pi * ghost_progress) * 8
                ),
            )
            ghost_sprite = player_sprite.copy()
            ghost_sprite.fill(
                (15, 55, 35),
                special_flags=pygame.BLEND_RGB_ADD,
            )
            ghost_sprite.set_alpha(alpha)
            view_surface.blit(ghost_sprite, ghost_position)

    if (
        berserker_leap_travel_active
        and leap_start_position is not None
    ):
        for lag, alpha in (
            (0.10, 125),
            (0.21, 78),
            (0.32, 38),
        ):
            ghost_progress = max(0, leap_progress - lag)
            ghost_eased_progress = (
                1 - (1 - ghost_progress) ** 3
            )
            ghost_position = (
                round(
                    leap_start_position[0]
                    + (
                        leap_end_position[0]
                        - leap_start_position[0]
                    )
                    * ghost_eased_progress
                ),
                round(
                    leap_start_position[1]
                    + (
                        leap_end_position[1]
                        - leap_start_position[1]
                    )
                    * ghost_eased_progress
                    - math.sin(math.pi * ghost_progress) * 13
                ),
            )
            ghost_sprite = player_sprite.copy()
            ghost_sprite.fill(
                (62, 10, 8),
                special_flags=pygame.BLEND_RGB_ADD,
            )
            ghost_sprite.set_alpha(alpha)
            view_surface.blit(ghost_sprite, ghost_position)

    if (
        shield_charge_active
        and shield_charge_start_position is not None
    ):
        for lag, alpha in (
            (0.09, 125),
            (0.18, 78),
            (0.28, 38),
        ):
            ghost_progress = max(
                0,
                shield_charge_progress - lag,
            )
            ghost_eased_progress = (
                ghost_progress
                * ghost_progress
                * (3 - 2 * ghost_progress)
            )
            ghost_position = (
                round(
                    shield_charge_start_position[0]
                    + (
                        leap_end_position[0]
                        - shield_charge_start_position[0]
                    )
                    * ghost_eased_progress
                ),
                round(
                    shield_charge_start_position[1]
                    + (
                        leap_end_position[1]
                        - shield_charge_start_position[1]
                    )
                    * ghost_eased_progress
                ),
            )
            ghost_sprite = player_sprite.copy()
            ghost_sprite.fill(
                (72, 49, 8),
                special_flags=pygame.BLEND_RGB_ADD,
            )
            ghost_sprite.set_alpha(alpha)
            view_surface.blit(
                ghost_sprite,
                ghost_position,
            )

    if (
        player_subclass == "berserker"
        and player_death_elapsed is not None
    ):
        _draw_berserker_death_echoes(
            view_surface,
            assets,
            player_position,
            game_state.player,
            current_time,
        )
    elif (
        player_subclass == "paladin"
        and player_death_elapsed is not None
    ):
        _draw_paladin_death_echoes(
            view_surface,
            assets,
            player_position,
            game_state.player,
            current_time,
        )
    elif (
        player_subclass == "assassin"
        and player_death_elapsed is not None
    ):
        _draw_assassin_death_echoes(
            view_surface,
            assets,
            player_position,
            game_state.player,
            current_time,
        )
    elif (
        player_subclass == "archer"
        and player_death_elapsed is not None
    ):
        _draw_archer_death_echoes(
            view_surface,
            assets,
            player_position,
            game_state.player,
            current_time,
        )
    elif (
        player_subclass == "warlock"
        and player_death_elapsed is not None
    ):
        _draw_warlock_death_echoes(
            view_surface,
            assets,
            player_position,
            game_state.player,
            current_time,
        )
    elif (
        player_subclass == "summoner"
        and player_death_elapsed is not None
    ):
        _draw_summoner_death_echoes(
            view_surface,
            assets,
            player_position,
            game_state.player,
            current_time,
        )

    draw_player_block_effect(
        view_surface,
        game_state.player,
        (
            player_position[0] + ACT_THREE_TILE_SIZE // 2,
            player_position[1] + ACT_THREE_TILE_SIZE // 2,
        ),
        current_time,
        ACT_THREE_TILE_SIZE,
        fonts["sidebar_numbers"],
    )

    if (
        player_subclass == "berserker"
        and player_death_elapsed is not None
    ):
        _draw_berserker_death_impact(
            view_surface,
            player_position,
            game_state.player,
            current_time,
        )
    elif (
        player_subclass == "paladin"
        and player_death_elapsed is not None
    ):
        _draw_paladin_death_impact(
            view_surface,
            player_position,
            game_state.player,
            current_time,
        )
    elif (
        player_subclass == "assassin"
        and player_death_elapsed is not None
    ):
        _draw_assassin_death_impact(
            view_surface,
            player_position,
            game_state.player,
            current_time,
        )
    elif (
        player_subclass == "archer"
        and player_death_elapsed is not None
    ):
        _draw_archer_death_impact(
            view_surface,
            player_position,
            game_state.player,
            current_time,
        )
    elif (
        player_subclass == "warlock"
        and player_death_elapsed is not None
    ):
        _draw_warlock_death_impact(
            view_surface,
            player_position,
            game_state.player,
            current_time,
        )
    elif (
        player_subclass == "summoner"
        and player_death_elapsed is not None
    ):
        _draw_summoner_death_impact(
            view_surface,
            player_position,
            game_state.player,
            current_time,
        )

    familiar_position = game_state.player.summoner_familiar_position
    if (
        player_subclass == "summoner"
        and game_state.player.summoner_familiar_active
        and familiar_position is not None
    ):
        familiar_attack_elapsed = (
            current_time
            - game_state.player.summoner_familiar_attack_started_at
        )
        if (
            game_state.player.summoner_true_form_active
            and 0 <= familiar_attack_elapsed < _ATTACK_FRAME_DURATION_MS
        ):
            familiar_sprite = assets[
                "summoner_true_form_attack"
            ]
        elif game_state.player.summoner_true_form_active:
            familiar_frame = (current_time // 180) % 3
            familiar_sprite = assets[
                f"summoner_true_form_idle_{familiar_frame}"
            ]
        elif 0 <= familiar_attack_elapsed < _ATTACK_FRAME_DURATION_MS:
            familiar_sprite = assets[
                "summoner_familiar_attack"
            ]
        else:
            familiar_frame = (current_time // 180) % 3
            familiar_asset_frame = (0, 1, 2)[familiar_frame]
            familiar_sprite = assets[
                f"summoner_familiar_idle_{familiar_asset_frame}"
            ]
        familiar_render_position = _view_position(
            familiar_position[0],
            familiar_position[1],
            camera_x,
            camera_y,
        )
        familiar_origin = (
            game_state.player.summoner_familiar_movement_origin
        )
        familiar_move_elapsed = (
            current_time
            - game_state.player.summoner_familiar_movement_started_at
        )
        if (
            familiar_origin is not None
            and 0 <= familiar_move_elapsed < _FAMILIAR_MOVE_DURATION_MS
        ):
            move_progress = familiar_move_elapsed / _FAMILIAR_MOVE_DURATION_MS
            move_progress = (
                move_progress
                * move_progress
                * (3 - 2 * move_progress)
            )
            origin_position = _view_position(
                familiar_origin[0],
                familiar_origin[1],
                camera_x,
                camera_y,
            )
            familiar_render_position = (
                round(
                    origin_position[0]
                    + (
                        familiar_render_position[0]
                        - origin_position[0]
                    )
                    * move_progress
                ),
                round(
                    origin_position[1]
                    + (
                        familiar_render_position[1]
                        - origin_position[1]
                    )
                    * move_progress
                ),
            )
        _draw_familiar_hit_feedback(
            view_surface,
            familiar_sprite,
            familiar_render_position,
            game_state.player,
            familiar_position[0],
            familiar_position[1],
            current_time,
            fonts["sidebar_numbers"],
        )
        if 0 <= familiar_attack_elapsed < _ATTACK_FRAME_DURATION_MS:
            _draw_summoner_familiar_attack_glow(
                view_surface,
                familiar_render_position[0],
                familiar_render_position[1],
                current_time,
            )
        if game_state.player.summoner_familiar_max_health > 0:
            _draw_health_bar(
                view_surface,
                familiar_render_position[0],
                familiar_render_position[1],
                game_state.player.summoner_familiar_health,
                game_state.player.summoner_familiar_max_health,
                HEALTH_BAR_COLOR,
            )

        if game_state.player.summoner_bond_active:
            _draw_summoner_bond_pentagram(
                view_surface,
                player_position[0],
                player_position[1],
                current_time,
            )
            _draw_summoner_bond_pentagram(
                view_surface,
                familiar_render_position[0],
                familiar_render_position[1],
                current_time + 180,
            )
    elif (
        player_subclass == "summoner"
        and _familiar_hit_feedback_active(
            game_state.player,
            current_time,
        )
        and game_state.player.summoner_familiar_hit_position is not None
    ):
        defeated_familiar_position = (
            game_state.player.summoner_familiar_hit_position
        )
        familiar_render_position = _view_position(
            defeated_familiar_position[0],
            defeated_familiar_position[1],
            camera_x,
            camera_y,
        )
        _draw_familiar_hit_feedback(
            view_surface,
            None,
            familiar_render_position,
            game_state.player,
            defeated_familiar_position[0],
            defeated_familiar_position[1],
            current_time,
            fonts["sidebar_numbers"],
        )

    active_barrage_shots = []
    for barrage_shot in game_state.player.archer_barrage_shots:
        if barrage_shot.started_at <= 0:
            active_barrage_shots.append(barrage_shot)
            continue

        barrage_elapsed = (
            current_time - barrage_shot.started_at
        )
        if not (
            0
            <= barrage_elapsed
            < _ARCHER_BARRAGE_SHOT_EFFECT_MS
        ):
            continue

        active_barrage_shots.append(barrage_shot)
        barrage_progress = min(
            1,
            barrage_elapsed
            / ARCHER_EMPOWERED_SHOT_PROJECTILE_MS,
        )
        ghost_visibility = math.sin(
            math.pi
            * min(
                1,
                barrage_elapsed
                / _ARCHER_BARRAGE_SHOT_EFFECT_MS,
            )
        )
        ghost_sprite = assets["player_archer_attack"].copy()
        ghost_sprite.fill(
            (18, 75, 42),
            special_flags=pygame.BLEND_RGB_ADD,
        )
        ghost_sprite.set_alpha(
            round(145 * ghost_visibility)
        )
        ghost_position = _view_position(
            barrage_shot.origin[0],
            barrage_shot.origin[1],
            camera_x,
            camera_y,
        )
        view_surface.blit(ghost_sprite, ghost_position)

        if (
            barrage_elapsed
            < ARCHER_EMPOWERED_SHOT_PROJECTILE_MS
        ):
            target_position = _view_position(
                barrage_shot.target[0],
                barrage_shot.target[1],
                camera_x,
                camera_y,
            )
            _draw_archer_projectile(
                view_surface,
                assets["archer_empowered_shot_arrow"],
                (
                    ghost_position[0]
                    + ACT_THREE_TILE_SIZE // 2,
                    ghost_position[1]
                    + ACT_THREE_TILE_SIZE // 2,
                ),
                (
                    target_position[0]
                    + ACT_THREE_TILE_SIZE // 2,
                    target_position[1]
                    + ACT_THREE_TILE_SIZE // 2,
                ),
                barrage_progress,
                empowered=True,
                current_time=current_time,
            )

    game_state.player.archer_barrage_shots = (
        active_barrage_shots
    )

    if (
        player_subclass == "archer"
        and leap_origin is not None
        and leap_started_at > 0
        and leap_elapsed >= ARCHER_LEAP_DURATION_MS
    ):
        game_state.player.archer_leap_origin = None
        game_state.player.archer_leap_started_at = 0
    if (
        player_subclass == "berserker"
        and berserker_leap_origin is not None
        and berserker_leap_started_at > 0
        and berserker_leap_elapsed
        >= (
            BERSERKER_CRUSHING_LEAP_TRAVEL_MS
            + BERSERKER_CRUSHING_LEAP_IMPACT_MS
        )
    ):
        game_state.player.berserker_crushing_leap_origin = None
        game_state.player.berserker_crushing_leap_started_at = 0
        game_state.player.berserker_crushing_leap_preview_cells.clear()
    if (
        player_subclass == "paladin"
        and shield_charge_origin is not None
        and shield_charge_started_at > 0
        and shield_charge_elapsed
        >= PALADIN_SHIELD_CHARGE_TRAVEL_MS
    ):
        game_state.player.paladin_shield_charge_origin = None
        game_state.player.paladin_shield_charge_started_at = 0

    empowered_target = game_state.player.archer_empowered_shot_target
    empowered_started_at = game_state.player.archer_empowered_shot_started_at
    empowered_elapsed = current_time - empowered_started_at
    ordinary_target = (
        game_state.player_attack_targets[0]
        if game_state.player_attack_targets
        else None
    )
    ordinary_elapsed = current_time - game_state.player.attack_animation_started_at
    if (
        player_subclass == "archer"
        and empowered_target is not None
        and empowered_started_at
        and 0 <= empowered_elapsed < ARCHER_EMPOWERED_SHOT_PROJECTILE_MS
    ):
        target_position = _view_position(
            empowered_target[0],
            empowered_target[1],
            camera_x,
            camera_y,
        )
        origin = (
            player_position[0] + ACT_THREE_TILE_SIZE // 2,
            player_position[1] + ACT_THREE_TILE_SIZE // 2,
        )
        destination = (
            target_position[0] + ACT_THREE_TILE_SIZE // 2,
            target_position[1] + ACT_THREE_TILE_SIZE // 2,
        )
        progress = min(1, empowered_elapsed / ARCHER_EMPOWERED_SHOT_PROJECTILE_MS)
        _draw_archer_projectile(
            view_surface,
            assets["archer_empowered_shot_arrow"],
            origin,
            destination,
            progress,
            empowered=True,
            current_time=current_time,
        )
    elif (
        player_subclass == "archer"
        and empowered_target is not None
        and empowered_started_at
        and empowered_elapsed >= ARCHER_EMPOWERED_SHOT_PROJECTILE_MS
    ):
        game_state.player.archer_empowered_shot_target = None
        game_state.player.archer_empowered_shot_started_at = 0

    if (
        player_subclass == "archer"
        and empowered_target is None
        and ordinary_target is not None
        and 0 <= ordinary_elapsed < _ATTACK_FRAME_DURATION_MS
    ):
        target_position = _view_position(
            ordinary_target[0],
            ordinary_target[1],
            camera_x,
            camera_y,
        )
        origin = (
            player_position[0] + ACT_THREE_TILE_SIZE // 2,
            player_position[1] + ACT_THREE_TILE_SIZE // 2,
        )
        destination = (
            target_position[0] + ACT_THREE_TILE_SIZE // 2,
            target_position[1] + ACT_THREE_TILE_SIZE // 2,
        )
        _draw_archer_projectile(
            view_surface,
            assets["archer_empowered_shot_arrow"],
            origin,
            destination,
            min(1, ordinary_elapsed / _ATTACK_FRAME_DURATION_MS),
        )
    elif (
        player_subclass == "warlock"
        and ordinary_target is not None
        and 0 <= ordinary_elapsed < _ATTACK_FRAME_DURATION_MS
    ):
        target_position = _view_position(
            ordinary_target[0],
            ordinary_target[1],
            camera_x,
            camera_y,
        )
        _draw_warlock_orb(
            view_surface,
            (
                player_position[0] + ACT_THREE_TILE_SIZE // 2,
                player_position[1] + ACT_THREE_TILE_SIZE // 2,
            ),
            (
                target_position[0] + ACT_THREE_TILE_SIZE // 2,
                target_position[1] + ACT_THREE_TILE_SIZE // 2,
            ),
            min(
                1,
                ordinary_elapsed / _ATTACK_FRAME_DURATION_MS,
            ),
            current_time,
        )

    if (
        teleport_origin is not None
        and transition_started_at
        and current_time - transition_started_at
        >= _TELEPORT_CAMERA_DURATION_MS
    ):
        game_state.player.teleport_camera_origin = None
        game_state.player.teleport_transition_started_at = 0

    draw_paladin_attack_effects(
        view_surface,
        game_state.player,
        player_position,
        game_state.player_attack_targets,
        camera_x,
        camera_y,
        current_time,
    )

    if (
        player_subclass in ("assassin", "archer", "warlock")
        and 0 <= attack_elapsed < _ATTACK_FRAME_DURATION_MS
    ):
        flash_color = {
            "archer": (80, 230, 120),
            "warlock": (195, 70, 245),
            "assassin": (155, 215, 255),
        }[player_subclass]
        for column, row in game_state.player_attack_targets:
            _draw_attack_impact_flash(
                view_surface,
                _view_position(
                    column,
                    row,
                    camera_x,
                    camera_y,
                ),
                current_time,
                game_state.player.attack_animation_started_at,
                flash_color,
            )

    if player_subclass == "assassin":
        draw_killing_spree_target_marks(
            view_surface,
            game_state.player,
            floor,
            camera_x,
            camera_y,
        )
    if player_subclass == "assassin":
        draw_killing_spree_effects(
            view_surface,
            game_state.player,
            floor,
            assets,
            current_time,
            camera_x,
            camera_y,
        )
        draw_killing_spree_final_impacts(
            view_surface,
            game_state.player,
            current_time,
            camera_x,
            camera_y,
        )
    if (
        player_subclass == "assassin"
        and player_death_elapsed is None
        and not game_state.player.ultimate_animation_active
    ):
        _draw_assassin_idle_smoke(
            view_surface,
            player_position[0],
            player_position[1],
            current_time,
            (
                floor.visual_seed
                ^ _stable_text_seed("player:assassin:smoke")
            ),
        )
    elif player_subclass == "archer":
        _draw_rogue_idle_particles(
            view_surface,
            player_position[0],
            player_position[1],
            current_time,
            (
                floor.visual_seed
                ^ _stable_text_seed("player:archer:motes")
            ),
            player_subclass,
        )
    elif player_subclass == "warlock" and player_death_elapsed is None:
        draw_warlock_demon_transformation(
            view_surface,
            game_state.player,
            player_position,
            current_time,
        )
        if game_state.player.warlock_demon_form_active:
            draw_warlock_demon_smoke(
                view_surface,
                player_position,
                current_time,
            )
        else:
            _draw_warlock_idle_flashes(
                view_surface,
                player_position[0],
                player_position[1],
                current_time,
                (
                        floor.visual_seed
                        ^ _stable_text_seed(
                    "player:warlock:flashes"
                )
                ),
            )
    elif player_subclass == "summoner" and player_death_elapsed is None:
        _draw_summoner_idle_lights(
            view_surface,
            player_position[0],
            player_position[1],
            current_time,
            (
                floor.visual_seed
                ^ _stable_text_seed(
                    "player:summoner:lights"
                )
            ),
        )

    if floor.tile_layers and tile_assets.get("tmx_tiles"):
        draw_fading_foreground_layers(
            view_surface,
            floor,
            tile_assets,
            layer_names_by_prefix(
                floor,
                "WallsFront",
                "DecorFront",
                "Gate",
            ),
            first_column,
            first_row,
            last_column,
            last_row,
            camera_x,
            camera_y,
            player_sprite,
            player_position,
        )
    for column, row in floor.torches:
        view_surface.blit(
            assets["torch_base"],
            _view_position(
                column,
                row,
                camera_x,
                camera_y,
            ),
        )
    draw_act_three_lighting(
        view_surface,
        floor.torches,
        floor.barriers,
        camera_x,
        camera_y,
        current_time,
        ACT_THREE_TILE_SIZE,
    )
    draw_lit_atmosphere(
        view_surface,
        floor.torches,
        camera_x,
        camera_y,
        current_time,
        ACT_THREE_TILE_SIZE,
    )
    for torch_index, (column, row) in enumerate(floor.torches):
        draw_torch_flame(
            view_surface,
            assets,
            _view_position(
                column,
                row,
                camera_x,
                camera_y,
            ),
            current_time,
            torch_index,
        )
    _draw_fog_of_war(
        view_surface,
        floor,
        camera_x,
        camera_y,
        player_position,
    )
    draw_act_three_color_grading(
        view_surface,
        floor.torches,
        camera_x,
        camera_y,
        ACT_THREE_TILE_SIZE,
    )

    if player_subclass == "assassin":
        draw_shadow_reflex_feedback(
            view_surface,
            game_state.player,
            current_time,
            camera_x,
            camera_y,
            fonts["sidebar_numbers"],
        )

    _draw_player_hit_vignette(
        view_surface,
        game_state.player,
        current_time,
    )

    viewport = pygame.Rect(
        ACT_THREE_VIEW_X,
        ACT_THREE_VIEW_Y,
        ACT_THREE_VIEW_WIDTH,
        ACT_THREE_VIEW_HEIGHT,
    )

    if view_surface.get_size() != viewport.size:
        view_surface = pygame.transform.scale(
            view_surface,
            viewport.size,
        )

    screen.blit(view_surface, viewport)

    draw_map_trail(
        screen,
        floor,
        (camera_x, camera_y),
        ACT_THREE_TILE_SIZE,
        act_three_camera_scale(floor),
        viewport,
    )
