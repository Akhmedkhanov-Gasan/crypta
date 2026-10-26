from game.state import GameState

from acts.act_two.abilities import ability_charge_required
from acts.act_two.consumables import get_act_two_consumable_slots
from acts.act_two.progression import get_act_two_attribute_preview
from acts.act_two.presentation.bloody_altar import draw_bloody_altar_window
from acts.act_two.presentation.bosses.oracle_death import draw_oracle_death_overlay
from acts.act_two.presentation.bosses.oracle_intro import draw_oracle_intro
from acts.act_two.presentation.bosses.oracle_phase_transition import (
    draw_oracle_phase_transition,
)
from acts.act_two.presentation.bosses.oracle_ui import draw_oracle_ui
from acts.act_two.presentation.death_scene import (
    draw_act_two_death_dialogue_overlay,
)
from acts.act_two.presentation.hud import draw_act_two_sidebar
from acts.act_two.presentation.player import draw_act_two_player_feedback_overlay
from acts.act_two.presentation.rune_selection import draw_rune_selection
from acts.act_two.presentation.trade_window import draw_act_two_trade_window
from application.ground_items import ground_item_input_available
from presentation.ground_items import draw_ground_item_window
from presentation.status import draw_status
from systems.player_combat import basic_attack_damage_range


class ActTwoInterface:
    def __init__(
        self,
        fonts,
        sprites,
        hud_layout,
        trade_layout,
        bloody_altar_layout,
        oracle_ui_layout,
        oracle_ui_assets,
    ):
        self.fonts = fonts
        self.sprites = sprites
        self.hud_layout = hud_layout
        self.trade_layout = trade_layout
        self.bloody_altar_layout = bloody_altar_layout
        self.oracle_ui_layout = oracle_ui_layout
        self.oracle_ui_assets = oracle_ui_assets

    def draw(
        self,
        surface,
        game_state: GameState,
        camera,
        map_navigation,
        ground_item_window,
        input_state,
        current_time,
        mouse_position,
        oracle_world_frame,
        continuous_movement_available,
    ):
        player = game_state.player
        floor = game_state.floor

        draw_status(
            surface,
            self.fonts["status"],
            game_state.floor_index,
            player.health,
            floor.enemies,
            game_state.game_won,
        )
        draw_oracle_ui(
            surface,
            floor,
            self.oracle_ui_layout,
            self.oracle_ui_assets,
        )
        draw_act_two_player_feedback_overlay(
            surface,
            game_state,
            self.fonts,
            self.sprites,
            current_time,
            camera,
        )

        preview_player = get_act_two_attribute_preview(player)
        displayed_damage_minimum, displayed_damage_maximum = (
            basic_attack_damage_range(preview_player)
        )
        draw_act_two_sidebar(
            surface,
            self.fonts["sidebar_heading"],
            self.fonts["log"],
            self.fonts["sidebar_controls"],
            self.fonts["ability_text"],
            game_state.combat_log,
            preview_player.health,
            preview_player.max_health,
            displayed_damage_minimum,
            displayed_damage_maximum,
            preview_player.crit_chance,
            preview_player.critical_damage_multiplier,
            preview_player.dodge_chance,
            player.attribute_ranks,
            player.act_two.pending_attribute_upgrades,
            get_act_two_consumable_slots(player),
            player.gold_count,
            player.player_class,
            player.selected_rune_id,
            player.level,
            player.experience,
            player.ability_kill_charge,
            ability_charge_required(player),
            player.attribute_points,
            game_state.act_two_stats_open,
            game_state.act_two_journal_open,
            game_state.act_two_journal_scroll,
            mouse_position,
            self.sprites,
            self.hud_layout,
            player.invisibility_turns,
            player.act_two.stoneflesh_hits,
            player.act_two.bloody_pact_id,
            dragged_consumable_slot=input_state.dragged_consumable_slot,
        )
        map_navigation.draw(
            surface,
            game_state,
            mouse_position,
            enabled=continuous_movement_available,
        )

        if game_state.rune_selection_open:
            draw_rune_selection(
                surface,
                game_state,
                self.fonts,
                self.sprites,
                mouse_position,
            )
        if game_state.trade_screen_open:
            draw_act_two_trade_window(
                surface,
                self.sprites,
                self.trade_layout,
                self.fonts,
                mouse_position,
            )
        if game_state.bloody_altar_open:
            draw_bloody_altar_window(
                surface,
                game_state,
                self.sprites,
                self.bloody_altar_layout,
                mouse_position,
            )
        if ground_item_input_available(game_state):
            draw_ground_item_window(
                surface,
                game_state,
                ground_item_window,
                self.sprites,
                self.fonts,
                current_time,
            )

        draw_act_two_death_dialogue_overlay(
            surface,
            game_state,
            self.fonts,
            current_time,
            camera,
        )
        draw_oracle_intro(
            surface,
            oracle_world_frame,
            floor,
            self.oracle_ui_layout,
            self.oracle_ui_assets,
        )
        draw_oracle_phase_transition(surface, oracle_world_frame, floor)
        draw_oracle_death_overlay(
            surface,
            oracle_world_frame,
            floor,
            mouse_position,
        )


__all__ = ["ActTwoInterface"]
