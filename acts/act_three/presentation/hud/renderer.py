import math

import pygame

from acts.act_three.presentation.hud.content import (
    ABILITY_SLOT_ORDER,
)
from acts.act_three.presentation.hud.ability_tooltips import (
    ability_tooltip_content,
    draw_ability_slot_highlight,
    hovered_ability_slot,
)
from acts.act_three.abilities import (
    get_ability_definition,
    get_ability_slot_charge,
    get_mastery_charge_rate,
    get_passive_definition,
    is_ability_slot_unlocked,
)
from acts.act_two.abilities import (
    ability_charge_required,
)
from acts.act_two.bloody_altar import (
    healing_consumables_are_blocked,
)
from acts.act_two.consumables import (
    get_act_two_consumable_slots,
)
from acts.act_two.presentation.hud_tooltips import (
    consumable_tooltip_content,
)
from game.rune_catalog import RUNES_BY_ID
from acts.act_three.presentation.hud.layout import (
    get_layout_rect,
)
from acts.act_three.presentation.hud.tooltips import (
    character_panel_tooltip_content,
    draw_character_panel_highlight,
    get_character_panel_hover,
)
from game.progression import experience_required_for_level
from presentation.hud import get_event_color, wrap_text
from presentation.tooltips import draw_tooltip
from presentation.figma_ui import (
    draw_figma_rectangle,
    draw_figma_text,
    figma_rect,
    get_figma_font as get_layout_font,
)

_TEXT_COLOR = (174, 154, 143)
_EMPTY_BAR_COLOR = (13, 10, 11)
_XP_COLOR = (112, 63, 42)
_ACTIVE_CHARGE_COLOR = (161, 28, 28)
_INACTIVE_CHARGE_COLOR = (77, 73, 73)
_FLAME_SEQUENCE = (0, 1, 2, 1, 3, 2)
_FLAME_FRAME_MS = 220
_CANDLE_GLOW_CACHE = {}
_HEALING_CONSUMABLES = frozenset({
    "potion",
    "healing_scroll",
})

_SUBCLASS_NAMES = {
    "assassin": "ASSASSIN",
    "archer": "ARCHER",
    "berserker": "BERSERKER",
    "paladin": "PALADIN",
    "summoner": "SUMMONER",
    "warlock": "WARLOCK",
}


def _ratio(value, maximum):
    if maximum <= 0:
        return 0.0

    return max(
        0.0,
        min(1.0, value / maximum),
    )


def _blit_asset(screen, assets, name, rectangle):
    image = assets.get(name)

    if image is not None:
        screen.blit(image, rectangle)


def _get_candle_glow(radius, alpha):
    cache_key = (radius, alpha)
    cached = _CANDLE_GLOW_CACHE.get(cache_key)

    if cached is not None:
        return cached

    size = radius * 2
    glow = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )

    pygame.draw.circle(
        glow,
        (255, 109, 28, alpha // 4),
        (radius, radius),
        radius,
    )
    pygame.draw.circle(
        glow,
        (255, 143, 42, alpha // 2),
        (radius, radius),
        max(1, radius // 2),
    )
    pygame.draw.circle(
        glow,
        (255, 196, 89, alpha),
        (radius, radius),
        max(1, radius // 5),
    )

    glow = pygame.transform.gaussian_blur(
        glow,
        max(1, radius // 3),
    )

    _CANDLE_GLOW_CACHE[cache_key] = glow
    return glow


def _draw_candle_flame(
    screen,
    frames,
    rectangle,
    current_time,
    phase_offset,
    glow_radius,
):
    sequence_position = (
        current_time // _FLAME_FRAME_MS
        + phase_offset
    ) % len(_FLAME_SEQUENCE)

    frame_index = _FLAME_SEQUENCE[
        sequence_position
    ]

    pulse = (
        math.sin(
            current_time * 0.011
            + phase_offset * 1.7
        )
        + 1.0
    ) / 2.0

    radius = glow_radius + round(pulse * 3)
    alpha = 18 + round(pulse * 10)
    glow = _get_candle_glow(
        radius,
        alpha,
    )

    glow_center = (
        rectangle.centerx,
        rectangle.centery + 2,
    )

    screen.blit(
        glow,
        glow.get_rect(center=glow_center),
    )
    screen.blit(
        frames[frame_index],
        rectangle,
    )


def _draw_candles(
    screen,
    assets,
    layout,
    current_time,
):
    flame_assets = assets["hud_candle_flames"]

    small_rectangle = get_layout_rect(
        layout,
        "top_bar",
        "candles",
        "small",
    )
    large_rectangle = get_layout_rect(
        layout,
        "top_bar",
        "candles",
        "large",
    )

    _draw_candle_flame(
        screen,
        flame_assets["small"],
        small_rectangle,
        current_time,
        0,
        20,
    )
    _draw_candle_flame(
        screen,
        flame_assets["large"],
        large_rectangle,
        current_time,
        3,
        27,
    )


def _draw_left_text(
    screen,
    font,
    text,
    rectangle,
    color=_TEXT_COLOR,
):
    surface = font.render(str(text), True, color)
    screen.blit(
        surface,
        surface.get_rect(
            midleft=rectangle.midleft,
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
            "a": (
                color[3]
                if len(color) > 3
                else 255
            ),
        }

    draw_figma_text(
        screen,
        runtime_spec,
    )

def _draw_fill(
    screen,
    rectangle,
    ratio,
    color,
    image=None,
):
    pygame.draw.rect(
        screen,
        _EMPTY_BAR_COLOR,
        rectangle,
    )

    width = round(
        rectangle.width
        * max(0.0, min(1.0, ratio))
    )

    if width <= 0:
        return

    if image is None:
        pygame.draw.rect(
            screen,
            color,
            (
                rectangle.x,
                rectangle.y,
                width,
                rectangle.height,
            ),
        )
        return

    screen.blit(
        image,
        rectangle.topleft,
        pygame.Rect(
            0,
            0,
            width,
            rectangle.height,
        ),
    )


def _draw_top_bar(
    screen,
    game_state,
    fonts,
    assets,
    layout,
    current_time,
):
    player = game_state.player

    portrait_back = get_layout_rect(
        layout,
        "top_bar",
        "portrait_back",
    )
    portrait_rect = get_layout_rect(
        layout,
        "top_bar",
        "portrait",
    )
    hp_rect = get_layout_rect(
        layout,
        "top_bar",
        "hp_fill",
    )
    xp_rect = get_layout_rect(
        layout,
        "top_bar",
        "xp_fill",
    )

    pygame.draw.rect(
        screen,
        (0, 0, 0),
        portrait_back,
    )

    portrait = assets["hud_portraits"].get(
        player.subclass
    )

    if portrait is not None:
        screen.blit(
            portrait,
            portrait_rect,
        )

    experience_required = experience_required_for_level(
        player.level
    )

    _draw_fill(
        screen,
        hp_rect,
        _ratio(
            player.health,
            player.max_health,
        ),
        _ACTIVE_CHARGE_COLOR,
        assets.get("hud_hp_fill"),
    )

    _draw_fill(
        screen,
        xp_rect,
        _ratio(
            player.experience,
            experience_required,
        ),
        _XP_COLOR,
        assets.get("hud_xp_fill"),
    )

    _blit_asset(
        screen,
        assets,
        "hud_top_bar_frame",
        get_layout_rect(
            layout,
            "top_bar",
            "frame",
        ),
    )

    _draw_candles(
        screen,
        assets,
        layout,
        current_time,
    )

    hp_text = layout["top_bar"]["hp_text"]
    xp_text = layout["top_bar"]["xp_text"]
    level_text = layout["top_bar"]["level"]

    _draw_dynamic_figma_text(
        screen,
        hp_text,
        f"{player.health}/{player.max_health}",
    )

    _draw_dynamic_figma_text(
        screen,
        xp_text,
        f"{player.experience}/{experience_required}",
    )

    _draw_dynamic_figma_text(
        screen,
        level_text,
        player.level,
    )


def _draw_combat_log(
    screen,
    game_state,
    fonts,
    assets,
    layout,
):
    combat_log = layout["down_bar"]["combat_log"]

    _blit_asset(
        screen,
        assets,
        "hud_combat_log_frame",
        get_layout_rect(
            layout,
            "down_bar",
            "combat_log",
            "frame",
        ),
    )

    viewport = get_layout_rect(
        layout,
        "down_bar",
        "combat_log",
        "viewport",
    )
    row_text = combat_log["row_template"]["text"]
    row_font = get_layout_font(row_text)
    lines = []

    for message in game_state.combat_log[-5:]:
        wrapped = wrap_text(
            row_font,
            message,
            viewport.width,
        )

        lines.extend(
            (line, get_event_color(message))
            for line in wrapped
        )

    row_height = max(
        17,
        combat_log["row_template"]["rect"]["height"],
    )

    for index, (line, color) in enumerate(lines[-3:]):
        rectangle = pygame.Rect(
            viewport.x,
            viewport.y + index * row_height,
            viewport.width,
            row_height,
        )

        _draw_left_text(
            screen,
            row_font,
            line,
            rectangle,
            color,
        )


def _draw_consumables(
    screen,
    player,
    fonts,
    assets,
    layout,
    mouse_position,
):
    _blit_asset(
        screen,
        assets,
        "hud_consumable_belt_frame",
        get_layout_rect(
            layout,
            "down_bar",
            "consumable_belt_frame",
        ),
    )

    slots = layout[
        "down_bar"
    ]["consumable_belt"]["slots"]

    stored_items = get_act_two_consumable_slots(
        player
    )
    belt_sprites = assets.get(
        "act_three_consumable_belt_sprites",
        {},
    )
    healing_blocked = (
        healing_consumables_are_blocked(player)
    )
    hovered_item = None

    for index, slot_name in enumerate(
        sorted(slots)
    ):
        slot = slots[slot_name]
        hitbox = figma_rect(
            slot["hitbox"]
        )

        key_surface = fonts["sidebar_hud"].render(
            str(index + 1),
            True,
            _TEXT_COLOR,
        )
        screen.blit(
            key_surface,
            (
                hitbox.x + 1,
                hitbox.y - key_surface.get_height(),
            ),
        )

        item = (
            stored_items[index]
            if index < len(stored_items)
            else None
        )

        if item is None:
            continue

        is_hovered = (
            mouse_position is not None
            and hitbox.collidepoint(
                mouse_position
            )
        )

        if is_hovered:
            hovered_item = item

            pygame.draw.rect(
                screen,
                (181, 145, 81),
                hitbox,
                width=1,
                border_radius=4,
            )

        icon = belt_sprites.get(item)

        if icon is None:
            continue

        icon_rectangle = figma_rect(
            slot["icon"]
        )
        displayed_icon = pygame.transform.smoothscale(
            icon,
            icon_rectangle.size,
        )

        screen.blit(
            displayed_icon,
            icon_rectangle,
        )

        if (
            healing_blocked
            and item in _HEALING_CONSUMABLES
        ):
            disabled_overlay = pygame.Surface(
                icon_rectangle.size,
                pygame.SRCALPHA,
            )
            disabled_overlay.fill(
                (10, 7, 12, 175)
            )

            screen.blit(
                disabled_overlay,
                icon_rectangle,
            )

    if hovered_item is None:
        return None

    return consumable_tooltip_content(
        hovered_item,
        (
            healing_blocked
            and hovered_item
            in _HEALING_CONSUMABLES
        ),
    )


def _draw_ability_charge_mask(
    screen,
    charge_level,
    ratio,
):
    remaining_ratio = 1.0 - max(
        0.0,
        min(1.0, ratio),
    )

    if remaining_ratio <= 0.0:
        return

    source_rectangle = charge_level["rect"]
    visible_height = round(
        source_rectangle["height"]
        * remaining_ratio
    )

    if visible_height <= 0:
        return

    runtime_charge_level = {
        **charge_level,
        "rect": {
            **source_rectangle,
            "height": visible_height,
        },
    }

    draw_figma_rectangle(
        screen,
        runtime_charge_level,
    )


def _get_ability_icon_asset(
    player,
    ability,
):
    if not ability.inherited:
        return ability.icon_asset

    selected_rune = RUNES_BY_ID.get(
        player.selected_rune_id
    )

    if selected_rune is None:
        return ability.icon_asset

    return f"act_three_{selected_rune.id}"


def _get_ability_charge_ratio(
    player,
    slot,
    ability,
):
    if slot == "e":
        if player.selected_rune_id == "rune_of_the_veil":
            return 1.0

        return _ratio(
            player.ability_kill_charge,
            ability_charge_required(player),
        )

    return _ratio(
        get_ability_slot_charge(
            player,
            slot,
        ),
        ability.charge_required,
    )


def _draw_locked_ability(
    screen,
    assets,
    slot,
):
    _draw_ability_charge_mask(
        screen,
        slot["charge_level"],
        0.0,
    )

    chains_layout = slot.get("chains")
    chains_image = assets.get(
        "hud_ability_chains"
    )

    if (
        chains_layout is None
        or chains_image is None
    ):
        return

    chains_rectangle = figma_rect(
        chains_layout
    )

    screen.blit(
        pygame.transform.smoothscale(
            chains_image,
            chains_rectangle.size,
        ),
        chains_rectangle,
    )


def _draw_abilities(
    screen,
    player,
    assets,
    layout,
    mouse_position,
):
    from acts.act_three.presentation.sidebar import (
        _SUBCLASS_PRESENTATION,
    )

    _, accent_color = _SUBCLASS_PRESENTATION.get(
        player.subclass,
        ("UNBOUND", _ACTIVE_CHARGE_COLOR),
    )

    slots = layout["down_bar"]["abilities"]["slots"]
    hovered_slot = hovered_ability_slot(
        slots,
        mouse_position,
    )

    for slot_name in ABILITY_SLOT_ORDER:
        slot_key = slot_name.removeprefix(
            "ability_"
        )
        slot = slots.get(slot_name)

        if slot is None:
            continue

        ability = get_ability_definition(
            player.subclass,
            slot_key,
        )

        if ability is None:
            continue

        unlocked = is_ability_slot_unlocked(
            player,
            slot_key,
        )

        if slot_key == hovered_slot:
            draw_ability_slot_highlight(
                screen,
                slot,
                locked=not unlocked,
            )

        icon_rectangle = figma_rect(
            slot["icon"]
        )
        icon_asset = _get_ability_icon_asset(
            player,
            ability,
        )
        icon = assets.get(icon_asset)

        if icon is not None:
            screen.blit(
                pygame.transform.smoothscale(
                    icon,
                    icon_rectangle.size,
                ),
                icon_rectangle,
            )

        if not unlocked:
            _draw_locked_ability(
                screen,
                assets,
                slot,
            )
            continue

        charge_ratio = _get_ability_charge_ratio(
            player,
            slot_key,
            ability,
        )

        _draw_ability_charge_mask(
            screen,
            slot["charge_level"],
            charge_ratio,
        )

        if charge_ratio >= 1.0:
            pygame.draw.rect(
                screen,
                accent_color,
                icon_rectangle.inflate(2, 2),
                width=1,
                border_radius=6,
            )
    return ability_tooltip_content(
        player,
        hovered_slot,
    )


def _draw_gold(
    screen,
    player,
    fonts,
    assets,
    layout,
):
    _blit_asset(
        screen,
        assets,
        "hud_gold_icon",
        get_layout_rect(
            layout,
            "down_bar",
            "gold",
            "icon",
        ),
    )

    value_text = layout["down_bar"]["gold"]["value"]

    _draw_dynamic_figma_text(
        screen,
        value_text,
        player.gold_count,
    )


def _draw_tabs(
    screen,
    game_state,
    assets,
    layout,
    mouse_position,
):
    _blit_asset(
        screen,
        assets,
        "hud_tabs_frame",
        get_layout_rect(
            layout,
            "right_bar",
            "tabs",
            "frame",
        ),
    )

    active_tab = getattr(
        game_state,
        "sidebar_tab",
        "closed",
    )
    buttons = layout["right_bar"]["tabs"]["buttons"]

    for button_name, button_layout in buttons.items():
        button_rectangle = figma_rect(
            button_layout["hitbox"]
        )

        is_hovered = (
            mouse_position is not None
            and button_rectangle.collidepoint(
                mouse_position
            )
        )
        is_selected = button_name == active_tab

        if not (is_hovered or is_selected):
            continue

        draw_figma_rectangle(
            screen,
            button_layout["highlight"],
        )


def _draw_rank_track(
    screen,
    assets,
    track,
    current_rank,
):
    current_rank = max(
        0,
        min(5, int(current_rank)),
    )
    level_image = assets.get(
        "hud_rank_level"
    )

    if level_image is None:
        return

    for level_index, level_name in enumerate(
        sorted(track["levels"]),
        start=1,
    ):
        if level_index > current_rank:
            continue

        rectangle = figma_rect(
            track["levels"][level_name]
        )

        screen.blit(
            pygame.transform.smoothscale(
                level_image,
                rectangle.size,
            ),
            rectangle,
        )


def _draw_character_panel(
    screen,
    game_state,
    fonts,
    assets,
    layout,
    mouse_position,
):
    from acts.act_three.presentation.sidebar import (
        _damage_value,
    )

    player = game_state.player
    panel = layout["right_bar"]["character_panel"]
    hovered_item = get_character_panel_hover(
        panel,
        mouse_position,
    )
    _blit_asset(
        screen,
        assets,
        "hud_character_panel_frame",
        get_layout_rect(
            layout,
            "right_bar",
            "character_panel",
            "frame",
        ),
    )
    _blit_asset(
        screen,
        assets,
        "hud_character_panel_button",
        get_layout_rect(
            layout,
            "right_bar",
            "character_panel",
            "confirm",
            "button",
        ),
    )
    draw_character_panel_highlight(
        screen,
        panel,
        hovered_item,
    )
    class_name_text = panel["class_name"]
    attribute_points = panel["attribute_points"]

    _draw_dynamic_figma_text(
        screen,
        class_name_text,
        _SUBCLASS_NAMES.get(
            player.subclass,
            "UNBOUND",
        ),
    )

    draw_figma_text(
        screen,
        attribute_points["label"],
    )

    _draw_dynamic_figma_text(
        screen,
        attribute_points["value"],
        player.attribute_points,
    )

    ranks = player.attribute_ranks

    for name, row in panel["attributes"]["rows"].items():
        draw_figma_text(
            screen,
            row["label"],
        )

        _draw_dynamic_figma_text(
            screen,
            row["value"],
            ranks.get(name, 0),
        )

    equipment = panel["equipment"]

    draw_figma_text(
        screen,
        equipment["heading"]["label"],
    )

    for track_name in ("weapon", "armor"):
        track_label = equipment[
            track_name
        ].get("label")

        if track_label is not None:
            draw_figma_text(
                screen,
                track_label,
            )

    mastery_rank = getattr(
        player,
        "mastery_rank",
        0,
    )
    weapon_rank = getattr(
        player,
        "weapon_rank",
        0,
    )
    armor_rank = getattr(
        player,
        "armor_rank",
        0,
    )

    _draw_rank_track(
        screen,
        assets,
        panel["mastery"],
        mastery_rank,
    )
    _draw_rank_track(
        screen,
        assets,
        equipment["weapon"],
        weapon_rank,
    )
    _draw_rank_track(
        screen,
        assets,
        equipment["armor"],
        armor_rank,
    )

    armor_value = getattr(
        player,
        "armor",
        0,
    )
    charge_rate = round(
        get_mastery_charge_rate(player) * 100
    )

    combat_values = {
        "damage": _damage_value(player),
        "armor": armor_value,
        "critical_chance": (
            f"{round(player.crit_chance * 100)}%"
        ),
        "critical_damage": (
            f"x{player.critical_damage_multiplier:.1f}"
        ),
        "dodge_chance": (
            f"{round(player.dodge_chance * 100)}%"
        ),
        "charge_rate": f"{charge_rate}%",
    }

    for name, row in panel["combat_stats"]["rows"].items():
        draw_figma_text(
            screen,
            row["label"],
        )

        _draw_dynamic_figma_text(
            screen,
            row["value"],
            combat_values.get(name, 0),
        )

    passive_layout = panel["subclass_passive"]
    passive_definition = get_passive_definition(
        player.subclass
    )

    if passive_definition is not None:
        passive_icon = assets.get(
            passive_definition.icon_asset
        )
        passive_icon_rectangle = figma_rect(
            passive_layout["icon"]
        )

        if passive_icon is not None:
            screen.blit(
                pygame.transform.smoothscale(
                    passive_icon,
                    passive_icon_rectangle.size,
                ),
                passive_icon_rectangle,
            )

        _draw_dynamic_figma_text(
            screen,
            passive_layout["name"],
            passive_definition.name,
        )

        _draw_dynamic_figma_text(
            screen,
            passive_layout["value"],
            passive_definition.description,
        )

    tooltip_content = character_panel_tooltip_content(
        hovered_item,
        player,
        combat_values,
    )

    if tooltip_content is not None:
        draw_tooltip(
            screen,
            tooltip_content,
            mouse_position,
        )


def _draw_journal_panel(
    screen,
    game_state,
    fonts,
    assets,
    layout,
):
    journal = layout["journal_panel"]

    _blit_asset(
        screen,
        assets,
        "hud_journal_panel_frame",
        get_layout_rect(
            layout,
            "journal_panel",
            "frame",
        ),
    )

    viewport_rectangle = figma_rect(
        journal["viewport"]
    )

    row_template = journal["row_template"]
    text_template = row_template["text"]
    separator_template = row_template["separator"]

    text_template_rectangle = figma_rect(
        text_template["rect"]
    )
    separator_template_rectangle = figma_rect(
        separator_template["rect"]
    )

    text_font = get_layout_font(
        text_template
    )
    line_height = max(
        1,
        text_font.get_linesize(),
    )

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
    content_height = 0

    for message in game_state.combat_log:
        wrapped_lines = wrap_text(
            text_font,
            str(message),
            text_width,
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
            max(
                viewport_rectangle.height,
                content_height,
            ),
        ),
        pygame.SRCALPHA,
    )

    content_y = 0

    for wrapped_lines, text_color, text_height in rows:
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
            text_color,
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

        content_y = (
            separator_y
            + separator_template_rectangle.height
        )

    maximum_scroll = max(
        0,
        content_height - viewport_rectangle.height,
    )

    maximum_log_offset = max(
        0,
        len(game_state.combat_log) - 4,
    )

    if maximum_log_offset == 0:
        scroll_ratio = 1.0
    else:
        scroll_ratio = 1.0 - (
            game_state.log_scroll_offset
            / maximum_log_offset
        )

    scroll_ratio = max(
        0.0,
        min(1.0, scroll_ratio),
    )

    content_scroll = round(
        maximum_scroll * scroll_ratio
    )

    screen.blit(
        content_surface,
        viewport_rectangle.topleft,
        pygame.Rect(
            0,
            content_scroll,
            viewport_rectangle.width,
            viewport_rectangle.height,
        ),
    )

    track_rectangle = get_layout_rect(
        layout,
        "journal_panel",
        "scrollbar",
        "track",
    )
    thumb_rectangle = get_layout_rect(
        layout,
        "journal_panel",
        "scrollbar",
        "thumb",
    )

    thumb_travel = max(
        0,
        track_rectangle.height
        - thumb_rectangle.height,
    )

    thumb_rectangle.y = (
        track_rectangle.y
        + round(thumb_travel * scroll_ratio)
    )

    _blit_asset(
        screen,
        assets,
        "hud_journal_scrollbar_thumb",
        thumb_rectangle,
    )


def draw_act_three_hud(
    screen,
    game_state,
    fonts,
    assets,
    current_time,
    mouse_position=None,
):
    layout = assets["act_three_hud_layout"]
    player = game_state.player

    _draw_top_bar(
        screen,
        game_state,
        fonts,
        assets,
        layout,
        current_time,
    )
    _draw_combat_log(
        screen,
        game_state,
        fonts,
        assets,
        layout,
    )
    hud_tooltip = _draw_consumables(
        screen,
        player,
        fonts,
        assets,
        layout,
        mouse_position,
    )

    ability_tooltip = _draw_abilities(
        screen,
        player,
        assets,
        layout,
        mouse_position,
    )

    if ability_tooltip is not None:
        hud_tooltip = ability_tooltip
    _draw_gold(
        screen,
        player,
        fonts,
        assets,
        layout,
    )

    camera_rectangle = get_layout_rect(
        layout,
        "down_bar",
        "camera",
        "frame",
    )

    pygame.draw.rect(
        screen,
        (0, 0, 0),
        camera_rectangle,
    )

    _blit_asset(
        screen,
        assets,
        "hud_camera_frame",
        camera_rectangle,
    )

    _draw_tabs(
        screen,
        game_state,
        assets,
        layout,
        mouse_position,
    )

    active_tab = getattr(
        game_state,
        "sidebar_tab",
        "closed",
    )

    if active_tab == "stats":
        _draw_character_panel(
            screen,
            game_state,
            fonts,
            assets,
            layout,
            mouse_position,
        )
    elif active_tab == "journal":
        _draw_journal_panel(
            screen,
            game_state,
            fonts,
            assets,
            layout,
        )
    if hud_tooltip is not None:
        draw_tooltip(
            screen,
            hud_tooltip,
            mouse_position,
        )
