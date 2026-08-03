from dataclasses import dataclass, field, fields


@dataclass(eq=False)
class ArcherBarrageShotState:
    origin: tuple[int, int]
    target: tuple[int, int]
    started_at: int = 0


@dataclass
class ActThreePlayerState:
    archer_empowered_shot_charge: int = 0
    archer_leap_charge: int = 0
    archer_barrage_zone_charge: int = 0
    archer_attack_target: tuple[int, int] | None = None
    archer_empowered_shot_aiming: bool = False
    archer_empowered_shot_target: tuple[int, int] | None = None
    archer_empowered_shot_started_at: int = 0
    archer_leap_aiming: bool = False
    archer_leap_target: tuple[int, int] | None = None
    archer_leap_origin: tuple[int, int] | None = None
    archer_leap_started_at: int = 0
    archer_barrage_zone_aiming: bool = False
    archer_barrage_zone_anchor: tuple[int, int] | None = None
    archer_barrage_zone_preview_cells: list[
        tuple[int, int]
    ] = field(default_factory=list)
    archer_barrage_zone_cells: list[
        tuple[int, int]
    ] = field(default_factory=list)
    archer_barrage_shots: list[
        ArcherBarrageShotState
    ] = field(default_factory=list)

    berserker_crushing_leap_charge: int = 0
    berserker_crushing_leap_aiming: bool = False
    berserker_crushing_leap_target: tuple[int, int] | None = None
    berserker_crushing_leap_preview_cells: list[
        tuple[int, int]
    ] = field(default_factory=list)
    berserker_crushing_leap_origin: tuple[int, int] | None = None
    berserker_crushing_leap_started_at: int = 0
    berserker_last_rage_charge: int = 0
    berserker_last_rage_turns: int = 0

    paladin_holy_hand_charge: int = 0
    paladin_holy_hand_started_at: int = 0
    paladin_shield_charge_charge: int = 0
    paladin_shield_charge_aiming: bool = False
    paladin_shield_charge_target: tuple[int, int] | None = None
    paladin_shield_charge_preview_cells: list[
        tuple[int, int]
    ] = field(default_factory=list)
    paladin_shield_charge_origin: tuple[int, int] | None = None
    paladin_shield_charge_started_at: int = 0
    paladin_holy_shield_charge: int = 0
    paladin_holy_shield_turns: int = 0

    warlock_attack_target: tuple[int, int] | None = None
    warlock_curse_charge: int = 0
    warlock_curse_aiming: bool = False
    warlock_curse_target: tuple[int, int] | None = None
    warlock_newly_cursed_enemy: str | None = None
    warlock_soul_exchange_charge: int = 0
    warlock_soul_exchange_aiming: bool = False
    warlock_soul_exchange_target: tuple[int, int] | None = None
    warlock_soul_exchange_player_origin: (
        tuple[int, int] | None
    ) = None
    warlock_soul_exchange_enemy_origin: (
        tuple[int, int] | None
    ) = None
    warlock_soul_exchange_enemy_name: str | None = None
    warlock_soul_exchange_started_at: int = 0
    warlock_demon_form_active: bool = False

    summoner_familiar_active: bool = False
    summoner_familiar_position: tuple[int, int] | None = None
    summoner_familiar_max_health: int = 0
    summoner_familiar_health: int = 0
    summoner_familiar_charge: float = 0.0
    summoner_familiar_death_penalty: bool = False
    summoner_true_form_active: bool = False
    summoner_true_form_charge: int = 0
    summoner_true_form_base_max_health: int = 0
    summoner_bond_charge: int = 0
    summoner_bond_active: bool = False
    summoner_bond_player_max_health: int = 0
    summoner_bond_familiar_max_health: int = 0
    summoner_bond_familiar_health: int = 0
    summoner_familiar_movement_origin: tuple[int, int] | None = None
    summoner_familiar_movement_started_at: int = 0
    summoner_familiar_attack_started_at: int = 0
    familiar_turn_started_at: int = 0
    summoner_attack_target: tuple[int, int] | None = None

    facing_direction: tuple[int, int] = (0, 1)
    teleport_charge: int = 0
    teleport_aiming: bool = False
    teleport_target: tuple[int, int] | None = None
    teleport_camera_origin: tuple[int, int] | None = None
    teleport_transition_started_at: int = 0
    ultimate_charge: int = 0
    ultimate_aiming: bool = False
    ultimate_targets: list[str] = field(default_factory=list)
    ultimate_visual_variants: list[int] = field(default_factory=list)
    ultimate_animation_started_at: int = 0
    ultimate_animation_active: bool = False
    movement_animation_started_at: int = 0
    attack_animation_started_at: int = 0


@dataclass
class ActThreeSessionState:
    act_three_transition_open: bool = False
    act_three_transition_started_at: int = 0
    act_three_visual_started_at: int = 0
    act_three_debug_class_selection_open: bool = False
    subclass_selection_open: bool = False
    act_three_test_mode: bool = False
    sidebar_tab: str = "stats"
    log_scroll_offset: int = 0
    upgrade_altar_hovered: bool = False
    upgrade_altar_menu_open: bool = False
    upgrade_altar_menu_tab: str = "attributes"
    upgrade_altar_menu_hovered_control: str | None = None


ACT_THREE_PLAYER_FIELD_NAMES = frozenset(
    state_field.name
    for state_field in fields(ActThreePlayerState)
)
ACT_THREE_SESSION_FIELD_NAMES = frozenset(
    state_field.name
    for state_field in fields(ActThreeSessionState)
)
