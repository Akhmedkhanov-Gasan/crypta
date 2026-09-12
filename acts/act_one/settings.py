from game.attributes import PlayerBaseStats, player_stats_with_attributes


# Edit this block to rebalance the common Act One character. The starting
# combat values below are derived from these base values plus attribute ranks.
PLAYER_BASE_STATS = PlayerBaseStats(
    max_health=7,
    damage_min=1,
    damage_max=2,
    crit_chance=0.05,
    dodge_chance=0.05,
    critical_damage_multiplier=1.90,
)
PLAYER_STARTING_ATTRIBUTE_RANKS = {
    "valor": 2,
    "instinct": 1,
    "fortitude": 2,
}
PLAYER_STARTING_STATS = player_stats_with_attributes(
    PLAYER_BASE_STATS,
    PLAYER_STARTING_ATTRIBUTE_RANKS,
)


# Brief captions shown after descending from the upgrade screen.
FLOOR_INTRO_SUBTITLES = {
    2: "THE DESCENT CONTINUES",
    3: "THE AIR GROWS COLDER",
    4: "SOMETHING STIRS BELOW",
}


# Crypt Warden movement
WARDEN_REPOSITION_AFTER_ATTACKS = 2
WARDEN_REPOSITION_COOLDOWN_ATTACKS = 2
WARDEN_REPOSITION_MIN_TRAVEL = 2
WARDEN_REPOSITION_MAX_TRAVEL = 3
WARDEN_REPOSITION_TRIGGER_PLAYER_DISTANCE = 3
WARDEN_REPOSITION_PREFERRED_PLAYER_DISTANCE = 4
ACT_ONE_BELT_SIZE = 6
