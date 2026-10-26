from dataclasses import dataclass

import pygame

from game.state import GameState

from acts.act_two.consumables import (
    FIRE_BOMB,
    TARGETED_SCROLLS,
    cancel_fire_bomb_aiming,
    cancel_scroll_aiming,
    get_act_two_consumable_slots,
    request_fire_bomb_aiming,
    request_scroll_aiming,
)
from acts.act_two.controls import CONSUMABLE_KEYS


@dataclass(frozen=True)
class ActTwoActionRequest:
    selected_consumable: str | None
    consumable_slot: int | None
    fire_bomb_target: tuple[int, int] | None
    fire_bomb_slot: int | None
    scroll_target: tuple[int, int] | None
    scroll_slot: int | None
    mage_ability_target: tuple[int, int] | None
    resonance_target: tuple[int, int] | None
    dropped_consumable_slot: int | None
    dropped_consumable_target: tuple[int, int] | None
    dropped_consumable_started_at: int

    @classmethod
    def from_event(cls, event, game_state: GameState, enabled: bool):
        consumable_slot = CONSUMABLE_KEYS.get(event.key) if enabled else None
        consumable_slots = get_act_two_consumable_slots(game_state.player)
        return cls(
            selected_consumable=(
                consumable_slots[consumable_slot]
                if consumable_slot is not None
                else None
            ),
            consumable_slot=consumable_slot,
            fire_bomb_target=getattr(event, "fire_bomb_target", None),
            fire_bomb_slot=getattr(event, "fire_bomb_slot", None),
            scroll_target=getattr(event, "scroll_target", None),
            scroll_slot=getattr(event, "scroll_slot", None),
            mage_ability_target=getattr(event, "mage_ability_target", None),
            resonance_target=getattr(event, "resonance_target", None),
            dropped_consumable_slot=getattr(
                event,
                "dropped_consumable_slot",
                None,
            ),
            dropped_consumable_target=getattr(
                event,
                "dropped_consumable_target",
                None,
            ),
            dropped_consumable_started_at=getattr(
                event,
                "dropped_consumable_started_at",
                0,
            ),
        )

    def handle_aiming(self, event, game_state: GameState, input_state) -> bool:
        player = game_state.player
        if player.act_two.fire_bomb_aiming and self.fire_bomb_target is None:
            if event.key == pygame.K_ESCAPE or self.selected_consumable == FIRE_BOMB:
                cancel_fire_bomb_aiming(game_state)
            return True
        if self.selected_consumable == FIRE_BOMB:
            input_state.reset_held_movement()
            request_fire_bomb_aiming(game_state, self.consumable_slot)
            return True
        if player.act_two.scroll_aiming_kind is not None and self.scroll_target is None:
            if (
                event.key == pygame.K_ESCAPE
                or self.selected_consumable in TARGETED_SCROLLS
            ):
                cancel_scroll_aiming(game_state)
            return True
        if self.selected_consumable in TARGETED_SCROLLS:
            input_state.reset_held_movement()
            request_scroll_aiming(game_state, self.consumable_slot)
            return True
        return False


__all__ = ["ActTwoActionRequest"]
