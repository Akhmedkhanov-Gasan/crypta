from settings import SLEEPING_WARDEN_COLOR, WARDEN_COLOR


ACT_ONE_ENEMY_TYPES = {
    "warden": {
        "display_name": "Crypt Warden",
        "max_health": 20,
        "aggro_radius": 12,
        "wander_chance": 0.0,
        "move_every": 1,
        "attack_kind": "boss",
        "attack_range": 7,
        "damage_by_mode": {
            "cross": ((2, 3), (80, 20)),
            "sweep": ((2, 3), (70, 30)),
            "runes": ((3,), (1,)),
        },
        "color": WARDEN_COLOR,
        "sleeping_color": SLEEPING_WARDEN_COLOR,
        "retreat_jump_chance": 0.0,
        "is_unique": True,
    },
}
