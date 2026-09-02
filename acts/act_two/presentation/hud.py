import pygame

from game.rune_catalog import RUNES_BY_ID
from acts.act_two.bloody_altar_catalog import BLOODY_PACTS_BY_ID
from settings import MAX_ATTRIBUTE_RANK

from acts.act_two.settings import (
    CONSUMABLE_BELT_SIZE,
)
from acts.act_two.bloody_altar import BLOOD_HUNGER
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
    "healing_scroll": "Restores 8 health.",
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
_ACT_TWO_HEALING_CONSUMABLES = frozenset(
    (
        "potion",
        "healing_scroll",
    )
)


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



def _draw_act_two_compact_combat_log_contents(
    screen,
    combat_log,
    combat_log_layout,
):
    viewport_rectangle = figma_rect(
        combat_log_layout["viewport"]
    )

    row_template = combat_log_layout["row_template"]
    text_template = row_template["text"]
    separator_template = row_template["separator"]

    text_template_rectangle = figma_rect(
        text_template["rect"]
    )
    separator_template_rectangle = figma_rect(
        separator_template["rect"]
    )

    text_font = get_figma_font(text_template)
    line_height = max(1, text_font.get_linesize())

    text_x = max(
        0,
        text_template_rectangle.x
        - viewport_rectangle.x,
    )
    separator_x = max(
        0,
        separator_template_rectangle.x
        - viewport_rectangle.x,
    )

    text_width = min(
        text_template_rectangle.width,
        viewport_rectangle.width - text_x,
    )
    separator_width = min(
        separator_template_rectangle.width,
        viewport_rectangle.width - separator_x,
    )

    separator_gap = max(
        0,
        separator_template_rectangle.top
        - text_template_rectangle.bottom,
    )

    rows = []
    occupied_height = 0

    for message in reversed(combat_log):
        wrapped_lines = wrap_text(
            text_font,
            str(message),
            text_width,
        ) or [""]

        text_height = max(
            line_height,
            len(wrapped_lines) * line_height,
        )
        row_height = (
            text_height
            + separator_gap
            + separator_template_rectangle.height
        )

        if occupied_height + row_height > viewport_rectangle.height:
            if rows:
                break

            maximum_line_count = max(
                1,
                (
                    viewport_rectangle.height
                    - separator_gap
                    - separator_template_rectangle.height
                )
                // line_height,
            )

            visible_lines = wrapped_lines[
                :maximum_line_count
            ]

            if len(visible_lines) < len(wrapped_lines):
                visible_lines[-1] = fit_text_to_width(
                    text_font,
                    visible_lines[-1] + "...",
                    text_width,
                )

            wrapped_lines = visible_lines
            text_height = (
                len(wrapped_lines) * line_height
            )
            row_height = (
                text_height
                + separator_gap
                + separator_template_rectangle.height
            )

        rows.append(
            (
                wrapped_lines,
                get_event_color(message),
                text_height,
                row_height,
            )
        )
        occupied_height += row_height

    rows.reverse()

    content_surface = pygame.Surface(
        viewport_rectangle.size,
        pygame.SRCALPHA,
    )

    content_y = max(
        0,
        viewport_rectangle.height - occupied_height,
    )

    for (
        wrapped_lines,
        text_color,
        text_height,
        row_height,
    ) in rows:
        runtime_text_spec = {
            **text_template,
            "rect": {
                "x": text_x,
                "y": content_y,
                "width": text_width,
                "height": text_height,
            },
        }

        _draw_dynamic_figma_text(
            content_surface,
            runtime_text_spec,
            "\n".join(wrapped_lines),
            color=text_color,
        )

        separator_y = (
            content_y
            + text_height
            + separator_gap
        )

        runtime_separator_spec = {
            **separator_template,
            "rect": {
                "x": separator_x,
                "y": separator_y,
                "width": separator_width,
                "height": (
                    separator_template_rectangle.height
                ),
            },
        }

        draw_figma_rectangle(
            content_surface,
            runtime_separator_spec,
        )

        content_y += row_height

    screen.blit(
        content_surface,
        viewport_rectangle.topleft,
    )


def _draw_act_two_journal_contents(
    screen,
    combat_log,
    journal_layout,
    scroll_ratio,
):
    viewport_rectangle = figma_rect(
        journal_layout["viewport"]
    )

    row_template = journal_layout["row_template"]
    text_template = row_template["text"]
    separator_template = row_template["separator"]

    text_template_rectangle = figma_rect(
        text_template["rect"]
    )
    separator_template_rectangle = figma_rect(
        separator_template["rect"]
    )

    text_font = get_figma_font(text_template)
    line_height = max(1, text_font.get_linesize())

    separator_gap = max(
        0,
        separator_template_rectangle.top
        - text_template_rectangle.bottom,
    )

    rows = []
    content_height = 0

    for message in combat_log:
        wrapped_lines = wrap_text(
            text_font,
            message,
            text_template_rectangle.width,
        ) or [""]

        text_height = max(
            line_height,
            len(wrapped_lines) * line_height,
        )

        rows.append(
            (
                wrapped_lines,
                get_event_color(message),
                text_height,
            )
        )

        content_height += (
            text_height
            + separator_gap
            + separator_template_rectangle.height
        )

    content_surface = pygame.Surface(
        (
            viewport_rectangle.width,
            max(viewport_rectangle.height, content_height),
        ),
        pygame.SRCALPHA,
    )

    content_y = 0

    for wrapped_lines, text_color, text_height in rows:
        runtime_text_spec = {
            **text_template,
            "rect": {
                "x": 0,
                "y": content_y,
                "width": text_template_rectangle.width,
                "height": text_height,
            },
        }

        _draw_dynamic_figma_text(
            content_surface,
            runtime_text_spec,
            "\n".join(wrapped_lines),
            color=text_color,
        )

        separator_y = (
            content_y
            + text_height
            + separator_gap
        )

        runtime_separator_spec = {
            **separator_template,
            "rect": {
                "x": 0,
                "y": separator_y,
                "width": separator_template_rectangle.width,
                "height": separator_template_rectangle.height,
            },
        }

        draw_figma_rectangle(
            content_surface,
            runtime_separator_spec,
        )

        content_y = (
            separator_y
            + separator_template_rectangle.height
        )

    maximum_scroll = max(
        0,
        content_height - viewport_rectangle.height,
    )

    scroll_ratio = max(
        0.0,
        min(1.0, scroll_ratio),
    )

    scroll_offset = round(
        maximum_scroll * scroll_ratio
    )

    screen.blit(
        content_surface,
        viewport_rectangle.topleft,
        pygame.Rect(
            0,
            scroll_offset,
            viewport_rectangle.width,
            viewport_rectangle.height,
        ),
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
    journal_open,
    journal_scroll,
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

    selected_rune = RUNES_BY_ID.get(selected_rune_id)
    bloody_pact = BLOODY_PACTS_BY_ID.get(bloody_pact_id)

    active_status_effects = []

    if invisibility_turns > 0:
        active_status_effects.append(
            (
                "rogue_invisibility_icon",
                invisibility_turns,
                "Invisibility",
                (
                    "Enemies cannot see you. "
                    "Your next attack is a guaranteed critical hit."
                ),
            )
        )

    if selected_rune is not None:
        active_status_effects.append(
            (
                f"{selected_rune.id}_icon",
                None,
                selected_rune.name,
                selected_rune.description,
            )
        )

    if bloody_pact is not None:
        active_status_effects.append(
            (
                f"bloody_pact_{bloody_pact.id}",
                None,
                bloody_pact.name,
                f"{bloody_pact.reward} {bloody_pact.sacrifice}",
            )
        )

    if stoneflesh_hits > 0:
        active_status_effects.append(
            (
                "trader_scroll_of_stoneflesh",
                stoneflesh_hits,
                "Stoneflesh",
                (
                    "Reduces incoming physical damage by 60%. "
                    f"{stoneflesh_hits} protected hits remain."
                ),
            )
        )

    status_slots = tuple(
        status_layout["slots"][slot_name]
        for slot_name in sorted(status_layout["slots"])
    )

    hovered_status_effect = None

    for slot_layout, status_effect in zip(
            status_slots,
            active_status_effects,
    ):
        (
            sprite_name,
            remaining_value,
            effect_name,
            effect_description,
        ) = status_effect

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

        if (
                mouse_position is not None
                and figma_rect(
            slot_layout["hitbox"]
        ).collidepoint(mouse_position)
        ):
            hovered_status_effect = (
                sprite_name,
                effect_name,
                effect_description,
            )

    value_color = (239, 235, 225)

    down_bar_layout = hud_layout["down_bar"]

    _blit_layout_image(
        screen,
        sprites["act_two_bottom_bar"],
        down_bar_layout["frame"],
    )
    combat_log_layout = down_bar_layout["combat_log"]

    _blit_layout_image(
        screen,
        sprites["act_two_combat_log_frame"],
        combat_log_layout["frame"],
    )

    _draw_act_two_compact_combat_log_contents(
        screen,
        combat_log,
        combat_log_layout,
    )

    consumable_slots_layout = tuple(
        down_bar_layout["consumable_belt"]["slots"][slot_name]
        for slot_name in sorted(
            down_bar_layout["consumable_belt"]["slots"]
        )
    )
    healing_consumables_blocked = (
            bloody_pact_id == BLOOD_HUNGER
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

        icon_layout = consumable_slots_layout[slot_index]["icon"]

        _blit_layout_image(
            screen,
            sprites[sprite_name],
            icon_layout,
        )

        if (
                healing_consumables_blocked
                and item in _ACT_TWO_HEALING_CONSUMABLES
        ):
            icon_rectangle = figma_rect(icon_layout)

            disabled_overlay = pygame.Surface(
                icon_rectangle.size,
                pygame.SRCALPHA,
            )
            disabled_overlay.fill((10, 7, 12, 175))

            screen.blit(
                disabled_overlay,
                icon_rectangle,
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

        hovered_description = _ACT_TWO_CONSUMABLE_DESCRIPTIONS.get(
            hovered_item,
            "Consumable item.",
        )

        if (
                healing_consumables_blocked
                and hovered_item in _ACT_TWO_HEALING_CONSUMABLES
        ):
            hovered_description = (
                "Blood Hunger prevents the use of this healing item."
            )

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
            hovered_description,
        )

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

    rune_passive = (
        (
            player_class == "rogue"
            and selected_rune_id == "rune_of_the_veil"
        )
        or (
            player_class == "mage"
            and selected_rune_id == "rune_of_resonance"
        )
        or (
            player_class == "warrior"
            and selected_rune_id == "rune_of_impact"
        )
    )

    charge_layouts = (
        ()
        if rune_passive
        else tuple(
            ability_layout["charges"][charge_name]
            for charge_name in sorted(ability_layout["charges"])
        )
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
    if journal_open:
        journal_layout = hud_layout["journal_panel"]

        _blit_layout_image(
            screen,
            sprites["act_two_journal_panel"],
            journal_layout["frame"],
        )
        _draw_act_two_journal_contents(
            screen,
            combat_log,
            journal_layout,
            journal_scroll,
        )
        track_rectangle = figma_rect(
            journal_layout["scrollbar"]["track"]
        )

        thumb_layout = journal_layout["scrollbar"]["thumb"]
        thumb_rectangle = figma_rect(thumb_layout)

        thumb_travel = max(
            0,
            track_rectangle.height - thumb_rectangle.height,
        )

        runtime_thumb_layout = {
            **thumb_layout,
            "y": (
                    track_rectangle.y
                    + round(thumb_travel * journal_scroll)
            ),
        }

        _blit_layout_image(
            screen,
            sprites["act_two_journal_thumb"],
            runtime_thumb_layout,
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

    if hovered_status_effect is not None:
        (
            status_sprite_name,
            status_name,
            status_description,
        ) = hovered_status_effect

        base_info_layout = hud_layout["info"]
        base_info_rectangle = figma_rect(
            base_info_layout["rect"]
        )
        status_rectangle = figma_rect(
            status_layout["rect"]
        )

        target_left = max(
            0,
            min(
                screen.get_width() - base_info_rectangle.width,
                status_rectangle.left,
            ),
        )

        target_top = max(
            0,
            min(
                screen.get_height() - base_info_rectangle.height,
                status_rectangle.bottom + 8,
            ),
        )

        status_info_layout = _offset_layout(
            base_info_layout,
            target_left - base_info_rectangle.left,
            target_top - base_info_rectangle.top,
        )

        _draw_act_two_hover_panel(
            screen,
            sprites,
            status_info_layout,
            status_sprite_name,
            status_name,
            status_description,
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

    combat_stats_layout = stats_panel_layout["combat_stats"]

    combat_heading_spec = combat_stats_layout["heading"]

    _draw_dynamic_figma_text(
        screen,
        combat_heading_spec,
        combat_heading_spec["text"],
    )

    combat_values = {
        "damage": (
            f"{player_damage_min}-{player_damage_max}"
        ),
        "critical": (
            f"{round(player_crit_chance * 100)}%"
        ),
        "critical_power": (
            f"x{player_critical_damage_multiplier:.1f}"
        ),
        "dodge": (
            f"{round(player_dodge_chance * 100)}%"
        ),
        "magical_power": str(player_spell_power),
    }

    for row_name, value in combat_values.items():
        row_layout = combat_stats_layout["rows"][row_name]
        label_spec = row_layout["label"]

        _draw_dynamic_figma_text(
            screen,
            label_spec,
            label_spec["text"],
        )

        _draw_dynamic_figma_text(
            screen,
            row_layout["value"],
            value,
        )

    pending_points = sum(pending_attribute_upgrades.values())

    if pending_points > 0:
        confirm_layout = stats_panel_layout["confirm"]

        confirm_rectangle = figma_rect(
            confirm_layout["button"]
        )
        confirm_hitbox = figma_rect(
            confirm_layout["hitbox"]
        )

        confirm_button = sprites[
            "act_two_confirm_button"
        ]

        if confirm_button.get_size() != confirm_rectangle.size:
            confirm_button = pygame.transform.smoothscale(
                confirm_button,
                confirm_rectangle.size,
            )

        screen.blit(
            confirm_button,
            confirm_rectangle,
        )

        confirm_hovered = (
                mouse_position is not None
                and confirm_hitbox.collidepoint(
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


def get_act_two_journal_close_rectangle(hud_layout):
    return figma_rect(
        hud_layout["journal_panel"]["close_hitbox"]
    )


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


def get_act_two_confirm_button_rectangle(hud_layout):
    return figma_rect(
        hud_layout["right_bar"]
        ["stats_panel"]
        ["confirm"]
        ["hitbox"]
    )

def get_act_two_journal_viewport_rectangle(hud_layout):
    return figma_rect(
        hud_layout["journal_panel"]["viewport"]
    )


def get_act_two_journal_scrollbar_rectangles(
    hud_layout,
    scroll_ratio,
):
    scrollbar_layout = (
        hud_layout["journal_panel"]["scrollbar"]
    )

    track_rectangle = figma_rect(
        scrollbar_layout["track"]
    )

    thumb_rectangle = figma_rect(
        scrollbar_layout["thumb"]
    )

    thumb_travel = max(
        0,
        track_rectangle.height - thumb_rectangle.height,
    )

    scroll_ratio = max(
        0.0,
        min(1.0, scroll_ratio),
    )

    thumb_rectangle.y = (
        track_rectangle.y
        + round(thumb_travel * scroll_ratio)
    )

    return track_rectangle, thumb_rectangle
