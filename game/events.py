from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


Position = tuple[int, int]


class GameEventType(Enum):
    MOVE = auto()
    ATTACK = auto()
    ABILITY = auto()
    PREPARE_ATTACK = auto()
    PREPARE_HEAL = auto()
    HIT = auto()
    DODGE = auto()
    HEAL = auto()
    DEATH = auto()
    PICKUP = auto()
    CHEST_OPEN = auto()
    ENVIRONMENT = auto()
    LEVEL_UP = auto()
    PREPARE_SUMMON = auto()
    SUMMON = auto()


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
