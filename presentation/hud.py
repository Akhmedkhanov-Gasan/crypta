import pygame

from levels import FLOOR_CONFIGS
from presentation.layout import (
    MAP_OFFSET_X,
    MAP_WIDTH,
    SIDEBAR_HEIGHT,
    SIDEBAR_WIDTH,
    SIDEBAR_X,
    SIDEBAR_Y,
)
from settings import (
    ENEMY_COLOR,
    GAME_HEIGHT,
    GAME_WIDTH,
    HEALTH_BAR_BACKGROUND,
    PANEL_BORDER_COLOR,
    PANEL_COLOR,
    PLAYER_COLOR,
    PLAYER_HEALTH_BAR_COLOR,
    TEXT_COLOR,
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
                        MAP_OFFSET_X + MAP_WIDTH // 2,
                        55,
                    )
                ),
            )
            boss_bar_width = min(640, MAP_WIDTH - 120)
            boss_bar_height = 22
            boss_bar_left = (
                MAP_OFFSET_X
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
                    center=(MAP_OFFSET_X + MAP_WIDTH // 2, 57)
                ),
            )
            boss_bar_width = 500
            boss_bar_height = 14
            boss_bar_left = (
                MAP_OFFSET_X + (MAP_WIDTH - boss_bar_width) // 2
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
                        center=(MAP_OFFSET_X + MAP_WIDTH // 2, 104)
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
