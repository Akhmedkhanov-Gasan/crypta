from acts.player_stats import PlayerBaseStats


# Base player stats at the beginning of a new run.
# Run upgrades are applied on top of these values.
PLAYER_STARTING_STATS = PlayerBaseStats(
    max_health=12,
    damage_min=2,
    damage_max=3,
    crit_chance=0.10,
    dodge_chance=0.10,
)


# Brief captions shown after descending from the upgrade screen.
FLOOR_INTRO_SUBTITLES = {
    2: "THE AIR GROWS COLDER",
    3: "SOMETHING STIRS BELOW",
}
