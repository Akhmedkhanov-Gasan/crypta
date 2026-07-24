import pygame

from levels import FLOORS
from settings import (
    ENEMY_COLOR,
    FLOOR_COLOR,
    GRID_COLOR,
    HEALTH_BAR_BACKGROUND,
    HEALTH_BAR_COLOR,
    LOCKED_COLOR,
    PANEL_BORDER_COLOR,
    PANEL_COLOR,
    PLAYER_COLOR,
    PLAYER_DAMAGE_MAX,
    PLAYER_DAMAGE_MIN,
    PLAYER_HEALTH_BAR_COLOR,
    PLAYER_MAX_HEALTH,
    POTION_COLOR,
    SLEEPING_ENEMY_COLOR,
    STAIRS_COLOR,
    TEXT_COLOR,
    TILE_SIZE,
    WALL_COLOR,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


MAP_WIDTH = len(FLOORS[0]["map"][0]) * TILE_SIZE
MAP_HEIGHT = len(FLOORS[0]["map"]) * TILE_SIZE
MAP_OFFSET_X = 40
MAP_OFFSET_Y = (WINDOW_HEIGHT - MAP_HEIGHT) // 2
SIDEBAR_X = MAP_OFFSET_X + MAP_WIDTH + 40
SIDEBAR_Y = MAP_OFFSET_Y
SIDEBAR_WIDTH = WINDOW_WIDTH - SIDEBAR_X - 40
SIDEBAR_HEIGHT = MAP_HEIGHT


def draw_dungeon(screen, dungeon_map):
    for row_index, row in enumerate(dungeon_map):
        for column_index, tile in enumerate(row):
            x = MAP_OFFSET_X + column_index * TILE_SIZE
            y = MAP_OFFSET_Y + row_index * TILE_SIZE
            tile_rectangle = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            color = WALL_COLOR if tile == "#" else FLOOR_COLOR

            pygame.draw.rect(screen, color, tile_rectangle)
            pygame.draw.rect(screen, GRID_COLOR, tile_rectangle, 1)


def draw_player(screen, column, row, health):
    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
    pygame.draw.circle(
        screen,
        PLAYER_COLOR,
        (center_x, center_y),
        TILE_SIZE // 3,
    )

    health_ratio = health / PLAYER_MAX_HEALTH
    bar_x = MAP_OFFSET_X + column * TILE_SIZE + 5
    bar_y = MAP_OFFSET_Y + row * TILE_SIZE + 3
    bar_width = TILE_SIZE - 10
    bar_height = 5

    pygame.draw.rect(
        screen,
        HEALTH_BAR_BACKGROUND,
        (bar_x, bar_y, bar_width, bar_height),
    )
    pygame.draw.rect(
        screen,
        PLAYER_HEALTH_BAR_COLOR,
        (bar_x, bar_y, int(bar_width * health_ratio), bar_height),
    )


def draw_enemy(screen, enemy):
    padding = TILE_SIZE // 5
    column = enemy["column"]
    row = enemy["row"]
    x = MAP_OFFSET_X + column * TILE_SIZE + padding
    y = MAP_OFFSET_Y + row * TILE_SIZE + padding
    size = TILE_SIZE - padding * 2
    color = ENEMY_COLOR if enemy["is_aggro"] else SLEEPING_ENEMY_COLOR
    pygame.draw.rect(
        screen,
        color,
        (x, y, size, size),
        border_radius=6,
    )

    health_ratio = enemy["health"] / enemy["max_health"]
    bar_x = MAP_OFFSET_X + column * TILE_SIZE + 5
    bar_y = MAP_OFFSET_Y + row * TILE_SIZE + 3
    bar_width = TILE_SIZE - 10
    bar_height = 5

    pygame.draw.rect(
        screen,
        HEALTH_BAR_BACKGROUND,
        (bar_x, bar_y, bar_width, bar_height),
    )
    pygame.draw.rect(
        screen,
        HEALTH_BAR_COLOR,
        (bar_x, bar_y, int(bar_width * health_ratio), bar_height),
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
    enemies,
    game_won,
):
    living_enemy_count = sum(enemy["health"] > 0 for enemy in enemies)
    total_enemy_count = len(enemies)
    stairs_are_open = living_enemy_count == 0
    status = (
        f"Floor {floor_index + 1}/{len(FLOORS)}  |  "
        f"Enemies {living_enemy_count}/{total_enemy_count}  |  "
        f"Stairs {'open' if stairs_are_open else 'locked'}"
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
    elif stairs_are_open:
        message = "Enemies defeated - find the stairs"
        message_color = PLAYER_COLOR

    if message:
        message_surface = font.render(message, True, message_color)
        message_rectangle = message_surface.get_rect(
            center=(
                MAP_OFFSET_X + MAP_WIDTH // 2,
                WINDOW_HEIGHT - 38,
            )
        )
        screen.blit(message_surface, message_rectangle)


def draw_sidebar(
    screen,
    title_font,
    log_font,
    combat_log,
    player_health,
    potion_count,
    enemies_defeated,
):
    panel_rectangle = pygame.Rect(
        SIDEBAR_X,
        SIDEBAR_Y,
        SIDEBAR_WIDTH,
        SIDEBAR_HEIGHT,
    )
    pygame.draw.rect(screen, PANEL_COLOR, panel_rectangle, border_radius=8)
    pygame.draw.rect(
        screen,
        PANEL_BORDER_COLOR,
        panel_rectangle,
        width=2,
        border_radius=8,
    )

    title_surface = title_font.render("CHARACTER", True, TEXT_COLOR)
    screen.blit(title_surface, (SIDEBAR_X + 18, SIDEBAR_Y + 16))

    character_lines = [
        f"Health: {player_health}/{PLAYER_MAX_HEALTH}",
        f"Damage: {PLAYER_DAMAGE_MIN}-{PLAYER_DAMAGE_MAX}",
        f"Potions: {potion_count}",
        f"Enemies defeated: {enemies_defeated}",
    ]

    line_y = SIDEBAR_Y + 52

    for line in character_lines:
        line_surface = log_font.render(line, True, TEXT_COLOR)
        screen.blit(line_surface, (SIDEBAR_X + 18, line_y))
        line_y += 25

    divider_y = SIDEBAR_Y + 165
    pygame.draw.line(
        screen,
        PANEL_BORDER_COLOR,
        (SIDEBAR_X + 18, divider_y),
        (SIDEBAR_X + SIDEBAR_WIDTH - 18, divider_y),
        1,
    )

    events_title = title_font.render("RECENT EVENTS", True, TEXT_COLOR)
    screen.blit(events_title, (SIDEBAR_X + 18, divider_y + 18))

    line_y = divider_y + 58

    for message in combat_log:
        message_surface = log_font.render(message, True, TEXT_COLOR)
        screen.blit(message_surface, (SIDEBAR_X + 18, line_y))
        line_y += 26

    controls_y = SIDEBAR_Y + SIDEBAR_HEIGHT - 62
    controls_surface = log_font.render(
        "Move: WASD / arrows    Potion: H",
        True,
        PANEL_BORDER_COLOR,
    )
    screen.blit(controls_surface, (SIDEBAR_X + 18, controls_y))
