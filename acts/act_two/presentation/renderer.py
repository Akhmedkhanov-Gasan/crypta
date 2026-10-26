import pygame

from game.state import GameState
from settings import BACKGROUND_COLOR

from acts.act_one.presentation.world import draw_dungeon
from acts.act_one.presentation.world import (
    draw_attack_markers,
    draw_boss_door,
    draw_chest,
    draw_coin,
    draw_enemy,
    draw_fire_bomb,
    draw_passage,
    draw_player,
    draw_player_attack_markers,
    draw_potion,
    draw_scroll,
)
from acts.act_two.consumables import FIRE_BOMB, SCROLLS
from acts.act_two.presentation.awakening_timing import (
    AWAKENING_WORLD_SWAP_MS,
    CLASS_SELECTION_OLD_MAN_FADE_END_MS,
    CLASS_SELECTION_OLD_MAN_FADE_START_MS,
    CLASS_SELECTION_TRANSFORM_END_MS,
    CLASS_SELECTION_TURN_TO_OLD_MAN_MS,
    CLASS_SELECTION_WALK_END_MS,
    CLASS_SELECTION_WALK_START_MS,
)
from acts.act_two.presentation.abilities import (
    draw_act_two_ability_preview,
    draw_act_two_arcane_burst_effect,
    draw_act_two_power_cleave_effect,
)
from acts.act_two.presentation.bloody_altar import draw_bloody_altar_object
from acts.act_two.presentation.bosses.oracle import draw_oracle_projectiles
from acts.act_two.presentation.bosses.oracle_arena import (
    draw_oracle_lighting,
    draw_oracle_pillars,
)
from acts.act_two.presentation.bosses.oracle_combat_fx import (
    draw_oracle_attack_fx,
    draw_oracle_blackfire,
)
from acts.act_two.presentation.bosses.oracle_death import draw_oracle_death_fx
from acts.act_two.presentation.bosses.oracle_phase_transition import (
    oracle_cutscene_active,
)
from acts.act_two.presentation.bosses.oracle_phase_two import (
    draw_oracle_phase_two_fx,
)
from acts.act_two.presentation.bosses.oracle_room import (
    draw_oracle_braziers,
    draw_oracle_gate,
)
from acts.act_two.presentation.camera import (
    act_two_screen_to_cell,
    act_two_world_surface_size,
    draw_act_two_camera_view,
    update_act_two_camera,
)
from acts.act_two.presentation.combat.attack_effects import (
    draw_player_attack_effect,
)
from acts.act_two.presentation.enemies.brute.aftershocks import (
    draw_brute_aftershocks,
)
from acts.act_two.presentation.environment.atmosphere import draw_atmosphere
from acts.act_two.presentation.fire_bomb import (
    draw_fire_bomb_flight,
    draw_fire_bomb_targeting,
    draw_fire_zones,
)
from acts.act_two.presentation.fog import draw_act_two_fog_of_war
from acts.act_two.presentation.items import (
    draw_act_one_revisit_corpses,
    draw_coin_pile,
)
from acts.act_two.presentation.items.effects import draw_pickup_effect
from acts.act_two.presentation.items.ground_items import (
    draw_ground_items,
    draw_pickup_hint,
)
from acts.act_two.presentation.items.renderer import draw_breakable_crate
from acts.act_two.presentation.movement import (
    MAGE_MOVE_DURATION_MS,
    ROGUE_MOVE_DURATION_MS,
    WARRIOR_MOVE_DURATION_MS,
    sample_mage_movement,
    sample_rogue_movement,
    sample_warrior_movement,
)
from acts.act_two.presentation.player import draw_act_two_wait_indicator
from acts.act_two.presentation.runes import draw_act_two_rune_room
from acts.act_two.presentation.scrolls import draw_scroll_effect
from acts.act_two.presentation.trader import draw_act_two_trader
from acts.act_two.presentation.traps import draw_act_two_spike_traps
from acts.act_two.presentation.treasury import draw_act_two_treasury
from acts.act_two.visibility import position_is_visible
from application.ground_items import ground_item_input_available
from logic import get_enemy_occupied_positions, get_mage_resonance_target
from presentation.combat_effects import draw_impact_block_effect
from presentation.cursors import set_warlock_staff_cursor
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


_CLASS_TRANSFORMATION_COLORS = {
    "warrior": (186, 58, 48),
    "rogue": (126, 48, 166),
    "mage": (55, 108, 183),
}

_AWAKENING_WALK_PATH = (
    (18, 7),
    (18, 6),
    (18, 5),
    (18, 4),
    (18, 3),
    (19, 3),
)

_CLASS_MOVEMENT_SAMPLERS = {
    "warrior": sample_warrior_movement,
    "rogue": sample_rogue_movement,
    "mage": sample_mage_movement,
}

_CLASS_MOVEMENT_DURATIONS = {
    "warrior": WARRIOR_MOVE_DURATION_MS,
    "rogue": ROGUE_MOVE_DURATION_MS,
    "mage": MAGE_MOVE_DURATION_MS,
}


def _awakening_player_movement(
    game_state,
    current_time,
):
    floor = game_state.floor
    player = game_state.player
    default_state = (
        floor.player_column,
        floor.player_row,
        player.act_two_movement_started_at,
        player.act_two_movement_origin,
        player.act_two_facing_direction,
        float(floor.player_column),
        float(floor.player_row),
    )

    if (
        not game_state.class_selection_open
        or not game_state.class_transition_world_swapped
        or game_state.class_selection_choice_started_at <= 0
    ):
        return default_state

    choice_elapsed = (
        current_time
        - game_state.class_selection_choice_started_at
    )
    if choice_elapsed < CLASS_SELECTION_WALK_START_MS:
        return default_state

    final_column, final_row = _AWAKENING_WALK_PATH[-1]
    if choice_elapsed >= CLASS_SELECTION_WALK_END_MS:
        return (
            final_column,
            final_row,
            -1,
            None,
            (0, -1),
            float(final_column),
            float(final_row),
        )

    movement_sampler = _CLASS_MOVEMENT_SAMPLERS.get(
        player.player_class,
    )
    movement_duration = _CLASS_MOVEMENT_DURATIONS.get(
        player.player_class,
    )
    if movement_sampler is None or movement_duration is None:
        return default_state

    walk_progress = (
        choice_elapsed - CLASS_SELECTION_WALK_START_MS
    ) / (
        CLASS_SELECTION_WALK_END_MS
        - CLASS_SELECTION_WALK_START_MS
    )
    segment_count = len(_AWAKENING_WALK_PATH) - 1
    path_progress = walk_progress * segment_count
    segment_index = min(
        segment_count - 1,
        int(path_progress),
    )
    segment_progress = path_progress - segment_index

    origin = _AWAKENING_WALK_PATH[segment_index]
    destination = _AWAKENING_WALK_PATH[segment_index + 1]
    sampled_elapsed = min(
        movement_duration - 1,
        round(segment_progress * movement_duration),
    )
    movement_started_at = current_time - sampled_elapsed
    movement_pose = movement_sampler(
        destination[0],
        destination[1],
        origin,
        current_time,
        movement_started_at,
    )
    focus_column = (
        movement_pose.ground_position[0] - MAP_OFFSET_X
    ) / TILE_SIZE
    focus_row = (
        movement_pose.ground_position[1] - MAP_OFFSET_Y
    ) / TILE_SIZE

    return (
        destination[0],
        destination[1],
        movement_started_at,
        origin,
        (
            destination[0] - origin[0],
            destination[1] - origin[1],
        ),
        focus_column,
        focus_row,
    )


def _awakening_player_visual_position(
    game_state,
    current_time,
):
    movement_state = _awakening_player_movement(
        game_state,
        current_time,
    )
    return movement_state[-2], movement_state[-1]


def _draw_awakening_transformation(
    target,
    sprites,
    player_class,
    column,
    row,
    choice_elapsed,
):
    if (
        player_class not in _CLASS_TRANSFORMATION_COLORS
        or choice_elapsed >= CLASS_SELECTION_TRANSFORM_END_MS
    ):
        return

    progress = max(
        0.0,
        min(
            1.0,
            choice_elapsed
            / CLASS_SELECTION_TRANSFORM_END_MS,
        ),
    )
    position = (
        round(MAP_OFFSET_X + column * TILE_SIZE),
        round(MAP_OFFSET_Y + row * TILE_SIZE),
    )

    unawakened = sprites["player_unawakened"].copy()
    unawakened.set_alpha(
        round(255 * (1.0 - progress)),
    )
    target.blit(
        unawakened,
        position,
    )

    color = _CLASS_TRANSFORMATION_COLORS[player_class]
    effect = pygame.Surface(
        (TILE_SIZE + 16, TILE_SIZE + 16),
        pygame.SRCALPHA,
    )
    visibility = 1.0 - abs(progress * 2.0 - 1.0)

    pygame.draw.circle(
        effect,
        (
            color[0],
            color[1],
            color[2],
            round(120 * visibility),
        ),
        (
            effect.get_width() // 2,
            effect.get_height() // 2,
        ),
        round(10 + progress * 12),
        width=2,
    )

    for particle_index in range(12):
        particle_x = (
            5
            + (
                particle_index * 11
                + round(progress * 19)
            )
            % (TILE_SIZE + 6)
        )
        particle_y = (
            5
            + (
                particle_index * 7
                - round(progress * 24)
            )
            % (TILE_SIZE + 6)
        )
        pygame.draw.rect(
            effect,
            (
                color[0],
                color[1],
                color[2],
                round(210 * visibility),
            ),
            (
                particle_x,
                particle_y,
                2,
                2,
            ),
        )

    target.blit(
        effect,
        (
            position[0] - 8,
            position[1] - 8,
        ),
    )


class ActTwoRenderer:
    def __init__(self):
        self.world_surface = None
        self.map_surface = None
        self.map_cache_key = None

    def reset(self):
        self.world_surface = None
        self.map_surface = None
        self.map_cache_key = None

    @staticmethod
    def _decor_excluded_positions(floor):
        positions = {
            (floor.stairs_column, floor.stairs_row),
            *((chest.column, chest.row) for chest in floor.chests),
            *((crate.column, crate.row) for crate in floor.breakable_crates),
            *((potion.column, potion.row) for potion in floor.potions),
            *((trap.column, trap.row) for trap in floor.spike_traps),
            *floor.boss_columns,
            *floor.boss_emitters,
        }
        if floor.boss_door is not None:
            positions.add(floor.boss_door)
        if floor.upgrade_altar is not None:
            positions.add(floor.upgrade_altar)
        if floor.bloody_altar is not None:
            positions.add((floor.bloody_altar.column, floor.bloody_altar.row))
        if floor.treasury_room is not None:
            positions.update(
                {
                    floor.treasury_room.door_position,
                    floor.treasury_room.chest_position,
                    *floor.treasury_room.statue_positions,
                }
            )
        if floor.rune_room is not None:
            positions.update(
                {
                    floor.rune_room.door_position,
                    floor.rune_room.pedestal_position,
                    *floor.rune_room.floor_rune_positions,
                }
            )
        return tuple(sorted(positions))

    def _prepare_world_surface(
        self,
        game_state: GameState,
        sprites,
        act_floor,
    ):
        floor = game_state.floor
        world_size = act_two_world_surface_size(floor.map)
        if self.world_surface is None or self.world_surface.get_size() != world_size:
            self.world_surface = pygame.Surface(world_size)
            self.map_surface = None
            self.map_cache_key = None

        excluded_positions = self._decor_excluded_positions(floor)
        cache_key = (
            game_state.floor_index,
            floor.visual_seed,
            tuple(floor.map),
            excluded_positions,
        )
        if self.map_cache_key != cache_key:
            self.map_surface = pygame.Surface(world_size)
            self.map_surface.fill(BACKGROUND_COLOR)
            visual_map = floor.map
            if floor.has_oracle_gate:
                visual_map = [row.replace("C", ".") for row in visual_map]
            draw_dungeon(
                self.map_surface,
                visual_map,
                2,
                sprites,
                act_floor,
                floor.visual_seed,
                excluded_positions,
            )
            self.map_cache_key = cache_key

        self.world_surface.fill(BACKGROUND_COLOR)
        self.world_surface.blit(self.map_surface, (0, 0))
        return self.world_surface

    def draw_environment(
        self,
        game_state: GameState,
        camera,
        sprites,
        current_time,
        act_floor,
    ):
        floor = game_state.floor
        focus_column, focus_row = (
            _awakening_player_visual_position(
                game_state,
                current_time,
            )
        )
        if not oracle_cutscene_active(floor):
            update_act_two_camera(
                camera,
                floor.map,
                focus_column,
                focus_row,
                game_state.floor_index,
                current_time,
            )

        target = self._prepare_world_surface(game_state, sprites, act_floor)
        if not floor.has_oracle_gate:
            draw_atmosphere(
                target,
                focus_column,
                focus_row,
                floor.map,
                act_floor,
                floor.visual_seed,
                current_time,
            )
        draw_oracle_braziers(target, floor, current_time)
        draw_oracle_pillars(target, floor, current_time)
        draw_act_two_spike_traps(
            target,
            floor.spike_traps,
            sprites,
            floor.visible_cells,
            current_time,
        )
        draw_brute_aftershocks(target, floor, current_time)
        draw_act_two_treasury(
            target,
            floor.treasury_room,
            sprites,
            floor.visible_cells,
            current_time,
        )
        draw_act_two_rune_room(
            target,
            floor.rune_room,
            sprites,
            floor.visible_cells,
            floor.explored_cells,
            current_time,
        )
        for trader in (floor.trader, floor.quest_trader):
            draw_act_two_trader(
                target,
                trader,
                sprites,
                floor.visible_cells,
                current_time,
            )
        draw_bloody_altar_object(
            target,
            floor.bloody_altar,
            sprites,
            floor.visible_cells,
            current_time,
        )
        draw_fire_zones(target, game_state, sprites, current_time)
        return target

    @staticmethod
    def _draw_targeting(
        target,
        game_state,
        camera,
        current_time,
        mouse_position,
        input_state,
    ):
        player = game_state.player
        effect_duration = (
            620
            if player.player_class == "mage"
            else 760 if player.selected_rune_id == "rune_of_aftershock" else 460
        )
        effect_elapsed = current_time - player.act_two.ability_effect_started_at
        effect_active = (
            player.act_two.ability_effect_started_at > 0
            and player.act_two.ability_effect_started_at
            == player.attack_animation_started_at
            and 0 <= effect_elapsed < effect_duration
        )
        draw_player_attack_markers(target, [])

        preview_target = (
            act_two_screen_to_cell(mouse_position, camera)
            if mouse_position is not None
            else None
        )
        resonance_cursor_active = (
            player.health > 0
            and not game_state.class_selection_open
            and not game_state.upgrade_screen_open
            and not game_state.trade_screen_open
            and not game_state.rune_selection_open
            and not game_state.bloody_altar_open
            and not game_state.act_two_stats_open
            and not game_state.act_two_journal_open
            and game_state.floor_transition_started_at < 0
            and not oracle_cutscene_active(game_state.floor)
            and input_state.dragged_consumable_slot is None
            and not player.act_two.fire_bomb_aiming
            and player.act_two.scroll_aiming_kind is None
            and get_mage_resonance_target(game_state, preview_target) is not None
        )
        if resonance_cursor_active != input_state.resonance_cursor_active:
            set_warlock_staff_cursor(resonance_cursor_active)
            input_state.resonance_cursor_active = resonance_cursor_active

        draw_act_two_ability_preview(
            target,
            game_state,
            current_time,
            preview_target,
        )
        draw_attack_markers(
            target,
            game_state.floor.enemies,
            2,
            current_time,
            game_state.floor.visible_cells,
            (game_state.floor.player_column, game_state.floor.player_row),
        )
        return effect_active

    @staticmethod
    def _draw_passages(target, game_state, sprites):
        floor = game_state.floor
        if floor.boss_door is not None and not floor.has_oracle_gate:
            living_boss_group = any(
                enemy.health > 0 and enemy.boss_group for enemy in floor.enemies
            )
            living_boss_guards = any(
                enemy.health > 0 and not enemy.boss_group
                for enemy in floor.enemies
            )
            boss_door_is_open = not living_boss_guards
            if floor.seal_boss_door_during_fight and floor.boss_fight_started:
                boss_door_is_open = not living_boss_group
            draw_boss_door(
                target,
                floor.boss_door[0],
                floor.boss_door[1],
                boss_door_is_open,
            )

        living_enemies_remain = any(enemy.health > 0 for enemy in floor.enemies)
        oracle_is_alive = any(
            enemy.type == "oracle" and enemy.health > 0
            for enemy in floor.enemies
        )
        for passage in floor.passages:
            if not passage.discovered:
                continue
            if (
                floor.has_oracle_gate
                and passage.passage_id == "exit"
                and oracle_is_alive
            ):
                continue
            draw_passage(
                target,
                passage.wall_position[0],
                passage.wall_position[1],
                (
                    not passage.requires_clear
                    or game_state.player.player_class is not None
                    or not living_enemies_remain
                ),
                2,
                sprites,
                is_return=passage.passage_id == "entrance",
            )

    @staticmethod
    def _draw_containers(target, game_state, sprites, current_time, status_font):
        floor = game_state.floor
        for crate in floor.breakable_crates:
            visible = position_is_visible(floor, crate.column, crate.row)
            remembered = (
                {
                    "column": crate.column,
                    "row": crate.row,
                    "variant": crate.variant,
                    "is_broken": crate.is_broken,
                    "loot_kind": crate.loot_kind,
                    "loot_available": crate.loot_available,
                }
                if visible
                else floor.act_two_remembered_crates.get((crate.column, crate.row))
            )
            if remembered is None:
                continue
            draw_breakable_crate(target, remembered, sprites)
            if remembered["loot_available"] and not visible:
                draw_loot = (
                    draw_potion if remembered["loot_kind"] == "potion" else draw_coin
                )
                draw_loot(target, remembered["column"], remembered["row"], 2, sprites)

        corpse_types = {
            "goblin",
            "mimic",
            "archer",
            "brute",
            "sentinel",
            "priest",
            "priest_ghost",
        }
        for enemy in floor.enemies:
            if (
                enemy.type in corpse_types
                and enemy.health <= 0
                and position_is_visible(floor, enemy.column, enemy.row)
            ):
                draw_enemy(target, enemy, 2, sprites, current_time, status_font)

        for chest in floor.chests:
            visible = position_is_visible(floor, chest.column, chest.row)
            remembered = (
                chest
                if visible
                else floor.act_two_remembered_chests.get((chest.column, chest.row))
            )
            if remembered is None:
                continue
            draw_chest(target, remembered, 2, sprites, current_time)
            if not remembered["loot_available"] or visible:
                continue
            loot_kind = remembered.get("contains")
            if loot_kind == "potion":
                draw_potion(
                    target,
                    remembered["column"],
                    remembered["row"],
                    2,
                    sprites,
                )
            elif loot_kind == FIRE_BOMB:
                draw_fire_bomb(
                    target,
                    remembered["column"],
                    remembered["row"],
                    2,
                    sprites,
                )
            elif loot_kind in SCROLLS:
                draw_scroll(
                    target,
                    remembered["column"],
                    remembered["row"],
                    loot_kind,
                    2,
                    sprites,
                )
            elif loot_kind == "gold" and remembered.get("requires_key", True):
                draw_coin_pile(
                    target,
                    remembered["column"],
                    remembered["row"],
                    sprites,
                )
            else:
                draw_coin(
                    target,
                    remembered["column"],
                    remembered["row"],
                    2,
                    sprites,
                )

        draw_act_one_revisit_corpses(
            target,
            floor.act_one_revisit,
            floor.visible_cells,
            sprites,
        )
        draw_ground_items(target, game_state, sprites, current_time)
        draw_oracle_blackfire(target, floor, current_time)

    @staticmethod
    def _draw_characters(
        target,
        game_state,
        sprites,
        current_time,
        status_font,
    ):
        floor = game_state.floor
        player = game_state.player
        awakening_active = (
            game_state.class_selection_open
            and game_state.class_transition_world_swapped
        )

        (
            visual_column,
            visual_row,
            visual_movement_started_at,
            visual_movement_origin,
            visual_facing_direction,
            _,
            _,
        ) = _awakening_player_movement(
            game_state,
            current_time,
        )
        choice_elapsed = None

        if awakening_active:
            elapsed = (
                current_time
                - game_state.class_transition_started_at
            )
            old_man_opacity = max(
                0.0,
                min(
                    1.0,
                    (
                        elapsed
                        - AWAKENING_WORLD_SWAP_MS
                    )
                    / 700,
                ),
            )

            if game_state.class_selection_choice_started_at > 0:
                choice_elapsed = (
                    current_time
                    - game_state.class_selection_choice_started_at
                )
                old_man_fade = max(
                    0.0,
                    min(
                        1.0,
                        (
                            choice_elapsed
                            - CLASS_SELECTION_OLD_MAN_FADE_START_MS
                        )
                        / (
                            CLASS_SELECTION_OLD_MAN_FADE_END_MS
                            - CLASS_SELECTION_OLD_MAN_FADE_START_MS
                        ),
                    ),
                )
                old_man_opacity *= 1.0 - old_man_fade

                if choice_elapsed < CLASS_SELECTION_TURN_TO_OLD_MAN_MS:
                    visual_facing_direction = (0, 1)
                elif choice_elapsed < CLASS_SELECTION_WALK_START_MS:
                    visual_facing_direction = (-1, 0)
                else:
                    visual_facing_direction = (0, -1)

            if old_man_opacity > 0:
                old_man = pygame.transform.flip(
                    sprites["old_man_standing"],
                    True,
                    False,
                )
                old_man = old_man.copy()
                old_man.set_alpha(
                    round(255 * old_man_opacity),
                )
                target.blit(
                    old_man,
                    (
                        MAP_OFFSET_X + 17 * TILE_SIZE,
                        MAP_OFFSET_Y + 7 * TILE_SIZE,
                    ),
                )

        draw_player(
            target,
            visual_column,
            visual_row,
            player.health,
            player.max_health,
            player.player_class,
            2,
            sprites,
            player.invisibility_turns,
            current_time,
            player.potion_effect_started_at,
            player.hit_animation_started_at,
            player.hit_origin,
            player.attack_animation_started_at,
            player.act_one_attack_target,
            visual_movement_started_at,
            visual_movement_origin,
            player.act_one_dodge_started_at,
            player.act_one_dodge_origin,
            player.death_animation_started_at,
            player.hit_damage,
            status_font,
            visual_facing_direction,
            player.act_two_blocked_movement_started_at,
            player.act_two_blocked_movement_direction,
            player.act_two.level_up_effect_started_at,
            player.act_two.stoneflesh_hits,
            player.act_two.stoneflesh_effect_started_at,
            player.act_two.dodge_effect_started_at,
            control_player=player,
        )

        if choice_elapsed is not None:
            _draw_awakening_transformation(
                target,
                sprites,
                player.player_class,
                visual_column,
                visual_row,
                choice_elapsed,
            )
        if player.health > 0 and not awakening_active:
            draw_impact_block_effect(
                target,
                player,
                (
                    MAP_OFFSET_X + floor.player_column * TILE_SIZE + TILE_SIZE // 2,
                    MAP_OFFSET_Y + floor.player_row * TILE_SIZE + TILE_SIZE // 2,
                ),
                current_time,
                TILE_SIZE,
            )
            draw_act_two_wait_indicator(
                target,
                floor.player_column,
                floor.player_row,
                current_time,
                player.act_two.wait_effect_started_at,
            )

        for enemy in floor.enemies:
            if enemy.type == "oracle_pillar" or enemy.health <= 0:
                continue
            if not any(
                position in floor.visible_cells
                for position in get_enemy_occupied_positions(enemy)
            ):
                continue
            draw_enemy(target, enemy, 2, sprites, current_time, status_font)
        draw_attack_markers(
            target,
            floor.enemies,
            2,
            current_time,
            floor.visible_cells,
            (floor.player_column, floor.player_row),
            foreground=True,
        )

    @staticmethod
    def _draw_effects(
        target,
        game_state,
        sprites,
        current_time,
        ability_effect_active,
        fire_bomb_target,
    ):
        floor = game_state.floor
        player = game_state.player
        draw_player_attack_effect(
            target,
            floor.player_column,
            floor.player_row,
            (
                None
                if player.player_class == "mage" and ability_effect_active
                else player.act_one_attack_target
            ),
            player.player_class,
            current_time,
            player.attack_animation_started_at,
            player.act_one_attack_was_critical,
        )
        draw_act_two_power_cleave_effect(target, game_state, current_time)
        draw_act_two_arcane_burst_effect(target, game_state, current_time)
        draw_scroll_effect(target, game_state, current_time)
        draw_pickup_effect(
            target,
            sprites,
            player.act_two_pickup_kind,
            player.act_two_pickup_origin,
            current_time,
            player.act_two_pickup_started_at,
        )
        draw_oracle_projectiles(
            target,
            [
                projectile
                for projectile in floor.projectiles
                if position_is_visible(
                    floor,
                    projectile.column,
                    projectile.row,
                )
            ],
            sprites,
        )
        draw_fire_bomb_flight(target, game_state, sprites, current_time)
        draw_fire_bomb_targeting(target, game_state, fire_bomb_target)
        draw_oracle_lighting(target, floor, current_time)
        draw_oracle_attack_fx(target, floor, current_time)
        draw_oracle_phase_two_fx(target, floor, current_time)
        draw_oracle_death_fx(target, floor, current_time)
        draw_act_two_fog_of_war(target, 2, floor)
        draw_oracle_gate(target, floor, current_time)

    def draw_world(
        self,
        game_surface,
        game_state: GameState,
        camera,
        sprites,
        fonts,
        status_font,
        current_time,
        mouse_position,
        input_state,
        ground_item_window,
    ):
        target = self.world_surface
        ability_effect_active = self._draw_targeting(
            target,
            game_state,
            camera,
            current_time,
            mouse_position,
            input_state,
        )
        self._draw_passages(target, game_state, sprites)
        self._draw_containers(
            target,
            game_state,
            sprites,
            current_time,
            status_font,
        )
        self._draw_characters(
            target,
            game_state,
            sprites,
            current_time,
            status_font,
        )
        fire_bomb_target = (
            act_two_screen_to_cell(mouse_position, camera)
            if mouse_position is not None
            else None
        )
        self._draw_effects(
            target,
            game_state,
            sprites,
            current_time,
            ability_effect_active,
            fire_bomb_target,
        )
        draw_act_two_camera_view(
            game_surface,
            target,
            camera,
            game_state.floor,
        )
        draw_pickup_hint(
            game_surface,
            game_state,
            ground_item_window,
            camera,
            fonts["pickup_hint"],
            current_time,
            ground_item_input_available(game_state),
        )
        return (
            game_surface.copy()
            if oracle_cutscene_active(game_state.floor)
            else None
        )

    def draw_gameplay(
        self,
        game_surface,
        game_state: GameState,
        camera,
        sprites,
        fonts,
        status_font,
        current_time,
        act_floor,
        mouse_position,
        input_state,
        ground_item_window,
    ):
        self.draw_environment(
            game_state,
            camera,
            sprites,
            current_time,
            act_floor,
        )
        return self.draw_world(
            game_surface,
            game_state,
            camera,
            sprites,
            fonts,
            status_font,
            current_time,
            mouse_position,
            input_state,
            ground_item_window,
        )


__all__ = ["ActTwoRenderer"]
