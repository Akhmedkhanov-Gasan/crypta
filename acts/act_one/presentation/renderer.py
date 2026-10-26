from acts.act_one.camera import draw_act_one_camera_view
from acts.act_one.interface import draw_act_one_upgrade_screen
from acts.act_one.presentation.crate_presentation import draw_act_one_crate
from acts.act_one.presentation.environment import draw_act_one_fog_of_war
from acts.act_one.presentation.hud import draw_act_one_hud
from acts.act_one.presentation.intro import (
    act_one_intro_head_lift,
    act_one_intro_hud_opacity,
    draw_act_one_intro_overlay,
    draw_act_one_intro_world,
)
from acts.act_one.presentation.player import draw_act_one_wait_indicator
from acts.act_one.presentation.tutorial_presentation import (
    draw_tutorial_floor_labels,
)
from acts.act_one.presentation.warden_floor import draw_warden_braziers
from acts.act_one.presentation.warden_intro import (
    draw_warden_intro_overlay,
    draw_warden_intro_world,
)
from acts.act_one.presentation.world import (
    draw_act_one_atmosphere,
    draw_act_one_boss_effects,
    draw_act_one_pickup_effect,
    draw_act_one_player_attack_effect,
    draw_attack_markers,
    draw_boss_door,
    draw_chest,
    draw_coin,
    draw_dungeon,
    draw_enemy,
    draw_key,
    draw_map_frame,
    draw_passage,
    draw_player,
    draw_player_attack_markers,
    draw_potion,
)
from acts.act_one.visibility import position_is_visible
from acts.act_one.warden_intro import (
    warden_intro_enemy_visible,
    warden_intro_hud_opacity,
)
from logic import get_enemy_occupied_positions
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import BACKGROUND_COLOR, TILE_SIZE


def _draw_boss_door(screen, game_state):
    floor = game_state.floor

    if floor.boss_door is None:
        return

    living_boss_group = any(
        enemy.health > 0 and enemy.boss_group
        for enemy in floor.enemies
    )
    living_boss_guards = any(
        enemy.health > 0 and not enemy.boss_group
        for enemy in floor.enemies
    )
    door_is_open = not living_boss_guards

    if floor.seal_boss_door_during_fight and floor.boss_fight_started:
        door_is_open = not living_boss_group

    draw_boss_door(
        screen,
        floor.boss_door[0],
        floor.boss_door[1],
        door_is_open,
    )


def _draw_passages(screen, game_state, shared_sprites):
    floor = game_state.floor

    if not floor.passages:
        return

    living_enemies_remain = any(
        enemy.health > 0
        for enemy in floor.enemies
    )

    for passage in floor.passages:
        passage_is_open = (
            not passage.requires_clear
            or game_state.player.player_class is not None
            or not living_enemies_remain
        )
        draw_passage(
            screen,
            passage.wall_position[0],
            passage.wall_position[1],
            passage_is_open,
            1,
            shared_sprites,
            is_return=False,
        )


def _draw_items(screen, game_state, gameplay_assets, shared_sprites, current_time):
    floor = game_state.floor

    for crate in floor.breakable_crates:
        draw_act_one_crate(screen, crate)

    for potion in floor.potions:
        draw_potion(
            screen,
            potion.column,
            potion.row,
            1,
            gameplay_assets,
        )

    for chest in floor.chests:
        draw_chest(
            screen,
            chest,
            1,
            shared_sprites,
            current_time,
        )
        if not chest.loot_available:
            continue
        if chest.contains == "potion":
            draw_potion(
                screen,
                chest.column,
                chest.row,
                1,
                gameplay_assets,
            )
        else:
            draw_coin(
                screen,
                chest.column,
                chest.row,
                1,
                shared_sprites,
            )

    for column, row in floor.dropped_gold:
        draw_coin(screen, column, row, 1, shared_sprites)

    for column, row in floor.dropped_keys:
        draw_key(screen, column, row, 1, shared_sprites)


def _draw_player(screen, game_state, shared_sprites, status_font, current_time):
    floor = game_state.floor
    player = game_state.player
    intro = getattr(game_state, "act_one_intro", None)

    draw_player(
        screen,
        floor.player_column,
        floor.player_row,
        player.health,
        player.max_health,
        player.player_class,
        1,
        shared_sprites,
        player.invisibility_turns,
        current_time=current_time,
        potion_effect_started_at=player.potion_effect_started_at,
        hit_animation_started_at=player.hit_animation_started_at,
        hit_origin=player.hit_origin,
        attack_animation_started_at=player.attack_animation_started_at,
        attack_target=player.act_one_attack_target,
        movement_animation_started_at=player.movement_animation_started_at,
        movement_origin=player.act_one_movement_origin,
        dodge_animation_started_at=player.act_one_dodge_started_at,
        dodge_origin=player.act_one_dodge_origin,
        death_animation_started_at=player.death_animation_started_at,
        hit_damage=player.hit_damage,
        damage_font=status_font,
        act_one_head_lift_progress=act_one_intro_head_lift(intro),
        act_one_hud_opacity=min(
            act_one_intro_hud_opacity(intro, current_time),
            warden_intro_hud_opacity(floor, current_time),
        ),
        control_player=player,
    )

    if player.health > 0:
        draw_act_one_wait_indicator(
            screen,
            MAP_OFFSET_X + floor.player_column * TILE_SIZE + TILE_SIZE // 2,
            MAP_OFFSET_Y + floor.player_row * TILE_SIZE + TILE_SIZE // 2,
            current_time,
            player.act_one_wait_effect_started_at,
        )

    if game_state.floor_index == 0:
        draw_act_one_intro_world(screen, intro)

    draw_warden_intro_world(screen, floor, current_time)


def _draw_enemies(screen, game_state, shared_sprites, status_font, current_time):
    floor = game_state.floor

    for enemy in floor.enemies:
        if not warden_intro_enemy_visible(floor, enemy):
            continue
        if not any(
            position_is_visible(floor, column, row)
            for column, row in get_enemy_occupied_positions(enemy)
        ):
            continue

        recent_hit = (
            enemy.hit_animation_started_at >= 0
            and 0 <= current_time - enemy.hit_animation_started_at < 380
        )
        has_death_effect = enemy.death_animation_started_at >= 0
        if enemy.health > 0 or recent_hit or has_death_effect:
            draw_enemy(
                screen,
                enemy,
                1,
                shared_sprites,
                current_time,
                status_font,
            )


def draw_act_one_gameplay(
    game_surface,
    world_surface,
    camera,
    game_state,
    fonts,
    gameplay_assets,
    shared_sprites,
    current_time,
    act_floor,
    mouse_position,
):
    floor = game_state.floor
    player = game_state.player
    status_font = fonts["status"]

    game_surface.fill(BACKGROUND_COLOR)
    world_surface.fill(BACKGROUND_COLOR)
    draw_dungeon(
        world_surface,
        floor.map,
        1,
        shared_sprites,
        act_floor,
        floor.visual_seed,
    )
    draw_act_one_atmosphere(
        world_surface,
        1,
        floor.player_column,
        floor.player_row,
        floor.map,
        act_floor,
        floor.visual_seed,
        current_time,
    )
    draw_tutorial_floor_labels(world_surface, game_state)
    draw_warden_braziers(world_surface, floor, current_time)
    draw_map_frame(world_surface, 1)
    draw_player_attack_markers(
        world_surface,
        game_state.player_attack_targets,
    )
    draw_attack_markers(
        world_surface,
        floor.enemies,
        1,
        current_time,
        None,
        None,
    )
    draw_act_one_boss_effects(
        world_surface,
        floor.enemies,
        1,
        current_time,
        status_font,
    )
    _draw_boss_door(world_surface, game_state)
    _draw_passages(world_surface, game_state, shared_sprites)
    _draw_items(
        world_surface,
        game_state,
        gameplay_assets,
        shared_sprites,
        current_time,
    )
    _draw_player(
        world_surface,
        game_state,
        shared_sprites,
        status_font,
        current_time,
    )
    _draw_enemies(
        world_surface,
        game_state,
        shared_sprites,
        status_font,
        current_time,
    )
    draw_act_one_player_attack_effect(
        world_surface,
        1,
        floor.player_column,
        floor.player_row,
        player.act_one_attack_target,
        current_time,
        player.attack_animation_started_at,
        player.act_one_attack_was_critical,
    )
    draw_act_one_pickup_effect(
        world_surface,
        1,
        player.act_one_pickup_kind,
        player.act_one_pickup_origin,
        current_time,
        player.act_one_pickup_started_at,
    )
    draw_act_one_fog_of_war(
        world_surface,
        1,
        floor,
        current_time,
        player.movement_animation_started_at,
        player.act_one_movement_origin,
    )
    draw_act_one_camera_view(game_surface, world_surface, camera)
    if not game_state.class_selection_open:
        draw_act_one_hud(
            game_surface,
            game_state,
            fonts["hud"],
            fonts["hud_small"],
            status_font,
            gameplay_assets,
            current_time,
        )

    if game_state.upgrade_screen_open:
        draw_act_one_upgrade_screen(
            game_surface,
            fonts["title"],
            fonts["interface"],
            player,
            game_state.act_one_upgrades_remaining,
            game_state.upgrade_message,
            mouse_position,
        )

    draw_act_one_intro_overlay(
        game_surface,
        getattr(game_state, "act_one_intro", None),
        fonts["interface"],
        fonts["text"],
    )
    draw_warden_intro_overlay(
        game_surface,
        floor,
        fonts["interface"],
        fonts["text"],
    )


__all__ = ["draw_act_one_gameplay"]
