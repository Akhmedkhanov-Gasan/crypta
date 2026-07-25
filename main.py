import random

import pygame

from enemies import ENEMY_TYPES
from generation import generate_floor
from levels import FLOOR_CONFIGS
from logic import (
    can_move_to,
    distance_between,
    get_enemy_attack_mode,
    get_enemy_attack_targets,
    get_enemy_occupied_positions,
    get_oracle_ray,
    has_line_of_sight,
    move_enemy,
    move_enemy_away,
    move_enemy_randomly,
    move_enemy_toward_position,
    roll_enemy_damage,
    roll_player_damage,
    update_enemy_aggro,
)
from rendering import (
    CLASS_SELECTION_READY_MS,
    draw_attack_markers,
    draw_boss_door,
    draw_chest,
    draw_class_selection_screen,
    draw_coin,
    draw_dungeon,
    draw_enemy,
    draw_key,
    draw_map_frame,
    draw_oracle_emitters,
    draw_oracle_projectiles,
    draw_player,
    draw_player_attack_markers,
    draw_potion,
    draw_sidebar,
    draw_stairs,
    draw_status,
    draw_upgrade_screen,
    get_class_selection_rectangles,
    load_act_one_fonts,
    load_act_two_fonts,
    load_act_two_sprites,
)
from settings import (
    BACKGROUND_COLOR,
    COMBAT_LOG_LIMIT,
    CRIT_UPGRADE_AMOUNT,
    DODGE_UPGRADE_AMOUNT,
    FPS,
    GAME_HEIGHT,
    GAME_WIDTH,
    INITIAL_WINDOW_SCALE,
    MAX_CRIT_CHANCE,
    MAX_DODGE_CHANCE,
    PLAYER_DAMAGE_MAX,
    PLAYER_DAMAGE_MIN,
    PLAYER_MAX_HEALTH,
    POTION_HEALING,
)

FIRST_ACT_FINAL_FLOOR = 2
CLASS_ABILITY_KILLS = 2
ROGUE_INVISIBILITY_TURNS = 5
MAGE_SPELL_RANGE = 5
MAGE_SPELL_DAMAGE_BONUS = 2
WARRIOR_STRIKE_DAMAGE_BONUS = 2


def create_floor_state(floor_index):
    floor = generate_floor(floor_index)
    player_column, player_row = floor["player_start"]
    enemies = []
    enemy_type_counts = {}

    for enemy_data in floor["enemies"]:
        enemy_column, enemy_row = enemy_data["position"]
        enemy_type = enemy_data["type"]
        belongs_to_boss_group = enemy_data.get(
            "boss_group",
            False,
        )
        enemy_config = ENEMY_TYPES[enemy_type]
        enemy_type_counts[enemy_type] = (
            enemy_type_counts.get(enemy_type, 0) + 1
        )
        enemy_number = enemy_type_counts[enemy_type]
        enemy_name = (
            enemy_config["display_name"]
            if enemy_config.get("is_unique", False)
            else f"{enemy_config['display_name']} {enemy_number}"
        )
        enemies.append(
            {
                "type": enemy_type,
                "column": enemy_column,
                "row": enemy_row,
                "health": enemy_config["max_health"],
                "max_health": enemy_config["max_health"],
                "is_aggro": False,
                "name": enemy_name,
                "has_key": False,
                "attack_targets": [],
                "aggro_radius": enemy_config["aggro_radius"],
                "wander_chance": enemy_config["wander_chance"],
                "move_every": enemy_config["move_every"],
                "move_counter": 0,
                "attack_kind": enemy_config["attack_kind"],
                "attack_range": enemy_config["attack_range"],
                "damage_by_mode": enemy_config["damage_by_mode"],
                "phase_two_damage_by_mode": enemy_config.get(
                    "phase_two_damage_by_mode",
                ),
                "color": enemy_config["color"],
                "sleeping_color": enemy_config["sleeping_color"],
                "retreat_jump_chance": (
                    enemy_config["retreat_jump_chance"]
                ),
                "is_immobile": enemy_config.get(
                    "is_immobile",
                    False,
                ),
                "footprint_width": enemy_config.get(
                    "footprint_width",
                    1,
                ),
                "footprint_height": enemy_config.get(
                    "footprint_height",
                    1,
                ),
                "projectile_cooldown": 0,
                "projectile_cooldown_duration": enemy_config.get(
                    "projectile_cooldown",
                    0,
                ),
                "last_oracle_action": None,
                "last_straight_pattern": None,
                "oracle_awakened": False,
                "phase_transition_pending": False,
                "prepared_attack_mode": None,
                "selected_attack_mode": None,
                "last_attack_mode": None,
                "second_phase_announced": False,
                "boss_group": belongs_to_boss_group,
                "is_active": not belongs_to_boss_group,
                "shield_turns": 0,
                "shield_direction": None,
                "shield_cooldown": 0,
                "shield_duration": enemy_config.get(
                    "shield_duration",
                    0,
                ),
                "shield_cooldown_duration": enemy_config.get(
                    "shield_cooldown",
                    0,
                ),
                "heal_target": None,
                "heal_cooldown": 0,
                "heal_amount": enemy_config.get(
                    "heal_amount",
                    0,
                ),
                "heal_cooldown_duration": enemy_config.get(
                    "heal_cooldown",
                    0,
                ),
                "heal_range": enemy_config.get(
                    "heal_range",
                    0,
                ),
            }
        )

    eligible_key_carriers = [
        enemy
        for enemy in enemies
        if (
            (enemy["column"], enemy["row"]) != floor["stairs"]
            and not enemy["boss_group"]
        )
    ]

    other_key_carriers = [
        enemy
        for enemy in enemies
        if enemy not in eligible_key_carriers
    ]
    possible_key_carriers = (
        eligible_key_carriers + other_key_carriers
    )
    key_carrier_count = min(
        len(floor["chests"]),
        len(possible_key_carriers),
    )

    for key_carrier in random.sample(
        possible_key_carriers,
        key_carrier_count,
    ):
        key_carrier["has_key"] = True

    chests = []

    for chest_data in floor["chests"]:
        chest_column, chest_row = chest_data["position"]
        chests.append(
            {
                "column": chest_column,
                "row": chest_row,
                "contains": chest_data["contains"],
                "is_open": False,
                "loot_available": False,
            }
        )

    potions = [
        {
            "column": potion_position[0],
            "row": potion_position[1],
        }
        for potion_position in floor["potions"]
    ]

    return {
        "map": floor["map"],
        "player_column": player_column,
        "player_row": player_row,
        "enemies": enemies,
        "chests": chests,
        "potions": potions,
        "dropped_keys": [],
        "projectiles": [],
        "stairs_column": floor["stairs"][0],
        "stairs_row": floor["stairs"][1],
        "boss_door": floor["boss_door"],
        "boss_room": floor["boss_room"],
        "boss_columns": floor["boss_columns"],
        "boss_emitters": floor["boss_emitters"],
        "seal_boss_door_during_fight": floor[
            "seal_boss_door_during_fight"
        ],
        "boss_fight_started": floor["boss_door"] is None,
    }


def add_log_message(combat_log, message):
    combat_log.append(message)

    if len(combat_log) > COMBAT_LOG_LIMIT:
        combat_log.pop(0)


def choose_oracle_action(oracle):
    if oracle["oracle_awakened"]:
        actions = ("straight", "terrain", "homing")
        action_weights = {
            "straight": (
                25
                if oracle["last_oracle_action"] == "straight"
                else 45
            ),
            "terrain": 30,
            "homing": 25,
        }
    else:
        actions = ("straight", "terrain")
        action_weights = {
            "straight": (
                30
                if oracle["last_oracle_action"] == "straight"
                else 60
            ),
            "terrain": 40,
        }
    available_actions = [
        action
        for action in actions
        if not (
            action == "homing"
            and oracle["last_oracle_action"] == "homing"
        )
    ]
    selected_action = random.choices(
        available_actions,
        weights=[
            action_weights[action]
            for action in available_actions
        ],
        k=1,
    )[0]
    oracle["last_oracle_action"] = selected_action

    return selected_action


def choose_straight_pattern(oracle):
    patterns = (
        "cross",
        "diagonal",
        "horizontal",
        "vertical",
    )
    available_patterns = [
        pattern
        for pattern in patterns
        if pattern != oracle["last_straight_pattern"]
    ]
    selected_pattern = random.choice(available_patterns)
    oracle["last_straight_pattern"] = selected_pattern

    return selected_pattern


def spawn_oracle_projectiles(
    oracle,
    floor_state,
    combat_log,
    projectile_kind,
):
    second_phase = (
        oracle["health"] <= oracle["max_health"] // 2
    )
    pattern_name = None

    if projectile_kind == "straight":
        pattern_name = choose_straight_pattern(oracle)
        pattern_projectiles = {
            "cross": [
                ((0, -3), (0, -1)),
                ((3, 0), (1, 0)),
                ((0, 3), (0, 1)),
                ((-3, 0), (-1, 0)),
            ],
            "diagonal": [
                ((-3, -3), (-1, -1)),
                ((3, -3), (1, -1)),
                ((3, 3), (1, 1)),
                ((-3, 3), (-1, 1)),
            ],
            "horizontal": [
                ((-3, -1), (-1, 0)),
                ((-3, 0), (-1, 0)),
                ((-3, 1), (-1, 0)),
                ((3, -1), (1, 0)),
                ((3, 0), (1, 0)),
                ((3, 1), (1, 0)),
            ],
            "vertical": [
                ((-1, -3), (0, -1)),
                ((0, -3), (0, -1)),
                ((1, -3), (0, -1)),
                ((-1, 3), (0, 1)),
                ((0, 3), (0, 1)),
                ((1, 3), (0, 1)),
            ],
        }
        projectile_specs = pattern_projectiles[pattern_name]
    else:
        occupied_projectile_positions = {
            (projectile["column"], projectile["row"])
            for projectile in floor_state["projectiles"]
        }
        available_emitters = [
            emitter
            for emitter in floor_state["boss_emitters"]
            if emitter not in occupied_projectile_positions
        ]
        selected_emitters = random.sample(
            available_emitters,
            min(2, len(available_emitters)),
        )
        projectile_specs = [
            (
                (
                    emitter[0] - oracle["column"],
                    emitter[1] - oracle["row"],
                ),
                (0, 0),
            )
            for emitter in selected_emitters
        ]

    projectile_damage = (
        5
        if projectile_kind == "homing"
        else (3 if second_phase else 2)
    )
    player_position = (
        floor_state["player_column"],
        floor_state["player_row"],
    )
    occupied_projectile_positions = {
        (projectile["column"], projectile["row"])
        for projectile in floor_state["projectiles"]
    }

    for (
        (column_offset, row_offset),
        projectile_direction,
    ) in projectile_specs:
        column = oracle["column"] + column_offset
        row = oracle["row"] + row_offset
        is_emitter_projectile = (
            projectile_kind == "homing"
            and (column, row) in floor_state["boss_emitters"]
        )

        if (
            (column, row) == player_position
            or (column, row) in occupied_projectile_positions
            or (
                not is_emitter_projectile
                and not can_move_to(
                    floor_state["map"],
                    column,
                    row,
                )
            )
        ):
            continue

        floor_state["projectiles"].append(
            {
                "column": column,
                "row": row,
                "state": "charging",
                "kind": projectile_kind,
                "direction": projectile_direction,
                "damage": projectile_damage,
            }
        )

    oracle["projectile_cooldown"] = (
        0
        if oracle["oracle_awakened"]
        else oracle["projectile_cooldown_duration"]
    )
    add_log_message(
        combat_log,
        (
            (
                f"Oracle forms a {pattern_name} "
                "straight volley."
            )
            if projectile_kind == "straight"
            else "Oracle calls forth seeking projectiles."
        ),
    )


def hit_player_with_projectile(
    projectile,
    player_health,
    player_dodge_chance,
    combat_log,
):
    if random.random() < player_dodge_chance:
        add_log_message(
            combat_log,
            "Hero dodges an Oracle projectile.",
        )
        return player_health

    damage = projectile["damage"]
    add_log_message(
        combat_log,
        f"An Oracle projectile hits hero for {damage}.",
    )

    return max(0, player_health - damage)


def update_oracle_projectiles(
    floor_state,
    player_health,
    player_dodge_chance,
    combat_log,
):
    player_position = (
        floor_state["player_column"],
        floor_state["player_row"],
    )
    blocking_positions = {
        (chest["column"], chest["row"])
        for chest in floor_state["chests"]
        if not chest["is_open"]
    }
    blocking_positions.update(
        position
        for enemy in floor_state["enemies"]
        if enemy["type"] == "oracle" and enemy["health"] > 0
        for position in get_enemy_occupied_positions(enemy)
    )
    remaining_projectiles = []
    launched_kinds = set()

    for projectile in floor_state["projectiles"]:
        projectile_position = (
            projectile["column"],
            projectile["row"],
        )

        if player_health <= 0:
            remaining_projectiles.append(projectile)
            continue

        if projectile_position == player_position:
            player_health = hit_player_with_projectile(
                projectile,
                player_health,
                player_dodge_chance,
                combat_log,
            )
            continue

        if projectile["state"] == "charging":
            projectile["state"] = "flying"
            launched_kinds.add(projectile["kind"])

        if projectile["kind"] == "homing":
            projectile_path = get_oracle_ray(
                floor_state["map"],
                projectile["column"],
                projectile["row"],
                floor_state["player_column"],
                floor_state["player_row"],
                blocking_positions,
            )

            if not projectile_path:
                continue

            next_column, next_row = projectile_path[0]
        else:
            next_column = (
                projectile["column"]
                + projectile["direction"][0]
            )
            next_row = (
                projectile["row"]
                + projectile["direction"][1]
            )

            if (
                not (
                    0 <= next_row < len(floor_state["map"])
                    and 0
                    <= next_column
                    < len(floor_state["map"][0])
                )
                or (next_column, next_row)
                in blocking_positions
                or not can_move_to(
                    floor_state["map"],
                    next_column,
                    next_row,
                )
            ):
                continue

        projectile["column"] = next_column
        projectile["row"] = next_row

        if (next_column, next_row) == player_position:
            player_health = hit_player_with_projectile(
                projectile,
                player_health,
                player_dodge_chance,
                combat_log,
            )
            continue

        remaining_projectiles.append(projectile)

    floor_state["projectiles"] = remaining_projectiles

    if "straight" in launched_kinds:
        add_log_message(
            combat_log,
            "Oracle releases its straight volley.",
        )

    if "homing" in launched_kinds:
        add_log_message(
            combat_log,
            "Oracle releases its seeking projectiles.",
        )

    return player_health


def direction_toward(
    start_column,
    start_row,
    target_column,
    target_row,
):
    column_distance = target_column - start_column
    row_distance = target_row - start_row

    if abs(column_distance) >= abs(row_distance):
        return (1 if column_distance > 0 else -1, 0)

    return (0, 1 if row_distance > 0 else -1)


def resolve_oracle_phase_transition(
    oracle,
    floor_state,
    combat_log,
):
    if not oracle["phase_transition_pending"]:
        return False

    oracle["phase_transition_pending"] = False
    oracle["oracle_awakened"] = True
    oracle["attack_targets"] = []
    oracle["prepared_attack_mode"] = None
    oracle["projectile_cooldown"] = 1
    floor_state["projectiles"].clear()
    column_change, row_change = direction_toward(
        oracle["column"],
        oracle["row"],
        floor_state["player_column"],
        floor_state["player_row"],
    )
    occupied_positions = {
        position
        for enemy in floor_state["enemies"]
        if enemy is not oracle and enemy["health"] > 0
        for position in get_enemy_occupied_positions(enemy)
    }

    for _ in range(2):
        new_column = (
            floor_state["player_column"] + column_change
        )
        new_row = floor_state["player_row"] + row_change

        if not (
            0 <= new_row < len(floor_state["map"])
            and 0 <= new_column < len(floor_state["map"][0])
            and (new_column, new_row)
            not in occupied_positions
            and can_move_to(
                floor_state["map"],
                new_column,
                new_row,
            )
        ):
            break

        floor_state["player_column"] = new_column
        floor_state["player_row"] = new_row

    add_log_message(
        combat_log,
        "Oracle awakens and releases a wave of force.",
    )
    add_log_message(
        combat_log,
        "The hero is hurled away.",
    )

    return True


def get_oracle_reposition_blockers(
    oracle,
    floor_state,
):
    blocked_positions = {
        position
        for enemy in floor_state["enemies"]
        if enemy["health"] > 0
        for position in get_enemy_occupied_positions(enemy)
    }
    blocked_positions.update(
        (projectile["column"], projectile["row"])
        for projectile in floor_state["projectiles"]
    )
    blocked_positions.update(
        position
        for enemy in floor_state["enemies"]
        for position in enemy["attack_targets"]
    )
    blocked_positions.add(
        (
            floor_state["player_column"],
            floor_state["player_row"],
        )
    )

    for projectile in floor_state["projectiles"]:
        if projectile["kind"] != "straight":
            continue

        blocked_positions.add(
            (
                projectile["column"]
                + projectile["direction"][0],
                projectile["row"]
                + projectile["direction"][1],
            )
        )

    return blocked_positions


def push_player_randomly_from_oracle(
    oracle,
    floor_state,
    combat_log,
):
    directions = [
        (0, -1),
        (1, 0),
        (0, 1),
        (-1, 0),
    ]
    random.shuffle(directions)
    blocked_positions = get_oracle_reposition_blockers(
        oracle,
        floor_state,
    )
    selected_path = []

    for column_change, row_change in directions:
        candidate_path = []
        column = floor_state["player_column"]
        row = floor_state["player_row"]

        for _ in range(2):
            column += column_change
            row += row_change

            if not (
                0 <= row < len(floor_state["map"])
                and 0 <= column < len(floor_state["map"][0])
                and (column, row) not in blocked_positions
                and can_move_to(
                    floor_state["map"],
                    column,
                    row,
                )
            ):
                break

            candidate_path.append((column, row))

        if candidate_path:
            final_column, final_row = candidate_path[-1]

            if (
                max(
                    abs(final_column - oracle["column"]),
                    abs(final_row - oracle["row"]),
                )
                < 3
            ):
                continue

        if len(candidate_path) > len(selected_path):
            selected_path = candidate_path

        if len(selected_path) == 2:
            break

    if not selected_path:
        return

    (
        floor_state["player_column"],
        floor_state["player_row"],
    ) = selected_path[-1]
    add_log_message(
        combat_log,
        "Dormant force throws the hero aside.",
    )


def teleport_player_from_oracle(
    oracle,
    floor_state,
    combat_log,
):
    boss_room = floor_state["boss_room"]
    blocked_positions = get_oracle_reposition_blockers(
        oracle,
        floor_state,
    )
    candidate_positions = [
        (column, row)
        for row in range(
            boss_room["y"] + 1,
            boss_room["y"] + boss_room["height"] - 1,
        )
        for column in range(
            boss_room["x"] + 1,
            boss_room["x"] + boss_room["width"] - 1,
        )
        if (
            can_move_to(floor_state["map"], column, row)
            and (column, row) not in blocked_positions
            and max(
                abs(column - oracle["column"]),
                abs(row - oracle["row"]),
            )
            >= 3
        )
    ]

    if not candidate_positions:
        return

    (
        floor_state["player_column"],
        floor_state["player_row"],
    ) = random.choice(candidate_positions)
    add_log_message(
        combat_log,
        "Oracle warps the hero across the arena.",
    )


def resolve_oracle_hit_reaction(
    oracle,
    floor_state,
    combat_log,
):
    if oracle["health"] <= 0:
        return

    if resolve_oracle_phase_transition(
        oracle,
        floor_state,
        combat_log,
    ):
        return

    if oracle["oracle_awakened"]:
        teleport_player_from_oracle(
            oracle,
            floor_state,
            combat_log,
        )
    else:
        push_player_randomly_from_oracle(
            oracle,
            floor_state,
            combat_log,
        )


def get_priest_heal_candidate(priest, enemies):
    reserved_targets = {
        id(other_priest["heal_target"])
        for other_priest in enemies
        if (
            other_priest is not priest
            and other_priest["type"] == "priest"
            and other_priest["health"] > 0
            and other_priest["heal_target"] is not None
        )
    }
    candidates = [
        enemy
        for enemy in enemies
        if (
            enemy is not priest
            and enemy["health"] > 0
            and enemy["health"] < enemy["max_health"]
            and enemy["is_active"]
            and id(enemy) not in reserved_targets
            and distance_between(
                priest["column"],
                priest["row"],
                enemy["column"],
                enemy["row"],
            )
            <= priest["heal_range"]
        )
    ]

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda enemy: (
            enemy["health"] / enemy["max_health"],
            distance_between(
                priest["column"],
                priest["row"],
                enemy["column"],
                enemy["row"],
            ),
        ),
    )


def attack_enemy(
    enemy,
    damage_minimum,
    damage_maximum,
    critical_chance,
    combat_log,
    damage_bonus=0,
    force_critical=False,
    attacker_position=None,
):
    if (
        enemy["type"] == "sentinel"
        and enemy["shield_turns"] > 0
        and attacker_position is not None
    ):
        attack_direction = direction_toward(
            enemy["column"],
            enemy["row"],
            attacker_position[0],
            attacker_position[1],
        )
        shield_direction = enemy["shield_direction"]
        vulnerable_direction = (
            -shield_direction[0],
            -shield_direction[1],
        )

        if attack_direction != vulnerable_direction:
            add_log_message(
                combat_log,
                f"{enemy['name']}'s shield blocks the attack.",
            )
            return False

    damage = (
        roll_player_damage(damage_minimum, damage_maximum)
        + damage_bonus
    )
    critical_hit = (
        force_critical
        or random.random() < critical_chance
    )

    if critical_hit:
        damage *= 2

    enemy["health"] = max(0, enemy["health"] - damage)

    if critical_hit:
        add_log_message(
            combat_log,
            f"Critical hit on {enemy['name']} for {damage}!",
        )
    else:
        add_log_message(
            combat_log,
            f"Hero hits {enemy['name']} for {damage}.",
        )

    if (
        enemy["type"] in ("warden", "oracle")
        and enemy["health"] > 0
        and enemy["health"] <= enemy["max_health"] // 2
        and not enemy["second_phase_announced"]
    ):
        enemy["second_phase_announced"] = True
        if enemy["type"] == "oracle":
            enemy["phase_transition_pending"] = True
        add_log_message(
            combat_log,
            f"{enemy['name']} enters phase two!",
        )

    if enemy["health"] <= 0:
        add_log_message(
            combat_log,
            f"{enemy['name']} is defeated.",
        )
        return True

    return False


def get_directional_line(
    dungeon_map,
    start_column,
    start_row,
    column_change,
    row_change,
    maximum_range,
    blocking_positions,
):
    positions = []
    map_height = len(dungeon_map)
    map_width = len(dungeon_map[0])

    for distance in range(1, maximum_range + 1):
        column = start_column + column_change * distance
        row = start_row + row_change * distance

        if not (
            0 <= column < map_width
            and 0 <= row < map_height
            and can_move_to(dungeon_map, column, row)
        ):
            break

        if (column, row) in blocking_positions:
            break

        positions.append((column, row))

    return positions


def get_initial_window_size():
    display_info = pygame.display.Info()
    preferred_width = int(GAME_WIDTH * INITIAL_WINDOW_SCALE)
    preferred_height = int(GAME_HEIGHT * INITIAL_WINDOW_SCALE)
    maximum_width = int(display_info.current_w * 0.9)
    maximum_height = int(display_info.current_h * 0.85)
    scale = min(
        preferred_width / GAME_WIDTH,
        preferred_height / GAME_HEIGHT,
        maximum_width / GAME_WIDTH,
        maximum_height / GAME_HEIGHT,
    )

    return (
        int(GAME_WIDTH * scale),
        int(GAME_HEIGHT * scale),
    )


def present_game(window, game_surface):
    window_width, window_height = window.get_size()
    scale = min(
        window_width / GAME_WIDTH,
        window_height / GAME_HEIGHT,
    )
    scaled_width = max(1, int(GAME_WIDTH * scale))
    scaled_height = max(1, int(GAME_HEIGHT * scale))
    scaled_surface = pygame.transform.scale(
        game_surface,
        (scaled_width, scaled_height),
    )
    offset_x = (window_width - scaled_width) // 2
    offset_y = (window_height - scaled_height) // 2

    window.fill(BACKGROUND_COLOR)
    window.blit(scaled_surface, (offset_x, offset_y))
    pygame.display.flip()


def window_to_game_position(window, window_position):
    window_width, window_height = window.get_size()
    scale = min(
        window_width / GAME_WIDTH,
        window_height / GAME_HEIGHT,
    )
    scaled_width = int(GAME_WIDTH * scale)
    scaled_height = int(GAME_HEIGHT * scale)
    offset_x = (window_width - scaled_width) // 2
    offset_y = (window_height - scaled_height) // 2
    mouse_x, mouse_y = window_position

    if not (
        offset_x <= mouse_x < offset_x + scaled_width
        and offset_y <= mouse_y < offset_y + scaled_height
    ):
        return None

    return (
        int((mouse_x - offset_x) / scale),
        int((mouse_y - offset_y) / scale),
    )


def main():
    pygame.init()

    windowed_size = get_initial_window_size()
    screen = pygame.display.set_mode(
        windowed_size,
        pygame.RESIZABLE,
    )
    game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    pygame.display.set_caption("Crypta")
    clock = pygame.time.Clock()
    act_one_fonts = load_act_one_fonts()
    title_font = act_one_fonts["title"]
    font = act_one_fonts["status"]
    log_font = act_one_fonts["text"]
    act_two_fonts = load_act_two_fonts()
    act_two_sprites = load_act_two_sprites()

    floor_index = 0
    floor_state = create_floor_state(floor_index)
    player_max_health = PLAYER_MAX_HEALTH
    player_health = player_max_health
    player_damage_min = PLAYER_DAMAGE_MIN
    player_damage_max = PLAYER_DAMAGE_MAX
    player_crit_chance = 0.0
    player_dodge_chance = 0.0
    potion_count = 0
    gold_count = 0
    key_count = 0
    enemies_defeated = 0
    game_won = False
    upgrade_screen_open = False
    class_selection_open = False
    class_transition_started_at = 0
    upgrade_message = ""
    player_class = None
    player_attack_targets = []
    ability_kill_charge = 0
    invisibility_turns = 0
    directional_ability_aiming = False
    combat_log = ["The descent begins."]
    fullscreen = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                windowed_size = (
                    max(640, event.w),
                    max(360, event.h),
                )
                screen = pygame.display.set_mode(
                    windowed_size,
                    pygame.RESIZABLE,
                )
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and class_selection_open
            ):
                current_time = pygame.time.get_ticks()
                transition_elapsed = (
                    current_time - class_transition_started_at
                )

                if transition_elapsed < CLASS_SELECTION_READY_MS:
                    class_transition_started_at = (
                        current_time
                        - CLASS_SELECTION_READY_MS
                        - 500
                    )
                    continue

                game_mouse_position = window_to_game_position(
                    screen,
                    event.pos,
                )

                if game_mouse_position is None:
                    continue

                class_keys = {
                    "warrior": pygame.K_1,
                    "rogue": pygame.K_2,
                    "mage": pygame.K_3,
                }

                for (
                    class_name,
                    class_rectangle,
                ) in get_class_selection_rectangles().items():
                    if class_rectangle.collidepoint(
                        game_mouse_position
                    ):
                        pygame.event.post(
                            pygame.event.Event(
                                pygame.KEYDOWN,
                                key=class_keys[class_name],
                            )
                        )
                        break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    if fullscreen:
                        screen = pygame.display.set_mode(
                            windowed_size,
                            pygame.RESIZABLE,
                        )
                    else:
                        windowed_size = screen.get_size()
                        screen = pygame.display.set_mode(
                            (0, 0),
                            pygame.FULLSCREEN,
                        )

                    fullscreen = not fullscreen
                    continue

                if event.key == pygame.K_F2:
                    floor_index = FIRST_ACT_FINAL_FLOOR
                    floor_state = create_floor_state(floor_index)
                    player_max_health = PLAYER_MAX_HEALTH
                    player_health = player_max_health
                    player_damage_min = PLAYER_DAMAGE_MIN
                    player_damage_max = PLAYER_DAMAGE_MAX
                    player_crit_chance = 0.0
                    player_dodge_chance = 0.0
                    potion_count = 0
                    gold_count = 0
                    key_count = 0
                    enemies_defeated = 0
                    game_won = False
                    upgrade_screen_open = False
                    class_selection_open = True
                    class_transition_started_at = (
                        pygame.time.get_ticks()
                    )
                    upgrade_message = ""
                    player_class = None
                    player_attack_targets = []
                    ability_kill_charge = 0
                    invisibility_turns = 0
                    directional_ability_aiming = False
                    combat_log = [
                        "Debug jump: choose an Act II class."
                    ]
                    continue

                if event.key == pygame.K_F3:
                    player_class = player_class or "warrior"
                    player_max_health = PLAYER_MAX_HEALTH
                    player_crit_chance = 0.0
                    player_dodge_chance = 0.0

                    if player_class == "warrior":
                        player_max_health += 4
                    elif player_class == "rogue":
                        player_max_health = max(
                            1,
                            player_max_health - 2,
                        )
                        player_crit_chance = 0.10
                        player_dodge_chance = 0.10

                    player_health = player_max_health
                    player_damage_min = 5
                    player_damage_max = 6
                    potion_count = 2
                    gold_count = 0
                    key_count = 0
                    enemies_defeated = 0
                    game_won = False
                    upgrade_screen_open = False
                    class_selection_open = False
                    class_transition_started_at = 0
                    upgrade_message = ""
                    player_attack_targets = []
                    ability_kill_charge = CLASS_ABILITY_KILLS
                    invisibility_turns = 0
                    directional_ability_aiming = False
                    floor_index = len(FLOOR_CONFIGS) - 1
                    floor_state = create_floor_state(floor_index)
                    combat_log = [
                        "Debug jump: Oracle arena."
                    ]
                    continue

                if player_health <= 0 or game_won:
                    if event.key == pygame.K_r:
                        floor_index = 0
                        floor_state = create_floor_state(floor_index)
                        player_max_health = PLAYER_MAX_HEALTH
                        player_health = player_max_health
                        player_damage_min = PLAYER_DAMAGE_MIN
                        player_damage_max = PLAYER_DAMAGE_MAX
                        player_crit_chance = 0.0
                        player_dodge_chance = 0.0
                        potion_count = 0
                        gold_count = 0
                        key_count = 0
                        enemies_defeated = 0
                        game_won = False
                        upgrade_screen_open = False
                        class_selection_open = False
                        class_transition_started_at = 0
                        upgrade_message = ""
                        player_class = None
                        player_attack_targets = []
                        ability_kill_charge = 0
                        invisibility_turns = 0
                        directional_ability_aiming = False
                        combat_log = ["The descent begins."]
                    continue

                if class_selection_open:
                    transition_elapsed = (
                        pygame.time.get_ticks()
                        - class_transition_started_at
                    )

                    if transition_elapsed < CLASS_SELECTION_READY_MS:
                        if event.key in (
                            pygame.K_SPACE,
                            pygame.K_RETURN,
                            pygame.K_KP_ENTER,
                        ):
                            class_transition_started_at = (
                                pygame.time.get_ticks()
                                - CLASS_SELECTION_READY_MS
                                - 500
                            )
                        continue

                    chosen_class = None

                    if event.key in (pygame.K_1, pygame.K_KP1):
                        chosen_class = "warrior"
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        chosen_class = "rogue"
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        chosen_class = "mage"

                    if chosen_class is None:
                        continue

                    player_class = chosen_class

                    if player_class == "warrior":
                        player_max_health += 4
                        player_health += 4
                    elif player_class == "rogue":
                        player_max_health = max(
                            1,
                            player_max_health - 2,
                        )
                        player_health = max(
                            1,
                            player_health - 2,
                        )
                        player_crit_chance = min(
                            MAX_CRIT_CHANCE,
                            player_crit_chance + 0.10,
                        )
                        player_dodge_chance = min(
                            MAX_DODGE_CHANCE,
                            player_dodge_chance + 0.10,
                        )

                    floor_index += 1
                    floor_state = create_floor_state(floor_index)
                    key_count = 0
                    class_selection_open = False
                    class_transition_started_at = 0
                    player_attack_targets = []
                    add_log_message(
                        combat_log,
                        f"The hero becomes a {player_class}.",
                    )
                    add_log_message(
                        combat_log,
                        "Act II begins. The world gains shape.",
                    )
                    continue

                if upgrade_screen_open:
                    if event.key in (pygame.K_1, pygame.K_KP1):
                        if gold_count <= 0:
                            upgrade_message = "Not enough gold."
                        else:
                            gold_count -= 1
                            player_max_health += 2
                            player_health += 2
                            upgrade_message = "Maximum HP increased by 2."
                            add_log_message(
                                combat_log,
                                upgrade_message,
                            )
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        if gold_count <= 0:
                            upgrade_message = "Not enough gold."
                        else:
                            gold_count -= 1
                            player_damage_min += 1
                            player_damage_max += 1
                            upgrade_message = "Damage increased by 1."
                            add_log_message(
                                combat_log,
                                upgrade_message,
                            )
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        if gold_count <= 0:
                            upgrade_message = "Not enough gold."
                        elif player_crit_chance >= MAX_CRIT_CHANCE:
                            upgrade_message = "Critical chance is capped."
                        else:
                            gold_count -= 1
                            player_crit_chance = min(
                                MAX_CRIT_CHANCE,
                                player_crit_chance
                                + CRIT_UPGRADE_AMOUNT,
                            )
                            upgrade_message = "Critical chance increased by 5%."
                            add_log_message(
                                combat_log,
                                upgrade_message,
                            )
                    elif event.key in (pygame.K_4, pygame.K_KP4):
                        if gold_count <= 0:
                            upgrade_message = "Not enough gold."
                        elif player_dodge_chance >= MAX_DODGE_CHANCE:
                            upgrade_message = "Dodge chance is capped."
                        else:
                            gold_count -= 1
                            player_dodge_chance = min(
                                MAX_DODGE_CHANCE,
                                player_dodge_chance
                                + DODGE_UPGRADE_AMOUNT,
                            )
                            upgrade_message = "Dodge chance increased by 5%."
                            add_log_message(
                                combat_log,
                                upgrade_message,
                            )
                    elif event.key in (
                        pygame.K_RETURN,
                        pygame.K_KP_ENTER,
                    ):
                        floor_index += 1
                        floor_state = create_floor_state(floor_index)
                        key_count = 0
                        upgrade_screen_open = False
                        upgrade_message = ""
                        player_attack_targets = []
                        add_log_message(
                            combat_log,
                            f"Hero descends to floor {floor_index + 1}.",
                        )

                    continue

                column_change = 0
                row_change = 0

                if event.key in (pygame.K_w, pygame.K_UP):
                    row_change = -1
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    row_change = 1
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    column_change = -1
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    column_change = 1

                player_tried_to_move = (
                    column_change != 0 or row_change != 0
                )
                rogue_ability_activated = False
                directional_ability_cast = (
                    player_class in ("warrior", "mage")
                    and directional_ability_aiming
                    and player_tried_to_move
                )

                if event.key == pygame.K_e:
                    if (
                        player_class is not None
                        and ability_kill_charge
                        < CLASS_ABILITY_KILLS
                    ):
                        add_log_message(
                            combat_log,
                            "Class ability is not charged.",
                        )
                        continue

                    if player_class == "rogue":
                        ability_kill_charge = 0
                        invisibility_turns = (
                            ROGUE_INVISIBILITY_TURNS
                        )
                        rogue_ability_activated = True
                    elif player_class in ("warrior", "mage"):
                        directional_ability_aiming = (
                            not directional_ability_aiming
                        )
                        add_log_message(
                            combat_log,
                            (
                                "Choose an ability direction."
                                if directional_ability_aiming
                                else "Ability aiming cancelled."
                            ),
                        )
                        continue

                if (
                    directional_ability_aiming
                    and not player_tried_to_move
                ):
                    if event.key == pygame.K_ESCAPE:
                        directional_ability_aiming = False
                        add_log_message(
                            combat_log,
                            "Ability aiming cancelled.",
                        )
                    continue

                if directional_ability_cast:
                    directional_ability_aiming = False

                player_position_before_action = (
                    floor_state["player_column"],
                    floor_state["player_row"],
                )
                new_column = floor_state["player_column"] + column_change
                new_row = floor_state["player_row"] + row_change
                player_waited = event.key == pygame.K_SPACE
                living_enemies = [
                    enemy
                    for enemy in floor_state["enemies"]
                    if enemy["health"] > 0
                ]
                target_enemy = next(
                    (
                        enemy
                        for enemy in living_enemies
                        if (new_column, new_row)
                        in get_enemy_occupied_positions(enemy)
                    ),
                    None,
                )
                target_chest = next(
                    (
                        chest
                        for chest in floor_state["chests"]
                        if (
                            not chest["is_open"]
                            and (chest["column"], chest["row"])
                            == (new_column, new_row)
                        )
                    ),
                    None,
                )
                stairs_are_open = len(living_enemies) == 0
                target_is_locked_stairs = (
                    not stairs_are_open
                    and (new_column, new_row)
                    == (
                        floor_state["stairs_column"],
                        floor_state["stairs_row"],
                    )
                )
                target_is_boss_door = (
                    floor_state["boss_door"] is not None
                    and (new_column, new_row)
                    == floor_state["boss_door"]
                )
                target_is_inside_boss_room = (
                    floor_state["boss_room"] is not None
                    and floor_state["boss_room"]["x"]
                    <= new_column
                    < (
                        floor_state["boss_room"]["x"]
                        + floor_state["boss_room"]["width"]
                    )
                    and floor_state["boss_room"]["y"]
                    <= new_row
                    < (
                        floor_state["boss_room"]["y"]
                        + floor_state["boss_room"]["height"]
                    )
                )
                living_boss_group = [
                    enemy
                    for enemy in living_enemies
                    if enemy["boss_group"]
                ]
                boss_door_is_sealed = (
                    floor_state[
                        "seal_boss_door_during_fight"
                    ]
                    and floor_state["boss_fight_started"]
                    and bool(living_boss_group)
                )
                player_acted = False
                player_attack_targets = []

                if rogue_ability_activated:
                    for enemy in floor_state["enemies"]:
                        enemy["is_aggro"] = False
                        enemy["attack_targets"] = []
                        enemy["prepared_attack_mode"] = None
                        enemy["heal_target"] = None

                    add_log_message(
                        combat_log,
                        "The rogue vanishes from sight.",
                    )
                    player_acted = True
                elif directional_ability_cast:
                    ability_kill_charge = 0
                    blocking_positions = {
                        (chest["column"], chest["row"])
                        for chest in floor_state["chests"]
                        if not chest["is_open"]
                    }
                    if player_class == "warrior":
                        player_attack_targets = (
                            get_directional_line(
                                floor_state["map"],
                                floor_state["player_column"],
                                floor_state["player_row"],
                                column_change,
                                row_change,
                                1,
                                blocking_positions,
                            )
                        )
                        ability_damage_bonus = (
                            WARRIOR_STRIKE_DAMAGE_BONUS
                        )
                        ability_name = "power strike"
                    else:
                        player_attack_targets = (
                            get_directional_line(
                                floor_state["map"],
                                floor_state["player_column"],
                                floor_state["player_row"],
                                column_change,
                                row_change,
                                MAGE_SPELL_RANGE,
                                blocking_positions,
                            )
                        )
                        ability_damage_bonus = (
                            MAGE_SPELL_DAMAGE_BONUS
                        )
                        ability_name = "arcane burst"

                    ability_targets = [
                        enemy
                        for enemy in living_enemies
                        if any(
                            position
                            in get_enemy_occupied_positions(enemy)
                            for position in player_attack_targets
                        )
                    ]

                    if not ability_targets:
                        add_log_message(
                            combat_log,
                            f"The {ability_name} hits nothing.",
                        )

                    for ability_target in ability_targets:
                        enemy_was_defeated = attack_enemy(
                            ability_target,
                            player_damage_min,
                            player_damage_max,
                            player_crit_chance,
                            combat_log,
                            damage_bonus=ability_damage_bonus,
                            attacker_position=(
                                floor_state["player_column"],
                                floor_state["player_row"],
                            ),
                        )

                        if ability_target["type"] == "oracle":
                            resolve_oracle_hit_reaction(
                                ability_target,
                                floor_state,
                                combat_log,
                            )

                        if enemy_was_defeated:
                            enemies_defeated += 1
                            if ability_target["type"] == "oracle":
                                floor_state["projectiles"].clear()
                            ability_kill_charge = min(
                                CLASS_ABILITY_KILLS,
                                ability_kill_charge + 1,
                            )

                            if ability_target["has_key"]:
                                floor_state["dropped_keys"].append(
                                    (
                                        ability_target["column"],
                                        ability_target["row"],
                                    )
                                )
                                ability_target["has_key"] = False
                                add_log_message(
                                    combat_log,
                                    (
                                        f"{ability_target['name']} "
                                        "drops a key."
                                    ),
                                )

                    player_acted = True
                elif (
                    event.key == pygame.K_h
                    and potion_count > 0
                    and player_health < player_max_health
                ):
                    previous_health = player_health
                    player_health = min(
                        player_max_health,
                        player_health + POTION_HEALING,
                    )
                    potion_count -= 1
                    player_acted = True
                    healed_health = player_health - previous_health
                    add_log_message(
                        combat_log,
                        f"Hero heals {healed_health} HP.",
                    )
                elif player_waited:
                    player_acted = True
                elif player_tried_to_move:
                    if target_enemy:
                        attack_was_from_invisibility = (
                            player_class == "rogue"
                            and invisibility_turns > 0
                        )

                        if attack_was_from_invisibility:
                            invisibility_turns = 0
                            add_log_message(
                                combat_log,
                                "The rogue emerges to attack.",
                            )

                        blocking_positions = {
                            (chest["column"], chest["row"])
                            for chest in floor_state["chests"]
                            if not chest["is_open"]
                        }
                        player_attack_targets = get_directional_line(
                            floor_state["map"],
                            floor_state["player_column"],
                            floor_state["player_row"],
                            column_change,
                            row_change,
                            1,
                            blocking_positions,
                        )
                        enemies_hit = [
                            enemy
                            for enemy in living_enemies
                            if any(
                                position
                                in get_enemy_occupied_positions(enemy)
                                for position in player_attack_targets
                            )
                        ]

                        for hit_enemy in enemies_hit:
                            enemy_was_defeated = attack_enemy(
                                hit_enemy,
                                player_damage_min,
                                player_damage_max,
                                player_crit_chance,
                                combat_log,
                                force_critical=(
                                    attack_was_from_invisibility
                                ),
                                attacker_position=(
                                    floor_state["player_column"],
                                    floor_state["player_row"],
                                ),
                            )

                            if hit_enemy["type"] == "oracle":
                                resolve_oracle_hit_reaction(
                                    hit_enemy,
                                    floor_state,
                                    combat_log,
                                )

                            if not enemy_was_defeated:
                                continue

                            enemies_defeated += 1

                            if hit_enemy["type"] == "oracle":
                                floor_state["projectiles"].clear()

                            if player_class is not None:
                                ability_kill_charge = min(
                                    CLASS_ABILITY_KILLS,
                                    ability_kill_charge + 1,
                                )

                            if hit_enemy["has_key"]:
                                floor_state["dropped_keys"].append(
                                    (
                                        hit_enemy["column"],
                                        hit_enemy["row"],
                                    )
                                )
                                hit_enemy["has_key"] = False
                                add_log_message(
                                    combat_log,
                                    (
                                        f"{hit_enemy['name']} "
                                        "drops a key."
                                    ),
                                )

                        player_acted = True
                    elif target_chest:
                        if key_count > 0:
                            target_chest["is_open"] = True
                            key_count -= 1

                            if target_chest["contains"] == "gold":
                                target_chest["loot_available"] = True
                                add_log_message(
                                    combat_log,
                                    "Chest opened: gold found.",
                                )
                        else:
                            add_log_message(
                                combat_log,
                                "The chest is locked.",
                            )

                        player_acted = True
                    elif (
                        target_is_boss_door
                        and boss_door_is_sealed
                    ):
                        add_log_message(
                            combat_log,
                            "The boss chamber is sealed.",
                        )
                    elif (
                        not target_is_locked_stairs
                        and can_move_to(
                            floor_state["map"],
                            new_column,
                            new_row,
                        )
                    ):
                        floor_state["player_column"] = new_column
                        floor_state["player_row"] = new_row
                        player_acted = True

                        if (
                            (
                                (
                                    target_is_boss_door
                                    and not floor_state[
                                        "seal_boss_door_during_fight"
                                    ]
                                )
                                or (
                                    target_is_inside_boss_room
                                    and not target_is_boss_door
                                )
                            )
                            and not floor_state[
                                "boss_fight_started"
                            ]
                        ):
                            floor_state["boss_fight_started"] = True

                            for enemy in floor_state["enemies"]:
                                if enemy["boss_group"]:
                                    enemy["is_active"] = True
                                    enemy["is_aggro"] = True

                            awakened_boss = next(
                                (
                                    enemy
                                    for enemy
                                    in floor_state["enemies"]
                                    if enemy["boss_group"]
                                ),
                                None,
                            )
                            add_log_message(
                                combat_log,
                                "The boss chamber opens!",
                            )

                            if awakened_boss is None:
                                boss_entry_message = (
                                    "The boss awakens."
                                )
                            elif awakened_boss["type"] == "oracle":
                                boss_entry_message = (
                                    "Oracle's dormant shell begins "
                                    "to move."
                                )
                            else:
                                boss_entry_message = (
                                    f"{awakened_boss['name']} awakens."
                                )

                            add_log_message(
                                combat_log,
                                boss_entry_message,
                            )

                            if floor_state[
                                "seal_boss_door_during_fight"
                            ]:
                                add_log_message(
                                    combat_log,
                                    "The chamber seals behind the hero.",
                                )

                        found_potion = next(
                            (
                                potion
                                for potion in floor_state["potions"]
                                if (
                                    potion["column"],
                                    potion["row"],
                                )
                                == (new_column, new_row)
                            ),
                            None,
                        )

                        if found_potion:
                            potion_count += 1
                            floor_state["potions"].remove(found_potion)
                            add_log_message(
                                combat_log,
                                "Hero picks up a potion.",
                            )

                        chest_with_coin = next(
                            (
                                chest
                                for chest in floor_state["chests"]
                                if (
                                    chest["is_open"]
                                    and chest["loot_available"]
                                    and (
                                        chest["column"],
                                        chest["row"],
                                    )
                                    == (new_column, new_row)
                                )
                            ),
                            None,
                        )

                        if chest_with_coin:
                            gold_count += 1
                            chest_with_coin["loot_available"] = False
                            add_log_message(
                                combat_log,
                                "Hero picks up one gold.",
                            )

                        found_key = next(
                            (
                                key_position
                                for key_position
                                in floor_state["dropped_keys"]
                                if key_position
                                == (new_column, new_row)
                            ),
                            None,
                        )

                        if found_key is not None:
                            key_count += 1
                            floor_state["dropped_keys"].remove(
                                found_key
                            )
                            add_log_message(
                                combat_log,
                                "Hero picks up a key.",
                            )

                        reached_open_stairs = (
                            not any(
                                enemy["health"] > 0
                                for enemy in floor_state["enemies"]
                            )
                            and (new_column, new_row)
                            == (
                                floor_state["stairs_column"],
                                floor_state["stairs_row"],
                            )
                        )

                        if reached_open_stairs:
                            if floor_index == len(FLOOR_CONFIGS) - 1:
                                game_won = True
                                add_log_message(
                                    combat_log,
                                    "The Crypta is conquered.",
                                )
                            elif (
                                floor_index
                                == FIRST_ACT_FINAL_FLOOR
                                and player_class is None
                            ):
                                class_selection_open = True
                                class_transition_started_at = (
                                    pygame.time.get_ticks()
                                )
                                player_acted = False
                                add_log_message(
                                    combat_log,
                                    "The first veil falls.",
                                )
                            else:
                                upgrade_screen_open = True
                                upgrade_message = ""
                                player_acted = False
                                add_log_message(
                                    combat_log,
                                    "The descent altar opens.",
                                )

                if player_acted:
                    player_health = update_oracle_projectiles(
                        floor_state,
                        player_health,
                        player_dodge_chance,
                        combat_log,
                    )

                    if player_health <= 0:
                        (
                            floor_state["player_column"],
                            floor_state["player_row"],
                        ) = player_position_before_action
                        add_log_message(
                            combat_log,
                            "The hero has fallen.",
                        )

                    for enemy in floor_state["enemies"]:
                        if player_health <= 0:
                            break
                        if enemy["health"] <= 0:
                            continue
                        if not enemy["is_active"]:
                            continue
                        if invisibility_turns > 0:
                            enemy["is_aggro"] = False
                            enemy["attack_targets"] = []
                            enemy["prepared_attack_mode"] = None
                            enemy["heal_target"] = None
                            continue

                        if enemy["attack_targets"]:
                            attack_targets = enemy["attack_targets"]
                            attack_mode = enemy["prepared_attack_mode"]
                            enemy["attack_targets"] = []
                            enemy["prepared_attack_mode"] = None

                            if (
                                floor_state["player_column"],
                                floor_state["player_row"],
                            ) in attack_targets:
                                is_lethal_oracle_shockwave = (
                                    enemy["type"] == "oracle"
                                    and attack_mode == "shockwave"
                                )

                                if (
                                    not is_lethal_oracle_shockwave
                                    and random.random()
                                    < player_dodge_chance
                                ):
                                    add_log_message(
                                        combat_log,
                                        (
                                            f"Hero dodges "
                                            f"{enemy['name']}'s attack."
                                        ),
                                    )
                                else:
                                    damage = (
                                        player_health
                                        if is_lethal_oracle_shockwave
                                        else roll_enemy_damage(
                                            enemy,
                                            attack_mode,
                                        )
                                    )
                                    player_health = max(
                                        0,
                                        player_health - damage,
                                    )
                                    add_log_message(
                                        combat_log,
                                        (
                                            f"{enemy['name']} hits hero "
                                            f"for {damage}."
                                        ),
                                    )
                            else:
                                add_log_message(
                                    combat_log,
                                    f"{enemy['name']} misses.",
                                )

                            if player_health <= 0:
                                (
                                    floor_state["player_column"],
                                    floor_state["player_row"],
                                ) = player_position_before_action
                                add_log_message(
                                    combat_log,
                                    "The hero has fallen.",
                                )
                                break

                            continue

                        if (
                            enemy["type"] == "priest"
                            and enemy["heal_target"] is not None
                        ):
                            heal_target = enemy["heal_target"]
                            enemy["heal_target"] = None

                            if (
                                heal_target["health"] > 0
                                and heal_target["health"]
                                < heal_target["max_health"]
                                and distance_between(
                                    enemy["column"],
                                    enemy["row"],
                                    heal_target["column"],
                                    heal_target["row"],
                                )
                                == 1
                            ):
                                previous_health = heal_target["health"]
                                heal_target["health"] = min(
                                    heal_target["max_health"],
                                    heal_target["health"]
                                    + enemy["heal_amount"],
                                )
                                healed_amount = (
                                    heal_target["health"]
                                    - previous_health
                                )
                                enemy["heal_cooldown"] = (
                                    enemy[
                                        "heal_cooldown_duration"
                                    ]
                                )
                                add_log_message(
                                    combat_log,
                                    (
                                        f"{enemy['name']} heals "
                                        f"{heal_target['name']} "
                                        f"for {healed_amount}."
                                    ),
                                )
                                continue

                        if (
                            enemy["type"] == "sentinel"
                            and enemy["shield_turns"] > 0
                        ):
                            enemy["shield_turns"] -= 1

                            if enemy["shield_turns"] == 0:
                                enemy["shield_direction"] = None
                                enemy["shield_cooldown"] = (
                                    enemy[
                                        "shield_cooldown_duration"
                                    ]
                                )
                                add_log_message(
                                    combat_log,
                                    (
                                        f"{enemy['name']} "
                                        "lowers its shield."
                                    ),
                                )

                            continue

                        enemy_was_aggro = enemy["is_aggro"]
                        update_enemy_aggro(
                            floor_state["map"],
                            enemy,
                            floor_state["player_column"],
                            floor_state["player_row"],
                        )

                        if not enemy_was_aggro and enemy["is_aggro"]:
                            add_log_message(
                                combat_log,
                                f"{enemy['name']} spots the hero.",
                            )

                        occupied_positions = {
                            position
                            for other_enemy in floor_state["enemies"]
                            if (
                                other_enemy is not enemy
                                and other_enemy["health"] > 0
                            )
                            for position
                            in get_enemy_occupied_positions(
                                other_enemy
                            )
                        }
                        occupied_positions.update(
                            (chest["column"], chest["row"])
                            for chest in floor_state["chests"]
                            if not chest["is_open"]
                        )
                        occupied_positions.add(
                            (
                                floor_state["stairs_column"],
                                floor_state["stairs_row"],
                            )
                        )
                        attack_blocking_positions = {
                            (chest["column"], chest["row"])
                            for chest in floor_state["chests"]
                            if not chest["is_open"]
                        }

                        if not enemy["is_aggro"]:
                            (
                                enemy["column"],
                                enemy["row"],
                            ) = move_enemy_randomly(
                                floor_state["map"],
                                enemy,
                                floor_state["player_column"],
                                floor_state["player_row"],
                                occupied_positions,
                            )
                            enemy_was_aggro = enemy["is_aggro"]
                            update_enemy_aggro(
                                floor_state["map"],
                                enemy,
                                floor_state["player_column"],
                                floor_state["player_row"],
                            )

                            if (
                                not enemy_was_aggro
                                and enemy["is_aggro"]
                            ):
                                add_log_message(
                                    combat_log,
                                    f"{enemy['name']} spots the hero.",
                                )

                        if not enemy["is_aggro"]:
                            continue

                        shield_is_ready = (
                            enemy["shield_cooldown"] == 0
                        )
                        heal_is_ready = (
                            enemy["heal_cooldown"] == 0
                        )

                        if enemy["shield_cooldown"] > 0:
                            enemy["shield_cooldown"] -= 1

                        if enemy["heal_cooldown"] > 0:
                            enemy["heal_cooldown"] -= 1

                        distance_to_player = distance_between(
                            enemy["column"],
                            enemy["row"],
                            floor_state["player_column"],
                            floor_state["player_row"],
                        )

                        if enemy["type"] == "oracle":
                            if enemy["projectile_cooldown"] > 0:
                                enemy["projectile_cooldown"] -= 1
                                continue

                            oracle_action = choose_oracle_action(enemy)

                            if oracle_action in (
                                "straight",
                                "homing",
                            ):
                                spawn_oracle_projectiles(
                                    enemy,
                                    floor_state,
                                    combat_log,
                                    oracle_action,
                                )
                                continue

                            attack_targets = (
                                get_enemy_attack_targets(
                                    floor_state["map"],
                                    enemy,
                                    floor_state["player_column"],
                                    floor_state["player_row"],
                                    attack_blocking_positions,
                                )
                            )

                            if attack_targets:
                                attack_mode = (
                                    get_enemy_attack_mode(
                                        enemy,
                                        floor_state[
                                            "player_column"
                                        ],
                                        floor_state["player_row"],
                                    )
                                )
                                enemy["attack_targets"] = (
                                    attack_targets
                                )
                                enemy["prepared_attack_mode"] = (
                                    attack_mode
                                )
                                add_log_message(
                                    combat_log,
                                    (
                                        f"{enemy['name']} prepares "
                                        f"{attack_mode} attack."
                                    ),
                                )

                            continue

                        if (
                            enemy["type"] == "sentinel"
                            and shield_is_ready
                            and distance_to_player <= 3
                            and has_line_of_sight(
                                floor_state["map"],
                                enemy["column"],
                                enemy["row"],
                                floor_state["player_column"],
                                floor_state["player_row"],
                            )
                        ):
                            enemy["shield_direction"] = direction_toward(
                                enemy["column"],
                                enemy["row"],
                                floor_state["player_column"],
                                floor_state["player_row"],
                            )
                            enemy["shield_turns"] = enemy[
                                "shield_duration"
                            ]
                            add_log_message(
                                combat_log,
                                (
                                    f"{enemy['name']} raises "
                                    "its shield."
                                ),
                            )
                            continue

                        if (
                            enemy["type"] == "priest"
                            and heal_is_ready
                        ):
                            heal_candidate = (
                                get_priest_heal_candidate(
                                    enemy,
                                    floor_state["enemies"],
                                )
                            )

                            if heal_candidate is not None:
                                distance_to_ally = distance_between(
                                    enemy["column"],
                                    enemy["row"],
                                    heal_candidate["column"],
                                    heal_candidate["row"],
                                )
                                priest_started_healing = False

                                if distance_to_ally == 1:
                                    enemy["heal_target"] = (
                                        heal_candidate
                                    )
                                    priest_started_healing = True
                                    add_log_message(
                                        combat_log,
                                        (
                                            f"{enemy['name']} prepares "
                                            f"to heal "
                                            f"{heal_candidate['name']}."
                                        ),
                                    )
                                else:
                                    enemy["move_counter"] += 1

                                    if (
                                        enemy["move_counter"]
                                        >= enemy["move_every"]
                                    ):
                                        enemy["move_counter"] = 0
                                        previous_priest_position = (
                                            enemy["column"],
                                            enemy["row"],
                                        )
                                        (
                                            enemy["column"],
                                            enemy["row"],
                                        ) = move_enemy_toward_position(
                                            floor_state["map"],
                                            enemy,
                                            heal_candidate["column"],
                                            heal_candidate["row"],
                                            occupied_positions,
                                        )
                                        priest_started_healing = (
                                            (
                                                enemy["column"],
                                                enemy["row"],
                                            )
                                            != previous_priest_position
                                        )

                                if priest_started_healing:
                                    continue

                        archer_should_retreat = (
                            enemy["type"] == "archer"
                            and distance_to_player == 2
                        )
                        attack_targets = []

                        if not archer_should_retreat:
                            attack_targets = get_enemy_attack_targets(
                                floor_state["map"],
                                enemy,
                                floor_state["player_column"],
                                floor_state["player_row"],
                                attack_blocking_positions,
                            )

                        if attack_targets:
                            attack_mode = get_enemy_attack_mode(
                                enemy,
                                floor_state["player_column"],
                                floor_state["player_row"],
                            )
                            enemy["attack_targets"] = attack_targets
                            enemy["prepared_attack_mode"] = attack_mode
                            add_log_message(
                                combat_log,
                                (
                                    f"{enemy['name']} prepares "
                                    f"{attack_mode.replace('_', ' ')} "
                                    "attack."
                                ),
                            )
                            continue

                        if enemy["is_immobile"]:
                            continue

                        enemy["move_counter"] += 1

                        if enemy["move_counter"] < enemy["move_every"]:
                            continue

                        enemy["move_counter"] = 0

                        if archer_should_retreat:
                            previous_enemy_position = (
                                enemy["column"],
                                enemy["row"],
                            )
                            maximum_steps = (
                                2
                                if random.random()
                                < enemy["retreat_jump_chance"]
                                else 1
                            )
                            (
                                enemy["column"],
                                enemy["row"],
                            ) = move_enemy_away(
                                floor_state["map"],
                                enemy,
                                floor_state["player_column"],
                                floor_state["player_row"],
                                occupied_positions,
                                maximum_steps,
                            )

                            if (
                                distance_between(
                                    previous_enemy_position[0],
                                    previous_enemy_position[1],
                                    enemy["column"],
                                    enemy["row"],
                                )
                                == 2
                            ):
                                add_log_message(
                                    combat_log,
                                    f"{enemy['name']} leaps away.",
                                )
                        else:
                            enemy["column"], enemy["row"] = move_enemy(
                                floor_state["map"],
                                enemy,
                                floor_state["player_column"],
                                floor_state["player_row"],
                                occupied_positions,
                            )

                        attack_targets = get_enemy_attack_targets(
                            floor_state["map"],
                            enemy,
                            floor_state["player_column"],
                            floor_state["player_row"],
                            attack_blocking_positions,
                        )

                        if attack_targets:
                            attack_mode = get_enemy_attack_mode(
                                enemy,
                                floor_state["player_column"],
                                floor_state["player_row"],
                            )
                            enemy["attack_targets"] = attack_targets
                            enemy["prepared_attack_mode"] = attack_mode
                            add_log_message(
                                combat_log,
                                (
                                    f"{enemy['name']} prepares "
                                    f"{attack_mode.replace('_', ' ')} "
                                    "attack."
                                ),
                            )

                    if (
                        invisibility_turns > 0
                        and not rogue_ability_activated
                    ):
                        invisibility_turns -= 1

                        if invisibility_turns == 0:
                            add_log_message(
                                combat_log,
                                "The rogue becomes visible.",
                            )

        current_act = FLOOR_CONFIGS[floor_index]["act"]
        active_status_font = (
            act_two_fonts["status"]
            if current_act >= 2
            else font
        )
        active_heading_font = (
            act_two_fonts["heading"]
            if current_act >= 2
            else font
        )
        active_text_font = (
            act_two_fonts["text"]
            if current_act >= 2
            else log_font
        )
        active_controls_font = (
            act_two_fonts["controls"]
            if current_act >= 2
            else act_one_fonts["controls"]
        )
        game_surface.fill(BACKGROUND_COLOR)
        draw_dungeon(
            game_surface,
            floor_state["map"],
            current_act,
            act_two_sprites,
        )
        draw_map_frame(
            game_surface,
            current_act,
        )
        living_oracle = next(
            (
                enemy
                for enemy in floor_state["enemies"]
                if (
                    enemy["type"] == "oracle"
                    and enemy["health"] > 0
                )
            ),
            None,
        )
        draw_oracle_emitters(
            game_surface,
            floor_state["boss_emitters"],
            (
                living_oracle is not None
                and living_oracle["oracle_awakened"]
            ),
            act_two_sprites,
        )
        draw_player_attack_markers(
            game_surface,
            player_attack_targets,
        )
        draw_attack_markers(
            game_surface,
            floor_state["enemies"],
        )
        if floor_state["boss_door"] is not None:
            living_boss_group = any(
                enemy["health"] > 0 and enemy["boss_group"]
                for enemy in floor_state["enemies"]
            )
            boss_door_is_open = floor_state[
                "boss_fight_started"
            ]

            if floor_state[
                "seal_boss_door_during_fight"
            ]:
                boss_door_is_open = (
                    floor_state["boss_fight_started"]
                    and not living_boss_group
                )

            draw_boss_door(
                game_surface,
                floor_state["boss_door"][0],
                floor_state["boss_door"][1],
                boss_door_is_open,
            )
        draw_stairs(
            game_surface,
            floor_state["stairs_column"],
            floor_state["stairs_row"],
            not any(
                enemy["health"] > 0
                for enemy in floor_state["enemies"]
            ),
            current_act,
            act_two_sprites,
        )
        for potion in floor_state["potions"]:
            draw_potion(
                game_surface,
                potion["column"],
                potion["row"],
                current_act,
                act_two_sprites,
            )
        for chest in floor_state["chests"]:
            draw_chest(
                game_surface,
                chest,
                current_act,
                act_two_sprites,
            )
            if chest["loot_available"]:
                draw_coin(
                    game_surface,
                    chest["column"],
                    chest["row"],
                    current_act,
                    act_two_sprites,
                )
        for dropped_key in floor_state["dropped_keys"]:
            draw_key(
                game_surface,
                dropped_key[0],
                dropped_key[1],
                current_act,
                act_two_sprites,
            )
        draw_player(
            game_surface,
            floor_state["player_column"],
            floor_state["player_row"],
            player_health,
            player_max_health,
            player_class,
            current_act,
            act_two_sprites,
            invisibility_turns,
        )
        for enemy in floor_state["enemies"]:
            if enemy["health"] > 0:
                draw_enemy(
                    game_surface,
                    enemy,
                    current_act,
                    act_two_sprites,
                )
        draw_oracle_projectiles(
            game_surface,
            floor_state["projectiles"],
            act_two_sprites,
        )
        draw_status(
            game_surface,
            active_status_font,
            floor_index,
            player_health,
            floor_state["enemies"],
            game_won,
        )
        draw_sidebar(
            game_surface,
            active_heading_font,
            active_text_font,
            active_controls_font,
            combat_log,
            player_health,
            player_max_health,
            player_damage_min,
            player_damage_max,
            player_crit_chance,
            player_dodge_chance,
            potion_count,
            gold_count,
            key_count,
            enemies_defeated,
            player_class,
            ability_kill_charge,
            invisibility_turns,
            directional_ability_aiming,
            current_act,
            act_two_sprites,
        )
        if upgrade_screen_open:
            active_upgrade_title_font = (
                act_two_fonts["title"]
                if current_act >= 2
                else title_font
            )
            active_upgrade_text_font = (
                act_two_fonts["status"]
                if current_act >= 2
                else font
            )
            draw_upgrade_screen(
                game_surface,
                active_upgrade_title_font,
                active_upgrade_text_font,
                gold_count,
                player_health,
                player_max_health,
                player_damage_min,
                player_damage_max,
                player_crit_chance,
                player_dodge_chance,
                upgrade_message,
            )
        if class_selection_open:
            class_mouse_position = window_to_game_position(
                screen,
                pygame.mouse.get_pos(),
            )
            draw_class_selection_screen(
                game_surface,
                title_font,
                font,
                act_two_fonts["heading"],
                act_two_fonts["text"],
                act_two_sprites,
                (
                    pygame.time.get_ticks()
                    - class_transition_started_at
                ),
                class_mouse_position,
            )
        present_game(screen, game_surface)
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
