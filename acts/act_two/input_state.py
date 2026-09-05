from dataclasses import dataclass

from application.movement_state import MovementInputState


@dataclass
class ActTwoInputRuntimeState(MovementInputState):
    dragged_consumable_slot: int | None = None
    resonance_cursor_active: bool = False

    def cancel_consumable_drag(self):
        self.dragged_consumable_slot = None

    def reset_for_loading(self):
        self.reset_held_movement()
        self.reset_auto_move()
        self.cancel_consumable_drag()
        self.movement_input_locked_until = 0
