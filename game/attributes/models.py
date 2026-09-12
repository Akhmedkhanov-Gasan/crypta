from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerBaseStats:
    max_health: int
    damage_min: int
    damage_max: int
    crit_chance: float = 0.0
    dodge_chance: float = 0.0
    critical_damage_multiplier: float = 2.0


@dataclass(frozen=True)
class PlayerStatChanges:
    max_health: int = 0
    damage_min: int = 0
    damage_max: int = 0
    crit_chance: float = 0.0
    dodge_chance: float = 0.0
    critical_damage_multiplier: float = 0.0
