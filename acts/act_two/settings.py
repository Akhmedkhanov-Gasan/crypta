from acts.player_stats import PlayerBaseStats


ABILITY_HITS_REQUIRED = 4
WARRIOR_CLEAVE_DAMAGE_BONUS = 2
WARRIOR_CLEAVE_DAMAGE_PER_RANK = 1
WARRIOR_CLEAVE_MAX_RANK = 5
WARRIOR_RHYTHM_MAX_RANK = 2
MAGE_ARCANE_BURST_RANGE = 5
MAGE_ARCANE_BURST_BASE_DAMAGE_BONUS = 2
MAGE_ARCANE_BURST_SPELL_POWER_SCALING = 1
VISION_RADIUS_TILES = 4.6
FOG_UNEXPLORED_ALPHA = 246
FOG_EXPLORED_ALPHA = 194
FOG_EDGE_ALPHA = 146
FOG_EDGE_WIDTH_PIXELS = 38


# Weighted deterministic floor mix. The base and the strongest alternate
# masonry pattern dominate; strongly marked damage remains deliberately rare.
# The values may be tuned directly and do not need to add up to 100.
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

# Walkable debris is concentrated into sparse pockets instead of being spread
# evenly over every room. Percentages are intentionally independent from the
# sprite weights so density and visual variety can be tuned separately.
FLOOR_DECOR_VARIANT_WEIGHTS = (
    ("decor_floor_bone_pile", 12),
    ("decor_floor_urn_shards", 10),
    ("decor_floor_broken_crate", 38),
    ("decor_floor_broken_barrel", 38),
    ("decor_floor_skeleton_sprawled", 1),
    ("decor_floor_skeleton_curled", 1),
)
FLOOR_DECOR_CLUSTER_SIZE_TILES = 5
FLOOR_DECOR_CLUSTER_PERCENT = 35
FLOOR_DECOR_DENSE_PERCENT = 24
FLOOR_DECOR_SPARSE_PERCENT = 2
FLOOR_DECOR_MIN_SPACING_TILES = 2


# Broken and damp masonry are common texture variation. Fixtures use larger
# candidate weights and are then thinned spatially by the renderer.
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

# These are overlays placed only on exposed, otherwise undecorated walls.
WALL_OVERLAY_VARIANT_WEIGHTS = (
    (None, 82),
    ("decor_wall_cobweb", 8),
    ("decor_wall_torn_banner", 4),
    ("decor_wall_guardian_statue", 3),
    ("decor_wall_mourner_statue", 3),
)
WALL_OVERLAY_MIN_SPACING_TILES = 3


# Act Two owns its class baselines. These ranks are intentionally kept beside
# the class combat settings so each class can be balanced without changing Act
# One. They are wired into class transitions during the Act Two progression
# pass; Act One upgrades remain the player's invested ranks on top.
CLASS_BASE_ATTRIBUTE_RANKS = {
    "warrior": {
        "strength": 4,
        "dexterity": 1,
        "intelligence": 0,
        "vitality": 4,
    },
    "rogue": {
        "strength": 2,
        "dexterity": 4,
        "intelligence": 0,
        "vitality": 2,
    },
    "mage": {
        "strength": 1,
        "dexterity": 1,
        "intelligence": 4,
        "vitality": 3,
    },
}


# Base stats for each Act Two class, excluding upgrades earned during the run.
# The game applies only the difference from Act One, preserving run upgrades.
CLASS_BASE_STATS = {
    "warrior": PlayerBaseStats(
        max_health=16,
        damage_min=2,
        damage_max=3,
    ),
    "rogue": PlayerBaseStats(
        max_health=10,
        damage_min=2,
        damage_max=3,
        crit_chance=0.10,
        dodge_chance=0.10,
    ),
    "mage": PlayerBaseStats(
        max_health=12,
        damage_min=2,
        damage_max=3,
    ),
}
