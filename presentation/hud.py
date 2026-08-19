import pygame

from levels import FLOOR_CONFIGS
from presentation.layout import (
    MAP_OFFSET_X,
    MAP_WIDTH,
)
from settings import (
    ENEMY_COLOR,
    GAME_HEIGHT,
    GAME_WIDTH,
    PLAYER_COLOR,
    TEXT_COLOR,
)


_ACT_ONE_HUD_FRAME_RECT = pygame.Rect(25, 23, 466, 121)
_ACT_ONE_HEALTH_RECT = pygame.Rect(84, 65, 389, 34)
_ACT_ONE_BOTTOM_BAR_RECT = pygame.Rect(272, 495, 736, 245)
_ACT_ONE_HEALTH_TEXT_CENTER = (297, 82)
_ACT_ONE_LOG_POSITION = (320, 611)
_ACT_ONE_BELT_SLOT_CENTERS = tuple(
    (626 + slot_index * 65, 642)
    for slot_index in range(6)
)


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
    act_floor = floor_config["act_floor"]
    act_floor_count = sum(
        config["act"] == act_number
        for config in FLOOR_CONFIGS
    )
    living_enemy_count = sum(enemy["health"] > 0 for enemy in enemies)
    total_enemy_count = len(enemies)
    stairs_are_open = living_enemy_count == 0
    displayed_map_left = (
        (GAME_WIDTH - MAP_WIDTH) // 2
        if act_number in (1, 2)
        else MAP_OFFSET_X
    )
    if act_number in (1, 2):
        status = (
            f"ACT {'I' if act_number == 1 else 'II'}"
            f"  ·  FLOOR {act_floor}/{act_floor_count}"
        )
        status_surface = font.render(status, True, TEXT_COLOR)
        screen.blit(
            status_surface,
            status_surface.get_rect(midtop=(GAME_WIDTH // 2, 8)),
        )
    else:
        status = (
            f"Act {act_number} - Floor {act_floor}/{act_floor_count}  |  "
            f"Enemies {living_enemy_count}/{total_enemy_count}  |  "
            f"Stairs {'open' if stairs_are_open else 'locked'}"
        )
        screen.blit(font.render(status, True, TEXT_COLOR), (MAP_OFFSET_X, 8))

    living_boss = next(
        (
            enemy
            for enemy in enemies
            if (
                enemy["type"] in ("warden", "oracle")
                and enemy["health"] > 0
                and enemy["is_active"]
            )
        ),
        None,
    )

    if living_boss:
        phase = (
            2
            if living_boss["health"]
            <= living_boss["max_health"] // 2
            else 1
        )

        if living_boss["type"] == "oracle":
            boss_state = (
                "AWAKENED"
                if living_boss["oracle_awakened"]
                else "DORMANT"
            )
            boss_label = (
                f"ORACLE - {boss_state}  |  PHASE {phase}"
            )
            label_surface = font.render(
                boss_label,
                True,
                living_boss["color"],
            )
            screen.blit(
                label_surface,
                label_surface.get_rect(
                    center=(
                        displayed_map_left + MAP_WIDTH // 2,
                        55,
                    )
                ),
            )
            boss_bar_width = min(640, MAP_WIDTH - 120)
            boss_bar_height = 22
            boss_bar_left = (
                displayed_map_left
                + (MAP_WIDTH - boss_bar_width) // 2
            )
            boss_bar_top = 75
            boss_health_ratio = (
                living_boss["health"]
                / living_boss["max_health"]
            )
            pygame.draw.rect(
                screen,
                (24, 20, 27),
                (
                    boss_bar_left,
                    boss_bar_top,
                    boss_bar_width,
                    boss_bar_height,
                ),
            )
            pygame.draw.rect(
                screen,
                (
                    (65, 175, 225)
                    if living_boss["oracle_awakened"]
                    else (72, 108, 138)
                ),
                (
                    boss_bar_left + 3,
                    boss_bar_top + 3,
                    int(
                        (boss_bar_width - 6)
                        * boss_health_ratio
                    ),
                    boss_bar_height - 6,
                ),
            )
            pygame.draw.rect(
                screen,
                (130, 142, 158),
                (
                    boss_bar_left,
                    boss_bar_top,
                    boss_bar_width,
                    boss_bar_height,
                ),
                width=2,
            )
            health_surface = font.render(
                (
                    f"{living_boss['health']} / "
                    f"{living_boss['max_health']}"
                ),
                True,
                (235, 238, 242),
            )
            screen.blit(
                health_surface,
                health_surface.get_rect(
                    center=(
                        boss_bar_left + boss_bar_width // 2,
                        boss_bar_top + boss_bar_height // 2,
                    )
                ),
            )
        else:
            boss_status = (
                f"{living_boss['name'].upper()}  |  "
                f"{living_boss['health']}/"
                f"{living_boss['max_health']} HP  |  "
                f"PHASE {phase}"
            )
            boss_color = (
                (205, 74, 105)
                if phase == 2
                else living_boss["color"]
            )
            boss_surface = font.render(
                boss_status,
                True,
                boss_color,
            )
            screen.blit(
                boss_surface,
                boss_surface.get_rect(
                    center=(displayed_map_left + MAP_WIDTH // 2, 57)
                ),
            )
            boss_bar_width = 500
            boss_bar_height = 14
            boss_bar_left = (
                displayed_map_left + (MAP_WIDTH - boss_bar_width) // 2
            )
            boss_bar_top = 77
            health_ratio = (
                living_boss["health"] / living_boss["max_health"]
            )
            pygame.draw.rect(
                screen,
                (18, 14, 21),
                (boss_bar_left, boss_bar_top, boss_bar_width, boss_bar_height),
                border_radius=3,
            )
            pygame.draw.rect(
                screen,
                boss_color,
                (
                    boss_bar_left + 2,
                    boss_bar_top + 2,
                    round((boss_bar_width - 4) * health_ratio),
                    boss_bar_height - 4,
                ),
                border_radius=2,
            )
            pygame.draw.rect(
                screen,
                (94, 83, 99),
                (boss_bar_left, boss_bar_top, boss_bar_width, boss_bar_height),
                width=1,
                border_radius=3,
            )
            pygame.draw.line(
                screen,
                (28, 22, 31),
                (boss_bar_left + boss_bar_width // 2, boss_bar_top + 1),
                (
                    boss_bar_left + boss_bar_width // 2,
                    boss_bar_top + boss_bar_height - 2,
                ),
                2,
            )

            prepared_mode = living_boss.get("prepared_attack_mode")
            if living_boss["attack_targets"] and prepared_mode:
                mode_colors = {
                    "cross": (230, 79, 86),
                    "sweep": (235, 135, 57),
                    "runes": (190, 95, 214),
                }
                warning_surface = font.render(
                    f"PREPARING {prepared_mode.upper()}",
                    True,
                    mode_colors.get(prepared_mode, boss_color),
                )
                screen.blit(
                    warning_surface,
                    warning_surface.get_rect(
                        center=(displayed_map_left + MAP_WIDTH // 2, 104)
                    ),
                )

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
        message_center_y = 552 if act_number == 2 else GAME_HEIGHT - 38
        message_rectangle = message_surface.get_rect(
            center=(
                displayed_map_left + MAP_WIDTH // 2,
                message_center_y,
            )
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


def get_event_color(message):
    lower_message = message.lower()

    if "hits hero" in lower_message or "fallen" in lower_message:
        return (220, 85, 90)
    if "critical" in lower_message:
        return (245, 195, 75)
    if "hero hits" in lower_message or "defeated" in lower_message:
        return (218, 165, 75)
    if (
        "picks up" in lower_message
        or "heals" in lower_message
        or "found" in lower_message
        or "drops a key" in lower_message
    ):
        return (100, 190, 135)
    if "dodges" in lower_message:
        return (100, 175, 205)
    if "prepares" in lower_message or "spots" in lower_message:
        return (205, 125, 75)

    return TEXT_COLOR


def fit_text_to_width(font, text, maximum_width):
    if font.size(text)[0] <= maximum_width:
        return text

    ellipsis = "..."
    shortened_text = text

    while (
        shortened_text
        and font.size(shortened_text + ellipsis)[0]
        > maximum_width
    ):
        shortened_text = shortened_text[:-1]

    return shortened_text.rstrip() + ellipsis


def wrap_text(font, text, maximum_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        candidate = (
            f"{current_line} {word}"
            if current_line
            else word
        )

        if font.size(candidate)[0] <= maximum_width:
            current_line = candidate
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def get_class_selection_rectangles():
    card_width = 300
    card_height = 300
    gap = 30
    total_width = card_width * 3 + gap * 2
    start_x = (GAME_WIDTH - total_width) // 2
    card_y = 365

    return {
        class_name: pygame.Rect(
            start_x + index * (card_width + gap),
            card_y,
            card_width,
            card_height,
        )
        for index, class_name in enumerate(
            ("warrior", "rogue", "mage")
        )
    }


def draw_sidebar(
    screen,
    title_font,
    log_font,
    combat_log,
    player_health,
    player_max_health,
    potion_count,
    sprites,
):
    health_ratio = max(
        0.0,
        min(1.0, player_health / max(1, player_max_health)),
    )
    health_fill = sprites.get("act_one_health_fill")
    fill_width = round(_ACT_ONE_HEALTH_RECT.width * health_ratio)
    if health_fill is not None and fill_width > 0:
        screen.blit(
            health_fill,
            _ACT_ONE_HEALTH_RECT,
            pygame.Rect(
                0,
                0,
                fill_width,
                _ACT_ONE_HEALTH_RECT.height,
            ),
        )

    hud_frame = sprites.get("act_one_hud_frame")
    if hud_frame is not None:
        screen.blit(hud_frame, _ACT_ONE_HUD_FRAME_RECT)

    health_surface = title_font.render(
        f"{player_health}/{player_max_health}",
        True,
        (236, 236, 230),
    )
    screen.blit(
        health_surface,
        health_surface.get_rect(center=_ACT_ONE_HEALTH_TEXT_CENTER),
    )

    bottom_bar = sprites.get("act_one_bottom_bar")
    if bottom_bar is not None:
        screen.blit(bottom_bar, _ACT_ONE_BOTTOM_BAR_RECT)

    log_y = _ACT_ONE_LOG_POSITION[1]
    for message in combat_log[-3:]:
        visible_message = fit_text_to_width(log_font, message, 246)
        message_surface = log_font.render(
            visible_message,
            True,
            get_event_color(message),
        )
        screen.blit(message_surface, (_ACT_ONE_LOG_POSITION[0], log_y))
        log_y += 20

    potion_sprite = sprites.get("act_one_potion")
    if potion_sprite is not None:
        for slot_center in _ACT_ONE_BELT_SLOT_CENTERS[
            :min(potion_count, len(_ACT_ONE_BELT_SLOT_CENTERS))
        ]:
            screen.blit(
                potion_sprite,
                potion_sprite.get_rect(center=slot_center),
            )
