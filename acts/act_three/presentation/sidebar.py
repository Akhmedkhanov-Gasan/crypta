import math

import pygame

from game.progression import experience_required_for_level
from presentation.hud import get_event_color, wrap_text
from presentation.layout import (
    ACT_THREE_BOTTOM_BAR_HEIGHT,
    ACT_THREE_BOTTOM_BAR_WIDTH,
    ACT_THREE_BOTTOM_BAR_X,
    ACT_THREE_BOTTOM_BAR_Y,
    ACT_THREE_SIDEBAR_WIDTH,
    ACT_THREE_SIDEBAR_X,
    ACT_THREE_VIEW_HEIGHT,
)
from settings import (
    ARCHER_BARRAGE_ZONE_CHARGES,
    ARCHER_EMPOWERED_SHOT_CHARGES,
    ARCHER_LEAP_CHARGES,
    ASSASSIN_TELEPORT_CHARGES,
    ASSASSIN_ULTIMATE_CHARGES,
    BERSERKER_CRUSHING_LEAP_CHARGES,
    BERSERKER_LAST_RAGE_CHARGES,
    BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER,
    BERSERKER_RAGE_CRITICAL_HEALTH_RATIO,
    BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER,
    BERSERKER_RAGE_INJURED_HEALTH_RATIO,
    CLASS_ABILITY_KILLS,
    PALADIN_HOLY_HAND_CHARGES,
    PALADIN_HOLY_SHIELD_CHARGES,
    PALADIN_HOLY_SHIELD_DAMAGE_BONUS,
    PALADIN_SHIELD_CHARGE_CHARGES,
    SUMMONER_BOND_CHARGES,
    SUMMONER_FAMILIAR_CHARGES,
    SUMMONER_TRUE_FORM_CHARGES,
    WARLOCK_CURSE_CHARGES,
    WARLOCK_SOUL_EXCHANGE_CHARGES,
)


_PANEL_BACKGROUND = (8, 11, 14)
_PANEL_INNER = (12, 16, 19)
_SECTION_FILL = (15, 20, 23)
_SECTION_BORDER = (52, 67, 70)
_SECTION_HIGHLIGHT = (77, 94, 95)
_SLOT_FILL = (7, 10, 12)
_MUTED_TEXT = (132, 145, 145)
_BRIGHT_TEXT = (234, 232, 226)

_SUBCLASS_PRESENTATION = {
    "paladin": ("PALADIN", (206, 168, 80)),
    "assassin": ("ASSASSIN", (69, 130, 221)),
    "archer": ("ARCHER", (105, 151, 76)),
    "warlock": ("WARLOCK", (176, 91, 232)),
    "summoner": ("SUMMONER", (77, 184, 193)),
    "berserker": ("BERSERKER", (205, 68, 58)),
}

_ABILITY_DESCRIPTIONS = {
    "assassin_invisibility": "Vanish and prepare a stronger ambush.",
    "assassin_teleport": "Teleport to a selected visible position.",
    "assassin_killing_spree": "Chain rapid attacks across marked targets.",
    "archer_empowered_shot": "Fire a stronger long-range shot.",
    "archer_leap": "Leap to the selected cell.",
    "archer_barrage_zone": "Mark an area for a rain of arrows.",
    "berserker_rage": "Damage rises as health falls.",
    "berserker_crushing_leap": "Leap and strike an area on landing.",
    "berserker_last_rage": "Enter a temporary state of extreme rage.",
    "paladin_holy_hand": "Restore health with holy power.",
    "paladin_shield_charge": "Rush forward behind the shield.",
    "paladin_holy_shield": "Gain a temporary holy shield.",
    "warlock_curse": "Curse a target for several turns.",
    "warlock_soul_exchange": "Exchange positions with a target.",
    "warlock_demon_form": "Trade health for demonic power.",
    "summoner_familiar": "Summon or release the familiar.",
    "summoner_bond": "Strengthen the bond with the familiar.",
    "summoner_true_form": "Unite with the familiar temporarily.",
}


def _draw_label(surface, font, text, color, position):
    surface.blit(font.render(text, True, color), position)


_RAIL_BUTTON_SIZE = 52
_RAIL_BUTTON_GAP = 9
_RAIL_BUTTON_NAMES = ("inventory", "stats", "abilities", "log", "settings")


def get_act_three_sidebar_tab_rectangles():
    total_height = (
        len(_RAIL_BUTTON_NAMES) * _RAIL_BUTTON_SIZE
        + (len(_RAIL_BUTTON_NAMES) - 1) * _RAIL_BUTTON_GAP
    )
    top = (ACT_THREE_VIEW_HEIGHT - total_height) // 2
    left = ACT_THREE_SIDEBAR_X + (
        ACT_THREE_SIDEBAR_WIDTH - _RAIL_BUTTON_SIZE
    ) // 2
    return {
        name: pygame.Rect(
            left,
            top + index * (_RAIL_BUTTON_SIZE + _RAIL_BUTTON_GAP),
            _RAIL_BUTTON_SIZE,
            _RAIL_BUTTON_SIZE,
        )
        for index, name in enumerate(_RAIL_BUTTON_NAMES)
    }


def get_act_three_panel_close_rectangle():
    return pygame.Rect(ACT_THREE_SIDEBAR_X - 35, 68, 22, 22)


def get_act_three_popup_rectangle():
    return pygame.Rect(ACT_THREE_SIDEBAR_X - 342, 58, 330, 420)


def get_act_three_bottom_hud_rectangles():
    return (
        pygame.Rect(304, ACT_THREE_BOTTOM_BAR_Y + 4, 388, 80),
        pygame.Rect(704, ACT_THREE_BOTTOM_BAR_Y + 4, 318, 80),
    )


def get_act_three_log_panel_rect():
    return pygame.Rect(0, 0, 0, 0)


def get_act_three_log_arrow_rectangles():
    """The compact event area deliberately has no scrolling controls."""
    return {}


def _draw_panel_background(screen):
    bottom_panel = pygame.Rect(
        ACT_THREE_BOTTOM_BAR_X,
        ACT_THREE_BOTTOM_BAR_Y,
        ACT_THREE_BOTTOM_BAR_WIDTH,
        ACT_THREE_BOTTOM_BAR_HEIGHT,
    )
    shade = pygame.Surface(bottom_panel.size, pygame.SRCALPHA)
    shade.fill((*_PANEL_BACKGROUND, 242))
    screen.blit(shade, bottom_panel)
    pygame.draw.line(
        screen,
        (85, 99, 98),
        bottom_panel.topleft,
        bottom_panel.topright,
        2,
    )
    pygame.draw.line(
        screen,
        (29, 39, 42),
        bottom_panel.topleft,
        bottom_panel.topright,
        2,
    )
    for grain_y in range(bottom_panel.top + 9, bottom_panel.bottom, 19):
        for grain_x in range(bottom_panel.left + 11, bottom_panel.right, 23):
            if (grain_x * 7 + grain_y * 11) % 5 == 0:
                screen.set_at((grain_x, grain_y), (20, 25, 27))


def _draw_section(screen, rectangle, title, font, accent=None):
    pygame.draw.rect(screen, _SECTION_FILL, rectangle)
    pygame.draw.rect(screen, _SECTION_BORDER, rectangle, width=1)
    pygame.draw.line(
        screen,
        _SECTION_HIGHLIGHT,
        (rectangle.left + 1, rectangle.top + 1),
        (rectangle.right - 2, rectangle.top + 1),
    )
    corner_color = accent or _SECTION_BORDER
    corner_size = 3
    for corner in (
        (rectangle.left, rectangle.top),
        (rectangle.right - corner_size, rectangle.top),
        (rectangle.left, rectangle.bottom - corner_size),
        (rectangle.right - corner_size, rectangle.bottom - corner_size),
    ):
        pygame.draw.rect(
            screen,
            corner_color,
            (*corner, corner_size, corner_size),
        )
    if title:
        title_surface = font.render(title, True, _BRIGHT_TEXT)
        title_background = pygame.Rect(
            rectangle.left + 9,
            rectangle.top - 1,
            title_surface.get_width() + 12,
            20,
        )
        pygame.draw.rect(screen, _SECTION_FILL, title_background)
        screen.blit(title_surface, (rectangle.left + 15, rectangle.top + 1))


def _draw_bar(screen, rectangle, ratio, fill_color, label, font):
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(screen, (5, 8, 10), rectangle)
    fill = rectangle.inflate(-4, -4)
    fill.width = round(fill.width * ratio)
    if fill.width > 0:
        pygame.draw.rect(screen, fill_color, fill)
        pygame.draw.line(
            screen,
            tuple(min(255, channel + 44) for channel in fill_color),
            (fill.left, fill.top),
            (fill.right - 1, fill.top),
        )
    pygame.draw.rect(screen, _SECTION_BORDER, rectangle, width=1)
    label_surface = font.render(label, True, _BRIGHT_TEXT)
    screen.blit(label_surface, label_surface.get_rect(center=rectangle.center))


def _ratio(value, maximum):
    if maximum <= 0:
        return 0.0
    return max(0.0, min(1.0, value / maximum))


def _ability_entries(player, accent_color):
    if player.subclass == "archer":
        return (
            (
                "archer_empowered_shot",
                "Empowered Shot",
                _ratio(
                    player.archer_empowered_shot_charge,
                    ARCHER_EMPOWERED_SHOT_CHARGES,
                ),
                accent_color,
                None,
            ),
            (
                "archer_leap",
                "Leap",
                _ratio(player.archer_leap_charge, ARCHER_LEAP_CHARGES),
                accent_color,
                None,
            ),
            (
                "archer_barrage_zone",
                "Barrage Zone",
                _ratio(
                    player.archer_barrage_zone_charge,
                    ARCHER_BARRAGE_ZONE_CHARGES,
                ),
                accent_color,
                None,
            ),
        )
    if player.subclass == "berserker":
        return (
            ("berserker_rage", "Rage", 1.0, (220, 72, 58), "PASSIVE"),
            (
                "berserker_crushing_leap",
                "Crushing Leap",
                _ratio(
                    player.berserker_crushing_leap_charge,
                    BERSERKER_CRUSHING_LEAP_CHARGES,
                ),
                (220, 72, 58),
                None,
            ),
            (
                "berserker_last_rage",
                "Last Rage",
                (
                    1.0
                    if player.berserker_last_rage_turns > 0
                    else _ratio(
                        player.berserker_last_rage_charge,
                        BERSERKER_LAST_RAGE_CHARGES,
                    )
                ),
                (245, 54, 45),
                (
                    f"{player.berserker_last_rage_turns} TURNS"
                    if player.berserker_last_rage_turns > 0
                    else None
                ),
            ),
        )
    if player.subclass == "paladin":
        return (
            (
                "paladin_holy_hand",
                "Holy Hand",
                _ratio(
                    player.paladin_holy_hand_charge,
                    PALADIN_HOLY_HAND_CHARGES,
                ),
                (239, 194, 78),
                None,
            ),
            (
                "paladin_shield_charge",
                "Shield Charge",
                _ratio(
                    player.paladin_shield_charge_charge,
                    PALADIN_SHIELD_CHARGE_CHARGES,
                ),
                (239, 194, 78),
                None,
            ),
            (
                "paladin_holy_shield",
                "Holy Shield",
                (
                    1.0
                    if player.paladin_holy_shield_turns > 0
                    else _ratio(
                        player.paladin_holy_shield_charge,
                        PALADIN_HOLY_SHIELD_CHARGES,
                    )
                ),
                (255, 219, 116),
                (
                    f"{player.paladin_holy_shield_turns} TURNS"
                    if player.paladin_holy_shield_turns > 0
                    else None
                ),
            ),
        )
    if player.subclass == "warlock":
        return (
            (
                "warlock_curse",
                "Curse",
                _ratio(player.warlock_curse_charge, WARLOCK_CURSE_CHARGES),
                (198, 91, 238),
                None,
            ),
            (
                "warlock_soul_exchange",
                "Soul Exchange",
                _ratio(
                    player.warlock_soul_exchange_charge,
                    WARLOCK_SOUL_EXCHANGE_CHARGES,
                ),
                (184, 78, 224),
                None,
            ),
            (
                "warlock_demon_form",
                "Demon Form",
                1.0,
                (220, 67, 194),
                "ACTIVE" if player.warlock_demon_form_active else "READY",
            ),
        )
    if player.subclass == "summoner":
        return (
            (
                "summoner_familiar",
                "Release Familiar",
                _ratio(
                    player.summoner_familiar_charge,
                    SUMMONER_FAMILIAR_CHARGES,
                ),
                (74, 207, 202),
                None,
            ),
            (
                "summoner_bond",
                "Bond",
                _ratio(player.summoner_bond_charge, SUMMONER_BOND_CHARGES),
                (74, 207, 202),
                None,
            ),
            (
                "summoner_true_form",
                "True Form",
                _ratio(
                    player.summoner_true_form_charge,
                    SUMMONER_TRUE_FORM_CHARGES,
                ),
                (91, 224, 238),
                None,
            ),
        )
    return (
        (
            "assassin_invisibility",
            "Invisibility",
            _ratio(player.ability_kill_charge, CLASS_ABILITY_KILLS),
            accent_color,
            None,
        ),
        (
            "assassin_teleport",
            "Teleport",
            _ratio(player.teleport_charge, ASSASSIN_TELEPORT_CHARGES),
            accent_color,
            None,
        ),
        (
            "assassin_killing_spree",
            "Killing Spree",
            _ratio(player.ultimate_charge, ASSASSIN_ULTIMATE_CHARGES),
            (205, 68, 74),
            None,
        ),
    )


def _damage_value(player):
    damage_text = f"{player.damage_min}-{player.damage_max}"
    bonus_minimum = 0
    bonus_maximum = 0
    if player.subclass == "berserker":
        health_ratio = player.health / player.max_health
        if (
            player.berserker_last_rage_turns > 0
            or health_ratio <= BERSERKER_RAGE_CRITICAL_HEALTH_RATIO
        ):
            multiplier = BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER
        elif health_ratio <= BERSERKER_RAGE_INJURED_HEALTH_RATIO:
            multiplier = BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER
        else:
            multiplier = 1.0
        bonus_minimum = math.ceil(player.damage_min * multiplier) - player.damage_min
        bonus_maximum = math.ceil(player.damage_max * multiplier) - player.damage_max
    elif player.subclass == "paladin" and player.paladin_holy_shield_turns > 0:
        bonus_minimum = PALADIN_HOLY_SHIELD_DAMAGE_BONUS
        bonus_maximum = PALADIN_HOLY_SHIELD_DAMAGE_BONUS
    if bonus_maximum > 0:
        bonus = (
            f"+{bonus_minimum}"
            if bonus_minimum == bonus_maximum
            else f"+{bonus_minimum}-{bonus_maximum}"
        )
        damage_text += bonus
    return damage_text


def _draw_header(screen, player, fonts, assets, accent_color, subclass_name):
    frame_position = (8, 4)
    portrait_rect = pygame.Rect(45, 25, 86, 84)
    pygame.draw.rect(screen, _SLOT_FILL, portrait_rect)
    portrait = assets.get("character_portrait_placeholder")
    if portrait is not None:
        screen.blit(portrait, portrait_rect)

    health_rect = pygame.Rect(148, 53, 246, 18)
    experience_rect = pygame.Rect(148, 87, 246, 19)
    experience_required = experience_required_for_level(player.level)
    frame = assets.get("character_hud_frame")
    if frame is not None:
        screen.blit(frame, frame_position)

    for rectangle, ratio, asset_name in (
        (health_rect, player.health / player.max_health, "character_hud_hp"),
        (
            experience_rect,
            _ratio(player.experience, experience_required),
            "character_hud_xp",
        ),
    ):
        fill_sprite = assets.get(asset_name)
        fill_width = round(rectangle.width * max(0.0, min(1.0, ratio)))
        if fill_sprite is not None and fill_width > 0:
            screen.blit(
                fill_sprite,
                rectangle.topleft,
                pygame.Rect(0, 0, fill_width, rectangle.height),
            )

    name_surface = fonts["sidebar_class"].render(
        subclass_name,
        True,
        accent_color,
    )
    name_background = name_surface.get_rect(topleft=(180, 27)).inflate(14, 6)
    pygame.draw.rect(screen, (5, 7, 9), name_background)
    pygame.draw.rect(screen, (57, 47, 39), name_background, width=1)
    screen.blit(
        name_surface,
        name_surface.get_rect(midleft=(name_background.left + 7, name_background.centery)),
    )

    level_center = (92, 126)
    level_surface = fonts["sidebar_numbers"].render(
        str(player.level), True, _BRIGHT_TEXT
    )
    screen.blit(
        level_surface,
        level_surface.get_rect(center=level_center),
    )
    for rectangle, label in (
        (health_rect, f"HP {player.health}/{player.max_health}"),
        (experience_rect, f"XP {player.experience}/{experience_required}"),
    ):
        label_surface = fonts["sidebar_hud"].render(label, True, _BRIGHT_TEXT)
        screen.blit(label_surface, label_surface.get_rect(center=rectangle.center))


def _ability_status(ratio, explicit_status):
    if explicit_status is not None:
        return explicit_status
    return "READY" if ratio >= 1 else f"{round(ratio * 100)}%"


def _draw_ability_tooltip(
    screen,
    fonts,
    card,
    entry,
    key_number,
):
    asset_name, name, ratio, color, explicit_status = entry
    tooltip = pygame.Rect(card.x, ACT_THREE_BOTTOM_BAR_Y - 74, 292, 66)
    if tooltip.right > ACT_THREE_BOTTOM_BAR_WIDTH - 8:
        tooltip.right = ACT_THREE_BOTTOM_BAR_WIDTH - 8
    tooltip_surface = pygame.Surface(tooltip.size, pygame.SRCALPHA)
    tooltip_surface.fill((8, 11, 14, 244))
    pygame.draw.rect(
        tooltip_surface,
        _SECTION_BORDER,
        tooltip_surface.get_rect(),
        width=1,
    )
    screen.blit(tooltip_surface, tooltip)
    _draw_label(screen, fonts["sidebar_text"], name, color, (tooltip.x + 10, tooltip.y + 6))
    status = _ability_status(ratio, explicit_status)
    status_surface = fonts["sidebar_log"].render(
        f"KEY {key_number}  ·  {status}",
        True,
        _MUTED_TEXT,
    )
    screen.blit(
        status_surface,
        status_surface.get_rect(topright=(tooltip.right - 10, tooltip.y + 8)),
    )
    description = _ABILITY_DESCRIPTIONS.get(asset_name, "Subclass ability.")
    _draw_label(
        screen,
        fonts["sidebar_log"],
        description,
        _BRIGHT_TEXT,
        (tooltip.x + 10, tooltip.y + 36),
    )


def _draw_abilities(screen, player, fonts, assets, accent_color, mouse_position):
    rectangle = pygame.Rect(704, ACT_THREE_BOTTOM_BAR_Y + 4, 318, 80)
    entries = _ability_entries(player, accent_color)
    card_width = 88
    hovered = None
    for index, entry in enumerate(entries):
        asset_name, name, ratio, color, explicit_status = entry
        card = pygame.Rect(rectangle.x + 10 + index * 97, rectangle.y + 10, card_width, 62)
        is_hovered = mouse_position is not None and card.collidepoint(mouse_position)
        pygame.draw.rect(screen, (19, 25, 28) if is_hovered else _PANEL_INNER, card)
        pygame.draw.rect(
            screen,
            color if is_hovered else (43, 53, 56),
            card,
            width=1,
        )
        icon = assets.get(asset_name)
        if icon is not None:
            icon = pygame.transform.smoothscale(icon, (38, 38))
            screen.blit(
                icon,
                icon.get_rect(center=(card.centerx, card.y + 25)),
            )
        key_badge = pygame.Rect(card.right - 24, card.y + 5, 18, 18)
        pygame.draw.rect(screen, _SLOT_FILL, key_badge)
        pygame.draw.rect(screen, _SECTION_BORDER, key_badge, width=1)
        key_surface = fonts["sidebar_log"].render(str(index + 1), True, _BRIGHT_TEXT)
        screen.blit(key_surface, key_surface.get_rect(center=key_badge.center))
        progress = pygame.Rect(card.x + 5, card.bottom - 8, card.width - 10, 4)
        pygame.draw.rect(screen, (34, 40, 43), progress)
        if ratio > 0:
            pygame.draw.rect(
                screen,
                color,
                (progress.x, progress.y, round(progress.width * ratio), progress.height),
            )
        if is_hovered:
            hovered = (card, entry, index + 1)
    if hovered is not None:
        _draw_ability_tooltip(screen, fonts, *hovered)


def _draw_item_slot(screen, rectangle, slot_number, item, fonts, assets, accent_color):
    pygame.draw.rect(screen, _SLOT_FILL, rectangle)
    pygame.draw.rect(screen, _SECTION_BORDER, rectangle, width=1)
    pygame.draw.line(
        screen,
        (34, 44, 46),
        (rectangle.left + 2, rectangle.top + 2),
        (rectangle.right - 3, rectangle.top + 2),
    )
    if slot_number is not None:
        key_surface = fonts["sidebar_log"].render(str(slot_number), True, _MUTED_TEXT)
        screen.blit(key_surface, (rectangle.x + 4, rectangle.y + 1))
    if item is not None:
        sprite = assets.get(item)
        if sprite is not None:
            sprite = pygame.transform.smoothscale(sprite, (34, 34))
            screen.blit(
                sprite,
                sprite.get_rect(center=(rectangle.centerx + 2, rectangle.centery + 3)),
            )
        pygame.draw.rect(screen, accent_color, rectangle, width=1)


def _draw_belt(screen, player, fonts, assets, accent_color):
    rectangle = pygame.Rect(304, ACT_THREE_BOTTOM_BAR_Y + 4, 388, 80)
    slot_size = 60
    gap = 9
    slots_left = rectangle.x + (rectangle.width - slot_size * 5 - gap * 4) // 2
    belt_potions = min(5, player.potion_count)
    for index in range(5):
        _draw_item_slot(
            screen,
            pygame.Rect(
                slots_left + index * (slot_size + gap),
                rectangle.y + 10,
                slot_size,
                58,
            ),
            index + 1,
            "sidebar_potion" if index < belt_potions else None,
            fonts,
            assets,
            accent_color,
        )


def _draw_popup_shell(screen, rectangle, title, fonts, accent_color):
    shadow = pygame.Surface((rectangle.width + 12, rectangle.height + 12), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 135))
    screen.blit(shadow, (rectangle.x - 6, rectangle.y + 6))
    pygame.draw.rect(screen, _PANEL_BACKGROUND, rectangle)
    pygame.draw.rect(screen, (98, 79, 54), rectangle, width=2)
    pygame.draw.rect(screen, _SECTION_BORDER, rectangle.inflate(-8, -8), width=1)
    title_surface = fonts["sidebar_heading"].render(title, True, (224, 205, 163))
    screen.blit(title_surface, title_surface.get_rect(midtop=(rectangle.centerx, rectangle.y + 13)))
    pygame.draw.line(
        screen,
        accent_color,
        (rectangle.x + 12, rectangle.y + 48),
        (rectangle.right - 12, rectangle.y + 48),
    )
    close_rect = get_act_three_panel_close_rectangle()
    pygame.draw.rect(screen, (34, 15, 15), close_rect)
    pygame.draw.rect(screen, (116, 53, 43), close_rect, width=1)
    _draw_label(screen, fonts["sidebar_numbers"], "×", (214, 86, 69), (close_rect.x + 5, close_rect.y - 1))


def _draw_inventory_popup(screen, player, fonts, assets, accent_color):
    inventory_potions = max(0, player.potion_count - 5)
    used_slots = min(16, inventory_potions)
    rectangle = get_act_three_popup_rectangle()
    _draw_popup_shell(screen, rectangle, "INVENTORY", fonts, accent_color)
    slot_size = 62
    gap = 10
    slots_left = rectangle.x + (rectangle.width - slot_size * 4 - gap * 3) // 2
    for index in range(16):
        row = index // 4
        column = index % 4
        _draw_item_slot(
            screen,
            pygame.Rect(
                slots_left + column * (slot_size + gap),
                rectangle.y + 66 + row * (slot_size + gap),
                slot_size,
                slot_size,
            ),
            None,
            "sidebar_potion" if index < used_slots else None,
            fonts,
            assets,
            accent_color,
        )
    footer = f"Occupied: {used_slots} / 16     Gold: {player.gold_count}     Keys: {player.key_count}"
    _draw_label(
        screen,
        fonts["sidebar_log"],
        footer,
        _MUTED_TEXT,
        (rectangle.x + 18, rectangle.bottom - 33),
    )


def _draw_stats_popup(screen, player, fonts, accent_color):
    rectangle = get_act_three_popup_rectangle()
    _draw_popup_shell(screen, rectangle, "CHARACTER STATS", fonts, accent_color)
    ranks = player.attribute_ranks
    values = (
        ("Level", str(player.level)),
        ("Strength", str(ranks.get("strength", 0))),
        ("Dexterity", str(ranks.get("dexterity", 0))),
        ("Intelligence", str(ranks.get("intelligence", 0))),
        ("Vitality", str(ranks.get("vitality", 0))),
        ("Damage", _damage_value(player)),
        ("Critical chance", f"{round(player.crit_chance * 100)}%"),
        ("Critical damage", f"{round(player.critical_damage_multiplier * 100)}%"),
        ("Dodge chance", f"{round(player.dodge_chance * 100)}%"),
        ("Spell power", str(player.spell_power)),
        ("Gold", str(player.gold_count)),
        ("Keys", str(player.key_count)),
    )
    row_y = rectangle.y + 64
    for index, (label, value) in enumerate(values):
        row = pygame.Rect(rectangle.x + 18, row_y + index * 27, rectangle.width - 36, 25)
        if index % 2 == 0:
            pygame.draw.rect(screen, _PANEL_INNER, row)
        _draw_label(screen, fonts["sidebar_log"], label, _MUTED_TEXT, (row.x + 7, row.y + 3))
        value_surface = fonts["sidebar_numbers"].render(value, True, _BRIGHT_TEXT)
        screen.blit(value_surface, value_surface.get_rect(midright=(row.right - 7, row.centery)))


def _compact_event_message(message):
    compact = message.replace("Hero hits ", "Hit ")
    compact = compact.replace(" prepares melee at ", " prepares ")
    return compact.replace(" is defeated.", " defeated")


def _draw_events(screen, game_state, fonts, accent_color):
    rectangle = pygame.Rect(12, ACT_THREE_VIEW_HEIGHT - 132, 430, 50)
    event_surface = pygame.Surface(rectangle.size, pygame.SRCALPHA)
    event_surface.fill((5, 8, 10, 190))
    pygame.draw.rect(
        event_surface,
        (*accent_color, 120),
        event_surface.get_rect(),
        width=1,
    )
    screen.blit(event_surface, rectangle)
    rendered_lines = []
    for message in game_state.combat_log[-2:]:
        for line in wrap_text(
            fonts["sidebar_log"],
            _compact_event_message(message),
            rectangle.width - 18,
        ):
            rendered_lines.append((line, get_event_color(message)))
    for index, (line, color) in enumerate(rendered_lines[-2:]):
        _draw_label(
            screen,
            fonts["sidebar_log"],
            line,
            color,
            (rectangle.x + 9, rectangle.y + 7 + index * 18),
        )


def _draw_rail_icon(screen, name, rectangle, color, fonts):
    center_x, center_y = rectangle.center
    if name == "inventory":
        body = pygame.Rect(center_x - 13, center_y - 8, 26, 23)
        pygame.draw.rect(screen, color, body, width=2)
        pygame.draw.arc(screen, color, (center_x - 8, center_y - 17, 16, 16), math.pi, math.tau, 2)
    elif name == "stats":
        for index, height in enumerate((10, 18, 27)):
            pygame.draw.rect(screen, color, (center_x - 15 + index * 11, center_y + 13 - height, 7, height))
    elif name == "abilities":
        points = []
        for index in range(10):
            angle = -math.pi / 2 + index * math.pi / 5
            radius = 15 if index % 2 == 0 else 7
            points.append((center_x + math.cos(angle) * radius, center_y + math.sin(angle) * radius))
        pygame.draw.polygon(screen, color, points, width=2)
    elif name == "log":
        pygame.draw.rect(screen, color, (center_x - 14, center_y - 16, 28, 32), width=2)
        for offset in (-8, 0, 8):
            pygame.draw.line(screen, color, (center_x - 8, center_y + offset), (center_x + 8, center_y + offset))
    else:
        pygame.draw.circle(screen, color, (center_x, center_y), 13, width=3)
        pygame.draw.circle(screen, color, (center_x, center_y), 4, width=2)
        for index in range(8):
            angle = index * math.pi / 4
            start = (center_x + math.cos(angle) * 15, center_y + math.sin(angle) * 15)
            end = (center_x + math.cos(angle) * 19, center_y + math.sin(angle) * 19)
            pygame.draw.line(screen, color, start, end, 3)


def _draw_button_rail(screen, active_tab, fonts, accent_color, mouse_position):
    labels = {
        "inventory": "Inventory",
        "stats": "Character stats",
        "abilities": "Abilities (coming later)",
        "log": "Event log (coming later)",
        "settings": "Settings",
    }
    for name, rectangle in get_act_three_sidebar_tab_rectangles().items():
        hovered = mouse_position is not None and rectangle.collidepoint(mouse_position)
        active = active_tab == name
        shadow = rectangle.move(3, 4)
        pygame.draw.rect(screen, (3, 5, 6), shadow)
        pygame.draw.rect(screen, (23, 21, 19) if active else _PANEL_BACKGROUND, rectangle)
        border = accent_color if active else ((121, 91, 55) if hovered else (79, 69, 57))
        pygame.draw.rect(screen, border, rectangle, width=2 if active or hovered else 1)
        _draw_rail_icon(screen, name, rectangle, accent_color if active else _BRIGHT_TEXT, fonts)
        if hovered:
            label = fonts["sidebar_log"].render(labels[name], True, _BRIGHT_TEXT)
            tooltip = label.get_rect(midright=(rectangle.left - 9, rectangle.centery)).inflate(14, 8)
            pygame.draw.rect(screen, (7, 9, 11), tooltip)
            pygame.draw.rect(screen, _SECTION_BORDER, tooltip, width=1)
            screen.blit(label, label.get_rect(center=tooltip.center))


def _draw_act_three_sidebar(
    screen,
    game_state,
    fonts,
    assets,
    mouse_position=None,
):
    player = game_state.player
    subclass_name, accent_color = _SUBCLASS_PRESENTATION.get(
        player.subclass,
        ("UNBOUND", (139, 151, 151)),
    )
    _draw_header(screen, player, fonts, assets, accent_color, subclass_name)
    _draw_events(screen, game_state, fonts, accent_color)
    _draw_abilities(
        screen,
        player,
        fonts,
        assets,
        accent_color,
        mouse_position,
    )
    _draw_belt(screen, player, fonts, assets, accent_color)
    active_tab = getattr(game_state, "sidebar_tab", "closed")
    if active_tab == "inventory":
        _draw_inventory_popup(screen, player, fonts, assets, accent_color)
    elif active_tab == "stats":
        _draw_stats_popup(screen, player, fonts, accent_color)
    _draw_button_rail(screen, active_tab, fonts, accent_color, mouse_position)
