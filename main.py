import pygame

from levels import FLOORS
from settings import (
    BACKGROUND_COLOR,
    ENEMY_COLOR,
    ENEMY_DAMAGE,
    FLOOR_COLOR,
    FPS,
    GRID_COLOR,
    LOCKED_COLOR,
    PLAYER_COLOR,
    PLAYER_DAMAGE,
    PLAYER_MAX_HEALTH,
    POTION_COLOR,
    POTION_HEALING,
    STAIRS_COLOR,
    TEXT_COLOR,
    TILE_SIZE,
    WALL_COLOR,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)

MAP_WIDTH = len(FLOORS[0]["map"][0]) * TILE_SIZE
MAP_HEIGHT = len(FLOORS[0]["map"]) * TILE_SIZE
MAP_OFFSET_X = (WINDOW_WIDTH - MAP_WIDTH) // 2
MAP_OFFSET_Y = (WINDOW_HEIGHT - MAP_HEIGHT) // 2


def create_floor_state(floor_index):
    floor = FLOORS[floor_index]
    player_column, player_row = floor["player_start"]
    enemy_column, enemy_row = floor["enemy_start"]

    return {
        "map": floor["map"],
        "player_column": player_column,
        "player_row": player_row,
        "enemy_column": enemy_column,
        "enemy_row": enemy_row,
        "enemy_health": floor["enemy_health"],
        "enemy_max_health": floor["enemy_health"],
        "potion_column": floor["potion"][0],
        "potion_row": floor["potion"][1],
        "potion_is_on_map": True,
        "stairs_column": floor["stairs"][0],
        "stairs_row": floor["stairs"][1],
    }


def draw_dungeon(screen, dungeon_map):
    for row_index, row in enumerate(dungeon_map):
        for column_index, tile in enumerate(row):
            x = MAP_OFFSET_X + column_index * TILE_SIZE
            y = MAP_OFFSET_Y + row_index * TILE_SIZE
            tile_rectangle = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            color = WALL_COLOR if tile == "#" else FLOOR_COLOR

            pygame.draw.rect(screen, color, tile_rectangle)
            pygame.draw.rect(screen, GRID_COLOR, tile_rectangle, 1)


def draw_player(screen, column, row):
    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
    pygame.draw.circle(
        screen,
        PLAYER_COLOR,
        (center_x, center_y),
        TILE_SIZE // 3,
    )


def draw_enemy(screen, column, row):
    padding = TILE_SIZE // 5
    x = MAP_OFFSET_X + column * TILE_SIZE + padding
    y = MAP_OFFSET_Y + row * TILE_SIZE + padding
    size = TILE_SIZE - padding * 2
    pygame.draw.rect(
        screen,
        ENEMY_COLOR,
        (x, y, size, size),
        border_radius=6,
    )


def draw_potion(screen, column, row):
    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
    bottle_width = TILE_SIZE // 3
    bottle_height = TILE_SIZE // 2
    bottle_rectangle = pygame.Rect(
        center_x - bottle_width // 2,
        center_y - bottle_height // 2,
        bottle_width,
        bottle_height,
    )

    pygame.draw.rect(
        screen,
        POTION_COLOR,
        bottle_rectangle,
        border_radius=5,
    )
    pygame.draw.rect(
        screen,
        TEXT_COLOR,
        (
            center_x - bottle_width // 4,
            bottle_rectangle.top - 5,
            bottle_width // 2,
            7,
        ),
        border_radius=2,
    )


def draw_stairs(screen, column, row, is_open):
    color = STAIRS_COLOR if is_open else LOCKED_COLOR
    left = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 4
    top = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 5
    right = left + TILE_SIZE // 2
    bottom = top + TILE_SIZE * 3 // 5

    pygame.draw.line(screen, color, (left, top), (left, bottom), 4)
    pygame.draw.line(screen, color, (right, top), (right, bottom), 4)

    for step_number in range(4):
        step_y = top + step_number * (bottom - top) // 3
        pygame.draw.line(screen, color, (left, step_y), (right, step_y), 3)


def draw_status(
    screen,
    font,
    floor_index,
    player_health,
    enemy_health,
    enemy_max_health,
    potion_count,
    game_won,
):
    status = (
        f"Floor: {floor_index + 1}/{len(FLOORS)}    "
        f"HP: {player_health}/{PLAYER_MAX_HEALTH}    "
        f"Enemy: {enemy_health}/{enemy_max_health}    "
        f"Potions: {potion_count} (H)    "
        f"Stairs: {'open' if enemy_health <= 0 else 'locked'}"
    )
    screen.blit(font.render(status, True, TEXT_COLOR), (MAP_OFFSET_X, 28))

    message = None
    message_color = TEXT_COLOR

    if player_health <= 0:
        message = "Defeat - press R to restart"
        message_color = ENEMY_COLOR
    elif game_won:
        message = "Victory - press R to restart"
        message_color = PLAYER_COLOR
    elif enemy_health <= 0:
        message = "Enemy defeated - find the stairs"
        message_color = PLAYER_COLOR

    if message:
        message_surface = font.render(message, True, message_color)
        message_rectangle = message_surface.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 38)
        )
        screen.blit(message_surface, message_rectangle)


def can_move_to(dungeon_map, column, row):
    return dungeon_map[row][column] != "#"


def positions_are_adjacent(first_column, first_row, second_column, second_row):
    return (
        abs(first_column - second_column) + abs(first_row - second_row)
        == 1
    )


def move_enemy(
    dungeon_map,
    enemy_column,
    enemy_row,
    player_column,
    player_row,
):
    column_distance = player_column - enemy_column
    row_distance = player_row - enemy_row

    if abs(column_distance) + abs(row_distance) == 1:
        return enemy_column, enemy_row

    column_step = 0
    row_step = 0

    if column_distance > 0:
        column_step = 1
    elif column_distance < 0:
        column_step = -1

    if row_distance > 0:
        row_step = 1
    elif row_distance < 0:
        row_step = -1

    if abs(column_distance) >= abs(row_distance):
        possible_moves = [
            (enemy_column + column_step, enemy_row),
            (enemy_column, enemy_row + row_step),
        ]
    else:
        possible_moves = [
            (enemy_column, enemy_row + row_step),
            (enemy_column + column_step, enemy_row),
        ]

    for new_column, new_row in possible_moves:
        if (
            (new_column, new_row) != (player_column, player_row)
            and can_move_to(dungeon_map, new_column, new_row)
        ):
            return new_column, new_row

    return enemy_column, enemy_row


def main():
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Crypta")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    floor_index = 0
    floor_state = create_floor_state(floor_index)
    player_health = PLAYER_MAX_HEALTH
    potion_count = 0
    game_won = False
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
                        game_won = False
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
                target_is_enemy = (
                    floor_state["enemy_health"] > 0
                    and (new_column, new_row)
                    == (
                        floor_state["enemy_column"],
                        floor_state["enemy_row"],
                    )
                )
                target_is_locked_stairs = (
                    floor_state["enemy_health"] > 0
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
                    player_health = min(
                        PLAYER_MAX_HEALTH,
                        player_health + POTION_HEALING,
                    )
                    potion_count -= 1
                    player_acted = True
                elif player_tried_to_move:
                    if target_is_enemy:
                        floor_state["enemy_health"] = max(
                            0,
                            floor_state["enemy_health"] - PLAYER_DAMAGE,
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

                        reached_open_stairs = (
                            floor_state["enemy_health"] <= 0
                            and (new_column, new_row)
                            == (
                                floor_state["stairs_column"],
                                floor_state["stairs_row"],
                            )
                        )

                        if reached_open_stairs:
                            if floor_index == len(FLOORS) - 1:
                                game_won = True
                            else:
                                floor_index += 1
                                floor_state = create_floor_state(floor_index)
                                player_acted = False

                if player_acted and floor_state["enemy_health"] > 0:
                    (
                        floor_state["enemy_column"],
                        floor_state["enemy_row"],
                    ) = move_enemy(
                        floor_state["map"],
                        floor_state["enemy_column"],
                        floor_state["enemy_row"],
                        floor_state["player_column"],
                        floor_state["player_row"],
                    )

                    if positions_are_adjacent(
                        floor_state["player_column"],
                        floor_state["player_row"],
                        floor_state["enemy_column"],
                        floor_state["enemy_row"],
                    ):
                        player_health = max(
                            0,
                            player_health - ENEMY_DAMAGE,
                        )

        screen.fill(BACKGROUND_COLOR)
        draw_dungeon(screen, floor_state["map"])
        draw_stairs(
            screen,
            floor_state["stairs_column"],
            floor_state["stairs_row"],
            floor_state["enemy_health"] <= 0,
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
        )
        if floor_state["enemy_health"] > 0:
            draw_enemy(
                screen,
                floor_state["enemy_column"],
                floor_state["enemy_row"],
            )
        draw_status(
            screen,
            font,
            floor_index,
            player_health,
            floor_state["enemy_health"],
            floor_state["enemy_max_health"],
            potion_count,
            game_won,
        )
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
