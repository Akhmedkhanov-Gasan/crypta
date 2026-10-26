import pygame

from levels import FLOOR_CONFIGS
from presentation.floor_progress import draw_floor_indicator
from presentation.layout import MAP_OFFSET_X, MAP_WIDTH
from settings import GAME_HEIGHT, GAME_WIDTH, PLAYER_COLOR, TEXT_COLOR


def draw_status(
    screen,
    font,
    floor_index,
    player_health,
    enemies,
    game_won,
):
    floor_config = FLOOR_CONFIGS[floor_index]
    act_number = floor_config["act"]
    displayed_map_left = (
        (GAME_WIDTH - MAP_WIDTH) // 2
        if act_number in (1, 2)
        else MAP_OFFSET_X
    )
    oracle_panel_visible = (
        act_number == 2
        and any(
            enemy["type"] == "oracle"
            and enemy["health"] > 0
            and enemy["is_active"]
            for enemy in enemies
        )
    )

    if act_number in (1, 2) and not oracle_panel_visible:
        draw_floor_indicator(
            screen,
            font,
            floor_index,
            GAME_WIDTH // 2,
            top=4,
        )

    message = None
    message_color = TEXT_COLOR

    if game_won:
        message = "Victory - press R to restart"
        message_color = PLAYER_COLOR

    if message:
        message_surface = font.render(message, True, message_color)
        message_center_y = 552 if act_number == 2 else GAME_HEIGHT - 38
        message_rectangle = message_surface.get_rect(
            center=(
                displayed_map_left + MAP_WIDTH // 2,
                message_center_y,
            ),
        )

        if act_number == 2:
            message_backing = message_rectangle.inflate(28, 14)
            backing_surface = pygame.Surface(
                message_backing.size,
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                backing_surface,
                (8, 8, 11, 210),
                backing_surface.get_rect(),
                border_radius=5,
            )
            pygame.draw.rect(
                backing_surface,
                (101, 91, 88, 210),
                backing_surface.get_rect(),
                width=1,
                border_radius=5,
            )
            screen.blit(backing_surface, message_backing)

        screen.blit(message_surface, message_rectangle)
