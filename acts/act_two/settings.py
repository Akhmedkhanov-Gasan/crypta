from acts.player_stats import PlayerBaseStats


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
