import pygame

from presentation.hud import (
    get_class_selection_rectangles,
    wrap_text,
)
from presentation.layout import (
    AWAKENING_FADE_END_MS,
    AWAKENING_HOLD_END_MS,
    AWAKENING_OPEN_END_MS,
    AWAKENING_OPEN_START_MS,
    ASSET_ROOT,
    CLASS_SELECTION_READY_MS,
    FONT_ROOT,
    MAP_HEIGHT,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    MAP_WIDTH,
    SIDEBAR_HEIGHT,
    SIDEBAR_WIDTH,
    SIDEBAR_X,
    SIDEBAR_Y,
)
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
