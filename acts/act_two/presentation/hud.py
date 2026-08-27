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

from presentation.figma_ui import (
    draw_figma_rectangle,
    draw_figma_text,
    figma_rect,
    get_figma_font,
)

_ACT_TWO_CONSUMABLE_SPRITES = {
    "potion": "potion_belt",
    "fire_bomb": "fire_bomb_belt",
    "key": "key_belt",
    "scroll_of_stoneflesh": "scroll_of_stoneflesh",
    "scroll_of_binding": "scroll_of_binding",
    "healing_scroll": "healing_scroll",
    "scroll_of_arcane_impulse": "scroll_of_arcane_impulse",
    "guild_seal": "guild_seal",
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
    "guild_seal": (
        "The trader's lost guild seal. "
        "It cannot be used or discarded."
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
    "guild_seal": "GUILD SEAL",
}


def _blit_layout_image(
    screen,
    image,
    rectangle_data,
):
    rectangle = figma_rect(rectangle_data)

    if image.get_size() != rectangle.size:
        image = pygame.transform.smoothscale(
            image,
            rectangle.size,
        )

    screen.blit(image, rectangle)


def _blit_layout_fill(
    screen,
    image,
    rectangle_data,
    ratio,
):
    rectangle = figma_rect(rectangle_data)
    ratio = max(0.0, min(1.0, ratio))

    if ratio <= 0:
        return

    if image.get_size() != rectangle.size:
        image = pygame.transform.smoothscale(
            image,
            rectangle.size,
        )

    visible_width = round(rectangle.width * ratio)

    if visible_width <= 0:
        return

    screen.blit(
        image,
        rectangle,
        pygame.Rect(
            0,
            0,
            visible_width,
            rectangle.height,
        ),
    )


def _draw_dynamic_figma_text(
    screen,
    text_spec,
    value,
    color=None,
):
    runtime_spec = {
        **text_spec,
        "text": str(value),
    }

    if color is not None:
        runtime_spec["color"] = {
            "r": color[0],
            "g": color[1],
            "b": color[2],
            "a": color[3] if len(color) > 3 else 255,
        }

    draw_figma_text(screen, runtime_spec)
def _offset_layout(
    value,
    offset_x,
    offset_y,
):
    if isinstance(value, dict):
        shifted = {
            key: _offset_layout(
                child,
                offset_x,
                offset_y,
            )
            for key, child in value.items()
        }

        if (
            "x" in value
            and "y" in value
            and "width" in value
            and "height" in value
        ):
            shifted["x"] = value["x"] + offset_x
            shifted["y"] = value["y"] + offset_y

        return shifted

    if isinstance(value, list):
        return [
            _offset_layout(
                child,
                offset_x,
                offset_y,
            )
            for child in value
        ]

    return value


def _draw_wrapped_figma_text(
    screen,
    text_spec,
    value,
):
    text_rectangle = figma_rect(text_spec["rect"])
    text_font = get_figma_font(text_spec)

    wrapped_lines = wrap_text(
        text_font,
        str(value),
        text_rectangle.width,
    ) or [""]

    line_height = max(1, text_font.get_linesize())
    maximum_line_count = max(
        1,
        text_rectangle.height // line_height,
    )

    visible_lines = wrapped_lines[:maximum_line_count]

    if len(wrapped_lines) > maximum_line_count:
        visible_lines[-1] = fit_text_to_width(
            text_font,
            visible_lines[-1] + "...",
            text_rectangle.width,
        )

    _draw_dynamic_figma_text(
        screen,
        text_spec,
        "\n".join(visible_lines),
    )


def _draw_act_two_hover_panel(
    screen,
    sprites,
    info_layout,
    icon_asset_name,
    name,
    description,
):
    _blit_layout_image(
        screen,
        sprites["act_two_abilities_panel"],
        info_layout["frame"],
    )

    draw_figma_rectangle(
        screen,
        info_layout["description_backing"],
    )

    draw_figma_rectangle(
        screen,
        info_layout["name_backing"],
    )

    if icon_asset_name in sprites:
        _blit_layout_image(
            screen,
            sprites[icon_asset_name],
            info_layout["icon"],
        )

    name_spec = info_layout["name"]
    name_font = get_figma_font(name_spec)
    name_rectangle = figma_rect(name_spec["rect"])

    visible_name = fit_text_to_width(
        name_font,
        name,
        name_rectangle.width,
    )

    _draw_dynamic_figma_text(
        screen,
        name_spec,
        visible_name,
    )

    _draw_wrapped_figma_text(
        screen,
        info_layout["description"],
        description,
    )


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
    ability_charge_required,
    available_attribute_points,
    stats_open,
    mouse_position,
    sprites,
    hud_layout,
    invisibility_turns,
    stoneflesh_hits,
    bloody_pact_id,
    dragged_consumable_slot=None,
):
    top_bar_layout = hud_layout["top_bar"]

    health_ratio = player_health / max(1, player_max_health)

    experience_required = experience_required_for_level(
        player_level
    )
    experience_ratio = (
            player_experience / max(1, experience_required)
    )

    _blit_layout_fill(
        screen,
        sprites["act_two_hud_hp"],
        top_bar_layout["hp_fill"],
        health_ratio,
    )

    _blit_layout_fill(
        screen,
        sprites["act_two_hud_xp"],
        top_bar_layout["xp_fill"],
        experience_ratio,
    )

    _blit_layout_image(
        screen,
        sprites["act_two_hud_frame"],
        top_bar_layout["frame"],
    )

    if player_class is not None:
        _blit_layout_image(
            screen,
            sprites[f"player_{player_class}"],
            top_bar_layout["portrait"],
        )

    _draw_dynamic_figma_text(
        screen,
        top_bar_layout["level"],
        player_level,
    )

    _draw_dynamic_figma_text(
        screen,
        top_bar_layout["hp_text"],
        f"{player_health}/{player_max_health}",
    )

    _draw_dynamic_figma_text(
        screen,
        top_bar_layout["xp_text"],
        f"{player_experience}/{experience_required}",
    )

    status_layout = top_bar_layout["status_effects"]

    active_status_effects = []

    if invisibility_turns > 0:
        active_status_effects.append(
            (
                "rogue_invisibility_icon",
                invisibility_turns,
            )
        )

    if selected_rune_id is not None:
        active_status_effects.append(
            (
                f"{selected_rune_id}_icon",
                None,
            )
        )

    if bloody_pact_id is not None:
        active_status_effects.append(
            (
                f"bloody_pact_{bloody_pact_id}",
                None,
            )
        )

    if stoneflesh_hits > 0:
        active_status_effects.append(
            (
                "trader_scroll_of_stoneflesh",
                stoneflesh_hits,
            )
        )

    status_slots = tuple(
        status_layout["slots"][slot_name]
        for slot_name in sorted(status_layout["slots"])
    )

    for slot_layout, status_effect in zip(
        status_slots,
        active_status_effects,
    ):
        sprite_name, remaining_value = status_effect

        if sprite_name not in sprites:
            continue

        draw_figma_rectangle(
            screen,
            slot_layout["frame"],
        )

        _blit_layout_image(
            screen,
            sprites[sprite_name],
            slot_layout["icon"],
        )

        if remaining_value is not None:
            _draw_dynamic_figma_text(
                screen,
                slot_layout["value"],
                remaining_value,
            )

    value_color = (239, 235, 225)

    down_bar_layout = hud_layout["down_bar"]

    _blit_layout_image(
        screen,
        sprites["act_two_bottom_bar"],
        down_bar_layout["frame"],
    )
    combat_log_layout = down_bar_layout["combat_log"]

    draw_figma_rectangle(
        screen,
        combat_log_layout["backing"],
    )

    log_line_specs = tuple(
        combat_log_layout["lines"][line_name]
        for line_name in sorted(combat_log_layout["lines"])
    )

    maximum_line_count = len(log_line_specs)
    selected_messages = []
    remaining_line_count = maximum_line_count

    for message in reversed(combat_log):
        if remaining_line_count <= 0:
            break

        reference_spec = log_line_specs[0]
        reference_rect = figma_rect(reference_spec["rect"])
        reference_font = get_figma_font(reference_spec)

        wrapped_lines = wrap_text(
            reference_font,
            message,
            reference_rect.width,
        ) or [""]

        selected_lines = wrapped_lines[:remaining_line_count]

        if len(selected_lines) < len(wrapped_lines):
            last_line_spec = log_line_specs[
                remaining_line_count - 1
            ]
            last_line_rect = figma_rect(
                last_line_spec["rect"]
            )
            last_line_font = get_figma_font(last_line_spec)

            selected_lines[-1] = fit_text_to_width(
                last_line_font,
                selected_lines[-1] + "...",
                last_line_rect.width,
            )

        selected_messages.append(
            (
                selected_lines,
                get_event_color(message),
            )
        )

        remaining_line_count -= len(selected_lines)

    visible_log_lines = []

    for selected_lines, line_color in reversed(selected_messages):
        visible_log_lines.extend(
            (line, line_color)
            for line in selected_lines
        )

    for line_spec, visible_line in zip(
        log_line_specs,
        visible_log_lines,
    ):
        line_text, line_color = visible_line

        _draw_dynamic_figma_text(
            screen,
            line_spec,
            line_text,
            color=line_color,
        )

    consumable_slots_layout = tuple(
        down_bar_layout["consumable_belt"]["slots"][slot_name]
        for slot_name in sorted(
            down_bar_layout["consumable_belt"]["slots"]
        )
    )

    for slot_index, item in enumerate(
        consumable_slots[:CONSUMABLE_BELT_SIZE]
    ):
        if slot_index == dragged_consumable_slot:
            continue

        if slot_index >= len(consumable_slots_layout):
            break

        sprite_name = _ACT_TWO_CONSUMABLE_SPRITES.get(item)

        if sprite_name is None:
            continue

        _blit_layout_image(
            screen,
            sprites[sprite_name],
            consumable_slots_layout[slot_index]["icon"],
        )

    if (
        dragged_consumable_slot is not None
        and mouse_position is not None
        and 0 <= dragged_consumable_slot < len(consumable_slots)
    ):
        dragged_item = consumable_slots[dragged_consumable_slot]
        sprite_name = _ACT_TWO_CONSUMABLE_SPRITES.get(dragged_item)
        if sprite_name is not None:
            dragged_icon_size = (
                figma_rect(
                    consumable_slots_layout[
                        dragged_consumable_slot
                    ]["icon"]
                ).size
                if (
                    dragged_consumable_slot
                    < len(consumable_slots_layout)
                )
                else (26, 26)
            )

            item_sprite = pygame.transform.smoothscale(
                sprites[sprite_name],
                dragged_icon_size,
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
                    get_act_two_belt_slot_rectangles(hud_layout)
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
        hovered_item = consumable_slots[
            hovered_consumable_slot
        ]

        sprite_name = _ACT_TWO_CONSUMABLE_SPRITES.get(
            hovered_item
        )

        slot_rectangle = (
            get_act_two_belt_slot_rectangles(
                hud_layout
            )[hovered_consumable_slot]
        )

        base_info_layout = hud_layout["info"]
        base_info_rectangle = figma_rect(
            base_info_layout["rect"]
        )

        target_left = (
            slot_rectangle.centerx
            - base_info_rectangle.width // 2
        )

        target_left = max(
            0,
            min(
                screen.get_width()
                - base_info_rectangle.width,
                target_left,
            ),
        )

        info_layout = _offset_layout(
            base_info_layout,
            target_left - base_info_rectangle.left,
            0,
        )

        _draw_act_two_hover_panel(
            screen,
            sprites,
            info_layout,
            sprite_name,
            _ACT_TWO_CONSUMABLE_NAMES.get(
                hovered_item,
                "ITEM",
            ),
            _ACT_TWO_CONSUMABLE_DESCRIPTIONS.get(
                hovered_item,
                "Consumable item.",
            ),
        )

    selected_rune = RUNES_BY_ID.get(selected_rune_id)

    base_ability_asset_name = _ACT_TWO_ABILITY_ASSETS.get(player_class)

    displayed_ability_asset_name = (
        f"{selected_rune.id}_icon"
        if selected_rune is not None
        else base_ability_asset_name
    )

    displayed_ability_name = (
        selected_rune.name
        if selected_rune is not None
        else _ACT_TWO_ABILITY_NAMES.get(player_class, "ABILITY")
    )

    displayed_ability_description = (
        selected_rune.description
        if selected_rune is not None
        else _ACT_TWO_ABILITY_DESCRIPTIONS.get(
            player_class,
            "Choose a class to unlock its ability.",
        )
    )

    ability_layout = down_bar_layout["ability"]
    ability_hitbox = figma_rect(ability_layout["hitbox"])

    if displayed_ability_asset_name in sprites:
        _blit_layout_image(
            screen,
            sprites[displayed_ability_asset_name],
            ability_layout["icon"],
        )

    charge_layouts = tuple(
        ability_layout["charges"][charge_name]
        for charge_name in sorted(ability_layout["charges"])
    )

    displayed_charge = round(
        min(
            1.0,
            ability_kill_charge / max(1, ability_charge_required),
        )
        * len(charge_layouts)
    )

    active_charge_fill = (
        charge_layouts[0].get("fill")
        if charge_layouts
        else None
    )

    inactive_charge_fill = (
        charge_layouts[1].get("fill")
        if len(charge_layouts) > 1
        else active_charge_fill
    )

    for charge_index, charge_layout in enumerate(charge_layouts):
        runtime_charge_layout = {
            **charge_layout,
            "fill": (
                active_charge_fill
                if charge_index < displayed_charge
                else inactive_charge_fill
            ),
        }

        draw_figma_rectangle(
            screen,
            runtime_charge_layout,
        )

    gold_layout = down_bar_layout["gold"]

    _blit_layout_image(
        screen,
        sprites["act_two_gold_counter"],
        gold_layout["icon"],
    )

    _draw_dynamic_figma_text(
        screen,
        gold_layout["value"],
        gold_count,
    )

    right_bar_layout = hud_layout["right_bar"]
    tabs_layout = right_bar_layout["tabs"]
    tabs_buttons = tabs_layout["buttons"]
    stats_panel_layout = right_bar_layout["stats_panel"]

    if stats_open:
        _blit_layout_image(
            screen,
            sprites["act_two_stats_panel"],
            stats_panel_layout["frame"],
        )

    ability_hovered = (
        mouse_position is not None
        and ability_hitbox.collidepoint(mouse_position)
    )

    if ability_hovered:
        _draw_act_two_hover_panel(
            screen,
            sprites,
            hud_layout["info"],
            displayed_ability_asset_name,
            displayed_ability_name,
            displayed_ability_description,
        )

    _blit_layout_image(
        screen,
        sprites["act_two_side_buttons"],
        tabs_layout["frame"],
    )

    remaining_attribute_points = max(
        0,
        available_attribute_points
        - sum(pending_attribute_upgrades.values()),
    )

    if remaining_attribute_points > 0:
        pulse_progress = (
            pygame.time.get_ticks() % 1200
        ) / 1200

        pulse_strength = (
            1.0 - abs(pulse_progress * 2.0 - 1.0)
        )

        indicator_rectangle = figma_rect(
            tabs_layout["level_up_indicator"]
        )

        indicator = pygame.transform.smoothscale(
            sprites["act_two_level_up_indicator"],
            indicator_rectangle.size,
        )

        indicator.set_alpha(
            round(145 + 110 * pulse_strength)
        )

        screen.blit(
            indicator,
            indicator_rectangle,
        )

    for button_name, button_layout in tabs_buttons.items():
        button_rectangle = figma_rect(
            button_layout["hitbox"]
        )

        is_hovered = (
            mouse_position is not None
            and button_rectangle.collidepoint(mouse_position)
        )

        is_selected = (
            button_name == "stats"
            and stats_open
        )

        if not (is_hovered or is_selected):
            continue

        draw_figma_rectangle(
            screen,
            button_layout["highlight"],
        )


    if not stats_open:
        return

    muted_color = (174, 154, 143)

    class_name = (
            player_class or "UNBOUND"
    ).title()

    _draw_dynamic_figma_text(
        screen,
        stats_panel_layout["class_name"],
        class_name,
    )

    attribute_names = (
        "strength",
        "dexterity",
        "intelligence",
        "vitality",
    )

    attribute_rows = (
        stats_panel_layout["attributes"]["rows"]
    )

    attribute_values = {
        attribute: (
                attribute_ranks.get(attribute, 0)
                + pending_attribute_upgrades.get(attribute, 0)
        )
        for attribute in attribute_names
    }

    for attribute in attribute_names:
        row_layout = attribute_rows[attribute]

        _draw_dynamic_figma_text(
            screen,
            row_layout["label"],
            attribute.title(),
        )

        is_pending = (
                pending_attribute_upgrades.get(attribute, 0) > 0
        )

        _draw_dynamic_figma_text(
            screen,
            row_layout["value"],
            attribute_values[attribute],
            color=(
                (218, 165, 75, 255)
                if is_pending
                else None
            ),
        )

    upgrade_mode = available_attribute_points > 0

    if upgrade_mode:
        for attribute in attribute_names:
            row_layout = attribute_rows[attribute]

            plus_rectangle = figma_rect(
                row_layout["plus_hitbox"]
            )
            minus_rectangle = figma_rect(
                row_layout["minus_hitbox"]
            )

            future_rank = attribute_values[attribute]

            can_increase = (
                    remaining_attribute_points > 0
                    and future_rank < MAX_ATTRIBUTE_RANK
            )

            can_decrease = (
                    pending_attribute_upgrades.get(
                        attribute,
                        0,
                    ) > 0
            )

            plus_hovered = (
                    mouse_position is not None
                    and plus_rectangle.collidepoint(
                mouse_position
            )
            )

            minus_hovered = (
                    mouse_position is not None
                    and minus_rectangle.collidepoint(
                mouse_position
            )
            )

            plus_color = (
                (75, 70, 72, 255)
                if not can_increase
                else (245, 205, 105, 255)
                if plus_hovered
                else None
            )

            minus_color = (
                (75, 70, 72, 255)
                if not can_decrease
                else (245, 205, 105, 255)
                if minus_hovered
                else None
            )

            _draw_dynamic_figma_text(
                screen,
                row_layout["plus"],
                "+",
                color=plus_color,
            )

            _draw_dynamic_figma_text(
                screen,
                row_layout["minus"],
                "-",
                color=minus_color,
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

def get_act_two_sidebar_button_rectangles(hud_layout):
    buttons = hud_layout["right_bar"]["tabs"]["buttons"]

    return {
        button_name: figma_rect(button_layout["hitbox"])
        for button_name, button_layout in buttons.items()
    }


def get_act_two_belt_slot_rectangles(hud_layout):
    slots = hud_layout["down_bar"]["consumable_belt"]["slots"]

    return tuple(
        figma_rect(slots[slot_name]["hitbox"])
        for slot_name in sorted(slots)
    )[:CONSUMABLE_BELT_SIZE]


def get_act_two_attribute_plus_rectangles(hud_layout):
    rows = (
        hud_layout["right_bar"]
        ["stats_panel"]
        ["attributes"]
        ["rows"]
    )

    return {
        attribute: figma_rect(row["plus_hitbox"])
        for attribute, row in rows.items()
    }


def get_act_two_attribute_minus_rectangles(hud_layout):
    rows = (
        hud_layout["right_bar"]
        ["stats_panel"]
        ["attributes"]
        ["rows"]
    )

    return {
        attribute: figma_rect(row["minus_hitbox"])
        for attribute, row in rows.items()
    }


def get_act_two_confirm_button_rectangle():
    return _ACT_TWO_CONFIRM_BUTTON_HIT_RECT.copy()
