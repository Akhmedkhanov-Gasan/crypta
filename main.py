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
    move_enemy,
    move_enemy_away,
    move_enemy_randomly,
    roll_enemy_damage,
    roll_player_damage,
    update_enemy_aggro,
)
from rendering import (
    draw_attack_markers,
    draw_chest,
    draw_coin,
    draw_dungeon,
    draw_enemy,
    draw_key,
    draw_player,
    draw_potion,
    draw_sidebar,
    draw_stairs,
    draw_status,
)
from settings import (
    BACKGROUND_COLOR,
    COMBAT_LOG_LIMIT,
    FPS,
    GAME_HEIGHT,
    GAME_WIDTH,
    INITIAL_WINDOW_SCALE,
    PLAYER_MAX_HEALTH,
    POTION_HEALING,
)


def create_floor_state(floor_index):
    floor = generate_floor(floor_index)
    player_column, player_row = floor["player_start"]
    enemies = []
    enemy_type_counts = {}

    for enemy_data in floor["enemies"]:
        enemy_column, enemy_row = enemy_data["position"]
        enemy_type = enemy_data["type"]
        enemy_config = ENEMY_TYPES[enemy_type]
        enemy_type_counts[enemy_type] = (
            enemy_type_counts.get(enemy_type, 0) + 1
        )
        enemy_number = enemy_type_counts[enemy_type]
        enemies.append(
            {
                "type": enemy_type,
                "column": enemy_column,
                "row": enemy_row,
                "health": enemy_config["max_health"],
                "max_health": enemy_config["max_health"],
                "is_aggro": False,
                "name": (
                    f"{enemy_config['display_name']} {enemy_number}"
                ),
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
            }
        )

    eligible_key_carriers = [
        enemy
        for enemy in enemies
        if (enemy["column"], enemy["row"]) != floor["stairs"]
    ]

    possible_key_carriers = eligible_key_carriers or enemies

    if possible_key_carriers:
        random.choice(possible_key_carriers)["has_key"] = True

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
        "dropped_key": None,
        "stairs_column": floor["stairs"][0],
        "stairs_row": floor["stairs"][1],
    }


def add_log_message(combat_log, message):
    combat_log.append(message)

    if len(combat_log) > COMBAT_LOG_LIMIT:
        combat_log.pop(0)


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
    font = pygame.font.Font(None, 24)
    log_font = pygame.font.Font(None, 22)

    floor_index = 0
    floor_state = create_floor_state(floor_index)
    player_health = PLAYER_MAX_HEALTH
    potion_count = 0
    gold_count = 0
    has_key = False
    enemies_defeated = 0
    game_won = False
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

                if player_health <= 0 or game_won:
                    if event.key == pygame.K_r:
                        floor_index = 0
                        floor_state = create_floor_state(floor_index)
                        player_health = PLAYER_MAX_HEALTH
                        potion_count = 0
                        gold_count = 0
                        has_key = False
                        enemies_defeated = 0
                        game_won = False
                        combat_log = ["The descent begins."]
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

                new_column = floor_state["player_column"] + column_change
                new_row = floor_state["player_row"] + row_change
                player_tried_to_move = column_change != 0 or row_change != 0
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
                player_acted = False

                if (
                    event.key == pygame.K_h
                    and potion_count > 0
                    and player_health < PLAYER_MAX_HEALTH
                ):
                    previous_health = player_health
                    player_health = min(
                        PLAYER_MAX_HEALTH,
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
                        damage = roll_player_damage()
                        target_enemy["health"] = max(
                            0,
                            target_enemy["health"] - damage,
                        )
                        add_log_message(
                            combat_log,
                            f"Hero hits {target_enemy['name']} for {damage}.",
                        )

                        if target_enemy["health"] <= 0:
                            enemies_defeated += 1
                            add_log_message(
                                combat_log,
                                f"{target_enemy['name']} is defeated.",
                            )

                            if target_enemy["has_key"]:
                                floor_state["dropped_key"] = (
                                    target_enemy["column"],
                                    target_enemy["row"],
                                )
                                target_enemy["has_key"] = False
                                add_log_message(
                                    combat_log,
                                    f"{target_enemy['name']} drops a key.",
                                )

                        player_acted = True
                    elif target_chest:
                        if has_key:
                            target_chest["is_open"] = True
                            has_key = False

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

                        if (
                            floor_state["dropped_key"] is not None
                            and (new_column, new_row)
                            == floor_state["dropped_key"]
                        ):
                            has_key = True
                            floor_state["dropped_key"] = None
                            add_log_message(
                                combat_log,
                                "Hero picks up the key.",
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
                            else:
                                floor_index += 1
                                floor_state = create_floor_state(floor_index)
                                has_key = False
                                player_acted = False
                                add_log_message(
                                    combat_log,
                                    f"Hero descends to floor {floor_index + 1}.",
                                )

                if player_acted:
                    for enemy in floor_state["enemies"]:
                        if enemy["health"] <= 0:
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
                                add_log_message(
                                    combat_log,
                                    "The hero has fallen.",
                                )
                                break

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

                        distance_to_player = distance_between(
                            enemy["column"],
                            enemy["row"],
                            floor_state["player_column"],
                            floor_state["player_row"],
                        )
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

        game_surface.fill(BACKGROUND_COLOR)
        draw_dungeon(game_surface, floor_state["map"])
        draw_attack_markers(
            game_surface,
            floor_state["enemies"],
        )
        draw_stairs(
            game_surface,
            floor_state["stairs_column"],
            floor_state["stairs_row"],
            not any(
                enemy["health"] > 0
                for enemy in floor_state["enemies"]
            ),
        )
        for potion in floor_state["potions"]:
            draw_potion(
                game_surface,
                potion["column"],
                potion["row"],
            )
        for chest in floor_state["chests"]:
            draw_chest(game_surface, chest)
            if chest["loot_available"]:
                draw_coin(
                    game_surface,
                    chest["column"],
                    chest["row"],
                )
        if floor_state["dropped_key"] is not None:
            draw_key(
                game_surface,
                floor_state["dropped_key"][0],
                floor_state["dropped_key"][1],
            )
        draw_player(
            game_surface,
            floor_state["player_column"],
            floor_state["player_row"],
            player_health,
        )
        for enemy in floor_state["enemies"]:
            if enemy["health"] > 0:
                draw_enemy(game_surface, enemy)
        draw_status(
            game_surface,
            font,
            floor_index,
            player_health,
            floor_state["enemies"],
            game_won,
        )
        draw_sidebar(
            game_surface,
            font,
            log_font,
            combat_log,
            player_health,
            potion_count,
            gold_count,
            has_key,
            enemies_defeated,
        )
        present_game(screen, game_surface)
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
