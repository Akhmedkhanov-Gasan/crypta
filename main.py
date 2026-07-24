import pygame

from levels import FLOORS
from logic import (
    can_move_to,
    move_enemy,
    move_enemy_randomly,
    positions_are_adjacent,
    roll_enemy_damage,
    roll_player_damage,
    update_enemy_aggro,
)
from rendering import (
    draw_dungeon,
    draw_enemy,
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
    PLAYER_MAX_HEALTH,
    POTION_HEALING,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


def create_floor_state(floor_index):
    floor = FLOORS[floor_index]
    player_column, player_row = floor["player_start"]
    enemies = []

    for enemy_number, enemy_data in enumerate(floor["enemies"], start=1):
        enemy_column, enemy_row = enemy_data["position"]
        enemy_health = enemy_data["health"]
        enemies.append(
            {
                "column": enemy_column,
                "row": enemy_row,
                "health": enemy_health,
                "max_health": enemy_health,
                "is_aggro": False,
                "name": f"Enemy {enemy_number}",
            }
        )

    return {
        "map": floor["map"],
        "player_column": player_column,
        "player_row": player_row,
        "enemies": enemies,
        "potion_column": floor["potion"][0],
        "potion_row": floor["potion"][1],
        "potion_is_on_map": True,
        "stairs_column": floor["stairs"][0],
        "stairs_row": floor["stairs"][1],
    }


def add_log_message(combat_log, message):
    combat_log.append(message)

    if len(combat_log) > COMBAT_LOG_LIMIT:
        combat_log.pop(0)


def main():
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Crypta")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    log_font = pygame.font.Font(None, 22)

    floor_index = 0
    floor_state = create_floor_state(floor_index)
    player_health = PLAYER_MAX_HEALTH
    potion_count = 0
    enemies_defeated = 0
    game_won = False
    combat_log = ["The descent begins."]
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if player_health <= 0 or game_won:
                    if event.key == pygame.K_r:
                        floor_index = 0
                        floor_state = create_floor_state(floor_index)
                        player_health = PLAYER_MAX_HEALTH
                        potion_count = 0
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
                            floor_state["potion_is_on_map"]
                            and (new_column, new_row)
                            == (
                                floor_state["potion_column"],
                                floor_state["potion_row"],
                            )
                        ):
                            potion_count += 1
                            floor_state["potion_is_on_map"] = False
                            add_log_message(
                                combat_log,
                                "Hero picks up a potion.",
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
                            if floor_index == len(FLOORS) - 1:
                                game_won = True
                                add_log_message(
                                    combat_log,
                                    "The Crypta is conquered.",
                                )
                            else:
                                floor_index += 1
                                floor_state = create_floor_state(floor_index)
                                player_acted = False
                                add_log_message(
                                    combat_log,
                                    f"Hero descends to floor {floor_index + 1}.",
                                )

                if player_acted:
                    for enemy in floor_state["enemies"]:
                        if enemy["health"] <= 0:
                            continue

                        enemy_was_aggro = enemy["is_aggro"]
                        update_enemy_aggro(
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

                        if enemy["is_aggro"]:
                            enemy["column"], enemy["row"] = move_enemy(
                                floor_state["map"],
                                enemy,
                                floor_state["player_column"],
                                floor_state["player_row"],
                                occupied_positions,
                            )
                        else:
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

                        if (
                            enemy["is_aggro"]
                            and positions_are_adjacent(
                                floor_state["player_column"],
                                floor_state["player_row"],
                                enemy["column"],
                                enemy["row"],
                            )
                        ):
                            damage = roll_enemy_damage()
                            player_health = max(
                                0,
                                player_health - damage,
                            )
                            add_log_message(
                                combat_log,
                                f"{enemy['name']} hits hero for {damage}.",
                            )

                        if player_health <= 0:
                            add_log_message(
                                combat_log,
                                "The hero has fallen.",
                            )
                            break

        screen.fill(BACKGROUND_COLOR)
        draw_dungeon(screen, floor_state["map"])
        draw_stairs(
            screen,
            floor_state["stairs_column"],
            floor_state["stairs_row"],
            not any(
                enemy["health"] > 0
                for enemy in floor_state["enemies"]
            ),
        )
        if floor_state["potion_is_on_map"]:
            draw_potion(
                screen,
                floor_state["potion_column"],
                floor_state["potion_row"],
            )
        draw_player(
            screen,
            floor_state["player_column"],
            floor_state["player_row"],
            player_health,
        )
        for enemy in floor_state["enemies"]:
            if enemy["health"] > 0:
                draw_enemy(screen, enemy)
        draw_status(
            screen,
            font,
            floor_index,
            player_health,
            floor_state["enemies"],
            game_won,
        )
        draw_sidebar(
            screen,
            font,
            log_font,
            combat_log,
            player_health,
            potion_count,
            enemies_defeated,
        )
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
