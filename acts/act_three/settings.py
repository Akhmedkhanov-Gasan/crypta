from acts.player_stats import PlayerBaseStats


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


# Standalone values used only by the Act Three debug jump.
DEBUG_PLAYER_DAMAGE_MIN = 5
DEBUG_PLAYER_DAMAGE_MAX = 6
DEBUG_PLAYER_POTION_COUNT = 2
