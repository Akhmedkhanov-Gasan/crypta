import math

import pygame

from game.progression import experience_required_for_level
from presentation.hud import get_event_color, wrap_text
from presentation.layout import (
    ACT_THREE_SIDEBAR_WIDTH,
    ACT_THREE_SIDEBAR_X,
    ACT_THREE_SIDEBAR_Y,
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
    TEXT_COLOR,
    WARLOCK_CURSE_CHARGES,
    WARLOCK_SOUL_EXCHANGE_CHARGES,
)

def _draw_label(surface, font, text, color, position):
    surface.blit(font.render(text, True, color), position)


def get_act_three_sidebar_tab_rectangles():
    tabs_x = ACT_THREE_SIDEBAR_X + 30
    tabs_y = ACT_THREE_SIDEBAR_Y + 118
    tabs_width = ACT_THREE_SIDEBAR_WIDTH - 60
    gap = 6
    tab_width = (tabs_width - gap) // 2

    return {
        "stats": pygame.Rect(tabs_x, tabs_y, tab_width, 30),
        "inventory": pygame.Rect(
            tabs_x + tab_width + gap,
            tabs_y,
            tab_width,
            30,
        ),
    }


def get_act_three_log_panel_rect():
    return pygame.Rect(
        ACT_THREE_SIDEBAR_X + 35,
        ACT_THREE_SIDEBAR_Y + 524,
        ACT_THREE_SIDEBAR_WIDTH - 70,
        90,
    )


def get_act_three_log_arrow_rectangles():
    log_panel = get_act_three_log_panel_rect()
    arrow_size = 18
    return {
        "older": pygame.Rect(
            log_panel.right - arrow_size - 6,
            log_panel.y + 10,
            arrow_size,
            arrow_size,
        ),
        "newer": pygame.Rect(
            log_panel.right - arrow_size - 6,
            log_panel.bottom - arrow_size - 10,
            arrow_size,
            arrow_size,
        ),
    }


def _draw_act_three_sidebar(
    screen,
    game_state,
    fonts,
    assets,
):
    screen.blit(
        assets["sidebar_panel"],
        (ACT_THREE_SIDEBAR_X, ACT_THREE_SIDEBAR_Y),
    )
    player = game_state.player
    content_x = ACT_THREE_SIDEBAR_X + 30
    content_width = ACT_THREE_SIDEBAR_WIDTH - 60
    display_font = fonts["sidebar_display"]
    heading_font = fonts["sidebar_heading"]
    text_font = fonts["sidebar_text"]
    numbers_font = fonts["sidebar_numbers"]
    dim_color = (139, 132, 142)
    muted_border = (70, 63, 76)
    panel_fill = (18, 16, 23)
    subclass_name, accent_color = {
        "paladin": ("PALADIN", (206, 168, 80)),
        "assassin": ("ASSASSIN", (69, 130, 221)),
        "archer": ("ARCHER", (105, 151, 76)),
        "warlock": ("WARLOCK", (176, 91, 232)),
        "summoner": ("SUMMONER", (77, 184, 193)),
        "berserker": ("BERSERKER", (205, 68, 58)),
    }.get(
        player.subclass,
        ("BERSERKER", (205, 68, 58)),
    )

    experience_required = experience_required_for_level(player.level)
    experience_ratio = max(
        0,
        min(1, player.experience / experience_required),
    )
    experience_bar = pygame.Rect(
        ACT_THREE_SIDEBAR_X + 24,
        12,
        ACT_THREE_SIDEBAR_WIDTH - 48,
        20,
    )
    pygame.draw.rect(
        screen,
        (5, 7, 12),
        experience_bar.move(0, 2),
        border_radius=4,
    )
    pygame.draw.rect(
        screen,
        (15, 20, 29),
        experience_bar,
        border_radius=4,
    )
    experience_fill = experience_bar.inflate(-4, -4)
    experience_fill.width = round(
        experience_fill.width * experience_ratio
    )
    if experience_fill.width > 0:
        pygame.draw.rect(
            screen,
            (35, 126, 203),
            experience_fill,
            border_radius=2,
        )
        pygame.draw.line(
            screen,
            (89, 190, 239),
            (experience_fill.left + 1, experience_fill.top + 1),
            (experience_fill.right - 2, experience_fill.top + 1),
        )
    pygame.draw.rect(
        screen,
        (65, 108, 145),
        experience_bar,
        width=1,
        border_radius=4,
    )
    experience_label = numbers_font.render(
        f"XP {player.experience}/{experience_required}",
        True,
        (211, 235, 247),
    )
    screen.blit(
        experience_label,
        experience_label.get_rect(center=experience_bar.center),
    )

    header_x = ACT_THREE_SIDEBAR_X + 34
    header_y = ACT_THREE_SIDEBAR_Y + 21
    class_surface = display_font.render(
        subclass_name,
        True,
        accent_color,
    )
    screen.blit(class_surface, (header_x, header_y))
    level_x = min(
        header_x + class_surface.get_width() + 12,
        ACT_THREE_SIDEBAR_X + ACT_THREE_SIDEBAR_WIDTH - 66,
    )
    level_label = text_font.render("LVL", True, dim_color)
    level_label_rectangle = level_label.get_rect(
        topleft=(level_x, header_y + 7),
    )
    screen.blit(level_label, level_label_rectangle)
    level_number = numbers_font.render(
        str(player.level),
        True,
        TEXT_COLOR,
    )
    screen.blit(
        level_number,
        level_number.get_rect(
            midleft=(
                level_label_rectangle.right + 5,
                level_label_rectangle.centery,
            ),
        ),
    )
    hp_bar_position = (
        ACT_THREE_SIDEBAR_X + 23,
        ACT_THREE_SIDEBAR_Y + 48,
    )
    hp_inner_width = 204
    hp_ratio = max(0, min(1, player.health / player.max_health))
    screen.blit(assets["assassin_hp_bar"], hp_bar_position)
    hp_inner_left = hp_bar_position[0] + 27
    hp_inner_top = hp_bar_position[1] + 14
    hp_inner_height = 14
    missing_hp_rectangle = pygame.Rect(
        hp_inner_left + round(hp_inner_width * hp_ratio),
        hp_inner_top,
        round(hp_inner_width * (1 - hp_ratio)),
        hp_inner_height,
    )
    if missing_hp_rectangle.width > 0:
        pygame.draw.rect(
            screen,
            (42, 20, 27),
            missing_hp_rectangle,
        )
    hp_text = f"HP {player.health}/{player.max_health}"
    hp_surface = numbers_font.render(hp_text, True, TEXT_COLOR)
    screen.blit(
        hp_surface,
        hp_surface.get_rect(
            center=(
                hp_bar_position[0] + 129,
                hp_bar_position[1] + 21,
            ),
        ),
    )

    tab_rectangles = get_act_three_sidebar_tab_rectangles()
    tab_labels = {
        "stats": "Stats",
        "inventory": "Inventory",
    }
    for tab_name, tab_rectangle in tab_rectangles.items():
        is_active = game_state.sidebar_tab == tab_name
        pygame.draw.rect(
            screen,
            (27, 23, 32) if is_active else (16, 14, 20),
            tab_rectangle,
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            accent_color if is_active else muted_border,
            tab_rectangle,
            width=1,
            border_radius=3,
        )
        if is_active:
            pygame.draw.rect(
                screen,
                accent_color,
                (
                    tab_rectangle.x + 8,
                    tab_rectangle.bottom - 3,
                    tab_rectangle.width - 16,
                    2,
                ),
            )

        tab_surface = text_font.render(
            tab_labels[tab_name],
            True,
            TEXT_COLOR if is_active else dim_color,
        )
        screen.blit(
            tab_surface,
            tab_surface.get_rect(center=tab_rectangle.center),
        )

    tab_content_panel = pygame.Rect(
        content_x,
        tab_rectangles["stats"].bottom + 8,
        content_width,
        108,
    )
    pygame.draw.rect(
        screen,
        (12, 11, 16),
        tab_content_panel,
        border_radius=4,
    )
    pygame.draw.rect(
        screen,
        (50, 45, 56),
        tab_content_panel,
        width=1,
        border_radius=4,
    )
    tab_content_top = tab_content_panel.y + 7
    if game_state.sidebar_tab == "inventory":
        inventory = (
            ("sidebar_potion", player.potion_count),
            ("sidebar_coin", player.gold_count),
            ("sidebar_key", player.key_count),
        )
        slot_size = 48
        slot_gap = 10
        grid_width = slot_size * 3 + slot_gap * 2
        grid_x = content_x + (content_width - grid_width) // 2
        for slot_index in range(6):
            slot = pygame.Rect(
                grid_x + (slot_index % 3) * (slot_size + slot_gap),
                tab_content_top + (slot_index // 3) * (slot_size + 5),
                slot_size,
                slot_size,
            )
            pygame.draw.rect(screen, panel_fill, slot, border_radius=3)
            pygame.draw.rect(
                screen,
                muted_border,
                slot,
                width=1,
                border_radius=3,
            )
            if slot_index >= len(inventory):
                continue
            asset_name, count = inventory[slot_index]
            item = assets[asset_name]
            screen.blit(
                item,
                item.get_rect(center=slot.center),
            )
            count_badge = pygame.Rect(
                slot.right - 19,
                slot.bottom - 18,
                16,
                15,
            )
            pygame.draw.rect(
                screen,
                (12, 11, 15),
                count_badge,
                border_radius=3,
            )
            count_surface = numbers_font.render(
                str(count),
                True,
                TEXT_COLOR,
            )
            screen.blit(
                count_surface,
                count_surface.get_rect(center=count_badge.center),
            )
    else:
        damage_bonus = None
        damage_bonus_color = (225, 69, 55)
        if player.subclass == "berserker":
            health_ratio = player.health / player.max_health
            if (
                player.berserker_last_rage_turns > 0
                or health_ratio
                <= BERSERKER_RAGE_CRITICAL_HEALTH_RATIO
            ):
                rage_multiplier = (
                    BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER
                )
            elif (
                health_ratio
                <= BERSERKER_RAGE_INJURED_HEALTH_RATIO
            ):
                rage_multiplier = (
                    BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER
                )
            else:
                rage_multiplier = 1.0

            bonus_minimum = (
                math.ceil(player.damage_min * rage_multiplier)
                - player.damage_min
            )
            bonus_maximum = (
                math.ceil(player.damage_max * rage_multiplier)
                - player.damage_max
            )
            damage_bonus = (
                f"+{bonus_minimum}"
                if bonus_minimum == bonus_maximum
                else f"+{bonus_minimum}-{bonus_maximum}"
            )
        elif (
            player.subclass == "paladin"
            and player.paladin_holy_shield_turns > 0
        ):
            damage_bonus = (
                f"+{PALADIN_HOLY_SHIELD_DAMAGE_BONUS}"
            )
            damage_bonus_color = (242, 197, 78)

        stats = (
            (
                "Damage",
                f"{player.damage_min}-{player.damage_max}",
                damage_bonus,
            ),
            (
                "Critical chance",
                f"{round(player.crit_chance * 100)}%",
                None,
            ),
            (
                "Dodge chance",
                f"{round(player.dodge_chance * 100)}%",
                None,
            ),
        )
        for stat_index, (label, value, bonus) in enumerate(stats):
            stat_y = tab_content_top + stat_index * 29
            _draw_label(
                screen,
                text_font,
                label,
                dim_color,
                (content_x + 5, stat_y),
            )
            value_surface = numbers_font.render(value, True, TEXT_COLOR)
            value_right = content_x + content_width - 5
            if bonus is not None:
                bonus_surface = numbers_font.render(
                    bonus,
                    True,
                    damage_bonus_color,
                )
                screen.blit(
                    bonus_surface,
                    (
                        value_right - bonus_surface.get_width(),
                        stat_y,
                    ),
                )
                value_right -= bonus_surface.get_width() + 7
            screen.blit(
                value_surface,
                (
                    value_right - value_surface.get_width(),
                    stat_y,
                ),
            )
            if stat_index < len(stats) - 1:
                pygame.draw.line(
                    screen,
                    (51, 46, 56),
                    (content_x + 5, stat_y + 23),
                    (content_x + content_width - 5, stat_y + 23),
                )

    ability_y = ACT_THREE_SIDEBAR_Y + 270
    _draw_label(
        screen,
        heading_font,
        "Abilities",
        TEXT_COLOR,
        (content_x, ability_y),
    )

    pygame.draw.line(
        screen,
        muted_border,
        (content_x + 92, ability_y + 13),
        (content_x + content_width, ability_y + 15),
    )
    invisibility_charge_ratio = max(
        0,
        min(1, player.ability_kill_charge / CLASS_ABILITY_KILLS),
    )
    teleport_charge_ratio = max(
        0,
        min(1, player.teleport_charge / ASSASSIN_TELEPORT_CHARGES),
    )
    ultimate_charge_ratio = max(
        0,
        min(1, player.ultimate_charge / ASSASSIN_ULTIMATE_CHARGES),
    )
    if player.subclass == "archer":
        empowered_charge_ratio = max(
            0,
            min(
                1,
                player.archer_empowered_shot_charge
                / ARCHER_EMPOWERED_SHOT_CHARGES,
            ),
        )
        leap_charge_ratio = max(
            0,
            min(
                1,
                player.archer_leap_charge
                / ARCHER_LEAP_CHARGES,
            ),
        )
        barrage_charge_ratio = max(
            0,
            min(
                1,
                player.archer_barrage_zone_charge
                / ARCHER_BARRAGE_ZONE_CHARGES,
            ),
        )
        regular_abilities = (
            (
                "archer_empowered_shot",
                "Empowered Shot",
                empowered_charge_ratio,
                accent_color,
            ),
            (
                "archer_leap",
                "Leap",
                leap_charge_ratio,
                accent_color,
            ),
            (
                "archer_barrage_zone",
                "Barrage Zone",
                barrage_charge_ratio,
                accent_color,
            ),
        )
    elif player.subclass == "berserker":
        crushing_leap_charge_ratio = max(
            0,
            min(
                1,
                player.berserker_crushing_leap_charge
                / BERSERKER_CRUSHING_LEAP_CHARGES,
            ),
        )
        last_rage_charge_ratio = max(
            0,
            min(
                1,
                player.berserker_last_rage_charge
                / BERSERKER_LAST_RAGE_CHARGES,
            ),
        )
        regular_abilities = (
            (
                "berserker_rage",
                "Rage",
                1.0,
                (220, 72, 58),
            ),
            (
                "berserker_crushing_leap",
                "Crushing Leap",
                crushing_leap_charge_ratio,
                (220, 72, 58),
            ),
            (
                "berserker_last_rage",
                (
                    f"Last Rage ({player.berserker_last_rage_turns})"
                    if player.berserker_last_rage_turns > 0
                    else "Last Rage"
                ),
                (
                    1.0
                    if player.berserker_last_rage_turns > 0
                    else last_rage_charge_ratio
                ),
                (245, 54, 45),
            ),
        )
    elif player.subclass == "paladin":
        holy_hand_charge_ratio = max(
            0,
            min(
                1,
                player.paladin_holy_hand_charge
                / PALADIN_HOLY_HAND_CHARGES,
            ),
        )
        shield_charge_ratio = max(
            0,
            min(
                1,
                player.paladin_shield_charge_charge
                / PALADIN_SHIELD_CHARGE_CHARGES,
            ),
        )
        holy_shield_charge_ratio = max(
            0,
            min(
                1,
                player.paladin_holy_shield_charge
                / PALADIN_HOLY_SHIELD_CHARGES,
            ),
        )
        regular_abilities = (
            (
                "paladin_holy_hand",
                "Holy Hand",
                holy_hand_charge_ratio,
                (239, 194, 78),
            ),
            (
                "paladin_shield_charge",
                "Shield Charge",
                shield_charge_ratio,
                (239, 194, 78),
            ),
            (
                "paladin_holy_shield",
                (
                    f"Holy Shield ({player.paladin_holy_shield_turns})"
                    if player.paladin_holy_shield_turns > 0
                    else "Holy Shield"
                ),
                (
                    1.0
                    if player.paladin_holy_shield_turns > 0
                    else holy_shield_charge_ratio
                ),
                (255, 219, 116),
            ),
        )
    elif player.subclass == "warlock":
        curse_charge_ratio = max(
            0,
            min(
                1,
                player.warlock_curse_charge
                / WARLOCK_CURSE_CHARGES,
            ),
        )
        soul_exchange_charge_ratio = max(
            0,
            min(
                1,
                player.warlock_soul_exchange_charge
                / WARLOCK_SOUL_EXCHANGE_CHARGES,
            ),
        )
        regular_abilities = (
            (
                "warlock_curse",
                "Curse",
                curse_charge_ratio,
                (198, 91, 238),
            ),
            (
                "warlock_soul_exchange",
                "Soul Exchange",
                soul_exchange_charge_ratio,
                (184, 78, 224),
            ),
            (
                "warlock_demon_form",
                "Demon Form",
                0.0,
                (220, 67, 194),
            ),
        )
    elif player.subclass == "summoner":
        summoner_familiar_charge_ratio = max(
            0,
            min(
                1,
                player.summoner_familiar_charge
                / SUMMONER_FAMILIAR_CHARGES,
            ),
        )
        regular_abilities = (
            (
                "summoner_familiar",
                "Release Familiar",
                summoner_familiar_charge_ratio,
                (74, 207, 202),
            ),
            (
                "summoner_bond",
                "Bond",
                max(
                    0,
                    min(
                        1,
                        player.summoner_bond_charge
                        / SUMMONER_BOND_CHARGES,
                    ),
                ),
                (74, 207, 202),
            ),
            (
                "summoner_true_form",
                "True Form",
                max(
                    0,
                    min(
                        1,
                        player.summoner_true_form_charge
                        / SUMMONER_TRUE_FORM_CHARGES,
                    ),
                ),
                (91, 224, 238),
            ),
        )
    else:
        regular_abilities = (
            (
                "assassin_invisibility",
                "Invisibility",
                invisibility_charge_ratio,
                accent_color,
            ),
            (
                "assassin_teleport",
                "Teleport",
                teleport_charge_ratio,
                accent_color,
            ),
            (
                "assassin_killing_spree",
                "Killing Spree",
                ultimate_charge_ratio,
                (205, 68, 74),
            ),
        )
    card_y = ability_y + 30
    card_width = content_width
    card_height = 64
    for index, (asset_name, name, charge_ratio, ability_color) in enumerate(
        regular_abilities
    ):
        card = pygame.Rect(
            content_x,
            card_y + index * (card_height + 7),
            card_width,
            card_height,
        )
        pygame.draw.rect(screen, panel_fill, card, border_radius=4)
        pygame.draw.rect(
            screen,
            muted_border,
            card,
            width=1,
            border_radius=4,
        )
        icon = assets[asset_name]
        screen.blit(icon, (card.x + 7, card.y + 6))
        text_x = card.x + 61
        _draw_label(
            screen,
            text_font,
            name,
            ability_color,
            (text_x, card.y + 7),
        )
        key_badge = pygame.Rect(card.right - 29, card.y + 7, 20, 20)
        is_passive = player.subclass == "berserker" and index == 0
        if is_passive:
            key_badge = pygame.Rect(
                card.right - 69,
                card.y + 7,
                60,
                20,
            )
        pygame.draw.rect(screen, (32, 28, 38), key_badge, border_radius=3)
        pygame.draw.rect(
            screen,
            muted_border,
            key_badge,
            width=1,
            border_radius=3,
        )
        key_font = (
            fonts["sidebar_log"]
            if is_passive
            else numbers_font
        )
        key_surface = key_font.render(
            "PASSIVE" if is_passive else str(index + 1),
            True,
            (237, 104, 89) if is_passive else TEXT_COLOR,
        )
        screen.blit(key_surface, key_surface.get_rect(center=key_badge.center))
        last_rage_is_active = (
            asset_name == "berserker_last_rage"
            and player.berserker_last_rage_turns > 0
        )
        holy_shield_is_active = (
            asset_name == "paladin_holy_shield"
            and player.paladin_holy_shield_turns > 0
        )
        demon_form_is_active = (
            asset_name == "warlock_demon_form"
            and player.warlock_demon_form_active
        )
        status = (
            "ALWAYS ACTIVE"
            if is_passive
            else (
                "ACTIVE"
                if demon_form_is_active
                else (
                    "READY"
                    if asset_name == "warlock_demon_form"
                    else (
                        f"{player.paladin_holy_shield_turns} TURNS"
                        if holy_shield_is_active
                        else (
                            f"{player.berserker_last_rage_turns} TURNS"
                            if last_rage_is_active
                            else (
                                "READY"
                                if charge_ratio >= 1
                                else f"{round(charge_ratio * 100)}%"
                            )
                        )
                    )
                )
            )
        )
        _draw_label(
            screen,
            text_font if charge_ratio >= 1 else numbers_font,
            status,
            dim_color,
            (text_x, card.y + 27),
        )
        charge_bar = pygame.Rect(
            text_x,
            card.y + 48,
            card.right - text_x - 10,
            6,
        )
        pygame.draw.rect(screen, (43, 37, 48), charge_bar, border_radius=2)
        if charge_ratio > 0:
            pygame.draw.rect(
                screen,
                ability_color if is_passive else accent_color,
                (
                    charge_bar.x,
                    charge_bar.y,
                    round(charge_bar.width * charge_ratio),
                    charge_bar.height,
                ),
                border_radius=2,
            )

    log_panel = get_act_three_log_panel_rect()
    pygame.draw.rect(screen, (12, 11, 16), log_panel, border_radius=4)
    pygame.draw.rect(
        screen,
        (50, 45, 56),
        log_panel,
        width=1,
        border_radius=4,
    )
    log_font = fonts.get("sidebar_log", text_font)
    visible_line_count = 4
    max_log_scroll = max(
        0,
        len(game_state.combat_log) - visible_line_count,
    )
    game_state.log_scroll_offset = max(
        0,
        min(game_state.log_scroll_offset, max_log_scroll),
    )
    end_index = len(game_state.combat_log) - game_state.log_scroll_offset
    start_index = max(0, end_index - visible_line_count)
    log_messages = game_state.combat_log[start_index:end_index]
    arrow_rectangles = get_act_three_log_arrow_rectangles()
    for arrow_name, arrow_rectangle in arrow_rectangles.items():
        pygame.draw.rect(
            screen,
            (25, 22, 31),
            arrow_rectangle,
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            (70, 63, 76),
            arrow_rectangle,
            width=1,
            border_radius=3,
        )
        center_x = arrow_rectangle.centerx
        center_y = arrow_rectangle.centery
        if arrow_name == "older":
            points = (
                (center_x, center_y - 5),
                (center_x - 5, center_y + 3),
                (center_x + 5, center_y + 3),
            )
        else:
            points = (
                (center_x - 5, center_y - 3),
                (center_x + 5, center_y - 3),
                (center_x, center_y + 5),
            )
        pygame.draw.polygon(screen, (177, 166, 184), points)

    rendered_lines = []
    for message in log_messages:
        compact_message = message
        if "Hero hits " in compact_message and " for " in compact_message:
            attacker, amount = compact_message.rstrip(".").split(
                " for ",
                1,
            )
            compact_message = (
                attacker.replace("Hero hits ", "Hit ")
                + " "
                + amount
            )
        compact_message = compact_message.replace(
            " prepares melee at ",
            " prepares ",
        )
        compact_message = compact_message.replace(
            " is defeated.",
            " defeated",
        )
        for wrapped_line in wrap_text(
            log_font,
            compact_message,
            log_panel.width - 48,
        ):
            rendered_lines.append((wrapped_line, get_event_color(message)))

    for line_index, (visible_message, message_color) in enumerate(
        rendered_lines[:4]
    ):
        _draw_label(
            screen,
            log_font,
            visible_message,
            message_color,
            (log_panel.x + 10, log_panel.y + 8 + line_index * 17),
        )
