import pygame

from acts.act_two.progression import (
    get_act_two_upgrade_order,
)
from acts.player_stats import player_stat_changes_for_attribute_upgrade
from presentation.layout import GAME_HEIGHT, GAME_WIDTH
from presentation.screens import _draw_upgrade_icon
from settings import MAX_ATTRIBUTE_RANK


_PANEL_POSITION = (170, 66)
_CARD_POSITIONS = (
    pygame.Rect(210, 260, 410, 132),
    pygame.Rect(660, 260, 410, 132),
    pygame.Rect(210, 414, 410, 132),
    pygame.Rect(660, 414, 410, 132),
)
_CLASS_COLORS = {
    "warrior": (202, 66, 58),
    "rogue": (151, 87, 190),
    "mage": (69, 126, 215),
}
_CLASS_TITLES = {
    "warrior": "WARRIOR'S OATH",
    "rogue": "ROGUE'S VEIL",
    "mage": "MAGE'S COVENANT",
}


def get_act_two_upgrade_card_rectangles(player_class="warrior"):
    return dict(
        zip(
            get_act_two_upgrade_order(player_class),
            _CARD_POSITIONS,
        )
    )


def _fit_text(font, text, maximum_width):
    if font.size(text)[0] <= maximum_width:
        return text
    ellipsis = "..."
    while text and font.size(text + ellipsis)[0] > maximum_width:
        text = text[:-1]
    return text.rstrip() + ellipsis


def _draw_card_icon(screen, sprites, kind, center, color):
    _draw_upgrade_icon(screen, kind, center, color)


def _attribute_card(player, attribute):
    rank = player.attribute_ranks[attribute]
    change = player_stat_changes_for_attribute_upgrade(attribute, rank)
    capped = rank >= MAX_ATTRIBUTE_RANK

    if attribute == "strength":
        description = "Attack damage"
        if player.player_class == "warrior":
            description = "Attack + Cleave"
        return (
            "STRENGTH",
            description,
            (
                f"{player.damage_min}-{player.damage_max} > "
                f"{player.damage_min + change.damage_min}-"
                f"{player.damage_max + change.damage_max}"
            ),
            capped,
        )
    if attribute == "dexterity":
        description = "Crit / dodge / crit damage"
        if player.player_class == "rogue":
            description = "Crit / dodge / ambush"
        return (
            "DEXTERITY",
            description,
            (
                f"{round(player.crit_chance * 100)}/"
                f"{round(player.dodge_chance * 100)}% > "
                f"{round((player.crit_chance + change.crit_chance) * 100)}/"
                f"{round((player.dodge_chance + change.dodge_chance) * 100)}% | "
                f"x{player.critical_damage_multiplier:.1f} > "
                f"x{player.critical_damage_multiplier + change.critical_damage_multiplier:.1f}"
            ),
            capped,
        )
    if attribute == "intelligence":
        description = "Spell power"
        if player.player_class == "mage":
            description = "Spell power + Burst"
        elif player.player_class == "rogue":
            description = "Spell power + future skills"
        return (
            "INTELLIGENCE",
            description,
            f"{player.spell_power} > {player.spell_power + change.spell_power}",
            capped,
        )
    return (
        "VITALITY",
        "Maximum health",
        f"{player.max_health} > {player.max_health + change.max_health} HP",
        capped,
    )


def _upgrade_card_data(player, upgrade):
    return _attribute_card(player, upgrade)


def _draw_upgrade_card(
    screen,
    text_font,
    sprites,
    rectangle,
    upgrade,
    player,
    accent,
    hovered,
):
    title, description, value, capped = _upgrade_card_data(player, upgrade)
    disabled = player.attribute_points <= 0 or capped

    if disabled or hovered:
        overlay = pygame.Surface(rectangle.size, pygame.SRCALPHA)
        overlay.fill(
            (4, 4, 6, 105)
            if disabled
            else (*accent, 24)
        )
        screen.blit(overlay, rectangle)
    if hovered and not disabled:
        pygame.draw.rect(screen, accent, rectangle, width=2)

    icon_color = accent if not disabled else (77, 72, 79)
    _draw_card_icon(
        screen,
        sprites,
        upgrade,
        (rectangle.x + 68, rectangle.centery + 1),
        icon_color,
    )
    text_color = (225, 216, 205) if not disabled else (105, 100, 108)
    screen.blit(
        text_font.render(title, True, text_color),
        (rectangle.x + 112, rectangle.y + 20),
    )
    current_value_surface = text_font.render(
        f"CURRENT: {player.attribute_ranks[upgrade]}",
        True,
        (137, 131, 136) if not disabled else (82, 78, 85),
    )
    screen.blit(
        current_value_surface,
        current_value_surface.get_rect(
            topright=(rectangle.right - 20, rectangle.y + 20)
        ),
    )
    maximum_text_width = rectangle.width - 128
    screen.blit(
        text_font.render(
            _fit_text(text_font, description, maximum_text_width),
            True,
            (166, 157, 157) if not disabled else (91, 87, 94),
        ),
        (rectangle.x + 112, rectangle.y + 53),
    )
    screen.blit(
        text_font.render(
            _fit_text(text_font, value, maximum_text_width),
            True,
            accent if not disabled else (82, 78, 85),
        ),
        (rectangle.x + 112, rectangle.y + 86),
    )


def _summary_text(player):
    summary = (
        f"HP {player.health}/{player.max_health}     "
        f"DAMAGE {player.damage_min}-{player.damage_max}     "
        f"CRIT {round(player.crit_chance * 100)}% x"
        f"{player.critical_damage_multiplier:.1f}     "
        f"DODGE {round(player.dodge_chance * 100)}%"
    )
    summary += f"     SPELL {player.spell_power}"
    return summary


def draw_act_two_upgrade_screen(
    screen,
    title_font,
    text_font,
    player,
    sprites,
    message,
    mouse_position=None,
    reward_pending=False,
):
    overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 218))
    screen.blit(overlay, (0, 0))
    screen.blit(sprites["upgrade_window"], _PANEL_POSITION)

    player_class = player.player_class or "warrior"
    accent = _CLASS_COLORS[player_class]
    portrait = pygame.transform.smoothscale(
        sprites[f"{player_class}_portrait"],
        (64, 64),
    )
    screen.blit(portrait, (220, 127))
    screen.blit(
        title_font.render(_CLASS_TITLES[player_class], True, (215, 202, 186)),
        (302, 117),
    )
    points = player.attribute_points
    blessings = (
        f"{points} ATTRIBUTE POINT"
        f"{'S' if points != 1 else ''} AVAILABLE"
    )
    screen.blit(
        text_font.render(blessings, True, (216, 161, 74)),
        (305, 163),
    )
    summary_surface = text_font.render(
        _summary_text(player),
        True,
        (190, 184, 181),
    )
    screen.blit(
        summary_surface,
        summary_surface.get_rect(center=(GAME_WIDTH // 2, 222)),
    )

    order = get_act_two_upgrade_order(player_class)
    rectangles = get_act_two_upgrade_card_rectangles(player_class)
    for upgrade in order:
        rectangle = rectangles[upgrade]
        _draw_upgrade_card(
            screen,
            text_font,
            sprites,
            rectangle,
            upgrade,
            player,
            accent,
            (
                mouse_position is not None
                and rectangle.collidepoint(mouse_position)
            ),
        )

    if message:
        message_surface = text_font.render(message, True, (222, 165, 78))
        screen.blit(
            message_surface,
            message_surface.get_rect(center=(GAME_WIDTH // 2, 574)),
        )
    footer_text = (
        "CHOOSE ONE UPGRADE"
        if reward_pending
        else "[ENTER] DESCEND"
    )
    footer = text_font.render(
        footer_text,
        True,
        (171, 164, 168),
    )
    screen.blit(
        footer,
        footer.get_rect(
            center=(GAME_WIDTH // 2, 604 if message else 590)
        ),
    )
