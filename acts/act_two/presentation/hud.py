import pygame

from settings import MAX_ATTRIBUTE_RANK

from acts.act_two.settings import (
    ABILITY_HITS_REQUIRED,
    CONSUMABLE_BELT_SIZE,
)
from game.progression import experience_required_for_level
from presentation.hud import (
    fit_text_to_width,
    get_event_color,
    wrap_text,
)


_ACT_TWO_BOTTOM_BAR_POSITION = (256, 529)
_ACT_TWO_BELT_ITEM_POSITIONS = (
    (550, 643),
    (610, 643),
    (668, 643),
    (728, 643),
    (788, 643),
    (850, 643),
)
_ACT_TWO_BELT_ITEM_SIZE = (36, 36)
_ACT_TWO_ABILITY_RECT = pygame.Rect(931, 636, 42, 42)
_ACT_TWO_ABILITY_CHARGE_RECTS = tuple(
    pygame.Rect(936 + charge_index * 9, 675, 7, 3)
    for charge_index in range(ABILITY_HITS_REQUIRED)
)
_ACT_TWO_LOG_TEXT_RECT = pygame.Rect(308, 625, 194, 65)
_ACT_TWO_LOG_BACKING_POSITION = (301, 620)
_ACT_TWO_SIDEBAR_BUTTON_RECTS = {
    "stats": pygame.Rect(1195, 219, 72, 59),
    "placeholder": pygame.Rect(1195, 277, 72, 59),
    "settings": pygame.Rect(1195, 335, 72, 59),
}
_ACT_TWO_SIDEBAR_HIGHLIGHT_RECTS = {
    "stats": pygame.Rect(1207, 230, 47, 44),
    "placeholder": pygame.Rect(1207, 288, 47, 44),
    "settings": pygame.Rect(1207, 346, 47, 44),
}
_ACT_TWO_ATTRIBUTE_PLUS_RECTS = {
    "strength": pygame.Rect(1123, 243, 26, 22),
    "dexterity": pygame.Rect(1123, 271, 26, 22),
    "intelligence": pygame.Rect(1123, 299, 26, 22),
    "vitality": pygame.Rect(1123, 327, 26, 22),
}
_ACT_TWO_ATTRIBUTE_MINUS_RECTS = {
    "strength": pygame.Rect(1085, 243, 26, 22),
    "dexterity": pygame.Rect(1085, 271, 26, 22),
    "intelligence": pygame.Rect(1085, 299, 26, 22),
    "vitality": pygame.Rect(1085, 327, 26, 22),
}
_ACT_TWO_CONFIRM_BUTTON_RECT = pygame.Rect(
    987,
    335,
    158,
    53,
)
_ACT_TWO_CONFIRM_BUTTON_HIT_RECT = (
    _ACT_TWO_CONFIRM_BUTTON_RECT.inflate(-32, -16)
)
_ACT_TWO_ABILITIES_PANEL_POSITION = (809, 464)
_ACT_TWO_ABILITIES_ICON_RECT = pygame.Rect(844, 546, 42, 42)
_ACT_TWO_ABILITIES_TEXT_BACKING_POSITION = (905, 537)
_ACT_TWO_ABILITIES_TEXT_RECT = pygame.Rect(917, 548, 135, 48)
_ACT_TWO_ABILITY_ASSETS = {
    "warrior": "warrior_power_cleave_icon",
    "rogue": "rogue_invisibility_icon",
    "mage": "mage_arcane_burst_icon",
}
_ACT_TWO_ABILITY_DESCRIPTIONS = {
    "warrior": "Cleave several tiles for bonus damage.",
    "rogue": "Vanish. Your next attack is a sure critical.",
    "mage": "Blast up to 5 tiles with bonus spell damage.",
}
_ACT_TWO_LEVEL_UP_POSITION = (1185, 207)
_ACT_TWO_GOLD_COUNTER_POSITION = (1167, 610)
_ACT_TWO_GOLD_VALUE_CENTER = (1218, 675)

def draw_act_two_sidebar(
    screen,
    title_font,
    log_font,
    controls_font,
    ability_font,
    combat_log,
    player_health,
    player_max_health,
    player_damage_min,
    player_damage_max,
    player_crit_chance,
    player_dodge_chance,
    player_spell_power,
    attribute_ranks,
    pending_attribute_upgrades,
    consumable_slots,
    gold_count,
    player_class,
    player_level,
    player_experience,
    ability_kill_charge,
    available_attribute_points,
    stats_open,
    mouse_position,
    sprites,

):
    def draw_fill(asset_name, position, ratio):
        asset = sprites[asset_name]
        visible_width = round(
            asset.get_width() * max(0.0, min(1.0, ratio))
        )
        if visible_width > 0:
            screen.blit(
                asset,
                position,
                pygame.Rect(0, 0, visible_width, asset.get_height()),
            )

    health_ratio = player_health / max(1, player_max_health)
    experience_required = experience_required_for_level(player_level)
    experience_ratio = player_experience / max(1, experience_required)
    draw_fill("act_two_hud_hp", (114, 53), health_ratio)
    draw_fill("act_two_hud_xp", (63, 89), experience_ratio)

    screen.blit(sprites["act_two_hud_frame"], (44, 19))

    portrait_rectangle = pygame.Rect(70, 48, 55, 53)
    if player_class is not None:
        portrait = pygame.transform.scale(
            sprites[f"player_{player_class}"],
            portrait_rectangle.size,
        )
        screen.blit(portrait, portrait_rectangle)

    value_color = (239, 235, 225)
    level_surface = title_font.render(
        str(player_level),
        True,
        value_color,
    )
    screen.blit(
        level_surface,
        level_surface.get_rect(center=(129, 115)),
    )
    hp_surface = controls_font.render(
        f"{player_health}/{player_max_health}",
        True,
        value_color,
    )
    screen.blit(hp_surface, hp_surface.get_rect(center=(307, 64)))
    xp_surface = controls_font.render(
        f"{player_experience}/{experience_required}",
        True,
        value_color,
    )
    screen.blit(xp_surface, xp_surface.get_rect(center=(282, 101)))

    screen.blit(
        sprites["act_two_bottom_bar"],
        _ACT_TWO_BOTTOM_BAR_POSITION,
    )
    screen.blit(
        sprites["act_two_chat_log_backing"],
        _ACT_TWO_LOG_BACKING_POSITION,
    )
    line_height = 16
    maximum_line_count = (
        _ACT_TWO_LOG_TEXT_RECT.height // line_height
    )
    recent_messages = []
    for message in combat_log[-3:]:
        recent_messages.append(
            (
                wrap_text(
                    log_font,
                    message,
                    _ACT_TWO_LOG_TEXT_RECT.width,
                ),
                get_event_color(message),
            )
        )

    selected_messages = [
        ([lines[0]] if lines else [""], color)
        for lines, color in recent_messages
    ]
    remaining_line_count = max(
        0,
        maximum_line_count - len(selected_messages),
    )
    for message_index in range(len(recent_messages) - 1, -1, -1):
        if remaining_line_count <= 0:
            break
        wrapped_lines, _color = recent_messages[message_index]
        extra_lines = wrapped_lines[1:1 + remaining_line_count]
        selected_messages[message_index][0].extend(extra_lines)
        remaining_line_count -= len(extra_lines)

    visible_log_lines = []
    for message_index, ((wrapped_lines, color), selected_message) in (
        enumerate(zip(recent_messages, selected_messages))
    ):
        selected_lines, _selected_color = selected_message
        if len(selected_lines) < len(wrapped_lines):
            selected_lines[-1] = fit_text_to_width(
                log_font,
                selected_lines[-1] + "...",
                _ACT_TWO_LOG_TEXT_RECT.width,
            )
        visible_log_lines.extend(
            (line, color)
            for line in selected_lines
        )
    log_y = _ACT_TWO_LOG_TEXT_RECT.y
    for line, line_color in visible_log_lines:
        screen.blit(
            log_font.render(
                line,
                True,
                line_color,
            ),
            (_ACT_TWO_LOG_TEXT_RECT.x, log_y),
        )
        log_y += line_height

    for slot_index, item in enumerate(consumable_slots[:5]):
        sprite_name = {
            "potion": "potion_belt",
            "fire_bomb": "fire_bomb_belt",
            "key": "key_belt",
        }.get(item)
        if sprite_name is None:
            continue
        item_sprite = pygame.transform.scale(
            sprites[sprite_name],
            _ACT_TWO_BELT_ITEM_SIZE,
        )
        screen.blit(
            item_sprite,
            _ACT_TWO_BELT_ITEM_POSITIONS[slot_index],
        )

    ability_asset_name = _ACT_TWO_ABILITY_ASSETS.get(player_class)
    if ability_asset_name in sprites:
        ability_icon = pygame.transform.scale(
            sprites[ability_asset_name],
            _ACT_TWO_ABILITY_RECT.size,
        )
        screen.blit(ability_icon, _ACT_TWO_ABILITY_RECT)
    for charge_index, charge_rectangle in enumerate(
        _ACT_TWO_ABILITY_CHARGE_RECTS
    ):
        pygame.draw.rect(
            screen,
            (
                (177, 40, 48)
                if charge_index < ability_kill_charge
                else (40, 35, 39)
            ),
            charge_rectangle,
        )

    screen.blit(
        sprites["act_two_gold_counter"],
        _ACT_TWO_GOLD_COUNTER_POSITION,
    )
    gold_surface = controls_font.render(
        str(gold_count),
        True,
        value_color,
    )
    screen.blit(
        gold_surface,
        gold_surface.get_rect(center=_ACT_TWO_GOLD_VALUE_CENTER),
    )

    if stats_open:
        screen.blit(sprites["act_two_stats_panel"], (948, 101))
    ability_hovered = (
        mouse_position is not None
        and _ACT_TWO_ABILITY_RECT.collidepoint(mouse_position)
    )
    if ability_hovered:
        screen.blit(
            sprites["act_two_abilities_panel"],
            _ACT_TWO_ABILITIES_PANEL_POSITION,
        )
        screen.blit(
            sprites["act_two_ability_text_backing"],
            _ACT_TWO_ABILITIES_TEXT_BACKING_POSITION,
        )
        if ability_asset_name in sprites:
            panel_icon = pygame.transform.scale(
                sprites[ability_asset_name],
                _ACT_TWO_ABILITIES_ICON_RECT.size,
            )
            screen.blit(panel_icon, _ACT_TWO_ABILITIES_ICON_RECT)

        description = _ACT_TWO_ABILITY_DESCRIPTIONS.get(
            player_class,
            "Choose a class to unlock its ability.",
        )
        description_lines = wrap_text(
            ability_font,
            description,
            _ACT_TWO_ABILITIES_TEXT_RECT.width,
        )
        maximum_description_lines = 3
        visible_description_lines = description_lines[
            :maximum_description_lines
        ]
        if len(description_lines) > maximum_description_lines:
            visible_description_lines[-1] = fit_text_to_width(
                ability_font,
                visible_description_lines[-1] + "...",
                _ACT_TWO_ABILITIES_TEXT_RECT.width,
            )
        description_y = _ACT_TWO_ABILITIES_TEXT_RECT.y
        for description_line in visible_description_lines:
            screen.blit(
                ability_font.render(
                    description_line,
                    True,
                    value_color,
                ),
                (_ACT_TWO_ABILITIES_TEXT_RECT.x, description_y),
            )
            description_y += 14
    screen.blit(sprites["act_two_side_buttons"], (1187, 195))
    remaining_attribute_points = max(
        0,
        available_attribute_points
        - sum(pending_attribute_upgrades.values()),
    )
    if remaining_attribute_points > 0:
        pulse_progress = (
                                 pygame.time.get_ticks() % 1200
                         ) / 1200
        pulse_strength = 1.0 - abs(pulse_progress * 2.0 - 1.0)

        indicator = sprites["act_two_level_up_indicator"].copy()
        indicator.set_alpha(
            round(145 + 110 * pulse_strength)
        )
        screen.blit(
            indicator,
            _ACT_TWO_LEVEL_UP_POSITION,
        )

    for button_name, button_rectangle in (
        _ACT_TWO_SIDEBAR_BUTTON_RECTS.items()
    ):
        is_hovered = (
            mouse_position is not None
            and button_rectangle.collidepoint(mouse_position)
        )
        is_selected = button_name == "stats" and stats_open
        if not (is_hovered or is_selected):
            continue
        highlight_rectangle = _ACT_TWO_SIDEBAR_HIGHLIGHT_RECTS[
            button_name
        ]
        highlight = pygame.Surface(
            highlight_rectangle.size,
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            highlight,
            (145, 26, 26, 42 if is_hovered else 25),
            highlight.get_rect(),
            border_radius=10,
        )
        screen.blit(highlight, highlight_rectangle)


    if not stats_open:
        return

    class_name = (player_class or "UNBOUND").upper()
    class_surface = title_font.render(class_name, True, (174, 21, 24))
    screen.blit(
        class_surface,
        class_surface.get_rect(center=(1069, 177)),
    )

    attribute_names = (
        "strength",
        "dexterity",
        "intelligence",
        "vitality",
    )

    attribute_values = tuple(
        attribute_ranks.get(attribute, 0)
        + pending_attribute_upgrades.get(attribute, 0)
        for attribute in attribute_names
    )

    for attribute, value, center_y in zip(
            attribute_names,
            attribute_values,
            (253, 281, 309, 337),
    ):
        is_pending = (
                pending_attribute_upgrades.get(attribute, 0) > 0
        )
        value_surface = controls_font.render(
            str(value),
            True,
            (218, 165, 75) if is_pending else value_color,
        )
        screen.blit(
            value_surface,
            value_surface.get_rect(center=(1117, center_y)),
        )
    for attribute, rectangle in (
            _ACT_TWO_ATTRIBUTE_PLUS_RECTS.items()
    ):
        future_rank = (
                attribute_ranks.get(attribute, 0)
                + pending_attribute_upgrades.get(attribute, 0)
        )
        can_increase = (
                remaining_attribute_points > 0
                and future_rank < MAX_ATTRIBUTE_RANK
        )
        is_hovered = (
                mouse_position is not None
                and rectangle.collidepoint(mouse_position)
        )

        if can_increase and is_hovered:
            pygame.draw.rect(
                screen,
                (0, 0, 0),
                rectangle,
                border_radius=4,
            )

        if not can_increase:
            plus_color = (75, 70, 72)
        elif is_hovered:
            plus_color = (245, 205, 105)
        else:
            plus_color = (190, 82, 64)

        plus_surface = controls_font.render(
            "+",
            True,
            plus_color,
        )
        screen.blit(
            plus_surface,
            plus_surface.get_rect(center=rectangle.center),
        )

    for attribute, rectangle in (
            _ACT_TWO_ATTRIBUTE_MINUS_RECTS.items()
    ):
        can_decrease = (
                pending_attribute_upgrades.get(attribute, 0) > 0
        )
        is_hovered = (
                mouse_position is not None
                and rectangle.collidepoint(mouse_position)
        )

        if can_decrease and is_hovered:
            pygame.draw.rect(
                screen,
                (0, 0, 0),
                rectangle,
                border_radius=4,
            )

        if not can_decrease:
            minus_color = (75, 70, 72)
        elif is_hovered:
            minus_color = (245, 205, 105)
        else:
            minus_color = (190, 82, 64)

        minus_surface = controls_font.render(
            "-",
            True,
            minus_color,
        )
        screen.blit(
            minus_surface,
            minus_surface.get_rect(center=rectangle.center),
        )

    combat_values = (
        f"{player_damage_min}-{player_damage_max}",
        f"{round(player_crit_chance * 100)}%",
        f"{round(player_dodge_chance * 100)}%",
        str(player_spell_power),
    )
    for value, center_y in zip(
        combat_values,
        (417, 445, 473, 501),
    ):
        value_surface = controls_font.render(
            value,
            True,
            value_color,
        )
        screen.blit(
            value_surface,
            value_surface.get_rect(center=(1117, center_y)),
        )

    pending_points = sum(pending_attribute_upgrades.values())

    if pending_points > 0:
        confirm_rectangle = _ACT_TWO_CONFIRM_BUTTON_RECT
        confirm_button = sprites["act_two_confirm_button"]

        screen.blit(
            confirm_button,
            confirm_rectangle,
        )

        confirm_hovered = (
                mouse_position is not None
                and _ACT_TWO_CONFIRM_BUTTON_HIT_RECT.collidepoint(
                mouse_position
            )
        )

        if confirm_hovered:
            hovered_button = confirm_button.copy()
            hovered_button.fill(
                (35, 18, 4, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            screen.blit(
                hovered_button,
                confirm_rectangle,
            )

def get_act_two_sidebar_button_rectangles():
    return {
        button_name: button_rectangle.copy()
        for button_name, button_rectangle in (
            _ACT_TWO_SIDEBAR_BUTTON_RECTS.items()
        )
    }


def get_act_two_belt_slot_rectangles():
    return tuple(
        pygame.Rect(
            item_x - 7,
            619,
            52,
            70,
        )
        for item_x, _item_y in _ACT_TWO_BELT_ITEM_POSITIONS[
            :CONSUMABLE_BELT_SIZE
        ]
    )


def get_act_two_attribute_plus_rectangles():
    return {
        attribute: rectangle.copy()
        for attribute, rectangle in (
            _ACT_TWO_ATTRIBUTE_PLUS_RECTS.items()
        )
    }


def get_act_two_attribute_minus_rectangles():
    return {
        attribute: rectangle.copy()
        for attribute, rectangle in (
            _ACT_TWO_ATTRIBUTE_MINUS_RECTS.items()
        )
    }


def get_act_two_confirm_button_rectangle():
    return _ACT_TWO_CONFIRM_BUTTON_HIT_RECT.copy()
