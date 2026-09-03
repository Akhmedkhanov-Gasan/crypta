import pygame

from acts.act_one.item_visuals import draw_potion_icon as _draw_potion
from acts.player_stats import player_stat_changes_for_attribute_upgrade
from presentation.hud import fit_text_to_width, get_event_color
from presentation.screens import (
    _draw_upgrade_icon,
    get_upgrade_card_rectangles,
)
from settings import (
    GAME_HEIGHT,
    GAME_WIDTH,
    MAX_ATTRIBUTE_RANK,
    MAX_CRIT_CHANCE,
    MAX_DODGE_CHANCE,
)


BACKGROUND = (17, 19, 24)
BORDER = (74, 76, 84)
TEXT = (224, 217, 199)
MUTED = (139, 140, 148)
GOLD = (190, 161, 105)
RED = (175, 54, 65)


def _panel(screen, rectangle, accent=BORDER, fill=BACKGROUND):
    rectangle = pygame.Rect(rectangle)
    cut = 7

    points = (
        (rectangle.left + cut, rectangle.top),
        (rectangle.right - cut, rectangle.top),
        (rectangle.right, rectangle.top + cut),
        (rectangle.right, rectangle.bottom - cut),
        (rectangle.right - cut, rectangle.bottom),
        (rectangle.left + cut, rectangle.bottom),
        (rectangle.left, rectangle.bottom - cut),
        (rectangle.left, rectangle.top + cut),
    )

    shadow = [(x + 3, y + 4) for x, y in points]
    pygame.draw.polygon(screen, (5, 6, 9), shadow)
    pygame.draw.polygon(screen, fill, points)
    pygame.draw.polygon(screen, accent, points, width=1)

    pygame.draw.line(
        screen,
        (91, 91, 98),
        (rectangle.left + cut + 2, rectangle.top + 2),
        (rectangle.right - cut - 2, rectangle.top + 2),
    )


def _text(screen, font, text, center, color=TEXT, maximum_width=None):
    surface = font.render(text, True, color)

    if maximum_width and surface.get_width() > maximum_width:
        ratio = maximum_width / surface.get_width()
        surface = pygame.transform.smoothscale(
            surface,
            (
                maximum_width,
                max(1, round(surface.get_height() * ratio)),
            ),
        )

    screen.blit(surface, surface.get_rect(center=center))


def _draw_health_panel(
    screen,
    title_font,
    log_font,
    player_health,
    player_max_health,
):
    rectangle = pygame.Rect(20, 40, 280, 84)
    ratio = max(
        0.0,
        min(1.0, player_health / max(1, player_max_health)),
    )
    low_health = ratio <= 0.3
    accent = (159, 66, 77) if low_health else (91, 84, 88)

    _panel(screen, rectangle, accent, (21, 19, 25))

    diamond_center = (rectangle.left + 19, rectangle.top + 21)
    x, y = diamond_center

    pygame.draw.polygon(
        screen,
        (202, 98, 104) if low_health else (160, 83, 94),
        (
            (x, y - 5),
            (x + 4, y),
            (x, y + 5),
            (x - 4, y),
        ),
    )

    label = log_font.render("HEALTH", True, (169, 151, 151))
    screen.blit(
        label,
        label.get_rect(
            midleft=(rectangle.left + 31, rectangle.top + 21),
        ),
    )

    health_text = title_font.render(
        f"{player_health} / {player_max_health}",
        True,
        (242, 155, 157) if low_health else (231, 218, 205),
    )
    screen.blit(
        health_text,
        health_text.get_rect(
            midright=(rectangle.right - 15, rectangle.top + 21),
        ),
    )

    bar = pygame.Rect(
        rectangle.left + 14,
        rectangle.top + 41,
        rectangle.width - 28,
        23,
    )

    pygame.draw.rect(
        screen,
        (42, 32, 41),
        bar.inflate(4, 4),
        border_radius=6,
    )
    pygame.draw.rect(
        screen,
        (7, 8, 12),
        bar,
        border_radius=4,
    )

    inner = bar.inflate(-4, -4)
    fill_width = round(inner.width * ratio)

    if fill_width > 0:
        gradient = pygame.Surface(inner.size, pygame.SRCALPHA)
        top_color = (209, 83, 94)
        bottom_color = (94, 23, 42)

        for row in range(inner.height):
            blend = row / max(1, inner.height - 1)
            color = tuple(
                round(start + (end - start) * blend)
                for start, end in zip(top_color, bottom_color)
            )
            pygame.draw.line(
                gradient,
                color,
                (0, row),
                (inner.width - 1, row),
            )

        mask = pygame.Surface(inner.size, pygame.SRCALPHA)
        pygame.draw.rect(
            mask,
            (255, 255, 255, 255),
            mask.get_rect(),
            border_radius=3,
        )
        gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        screen.blit(
            gradient,
            inner.topleft,
            pygame.Rect(0, 0, fill_width, inner.height),
        )

        if fill_width > 4:
            pygame.draw.line(
                screen,
                (234, 128, 131),
                (inner.left + 2, inner.top + 2),
                (inner.left + fill_width - 2, inner.top + 2),
            )

    pygame.draw.rect(
        screen,
        (80, 49, 62),
        bar,
        width=1,
        border_radius=4,
    )

    for fraction in (0.25, 0.5, 0.75):
        tick_x = inner.left + round(inner.width * fraction)
        pygame.draw.line(
            screen,
            (104, 77, 83),
            (tick_x, bar.bottom + 4),
            (tick_x, bar.bottom + 6),
        )


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
    _draw_health_panel(
        screen,
        title_font,
        log_font,
        player_health,
        player_max_health,
    )

    belt = pygame.Rect(
        GAME_WIDTH // 2 - 200,
        GAME_HEIGHT - 96,
        400,
        78,
    )
    _panel(screen, belt)

    for index in range(6):
        slot = pygame.Rect(
            belt.left + 16 + index * 62,
            belt.top + 10,
            54,
            58,
        )
        occupied = index < potion_count
        _panel(
            screen,
            slot,
            GOLD if occupied else (46, 49, 58),
            (27, 24, 29) if occupied else (12, 14, 19),
        )

        _text(
            screen,
            log_font,
            str(index + 1),
            (slot.left + 10, slot.top + 11),
            GOLD if occupied else (87, 90, 99),
        )

        if occupied:
            _draw_potion(screen, slot.center)
        else:
            pygame.draw.line(
                screen,
                (45, 48, 57),
                (slot.centerx - 5, slot.centery),
                (slot.centerx + 5, slot.centery),
            )

    journal = pygame.Rect(20, GAME_HEIGHT - 118, 350, 100)
    _panel(screen, journal)

    label = log_font.render("RECENT EVENTS", True, MUTED)
    screen.blit(label, (journal.left + 12, journal.top + 9))

    line_height = log_font.get_linesize()
    for index, message in enumerate(combat_log[-3:]):
        visible_text = fit_text_to_width(
            log_font,
            message,
            journal.width - 24,
        )
        surface = log_font.render(
            visible_text,
            True,
            get_event_color(message),
        )
        screen.blit(
            surface,
            (
                journal.left + 12,
                journal.top + 31 + index * line_height,
            ),
        )


def get_act_one_upgrade_card_rectangles():
    return get_upgrade_card_rectangles(False)


def draw_act_one_upgrade_screen(
    screen,
    title_font,
    text_font,
    player,
    upgrades_remaining,
    message,
    mouse_position=None,
):
    overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 205))
    screen.blit(overlay, (0, 0))

    _panel(screen, pygame.Rect(170, 76, 940, 540))

    _text(
        screen,
        title_font,
        "DESCENT ALTAR",
        (GAME_WIDTH // 2, 118),
        TEXT,
        850,
    )

    instruction = (
        f"{upgrades_remaining} BLESSING"
        f"{'S' if upgrades_remaining != 1 else ''} AVAILABLE"
        if upgrades_remaining > 0
        else "ALL BLESSINGS CHOSEN"
    )
    _text(
        screen,
        text_font,
        instruction,
        (GAME_WIDTH // 2, 164),
        GOLD,
    )

    stats = (
        f"HP {player.health}/{player.max_health}    "
        f"DAMAGE {player.damage_min}-{player.damage_max}    "
        f"CRIT {player.crit_chance:.0%}    "
        f"DODGE {player.dodge_chance:.0%}"
    )
    _text(
        screen,
        text_font,
        stats,
        (GAME_WIDTH // 2, 205),
        MUTED,
        860,
    )

    accents = {
        "strength": (181, 92, 79),
        "dexterity": (188, 158, 94),
        "vitality": (155, 102, 134),
    }

    rectangles = get_act_one_upgrade_card_rectangles()

    for index, (attribute, rectangle) in enumerate(rectangles.items(), 1):
        rank = player.attribute_ranks[attribute]
        capped = rank >= MAX_ATTRIBUTE_RANK
        enabled = upgrades_remaining > 0 and not capped
        hovered = (
            enabled
            and mouse_position is not None
            and rectangle.collidepoint(mouse_position)
        )
        accent = accents[attribute] if enabled else (79, 80, 89)

        _panel(
            screen,
            rectangle,
            accent if hovered else BORDER,
            (33, 33, 40) if hovered else BACKGROUND,
        )

        _text(
            screen,
            text_font,
            str(index),
            (rectangle.left + 23, rectangle.top + 23),
            accent,
        )

        _draw_upgrade_icon(
            screen,
            attribute,
            (rectangle.centerx, rectangle.top + 43),
            accent,
        )

        _text(
            screen,
            text_font,
            attribute.upper(),
            (rectangle.centerx, rectangle.top + 86),
            TEXT if enabled else MUTED,
        )
        _text(
            screen,
            text_font,
            f"RANK {rank}",
            (rectangle.centerx, rectangle.top + 117),
            MUTED,
        )

        change = player_stat_changes_for_attribute_upgrade(attribute, rank)

        if capped:
            lines = ("MAXIMUM RANK",)
        elif attribute == "strength":
            lines = (
                "ATTACK DAMAGE",
                (
                    f"{player.damage_min}-{player.damage_max}  ->  "
                    f"{player.damage_min + change.damage_min}-"
                    f"{player.damage_max + change.damage_max}"
                ),
            )
        elif attribute == "dexterity":
            next_crit = min(MAX_CRIT_CHANCE, player.crit_chance + change.crit_chance)
            next_dodge = min(MAX_DODGE_CHANCE, player.dodge_chance + change.dodge_chance)
            next_multiplier = (
                player.critical_damage_multiplier
                + change.critical_damage_multiplier
            )
            lines = (
                f"CRIT {player.crit_chance:.0%}  ->  {next_crit:.0%}",
                f"DODGE {player.dodge_chance:.0%}  ->  {next_dodge:.0%}",
                (
                    f"CRIT DAMAGE x{player.critical_damage_multiplier:.2f}"
                    f"  ->  x{next_multiplier:.2f}"
                ),
            )
        else:
            lines = (
                "MAXIMUM HEALTH",
                f"{player.max_health}  ->  {player.max_health + change.max_health} HP",
            )

        for line_index, line in enumerate(lines):
            _text(
                screen,
                text_font,
                line,
                (
                    rectangle.centerx,
                    rectangle.top + 157 + line_index * 29,
                ),
                accent,
                rectangle.width - 28,
            )

    if message:
        _text(
            screen,
            text_font,
            message,
            (GAME_WIDTH // 2, 526),
            GOLD,
            850,
        )

    footer = (
        "CHOOSE A BLESSING TO DESCEND"
        if upgrades_remaining > 0
        else "[ENTER] DESCEND"
    )
    _text(
        screen,
        text_font,
        footer,
        (GAME_WIDTH // 2, 578),
        MUTED,
    )
