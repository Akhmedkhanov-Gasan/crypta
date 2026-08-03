FLOOR_CONFIGS = [
    {
        "act": 1,
        "act_floor": 1,
        "room_count": 4,
        "enemy_types": ["goblin", "goblin"],
        "chest_count": 1,
        "potion_count": 1,
    },
    {
        "act": 1,
        "act_floor": 2,
        "room_count": 6,
        "enemy_types": ["goblin", "goblin", "brute"],
        "chest_count": 1,
        "potion_count": 1,
    },
    {
        "act": 1,
        "act_floor": 3,
        "room_count": 5,
        "enemy_types": ["goblin", "brute"],
        "boss_enemy_types": ["warden", "archer", "archer"],
        "chest_count": 1,
        "potion_count": 2,
    },
    {
        "act": 2,
        "act_floor": 1,
        "room_count": 6,
        "enemy_types": [
            "goblin",
            "brute",
            "archer",
            "sentinel",
        ],
        "chest_count": 1,
        "potion_count": 2,
    },
    {
        "act": 2,
        "act_floor": 2,
        "room_count": 7,
        "enemy_types": [
            "goblin",
            "brute",
            "archer",
            "sentinel",
            "priest",
        ],
        "chest_count": 2,
        "potion_count": 2,
    },
    {
        "act": 2,
        "act_floor": 3,
        "room_count": 0,
        "enemy_types": [],
        "boss_enemy_types": ["oracle"],
        "boss_room_width": 19,
        "boss_room_height": 13,
        "boss_room_layout": "oracle_arena",
        "seal_boss_door_during_fight": True,
        "chest_count": 0,
        "potion_count": 0,
    },
    {
        "act": 3,
        "act_floor": 1,
        "map_path": (
            "assets/maps/act_3/environment_v1/"
            "room_spawn_01.tmx"
        ),
        "room_template_directory": (
            "assets/maps/act_3/environment_v1"
        ),
        "generated_piece_count": 5,
    },
]
