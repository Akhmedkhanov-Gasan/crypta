from game.attributes import PlayerBaseStats
ACT_THREE_VISION_RADIUS_TILES = 5
ACT_THREE_EXPLORED_FOG_ALPHA = 210
ACT_THREE_FOG_INNER_RADIUS_TILES = 1.25
ACT_THREE_FOG_OUTER_RADIUS_TILES = 4.0
ACT_THREE_CURRENT_REVEAL_ALPHA = 170

# Base stats for every Act Three subclass, excluding run upgrades.
# They currently match their parent classes and can be balanced independently.
SUBCLASS_BASE_STATS = {
    "berserker": PlayerBaseStats(
        max_health=16,
        damage_min=2,
        damage_max=3,
    ),
    "paladin": PlayerBaseStats(
        max_health=16,
        damage_min=2,
        damage_max=3,
    ),
    "assassin": PlayerBaseStats(
        max_health=10,
        damage_min=2,
        damage_max=3,
        crit_chance=0.10,
        dodge_chance=0.10,
    ),
    "archer": PlayerBaseStats(
        max_health=10,
        damage_min=2,
        damage_max=3,
        crit_chance=0.10,
        dodge_chance=0.10,
    ),
    "warlock": PlayerBaseStats(
        max_health=12,
        damage_min=2,
        damage_max=3,
    ),
    "summoner": PlayerBaseStats(
        max_health=12,
        damage_min=2,
        damage_max=3,
    ),
}

