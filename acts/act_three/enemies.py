LANTERN_WARDEN_TYPE = "lantern_warden"

ACT_THREE_ENEMY_TYPES = {
    LANTERN_WARDEN_TYPE: {
        "display_name": "Lantern Warden",
        "max_health": 100,
        "aggro_radius": 7,
        "wander_chance": 0.0,
        "move_every": 1,
        "attack_kind": "melee",
        "attack_range": 1,
        "damage_by_mode": {
            "melee": ((0,), (1,)),
        },
        "color": (210, 164, 85),
        "sleeping_color": (120, 98, 65),
        "retreat_jump_chance": 0.0,
        "dodge_chance": 0.0,
        "is_immobile": False,
        "footprint_width": 2,
        "footprint_height": 2,
    },
}
