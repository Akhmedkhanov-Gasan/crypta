from dataclasses import dataclass, field, fields
from acts.act_three.awakening.state import AwakeningScene
from acts.act_three.items.inventory import INVENTORY_SLOT_COUNT
from acts.act_three.abilities.phantom_state import ArcherPhantom
from acts.act_three.rune_master.state import RuneMenuState


@dataclass(eq=False)
class ArcherBarrageShotState:
    origin: tuple[int, int]
    target: tuple[int, int]
    direction: tuple[int, int] = (1, 0)
    started_at: int = 0


@dataclass(eq=False)
class PaladinSacredLightningState:
    target: tuple[int, int]
    started_at: int = 0


@dataclass
class MageArcaneBurstState:
    ability_effect_started_at: int = 0
    ability_effect_target: tuple[int, int] | None = None
    ability_effect_kind: str | None = None
    ability_effect_cells: tuple[tuple[int, int], ...] = ()
    ability_effect_hit_positions: tuple[
        tuple[int, int],
        ...
    ] = ()


@dataclass
class ItemDragState:
    slot: int
    item: str
    from_belt: bool
    origin: tuple[int, int]
    moving: bool = False


@dataclass
class ActThreePlayerState:
    trader_quest: dict = field(default_factory=dict)
    inventory_unlocked: bool = False
    environment_attack = None

    level_up_effect_started_at: int = -1
    level_up_effect_amount: int = 1
    consumable_aim_slot: int | None = None
    item_drag: ItemDragState | None = None
    consumable_aim_target: tuple[int, int] | None = None
    regeneration_ticks: int = 0
    ironblood_guard: bool = False
    mining: dict | None = None
    blacksmith_quest: dict[str, bool] = field(default_factory=dict)
    rune_trial_quest: dict[str, bool] = field(default_factory=dict)
    ability_runes: dict[str, str] = field(default_factory=dict)
    forge_progress: dict[str, dict[str, int]] = field(default_factory=dict)
    inventory_slots: list[str | None] = field(
        default_factory=lambda: [None] * INVENTORY_SLOT_COUNT,
    )
    weapon_rank: int = 0
    armor_rank: int = 0
    pending_attribute_upgrades: dict[str, int] = field(
        default_factory=lambda: {
            "valor": 0,
            "instinct": 0,
            "will": 0,
            "fortitude": 0,
        }
    )
    unlocked_ability_slots: set[str] = field(
        default_factory=lambda: {"e"}
    )
    ability_slot_charges: dict[str, float] = field(
        default_factory=lambda: {
            "q": 0.0,
            "e": 0.0,
            "f": 0.0,
        }
    )
    debug_unlimited_abilities: bool = False
    mage_arcane_burst: MageArcaneBurstState = field(
        default_factory=MageArcaneBurstState,
    )
    archer_empowered_shot_charge: int = 0
    archer_phantoms: list[ArcherPhantom] = field(default_factory=list)
    archer_mirror_actions: list[dict] = field(default_factory=list)
    archer_rune_projectiles: list[dict] = field(default_factory=list)
    archer_phantom_cast: dict | None = None
    archer_phantom_travel_started_at: int = -1
    archer_phantom_travel_ended_at: int = -1
    archer_leap_charge: int = 0
    archer_attack_target: tuple[int, int] | None = None
    archer_basic_aiming: bool = False
    archer_basic_aim_target: tuple[int, int] | None = None
    archer_basic_aim_started_at: int = 0
    archer_piercing_aiming: bool = False
    archer_piercing_target: tuple[int, int] | None = None
    archer_piercing_effect_target: tuple[int, int] | None = None
    archer_piercing_effect_started_at: int = 0
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
    archer_barrage_zones: list[
        tuple[tuple[int, int], ...]
    ] = field(default_factory=list)
    archer_barrage_directions: dict[
        tuple[tuple[int, int], ...],
        tuple[int, int],
    ] = field(default_factory=dict)
    archer_barrage_hit_turns: dict[int, int] = field(
        default_factory=dict,
    )
    archer_barrage_shots: list[
        ArcherBarrageShotState
    ] = field(default_factory=list)
    archer_barrage_pending_hits: list[
        tuple[int, tuple[int, int], tuple[int, int]]
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
    berserker_last_rage_hits: int = 0
    berserker_last_rage_turns: int = 0
    berserker_last_rage_started_at: int = 0
    berserker_rage_rune: str | None = None
    berserker_deferred_healing: float = 0.0
    berserker_rage_extensions: int = 0
    berserker_rage_released_at: int = -1
    berserker_devastation_active: bool = False
    berserker_blood_cuts: list[tuple[int, int, int]] = field(default_factory=list)

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
    paladin_holy_shield_charge: int = field(default=0, metadata={"save_only": True})
    paladin_holy_shield_turns: int = field(default=0, metadata={"save_only": True})
    paladin_sacred_ground_charge: int = 0
    paladin_sacred_ground_cast_requested: bool = False
    paladin_sacred_ground_anchor: tuple[int, int] | None = None
    paladin_sacred_ground_cells: list[
        tuple[int, int]
    ] = field(default_factory=list)
    paladin_sacred_ground_turns: int = 0
    paladin_sacred_ground_hits: int = 0
    paladin_sacred_ground_floor: int | None = None
    paladin_crusade_hits: int = 0
    paladin_ultimate_rune: str | None = None
    paladin_ram_impacts: list[tuple[int, int, bool, int]] = field(default_factory=list)
    paladin_rune_block_started_at: int = -1
    paladin_tower_damage_remainder: float = 0.0
    paladin_sanctuary_healing_progress: float = 0.0
    paladin_sacred_ground_started_at: int = 0
    paladin_sacred_ground_lightnings: list[
        PaladinSacredLightningState
    ] = field(default_factory=list)

    warlock_attack_target: tuple[int, int] | None = None
    warlock_basic_aiming: bool = False
    warlock_aim_target: tuple[int, int] | None = None
    warlock_curse_aiming: bool = False
    warlock_curse_target: tuple[int, int] | None = None
    warlock_newly_cursed_enemy: str | None = None
    warlock_curse_started_at: int = 0
    warlock_curse_effect_target: (
        tuple[int, int] | None
    ) = None
    warlock_demon_form_active: bool = False
    warlock_demon_rune: str | None = None
    warlock_eternal_bound: bool = False
    warlock_blood_attacks: int = 0
    warlock_last_demon_attack_at: int = -1
    warlock_demon_healing_progress: float = 0.0
    warlock_newly_cursed_enemies: set[str] = field(default_factory=set)
    warlock_curse_transfers: list[tuple[int, int, int, int, int]] = field(default_factory=list)
    warlock_madness_attacks: list[tuple[int, int, int, int, int]] = field(default_factory=list)
    warlock_demon_form_started_at: int = -1
    warlock_demon_form_target_active: bool | None = None

    summoner_familiar_active: bool = False
    summoner_manifestation: dict | None = None
    summoner_manifestation_aiming: bool = False
    summoner_manifestation_target: tuple[int, int] | None = None
    summoner_familiar_mode: str = "familiar"
    summoner_entity_floor: int | None = None
    summoner_totem_anchor: tuple[int, int] | None = None
    summoner_possession_host: str | None = None
    summoner_possession_turns: int = 0
    summoner_recall_requirement: int = 0
    summoner_loss_turns: int = 0
    summoner_cataclysm_aiming: bool = False
    summoner_recall_position: tuple[int, int] | None = None
    summoner_recall_started_at: int = -1
    summoner_recall_floor: int | None = None
    summoner_recall_totem: bool = False
    summoner_absorption_origin: tuple[int, int] | None = None
    summoner_ultimate_rune: str | None = None
    summoner_absorption_attacks: int = 0
    summoner_absorption_damage: float = 1.75
    summoner_absorption_attack_active: bool = False
    summoner_suspended_familiar: dict | None = None
    summoner_rune_started_at: int = -1
    summoner_cataclysm_position: tuple[int, int] | None = None
    summoner_cataclysm_started_at: int = -1
    summoner_familiar_position: tuple[int, int] | None = None
    summoner_familiar_summon_aiming: bool = False
    summoner_familiar_summon_target: tuple[int, int] | None = None
    summoner_familiar_summoned_at: int = -1
    summoner_familiar_summon_direction: str = "left"
    summoner_familiar_skip_turn: bool = False
    summoner_familiar_max_health: int = 0
    summoner_familiar_health: int = 0
    summoner_familiar_charge: float = 0.0
    summoner_familiar_death_penalty: bool = field(default=False, metadata={"save_only": True})
    summoner_familiar_death_true_form: bool = False
    summoner_true_form_active: bool = False
    summoner_true_form_started_at: int = -1
    summoner_true_form_ending_started_at: int = -1
    summoner_true_form_charge: int = 0
    summoner_true_form_base_max_health: int = 0
    summoner_bond_charge: int = field(default=0, metadata={"save_only": True})
    summoner_bond_active: bool = field(default=False, metadata={"save_only": True})
    summoner_bond_player_max_health: int = field(default=0, metadata={"save_only": True})
    summoner_bond_familiar_max_health: int = field(default=0, metadata={"save_only": True})
    summoner_bond_familiar_health: int = field(default=0, metadata={"save_only": True})
    summoner_familiar_movement_origin: tuple[int, int] | None = None
    summoner_familiar_movement_started_at: int = 0
    summoner_familiar_attack_started_at: int = 0
    summoner_familiar_attack_target: tuple[int, int] | None = None
    summoner_familiar_hit_animation_started_at: int = -1
    summoner_familiar_hit_damage: int = 0
    summoner_familiar_hit_origin: tuple[int, int] | None = None
    summoner_familiar_hit_position: tuple[int, int] | None = None
    familiar_turn_started_at: int = 0
    summoner_attack_target: tuple[int, int] | None = None
    summoner_aiming: bool = False
    summoner_aim_target: tuple[int, int] | None = None
    summoner_aim_started_at: int = 0

    facing_direction: tuple[int, int] = (0, 1)
    shadow_reflex_started_at: int = -1
    shadow_reflex_origin: tuple[int, int] | None = None
    shadow_reflex_target: tuple[int, int] | None = None
    shadow_reflex_ranged: bool = False
    teleport_charge: int = 0
    teleport_aiming: bool = False
    teleport_target: tuple[int, int] | None = None
    teleport_preview_target: tuple[int, int] | None = None
    teleport_camera_origin: tuple[int, int] | None = None
    teleport_transition_started_at: int = 0
    ultimate_charge: int = 0
    ultimate_resolved_strikes: int = 0
    ultimate_bonus_strikes_awarded: bool = False
    ultimate_aiming: bool = False
    ultimate_preview_target: str | None = None
    ultimate_targets: list[str] = field(default_factory=list)
    ultimate_visual_variants: list[int] = field(default_factory=list)
    ultimate_origin: tuple[int, int] | None = None
    ultimate_animation_started_at: int = 0
    ultimate_animation_active: bool = False
    ultimate_impact_positions: list[
        tuple[int, int]
    ] = field(default_factory=list)
    ultimate_impact_started_at: int = 0
    movement_animation_started_at: int = 0
    movement_origin: tuple[int, int] | None = None
    attack_animation_started_at: int = 0
    hit_animation_started_at: int = -1
    hit_damage: int = 0
    hit_origin: tuple[int, int] | None = None
    dodge_animation_started_at: int = -1
    death_animation_started_at: int = -1
    old_man_position: tuple[int, int] | None = None


@dataclass
class ArcherBarrageTurnState:
    enemy_ids: tuple[int, ...]
    next_index: int
    player_position_before_action: tuple[int, int]
    rogue_ability_activated: bool
    damaged_enemy_names: frozenset[str]
    prelude_done: bool = False
    ready_at: int = 0


@dataclass
class ActThreeSessionState:
    map_open: bool = False
    map_opened_at: int = -1
    map_closing_at: int = -1
    map_zoom: float = 1.0
    map_offset: tuple[float, float] = (0.0, 0.0)
    map_drag_anchor: tuple[int, int] | None = None
    map_drag_offset: tuple[float, float] = (0.0, 0.0)
    pending_monster_loot: list[dict] = field(default_factory=list)
    dialogue_queue: list[dict] = field(default_factory=list)
    blacksmith_forge_open: bool = False
    rune_menu: RuneMenuState | None = None
    mining_effects: list[dict] = field(default_factory=list)
    mining_reward: dict | None = None
    mining_warning: dict | None = None
    awakening: AwakeningScene | None = None
    barrage_turn: ArcherBarrageTurnState | None = None
    npc_dialog_position: tuple[int, int] | None = None
    npc_menu_from_console: str | None = None
    npc_dialog_floor_index: int = -1
    npc_dialog_phase: str = "closed"
    npc_dialog_started_at: int = 0
    npc_dialog_line_index: int = 0
    trader_tab: str | None = None
    trader_focus: str | None = None
    trader_slot_presses: dict[str, tuple[int, bool]] = field(default_factory=dict)
    npc_conversations_completed: set[str] = field(default_factory=set)
    act_three_transition_open: bool = False
    act_three_transition_started_at: int = 0
    act_three_visual_started_at: int = 0
    act_three_debug_class_selection_open: bool = False
    subclass_selection_open: bool = False
    subclass_pressed_option: str | None = None
    act_three_test_mode: bool = False
    sidebar_tab: str = "closed"
    character_panel_focus: str | None = None
    character_panel_keyboard_focus: bool = False
    journal_scroll_ratio: float | None = None
    journal_dragging: bool = False
    journal_drag_offset: float = 0.0
    log_scroll_offset: int = 0
    enemy_stun_visuals: dict[int, int] = field(
        default_factory=dict,
    )
    priest_rebirth_consumed_corpses: set[int] = field(
        default_factory=set,
    )


ACT_THREE_PLAYER_FIELD_NAMES = frozenset(
    state_field.name
    for state_field in fields(ActThreePlayerState)
    if not state_field.metadata.get("save_only")
)
ACT_THREE_SESSION_FIELD_NAMES = frozenset(
    state_field.name
    for state_field in fields(ActThreeSessionState)
)
