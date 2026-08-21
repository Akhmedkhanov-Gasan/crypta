import pygame

from acts.act_two.rune_catalog import RUNES_BY_ID
from settings import MAX_ATTRIBUTE_RANK

from acts.act_two.settings import (
    CONSUMABLE_BELT_SIZE,
)
from game.progression import experience_required_for_level
from presentation.hud import (
    fit_text_to_width,
    get_event_color,
    wrap_text,
)


_ACT_TWO_BOTTOM_BAR_POSITION = (456, 609)
_ACT_TWO_BELT_ITEM_POSITIONS = (
    (476, 656),
    (519, 656),
    (561, 656),
    (605, 656),
    (649, 657),
    (694, 656),
)
_ACT_TWO_BELT_ITEM_SIZE = (26, 26)
_ACT_TWO_ABILITY_RECT = pygame.Rect(754, 651, 30, 30)
_ACT_TWO_RUNE_RECT = pygame.Rect(718, 651, 30, 30)
_ACT_TWO_CONSUMABLE_SPRITES = {
    "potion": "potion_belt",
    "fire_bomb": "fire_bomb_belt",
    "key": "key_belt",
    "scroll_of_stoneflesh": "scroll_of_stoneflesh",
    "scroll_of_binding": "scroll_of_binding",
    "healing_scroll": "healing_scroll",
    "scroll_of_arcane_impulse": "scroll_of_arcane_impulse",
}
_ACT_TWO_ABILITY_CHARGE_RECTS = (
    pygame.Rect(757, 679, 5, 3),
    pygame.Rect(764, 679, 4, 3),
    pygame.Rect(770, 679, 5, 3),
    pygame.Rect(777, 679, 4, 3),
)
_ACT_TWO_LOG_TEXT_RECT = pygame.Rect(38, 630, 247, 60)
_ACT_TWO_LOG_BACKING_POSITION = (23, 619)
_ACT_TWO_SIDEBAR_BUTTON_RECTS = {
    "stats": pygame.Rect(1218, 267, 55, 45),
    "placeholder": pygame.Rect(1218, 311, 55, 45),
    "settings": pygame.Rect(1218, 355, 55, 45),
}
_ACT_TWO_SIDEBAR_HIGHLIGHT_RECTS = {
    "stats": pygame.Rect(1227, 276, 36, 34),
    "placeholder": pygame.Rect(1227, 320, 36, 34),
    "settings": pygame.Rect(1227, 364, 36, 34),
}
_ACT_TWO_ATTRIBUTE_PLUS_RECTS = {
    "strength": pygame.Rect(1162, 245, 22, 19),
    "dexterity": pygame.Rect(1162, 266, 22, 19),
    "intelligence": pygame.Rect(1162, 287, 22, 19),
    "vitality": pygame.Rect(1162, 308, 22, 19),
}
_ACT_TWO_ATTRIBUTE_MINUS_RECTS = {
    "strength": pygame.Rect(1114, 245, 22, 19),
    "dexterity": pygame.Rect(1114, 266, 22, 19),
    "intelligence": pygame.Rect(1114, 287, 22, 19),
    "vitality": pygame.Rect(1114, 308, 22, 19),
}
_ACT_TWO_CONFIRM_BUTTON_RECT = pygame.Rect(
    1049,
    326,
    121,
    40,
)
_ACT_TWO_CONFIRM_BUTTON_HIT_RECT = (
    _ACT_TWO_CONFIRM_BUTTON_RECT.inflate(-24, -12)
)
_ACT_TWO_ABILITIES_PANEL_POSITION = (637, 496)
_ACT_TWO_ABILITIES_ICON_RECT = pygame.Rect(671, 570, 36, 36)
_ACT_TWO_ABILITIES_TEXT_BACKING_POSITION = (724, 562)
_ACT_TWO_ABILITIES_TEXT_RECT = pygame.Rect(732, 570, 130, 50)
_ACT_TWO_ABILITIES_NAME_BACKING_POSITION = (747, 544)
_ACT_TWO_ABILITIES_NAME_RECT = pygame.Rect(751, 548, 78, 15)
_ACT_TWO_ABILITY_ASSETS = {
    "warrior": "warrior_power_cleave_icon",
    "rogue": "rogue_invisibility_icon",
    "mage": "mage_arcane_burst_icon",
}
_ACT_TWO_ABILITY_DESCRIPTIONS = {
    "warrior": "Cleave three tiles and knock enemies back.",
    "rogue": "Vanish. Your next attack is a sure critical.",
    "mage": "Burst a cross at range and scatter enemies outward.",
}
_ACT_TWO_ABILITY_NAMES = {
    "warrior": "POWER CLEAVE",
    "rogue": "INVISIBILITY",
    "mage": "ARCANE BURST",
}
_ACT_TWO_CONSUMABLE_DESCRIPTIONS = {
    "potion": "Restores 4 health.",
    "fire_bomb": "Ignites a 3x3 area and burns everything inside.",
    "key": "Opens one locked chest.",
    "scroll_of_stoneflesh": (
        "Reduces the next 6 physical hits by 60%."
    ),
    "scroll_of_binding": "Binds one visible enemy for 5 turns.",
    "healing_scroll": "Restores 6 health.",
    "scroll_of_arcane_impulse": (
        "Deals 5 magic damage to one visible enemy."
    ),
}
_ACT_TWO_CONSUMABLE_NAMES = {
    "potion": "POTION",
    "fire_bomb": "FIRE BOMB",
    "key": "KEY",
    "scroll_of_stoneflesh": "STONEFLESH",
    "scroll_of_binding": "BINDING",
    "healing_scroll": "HEALING",
    "scroll_of_arcane_impulse": "IMPULSE",
}
_ACT_TWO_LEVEL_UP_POSITION = (1210, 258)
_ACT_TWO_GOLD_COUNTER_POSITION = (1193, 631)
_ACT_TWO_GOLD_VALUE_CENTER = (1231, 679)


def _draw_act_two_hover_panel(
    screen,
    ability_font,
    sprites,
    panel_position,
    icon_asset_name,
    name,
    description,
    text_color,
):
    panel_offset = (
        panel_position[0] - _ACT_TWO_ABILITIES_PANEL_POSITION[0],
        panel_position[1] - _ACT_TWO_ABILITIES_PANEL_POSITION[1],
    )
    relative_icon_rect = _ACT_TWO_ABILITIES_ICON_RECT.move(*panel_offset)
    relative_text_backing_position = (
        _ACT_TWO_ABILITIES_TEXT_BACKING_POSITION[0] + panel_offset[0],
        _ACT_TWO_ABILITIES_TEXT_BACKING_POSITION[1] + panel_offset[1],
    )
    relative_text_rect = _ACT_TWO_ABILITIES_TEXT_RECT.move(
        *panel_offset
    )
    relative_name_backing_position = (
        _ACT_TWO_ABILITIES_NAME_BACKING_POSITION[0] + panel_offset[0],
        _ACT_TWO_ABILITIES_NAME_BACKING_POSITION[1] + panel_offset[1],
    )
    relative_name_rect = _ACT_TWO_ABILITIES_NAME_RECT.move(
        *panel_offset
    )

    screen.blit(sprites["act_two_abilities_panel"], panel_position)
    screen.blit(
        sprites["act_two_ability_text_backing"],
        relative_text_backing_position,
    )
    screen.blit(
        sprites["act_two_ability_name_backing"],
        relative_name_backing_position,
    )
    if icon_asset_name in sprites:
        panel_icon = pygame.transform.scale(
            sprites[icon_asset_name],
            relative_icon_rect.size,
        )
        screen.blit(panel_icon, relative_icon_rect)

    visible_name = fit_text_to_width(
        ability_font,
        name,
        relative_name_rect.width - 4,
    )
    name_surface = ability_font.render(
        visible_name,
        True,
        text_color,
    )
    screen.blit(
        name_surface,
        name_surface.get_rect(center=relative_name_rect.center),
    )

    description_lines = wrap_text(
        ability_font,
        description,
        relative_text_rect.width,
    )
    maximum_description_lines = 3
    visible_description_lines = description_lines[
        :maximum_description_lines
    ]
    if len(description_lines) > maximum_description_lines:
        visible_description_lines[-1] = fit_text_to_width(
            ability_font,
            visible_description_lines[-1] + "...",
            relative_text_rect.width,
        )
    line_height = 16
    description_y = (
        relative_text_rect.centery
        - len(visible_description_lines) * line_height // 2
    )
    for line in visible_description_lines:
        line_surface = ability_font.render(line, True, text_color)
        screen.blit(
            line_surface,
            line_surface.get_rect(
                midtop=(relative_text_rect.centerx, description_y)
            ),
        )
        description_y += line_height


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
    player_critical_damage_multiplier,
    player_dodge_chance,
    player_spell_power,
    attribute_ranks,
    pending_attribute_upgrades,
    consumable_slots,
    gold_count,
    player_class,
    selected_rune_id,
    player_level,
    player_experience,
    ability_kill_charge,
    available_attribute_points,
    stats_open,
    mouse_position,
    sprites,
    dragged_consumable_slot=None,

):
    def draw_fill(
        asset_name,
        position,
        ratio,
        hidden_leading_width=0,
    ):
        asset = sprites[asset_name]
        clamped_ratio = max(0.0, min(1.0, ratio))
        usable_width = max(
            0,
            asset.get_width() - hidden_leading_width,
        )
        visible_width = hidden_leading_width + round(
            usable_width * clamped_ratio
        )
        if clamped_ratio > 0 and visible_width > 0:
            screen.blit(
                asset,
                position,
                pygame.Rect(0, 0, visible_width, asset.get_height()),
            )

    health_ratio = player_health / max(1, player_max_health)
    experience_required = experience_required_for_level(player_level)
    experience_ratio = player_experience / max(1, experience_required)
    draw_fill("act_two_hud_hp", (65, 41), health_ratio)
    draw_fill(
        "act_two_hud_xp",
        (29, 67),
        experience_ratio,
        hidden_leading_width=54,
    )

    screen.blit(sprites["act_two_hud_frame"], (15, 17))

    portrait_rectangle = pygame.Rect(33, 38, 39, 38)
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
        level_surface.get_rect(center=(75, 85)),
    )
    hp_surface = controls_font.render(
        f"{player_health}/{player_max_health}",
        True,
        value_color,
    )
    screen.blit(hp_surface, hp_surface.get_rect(center=(194, 50)))
    xp_surface = controls_font.render(
        f"{player_experience}/{experience_required}",
        True,
        value_color,
    )
    screen.blit(xp_surface, xp_surface.get_rect(center=(176, 74)))

    screen.blit(
        sprites["act_two_bottom_bar"],
        _ACT_TWO_BOTTOM_BAR_POSITION,
    )
    screen.blit(
        sprites["act_two_chat_log_backing"],
        _ACT_TWO_LOG_BACKING_POSITION,
    )
    line_height = 14
    maximum_line_count = (
        _ACT_TWO_LOG_TEXT_RECT.height // line_height
    )
    selected_messages = []
    remaining_line_count = maximum_line_count
    for message in reversed(combat_log):
        if remaining_line_count <= 0:
            break
        wrapped_lines = wrap_text(
            log_font,
            message,
            _ACT_TWO_LOG_TEXT_RECT.width,
        ) or [""]
        selected_lines = wrapped_lines[:remaining_line_count]
        if len(selected_lines) < len(wrapped_lines):
            selected_lines[-1] = fit_text_to_width(
                log_font,
                selected_lines[-1] + "...",
                _ACT_TWO_LOG_TEXT_RECT.width,
            )
        selected_messages.append(
            (selected_lines, get_event_color(message))
        )
        remaining_line_count -= len(selected_lines)

    visible_log_lines = []
    for selected_lines, color in reversed(selected_messages):
        visible_log_lines.extend(
            (line, color) for line in selected_lines
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

    for slot_index, item in enumerate(
        consumable_slots[:CONSUMABLE_BELT_SIZE]
    ):
        if slot_index == dragged_consumable_slot:
            continue
        sprite_name = _ACT_TWO_CONSUMABLE_SPRITES.get(item)
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

    if (
        dragged_consumable_slot is not None
        and mouse_position is not None
        and 0 <= dragged_consumable_slot < len(consumable_slots)
    ):
        dragged_item = consumable_slots[dragged_consumable_slot]
        sprite_name = _ACT_TWO_CONSUMABLE_SPRITES.get(dragged_item)
        if sprite_name is not None:
            item_sprite = pygame.transform.scale(
                sprites[sprite_name],
                _ACT_TWO_BELT_ITEM_SIZE,
            )
            screen.blit(
                item_sprite,
                item_sprite.get_rect(center=mouse_position),
            )

    hovered_consumable_slot = None
    if mouse_position is not None and dragged_consumable_slot is None:
        hovered_consumable_slot = next(
            (
                slot_index
                for slot_index, rectangle in enumerate(
                    get_act_two_belt_slot_rectangles()
                )
                if (
                    rectangle.collidepoint(mouse_position)
                    and slot_index < len(consumable_slots)
                    and consumable_slots[slot_index] is not None
                )
            ),
            None,
        )

    if hovered_consumable_slot is not None:
        hovered_item = consumable_slots[hovered_consumable_slot]
        slot_rectangle = get_act_two_belt_slot_rectangles()[
            hovered_consumable_slot
        ]
        panel = sprites["act_two_abilities_panel"]
        panel_position = (
            slot_rectangle.centerx - panel.get_width() // 2,
            _ACT_TWO_ABILITIES_PANEL_POSITION[1],
        )
        sprite_name = _ACT_TWO_CONSUMABLE_SPRITES.get(hovered_item)
        _draw_act_two_hover_panel(
            screen,
            ability_font,
            sprites,
            panel_position,
            sprite_name,
            _ACT_TWO_CONSUMABLE_NAMES.get(
                hovered_item,
                "ITEM",
            ),
            _ACT_TWO_CONSUMABLE_DESCRIPTIONS.get(
                hovered_item,
                "Consumable item.",
            ),
            value_color,
        )

    selected_rune = RUNES_BY_ID.get(selected_rune_id)
    rune_asset_name = (
        f"{selected_rune.id}_icon"
        if selected_rune is not None
        else None
    )
    if rune_asset_name in sprites:
        rune_icon = pygame.transform.scale(
            sprites[rune_asset_name],
            _ACT_TWO_RUNE_RECT.size,
        )
        screen.blit(rune_icon, _ACT_TWO_RUNE_RECT)

    rune_hovered = (
        selected_rune is not None
        and mouse_position is not None
        and _ACT_TWO_RUNE_RECT.collidepoint(mouse_position)
    )
    if rune_hovered:
        panel = sprites["act_two_abilities_panel"]
        panel_position = (
            _ACT_TWO_RUNE_RECT.centerx - panel.get_width() // 2,
            _ACT_TWO_ABILITIES_PANEL_POSITION[1],
        )
        _draw_act_two_hover_panel(
            screen,
            ability_font,
            sprites,
            panel_position,
            rune_asset_name,
            selected_rune.name,
            selected_rune.description,
            value_color,
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
        screen.blit(sprites["act_two_stats_panel"], (991, 183))
    ability_hovered = (
        mouse_position is not None
        and _ACT_TWO_ABILITY_RECT.collidepoint(mouse_position)
    )
    if ability_hovered:
        _draw_act_two_hover_panel(
            screen,
            ability_font,
            sprites,
            _ACT_TWO_ABILITIES_PANEL_POSITION,
            ability_asset_name,
            _ACT_TWO_ABILITY_NAMES.get(player_class, "ABILITY"),
            _ACT_TWO_ABILITY_DESCRIPTIONS.get(
                player_class,
                "Choose a class to unlock its ability.",
            ),
            value_color,
        )
    screen.blit(sprites["act_two_side_buttons"], (1212, 249))
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

    muted_color = (174, 154, 143)
    class_name = (player_class or "UNBOUND").title()
    class_surface = title_font.render(class_name, True, muted_color)
    screen.blit(
        class_surface,
        class_surface.get_rect(center=(1112, 230)),
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
            (254, 275, 296, 317),
    ):
        label_surface = log_font.render(
            attribute.title(),
            True,
            muted_color,
        )
        screen.blit(
            label_surface,
            label_surface.get_rect(midleft=(1034, center_y)),
        )
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
            value_surface.get_rect(center=(1149, center_y)),
        )
    upgrade_mode = available_attribute_points > 0
    if upgrade_mode:
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

            plus_color = (
                (75, 70, 72)
                if not can_increase
                else (245, 205, 105)
                if is_hovered
                else (190, 82, 64)
            )
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

            minus_color = (
                (75, 70, 72)
                if not can_decrease
                else (245, 205, 105)
                if is_hovered
                else (190, 82, 64)
            )
            minus_surface = controls_font.render(
                "-",
                True,
                minus_color,
            )
            screen.blit(
                minus_surface,
                minus_surface.get_rect(center=rectangle.center),
            )

    combat_heading = log_font.render(
        "Combat stats",
        True,
        muted_color,
    )
    screen.blit(
        combat_heading,
        combat_heading.get_rect(center=(1109, 371)),
    )
    combat_rows = (
        ("Damage", f"{player_damage_min}-{player_damage_max}"),
        (
            "Critical",
            f"{round(player_crit_chance * 100)}% "
            f"x{player_critical_damage_multiplier:.1f}",
        ),
        ("Dodge", f"{round(player_dodge_chance * 100)}%"),
        ("Magical power", str(player_spell_power)),
    )
    for (label, value), center_y in zip(
        combat_rows,
        (393, 413, 431, 453),
    ):
        label_surface = log_font.render(
            label,
            True,
            muted_color,
        )
        screen.blit(
            label_surface,
            label_surface.get_rect(midleft=(1034, center_y)),
        )
        value_surface = controls_font.render(
            value,
            True,
            muted_color,
        )
        screen.blit(
            value_surface,
            value_surface.get_rect(center=(1150, center_y)),
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
            item_x - 8,
            638,
            42,
            64,
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
