from dataclasses import dataclass


@dataclass
class ActOneIntroState:
    column: int
    row: int
    elapsed: int = 0
    finished: bool = False
    skip_held_ms: int = 0
    updated_at: int = -1


__all__ = ["ActOneIntroState"]
