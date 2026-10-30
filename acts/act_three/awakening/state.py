from dataclasses import dataclass


@dataclass
class AwakeningScene:
    phase: str = "farewell"
    elapsed: int = 0
    updated_at: int = 0
    old_man_position: tuple[int, int] = (0, 0)
    boss_position: tuple[int, int] = (0, 0)
    logged_lines: int = 0
    world_swapped: bool = False
    paused: bool = False
    debug_reveal: bool = False

