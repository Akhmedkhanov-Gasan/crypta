import pygame

from application.directional_input import movement_direction_for_key
from application.movement_input import movement_input_is_locked
from acts.ground_items import (
    collect_ground_gold,
    ground_item_act_input_available,
    ground_item_rules,
    ground_items_at_player,
    pick_up_ground_item,
    play_ground_item_events,
    prepare_ground_item_pickup,
)
from presentation.ground_items import ground_item_window_layout
from game.combat_log import add_log_message


def ground_item_input_available(game_state):
    player = game_state.player

    return (
        game_state.floor.presentation_act in (1, 2, 3)
        and player.health > 0
        and not game_state.game_won
        and game_state.floor_transition_started_at < 0
        and not game_state.class_selection_open
        and not game_state.upgrade_screen_open
        and not game_state.rune_selection_open
        and not game_state.bloody_altar_open
        and not game_state.trade_screen_open
        and not game_state.subclass_selection_open
        and not game_state.act_three_transition_open
        and not game_state.act_three_debug_class_selection_open
        and not game_state.upgrade_altar_menu_open
        and not player.directional_ability_aiming
        and not player.act_two.fire_bomb_aiming
        and player.act_two.scroll_aiming_kind is None
        and not player.teleport_aiming
        and not player.ultimate_aiming
        and not player.ultimate_animation_active
        and not player.archer_empowered_shot_aiming
        and not player.archer_leap_aiming
        and not player.archer_barrage_zone_aiming
        and not player.berserker_crushing_leap_aiming
        and not player.paladin_shield_charge_aiming
        and not player.warlock_curse_aiming
        and not player.warlock_soul_exchange_aiming
        and ground_item_act_input_available(game_state)
    )


class GroundItemInput:
    def __init__(self):
        self.is_open = False
        self.selected = 0
        self.floor = None
        self.seen_position = None

    def close(self):
        self.is_open = False
        self.selected = 0

    def _open(self, movement_state):
        self.is_open = True
        self.selected = 0
        movement_state.reset_held_movement()
        movement_state.cancel_auto_move()
        movement_state.cancel_consumable_drag()

    def update(
        self,
        game_state,
        movement_state,
        enabled,
        current_time,
        sounds=None,
    ):
        if not enabled or not ground_item_input_available(game_state):
            self.close()
            self.floor = None
            self.seen_position = None
            return False

        event_start = len(game_state.events)
        collect_ground_gold(game_state, current_time)
        play_ground_item_events(
            game_state,
            game_state.events[event_start:],
            sounds,
        )

        floor = game_state.floor
        if self.floor is not floor:
            self.close()
            self.floor = floor
            self.seen_position = None

        position = (floor.player_column, floor.player_row)
        items = ground_items_at_player(game_state, current_time)

        if position != self.seen_position:
            self.close()

            if movement_input_is_locked(movement_state, current_time):
                return False

            self.seen_position = position

            if len(items) > 1 and ground_item_rules(game_state).use_window:
                self._open(movement_state)
                return True

        if self.is_open:
            if not items:
                self.close()
            else:
                self.selected = min(self.selected, len(items) - 1)

        return False

    def _take(
        self,
        game_state,
        movement_state,
        sounds,
        current_time,
    ):
        if movement_input_is_locked(movement_state, current_time):
            return

        prepare_ground_item_pickup(
            game_state,
            current_time,
            sounds,
        )
        if not ground_item_input_available(game_state):
            self.close()
            return

        items = ground_items_at_player(game_state, current_time)
        if not items:
            self.close()
            return

        self.selected = min(self.selected, len(items) - 1)
        event_start = len(game_state.events)

        pick_up_ground_item(
            game_state,
            items[self.selected],
            current_time,
        )

        play_ground_item_events(
            game_state,
            game_state.events[event_start:],
            sounds,
        )

        remaining = ground_items_at_player(game_state, current_time)
        if not remaining:
            self.close()
        else:
            self.selected = min(self.selected, len(remaining) - 1)

    def handle_event(
        self,
        event,
        game_state,
        movement_state,
        sounds,
        mouse_position,
        surface_size,
        enabled,
        current_time,
    ):
        if event.type not in (
            pygame.KEYDOWN,
            pygame.KEYUP,
            pygame.MOUSEMOTION,
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEWHEEL,
        ):
            return False

        opened_now = self.update(
            game_state,
            movement_state,
            enabled,
            current_time,
            sounds,
        )

        if not enabled or not ground_item_input_available(game_state):
            return False

        if opened_now:
            return True

        if not self.is_open:
            if not (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_g
            ):
                return False

            if movement_input_is_locked(movement_state, current_time):
                return True

            items = ground_items_at_player(game_state, current_time)
            if not items:
                add_log_message(
                    game_state.combat_log,
                    "There is nothing to pick up here.",
                    category="neutral",
                )
                return True

            movement_state.reset_held_movement()
            movement_state.cancel_auto_move()
            movement_state.cancel_consumable_drag()

            if (
                len(items) == 1
                or not ground_item_rules(game_state).use_window
            ):
                self.selected = 0
                self._take(
                    game_state,
                    movement_state,
                    sounds,
                    current_time,
                )
            else:
                self._open(movement_state)

            return True

        items = ground_items_at_player(game_state, current_time)
        if not items:
            self.close()
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
            elif getattr(event, "movement_direction", None) is not None:
                return True
            elif event.key in (
                pygame.K_g,
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
            ):
                if not getattr(event, "repeat", False):
                    self._take(
                        game_state,
                        movement_state,
                        sounds,
                        current_time,
                    )
            else:
                direction = movement_direction_for_key(event.key)
                if direction is not None:
                    change = direction[1] or direction[0]
                    self.selected = (
                        self.selected + change
                    ) % len(items)

        elif event.type == pygame.MOUSEWHEEL:
            self.selected = max(
                0,
                min(self.selected - event.y, len(items) - 1),
            )

        elif event.type in (
            pygame.MOUSEMOTION,
            pygame.MOUSEBUTTONDOWN,
        ):
            panel, close_button, rows = ground_item_window_layout(
                surface_size,
                len(items),
                self.selected,
            )

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):
                if (
                    close_button.collidepoint(mouse_position)
                    or not panel.collidepoint(mouse_position)
                ):
                    self.close()
                    return True

            for index, rect in rows:
                if not rect.collidepoint(mouse_position):
                    continue

                self.selected = index
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                ):
                    self._take(
                        game_state,
                        movement_state,
                        sounds,
                        current_time,
                    )
                break

        return True
