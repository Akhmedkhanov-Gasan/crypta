from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


Position = tuple[int, int]


class GameEventType(Enum):
    MOVE = auto()
    ATTACK = auto()
    HIT = auto()
    HEAL = auto()
    DEATH = auto()


@dataclass(frozen=True)
class GameEvent:
    type: GameEventType
    actor: str
    target: str | None = None
    origin: Position | None = None
    destination: Position | None = None
    positions: tuple[Position, ...] = ()
    amount: int | None = None
    data: dict[str, Any] = field(default_factory=dict)
