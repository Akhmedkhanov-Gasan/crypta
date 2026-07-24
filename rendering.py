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


def load_act_two_sprites():
    asset_directory = ASSET_ROOT / "act_2"
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
        and enemy["type"] in ("goblin", "brute", "archer")
    ):
        screen.blit(
            sprites[enemy["type"]],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
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


def draw_sidebar(
    screen,
    title_font,
    log_font,
    combat_log,
    player_health,
    player_max_health,
    player_damage_min,
    player_damage_max,
    player_crit_chance,
    player_dodge_chance,
    potion_count,
    gold_count,
    has_key,
    enemies_defeated,
    player_class,
    ability_kill_charge,
    invisibility_turns,
    directional_ability_aiming,
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
        f"Class: {player_class.title() if player_class else 'Unchosen'}",
        f"Health: {player_health}/{player_max_health}",
        f"Damage: {player_damage_min}-{player_damage_max}",
        f"Potions: {potion_count}",
        f"Gold: {gold_count}",
        f"Key: {'yes' if has_key else 'no'}",
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

    for line in character_lines:
        line_surface = log_font.render(line, True, TEXT_COLOR)
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

    line_y = divider_y + 58

    for message in combat_log:
        message_surface = log_font.render(message, True, TEXT_COLOR)
        screen.blit(message_surface, (SIDEBAR_X + 18, line_y))
        line_y += 24

    controls_y = SIDEBAR_Y + SIDEBAR_HEIGHT - 68
    controls_surface = log_font.render(
        "Move/Aim: WASD/arrows  |  Wait: Space",
        True,
        PANEL_BORDER_COLOR,
    )
    screen.blit(controls_surface, (SIDEBAR_X + 18, controls_y))

    fullscreen_surface = log_font.render(
        "Ability: E  |  Potion: H  |  Fullscreen: F11",
        True,
        PANEL_BORDER_COLOR,
    )
    screen.blit(
        fullscreen_surface,
        (SIDEBAR_X + 18, controls_y + 24),
    )


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


def draw_class_selection_screen(screen, title_font, text_font):
    dark_overlay = pygame.Surface(
        (GAME_WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA,
    )
    dark_overlay.fill((0, 0, 0, 210))
    screen.blit(dark_overlay, (0, 0))

    panel_rectangle = pygame.Rect(180, 70, 920, 580)
    pygame.draw.rect(
        screen,
        PANEL_COLOR,
        panel_rectangle,
        border_radius=12,
    )
    pygame.draw.rect(
        screen,
        PLAYER_ATTACK_BORDER_COLOR,
        panel_rectangle,
        width=3,
        border_radius=12,
    )

    title_surface = title_font.render(
        "THE FIRST VEIL FALLS",
        True,
        PLAYER_ATTACK_BORDER_COLOR,
    )
    screen.blit(
        title_surface,
        title_surface.get_rect(center=(GAME_WIDTH // 2, 120)),
    )

    narrative_lines = [
        "The Warden is gone. Shapes become bodies. Stone gains texture.",
        "For the first time, you begin to see the Crypta as it is.",
        "Choose what the descent will make of you.",
    ]
    line_y = 170

    for line in narrative_lines:
        line_surface = text_font.render(line, True, TEXT_COLOR)
        screen.blit(
            line_surface,
            line_surface.get_rect(center=(GAME_WIDTH // 2, line_y)),
        )
        line_y += 30

    choices = [
        (
            "[1] WARRIOR",
            "+4 max HP; two kills charge one powerful melee strike",
            (190, 70, 65),
        ),
        (
            "[2] ROGUE",
            "-2 max HP, +10% crit/dodge; invisibility enables a sure crit",
            (125, 75, 165),
        ),
        (
            "[3] MAGE",
            "Two kills charge a powerful spell in a straight line",
            (70, 105, 185),
        ),
    ]
    choice_y = 300

    for heading, description, color in choices:
        heading_surface = title_font.render(heading, True, color)
        description_surface = text_font.render(
            description,
            True,
            TEXT_COLOR,
        )
        screen.blit(heading_surface, (270, choice_y))
        screen.blit(description_surface, (270, choice_y + 38))
        choice_y += 105
