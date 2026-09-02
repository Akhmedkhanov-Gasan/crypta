from dataclasses import dataclass, field, fields
from enum import Enum, auto
from typing import Any, Iterator

from acts.act_two.state import (
    ActOneRevisitState,
    ActTwoPlayerState,
    BloodyAltarState,
    BreakableCrateState,
    DroppedConsumableState,
    FireZoneState,
    RuneRoomState,
    SpikeTrapPhase,
    SpikeTrapState,
    TreasuryRoomState,
    TraderState,
    BruteAftershockState,
)
from acts.act_two.quests import ActTwoQuestState
from acts.act_three.state import (
    ACT_THREE_PLAYER_FIELD_NAMES,
    ACT_THREE_SESSION_FIELD_NAMES,
    ActThreePlayerState,
    ActThreeSessionState,
    ArcherBarrageShotState,
)
from game.events import GameEvent, GameEventType


class EnemyBehaviorState(Enum):
    INACTIVE = auto()
    IDLE = auto()
    CHASING = auto()
    PREPARING_ATTACK = auto()
    PREPARING_HEAL = auto()
    GUARDING = auto()
    DEAD = auto()
    PREPARING_SUMMON = auto()


class AttributeMapping:
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
    open_animation_started_at: int = -1
    requires_key: bool = True
    appearance: str = "standard"


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
    dodge_chance: float = 0.0
    behavior_state: EnemyBehaviorState = EnemyBehaviorState.IDLE
    is_aggro: bool = False
    has_key: bool = False
    attack_targets: list[tuple[int, int]] = field(
        default_factory=list
    )
    attack_telegraph_visible_at: int = 0
    move_counter: int = 0
    is_immobile: bool = False
    footprint_width: int = 1
    footprint_height: int = 1
    projectile_cooldown: int = 0
    projectile_cooldown_duration: int = 0
    last_oracle_action: str | None = None
    last_straight_pattern: str | None = None
    oracle_phase: int = 1
    oracle_base_column: int | None = None
    oracle_base_row: int | None = None
    oracle_phase_elapsed: int = 0
    oracle_phase_detached: bool = False
    oracle_render_column: float | None = None
    oracle_render_row: float | None = None
    oracle_phase_two_eye: str = "idle"
    oracle_phase_two_opening_attack_pending: bool = False
    oracle_death_started_at: int = -1
    oracle_death_elapsed: int = 0
    oracle_awakened: bool = False
    oracle_eye_progress: float = 0.0
    oracle_head_angle: float = 0.0
    oracle_cast_amount: float = 0.0
    phase_transition_pending: bool = False
    prepared_attack_mode: str | None = None
    prepared_attack_target: str = "hero"
    attack_windup_turns_remaining: int = 0
    selected_attack_mode: str | None = None
    last_attack_mode: str | None = None
    second_phase_announced: bool = False
    boss_group: bool = False
    is_active: bool = True
    shield_blocks_remaining: int = 0
    shield_durability: int = 0
    shield_cooldown: int = 0
    shield_cooldown_duration: int = 0
    heal_target: "EnemyState | None" = None
    priest_retreat_counter: int = 0
    heal_cooldown: int = 0
    heal_amount: int = 0
    heal_cooldown_duration: int = 0
    heal_range: int = 0
    curse_turns: int = 0
    binding_turns: int = 0
    stun_turns: int = 0
    bleed_turns: int = 0
    bleed_damage: int = 0
    movement_animation_started_at: int = 0
    movement_origin: tuple[int, int] | None = None
    movement_animation_kind: str | None = None
    skip_next_movement: bool = False
    attack_animation_started_at: int = 0
    attack_effect_mode: str | None = None
    attack_effect_positions: tuple[tuple[int, int], ...] = ()
    phase_transition_started_at: int = -1
    hit_animation_started_at: int = -1
    hit_damage: int = 0
    hit_critical: bool = False
    hit_blocked: bool = False
    hit_dodged: bool = False
    hit_origin: tuple[int, int] | None = None
    hit_attacker_class: str | None = None
    aftershock_hit_started_at: int = -1
    aftershock_hit_damage: int = 0
    death_animation_started_at: int = -1
    movement_bounds: tuple[int, int, int, int] | None = None
    warden_attacks_since_reposition: int = 0
    warden_reposition_cooldown: int = 0
    warden_reposition_target: tuple[int, int] | None = None
    defeat_rewards_claimed: bool = False
    treasury_trial_enemy: bool = False
    is_summoned: bool = False
    goblin_summon_used: bool = False
    summon_animation_started_at: int = -1
    summon_spawn_animation_started_at: int = -1
    summon_windup_turns_remaining: int = 0

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
            dodge_chance=config.get("dodge_chance", 0.0),
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
            shield_durability=config.get(
                "shield_durability",
                0,
            ),
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
class PassageState(AttributeMapping):
    passage_id: str
    wall_position: tuple[int, int]
    trigger_position: tuple[int, int]
    target_floor_index: int | None
    target_passage_id: str | None = None
    requires_clear: bool = False
    discovered: bool = False


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
    has_oracle_gate: bool = False
    oracle_gate_opened: bool = False
    oracle_gate_opening_started_at: int = -1
    oracle_intro: Any | None = None
    oracle_combat: Any | None = None
    oracle_phase_transition: Any | None = None
    oracle_phase_two: Any | None = None
    oracle_death: Any | None = None
    passages: list[PassageState] = field(default_factory=list)
    act_one_revisit: ActOneRevisitState | None = None
    upgrade_altar: tuple[int, int] | None = None
    bloody_altar: BloodyAltarState | None = None
    trader: TraderState | None = None
    quest_trader: TraderState | None = None
    breakable_crates: list[BreakableCrateState] = field(
        default_factory=list
    )
    spike_traps: list[SpikeTrapState] = field(
        default_factory=list
    )
    treasury_room: TreasuryRoomState | None = None
    rune_room: RuneRoomState | None = None
    torches: list[tuple[int, int]] = field(
        default_factory=list
    )
    tile_layers: dict[str, list[list[int]]] = field(
        default_factory=dict
    )
    barriers: set[
        tuple[tuple[int, int], tuple[int, int]]
    ] = field(default_factory=set)
    connectors: list[dict[str, Any]] = field(default_factory=list)
    visual_seed: int = 0
    presentation_act: int = 1
    dropped_keys: list[tuple[int, int]] = field(
        default_factory=list
    )
    dropped_gold: list[tuple[int, int]] = field(
        default_factory=list
    )
    dropped_consumables: list[DroppedConsumableState] = field(
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
    act_two_remembered_chests: dict[
        tuple[int, int], dict[str, Any]
    ] = field(default_factory=dict)
    act_two_remembered_crates: dict[
        tuple[int, int], dict[str, Any]
    ] = field(default_factory=dict)
    fire_zones: list[FireZoneState] = field(default_factory=list)
    brute_aftershocks: list[
        BruteAftershockState
    ] = field(default_factory=list)


@dataclass
class PlayerState:
    max_health: int
    health: int
    damage_min: int
    damage_max: int
    crit_chance: float = 0.0
    dodge_chance: float = 0.0
    critical_damage_multiplier: float = 2.0
    spell_power: int = 0
    player_class: str | None = None
    subclass: str | None = None
    potion_count: int = 0
    gold_count: int = 0
    key_count: int = 0
    enemies_defeated: int = 0
    level: int = 1
    experience: int = 0
    attribute_points: int = 0
    attribute_ranks: dict[str, int] = field(
        default_factory=lambda: {
            "strength": 0,
            "dexterity": 0,
            "intelligence": 0,
            "vitality": 0,
        }
    )
    ability_kill_charge: int = 0
    invisibility_turns: int = 0
    selected_rune_id: str | None = None
    impact_block_started_at: int = -1
    veil_triggered_this_turn: bool = False
    directional_ability_aiming: bool = False
    potion_effect_started_at: int = 0
    act_one_attack_target: tuple[int, int] | None = None
    act_one_attack_was_critical: bool = False
    act_one_movement_origin: tuple[int, int] | None = None
    act_two_movement_started_at: int = 0
    act_two_movement_origin: tuple[int, int] | None = None
    act_two_facing_direction: tuple[int, int] = (0, 1)
    act_two_blocked_movement_started_at: int = -1
    act_two_blocked_movement_direction: tuple[int, int] = (0, 1)
    act_one_dodge_started_at: int = -1
    act_one_dodge_origin: tuple[int, int] | None = None
    act_one_pickup_kind: str | None = None
    act_one_pickup_origin: tuple[int, int] | None = None
    act_one_pickup_started_at: int = -1
    act_two_pickup_kind: str | None = None
    act_two_pickup_origin: tuple[int, int] | None = None
    act_two_pickup_started_at: int = -1
    act_two: ActTwoPlayerState = field(
        default_factory=ActTwoPlayerState,
    )
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
class RunStatistics:
    turns_taken: int = 0
    gold_earned: int = 0
    gold_spent: int = 0
    chests_opened: int = 0
    consumables_used: int = 0
    completed_floors: set[int] = field(default_factory=set)
    kills_by_type: dict[str, int] = field(default_factory=dict)
    death_cause: str | None = None


@dataclass
class GameState:
    floor_index: int
    floor: FloorState
    player: PlayerState
    combat_log: list[str]
    run_stats: RunStatistics = field(
        default_factory=RunStatistics,
    )
    visited_floors: dict[int, FloorState] = field(default_factory=dict)
    act_two_quests: ActTwoQuestState = field(
        default_factory=ActTwoQuestState,
    )
    act_two_trader_floor_index: int | None = None
    act_one_revisit_prepared: bool = False
    game_won: bool = False
    upgrade_screen_open: bool = False
    act_one_upgrades_remaining: int = 0
    class_selection_open: bool = False
    class_transition_started_at: int = 0
    class_selection_choice: str | None = None
    class_selection_choice_started_at: int = 0
    class_selection_preview_ranks: dict[str, int] = field(
        default_factory=dict,
    )
    oracle_debug_mode: bool = False
    act_two_stats_open: bool = False
    act_two_journal_open: bool = False
    act_two_journal_scroll: float = 1.0
    act_two_journal_dragging: bool = False
    act_two_journal_drag_offset: int = 0
    trade_screen_open: bool = False
    rune_selection_open: bool = False
    rune_selection_pending_id: str | None = None
    bloody_altar_open: bool = False
    bloody_altar_pending_id: str | None = None
    upgrade_message: str = ""
    upgrade_reward_pending: bool = False
    floor_transition_started_at: int = -1
    floor_transition_target_index: int | None = None
    floor_transition_target_passage_id: str | None = None
    floor_transition_swapped: bool = False
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

        if (
            self.player.health > 0
            or self.run_stats.death_cause is not None
        ):
            return

        if (
            event.type is GameEventType.HIT
            and event.target == "hero"
            and (event.amount or 0) > 0
        ):
            self.run_stats.death_cause = event.actor

        elif (
            event.type is GameEventType.DEATH
            and event.actor == "hero"
        ):
            self.run_stats.death_cause = str(
                event.data.get("cause") or "unknown"
            )

    def clear_events(self) -> None:
        self.events.clear()


__all__ = [
    "ArcherBarrageShotState",
    "AttributeMapping",
    "BreakableCrateState",
    "BloodyAltarState",
    "ChestState",
    "EnemyBehaviorState",
    "EnemyState",
    "FloorState",
    "GameState",
    "PlayerState",
    "PotionState",
    "ProjectileState",
    "RoomState",
    "SpikeTrapPhase",
    "SpikeTrapState",
    "TreasuryRoomState",
]
