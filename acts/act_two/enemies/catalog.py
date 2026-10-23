from settings import (
    MIMIC_COLOR,
    ORACLE_COLOR,
    SLEEPING_MIMIC_COLOR,
    SLEEPING_ORACLE_COLOR,
)


ACT_TWO_ENEMY_TYPES = {
    "mimic": {
        "display_name": "Mimic",
        "max_health": 9,
        "aggro_radius": 99,
        "wander_chance": 0.0,
        "move_every": 1,
        "attack_kind": "melee",
        "attack_range": 1,
        "damage_by_mode": {
            "melee": ((2, 3), (75, 25)),
        },
        "color": MIMIC_COLOR,
        "sleeping_color": SLEEPING_MIMIC_COLOR,
        "retreat_jump_chance": 0.0,
        "dodge_chance": 0.0,
    },
    "oracle": {
        "display_name": "Oracle",
        "max_health": 400,
        "aggro_radius": 99,
        "wander_chance": 0.0,
        "move_every": 1,
        "attack_kind": "oracle",
        "attack_range": 99,
        "damage_by_mode": {
            "gaze": ((5, 6), (70, 30)),
            "revelation": ((5, 6), (60, 40)),
            "shockwave": ((3, 4), (75, 25)),
        },
        "phase_two_damage_by_mode": {
            "gaze": ((7, 8), (60, 40)),
            "revelation": ((7, 8), (50, 50)),
            "shockwave": ((4, 5), (75, 25)),
        },
        "color": ORACLE_COLOR,
        "sleeping_color": SLEEPING_ORACLE_COLOR,
        "retreat_jump_chance": 0.0,
        "is_unique": True,
        "is_immobile": True,
        "footprint_width": 3,
        "footprint_height": 3,
        "projectile_cooldown": 1,
    },
}
