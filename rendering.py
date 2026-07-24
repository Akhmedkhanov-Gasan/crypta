from pathlib import Path

import pygame

from levels import FLOOR_CONFIGS
from settings import (
    ATTACK_WARNING_COLOR,
    CHEST_BAND_COLOR,
    CHEST_COLOR,
    DANGER_BORDER_COLOR,
    DANGER_TILE_COLOR,
    ENEMY_COLOR,
    FLOOR_COLOR,
    GAME_HEIGHT,
    GAME_WIDTH,
    GOLD_COLOR,
    GRID_COLOR,
    HEALTH_BAR_BACKGROUND,
    HEALTH_BAR_COLOR,
    KEY_COLOR,
    LOCKED_COLOR,
    MAP_COLUMNS,
    MAP_ROWS,
    OPEN_CHEST_COLOR,
    PANEL_BORDER_COLOR,
    PANEL_COLOR,
    PLAYER_ATTACK_BORDER_COLOR,
    PLAYER_ATTACK_TILE_COLOR,
    PLAYER_COLOR,
    PLAYER_HEALTH_BAR_COLOR,
    POTION_COLOR,
    STAIRS_COLOR,
    TEXT_COLOR,
    TILE_SIZE,
    WALL_COLOR,
)


MAP_WIDTH = MAP_COLUMNS * TILE_SIZE
MAP_HEIGHT = MAP_ROWS * TILE_SIZE
MAP_OFFSET_X = 40
MAP_OFFSET_Y = (GAME_HEIGHT - MAP_HEIGHT) // 2
SIDEBAR_X = MAP_OFFSET_X + MAP_WIDTH + 40
SIDEBAR_Y = MAP_OFFSET_Y
SIDEBAR_WIDTH = GAME_WIDTH - SIDEBAR_X - 40
SIDEBAR_HEIGHT = MAP_HEIGHT
ASSET_ROOT = Path(__file__).resolve().parent / "assets" / "sprites"
FONT_ROOT = Path(__file__).resolve().parent / "assets" / "fonts"
AWAKENING_OPEN_START_MS = 300
AWAKENING_OPEN_END_MS = 1500
AWAKENING_HOLD_END_MS = 2500
AWAKENING_FADE_END_MS = 3100
CLASS_SELECTION_READY_MS = 6600


def load_act_one_fonts():
    regular_path = FONT_ROOT / "PixelOperator.ttf"
    bold_path = FONT_ROOT / "PixelOperator-Bold.ttf"

    return {
        "title": pygame.font.Font(str(bold_path), 44),
        "heading": pygame.font.Font(str(bold_path), 28),
        "status": pygame.font.Font(str(bold_path), 24),
        "text": pygame.font.Font(str(regular_path), 20),
        "controls": pygame.font.Font(str(bold_path), 19),
    }


def load_act_two_fonts():
    regular_path = FONT_ROOT / "Almendra-Regular.ttf"
    bold_path = FONT_ROOT / "Almendra-Bold.ttf"

    return {
        "title": pygame.font.Font(str(bold_path), 42),
        "heading": pygame.font.Font(str(bold_path), 25),
        "status": pygame.font.Font(str(bold_path), 24),
        "text": pygame.font.Font(str(regular_path), 18),
        "controls": pygame.font.Font(str(bold_path), 18),
    }


def load_act_two_sprites():
    asset_directory = ASSET_ROOT / "act_2"
    ui_directory = ASSET_ROOT / "ui" / "act_2"
    sprite_names = (
        "player_warrior",
        "player_rogue",
        "player_mage",
        "goblin",
        "brute",
        "archer",
        "potion",
        "key",
        "coin",
        "chest_closed",
        "chest_open",
        "stairs_locked",
        "stairs_open",
        "floor",
        "wall",
        "sentinel_idle",
        "sentinel_guard",
        "priest_idle",
        "priest_cast",
    )

    sprites = {
        name: pygame.transform.scale(
            pygame.image.load(
                str(asset_directory / f"{name}.png")
            ).convert_alpha(),
            (TILE_SIZE, TILE_SIZE),
        )
        for name in sprite_names
    }
    sprites["floor"].fill(
        (150, 145, 160),
        special_flags=pygame.BLEND_RGB_MULT,
    )
    sprites["wall"].fill(
        (10, 12, 16),
        special_flags=pygame.BLEND_RGB_ADD,
    )
    awakening_source = pygame.image.load(
        str(ui_directory / "awakening.png")
    ).convert()
    source_width, source_height = awakening_source.get_size()
    target_ratio = GAME_WIDTH / GAME_HEIGHT
    source_ratio = source_width / source_height

    if source_ratio > target_ratio:
        crop_width = int(source_height * target_ratio)
        crop_rectangle = pygame.Rect(
            (source_width - crop_width) // 2,
            0,
            crop_width,
            source_height,
        )
    else:
        crop_height = int(source_width / target_ratio)
        crop_rectangle = pygame.Rect(
            0,
            (source_height - crop_height) // 2,
            source_width,
            crop_height,
        )

    awakening_small = pygame.transform.smoothscale(
        awakening_source.subsurface(crop_rectangle),
        (320, 180),
    )

    if hasattr(pygame.transform, "grayscale"):
        awakening_gray = pygame.transform.grayscale(
            awakening_small
        )
        awakening_gray.set_alpha(75)
        awakening_small.blit(awakening_gray, (0, 0))

    awakening_small.fill(
        (145, 140, 160),
        special_flags=pygame.BLEND_RGB_MULT,
    )
    sprites["awakening"] = pygame.transform.scale(
        awakening_small,
        (GAME_WIDTH, GAME_HEIGHT),
    )

    for class_name in ("warrior", "rogue", "mage"):
        sprites[f"{class_name}_portrait"] = pygame.image.load(
            str(
                ui_directory
                / f"{class_name}_portrait.png"
            )
        ).convert_alpha()

    return sprites


def draw_dungeon(screen, dungeon_map, act_number, sprites):
    for row_index, row in enumerate(dungeon_map):
        for column_index, tile in enumerate(row):
            x = MAP_OFFSET_X + column_index * TILE_SIZE
            y = MAP_OFFSET_Y + row_index * TILE_SIZE
            tile_rectangle = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            if act_number >= 2:
                texture_name = "wall" if tile == "#" else "floor"
                screen.blit(sprites[texture_name], tile_rectangle)
            else:
                color = WALL_COLOR if tile == "#" else FLOOR_COLOR
                pygame.draw.rect(screen, color, tile_rectangle)

            pygame.draw.rect(screen, GRID_COLOR, tile_rectangle, 1)


def draw_map_frame(screen, act_number):
    if act_number < 2:
        return

    outer_rectangle = pygame.Rect(
        MAP_OFFSET_X - 4,
        MAP_OFFSET_Y - 4,
        MAP_WIDTH + 8,
        MAP_HEIGHT + 8,
    )
    pygame.draw.rect(
        screen,
        (72, 68, 78),
        outer_rectangle,
        width=3,
    )
    pygame.draw.rect(
        screen,
        (30, 27, 34),
        outer_rectangle.inflate(-6, -6),
        width=1,
    )


def draw_attack_markers(screen, enemies):
    for enemy in enemies:
        if enemy["health"] <= 0:
            continue

        for column, row in enemy["attack_targets"]:
            target_rectangle = pygame.Rect(
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
            )
            pygame.draw.rect(screen, DANGER_TILE_COLOR, target_rectangle)
            pygame.draw.rect(
                screen,
                DANGER_BORDER_COLOR,
                target_rectangle,
                width=3,
            )


def draw_player_attack_markers(screen, attack_targets):
    for column, row in attack_targets:
        target_rectangle = pygame.Rect(
            MAP_OFFSET_X + column * TILE_SIZE,
            MAP_OFFSET_Y + row * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(
            screen,
            PLAYER_ATTACK_TILE_COLOR,
            target_rectangle,
        )
        pygame.draw.rect(
            screen,
            PLAYER_ATTACK_BORDER_COLOR,
            target_rectangle,
            width=3,
        )


def draw_player(
    screen,
    column,
    row,
    health,
    max_health,
    player_class,
    act_number,
    sprites,
    invisibility_turns,
):
    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
    if act_number >= 2 and player_class is not None:
        player_sprite = sprites[f"player_{player_class}"]

        if invisibility_turns > 0:
            player_sprite = player_sprite.copy()
            player_sprite.set_alpha(90)

        screen.blit(
            player_sprite,
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
    else:
        pygame.draw.circle(
            screen,
            PLAYER_COLOR,
            (center_x, center_y),
            TILE_SIZE // 3,
        )

    health_ratio = health / max_health
    bar_x = MAP_OFFSET_X + column * TILE_SIZE + 4
    bar_y = MAP_OFFSET_Y + (row + 1) * TILE_SIZE - 5
    bar_width = TILE_SIZE - 8
    bar_height = 4

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


def draw_enemy(screen, enemy, act_number, sprites):
    padding = TILE_SIZE // 5
    column = enemy["column"]
    row = enemy["row"]
    x = MAP_OFFSET_X + column * TILE_SIZE + padding
    y = MAP_OFFSET_Y + row * TILE_SIZE + padding
    size = TILE_SIZE - padding * 2
    color = (
        enemy["color"]
        if enemy["is_aggro"]
        else enemy["sleeping_color"]
    )

    if (
        act_number >= 2
        and enemy["type"] in (
            "goblin",
            "brute",
            "archer",
            "sentinel",
            "priest",
        )
    ):
        sprite_name = enemy["type"]

        if enemy["type"] == "sentinel":
            sprite_name = (
                "sentinel_guard"
                if enemy["shield_turns"] > 0
                else "sentinel_idle"
            )
        elif enemy["type"] == "priest":
            sprite_name = (
                "priest_cast"
                if (
                    enemy["attack_targets"]
                    or enemy["heal_target"] is not None
                )
                else "priest_idle"
            )

        enemy_sprite = sprites[sprite_name]

        screen.blit(
            enemy_sprite,
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )

        if (
            enemy["type"] == "sentinel"
            and enemy["shield_turns"] > 0
        ):
            opening_color = (235, 185, 75)
            tile_left = MAP_OFFSET_X + column * TILE_SIZE
            tile_top = MAP_OFFSET_Y + row * TILE_SIZE
            shield_direction = enemy["shield_direction"]
            vulnerable_direction = (
                -shield_direction[0],
                -shield_direction[1],
            )
            opening_lines = {
                (0, -1): (
                    (tile_left + 5, tile_top + 3),
                    (tile_left + TILE_SIZE - 5, tile_top + 3),
                ),
                (0, 1): (
                    (tile_left + 5, tile_top + TILE_SIZE - 3),
                    (
                        tile_left + TILE_SIZE - 5,
                        tile_top + TILE_SIZE - 3,
                    ),
                ),
                (-1, 0): (
                    (tile_left + 3, tile_top + 5),
                    (tile_left + 3, tile_top + TILE_SIZE - 5),
                ),
                (1, 0): (
                    (tile_left + TILE_SIZE - 3, tile_top + 5),
                    (
                        tile_left + TILE_SIZE - 3,
                        tile_top + TILE_SIZE - 5,
                    ),
                ),
            }
            opening_line = opening_lines.get(
                vulnerable_direction
            )

            if opening_line is not None:
                pygame.draw.line(
                    screen,
                    opening_color,
                    opening_line[0],
                    opening_line[1],
                    3,
                )

        if (
            enemy["type"] == "priest"
            and enemy["heal_target"] is not None
            and enemy["heal_target"]["health"] > 0
        ):
            heal_target = enemy["heal_target"]
            pygame.draw.rect(
                screen,
                (80, 220, 130),
                (
                    MAP_OFFSET_X
                    + heal_target["column"] * TILE_SIZE
                    + 3,
                    MAP_OFFSET_Y
                    + heal_target["row"] * TILE_SIZE
                    + 3,
                    TILE_SIZE - 6,
                    TILE_SIZE - 6,
                ),
                width=2,
                border_radius=4,
            )

        if enemy["is_aggro"]:
            pygame.draw.rect(
                screen,
                DANGER_BORDER_COLOR,
                (
                    MAP_OFFSET_X + column * TILE_SIZE + 2,
                    MAP_OFFSET_Y + row * TILE_SIZE + 2,
                    TILE_SIZE - 4,
                    TILE_SIZE - 4,
                ),
                width=2,
                border_radius=3,
            )
    elif enemy["type"] == "brute":
        corner = 4
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + corner, y),
                (x + size - corner, y),
                (x + size, y + corner),
                (x + size, y + size - corner),
                (x + size - corner, y + size),
                (x + corner, y + size),
                (x, y + size - corner),
                (x, y + corner),
            ],
        )
    elif enemy["type"] == "archer":
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + size // 2, y),
                (x + size, y + size),
                (x, y + size),
            ],
        )
    elif enemy["type"] == "warden":
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + size // 2, y),
                (x + size, y + size // 2),
                (x + size // 2, y + size),
                (x, y + size // 2),
            ],
        )
        crown_y = y + size // 4
        pygame.draw.line(
            screen,
            ATTACK_WARNING_COLOR,
            (x + size // 4, crown_y),
            (x + size * 3 // 4, crown_y),
            2,
        )
        pygame.draw.circle(
            screen,
            ATTACK_WARNING_COLOR,
            (x + size // 2, y + size // 2),
            3,
        )
    else:
        pygame.draw.rect(
            screen,
            color,
            (x, y, size, size),
            border_radius=6,
        )

    health_ratio = enemy["health"] / enemy["max_health"]
    bar_x = MAP_OFFSET_X + column * TILE_SIZE + 4
    bar_y = MAP_OFFSET_Y + (row + 1) * TILE_SIZE - 5
    bar_width = TILE_SIZE - 8
    bar_height = 4

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

    if enemy["attack_targets"]:
        warning_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
        warning_top = MAP_OFFSET_Y + row * TILE_SIZE + 8
        pygame.draw.line(
            screen,
            ATTACK_WARNING_COLOR,
            (warning_x, warning_top),
            (warning_x, warning_top + 9),
            3,
        )
        pygame.draw.circle(
            screen,
            ATTACK_WARNING_COLOR,
            (warning_x, warning_top + 14),
            2,
        )


def draw_key(screen, column, row, act_number, sprites):
    if act_number >= 2:
        screen.blit(
            sprites["key"],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
        return

    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2

    pygame.draw.circle(
        screen,
        KEY_COLOR,
        (center_x - 8, center_y),
        6,
        width=3,
    )
    pygame.draw.line(
        screen,
        KEY_COLOR,
        (center_x - 2, center_y),
        (center_x + 13, center_y),
        4,
    )
    pygame.draw.line(
        screen,
        KEY_COLOR,
        (center_x + 7, center_y),
        (center_x + 7, center_y + 6),
        3,
    )
    pygame.draw.line(
        screen,
        KEY_COLOR,
        (center_x + 12, center_y),
        (center_x + 12, center_y + 5),
        3,
    )


def draw_boss_door(screen, column, row, is_open):
    cell_x = MAP_OFFSET_X + column * TILE_SIZE
    cell_y = MAP_OFFSET_Y + row * TILE_SIZE
    frame_color = (115, 75, 130)

    pygame.draw.rect(
        screen,
        frame_color,
        (cell_x + 3, cell_y + 2, TILE_SIZE - 6, TILE_SIZE - 4),
        width=3,
        border_radius=3,
    )

    if is_open:
        return

    pygame.draw.rect(
        screen,
        (55, 35, 62),
        (cell_x + 7, cell_y + 5, TILE_SIZE - 14, TILE_SIZE - 7),
        border_radius=2,
    )
    pygame.draw.line(
        screen,
        frame_color,
        (cell_x + TILE_SIZE // 2, cell_y + 7),
        (cell_x + TILE_SIZE // 2, cell_y + TILE_SIZE - 5),
        2,
    )
    pygame.draw.circle(
        screen,
        ATTACK_WARNING_COLOR,
        (cell_x + TILE_SIZE // 2, cell_y + TILE_SIZE // 2),
        3,
    )


def draw_potion(screen, column, row, act_number, sprites):
    if act_number >= 2:
        screen.blit(
            sprites["potion"],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
        return

    cell_x = MAP_OFFSET_X + column * TILE_SIZE
    cell_y = MAP_OFFSET_Y + row * TILE_SIZE
    bottle_rectangle = pygame.Rect(
        cell_x + TILE_SIZE // 2 - 6,
        cell_y + 12,
        12,
        15,
    )

    pygame.draw.rect(
        screen,
        POTION_COLOR,
        bottle_rectangle,
        border_radius=4,
    )
    pygame.draw.rect(
        screen,
        TEXT_COLOR,
        (cell_x + TILE_SIZE // 2 - 3, cell_y + 8, 6, 6),
        border_radius=2,
    )


def draw_coin(screen, column, row, act_number, sprites):
    if act_number >= 2:
        screen.blit(
            sprites["coin"],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
        return

    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2

    pygame.draw.circle(
        screen,
        GOLD_COLOR,
        (center_x, center_y),
        7,
    )
    pygame.draw.circle(
        screen,
        KEY_COLOR,
        (center_x, center_y),
        7,
        width=2,
    )
    pygame.draw.line(
        screen,
        KEY_COLOR,
        (center_x, center_y - 3),
        (center_x, center_y + 3),
        2,
    )


def draw_chest(screen, chest, act_number, sprites):
    cell_x = MAP_OFFSET_X + chest["column"] * TILE_SIZE
    cell_y = MAP_OFFSET_Y + chest["row"] * TILE_SIZE

    if act_number >= 2:
        sprite_name = (
            "chest_open"
            if chest["is_open"]
            else "chest_closed"
        )
        screen.blit(sprites[sprite_name], (cell_x, cell_y))
        return

    if chest["is_open"]:
        pygame.draw.rect(
            screen,
            OPEN_CHEST_COLOR,
            (cell_x + 4, cell_y + 17, TILE_SIZE - 8, 11),
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            CHEST_COLOR,
            (cell_x + 4, cell_y + 6, TILE_SIZE - 8, 7),
            border_radius=3,
        )
        return

    pygame.draw.rect(
        screen,
        CHEST_COLOR,
        (cell_x + 4, cell_y + 9, TILE_SIZE - 8, 19),
        border_radius=4,
    )
    pygame.draw.rect(
        screen,
        CHEST_BAND_COLOR,
        (cell_x + TILE_SIZE // 2 - 3, cell_y + 9, 6, 19),
    )
    pygame.draw.rect(
        screen,
        KEY_COLOR,
        (cell_x + TILE_SIZE // 2 - 2, cell_y + 17, 4, 7),
        border_radius=2,
    )


def draw_stairs(
    screen,
    column,
    row,
    is_open,
    act_number,
    sprites,
):
    if act_number >= 2:
        sprite_name = (
            "stairs_open" if is_open else "stairs_locked"
        )
        screen.blit(
            sprites[sprite_name],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
        return

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
    status = (
        f"Act {act_number} - Floor {act_floor}/{act_floor_count}  |  "
        f"Enemies {living_enemy_count}/{total_enemy_count}  |  "
        f"Stairs {'open' if stairs_are_open else 'locked'}"
    )
    screen.blit(font.render(status, True, TEXT_COLOR), (MAP_OFFSET_X, 28))

    living_warden = next(
        (
            enemy
            for enemy in enemies
            if (
                enemy["type"] == "warden"
                and enemy["health"] > 0
                and enemy["is_active"]
            )
        ),
        None,
    )

    if living_warden:
        phase = (
            2
            if living_warden["health"]
            <= living_warden["max_health"] // 2
            else 1
        )
        boss_status = (
            f"CRYPT WARDEN  "
            f"{living_warden['health']}/{living_warden['max_health']} HP  "
            f"|  Phase {phase}"
        )
        screen.blit(
            font.render(
                boss_status,
                True,
                living_warden["color"],
            ),
            (MAP_OFFSET_X, 55),
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
        message_rectangle = message_surface.get_rect(
            center=(
                MAP_OFFSET_X + MAP_WIDTH // 2,
                GAME_HEIGHT - 38,
            )
        )
        screen.blit(message_surface, message_rectangle)


def draw_pixel_section(screen, rectangle):
    pygame.draw.rect(screen, (24, 21, 27), rectangle)
    pygame.draw.rect(
        screen,
        (66, 61, 70),
        rectangle,
        width=2,
    )
    pygame.draw.line(
        screen,
        (92, 84, 96),
        (rectangle.left + 2, rectangle.top + 2),
        (rectangle.right - 3, rectangle.top + 2),
        1,
    )


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
    card_width = 330
    card_height = 370
    gap = 20
    total_width = card_width * 3 + gap * 2
    start_x = (GAME_WIDTH - total_width) // 2
    card_y = 270

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


def draw_act_two_sidebar(
    screen,
    title_font,
    log_font,
    controls_font,
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
    sprites,
):
    panel_rectangle = pygame.Rect(
        SIDEBAR_X,
        SIDEBAR_Y,
        SIDEBAR_WIDTH,
        SIDEBAR_HEIGHT,
    )
    pygame.draw.rect(screen, (16, 14, 18), panel_rectangle)
    pygame.draw.rect(
        screen,
        (82, 75, 86),
        panel_rectangle,
        width=3,
    )
    pygame.draw.rect(
        screen,
        (35, 31, 39),
        panel_rectangle.inflate(-8, -8),
        width=1,
    )

    class_colors = {
        "warrior": (190, 70, 65),
        "rogue": (135, 75, 175),
        "mage": (70, 110, 195),
    }
    class_color = class_colors.get(
        player_class,
        PLAYER_HEALTH_BAR_COLOR,
    )
    portrait_rectangle = pygame.Rect(
        SIDEBAR_X + 14,
        SIDEBAR_Y + 14,
        44,
        44,
    )
    draw_pixel_section(screen, portrait_rectangle)

    if player_class is not None:
        screen.blit(
            sprites[f"player_{player_class}"],
            (SIDEBAR_X + 20, SIDEBAR_Y + 20),
        )

    class_name = (
        player_class.upper()
        if player_class is not None
        else "UNCHOOSEN"
    )
    screen.blit(
        title_font.render(class_name, True, class_color),
        (SIDEBAR_X + 70, SIDEBAR_Y + 5),
    )

    health_text = f"HP {player_health}/{player_max_health}"
    health_surface = log_font.render(
        health_text,
        True,
        TEXT_COLOR,
    )
    health_rectangle = health_surface.get_rect(
        midleft=(SIDEBAR_X + 70, SIDEBAR_Y + 51),
    )
    health_bar_x = health_rectangle.right + 8
    health_bar_rectangle = pygame.Rect(
        health_bar_x,
        SIDEBAR_Y + 42,
        SIDEBAR_X + SIDEBAR_WIDTH - 18 - health_bar_x,
        18,
    )
    pygame.draw.rect(
        screen,
        HEALTH_BAR_BACKGROUND,
        health_bar_rectangle,
    )
    health_ratio = max(
        0,
        min(1, player_health / player_max_health),
    )
    pygame.draw.rect(
        screen,
        class_color,
        (
            health_bar_rectangle.x,
            health_bar_rectangle.y,
            int(health_bar_rectangle.width * health_ratio),
            health_bar_rectangle.height,
        ),
    )
    pygame.draw.rect(
        screen,
        (105, 95, 108),
        health_bar_rectangle,
        width=2,
    )
    screen.blit(
        health_surface,
        health_rectangle,
    )

    stats_rectangle = pygame.Rect(
        SIDEBAR_X + 10,
        SIDEBAR_Y + 68,
        SIDEBAR_WIDTH - 20,
        50,
    )
    draw_pixel_section(screen, stats_rectangle)
    stats = (
        f"DMG {player_damage_min}-{player_damage_max}"
        f"    CRIT {round(player_crit_chance * 100)}%"
        f"    DODGE {round(player_dodge_chance * 100)}%"
    )
    screen.blit(
        log_font.render(stats, True, TEXT_COLOR),
        (stats_rectangle.x + 10, stats_rectangle.y + 8),
    )
    defeated_text = f"Defeated: {enemies_defeated}"
    screen.blit(
        log_font.render(
            defeated_text,
            True,
            PANEL_BORDER_COLOR,
        ),
        (stats_rectangle.x + 10, stats_rectangle.y + 27),
    )

    ability_rectangle = pygame.Rect(
        SIDEBAR_X + 10,
        SIDEBAR_Y + 126,
        SIDEBAR_WIDTH - 20,
        68,
    )
    draw_pixel_section(screen, ability_rectangle)
    ability_names = {
        "warrior": "POWER STRIKE",
        "rogue": "INVISIBILITY",
        "mage": "ARCANE BURST",
    }
    ability_descriptions = {
        "warrior": "E + direction | heavy melee hit",
        "rogue": "E | vanish, first hit is critical",
        "mage": "E + direction | magic line",
    }
    ability_name = ability_names.get(player_class, "ABILITY")
    screen.blit(
        title_font.render(ability_name, True, class_color),
        (ability_rectangle.x + 10, ability_rectangle.y + 7),
    )

    for charge_index in range(2):
        charge_rectangle = pygame.Rect(
            ability_rectangle.right - 48 + charge_index * 18,
            ability_rectangle.y + 10,
            12,
            12,
        )
        pygame.draw.rect(
            screen,
            (
                class_color
                if charge_index < ability_kill_charge
                else (43, 38, 46)
            ),
            charge_rectangle,
        )
        pygame.draw.rect(
            screen,
            (105, 95, 108),
            charge_rectangle,
            width=1,
        )

    if invisibility_turns > 0:
        ability_description = (
            f"INVISIBLE: {invisibility_turns} turns"
        )
    elif directional_ability_aiming:
        ability_description = "CHOOSE A DIRECTION"
    else:
        ability_description = ability_descriptions.get(
            player_class,
            "Defeat enemies to charge",
        )
    screen.blit(
        log_font.render(
            ability_description,
            True,
            TEXT_COLOR,
        ),
        (ability_rectangle.x + 10, ability_rectangle.y + 39),
    )

    inventory_rectangle = pygame.Rect(
        SIDEBAR_X + 10,
        SIDEBAR_Y + 202,
        SIDEBAR_WIDTH - 20,
        50,
    )
    draw_pixel_section(screen, inventory_rectangle)
    inventory_items = [
        ("potion", str(potion_count)),
        ("coin", str(gold_count)),
        ("key", str(key_count)),
    ]

    for item_index, (sprite_name, value) in enumerate(
        inventory_items
    ):
        item_x = inventory_rectangle.x + 8 + item_index * 108
        item_sprite = sprites[sprite_name]

        if sprite_name == "key" and key_count <= 0:
            item_sprite = item_sprite.copy()
            item_sprite.set_alpha(65)

        screen.blit(
            item_sprite,
            (item_x, inventory_rectangle.y + 9),
        )
        screen.blit(
            log_font.render(value, True, TEXT_COLOR),
            (item_x + 34, inventory_rectangle.y + 15),
        )

    events_title_y = SIDEBAR_Y + 258
    screen.blit(
        title_font.render("RECENT EVENTS", True, TEXT_COLOR),
        (SIDEBAR_X + 12, events_title_y),
    )
    event_y = events_title_y + 28

    for message in combat_log:
        visible_message = (
            message
            if len(message) <= 43
            else f"{message[:40]}..."
        )
        screen.blit(
            log_font.render(
                visible_message,
                True,
                get_event_color(message),
            ),
            (SIDEBAR_X + 12, event_y),
        )
        event_y += 21

    controls_rectangle = pygame.Rect(
        SIDEBAR_X + 10,
        SIDEBAR_Y + SIDEBAR_HEIGHT - 77,
        SIDEBAR_WIDTH - 20,
        67,
    )
    draw_pixel_section(screen, controls_rectangle)
    controls = (
        "WASD / Arrows - move / aim",
        "Space - wait  |  E - ability",
        "H - potion  |  F11 - fullscreen",
    )
    controls_y = controls_rectangle.y + 3

    for control_line in controls:
        screen.blit(
            controls_font.render(
                control_line,
                True,
                (232, 226, 234),
            ),
            (controls_rectangle.x + 9, controls_y),
        )
        controls_y += 21


def draw_sidebar(
    screen,
    title_font,
    log_font,
    controls_font,
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
    act_number,
    sprites,
):
    if act_number >= 2:
        draw_act_two_sidebar(
            screen,
            title_font,
            log_font,
            controls_font,
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
            sprites,
        )
        return

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
        f"Class: {player_class.title() if player_class else 'Unchosen'}",
        f"Health: {player_health}/{player_max_health}",
        f"Damage: {player_damage_min}-{player_damage_max}",
        f"Potions: {potion_count}",
        f"Gold: {gold_count}",
        f"Keys: {key_count}",
        f"Enemies defeated: {enemies_defeated}",
        (
            f"Crit: {round(player_crit_chance * 100)}%    "
            f"Dodge: {round(player_dodge_chance * 100)}%"
        ),
    ]

    if player_class == "rogue":
        character_lines.append(
            f"Invisibility: {ability_kill_charge}/2 kills"
        )
        if invisibility_turns > 0:
            character_lines.append(
                f"Invisible: {invisibility_turns} turns"
            )
    elif player_class == "mage":
        ability_status = (
            "AIM - choose direction"
            if directional_ability_aiming
            else f"{ability_kill_charge}/2 kills"
        )
        character_lines.append(
            f"Arcane burst: {ability_status}"
        )
    elif player_class == "warrior":
        ability_status = (
            "AIM - choose direction"
            if directional_ability_aiming
            else f"{ability_kill_charge}/2 kills"
        )
        character_lines.append(
            f"Power strike: {ability_status}"
        )

    line_y = SIDEBAR_Y + 52
    text_width = SIDEBAR_WIDTH - 36

    for line in character_lines:
        visible_line = fit_text_to_width(
            log_font,
            line,
            text_width,
        )
        line_surface = log_font.render(
            visible_line,
            True,
            TEXT_COLOR,
        )
        screen.blit(line_surface, (SIDEBAR_X + 18, line_y))
        line_y += 22

    divider_y = SIDEBAR_Y + 240
    pygame.draw.line(
        screen,
        PANEL_BORDER_COLOR,
        (SIDEBAR_X + 18, divider_y),
        (SIDEBAR_X + SIDEBAR_WIDTH - 18, divider_y),
        1,
    )

    events_title = title_font.render("RECENT EVENTS", True, TEXT_COLOR)
    screen.blit(events_title, (SIDEBAR_X + 18, divider_y + 18))

    line_y = divider_y + 52

    for message in combat_log:
        visible_message = fit_text_to_width(
            log_font,
            message,
            text_width,
        )
        message_surface = log_font.render(
            visible_message,
            True,
            TEXT_COLOR,
        )
        screen.blit(message_surface, (SIDEBAR_X + 18, line_y))
        line_y += 22

    controls_rectangle = pygame.Rect(
        SIDEBAR_X + 12,
        SIDEBAR_Y + SIDEBAR_HEIGHT - 79,
        SIDEBAR_WIDTH - 24,
        67,
    )
    pygame.draw.rect(
        screen,
        (27, 24, 30),
        controls_rectangle,
        border_radius=5,
    )
    pygame.draw.rect(
        screen,
        PANEL_BORDER_COLOR,
        controls_rectangle,
        width=2,
        border_radius=5,
    )
    controls = (
        "WASD / Arrows - move / aim",
        "Space - wait  |  H - potion",
        "F11 - fullscreen",
    )
    controls_y = controls_rectangle.y + 3

    for control_line in controls:
        controls_surface = controls_font.render(
            control_line,
            True,
            (232, 226, 234),
        )
        screen.blit(
            controls_surface,
            (controls_rectangle.x + 8, controls_y),
        )
        controls_y += 21


def draw_upgrade_screen(
    screen,
    title_font,
    text_font,
    gold_count,
    player_health,
    player_max_health,
    player_damage_min,
    player_damage_max,
    player_crit_chance,
    player_dodge_chance,
    message,
):
    dark_overlay = pygame.Surface(
        (GAME_WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA,
    )
    dark_overlay.fill((0, 0, 0, 175))
    screen.blit(dark_overlay, (0, 0))

    panel_rectangle = pygame.Rect(220, 105, 840, 510)
    pygame.draw.rect(
        screen,
        PANEL_COLOR,
        panel_rectangle,
        border_radius=12,
    )
    pygame.draw.rect(
        screen,
        PANEL_BORDER_COLOR,
        panel_rectangle,
        width=3,
        border_radius=12,
    )

    title_surface = title_font.render(
        "DESCENT ALTAR",
        True,
        STAIRS_COLOR,
    )
    title_rectangle = title_surface.get_rect(
        center=(GAME_WIDTH // 2, 155)
    )
    screen.blit(title_surface, title_rectangle)

    stats = (
        f"Gold: {gold_count}    "
        f"HP: {player_health}/{player_max_health}    "
        f"Damage: {player_damage_min}-{player_damage_max}"
    )
    stats_surface = text_font.render(stats, True, TEXT_COLOR)
    stats_rectangle = stats_surface.get_rect(
        center=(GAME_WIDTH // 2, 205)
    )
    screen.blit(stats_surface, stats_rectangle)

    chance_stats = (
        f"Critical chance: {round(player_crit_chance * 100)}%    "
        f"Dodge chance: {round(player_dodge_chance * 100)}%"
    )
    chance_surface = text_font.render(
        chance_stats,
        True,
        TEXT_COLOR,
    )
    chance_rectangle = chance_surface.get_rect(
        center=(GAME_WIDTH // 2, 235)
    )
    screen.blit(chance_surface, chance_rectangle)

    options = [
        "[1] Vitality: +2 maximum HP - 1 gold",
        "[2] Sharpen weapon: +1 damage - 1 gold",
        "[3] Precision: +5% critical chance - 1 gold",
        "[4] Evasion: +5% dodge chance - 1 gold",
        "[Enter] Descend without further purchases",
    ]
    option_y = 280

    for option in options:
        option_surface = text_font.render(option, True, TEXT_COLOR)
        screen.blit(option_surface, (310, option_y))
        option_y += 52

    if message:
        message_surface = text_font.render(
            message,
            True,
            PLAYER_HEALTH_BAR_COLOR,
        )
        message_rectangle = message_surface.get_rect(
            center=(GAME_WIDTH // 2, 570)
        )
        screen.blit(message_surface, message_rectangle)


def draw_class_selection_screen(
    screen,
    intro_title_font,
    intro_text_font,
    class_title_font,
    class_text_font,
    sprites,
    elapsed_ms,
    mouse_position,
):
    screen.fill((3, 2, 4))

    if elapsed_ms < AWAKENING_FADE_END_MS:
        if elapsed_ms >= AWAKENING_OPEN_START_MS:
            screen.blit(sprites["awakening"], (0, 0))
            opening_progress = max(
                0,
                min(
                    1,
                    (
                        elapsed_ms - AWAKENING_OPEN_START_MS
                    )
                    / (
                        AWAKENING_OPEN_END_MS
                        - AWAKENING_OPEN_START_MS
                    ),
                ),
            )
            opening_progress = (
                opening_progress
                * opening_progress
                * (3 - 2 * opening_progress)
            )
            aperture_height = max(
                2,
                int(
                    GAME_HEIGHT
                    * 1.8
                    * opening_progress
                ),
            )
            eyelids = pygame.Surface(
                (GAME_WIDTH, GAME_HEIGHT),
                pygame.SRCALPHA,
            )
            eyelids.fill((2, 1, 3, 255))
            pygame.draw.ellipse(
                eyelids,
                (0, 0, 0, 0),
                (
                    -GAME_WIDTH // 4,
                    GAME_HEIGHT // 2
                    - aperture_height // 2,
                    GAME_WIDTH * 3 // 2,
                    aperture_height,
                ),
            )
            screen.blit(eyelids, (0, 0))

            if elapsed_ms > AWAKENING_HOLD_END_MS:
                fade_progress = min(
                    1,
                    (
                        elapsed_ms - AWAKENING_HOLD_END_MS
                    )
                    / (
                        AWAKENING_FADE_END_MS
                        - AWAKENING_HOLD_END_MS
                    ),
                )
                fade_overlay = pygame.Surface(
                    (GAME_WIDTH, GAME_HEIGHT),
                    pygame.SRCALPHA,
                )
                fade_overlay.fill(
                    (3, 2, 4, int(255 * fade_progress))
                )
                screen.blit(fade_overlay, (0, 0))

        return

    narrative = [
        (
            3250,
            intro_title_font,
            "THE FIRST VEIL FALLS",
            PLAYER_ATTACK_BORDER_COLOR,
            62,
        ),
        (
            3850,
            intro_text_font,
            "Something changes within you.",
            TEXT_COLOR,
            120,
        ),
        (
            4450,
            intro_text_font,
            "The world around you begins to transform.",
            TEXT_COLOR,
            158,
        ),
        (
            5050,
            intro_text_font,
            "You begin to understand your place within it.",
            TEXT_COLOR,
            196,
        ),
        (
            5650,
            intro_text_font,
            "Choose your fate.",
            PLAYER_ATTACK_BORDER_COLOR,
            236,
        ),
    ]

    for start_time, font, text, color, center_y in narrative:
        text_alpha = max(
            0,
            min(255, int((elapsed_ms - start_time) * 255 / 450)),
        )

        if text_alpha <= 0:
            continue

        line_surface = font.render(text, True, color)
        line_surface.set_alpha(text_alpha)
        screen.blit(
            line_surface,
            line_surface.get_rect(
                center=(GAME_WIDTH // 2, center_y)
            ),
        )

    if elapsed_ms < CLASS_SELECTION_READY_MS:
        return

    class_data = {
        "warrior": {
            "number": "1",
            "title": "WARRIOR",
            "color": (205, 75, 68),
            "bonuses": (
                "+4 maximum HP",
                "Highest survivability",
            ),
            "ability": "POWER STRIKE",
            "description": (
                "After 2 kills, press E and choose a direction. "
                "Strike an adjacent enemy with +2 damage."
            ),
        },
        "rogue": {
            "number": "2",
            "title": "ROGUE",
            "color": (145, 78, 190),
            "bonuses": (
                "-2 maximum HP",
                "+10% critical and dodge chance",
            ),
            "ability": "INVISIBILITY",
            "description": (
                "After 2 kills, press E to vanish for 5 turns. "
                "Your first attack from invisibility is a sure critical."
            ),
        },
        "mage": {
            "number": "3",
            "title": "MAGE",
            "color": (75, 115, 205),
            "bonuses": (
                "No passive stat bonuses",
                "Attacks several enemies at once",
            ),
            "ability": "ARCANE BURST",
            "description": (
                "After 2 kills, press E and choose a direction. "
                "Magic hits every enemy in a line up to 5 cells "
                "away with +2 damage."
            ),
        },
    }
    cards_surface = pygame.Surface(
        (GAME_WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA,
    )
    rectangles = get_class_selection_rectangles()

    for class_name, card_rectangle in rectangles.items():
        data = class_data[class_name]
        is_hovered = (
            mouse_position is not None
            and card_rectangle.collidepoint(mouse_position)
        )
        border_color = (
            data["color"]
            if is_hovered
            else (82, 75, 86)
        )
        background_color = (
            (34, 28, 38)
            if is_hovered
            else (20, 17, 23)
        )
        pygame.draw.rect(
            cards_surface,
            background_color,
            card_rectangle,
            border_radius=10,
        )
        pygame.draw.rect(
            cards_surface,
            border_color,
            card_rectangle,
            width=3,
            border_radius=10,
        )

        portrait = pygame.transform.scale(
            sprites[f"{class_name}_portrait"],
            (96, 96),
        )
        portrait_rectangle = portrait.get_rect(
            center=(card_rectangle.centerx, card_rectangle.y + 58)
        )
        cards_surface.blit(portrait, portrait_rectangle)

        heading = class_title_font.render(
            f"[{data['number']}] {data['title']}",
            True,
            data["color"],
        )
        cards_surface.blit(
            heading,
            heading.get_rect(
                center=(card_rectangle.centerx, card_rectangle.y + 120)
            ),
        )

        text_y = card_rectangle.y + 151

        for bonus in data["bonuses"]:
            bonus_surface = class_text_font.render(
                bonus,
                True,
                TEXT_COLOR,
            )
            cards_surface.blit(
                bonus_surface,
                bonus_surface.get_rect(
                    center=(card_rectangle.centerx, text_y)
                ),
            )
            text_y += 23

        ability_surface = class_title_font.render(
            data["ability"],
            True,
            data["color"],
        )
        cards_surface.blit(
            ability_surface,
            ability_surface.get_rect(
                center=(card_rectangle.centerx, text_y + 13)
            ),
        )
        text_y += 43

        description_lines = wrap_text(
            class_text_font,
            data["description"],
            card_rectangle.width - 34,
        )

        for description_line in description_lines:
            description_surface = class_text_font.render(
                description_line,
                True,
                TEXT_COLOR,
            )
            cards_surface.blit(
                description_surface,
                (
                    card_rectangle.x + 17,
                    text_y,
                ),
            )
            text_y += 21

        if is_hovered:
            select_surface = class_text_font.render(
                "CLICK TO CHOOSE",
                True,
                data["color"],
            )
            cards_surface.blit(
                select_surface,
                select_surface.get_rect(
                    center=(
                        card_rectangle.centerx,
                        card_rectangle.bottom - 18,
                    )
                ),
            )

    card_alpha = min(
        255,
        int(
            (elapsed_ms - CLASS_SELECTION_READY_MS)
            * 255
            / 450
        ),
    )
    cards_surface.set_alpha(card_alpha)
    screen.blit(cards_surface, (0, 0))
