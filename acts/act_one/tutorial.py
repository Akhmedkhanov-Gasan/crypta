from enemies import ENEMY_TYPES
from settings import MAP_COLUMNS, MAP_ROWS
from worldgen.passages import create_north_wall_passage


TUTORIAL_GOBLIN_CONFIG = {
    **ENEMY_TYPES["goblin"],
    "display_name": "Watchful Goblin",
    "is_unique": True,
    "is_immobile": True,
    "wander_chance": 0.0,
    "retreat_jump_chance": 0.0,
    "dodge_chance": 0.0,
}

TUTORIAL_BRUTE_CONFIG = {
    **ENEMY_TYPES["brute"],
    "wander_chance": 0.0,
}

TUTORIAL_FLOOR_LABELS = (
    (
        (5.5, 3.5),
        (
            "WASD - MOVE",
            "SPACE - WAIT",
        ),
    ),
    (
        (17.5, 3.5),
        (
            "ENEMIES ATTACK WHEN THEY SPOT YOU.",
            "ENEMIES TAKE THEIR TURN AFTER YOURS.",
            "MOVE INTO AN ENEMY TO ATTACK.",
        ),
    ),
    (
        (17.5, 8.5),
        (
            "BRUTES STRIKE A LINE OF 3 TILES.",
            "STEP OUT OF THE MARKED TILES.",
        ),
    ),
    (
        (6.0, 8.2),
        (
            "MOVE INTO CRATES TO BREAK THEM.",
            "SUPPLIES INSIDE MAY INCLUDE POTIONS.",
            "STEP ON LOOT TO PICK IT UP.",
            "PRESS A POTION'S BELT NUMBER TO HEAL.",
        ),
    ),
)
WARDEN_FLOOR_LABELS = (
    (
        (3.5, 8.0),
        (
            "DODGE ARCHER SHOTS.",
            "AVOID GREEN ZONES.",
        ),
    ),
)

def generate_tutorial_floor(config, floor_index):
    dungeon_map = [
        ["#" for _ in range(MAP_COLUMNS)]
        for _ in range(MAP_ROWS)
    ]

    def carve_rectangle(left, top, right, bottom):
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                dungeon_map[row][column] = "."

    carve_rectangle(1, 1, 10, 6)
    carve_rectangle(12, 1, 23, 6)
    carve_rectangle(12, 8, 23, 13)
    carve_rectangle(1, 8, 10, 13)

    carve_rectangle(10, 3, 12, 3)
    carve_rectangle(21, 6, 21, 8)
    carve_rectangle(10, 11, 12, 11)

    exit_room = {
        "x": 1,
        "y": 8,
        "width": 10,
        "height": 6,
    }

    exit_passage = create_north_wall_passage(
        dungeon_map,
        exit_room,
        "exit",
        floor_index + 1,
        None,
        requires_clear=True,
    )

    return {
        "map": ["".join(row) for row in dungeon_map],
        "player_start": (3, 2),
        "enemies": [
            {
                "type": "goblin",
                "position": (21, 2),
                "boss_group": False,
                "config": TUTORIAL_GOBLIN_CONFIG,
                "movement_bounds": (12, 1, 23, 6),
            },
            {
                "type": "brute",
                "position": (16, 12),
                "boss_group": False,
                "config": TUTORIAL_BRUTE_CONFIG,
                "movement_bounds": (12, 8, 23, 13),
            },
        ],
        "chests": [],
        "potions": [],
        "breakable_crates": [
            {
                "position": (6, 11),
                "variant": 0,
                "loot_kind": "potion",
            },
        ],
        "passages": [exit_passage],
        "stairs": exit_passage["trigger_position"],
        "boss_door": None,
        "boss_room": None,
        "boss_columns": [],
        "boss_emitters": [],
        "seal_boss_door_during_fight": False,
        "torches": [],
        "visual_seed": 10101,
    }
