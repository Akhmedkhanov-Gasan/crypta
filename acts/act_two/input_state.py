"""Ephemeral input state for the running Act Two scene."""

from dataclasses import dataclass, field


@dataclass
class ActTwoInputRuntimeState:
    held_movement_keys: set[int] = field(default_factory=set)
    held_direction: tuple[int, int] = (0, 0)
    next_held_move_at: int = 0
    movement_input_locked_until: int = 0
    auto_move_target: tuple[int, int] | None = None
    auto_move_floor_index: int | None = None
    next_auto_move_at: int = 0
    dragged_consumable_slot: int | None = None
    resonance_cursor_active: bool = False

    def reset_held_movement(self):
        self.held_movement_keys.clear()
        self.held_direction = (0, 0)
        self.next_held_move_at = 0

    def cancel_auto_move(self):
        self.auto_move_target = None
        self.auto_move_floor_index = None

    def reset_auto_move(self):
        self.cancel_auto_move()
        self.next_auto_move_at = 0

    def cancel_consumable_drag(self):
        self.dragged_consumable_slot = None

    def reset_for_loading(self):
        self.reset_held_movement()
        self.reset_auto_move()
        self.cancel_consumable_drag()
        self.movement_input_locked_until = 0
