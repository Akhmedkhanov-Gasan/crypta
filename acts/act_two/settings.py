from acts.player_stats import (
    PlayerBaseStats,
    player_stats_with_attributes,
)


ABILITY_HITS_REQUIRED = 4
CONSUMABLE_BELT_SIZE = 6
FIRE_BOMB_DAMAGE = 1
FIRE_BOMB_TOTAL_TICKS = 9
FIRE_BOMB_FLIGHT_MS = 420
FIRE_BOMB_CHEST_DROP_CHANCE = 0.15
SCROLL_CHEST_DROP_CHANCE = 0.10
ACT_TWO_CHEST_LOOT_WEIGHTS = (
    ("gold", 0.60),
    ("fire_bomb", FIRE_BOMB_CHEST_DROP_CHANCE),
    ("scroll_of_stoneflesh", SCROLL_CHEST_DROP_CHANCE),
    ("scroll_of_binding", SCROLL_CHEST_DROP_CHANCE),
    ("healing_scroll", SCROLL_CHEST_DROP_CHANCE),
    ("scroll_of_arcane_impulse", SCROLL_CHEST_DROP_CHANCE),
)
STONEFLESH_SCROLL_HITS = 6
STONEFLESH_PHYSICAL_DAMAGE_MULTIPLIER = 0.40
BINDING_SCROLL_TURNS = 5
HEALING_SCROLL_HEALING = 8
ARCANE_IMPULSE_SCROLL_DAMAGE = 5
FIRE_FRAME_MS = 145
WARRIOR_CLEAVE_DAMAGE_BONUS = 2
WARRIOR_CLEAVE_COLLISION_DAMAGE = 2
WARRIOR_CLEAVE_DAMAGE_PER_RANK = 1
WARRIOR_CLEAVE_MAX_RANK = 5
WARRIOR_RHYTHM_MAX_RANK = 2
MAGE_BASIC_ATTACK_SPELL_POWER_SCALING = 0.5

MAGE_ARCANE_BURST_RANGE = 4
MAGE_ARCANE_BURST_BASE_DAMAGE_BONUS = 2
MAGE_ARCANE_BURST_SPELL_POWER_SCALING = 1.0
MAGE_ARCANE_BURST_EDGE_DAMAGE_MULTIPLIER = 0.5
VISION_RADIUS_TILES = 4.6
FOG_UNEXPLORED_ALPHA = 255
FOG_EXPLORED_ALPHA = 194
FOG_EDGE_ALPHA = 146
FOG_EDGE_WIDTH_PIXELS = 38
SPIKE_TRAP_DAMAGE = 3
BREAKABLE_CRATE_EMPTY_CHANCE = 0.55
BREAKABLE_CRATE_POTION_CHANCE = 0.40
BREAKABLE_CRATE_GOLD_CHANCE = 0.1
ENEMY_GOLD_DROP_CHANCE = 0.15

ACT_TWO_STARTING_LEVEL = 3



FLOOR_TILE_VARIANT_WEIGHTS = (
    ("floor_layout_b", 44),
    ("floor", 36),
    ("floor_fissure_cross", 4),
    ("floor_puddle", 4),
    ("floor_rubble_heavy", 4),
    ("floor_drain", 3),
    ("floor_burial_seal", 3),
    ("floor_fissure", 2),
)


FLOOR_DECOR_VARIANT_WEIGHTS = (
    ("decor_floor_bone_pile", 12),
    ("decor_floor_urn_shards", 10),
    ("decor_floor_broken_crate", 38),
    ("decor_floor_broken_barrel", 38),
    ("decor_floor_skeleton_sprawled", 1),
    ("decor_floor_skeleton_curled", 1),
)
FLOOR_DECOR_CLUSTER_SIZE_TILES = 5
FLOOR_DECOR_CLUSTER_PERCENT = 24
FLOOR_DECOR_DENSE_PERCENT = 12
FLOOR_DECOR_SPARSE_PERCENT = 1
FLOOR_DECOR_MIN_SPACING_TILES = 3



WALL_TILE_VARIANT_WEIGHTS = (
    ("wall", 34),
    ("wall_broken", 28),
    ("wall_damp", 24),
    ("wall_chains", 4),
    ("wall_iron_shackle", 3),
    ("wall_torch", 6),
    ("wall_skull_niche", 1),
)
WALL_WEAR_REPEAT_MIN_SPACING_TILES = 2
WALL_DECOR_MIN_SPACING_TILES = 3
WALL_TORCH_MIN_SPACING_TILES = 5


WALL_OVERLAY_VARIANT_WEIGHTS = (
    (None, 82),
    ("decor_wall_cobweb", 8),
    ("decor_wall_torn_banner", 4),
    ("decor_wall_guardian_statue", 3),
    ("decor_wall_mourner_statue", 3),
)
WALL_OVERLAY_MIN_SPACING_TILES = 3

CLASS_BASE_ATTRIBUTE_RANKS = {
    "warrior": {
        "strength": 4,
        "dexterity": 1,
        "intelligence": 0,
        "vitality": 5,
    },
    "rogue": {
        "strength": 3,
        "dexterity": 5,
        "intelligence": 0,
        "vitality": 2,
    },
    "mage": {
        "strength": 0,
        "dexterity": 1,
        "intelligence": 6,
        "vitality": 3,
    },
}


CLASS_BASE_STATS = {
    "warrior": PlayerBaseStats(
        max_health=8,
        damage_min=2,
        damage_max=3,
    ),
    "rogue": PlayerBaseStats(
        max_health=8,
        damage_min=1,
        damage_max=2,
    ),
    "mage": PlayerBaseStats(
        max_health=4,
        damage_min=1,
        damage_max=2,
    ),
}

CLASS_STARTING_STATS = {
    player_class: player_stats_with_attributes(
        base_stats,
        CLASS_BASE_ATTRIBUTE_RANKS[player_class],
    )
    for player_class, base_stats in CLASS_BASE_STATS.items()
}
