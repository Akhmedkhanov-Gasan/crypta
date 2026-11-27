from math import ceil

ACT_THREE_ENEMY_OVERRIDES = {
    "lantern_warden": {
        "max_health": 260,
        "aggro_radius": 7,
        "wander_chance": 0.0,
        "move_every": 1,
        "attack_kind": "melee",
        "attack_range": 1,
        "retreat_jump_chance": 0.0,
        "dodge_chance": 0.0,
        "damage_by_mode": {
            "melee": ((7, 8), (3, 1)),
            "lantern_sweep": ((8, 10), (3, 1)),
            "soul_lance": ((8, 11), (3, 1)),
            "cinder_nova": ((11, 14), (3, 1)),
            "soul_procession": ((7, 9), (3, 1)),
        },
    },
    "goblin": {
        "max_health": 16,
        "aggro_radius": 6,
        "damage_by_mode": {"melee": ((4, 5), (75, 25))},
    },
    "brute": {
        "max_health": 30,
        "aggro_radius": 6,
        "damage_by_mode": {"cleave": ((7, 9), (80, 20))},
    },
    "archer": {
        "max_health": 14,
        "aggro_radius": 7,
        "attack_range": 6,
        "damage_by_mode": {
            "ranged": ((4, 5), (75, 25)),
            "melee": ((3,), (1,)),
        },
    },
    "sentinel": {
        "max_health": 32,
        "aggro_radius": 6,
        "damage_by_mode": {
            "melee": ((6, 8), (75, 25)),
            "shield_bash": ((6, 8), (75, 25)),
        },
    },
    "priest": {
        "max_health": 18,
        "aggro_radius": 7,
        "heal_amount": 4,
        "damage_by_mode": {
            "magic": ((4, 6), (75, 25)),
            "melee": ((3,), (1,)),
        },
    },
    "priest_ghost": {
        "max_health": 14,
        "aggro_radius": 8,
        "dodge_chance": 0.35,
        "damage_by_mode": {
            "magic": ((5, 7), (75, 25)),
            "melee": ((3, 4), (75, 25)),
        },
    },
}

LANTERN_WARDEN_EXPERIENCE = 40
LANTERN_WARDEN_ABILITY_RANGE = 5
LANTERN_WARDEN_PROCESSION_RANGE = 6
LANTERN_WARDEN_PROCESSION_ARM_LENGTH = 3
LANTERN_WARDEN_ATTACK_ORDER = (
    "lantern_sweep", "soul_lance", "soul_procession", "cinder_nova",
)

HEALTH_GROWTH_PER_FLOOR = 0.12
DAMAGE_GROWTH_INTERVAL = 3


def act_three_enemy_config(enemy_type, act_floor, base_config=None):
    from enemies import ENEMY_TYPES

    config = {
        **(ENEMY_TYPES[enemy_type] if base_config is None else base_config),
        **ACT_THREE_ENEMY_OVERRIDES.get(enemy_type, {}),
    }
    if (
        enemy_type not in ACT_THREE_ENEMY_OVERRIDES
        or act_floor < 3
        or enemy_type == "lantern_warden"
    ):
        return config
    depth = act_floor - 2
    damage_steps = (depth + DAMAGE_GROWTH_INTERVAL - 1) // DAMAGE_GROWTH_INTERVAL
    config["max_health"] = ceil(config["max_health"] * (1 + HEALTH_GROWTH_PER_FLOOR * depth))
    config["damage_by_mode"] = {
        mode: (tuple(value + damage_steps for value in values), weights)
        for mode, (values, weights) in config["damage_by_mode"].items()
    }
    if "heal_amount" in config:
        config["heal_amount"] += damage_steps
    return config


def enemy_config_for_spawn(game_state, enemy_type, position):
    from enemies import ENEMY_TYPES
    from levels import FLOOR_CONFIGS

    floor = game_state.floor
    rune_trial = floor.rune_trial
    if (
        floor.presentation_act != 3
        or position in floor.trial_safe_cells
        or (rune_trial is not None and position in rune_trial["cells"])
    ):
        return ENEMY_TYPES[enemy_type]
    return act_three_enemy_config(
        enemy_type,
        FLOOR_CONFIGS[game_state.floor_index]["act_floor"],
    )
