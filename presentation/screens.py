import pygame

from acts.act_one.settings import PLAYER_STARTING_STATS
from acts.act_three.settings import SUBCLASS_BASE_STATS
from acts.act_two.settings import CLASS_BASE_STATS
from acts.player_stats import (
    describe_player_stat_changes,
    player_stat_changes_between,
)
from presentation.hud import (
    get_class_selection_rectangles,
    wrap_text,
)
from presentation.layout import (
    ACT_THREE_AWAKENING_END_MS,
    ACT_THREE_CAMERA_END_MS,
    ACT_THREE_CLENCH_END_MS,
    ACT_THREE_EYES_OPEN_END_MS,
    ACT_THREE_EYES_OPEN_START_MS,
    ACT_THREE_FINAL_HOLD_END_MS,
    ACT_THREE_HANDS_HOLD_END_MS,
    ACT_THREE_HANDS_RISE_END_MS,
    ACT_THREE_HANDS_RISE_START_MS,
    ACT_THREE_NARRATIVE_READY_MS,
    ACT_THREE_NARRATIVE_START_MS,
    AWAKENING_FADE_END_MS,
    AWAKENING_HOLD_END_MS,
    AWAKENING_OPEN_END_MS,
    AWAKENING_OPEN_START_MS,
    CLASS_SELECTION_READY_MS,
)
from settings import (
    CRIT_UPGRADE_AMOUNT,
    DAMAGE_UPGRADE_AMOUNT,
    DODGE_UPGRADE_AMOUNT,
    GAME_HEIGHT,
    GAME_WIDTH,
    HEALTH_UPGRADE_AMOUNT,
    MAX_CRIT_CHANCE,
    MAX_DODGE_CHANCE,
    PLAYER_ATTACK_BORDER_COLOR,
    TEXT_COLOR,
)


def get_upgrade_card_rectangles():
    return {
        "vitality": pygame.Rect(210, 240, 410, 132),
        "power": pygame.Rect(660, 240, 410, 132),
        "precision": pygame.Rect(210, 394, 410, 132),
        "evasion": pygame.Rect(660, 394, 410, 132),
    }


def _draw_upgrade_icon(screen, kind, center, color):
    icon_surface = pygame.Surface((44, 44), pygame.SRCALPHA)
    pygame.draw.circle(icon_surface, (11, 12, 16, 220), (22, 22), 21)
    pygame.draw.circle(icon_surface, color, (22, 22), 20, width=2)

    if kind == "vitality":
        pygame.draw.polygon(
            icon_surface,
            color,
            [(22, 34), (10, 21), (12, 14), (18, 12), (22, 17),
             (26, 12), (32, 14), (34, 21)],
        )
    elif kind == "power":
        pygame.draw.polygon(
            icon_surface,
            color,
            [
                (34, 7),
                (31, 18),
                (20, 29),
                (16, 25),
                (27, 14),
            ],
        )
        pygame.draw.line(
            icon_surface,
            (15, 16, 21),
            (29, 14),
            (19, 25),
            2,
        )
        pygame.draw.line(icon_surface, color, (12, 23), (22, 33), 3)
        pygame.draw.line(icon_surface, color, (16, 30), (11, 35), 4)
        pygame.draw.circle(icon_surface, color, (9, 37), 3)
    elif kind == "precision":
        pygame.draw.circle(icon_surface, color, (22, 22), 11, width=2)
        pygame.draw.circle(icon_surface, color, (22, 22), 4, width=2)
        pygame.draw.line(icon_surface, color, (22, 6), (22, 13), 2)
        pygame.draw.line(icon_surface, color, (22, 31), (22, 38), 2)
        pygame.draw.line(icon_surface, color, (6, 22), (13, 22), 2)
        pygame.draw.line(icon_surface, color, (31, 22), (38, 22), 2)
    else:
        pygame.draw.circle(icon_surface, color, (28, 10), 4)
        pygame.draw.line(icon_surface, color, (26, 13), (24, 17), 3)
        pygame.draw.line(icon_surface, color, (25, 15), (19, 26), 4)
        pygame.draw.line(icon_surface, color, (23, 18), (32, 21), 3)
        pygame.draw.line(icon_surface, color, (32, 21), (36, 17), 3)
        pygame.draw.line(icon_surface, color, (22, 18), (15, 16), 3)
        pygame.draw.line(icon_surface, color, (15, 16), (12, 20), 3)
        pygame.draw.line(icon_surface, color, (19, 26), (28, 30), 4)
        pygame.draw.line(icon_surface, color, (28, 30), (35, 28), 3)
        pygame.draw.line(icon_surface, color, (19, 26), (14, 34), 4)
        pygame.draw.line(icon_surface, color, (14, 34), (8, 34), 3)
        pygame.draw.line(icon_surface, color, (7, 12), (15, 12), 2)
        pygame.draw.line(icon_surface, color, (5, 25), (12, 25), 2)

    screen.blit(icon_surface, (center[0] - 22, center[1] - 22))


def _draw_upgrade_card(
    screen,
    text_font,
    rectangle,
    kind,
    key_label,
    title,
    description,
    value_text,
    accent_color,
    disabled,
    capped,
    hovered,
):
    if disabled:
        fill_color = (20, 20, 25)
        border_color = (51, 49, 56)
        text_color = (104, 101, 108)
    else:
        fill_color = (36, 35, 43) if hovered else (28, 28, 35)
        border_color = accent_color if hovered else (76, 72, 81)
        text_color = (224, 216, 204)

    pygame.draw.rect(screen, (8, 8, 11), rectangle.move(3, 4), border_radius=7)
    pygame.draw.rect(screen, fill_color, rectangle, border_radius=7)
    pygame.draw.rect(screen, border_color, rectangle, width=2, border_radius=7)
    pygame.draw.line(
        screen,
        (62, 59, 68) if not disabled else (35, 34, 40),
        (rectangle.x + 12, rectangle.y + 3),
        (rectangle.right - 12, rectangle.y + 3),
    )

    badge_rectangle = pygame.Rect(rectangle.x + 12, rectangle.y + 12, 30, 27)
    pygame.draw.rect(screen, (12, 12, 16), badge_rectangle, border_radius=4)
    pygame.draw.rect(screen, border_color, badge_rectangle, width=1, border_radius=4)
    badge = text_font.render(key_label, True, text_color)
    screen.blit(badge, badge.get_rect(center=badge_rectangle.center))

    _draw_upgrade_icon(
        screen,
        kind,
        (rectangle.x + 70, rectangle.centery),
        border_color,
    )
    title_surface = text_font.render(title, True, text_color)
    screen.blit(title_surface, (rectangle.x + 105, rectangle.y + 17))

    description_surface = text_font.render(
        description,
        True,
        (178, 173, 181) if not disabled else (96, 93, 101),
    )
    screen.blit(description_surface, (rectangle.x + 105, rectangle.y + 50))

    value_surface = text_font.render(
        value_text,
        True,
        accent_color if not disabled else (91, 88, 95),
    )
    screen.blit(value_surface, (rectangle.x + 105, rectangle.y + 82))

    cost_text = "MAX" if capped else "1 GOLD"
    cost_surface = text_font.render(
        cost_text,
        True,
        (195, 151, 67) if not disabled else (86, 82, 75),
    )
    screen.blit(
        cost_surface,
        cost_surface.get_rect(
            bottomright=(rectangle.right - 14, rectangle.bottom - 12)
        ),
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
    mouse_position=None,
):
    dark_overlay = pygame.Surface(
        (GAME_WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA,
    )
    dark_overlay.fill((0, 0, 0, 205))
    screen.blit(dark_overlay, (0, 0))

    panel_rectangle = pygame.Rect(170, 66, 940, 588)
    pygame.draw.rect(
        screen,
        (6, 6, 9),
        panel_rectangle.move(6, 8),
        border_radius=10,
    )
    pygame.draw.rect(
        screen,
        (18, 18, 24),
        panel_rectangle,
        border_radius=10,
    )
    pygame.draw.rect(
        screen,
        (70, 68, 77),
        panel_rectangle,
        width=3,
        border_radius=10,
    )
    pygame.draw.rect(
        screen,
        (38, 37, 45),
        panel_rectangle.inflate(-12, -12),
        width=1,
        border_radius=7,
    )
    for corner in (
        panel_rectangle.topleft,
        panel_rectangle.topright,
        panel_rectangle.bottomleft,
        panel_rectangle.bottomright,
    ):
        pygame.draw.circle(screen, (10, 10, 13), corner, 6)
        pygame.draw.circle(screen, (116, 104, 82), corner, 2)

    title_surface = title_font.render(
        "DESCENT ALTAR",
        True,
        (188, 177, 157),
    )
    title_rectangle = title_surface.get_rect(
        center=(GAME_WIDTH // 2, 108)
    )
    screen.blit(title_surface, title_rectangle)

    instruction = (
        f"{gold_count} BLESSING{'S' if gold_count != 1 else ''} AVAILABLE"
    )
    instruction_surface = text_font.render(
        instruction,
        True,
        (211, 169, 77),
    )
    screen.blit(
        instruction_surface,
        instruction_surface.get_rect(center=(GAME_WIDTH // 2, 153)),
    )

    stats = (
        f"HP {player_health}/{player_max_health}     "
        f"DAMAGE {player_damage_min}-{player_damage_max}     "
        f"CRIT {round(player_crit_chance * 100)}%     "
        f"DODGE {round(player_dodge_chance * 100)}%"
    )
    stats_surface = text_font.render(
        stats,
        True,
        (184, 179, 187),
    )
    screen.blit(
        stats_surface,
        stats_surface.get_rect(center=(GAME_WIDTH // 2, 196)),
    )

    crit_capped = player_crit_chance >= MAX_CRIT_CHANCE
    dodge_capped = player_dodge_chance >= MAX_DODGE_CHANCE
    no_gold = gold_count <= 0
    cards = (
        (
            "vitality", "1", "VITALITY",
            f"Maximum health • heals {HEALTH_UPGRADE_AMOUNT}",
            f"{player_max_health}  >  "
            f"{player_max_health + HEALTH_UPGRADE_AMOUNT} HP",
            (155, 71, 74), False,
        ),
        (
            "power", "2", "POWER", "Reliable weapon damage",
            f"{player_damage_min}-{player_damage_max}  >  "
            f"{player_damage_min + DAMAGE_UPGRADE_AMOUNT}-"
            f"{player_damage_max + DAMAGE_UPGRADE_AMOUNT}",
            (177, 112, 62), False,
        ),
        (
            "precision", "3", "PRECISION", "Chance for a critical hit",
            f"{round(player_crit_chance * 100)}%  >  "
            f"{round(min(MAX_CRIT_CHANCE, player_crit_chance + CRIT_UPGRADE_AMOUNT) * 100)}%",
            (166, 137, 69), crit_capped,
        ),
        (
            "evasion", "4", "EVASION", "Chance to avoid an attack",
            f"{round(player_dodge_chance * 100)}%  >  "
            f"{round(min(MAX_DODGE_CHANCE, player_dodge_chance + DODGE_UPGRADE_AMOUNT) * 100)}%",
            (76, 128, 131), dodge_capped,
        ),
    )
    card_rectangles = get_upgrade_card_rectangles()
    for (
        kind,
        key_label,
        title,
        description,
        value_text,
        accent_color,
        capped,
    ) in cards:
        rectangle = card_rectangles[kind]
        hovered = (
            mouse_position is not None
            and rectangle.collidepoint(mouse_position)
        )
        _draw_upgrade_card(
            screen,
            text_font,
            rectangle,
            kind,
            key_label,
            title,
            description,
            value_text,
            accent_color,
            no_gold or capped,
            capped,
            hovered,
        )

    if message:
        message_surface = text_font.render(
            message,
            True,
            (211, 169, 77),
        )
        message_rectangle = message_surface.get_rect(
            center=(GAME_WIDTH // 2, 565)
        )
        screen.blit(message_surface, message_rectangle)

    footer = (
        f"[ENTER] KEEP {gold_count} GOLD AND DESCEND"
        if gold_count > 0
        else "DESCENDING..."
    )
    footer_surface = text_font.render(footer, True, (171, 166, 174))
    screen.blit(
        footer_surface,
        footer_surface.get_rect(center=(GAME_WIDTH // 2, 620)),
    )


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
            "bonuses": describe_player_stat_changes(
                player_stat_changes_between(
                    PLAYER_STARTING_STATS,
                    CLASS_BASE_STATS["warrior"],
                )
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
            "bonuses": describe_player_stat_changes(
                player_stat_changes_between(
                    PLAYER_STARTING_STATS,
                    CLASS_BASE_STATS["rogue"],
                )
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
                describe_player_stat_changes(
                    player_stat_changes_between(
                        PLAYER_STARTING_STATS,
                        CLASS_BASE_STATS["mage"],
                    )
                )
                or ("No passive stat changes",)
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


def _smooth_progress(elapsed_ms, start_ms, end_ms):
    progress = max(
        0.0,
        min(1.0, (elapsed_ms - start_ms) / (end_ms - start_ms)),
    )
    return progress * progress * (3 - 2 * progress)


def _blit_with_alpha(screen, image, position, alpha):
    if alpha >= 255:
        screen.blit(image, position)
        return

    faded_image = image.copy()
    faded_image.set_alpha(max(0, min(255, round(alpha))))
    screen.blit(faded_image, position)


def _draw_act_three_narrative(
    screen,
    narrative_font,
    elapsed_ms,
):
    lines = (
        "THE SECOND VEIL FALLS.",
        "The world returns sharper than before.",
        "You begin to see what was hidden.",
        "Again, a silhouette waits at the end of the Crypta.",
        "Who is it?",
        "Who are you?",
    )
    line_delay_ms = 1400
    character_delay_ms = 55
    active_lines = [
        (index, line)
        for index, line in enumerate(lines)
        if (
            elapsed_ms
            >= ACT_THREE_NARRATIVE_START_MS
            + index * line_delay_ms
        )
    ]

    if not active_lines:
        return

    page_rectangle = pygame.Rect(140, 72, 1000, 575)
    page_shadow = page_rectangle.move(8, 10)
    pygame.draw.rect(
        screen,
        (6, 4, 3),
        page_shadow,
        border_radius=6,
    )
    pygame.draw.rect(
        screen,
        (27, 21, 17),
        page_rectangle,
        border_radius=6,
    )
    pygame.draw.rect(
        screen,
        (104, 76, 48),
        page_rectangle,
        width=2,
        border_radius=6,
    )
    inner_rectangle = page_rectangle.inflate(-22, -22)
    pygame.draw.rect(
        screen,
        (61, 46, 34),
        inner_rectangle,
        width=1,
        border_radius=4,
    )
    ornament_y = page_rectangle.y + 92
    pygame.draw.line(
        screen,
        (83, 58, 39),
        (page_rectangle.x + 60, ornament_y),
        (page_rectangle.right - 60, ornament_y),
        1,
    )
    pygame.draw.polygon(
        screen,
        (151, 64, 48),
        (
            (GAME_WIDTH // 2, ornament_y - 5),
            (GAME_WIDTH // 2 + 5, ornament_y),
            (GAME_WIDTH // 2, ornament_y + 5),
            (GAME_WIDTH // 2 - 5, ornament_y),
        ),
    )

    for visible_index, (line_index, line) in enumerate(active_lines):
        line_started_at = (
            ACT_THREE_NARRATIVE_START_MS
            + line_index * line_delay_ms
        )
        visible_character_count = max(
            0,
            int(
                (elapsed_ms - line_started_at)
                / character_delay_ms
            ),
        )
        visible_text = line[:visible_character_count]

        if not visible_text:
            continue

        color = (
            (205, 67, 59)
            if line_index == 0
            else TEXT_COLOR
        )
        line_surface = narrative_font.render(
            visible_text,
            True,
            color,
        )
        line_y = (
            page_rectangle.y + 47
            if line_index == 0
            else page_rectangle.y + 135 + (line_index - 1) * 67
        )
        screen.blit(
            line_surface,
            (page_rectangle.x + 60, line_y),
        )

    if elapsed_ms >= ACT_THREE_NARRATIVE_READY_MS:
        prompt_alpha = (
            255
            if (elapsed_ms // 650) % 2 == 0
            else 115
        )
        prompt = narrative_font.render(
            "CLICK / SPACE TO OPEN YOUR EYES",
            True,
            (171, 129, 83),
        )
        prompt.set_alpha(prompt_alpha)
        screen.blit(
            prompt,
            prompt.get_rect(
                bottomright=(
                    page_rectangle.right - 58,
                    page_rectangle.bottom - 34,
                )
            ),
        )


def get_act_three_debug_class_rectangles():
    button_width = 280
    button_height = 94
    gap = 34
    total_width = button_width * 3 + gap * 2
    left = (GAME_WIDTH - total_width) // 2
    top = 335

    return {
        "warrior": pygame.Rect(
            left,
            top,
            button_width,
            button_height,
        ),
        "rogue": pygame.Rect(
            left + button_width + gap,
            top,
            button_width,
            button_height,
        ),
        "mage": pygame.Rect(
            left + (button_width + gap) * 2,
            top,
            button_width,
            button_height,
        ),
    }


def draw_act_three_debug_class_selection(
    screen,
    title_font,
    heading_font,
    text_font,
    mouse_position,
):
    screen.fill((5, 4, 8))
    title = title_font.render(
        "ACT III AWAKENING",
        True,
        TEXT_COLOR,
    )
    screen.blit(
        title,
        title.get_rect(center=(GAME_WIDTH // 2, 165)),
    )
    subtitle = text_font.render(
        "DEBUG: CHOOSE THE CLASS TO PREVIEW",
        True,
        (143, 134, 151),
    )
    screen.blit(
        subtitle,
        subtitle.get_rect(center=(GAME_WIDTH // 2, 235)),
    )

    class_colors = {
        "warrior": (190, 57, 52),
        "rogue": (137, 75, 175),
        "mage": (67, 110, 190),
    }
    class_labels = {
        "warrior": "[1] WARRIOR",
        "rogue": "[2] ROGUE",
        "mage": "[3] MAGE",
    }

    for class_name, rectangle in (
        get_act_three_debug_class_rectangles().items()
    ):
        hovered = (
            mouse_position is not None
            and rectangle.collidepoint(mouse_position)
        )
        color = class_colors[class_name]
        pygame.draw.rect(
            screen,
            (22, 17, 25) if hovered else (13, 11, 16),
            rectangle,
            border_radius=8,
        )
        pygame.draw.rect(
            screen,
            color,
            rectangle,
            width=3 if hovered else 2,
            border_radius=8,
        )
        label = heading_font.render(
            class_labels[class_name],
            True,
            color if not hovered else TEXT_COLOR,
        )
        screen.blit(
            label,
            label.get_rect(center=rectangle.center),
        )

    hint = text_font.render(
        "CLICK A BUTTON OR PRESS 1 / 2 / 3",
        True,
        (117, 108, 125),
    )
    screen.blit(
        hint,
        hint.get_rect(center=(GAME_WIDTH // 2, 510)),
    )


def draw_act_three_awakening(
    screen,
    assets,
    narrative_font,
    narrative_elapsed_ms,
    visual_elapsed_ms,
    player_class,
):
    screen.fill((0, 0, 0))

    if visual_elapsed_ms is None:
        _draw_act_three_narrative(
            screen,
            narrative_font,
            narrative_elapsed_ms,
        )
        return

    elapsed_ms = visual_elapsed_ms

    background = assets["background"]
    camera_progress = _smooth_progress(
        elapsed_ms,
        ACT_THREE_EYES_OPEN_END_MS,
        ACT_THREE_CAMERA_END_MS,
    )
    background_overflow = max(
        0,
        background.get_height() - GAME_HEIGHT,
    )
    background_position = (
        (GAME_WIDTH - background.get_width()) // 2,
        -round(background_overflow * camera_progress),
    )
    screen.blit(background, background_position)

    hands_progress = _smooth_progress(
        elapsed_ms,
        ACT_THREE_HANDS_RISE_START_MS,
        ACT_THREE_HANDS_RISE_END_MS,
    )

    if hands_progress > 0:
        hands_class = (
            player_class
            if player_class in ("warrior", "rogue", "mage")
            else "warrior"
        )
        open_hands = assets[f"{hands_class}_hands_open"]
        clenched_hands = assets[
            f"{hands_class}_hands_clenched"
        ]
        hands_final_y = GAME_HEIGHT - open_hands.get_height()
        hands_start_y = hands_final_y + 300
        hands_y = round(
            hands_start_y
            + (hands_final_y - hands_start_y) * hands_progress
        )
        hands_position = (
            (GAME_WIDTH - open_hands.get_width()) // 2,
            hands_y,
        )

        if elapsed_ms < ACT_THREE_HANDS_HOLD_END_MS:
            _blit_with_alpha(
                screen,
                open_hands,
                hands_position,
                255 * hands_progress,
            )
        elif elapsed_ms < ACT_THREE_CLENCH_END_MS:
            clench_progress = _smooth_progress(
                elapsed_ms,
                ACT_THREE_HANDS_HOLD_END_MS,
                ACT_THREE_CLENCH_END_MS,
            )

            if clench_progress < 0.5:
                screen.blit(open_hands, hands_position)
            else:
                screen.blit(clenched_hands, hands_position)

            crossfade_darkness = pygame.Surface(
                (GAME_WIDTH, GAME_HEIGHT),
                pygame.SRCALPHA,
            )
            crossfade_darkness.fill(
                (
                    0,
                    0,
                    0,
                    round(225 * (1 - abs(2 * clench_progress - 1))),
                )
            )
            screen.blit(crossfade_darkness, (0, 0))
        else:
            screen.blit(clenched_hands, hands_position)

    opening_progress = _smooth_progress(
        elapsed_ms,
        ACT_THREE_EYES_OPEN_START_MS,
        ACT_THREE_EYES_OPEN_END_MS,
    )

    if opening_progress < 1:
        aperture_height = max(
            2,
            round(GAME_HEIGHT * 1.8 * opening_progress),
        )
        eyelids = pygame.Surface(
            (GAME_WIDTH, GAME_HEIGHT),
            pygame.SRCALPHA,
        )
        eyelids.fill((0, 0, 0, 255))
        pygame.draw.ellipse(
            eyelids,
            (0, 0, 0, 0),
            (
                -GAME_WIDTH // 4,
                GAME_HEIGHT // 2 - aperture_height // 2,
                GAME_WIDTH * 3 // 2,
                aperture_height,
            ),
        )
        screen.blit(eyelids, (0, 0))

    if elapsed_ms > ACT_THREE_FINAL_HOLD_END_MS:
        fade_progress = _smooth_progress(
            elapsed_ms,
            ACT_THREE_FINAL_HOLD_END_MS,
            ACT_THREE_AWAKENING_END_MS,
        )
        fade_overlay = pygame.Surface(
            (GAME_WIDTH, GAME_HEIGHT),
            pygame.SRCALPHA,
        )
        fade_overlay.fill((0, 0, 0, round(255 * fade_progress)))
        screen.blit(fade_overlay, (0, 0))


def _subclass_card_rectangles():
    card_width = 410
    card_height = 475
    gap = 50
    total_width = card_width * 2 + gap
    left = (GAME_WIDTH - total_width) // 2
    top = 155

    return (
        pygame.Rect(
            left,
            top,
            card_width,
            card_height,
        ),
        pygame.Rect(
            left + card_width + gap,
            top,
            card_width,
            card_height,
        ),
    )


def get_subclass_selection_rectangles(
    player_class="warrior",
):
    first_rectangle, second_rectangle = (
        _subclass_card_rectangles()
    )

    if player_class == "rogue":
        return {
            "assassin": first_rectangle,
            "archer": second_rectangle,
        }
    if player_class == "mage":
        return {
            "warlock": first_rectangle,
            "summoner": second_rectangle,
        }

    return {
        "berserker": first_rectangle,
        "paladin": second_rectangle,
    }


def draw_subclass_selection_screen(
    screen,
    title_font,
    heading_font,
    text_font,
    assets,
    mouse_position,
    selected_subclass,
    player_class,
):
    background = assets["background"]
    screen.blit(
        background,
        (
            (GAME_WIDTH - background.get_width()) // 2,
            GAME_HEIGHT - background.get_height(),
        ),
    )
    veil = pygame.Surface(
        (GAME_WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA,
    )
    veil.fill((3, 2, 5, 205))
    screen.blit(veil, (0, 0))

    is_rogue = player_class == "rogue"
    is_mage = player_class == "mage"
    title_color = (
        (70, 137, 230)
        if is_rogue
        else (163, 88, 221)
        if is_mage
        else (214, 70, 62)
    )
    title = title_font.render(
        "THE SECOND VEIL FALLS",
        True,
        title_color,
    )
    screen.blit(
        title,
        title.get_rect(center=(GAME_WIDTH // 2, 60)),
    )
    prompt = text_font.render(
        (
            "Choose what the rogue will become."
            if is_rogue
            else "Choose what the mage will become."
            if is_mage
            else "Choose what the warrior will become."
        ),
        True,
        TEXT_COLOR,
    )
    screen.blit(
        prompt,
        prompt.get_rect(center=(GAME_WIDTH // 2, 112)),
    )

    if is_rogue:
        card_configs = (
            {
                "name": "assassin",
                "number": 1,
                "title": "ASSASSIN",
                "description": (
                    "One blade. One breath. No witness."
                ),
                "portrait": "assassin_portrait",
                "color": (75, 143, 238),
                "dim_color": (39, 72, 116),
                "background": (9, 13, 22),
            },
            {
                "name": "archer",
                "number": 2,
                "title": "ARCHER",
                "description": (
                    "One arrow. One heartbeat. No escape."
                ),
                "portrait": "archer_portrait",
                "color": (105, 151, 76),
                "dim_color": (55, 79, 47),
                "background": (11, 17, 13),
            },
        )
    elif is_mage:
        card_configs = (
            {
                "name": "warlock",
                "number": 1,
                "title": "WARLOCK",
                "description": (
                    "One pact. Endless consequence."
                ),
                "portrait": "warlock_portrait",
                "color": (176, 91, 232),
                "dim_color": (88, 51, 111),
                "background": (17, 10, 22),
            },
            {
                "name": "summoner",
                "number": 2,
                "title": "SUMMONER",
                "description": (
                    "One call. Another world answers."
                ),
                "portrait": "summoner_portrait",
                "color": (77, 184, 193),
                "dim_color": (46, 94, 101),
                "background": (8, 18, 21),
            },
        )
    else:
        card_configs = (
            {
                "name": "berserker",
                "number": 1,
                "title": "BERSERKER",
                "description": "Two blades. No restraint.",
                "portrait": "berserker_portrait",
                "color": (225, 78, 62),
                "dim_color": (112, 54, 50),
                "background": (24, 13, 15),
            },
            {
                "name": "paladin",
                "number": 2,
                "title": "PALADIN",
                "description": "Sword. Shield. Unbroken oath.",
                "portrait": "paladin_portrait",
                "color": (218, 178, 86),
                "dim_color": (103, 87, 55),
                "background": (15, 16, 18),
            },
        )

    card_rectangles = _subclass_card_rectangles()

    for card_config, rectangle in zip(
        card_configs,
        card_rectangles,
    ):
        subclass = card_config["name"]
        hovered = (
            selected_subclass is None
            and mouse_position is not None
            and rectangle.collidepoint(mouse_position)
        )
        border_color = (
            card_config["color"]
            if hovered or selected_subclass == subclass
            else card_config["dim_color"]
        )
        pygame.draw.rect(
            screen,
            card_config["background"],
            rectangle,
            border_radius=12,
        )
        pygame.draw.rect(
            screen,
            border_color,
            rectangle,
            width=3,
            border_radius=12,
        )
        portrait = assets[card_config["portrait"]]
        screen.blit(
            portrait,
            portrait.get_rect(
                center=(rectangle.centerx, 285)
            ),
        )
        card_title = heading_font.render(
            (
                f"[{card_config['number']}] "
                f"{card_config['title']}"
            ),
            True,
            card_config["color"],
        )
        screen.blit(
            card_title,
            card_title.get_rect(
                center=(rectangle.centerx, 445)
            ),
        )
        description = text_font.render(
            card_config["description"],
            True,
            TEXT_COLOR,
        )
        screen.blit(
            description,
            description.get_rect(
                center=(rectangle.centerx, 490)
            ),
        )
        stat_changes = describe_player_stat_changes(
            player_stat_changes_between(
                CLASS_BASE_STATS[player_class],
                SUBCLASS_BASE_STATS[subclass],
            )
        )
        for index, stat_change in enumerate(stat_changes):
            stat_surface = text_font.render(
                stat_change,
                True,
                card_config["color"],
            )
            screen.blit(
                stat_surface,
                stat_surface.get_rect(
                    center=(rectangle.centerx, 525 + index * 24)
                ),
            )
        action_label = (
            "PATH CHOSEN"
            if selected_subclass == subclass
            else "CLICK TO CHOOSE"
            if hovered
            else f"PRESS {card_config['number']}"
        )
        action_surface = text_font.render(
            action_label,
            True,
            border_color,
        )
        screen.blit(
            action_surface,
            action_surface.get_rect(
                center=(rectangle.centerx, 585)
            ),
        )

