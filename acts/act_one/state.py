from dataclasses import dataclass, fields
from typing import Any


@dataclass
class ActOnePlayerState:
    act_one_attack_target: tuple[int, int] | None = None
    act_one_attack_was_critical: bool = False
    act_one_movement_origin: tuple[int, int] | None = None
    act_one_wait_effect_started_at: int = -1
    act_one_dodge_started_at: int = -1
    act_one_dodge_origin: tuple[int, int] | None = None
    act_one_pickup_kind: str | None = None
    act_one_pickup_origin: tuple[int, int] | None = None
    act_one_pickup_started_at: int = -1


@dataclass
class ActOneSessionState:
    act_one_intro: Any | None = None
    act_one_death_scene: Any | None = None
    act_one_upgrades_remaining: int = 0


@dataclass
class ActOneIntroState:
    column: int
    row: int
    elapsed: int = 0
    finished: bool = False
    skip_held_ms: int = 0
    updated_at: int = -1


@dataclass
class ActOneWardenIntroState:
    elapsed: int = 0
    started: bool = False
    finished: bool = False
    skip_held_ms: int = 0
    updated_at: int = -1


ACT_ONE_PLAYER_FIELD_NAMES = frozenset(
    state_field.name
    for state_field in fields(ActOnePlayerState)
)
ACT_ONE_SESSION_FIELD_NAMES = frozenset(
    state_field.name
    for state_field in fields(ActOneSessionState)
)


__all__ = [
    "ACT_ONE_PLAYER_FIELD_NAMES",
    "ACT_ONE_SESSION_FIELD_NAMES",
    "ActOneIntroState",
    "ActOnePlayerState",
    "ActOneSessionState",
    "ActOneWardenIntroState",
]
