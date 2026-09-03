from settings import MAP_COLUMNS, MAP_ROWS
from worldgen.passages import create_north_wall_passage

def generate_warden_floor(config, floor_index, crate_placer=None):
    dungeon_map = [
        ["#" for _ in range(MAP_COLUMNS)]
        for _ in range(MAP_ROWS)
    ]

    def carve_rectangle(left, top, right, bottom):
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                dungeon_map[row][column] = "."

    # Safe arrival chamber and a wide neck into the guard room.
    carve_rectangle(1, 5, 5, 9)
    carve_rectangle(5, 6, 7, 8)

    guard_room = {
        "x": 7,
        "y": 3,
        "width": 7,
        "height": 9,
    }
    carve_rectangle(7, 3, 13, 11)

    boss_room = {
        "x": 14,
        "y": 2,
        "width": 10,
        "height": 11,
    }
    carve_rectangle(15, 3, 22, 11)
    boss_door = (14, 7)
    dungeon_map[boss_door[1]][boss_door[0]] = "."

    guard_bounds = (7, 3, 13, 11)
    arena_bounds = (15, 3, 22, 11)
    guard_positions = (
        ("goblin", (9, 5)),
        ("brute", (11, 7)),
        ("archer", (12, 9)),
    )
    boss_positions = (
        ("warden", (19, 7)),
        ("archer", (16, 4)),
        ("archer", (22, 10)),
    )

    enemies = [
        {
            "type": enemy_type,
            "position": position,
            "boss_group": False,
            "movement_bounds": guard_bounds,
        }
        for enemy_type, position in guard_positions
    ]
    enemies.extend(
        {
            "type": enemy_type,
            "position": position,
            "boss_group": True,
            "movement_bounds": arena_bounds,
        }
        for enemy_type, position in boss_positions
    )

    passages = [
        create_north_wall_passage(
            dungeon_map,
            boss_room,
            "exit",
            floor_index + 1,
            "entrance",
            requires_clear=True,
        )
    ]

    breakable_crates = []

    if crate_placer is not None:
        candidate_positions = [
            (column, row)
            for row, map_row in enumerate(dungeon_map)
            for column, tile in enumerate(map_row)
            if (
                tile == "."
                and (
                    1 <= column <= 5 and 5 <= row <= 9
                    or 7 <= column <= 13 and 3 <= row <= 11
                )
            )
        ]

        protected_positions = {
            (2, 7),
            boss_door,
            *(
                (column, row)
                for column in range(1, 6)
                for row in range(8, 10)
            ),
            *(passage["trigger_position"] for passage in passages),
            *(passage["wall_position"] for passage in passages),
        }
        occupied_positions = {
            *protected_positions,
            *(enemy["position"] for enemy in enemies),
        }

        breakable_crates = crate_placer(
            dungeon_map,
            candidate_positions,
            config.get("breakable_crate_count", 0),
            occupied_positions,
            protected_positions,
        )

    return {
        "map": ["".join(row) for row in dungeon_map],
        "player_start": (2, 7),
        "enemies": enemies,
        "chests": [],
        "potions": [],
        "breakable_crates": breakable_crates,
        "passages": passages,
        "stairs": (19, 7),
        "boss_door": boss_door,
        "boss_room": boss_room,
        "boss_columns": [],
        "boss_emitters": [],
        "seal_boss_door_during_fight": True,
        "torches": [],
        "visual_seed": 10301,
    }


__all__ = ["generate_warden_floor"]
