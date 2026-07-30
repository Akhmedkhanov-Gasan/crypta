from dataclasses import dataclass, field, fields
from enum import Enum, auto
from typing import Any, Iterator

from acts.act_three.state import (
    ACT_THREE_PLAYER_FIELD_NAMES,
    ACT_THREE_SESSION_FIELD_NAMES,
    ActThreePlayerState,
    ActThreeSessionState,
    ArcherBarrageShotState,
)
from game.events import GameEvent


class EnemyBehaviorState(Enum):
    INACTIVE = auto()
    IDLE = auto()
    CHASING = auto()
    PREPARING_ATTACK = auto()
    PREPARING_HEAL = auto()
    GUARDING = auto()
    DEAD = auto()


class AttributeMapping:
    """Temporary mapping compatibility for incremental state migration."""

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __iter__(self) -> Iterator[str]:
        return (field.name for field in fields(self))

    def __len__(self) -> int:
        return len(fields(self))

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


@dataclass(eq=False)
class RoomState(AttributeMapping):
    x: int
    y: int
    width: int
    height: int

    @classmethod
    def from_mapping(cls, room: dict) -> "RoomState":
        return cls(
            x=room["x"],
            y=room["y"],
            width=room["width"],
            height=room["height"],
        )


@dataclass(eq=False)
class ChestState(AttributeMapping):
    column: int
    row: int
    contains: str
    is_open: bool = False
    loot_available: bool = False


@dataclass(eq=False)
class PotionState(AttributeMapping):
    column: int
    row: int


@dataclass(eq=False)
class ProjectileState(AttributeMapping):
    column: int
    row: int
    state: str
    kind: str
    direction: tuple[int, int]
    damage: int


@dataclass(eq=False)
class EnemyState(AttributeMapping):
    type: str
    column: int
    row: int
    health: int
    max_health: int
    name: str
    aggro_radius: int
    wander_chance: float
    move_every: int
    attack_kind: str
    attack_range: int
    damage_by_mode: dict
    color: tuple[int, int, int]
    sleeping_color: tuple[int, int, int]
    retreat_jump_chance: float
    phase_two_damage_by_mode: dict | None = None
    behavior_state: EnemyBehaviorState = EnemyBehaviorState.IDLE
    is_aggro: bool = False
    has_key: bool = False
    attack_targets: list[tuple[int, int]] = field(
        default_factory=list
    )
    move_counter: int = 0
    is_immobile: bool = False
    footprint_width: int = 1
    footprint_height: int = 1
    projectile_cooldown: int = 0
    projectile_cooldown_duration: int = 0
    last_oracle_action: str | None = None
    last_straight_pattern: str | None = None
    oracle_awakened: bool = False
    phase_transition_pending: bool = False
    prepared_attack_mode: str | None = None
    prepared_attack_target: str = "hero"
    selected_attack_mode: str | None = None
    last_attack_mode: str | None = None
    second_phase_announced: bool = False
    boss_group: bool = False
    is_active: bool = True
    shield_turns: int = 0
    shield_direction: tuple[int, int] | None = None
    shield_cooldown: int = 0
    shield_duration: int = 0
    shield_cooldown_duration: int = 0
    heal_target: "EnemyState | None" = None
    heal_cooldown: int = 0
    heal_amount: int = 0
    heal_cooldown_duration: int = 0
    heal_range: int = 0
    curse_turns: int = 0
    movement_animation_started_at: int = 0
    attack_animation_started_at: int = 0
    movement_bounds: tuple[int, int, int, int] | None = None

    @classmethod
    def from_config(
        cls,
        enemy_type: str,
        column: int,
        row: int,
        name: str,
        config: dict,
        belongs_to_boss_group: bool,
    ) -> "EnemyState":
        maximum_health = config["max_health"]

        return cls(
            type=enemy_type,
            column=column,
            row=row,
            health=maximum_health,
            max_health=maximum_health,
            name=name,
            aggro_radius=config["aggro_radius"],
            wander_chance=config["wander_chance"],
            move_every=config["move_every"],
            attack_kind=config["attack_kind"],
            attack_range=config["attack_range"],
            damage_by_mode=config["damage_by_mode"],
            phase_two_damage_by_mode=config.get(
                "phase_two_damage_by_mode"
            ),
            color=config["color"],
            sleeping_color=config["sleeping_color"],
            retreat_jump_chance=config["retreat_jump_chance"],
            behavior_state=(
                EnemyBehaviorState.INACTIVE
                if belongs_to_boss_group
                else EnemyBehaviorState.IDLE
            ),
            is_immobile=config.get("is_immobile", False),
            footprint_width=config.get("footprint_width", 1),
            footprint_height=config.get("footprint_height", 1),
            projectile_cooldown_duration=config.get(
                "projectile_cooldown",
                0,
            ),
            boss_group=belongs_to_boss_group,
            is_active=not belongs_to_boss_group,
            shield_duration=config.get("shield_duration", 0),
            shield_cooldown_duration=config.get(
                "shield_cooldown",
                0,
            ),
            heal_amount=config.get("heal_amount", 0),
            heal_cooldown_duration=config.get(
                "heal_cooldown",
                0,
            ),
            heal_range=config.get("heal_range", 0),
        )


@dataclass(eq=False)
class FloorState(AttributeMapping):
    map: list[str]
    player_column: int
    player_row: int
    enemies: list[EnemyState]
    chests: list[ChestState]
    potions: list[PotionState]
    stairs_column: int
    stairs_row: int
    boss_door: tuple[int, int] | None
    boss_room: RoomState | None
    boss_columns: list[tuple[int, int]]
    boss_emitters: list[tuple[int, int]]
    seal_boss_door_during_fight: bool
    boss_fight_started: bool
    torches: list[tuple[int, int]] = field(
        default_factory=list
    )
    visual_seed: int = 0
    dropped_keys: list[tuple[int, int]] = field(
        default_factory=list
    )
    projectiles: list[ProjectileState] = field(
        default_factory=list
    )
    explored_cells: set[tuple[int, int]] = field(
        default_factory=set
    )
    visible_cells: set[tuple[int, int]] = field(
        default_factory=set
    )


@dataclass
class PlayerState:
    max_health: int
    health: int
    damage_min: int
    damage_max: int
    crit_chance: float = 0.0
    dodge_chance: float = 0.0
    player_class: str | None = None
    subclass: str | None = None
    potion_count: int = 0
    gold_count: int = 0
    key_count: int = 0
    enemies_defeated: int = 0
    ability_kill_charge: int = 0
    invisibility_turns: int = 0
    directional_ability_aiming: bool = False
    act_three: ActThreePlayerState = field(
        default_factory=ActThreePlayerState,
    )

    def __getattr__(self, name: str) -> Any:
        if name in ACT_THREE_PLAYER_FIELD_NAMES:
            return getattr(self.act_three, name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        act_three_state = self.__dict__.get("act_three")
        if (
            act_three_state is not None
            and name in ACT_THREE_PLAYER_FIELD_NAMES
        ):
            setattr(act_three_state, name, value)
            return
        object.__setattr__(self, name, value)

@dataclass
class GameState:
    floor_index: int
    floor: FloorState
    player: PlayerState
    combat_log: list[str]
    game_won: bool = False
    upgrade_screen_open: bool = False
    class_selection_open: bool = False
    class_transition_started_at: int = 0
    upgrade_message: str = ""
    player_attack_targets: list[tuple[int, int]] = field(
        default_factory=list
    )
    events: list[GameEvent] = field(default_factory=list)
    act_three: ActThreeSessionState = field(
        default_factory=ActThreeSessionState,
    )

    def __getattr__(self, name: str) -> Any:
        if name in ACT_THREE_SESSION_FIELD_NAMES:
            return getattr(self.act_three, name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        act_three_state = self.__dict__.get("act_three")
        if (
            act_three_state is not None
            and name in ACT_THREE_SESSION_FIELD_NAMES
        ):
            setattr(act_three_state, name, value)
            return
        object.__setattr__(self, name, value)

    def emit(self, event: GameEvent) -> None:
        self.events.append(event)

    def clear_events(self) -> None:
        self.events.clear()


__all__ = [
    "ArcherBarrageShotState",
    "AttributeMapping",
    "ChestState",
    "EnemyBehaviorState",
    "EnemyState",
    "FloorState",
    "GameState",
    "PlayerState",
    "PotionState",
    "ProjectileState",
    "RoomState",
]
