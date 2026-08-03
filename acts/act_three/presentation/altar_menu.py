import pygame

from game.progression import (
    MAX_ATTRIBUTE_RANK,
    can_upgrade_attribute,
    experience_required_for_level,
)

ALTAR_MENU_RECT = pygame.Rect(140, 65, 1000, 590)
ALTAR_MENU_CLOSE_RECT = pygame.Rect(1082, 83, 38, 38)

_TAB_NAMES = ("attributes", "abilities", "passives")
_TAB_RECTS = {
    name: pygame.Rect(210 + index * 290, 181, 280, 58)
    for index, name in enumerate(_TAB_NAMES)
}
_CARD_RECTS = {
    "vitality": pygame.Rect(210, 244, 410, 205),
    "power": pygame.Rect(650, 244, 410, 205),
    "precision": pygame.Rect(210, 446, 410, 205),
    "evasion": pygame.Rect(650, 446, 410, 205),
}
_BUTTON_RECTS = {
    name: pygame.Rect(rectangle.x + 40, rectangle.y + 154, 330, 42)
    for name, rectangle in _CARD_RECTS.items()
}


def get_upgrade_altar_menu_control_at(position):
    if ALTAR_MENU_CLOSE_RECT.collidepoint(position):
        return "close"

    for name, rectangle in _TAB_RECTS.items():
        if rectangle.collidepoint(position):
            return f"tab:{name}"

    for name, rectangle in _BUTTON_RECTS.items():
        if rectangle.collidepoint(position):
            return f"upgrade:{name}"

    return None


def _draw_centered_text(surface, font, text, color, center):
    text_surface = font.render(text, True, color)
    surface.blit(
        text_surface,
        text_surface.get_rect(center=center),
    )


def _tinted_copy(source, color):
    tinted = source.copy()
    tinted.fill(color, special_flags=pygame.BLEND_RGBA_ADD)
    return tinted


def _draw_tabs(screen, game_state, fonts, assets):
    active_tab = game_state.upgrade_altar_menu_tab
    hovered = game_state.upgrade_altar_menu_hovered_control

    for name, rectangle in _TAB_RECTS.items():
        tab_surface = assets["altar_menu_tab"]
        if name == active_tab:
            tab_surface = _tinted_copy(
                tab_surface,
                (12, 30, 62, 0),
            )
        elif hovered == f"tab:{name}":
            tab_surface = _tinted_copy(
                tab_surface,
                (9, 18, 34, 0),
            )

        screen.blit(tab_surface, rectangle)
        label = name.upper()
        if name == "passives":
            label = "PASSIVES  ·  SOON"
        _draw_centered_text(
            screen,
            fonts["sidebar_heading"],
            label,
            (216, 207, 190) if name == active_tab else (139, 132, 142),
            rectangle.center,
        )


def _attribute_card_data(player):
    return {
        "vitality": (
            "VITALITY",
            f"HP  {player.health} / {player.max_health}",
            "+2 MAX HP",
        ),
        "power": (
            "POWER",
            f"DAMAGE  {player.damage_min}-{player.damage_max}",
            "+1 DAMAGE",
        ),
        "precision": (
            "PRECISION",
            f"CRITICAL  {round(player.crit_chance * 100)}%",
            "+5% CRITICAL CHANCE",
        ),
        "evasion": (
            "EVASION",
            f"DODGE  {round(player.dodge_chance * 100)}%",
            "+5% DODGE CHANCE",
        ),
    }


def _draw_attribute_cards(screen, game_state, fonts, assets):
    hovered = game_state.upgrade_altar_menu_hovered_control
    card_data = _attribute_card_data(game_state.player)

    for name, rectangle in _CARD_RECTS.items():
        screen.blit(assets["altar_menu_card"], rectangle)
        can_upgrade = can_upgrade_attribute(game_state.player, name)
        if hovered == f"upgrade:{name}" and can_upgrade:
            pygame.draw.rect(
                screen,
                (73, 142, 230),
                rectangle,
                width=3,
                border_radius=5,
            )

        screen.blit(
            assets[f"altar_menu_{name}"],
            (rectangle.x + 24, rectangle.y + 33),
        )
        title, current_value, next_value = card_data[name]
        text_x = rectangle.x + 116
        screen.blit(
            fonts["heading"].render(
                title,
                True,
                (226, 203, 160),
            ),
            (text_x, rectangle.y + 24),
        )
        screen.blit(
            fonts["sidebar_text"].render(
                current_value,
                True,
                (216, 207, 190),
            ),
            (text_x, rectangle.y + 69),
        )
        screen.blit(
            fonts["sidebar_text"].render(
                next_value,
                True,
                (102, 171, 239),
            ),
            (text_x, rectangle.y + 103),
        )

        current_rank = game_state.player.attribute_ranks[name]
        for rank_index in range(MAX_ATTRIBUTE_RANK):
            screen.blit(
                assets[
                    "altar_menu_rank_filled"
                    if rank_index < current_rank
                    else "altar_menu_rank_empty"
                ],
                (
                    text_x + rank_index * 22,
                    rectangle.y + 132,
                ),
            )

        button_rectangle = _BUTTON_RECTS[name]
        button_surface = assets["altar_menu_button"]
        if not can_upgrade:
            button_surface = button_surface.copy()
            button_surface.set_alpha(105)
        screen.blit(button_surface, button_rectangle)
        if current_rank >= MAX_ATTRIBUTE_RANK:
            button_label = "MAX RANK"
        elif game_state.player.attribute_points <= 0:
            button_label = "NO ATTRIBUTE POINTS"
        else:
            button_label = "UPGRADE  ·  1"
        _draw_centered_text(
            screen,
            fonts["sidebar_heading"],
            button_label,
            (185, 178, 165) if can_upgrade else (103, 98, 107),
            button_rectangle.center,
        )


def _draw_placeholder(screen, game_state, fonts):
    tab_name = game_state.upgrade_altar_menu_tab.upper()
    _draw_centered_text(
        screen,
        fonts["heading"],
        tab_name,
        (226, 203, 160),
        (640, 355),
    )
    _draw_centered_text(
        screen,
        fonts["sidebar_heading"],
        "COMING SOON",
        (102, 171, 239),
        (640, 402),
    )


def draw_upgrade_altar_menu(
    screen,
    game_state,
    fonts,
    assets,
):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((2, 3, 8, 205))
    screen.blit(overlay, (0, 0))
    screen.blit(assets["altar_menu_panel"], ALTAR_MENU_RECT)

    _draw_centered_text(
        screen,
        fonts["title"],
        "ALTAR OF ASCENSION",
        (226, 203, 160),
        (640, 105),
    )

    player = game_state.player
    experience_required = experience_required_for_level(player.level)
    experience_ratio = max(
        0,
        min(1, player.experience / experience_required),
    )
    experience_bar_position = (356, 136)
    screen.blit(
        assets["altar_menu_xp_bar"],
        experience_bar_position,
    )
    experience_fill = pygame.Rect(
        experience_bar_position[0] + 9,
        experience_bar_position[1] + 8,
        round(302 * experience_ratio),
        18,
    )
    if experience_fill.width > 0:
        pygame.draw.rect(
            screen,
            (31, 111, 189),
            experience_fill,
            border_radius=2,
        )
        pygame.draw.line(
            screen,
            (92, 191, 239),
            (experience_fill.left + 1, experience_fill.top + 1),
            (experience_fill.right - 2, experience_fill.top + 1),
        )
    _draw_centered_text(
        screen,
        fonts["sidebar_text"],
        (
            f"LEVEL {player.level}  ·  "
            f"XP {player.experience}/{experience_required}"
        ),
        (211, 235, 247),
        (516, 153),
    )
    screen.blit(
        assets["altar_menu_attribute_point"],
        (725, 141),
    )
    screen.blit(
        fonts["sidebar_text"].render(
            f"ATTRIBUTE POINTS  {player.attribute_points}",
            True,
            (185, 178, 165),
        ),
        (755, 143),
    )

    close_hovered = (
        game_state.upgrade_altar_menu_hovered_control
        == "close"
    )
    pygame.draw.rect(
        screen,
        (38, 45, 63) if close_hovered else (22, 20, 27),
        ALTAR_MENU_CLOSE_RECT,
        border_radius=4,
    )
    pygame.draw.rect(
        screen,
        (102, 171, 239) if close_hovered else (91, 78, 69),
        ALTAR_MENU_CLOSE_RECT,
        width=2,
        border_radius=4,
    )
    _draw_centered_text(
        screen,
        fonts["sidebar_heading"],
        "X",
        (216, 207, 190),
        ALTAR_MENU_CLOSE_RECT.center,
    )

    _draw_tabs(screen, game_state, fonts, assets)
    if game_state.upgrade_altar_menu_tab == "attributes":
        _draw_attribute_cards(
            screen,
            game_state,
            fonts,
            assets,
        )
    else:
        _draw_placeholder(screen, game_state, fonts)
