import math

import pygame

from acts.act_three.presentation.camera import (
    act_three_camera_scale,
    act_three_world_view_size,
    update_act_three_camera,
)
from presentation.map_navigation import draw_map_trail
from presentation.ground_items import draw_ground_items
from acts.act_three.presentation.tile_layers import (
    draw_fading_foreground_layers,
    draw_tile_layer_shadows,
    draw_tile_layers,
    layer_names_by_prefix,
)
from acts.act_three.presentation.environment_grading import (
    draw_environment_grading,
)
from acts.act_three.presentation.atmosphere import (
    draw_lit_atmosphere,
)
from acts.act_three.presentation.color_grading import (
    draw_act_three_color_grading,
)
from acts.act_three.presentation.view import (
    _camera_position,
    _draw_fog_of_war,
    _get_act_three_visibility,
    _view_position,
)

from game.state import EnemyBehaviorState
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
    WARLOCK_SOUL_EXCHANGE_TRAVEL_MS,
)
from settings import (
    DANGER_BORDER_COLOR,
    HEALTH_BAR_COLOR,
)


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


from acts.act_three.presentation.actors import _enemy_sprite
from acts.act_two.presentation.enemies.sentinel import draw_sentinel_status
from presentation.control_effects import draw_player_control_effects
from acts.act_three.presentation.animation import (
    _idle_frame,
    _stable_text_seed,
)
from acts.act_three.presentation.player_motion import (
    ASSASSIN_SHADOW_STEP_FRAME_COUNT,
    ASSASSIN_WALK_FRAME_COUNT,
    BERSERKER_WALK_FRAME_COUNT,
    assassin_attack_direction,
    assassin_attack_frame,
    assassin_shadow_step_direction,
    assassin_shadow_step_frame,
    assassin_idle_frame,
    berserker_idle_frame,
    berserker_walk_frame,
    assassin_walk_direction,
    assassin_walk_frame,
    assassin_hurt_frame,
    assassin_hurt_direction,
    interpolate_player_position,
    movement_frame_for_progress,
    player_movement_progress,

)
from acts.act_three.presentation.class_effects import (
    _draw_summoner_bond_pentagram,
    _draw_summoner_familiar_attack_glow,
    _draw_summoner_idle_lights,
    _draw_warlock_demon_aura,
    _draw_warlock_demon_overlay,
    _draw_warlock_idle_flashes,
)
from acts.act_three.presentation.combat_effects import (
    _draw_archer_projectile,
    _draw_archer_death_echoes,
    _draw_archer_death_impact,
    _draw_attack_impact_flash,
    _draw_assassin_death_echoes,
    _draw_assassin_death_impact,
    _PLAYER_HIT_SPRITE_DURATION_MS,
    _assassin_death_frame,
    _draw_berserker_death_echoes,
    _draw_berserker_death_impact,
    _draw_paladin_death_echoes,
    _draw_paladin_death_impact,
    _draw_warlock_death_echoes,
    _draw_warlock_death_impact,
    _draw_summoner_death_echoes,
    _draw_summoner_death_impact,
    _draw_enemy_hit_feedback,
    _draw_familiar_hit_feedback,
    _draw_player_hit_feedback,
    _draw_player_hit_vignette,
    _enemy_hit_feedback_active,
    _familiar_hit_feedback_active,
    _player_death_elapsed,
    _player_death_frame,
    _player_death_camera_offset,
    _player_death_sprite_offset,
    _player_hit_camera_offset,
    _player_hurt_sprite_active,
    _draw_warlock_orb,
)
from acts.act_three.presentation.lighting import (
    draw_act_three_lighting,
    draw_actor_shadow,
    draw_torch_flame,
)
from acts.act_three.presentation.primitives import (
    _draw_archer_barrage_zone_cells,
    _draw_health_bar,
    _draw_tile_markers,
)
from acts.act_three.presentation.status_effects import (
    _draw_assassin_invisibility_effect,
    _draw_berserker_last_rage_effect,
    _draw_berserker_rage_effect,
    _draw_healing_aura,
    _draw_paladin_holy_hand_glow,
    _draw_paladin_holy_shield_aura,
    _draw_rogue_idle_particles,
    _draw_warlock_curse_aura,
    _draw_assassin_idle_smoke,
)
from acts.act_three.presentation.targeting import (
    draw_shadow_step_targeting,
)
from acts.act_three.presentation.assassin import (
    draw_killing_spree_effects,
    draw_shadow_reflex_feedback,
    draw_killing_spree_final_impacts,
    draw_killing_spree_target_marks,
    killing_spree_camera_position,
    killing_spree_player_sprite,
)


def _draw_act_three_world(
    screen,
    game_state,
    fonts,
    assets,
    current_time,
):
    floor = game_state.floor
    dungeon_map = floor.map
    view_width, view_height = act_three_world_view_size(floor)
    movement_progress = player_movement_progress(
        current_time,
        game_state.player.movement_animation_started_at,
    )
    camera_player_position = (
        floor.player_column * ACT_THREE_TILE_SIZE,
        floor.player_row * ACT_THREE_TILE_SIZE,
    )
    movement_origin = game_state.player.movement_origin

    if movement_progress is not None and movement_origin is not None:
        camera_player_position = interpolate_player_position(
            (
                movement_origin[0] * ACT_THREE_TILE_SIZE,
                movement_origin[1] * ACT_THREE_TILE_SIZE,
            ),
            camera_player_position,
            movement_progress,
        )

    killing_spree_camera = (
        killing_spree_camera_position(
            game_state.player,
            floor,
            current_time,
        )
    )
    if killing_spree_camera is not None:
        camera_player_position = killing_spree_camera

    update_act_three_camera(
        floor,
        current_time,
        player_position=camera_player_position,
        cinematic=(
            killing_spree_camera is not None
        ),
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
        if transition_elapsed < _TELEPORT_CAMERA_DURATION_MS:
            transition_progress = transition_elapsed / _TELEPORT_CAMERA_DURATION_MS
            transition_progress = (
                transition_progress
                * transition_progress
                * (3 - 2 * transition_progress)
            )
            start_camera = _camera_position(floor, teleport_origin)
            camera_x = round(
                start_camera[0]
                + (camera_x - start_camera[0]) * transition_progress
            )
            camera_y = round(
                start_camera[1]
                + (camera_y - start_camera[1]) * transition_progress
            )
    hit_camera_x, hit_camera_y = _player_hit_camera_offset(
        game_state.player,
        current_time,
    )
    death_camera_x, death_camera_y = _player_death_camera_offset(
        game_state.player,
        current_time,
    )
    camera_x += hit_camera_x + death_camera_x
    camera_y += hit_camera_y + death_camera_y
    exchange_player_origin = (
        game_state.player.warlock_soul_exchange_player_origin
    )
    exchange_enemy_origin = (
        game_state.player.warlock_soul_exchange_enemy_origin
    )
    exchange_enemy_name = (
        game_state.player.warlock_soul_exchange_enemy_name
    )
    exchange_started_at = (
        game_state.player.warlock_soul_exchange_started_at
    )
    exchange_elapsed = current_time - exchange_started_at
    exchange_active = (
        game_state.player.subclass == "warlock"
        and exchange_player_origin is not None
        and exchange_enemy_origin is not None
        and exchange_enemy_name is not None
        and exchange_started_at > 0
        and 0
        <= exchange_elapsed
        < WARLOCK_SOUL_EXCHANGE_TRAVEL_MS
    )
    exchange_progress = min(
        1,
        max(
            0,
            exchange_elapsed
            / WARLOCK_SOUL_EXCHANGE_TRAVEL_MS,
        ),
    )
    exchange_eased_progress = (
        exchange_progress
        * exchange_progress
        * (3 - 2 * exchange_progress)
    )
    first_column = max(0, camera_x // ACT_THREE_TILE_SIZE)
    first_row = max(0, camera_y // ACT_THREE_TILE_SIZE)
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
    if floor.tile_layers and tile_assets.get("tmx_tiles"):
        draw_tile_layers(
            view_surface,
            floor,
            tile_assets,
            layer_names_by_prefix(
                floor,
                "Ground",
                "GroundDetails",
                "WallsBack",
                "DecorBack",
            ),
            first_column,
            first_row,
            last_column,
            last_row,
            camera_x,
            camera_y,
        )
        draw_environment_grading(
            view_surface,
            floor,
            camera_x,
            camera_y,
            first_column,
            first_row,
            last_column,
            last_row,
        )
        draw_tile_layer_shadows(
            view_surface,
            floor,
            tile_assets,
            layer_names_by_prefix(
                floor,
                "DecorMiddle",
                "Objects",
                "Gate",
            ),
            first_column,
            first_row,
            last_column,
            last_row,
            camera_x,
            camera_y,
        )

        draw_tile_layers(
            view_surface,
            floor,
            tile_assets,
            layer_names_by_prefix(
                floor,
                "DecorMiddle",
                "Objects",
            ),
            first_column,
            first_row,
            last_column,
            last_row,
            camera_x,
            camera_y,
        )

    _draw_archer_barrage_zone_cells(
        view_surface,
        assets["archer_barrage_zone_cell"],
        game_state.player.archer_barrage_zone_cells,
        camera_x,
        camera_y,
        current_time,
    )
    if game_state.player.archer_barrage_zone_aiming:
        _draw_archer_barrage_zone_cells(
            view_surface,
            assets["archer_barrage_zone_cell"],
            game_state.player.archer_barrage_zone_preview_cells,
            camera_x,
            camera_y,
            current_time,
            preview=True,
        )
    if game_state.player.berserker_crushing_leap_aiming:
        _draw_archer_barrage_zone_cells(
            view_surface,
            assets["berserker_crushing_leap_area"],
            game_state.player.berserker_crushing_leap_preview_cells,
            camera_x,
            camera_y,
            current_time,
            preview=True,
        )
    if game_state.player.paladin_shield_charge_aiming:
        _draw_tile_markers(
            view_surface,
            game_state.player.paladin_shield_charge_preview_cells,
            camera_x,
            camera_y,
            (241, 192, 70),
        )
    if (
        game_state.player.teleport_aiming
        and game_state.player.teleport_preview_target is not None
    ):
        teleport_preview_target = (
            game_state.player.teleport_preview_target
        )
        draw_shadow_step_targeting(
            view_surface,
            _view_position(
                floor.player_column,
                floor.player_row,
                camera_x,
                camera_y,
            ),
            _view_position(
                teleport_preview_target[0],
                teleport_preview_target[1],
                camera_x,
                camera_y,
            ),
            current_time,
            ACT_THREE_TILE_SIZE,
        )
    berserker_impact_elapsed = (
        current_time
        - game_state.player.berserker_crushing_leap_started_at
    )
    if (
        game_state.player.berserker_crushing_leap_origin is not None
        and (
            BERSERKER_CRUSHING_LEAP_TRAVEL_MS
            <= berserker_impact_elapsed
            < (
                BERSERKER_CRUSHING_LEAP_TRAVEL_MS
                + BERSERKER_CRUSHING_LEAP_IMPACT_MS
            )
        )
    ):
        _draw_archer_barrage_zone_cells(
            view_surface,
            assets["berserker_crushing_leap_area"],
            game_state.player.berserker_crushing_leap_preview_cells,
            camera_x,
            camera_y,
            current_time,
        )

    attack_positions = [
        position
        for enemy in floor.enemies
        if (
            enemy.health > 0
            and not (
                enemy.type == "sentinel"
                and enemy.prepared_attack_mode == "shield_bash"
            )
        )
        for position in enemy.attack_targets
    ]
    _draw_tile_markers(
        view_surface,
        attack_positions,
        camera_x,
        camera_y,
        (190, 48, 45),
    )
    _draw_tile_markers(
        view_surface,
        game_state.player_attack_targets,
        camera_x,
        camera_y,
        (210, 152, 42),
    )

    living_enemies = [
        enemy
        for enemy in floor.enemies
        if (
            enemy.health > 0
            and (enemy.column, enemy.row) in floor.visible_cells
        )
    ]
    rendered_enemies = [
        enemy
        for enemy in floor.enemies
        if (
            (enemy.column, enemy.row) in floor.visible_cells
            and (
                enemy.health > 0
                or (
                    enemy.type
                    in ("archer", "brute", "priest", "sentinel")
                    and enemy.behavior_state
                    is EnemyBehaviorState.DEAD
                )
                or _enemy_hit_feedback_active(
                    enemy,
                    current_time,
                )
            )
        )
    ]
    healing_aura_seeds = {}

    for enemy in living_enemies:
        heal_target = enemy.heal_target

        if (
            enemy.type == "priest"
            and enemy.behavior_state
            is EnemyBehaviorState.PREPARING_HEAL
            and heal_target is not None
            and heal_target.health > 0
        ):
            link_seed = (
                floor.visual_seed
                ^ _stable_text_seed(
                    f"heal:{enemy.name}:{heal_target.name}"
                )
            )
            healing_aura_seeds[id(enemy)] = link_seed
            healing_aura_seeds[id(heal_target)] = (
                link_seed ^ 0x9E3779B9
            )

    draw_ground_items(
        view_surface,
        game_state,
        assets["ground_item_sprites"],
        current_time,
        ACT_THREE_TILE_SIZE,
        (-camera_x, -camera_y),
    )

    for enemy in living_enemies:
        aura_seed = healing_aura_seeds.get(id(enemy))

        if aura_seed is None:
            continue

        aura_position = _view_position(
            enemy.column,
            enemy.row,
            camera_x,
            camera_y,
        )
        _draw_healing_aura(
            view_surface,
            aura_position[0],
            aura_position[1],
            current_time,
            aura_seed,
        )

    for enemy in sorted(
        rendered_enemies,
        key=lambda living_enemy: living_enemy.row,
    ):
        enemy_position = _view_position(
            enemy.column,
            enemy.row,
            camera_x,
            camera_y,
        )
        if (
            exchange_active
            and enemy.name == exchange_enemy_name
        ):
            exchange_enemy_start = _view_position(
                exchange_enemy_origin[0],
                exchange_enemy_origin[1],
                camera_x,
                camera_y,
            )
            exchange_enemy_end = _view_position(
                exchange_player_origin[0],
                exchange_player_origin[1],
                camera_x,
                camera_y,
            )
            enemy_position = (
                round(
                    exchange_enemy_start[0]
                    + (
                        exchange_enemy_end[0]
                        - exchange_enemy_start[0]
                    )
                    * exchange_eased_progress
                ),
                round(
                    exchange_enemy_start[1]
                    + (
                        exchange_enemy_end[1]
                        - exchange_enemy_start[1]
                    )
                    * exchange_eased_progress
                ),
            )

        enemy_sprite = _enemy_sprite(
            assets,
            enemy,
            current_time,
            floor.visual_seed,
        )
        if enemy.health > 0:
            draw_actor_shadow(
                view_surface,
                enemy_sprite,
                enemy_position,
                ACT_THREE_TILE_SIZE,
                floor.torches,
                camera_x,
                camera_y,
                (
                    "enemy",
                    enemy.type,
                    enemy_sprite.get_size(),
                ),
            )
        if enemy.health > 0 and enemy.curse_turns > 0:
            _draw_warlock_curse_aura(
                view_surface,
                enemy_position[0],
                enemy_position[1],
                current_time,
                floor.visual_seed
                ^ _stable_text_seed(
                    f"curse:{enemy.name}"
                ),
            )
        if (
            exchange_active
            and enemy.name == exchange_enemy_name
        ):
            _draw_warlock_curse_aura(
                view_surface,
                enemy_position[0],
                enemy_position[1],
                current_time,
                floor.visual_seed
                ^ _stable_text_seed(
                    f"exchange:enemy:{enemy.name}"
                ),
            )
        _draw_enemy_hit_feedback(
            view_surface,
            enemy_sprite,
            enemy_position,
            enemy,
            current_time,
            fonts["sidebar_numbers"],
        )
        if enemy.health > 0 and enemy.is_aggro:
            pygame.draw.rect(
                view_surface,
                DANGER_BORDER_COLOR,
                (
                    enemy_position[0] + 3,
                    enemy_position[1] + 3,
                    ACT_THREE_TILE_SIZE - 6,
                    ACT_THREE_TILE_SIZE - 6,
                ),
                width=2,
                border_radius=5,
            )

        if enemy.health > 0:
            draw_sentinel_status(
                view_surface,
                enemy,
                enemy_position,
                current_time,
                ACT_THREE_TILE_SIZE,
            )
            _draw_health_bar(
                view_surface,
                enemy_position[0],
                enemy_position[1],
                enemy.health,
                enemy.max_health,
                HEALTH_BAR_COLOR,
            )

    player_subclass = game_state.player.subclass

    if player_subclass not in (
        "berserker",
        "paladin",
        "assassin",
        "archer",
        "warlock",
        "summoner",
    ):
        player_subclass = "berserker"

    attack_elapsed = (
        current_time
        - game_state.player.attack_animation_started_at
    )
    leap_origin = game_state.player.archer_leap_origin
    leap_started_at = game_state.player.archer_leap_started_at
    leap_elapsed = current_time - leap_started_at
    leap_active = (
        player_subclass == "archer"
        and leap_origin is not None
        and leap_started_at > 0
        and 0 <= leap_elapsed < ARCHER_LEAP_DURATION_MS
    )
    berserker_leap_origin = (
        game_state.player.berserker_crushing_leap_origin
    )
    berserker_leap_started_at = (
        game_state.player.berserker_crushing_leap_started_at
    )
    berserker_leap_elapsed = (
        current_time - berserker_leap_started_at
    )
    berserker_leap_travel_active = (
        player_subclass == "berserker"
        and berserker_leap_origin is not None
        and berserker_leap_started_at > 0
        and 0
        <= berserker_leap_elapsed
        < BERSERKER_CRUSHING_LEAP_TRAVEL_MS
    )
    berserker_leap_impact_active = (
        player_subclass == "berserker"
        and berserker_leap_origin is not None
        and (
            BERSERKER_CRUSHING_LEAP_TRAVEL_MS
            <= berserker_leap_elapsed
            < (
                BERSERKER_CRUSHING_LEAP_TRAVEL_MS
                + BERSERKER_CRUSHING_LEAP_IMPACT_MS
            )
        )
    )
    shield_charge_origin = (
        game_state.player.paladin_shield_charge_origin
    )
    shield_charge_started_at = (
        game_state.player.paladin_shield_charge_started_at
    )
    shield_charge_elapsed = (
        current_time - shield_charge_started_at
    )
    shield_charge_active = (
        player_subclass == "paladin"
        and shield_charge_origin is not None
        and shield_charge_started_at > 0
        and 0
        <= shield_charge_elapsed
        < PALADIN_SHIELD_CHARGE_TRAVEL_MS
    )
    shadow_step_elapsed = current_time - transition_started_at
    shadow_step_active = (
        player_subclass == "assassin"
        and teleport_origin is not None
        and transition_started_at > 0
        and 0
        <= shadow_step_elapsed
        < _TELEPORT_CAMERA_DURATION_MS
    )
    shadow_step_frame = assassin_shadow_step_frame(
        shadow_step_elapsed,
        _TELEPORT_CAMERA_DURATION_MS,
    )
    player_hurt_sprite_active = _player_hurt_sprite_active(
        game_state.player,
        current_time,
    )
    player_death_elapsed = _player_death_elapsed(
        game_state.player,
        current_time,
    )
    if (
        player_subclass in (
            "berserker",
            "paladin",
            "assassin",
            "archer",
            "warlock",
            "summoner",
        )
        and player_death_elapsed is not None
    ):
        if player_subclass == "assassin":
            player_death_frame = _assassin_death_frame(
                game_state.player,
                current_time,
            )
        else:
            player_death_frame = _player_death_frame(
                game_state.player,
                current_time,
            )
        if player_death_frame is None:
            if player_subclass == "summoner":
                player_sprite = assets[
                    "player_summoner_no_familiar_hurt"
                ]
            else:
                player_sprite = assets[
                    f"player_{player_subclass}_hurt"
                ]
        else:
            player_sprite = assets[
                f"player_{player_subclass}_death_{player_death_frame}"
            ]
    elif player_hurt_sprite_active:
        if player_subclass == "berserker":
            player_sprite = assets["player_berserker_hurt"]
        elif player_subclass == "paladin":
            player_sprite = assets["player_paladin_hurt"]
        elif player_subclass == "assassin":
            hurt_elapsed = (
                    current_time
                    - game_state.player.hit_animation_started_at
            )
            hurt_direction = assassin_hurt_direction(
                game_state.player.facing_direction
            )
            hurt_frame = assassin_hurt_frame(
                hurt_elapsed,
                _PLAYER_HIT_SPRITE_DURATION_MS,
                hurt_direction,
            )
            player_sprite = assets[
                f"player_assassin_hurt_{hurt_direction}_{hurt_frame}"
            ]
        elif player_subclass == "archer":
            player_sprite = assets["player_archer_hurt"]
        elif player_subclass == "warlock":
            if game_state.player.warlock_demon_form_active:
                player_sprite = assets["player_warlock_demon_hurt"]
            else:
                player_sprite = assets["player_warlock_hurt"]
        elif player_subclass == "summoner":
            if game_state.player.summoner_familiar_active:
                player_sprite = assets[
                    "player_summoner_no_familiar_hurt"
                ]
            else:
                player_sprite = assets["player_summoner_hurt"]
        else:
            player_sprite = assets[
                f"player_{player_subclass}_idle_0"
            ]
    elif shadow_step_active:
        shadow_step_direction_name = (
            assassin_shadow_step_direction(
                teleport_origin,
                (
                    floor.player_column,
                    floor.player_row,
                ),
            )
        )
        player_sprite = assets[
            (
                "player_assassin_shadow_step_"
                f"{shadow_step_direction_name}_{shadow_step_frame}"
            )
        ]
    elif shield_charge_active:
        player_sprite = assets[
            "player_paladin_shield_charge"
        ]
    elif berserker_leap_travel_active:
        player_sprite = assets[
            "player_berserker_crushing_leap"
        ]
    elif berserker_leap_impact_active:
        player_sprite = assets[
            "player_berserker_crushing_leap_impact"
        ]
    elif leap_active:
        player_sprite = assets["player_archer_leap"]
    elif (
        player_subclass in (
            "assassin",
            "archer",
            "berserker",
            "paladin",
            "warlock",
            "summoner",
        )
        and 0 <= attack_elapsed < _ATTACK_FRAME_DURATION_MS
    ):
        if player_subclass == "assassin":
            attack_direction = assassin_attack_direction(
                game_state.player.facing_direction
            )
            attack_frame = assassin_attack_frame(
                attack_elapsed,
                _ATTACK_FRAME_DURATION_MS,
            )
            player_sprite = assets[
                f"player_assassin_attack_{attack_direction}_{attack_frame}"
            ]
        elif player_subclass == "berserker":
            attack_direction = assassin_attack_direction(
                game_state.player.facing_direction
            )
            attack_frame = assassin_attack_frame(
                attack_elapsed,
                _ATTACK_FRAME_DURATION_MS,
            )
            player_sprite = assets[
                f"player_berserker_attack_{attack_direction}_{attack_frame}"
            ]
        elif (
            player_subclass == "warlock"
            and game_state.player.warlock_demon_form_active
        ):
            player_sprite = assets["player_warlock_demon_attack"]
        elif (
            player_subclass == "summoner"
            and game_state.player.summoner_familiar_active
        ):
            player_sprite = assets[
                "player_summoner_no_familiar_attack"
            ]
        else:
            player_sprite = assets[
                f"player_{player_subclass}_attack"
            ]
    elif (
        player_subclass in (
            "assassin",
            "archer",
            "berserker",
            "paladin",
            "warlock",
            "summoner",
        )
        and movement_progress is not None
    ):
        movement_frame_count = (
            ASSASSIN_WALK_FRAME_COUNT
            if player_subclass == "assassin"
            else (
                BERSERKER_WALK_FRAME_COUNT
                if player_subclass == "berserker"
                else _MOVE_FRAME_COUNT
            )
        )
        if player_subclass == "assassin":
            movement_frame = assassin_walk_frame(current_time)
        elif player_subclass == "berserker":
            movement_frame = berserker_walk_frame(current_time)
        else:
            movement_frame = movement_frame_for_progress(
                movement_progress,
                movement_frame_count,
            )

        if player_subclass == "assassin":
            walk_direction = assassin_walk_direction(
                game_state.player.facing_direction
            )
            player_sprite = assets[
                f"player_assassin_walk_{walk_direction}_{movement_frame}"
            ]
        elif player_subclass == "berserker":
            walk_direction = assassin_walk_direction(
                game_state.player.facing_direction
            )
            player_sprite = assets[
                f"player_berserker_walk_{walk_direction}_{movement_frame}"
            ]
        elif (
            player_subclass == "warlock"
            and game_state.player.warlock_demon_form_active
        ):
            player_sprite = assets[
                f"player_warlock_demon_walk_{movement_frame}"
            ]
        elif (
            player_subclass == "summoner"
            and game_state.player.summoner_familiar_active
        ):
            player_sprite = assets[
                f"player_summoner_no_familiar_walk_{movement_frame}"
            ]
        else:
            player_sprite = assets[
                f"player_{player_subclass}_walk_{movement_frame}"
            ]
    else:
        if player_subclass == "assassin":
            player_frame = assassin_idle_frame(current_time)
        elif player_subclass == "berserker":
            player_frame = berserker_idle_frame(current_time)
        else:
            player_frame = _idle_frame(
                current_time,
                (
                        floor.visual_seed
                        ^ _stable_text_seed(
                    f"player:{player_subclass}"
                )
                ),
            )
        if player_subclass == "assassin":
            idle_direction = assassin_walk_direction(
                game_state.player.facing_direction
            )

            if idle_direction == "down":
                player_sprite = assets[
                    f"player_assassin_idle_{player_frame}"
                ]
            else:
                player_sprite = assets[
                    f"player_assassin_idle_{idle_direction}_{player_frame}"
                ]
        elif player_subclass == "berserker":
            idle_direction = assassin_walk_direction(
                game_state.player.facing_direction
            )

            if idle_direction == "down":
                player_sprite = assets[
                    f"player_berserker_idle_{player_frame}"
                ]
            else:
                player_sprite = assets[
                    f"player_berserker_idle_{idle_direction}_{player_frame}"
                ]
        elif (
            player_subclass == "warlock"
            and game_state.player.warlock_demon_form_active
        ):
            player_sprite = assets[
                f"player_warlock_demon_idle_{player_frame}"
            ]
        elif (
            player_subclass == "summoner"
            and game_state.player.summoner_familiar_active
        ):
            player_sprite = assets[
                f"player_summoner_no_familiar_idle_{player_frame}"
            ]
        else:
            player_sprite = assets[
                f"player_{player_subclass}_idle_{player_frame}"
            ]
    player_position = _view_position(
        floor.player_column,
        floor.player_row,
        camera_x,
        camera_y,
    )
    if (
        movement_progress is not None
        and game_state.player.movement_origin is not None
    ):
        movement_origin_position = _view_position(
            game_state.player.movement_origin[0],
            game_state.player.movement_origin[1],
            camera_x,
            camera_y,
        )
        player_position = interpolate_player_position(
            movement_origin_position,
            player_position,
            movement_progress,
        )
    if (
        shadow_step_active
        and shadow_step_frame
        < ASSASSIN_SHADOW_STEP_FRAME_COUNT // 2
    ):
        player_position = _view_position(
            teleport_origin[0],
            teleport_origin[1],
            camera_x,
            camera_y,
        )
    if (
        player_subclass in (
            "berserker",
            "paladin",
            "assassin",
            "archer",
            "warlock",
            "summoner",
        )
        and player_death_elapsed is not None
    ):
        death_offset_x, death_offset_y = _player_death_sprite_offset(
            game_state.player,
            current_time,
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
    if exchange_active:
        exchange_player_start = _view_position(
            exchange_player_origin[0],
            exchange_player_origin[1],
            camera_x,
            camera_y,
        )
        exchange_player_end = _view_position(
            exchange_enemy_origin[0],
            exchange_enemy_origin[1],
            camera_x,
            camera_y,
        )
        player_position = (
            round(
                exchange_player_start[0]
                + (
                    exchange_player_end[0]
                    - exchange_player_start[0]
                )
                * exchange_eased_progress
            ),
            round(
                exchange_player_start[1]
                + (
                    exchange_player_end[1]
                    - exchange_player_start[1]
                )
                * exchange_eased_progress
            ),
        )
    elif shield_charge_active:
        shield_charge_progress = min(
            1,
            shield_charge_elapsed
            / PALADIN_SHIELD_CHARGE_TRAVEL_MS,
        )
        eased_progress = (
            shield_charge_progress
            * shield_charge_progress
            * (3 - 2 * shield_charge_progress)
        )
        shield_charge_start_position = _view_position(
            shield_charge_origin[0],
            shield_charge_origin[1],
            camera_x,
            camera_y,
        )
        player_position = (
            round(
                shield_charge_start_position[0]
                + (
                    leap_end_position[0]
                    - shield_charge_start_position[0]
                )
                * eased_progress
            ),
            round(
                shield_charge_start_position[1]
                + (
                    leap_end_position[1]
                    - shield_charge_start_position[1]
                )
                * eased_progress
            ),
        )
        if floor.player_column < shield_charge_origin[0]:
            player_sprite = pygame.transform.flip(
                player_sprite,
                True,
                False,
            )
    elif leap_active:
        leap_progress = min(
            1,
            leap_elapsed / ARCHER_LEAP_DURATION_MS,
        )
        eased_progress = 1 - (1 - leap_progress) ** 3
        leap_start_position = _view_position(
            leap_origin[0],
            leap_origin[1],
            camera_x,
            camera_y,
        )
        player_position = (
            round(
                leap_start_position[0]
                + (leap_end_position[0] - leap_start_position[0])
                * eased_progress
            ),
            round(
                leap_start_position[1]
                + (leap_end_position[1] - leap_start_position[1])
                * eased_progress
                - math.sin(math.pi * leap_progress) * 8
            ),
        )
    elif berserker_leap_travel_active:
        leap_progress = min(
            1,
            berserker_leap_elapsed
            / BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
        )
        eased_progress = 1 - (1 - leap_progress) ** 3
        leap_start_position = _view_position(
            berserker_leap_origin[0],
            berserker_leap_origin[1],
            camera_x,
            camera_y,
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
                - math.sin(math.pi * leap_progress) * 13
            ),
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

    if player_death_elapsed is None:
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
        if last_rage_is_active:
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
        if (
            last_rage_is_active
            or berserker_health_ratio
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

    if exchange_active:
        _draw_warlock_curse_aura(
            view_surface,
            player_position[0],
            player_position[1],
            current_time,
            floor.visual_seed
            ^ _stable_text_seed("exchange:warlock"),
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

    from presentation.world import draw_impact_block_effect

    draw_impact_block_effect(
        view_surface,
        game_state.player,
        (
            player_position[0] + ACT_THREE_TILE_SIZE // 2,
            player_position[1] + ACT_THREE_TILE_SIZE // 2,
        ),
        current_time,
        ACT_THREE_TILE_SIZE,
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
    if (
        player_subclass == "warlock"
        and exchange_player_origin is not None
        and exchange_enemy_origin is not None
        and exchange_started_at > 0
        and exchange_elapsed
        >= WARLOCK_SOUL_EXCHANGE_TRAVEL_MS
    ):
        game_state.player.warlock_soul_exchange_player_origin = None
        game_state.player.warlock_soul_exchange_enemy_origin = None
        game_state.player.warlock_soul_exchange_enemy_name = None
        game_state.player.warlock_soul_exchange_started_at = 0

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
        if game_state.player.warlock_demon_form_active:
            _draw_warlock_demon_aura(
                view_surface,
                player_position[0],
                player_position[1],
                current_time,
            )
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

    if (
        player_subclass == "warlock"
        and game_state.player.warlock_demon_form_active
        and player_death_elapsed is None
    ):
        _draw_warlock_demon_overlay(
            view_surface,
            assets,
            current_time,
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
