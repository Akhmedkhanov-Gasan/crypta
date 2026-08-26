from dataclasses import dataclass, field
from enum import Enum, auto

from acts.act_two.settings import CONSUMABLE_BELT_SIZE


class SpikeTrapPhase(Enum):
    SAFE = auto()
    WARNING = auto()
    ACTIVE = auto()
    COOLDOWN = auto()


class TreasuryTrialPhase(Enum):
    DORMANT = auto()
    ACTIVE = auto()
    REWARD_AVAILABLE = auto()
    CLAIMED = auto()


class RunePuzzlePhase(Enum):
    DORMANT = auto()
    REWARD_AVAILABLE = auto()
    CLAIMED = auto()


@dataclass
class ActOneRevisitCorpseState:
    enemy_type: str
    column: int
    row: int


@dataclass
class ActOneRevisitState:
    dead_boss_position: tuple[int, int] | None = None
    guild_seal_position: tuple[int, int] | None = None
    trader_corpse_positions: list[
        tuple[int, int]
    ] = field(default_factory=list)
    enemy_corpses: list[
        ActOneRevisitCorpseState
    ] = field(default_factory=list)


@dataclass
class BloodyAltarState:
    column: int
    row: int
    claimed: bool = False


@dataclass
class FireZoneState:
    center: tuple[int, int]
    cells: tuple[tuple[int, int], ...]
    origin: tuple[int, int]
    created_at: int
    ticks_remaining: int
    skip_next_advance: bool = True


@dataclass
class DroppedConsumableState:
    kind: str
    origin: tuple[int, int]
    destination: tuple[int, int]
    thrown_at: int


@dataclass
class SpikeTrapState:
    column: int
    row: int
    phase: SpikeTrapPhase = SpikeTrapPhase.SAFE


@dataclass
class BreakableCrateState:
    column: int
    row: int
    variant: int
    is_broken: bool = False
    loot_kind: str | None = None
    loot_available: bool = False
    loot_fire_turns_remaining: int | None = None


@dataclass
class TraderState:
    column: int
    row: int


@dataclass
class TreasuryRoomState:
    x: int
    y: int
    width: int
    height: int
    door_position: tuple[int, int]
    door_orientation: str
    chest_position: tuple[int, int]
    statue_positions: tuple[tuple[int, int], tuple[int, int]]
    enemy_spawn_positions: tuple[
        tuple[int, int],
        tuple[int, int],
        tuple[int, int],
        tuple[int, int],
    ]
    phase: TreasuryTrialPhase = TreasuryTrialPhase.DORMANT

    @classmethod
    def from_mapping(cls, room: dict) -> "TreasuryRoomState":
        return cls(
            x=room["x"],
            y=room["y"],
            width=room["width"],
            height=room["height"],
            door_position=tuple(room["door_position"]),
            door_orientation=room["door_orientation"],
            chest_position=tuple(room["chest_position"]),
            statue_positions=tuple(
                tuple(position)
                for position in room["statue_positions"]
            ),
            enemy_spawn_positions=tuple(
                tuple(position)
                for position in room["enemy_spawn_positions"]
            ),
        )


@dataclass
class RuneRoomState:
    x: int
    y: int
    width: int
    height: int
    door_position: tuple[int, int]
    pedestal_position: tuple[int, int]
    floor_rune_positions: tuple[
        tuple[int, int],
        tuple[int, int],
        tuple[int, int],
    ]
    wall_rune_positions: tuple[
        tuple[int, int],
        tuple[int, int],
        tuple[int, int],
    ]
    activated_runes: set[int] = field(default_factory=set)
    activation_effect_started_at: dict[int, int] = field(
        default_factory=dict
    )
    phase: RunePuzzlePhase = RunePuzzlePhase.DORMANT

    @classmethod
    def from_mapping(cls, room: dict) -> "RuneRoomState":
        return cls(
            x=room["x"],
            y=room["y"],
            width=room["width"],
            height=room["height"],
            door_position=tuple(room["door_position"]),
            pedestal_position=tuple(room["pedestal_position"]),
            floor_rune_positions=tuple(
                tuple(position)
                for position in room["floor_rune_positions"]
            ),
            wall_rune_positions=tuple(
                tuple(position)
                for position in room["wall_rune_positions"]
            ),
        )


@dataclass
class ActTwoPlayerState:
    selected_rune_id: str | None = None
    bloody_pact_id: str | None = None
    consumable_slots: list[str | None] = field(
        default_factory=lambda: [None] * CONSUMABLE_BELT_SIZE
    )
    consumable_belt_initialized: bool = False
    fire_bomb_aiming: bool = False
    fire_bomb_aiming_slot: int | None = None
    scroll_aiming_kind: str | None = None
    scroll_aiming_slot: int | None = None
    stoneflesh_hits: int = 0
    stoneflesh_effect_started_at: int = -1
    scroll_effect_started_at: int = -1
    scroll_effect_kind: str | None = None
    scroll_effect_origin: tuple[int, int] | None = None
    scroll_effect_target: tuple[int, int] | None = None
    selected_ability_direction: tuple[int, int] | None = None
    wait_effect_started_at: int = -1
    dodge_effect_started_at: int = -1
    level_up_effect_started_at: int = -1
    ability_effect_started_at: int = 0
    ability_effect_direction: tuple[int, int] = (0, 1)
    ability_effect_target: tuple[int, int] | None = None
    ability_effect_kind: str | None = None
    ability_effect_cells: tuple[tuple[int, int], ...] = ()
    ability_effect_hit_positions: tuple[tuple[int, int], ...] = ()
    ability_effect_aftershock_positions: tuple[
        tuple[int, int], ...
    ] = ()
    class_upgrade_ranks: dict[str, int] = field(
        default_factory=lambda: {
            "warrior_cleave": 0,
            "warrior_rhythm": 0,
        }
    )
    pending_attribute_upgrades: dict[str, int] = field(
        default_factory=lambda: {
            "strength": 0,
            "dexterity": 0,
            "intelligence": 0,
            "vitality": 0,
        }
    )
