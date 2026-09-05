from dataclasses import dataclass, field


@dataclass
class MovementInputState:
    held_movement_keys: set[int] = field(default_factory=set)
    held_direction: tuple[int, int] = (0, 0)
    pending_movement_direction: tuple[int, int] | None = None
    pending_movement_at: int = 0
    next_held_move_at: int = 0
    movement_input_locked_until: int = 0
    auto_move_target: tuple[int, int] | None = None
    auto_move_enemy: object | None = None
    auto_move_revision: int = 0
    auto_move_floor_index: int | None = None
    auto_move_acknowledged_warnings: tuple[object, ...] = ()
    next_auto_move_at: int = 0

    def reset_held_movement(self):
        self.held_movement_keys.clear()
        self.held_direction = (0, 0)
        self.pending_movement_direction = None
        self.pending_movement_at = 0
        self.next_held_move_at = 0

    def cancel_auto_move(self):
        self.auto_move_target = None
        self.auto_move_enemy = None
        self.auto_move_floor_index = None
        self.auto_move_acknowledged_warnings = ()
        self.auto_move_revision += 1

    def reset_auto_move(self):
        self.cancel_auto_move()
        self.next_auto_move_at = 0