from dataclasses import dataclass


@dataclass
class SentinelState:
    shield_raised: bool = False
    shield_broken: bool = False
    recovery_turns: int = 0
    bash_direction: tuple[int, int] = (0, 0)


@dataclass
class ForcedMovementState:
    origin: tuple[int, int] = (0, 0)
    destination: tuple[int, int] = (0, 0)
    direction: tuple[int, int] = (0, 0)
    collided: bool = False
    started_at: int = -1
