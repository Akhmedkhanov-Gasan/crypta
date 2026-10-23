import pygame

from game.state import GameState

from acts.act_two.consumables import (
    cancel_fire_bomb_aiming,
    cancel_scroll_aiming,
)
from acts.act_two.controls import CONSUMABLE_KEY_ORDER
from acts.act_two.presentation.bloody_altar import handle_bloody_altar_event
from acts.act_two.presentation.camera import act_two_screen_to_cell
from acts.act_two.presentation.hud import (
    get_act_two_attribute_minus_rectangles,
    get_act_two_attribute_plus_rectangles,
    get_act_two_belt_slot_rectangles,
    get_act_two_confirm_button_rectangle,
    get_act_two_journal_close_rectangle,
    get_act_two_journal_scrollbar_rectangles,
    get_act_two_journal_viewport_rectangle,
    get_act_two_sidebar_button_rectangles,
)
from acts.act_two.presentation.rune_selection import (
    get_rune_selection_card_rectangles,
    get_rune_selection_confirm_rectangle,
)
from acts.act_two.presentation.trade_window import (
    get_act_two_trade_buy_rectangles,
    get_act_two_trade_close_rectangle,
)
from acts.act_two.progression import (
    cancel_queued_act_two_attribute_upgrade,
    confirm_queued_act_two_attribute_upgrades,
    queue_act_two_attribute_upgrade,
)
from acts.act_two.runes import cancel_rune_selection, select_rune
from acts.act_two.trader_logic import buy_trader_item
from game.combat_log import add_log_message
from game.rune_catalog import runes_for_class


class ActTwoInterfaceInput:
    def __init__(self, hud_layout, trade_layout, bloody_altar_layout):
        self.hud_layout = hud_layout
        self.trade_layout = trade_layout
        self.bloody_altar_layout = bloody_altar_layout

    def _handle_trade(self, event, game_state, input_state, sounds, mouse_position):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            game_state.trade_screen_open = False
            input_state.reset_held_movement()
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and mouse_position is not None
        ):
            if get_act_two_trade_close_rectangle(self.trade_layout).collidepoint(
                mouse_position
            ):
                game_state.trade_screen_open = False
                input_state.reset_held_movement()
            else:
                clicked_slot = next(
                    (
                        slot_name
                        for slot_name, rectangle in get_act_two_trade_buy_rectangles(
                            self.trade_layout
                        ).items()
                        if rectangle.collidepoint(mouse_position)
                    ),
                    None,
                )
                if clicked_slot is not None and buy_trader_item(
                    game_state,
                    clicked_slot,
                ):
                    sounds.play_ui_sound("gold_pickup")
        return True

    @staticmethod
    def _handle_rune_selection(event, game_state, mouse_position):
        available_runes = runes_for_class(game_state.player.player_class)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                cancel_rune_selection(game_state)
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                rune_index = event.key - pygame.K_1
                if rune_index < len(available_runes):
                    game_state.rune_selection_pending_id = available_runes[rune_index].id
            elif (
                event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
                and game_state.rune_selection_pending_id is not None
            ):
                select_rune(game_state, game_state.rune_selection_pending_id)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            cancel_rune_selection(game_state)
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and mouse_position is not None
        ):
            clicked_rune_id = next(
                (
                    rune_id
                    for rune_id, rectangle in get_rune_selection_card_rectangles(
                        game_state.player.player_class
                    ).items()
                    if rectangle.collidepoint(mouse_position)
                ),
                None,
            )
            if clicked_rune_id is not None:
                game_state.rune_selection_pending_id = clicked_rune_id
            elif (
                game_state.rune_selection_pending_id is not None
                and get_rune_selection_confirm_rectangle(
                    game_state.player.player_class
                ).collidepoint(mouse_position)
            ):
                select_rune(game_state, game_state.rune_selection_pending_id)
        return True

    def _handle_stats(self, event, game_state, mouse_position):
        if not (
            game_state.act_two_stats_open
            and not game_state.class_selection_open
            and not game_state.upgrade_screen_open
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and mouse_position is not None
        ):
            return False

        if get_act_two_confirm_button_rectangle(self.hud_layout).collidepoint(
            mouse_position
        ):
            confirmed, message = confirm_queued_act_two_attribute_upgrades(
                game_state.player
            )
            if confirmed:
                add_log_message(
                    game_state.combat_log,
                    message,
                    category="progress",
                )
            return True

        minus_attribute = next(
            (
                attribute
                for attribute, rectangle in get_act_two_attribute_minus_rectangles(
                    self.hud_layout
                ).items()
                if rectangle.collidepoint(mouse_position)
            ),
            None,
        )
        if minus_attribute is not None:
            cancel_queued_act_two_attribute_upgrade(
                game_state.player,
                minus_attribute,
            )
            return True

        plus_attribute = next(
            (
                attribute
                for attribute, rectangle in get_act_two_attribute_plus_rectangles(
                    self.hud_layout
                ).items()
                if rectangle.collidepoint(mouse_position)
            ),
            None,
        )
        if plus_attribute is not None:
            queue_act_two_attribute_upgrade(game_state.player, plus_attribute)
            return True
        return False

    def _handle_dragged_consumable(
        self,
        event,
        game_state,
        camera,
        input_state,
        mouse_position,
    ):
        if not (
            event.type == pygame.MOUSEBUTTONUP
            and event.button == 1
            and input_state.dragged_consumable_slot is not None
        ):
            return False

        dragged_slot = input_state.dragged_consumable_slot
        input_state.cancel_consumable_drag()
        released_belt_slot = None
        if mouse_position is not None:
            released_belt_slot = next(
                (
                    slot_index
                    for slot_index, rectangle in enumerate(
                        get_act_two_belt_slot_rectangles(self.hud_layout)
                    )
                    if rectangle.collidepoint(mouse_position)
                ),
                None,
            )
        if released_belt_slot is not None:
            if released_belt_slot == dragged_slot:
                pygame.event.post(
                    pygame.event.Event(
                        pygame.KEYDOWN,
                        key=CONSUMABLE_KEY_ORDER[dragged_slot],
                    )
                )
            else:
                slots = game_state.player.act_two.consumable_slots
                slots[dragged_slot], slots[released_belt_slot] = (
                    slots[released_belt_slot],
                    slots[dragged_slot],
                )
            return True

        target_cell = (
            act_two_screen_to_cell(mouse_position, camera)
            if mouse_position is not None
            else None
        )
        if target_cell is not None:
            pygame.event.post(
                pygame.event.Event(
                    pygame.KEYDOWN,
                    key=pygame.K_UNKNOWN,
                    dropped_consumable_slot=dragged_slot,
                    dropped_consumable_target=target_cell,
                    dropped_consumable_started_at=pygame.time.get_ticks(),
                )
            )
        return True

    def _handle_sidebar(self, event, game_state, mouse_position):
        if not (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and not game_state.class_selection_open
            and not game_state.upgrade_screen_open
            and mouse_position is not None
        ):
            return False
        clicked_button = next(
            (
                button_name
                for button_name, rectangle in get_act_two_sidebar_button_rectangles(
                    self.hud_layout
                ).items()
                if rectangle.collidepoint(mouse_position)
            ),
            None,
        )
        if clicked_button == "stats":
            game_state.act_two_stats_open = not game_state.act_two_stats_open
            game_state.act_two_journal_open = False
            return True
        if clicked_button == "journal":
            game_state.act_two_journal_open = not game_state.act_two_journal_open
            if game_state.act_two_journal_open:
                game_state.act_two_journal_scroll = 1.0
            game_state.act_two_stats_open = False
            return True
        if clicked_button == "settings":
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
            return True
        return False

    def _handle_journal(self, event, game_state, mouse_position):
        if (
            event.type == pygame.MOUSEWHEEL
            and game_state.act_two_journal_open
            and mouse_position is not None
            and get_act_two_journal_viewport_rectangle(self.hud_layout).collidepoint(
                mouse_position
            )
        ):
            game_state.act_two_journal_scroll = max(
                0.0,
                min(1.0, game_state.act_two_journal_scroll - event.y * 0.08),
            )
            return True

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and game_state.act_two_journal_open
            and mouse_position is not None
        ):
            scrollbar_rectangles = get_act_two_journal_scrollbar_rectangles(
                self.hud_layout,
                game_state.act_two_journal_scroll,
            )
            thumb_rectangle = scrollbar_rectangles[1]
            if thumb_rectangle.collidepoint(mouse_position):
                game_state.act_two_journal_dragging = True
                game_state.act_two_journal_drag_offset = (
                    mouse_position[1] - thumb_rectangle.y
                )
                return True
            if get_act_two_journal_close_rectangle(self.hud_layout).collidepoint(
                mouse_position
            ):
                game_state.act_two_journal_open = False
                game_state.act_two_journal_dragging = False
                return True

        if (
            event.type == pygame.MOUSEMOTION
            and game_state.act_two_journal_open
            and game_state.act_two_journal_dragging
            and mouse_position is not None
        ):
            track_rectangle, thumb_rectangle = (
                get_act_two_journal_scrollbar_rectangles(
                    self.hud_layout,
                    game_state.act_two_journal_scroll,
                )
            )
            thumb_travel = max(
                0,
                track_rectangle.height - thumb_rectangle.height,
            )
            desired_thumb_y = (
                mouse_position[1] - game_state.act_two_journal_drag_offset
            )
            clamped_thumb_y = max(
                track_rectangle.top,
                min(
                    track_rectangle.bottom - thumb_rectangle.height,
                    desired_thumb_y,
                ),
            )
            game_state.act_two_journal_scroll = (
                (clamped_thumb_y - track_rectangle.top) / thumb_travel
                if thumb_travel > 0
                else 0.0
            )
            return True

        if (
            event.type == pygame.MOUSEBUTTONUP
            and event.button == 1
            and game_state.act_two_journal_dragging
        ):
            game_state.act_two_journal_dragging = False
            return True
        return False

    def _handle_belt(self, event, game_state, input_state, mouse_position):
        if not (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and not game_state.class_selection_open
            and not game_state.upgrade_screen_open
            and game_state.player.health > 0
            and mouse_position is not None
        ):
            return False
        for slot_index, rectangle in enumerate(
            get_act_two_belt_slot_rectangles(self.hud_layout)
        ):
            if not rectangle.collidepoint(mouse_position):
                continue
            if game_state.player.act_two.consumable_slots[slot_index] is not None:
                cancel_fire_bomb_aiming(game_state)
                cancel_scroll_aiming(game_state)
                input_state.dragged_consumable_slot = slot_index
            return True
        return False

    def handle_event(
        self,
        event,
        game_state: GameState,
        camera,
        input_state,
        sounds,
        mouse_position,
    ):
        if game_state.bloody_altar_open:
            handle_bloody_altar_event(
                event,
                game_state,
                self.bloody_altar_layout,
                mouse_position,
            )
            input_state.reset_held_movement()
            return True
        if game_state.trade_screen_open:
            return self._handle_trade(
                event,
                game_state,
                input_state,
                sounds,
                mouse_position,
            )
        if game_state.rune_selection_open:
            return self._handle_rune_selection(event, game_state, mouse_position)
        return (
            self._handle_stats(event, game_state, mouse_position)
            or self._handle_dragged_consumable(
                event,
                game_state,
                camera,
                input_state,
                mouse_position,
            )
            or self._handle_sidebar(event, game_state, mouse_position)
            or self._handle_journal(event, game_state, mouse_position)
            or self._handle_belt(event, game_state, input_state, mouse_position)
        )


__all__ = ["ActTwoInterfaceInput"]
