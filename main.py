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
                "color": enemy_config["color"],
                "sleeping_color": enemy_config["sleeping_color"],
                "retreat_jump_chance": (
                    enemy_config["retreat_jump_chance"]
                ),
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
        "stairs_column": floor["stairs"][0],
        "stairs_row": floor["stairs"][1],
        "boss_door": floor["boss_door"],
        "boss_room": floor["boss_room"],
        "boss_fight_started": floor["boss_door"] is None,
    }


def add_log_message(combat_log, message):
    combat_log.append(message)

    if len(combat_log) > COMBAT_LOG_LIMIT:
        combat_log.pop(0)


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
        enemy["type"] == "warden"
        and enemy["health"] > 0
        and enemy["health"] <= enemy["max_health"] // 2
        and not enemy["second_phase_announced"]
    ):
        enemy["second_phase_announced"] = True
        add_log_message(
            combat_log,
            "The Warden enters phase two!",
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
                        if (enemy["column"], enemy["row"])
                        == (new_column, new_row)
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
                        for position in player_attack_targets
                        for enemy in living_enemies
                        if (
                            enemy["column"],
                            enemy["row"],
                        )
                        == position
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

                        if enemy_was_defeated:
                            enemies_defeated += 1
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
                            for position in player_attack_targets
                            for enemy in living_enemies
                            if (
                                enemy["column"],
                                enemy["row"],
                            )
                            == position
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

                            if not enemy_was_defeated:
                                continue

                            enemies_defeated += 1

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
                                target_is_boss_door
                                or target_is_inside_boss_room
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

                            add_log_message(
                                combat_log,
                                "The boss chamber opens!",
                            )
                            add_log_message(
                                combat_log,
                                "The Crypt Warden awakens.",
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
                    for enemy in floor_state["enemies"]:
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
                                if (
                                    random.random()
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
                                    damage = roll_enemy_damage(
                                        enemy,
                                        attack_mode,
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
                            (other_enemy["column"], other_enemy["row"])
                            for other_enemy in floor_state["enemies"]
                            if (
                                other_enemy is not enemy
                                and other_enemy["health"] > 0
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
                                    f"{attack_mode} attack."
                                ),
                            )
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
                                    f"{attack_mode} attack."
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
        draw_player_attack_markers(
            game_surface,
            player_attack_targets,
        )
        draw_attack_markers(
            game_surface,
            floor_state["enemies"],
        )
        if floor_state["boss_door"] is not None:
            draw_boss_door(
                game_surface,
                floor_state["boss_door"][0],
                floor_state["boss_door"][1],
                floor_state["boss_fight_started"],
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
