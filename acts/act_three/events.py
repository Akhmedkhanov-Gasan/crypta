"""Event boundary for the Act Three runtime.

The aliases preserve the current event protocol while allowing Act Three to
replace or extend it without changing the classic runtime.
"""

from game.events import GameEvent, GameEventType, Position


__all__ = [
    "GameEvent",
    "GameEventType",
    "Position",
]
