from settings import MAP_COLUMNS, MAP_ROWS


def generate_warden_floor(config):
    """Build the fixed Act One finale: staging room and boss arena."""
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

    # The player must clear this room before reaching the Warden.
    guard_room = {
        "x": 7,
        "y": 3,
        "width": 7,
        "height": 9,
    }
    carve_rectangle(7, 3, 13, 11)

    # A sealed arena with a single guaranteed, unobstructed entrance.
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
        ("goblin", (9, 9)),
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

    return {
        "map": ["".join(row) for row in dungeon_map],
        "player_start": (2, 7),
        "enemies": enemies,
        "chests": [],
        "potions": [(4, 8), (12, 10)],
        "stairs": (19, 7),
        "boss_door": boss_door,
        "boss_room": boss_room,
        "boss_columns": [],
        "boss_emitters": [],
        "seal_boss_door_during_fight": True,
        "torches": [],
        # Fixed seed keeps procedural cracks and decoration consistent.
        "visual_seed": 10301,
    }


__all__ = ["generate_warden_floor"]
