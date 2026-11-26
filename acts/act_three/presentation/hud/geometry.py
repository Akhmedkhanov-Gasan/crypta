from presentation.figma_ui import figma_rect
from acts.act_two.presentation.stats_tooltips import stat_row_rectangle
from acts.act_three.progression import can_queue_act_three_attribute_upgrade, get_pending_attribute_points

from acts.act_three.presentation.hud.layout import (
    get_act_three_hud_layout,
    get_player_hud_layout,
    get_layout_rect,
)


def get_character_panel_focus_rectangles(panel, belt_slots, player):
    rectangles = {
        f"inventory:{name}": figma_rect(slot["hitbox"])
        for name, slot in sorted(panel["inventory"]["slots"].items())
    }
    if not player.act_three.inventory_unlocked:
        rectangles.clear()
    rectangles.update({
        f"belt:{name}": figma_rect(slot["hitbox"])
        for name, slot in sorted(belt_slots.items())
    })
    for name, row in panel["attributes"]["rows"].items():
        rectangles[f"attribute:{name}"] = stat_row_rectangle(row)
        if can_queue_act_three_attribute_upgrade(player, name):
            rectangles[f"attribute:{name}:plus"] = figma_rect(row["plus_hitbox"])
        if player.act_three.pending_attribute_upgrades.get(name, 0) > 0:
            rectangles[f"attribute:{name}:minus"] = figma_rect(row["minus_hitbox"])
    rectangles.update({
        f"combat_stat:{name}": stat_row_rectangle(row)
        for name, row in panel["combat_stats"]["rows"].items()
    })
    rectangles["mastery:mastery"] = figma_rect(panel["mastery"]["hitbox"])
    for name in ("weapon", "armor"):
        if player.act_three.inventory_unlocked and player.act_three.blacksmith_quest.get("completed"):
            rectangles[f"equipment:{name}"] = figma_rect(panel["equipment"][name]["hitbox"])
    rectangles["passive:passive"] = figma_rect(panel["subclass_passive"]["hitbox"])
    if get_pending_attribute_points(player) > 0:
        rectangles["confirm"] = figma_rect(panel["confirm"]["hitbox"])
    return rectangles


def resolve_character_panel_focus(rectangles, focus):
    if focus in rectangles:
        return focus
    if focus is not None and focus.startswith("attribute:"):
        row_focus = ":".join(focus.split(":")[:2])
        if row_focus in rectangles:
            return row_focus
    return next(iter(rectangles))


def get_act_three_sidebar_tab_rectangles():
    layout = get_act_three_hud_layout()
    buttons = layout["right_bar"]["tabs"]["buttons"]

    return {
        name: get_layout_rect(
            layout,
            "right_bar",
            "tabs",
            "buttons",
            name,
            "hitbox",
        )
        for name in buttons
    }


def get_act_three_panel_close_rectangle(panel_name):
    layout = get_act_three_hud_layout()

    if panel_name == "journal":
        return get_layout_rect(
            layout,
            "journal_panel",
            "close_hitbox",
        )

    return get_layout_rect(
        layout,
        "right_bar",
        "character_panel",
        "close_hitbox",
    )


def get_act_three_popup_rectangle(panel_name):
    layout = get_act_three_hud_layout()

    if panel_name == "journal":
        return get_layout_rect(
            layout,
            "journal_panel",
        )

    return get_layout_rect(
        layout,
        "right_bar",
        "character_panel",
    )


def get_act_three_attribute_button_rectangles():
    layout = get_act_three_hud_layout()
    rows = layout[
        "right_bar"
    ][
        "character_panel"
    ][
        "attributes"
    ][
        "rows"
    ]

    return {
        name: {
            "minus": get_layout_rect(
                layout,
                "right_bar",
                "character_panel",
                "attributes",
                "rows",
                name,
                "minus_hitbox",
            ),
            "plus": get_layout_rect(
                layout,
                "right_bar",
                "character_panel",
                "attributes",
                "rows",
                name,
                "plus_hitbox",
            ),
        }
        for name in rows
    }


def get_act_three_character_confirm_rectangle():
    return get_layout_rect(
        get_act_three_hud_layout(),
        "right_bar",
        "character_panel",
        "confirm",
        "hitbox",
    )


def get_act_three_bottom_hud_rectangles(player=None):
    layout = get_player_hud_layout(player) if player is not None else get_act_three_hud_layout()

    return (
        get_layout_rect(
            layout,
            "top_bar",
            "frame",
        ),
        get_layout_rect(
            layout,
            "down_bar",
            "combat_log",
        ),
        get_layout_rect(
            layout,
            "down_bar",
            "belt_art",
        ),
        get_layout_rect(
            layout,
            "down_bar",
            "abilities",
        ),
        get_layout_rect(
            layout,
            "down_bar",
            "gold",
        ),
        get_layout_rect(
            layout,
            "cartography",
            "minimap",
            "frame",
        ),
    )


def get_act_three_journal_scroll_ratio(game_state):
    ratio = game_state.act_three.journal_scroll_ratio
    if ratio is None:
        maximum = max(0, len(game_state.combat_log) - 4)
        ratio = 1.0 - game_state.log_scroll_offset / maximum if maximum else 1.0
    return max(0.0, min(1.0, ratio))


def get_act_three_journal_scrollbar_rectangles(layout, ratio):
    track = get_layout_rect(layout, "journal_panel", "scrollbar", "track")
    thumb = get_layout_rect(layout, "journal_panel", "scrollbar", "thumb")
    travel = max(0, track.height - thumb.height)
    thumb.y = track.y + round(travel * max(0.0, min(1.0, ratio)))
    return track, thumb


def get_act_three_log_panel_rect():
    layout = get_act_three_hud_layout()

    return get_layout_rect(
        layout,
        "down_bar",
        "combat_log",
    )


def get_act_three_log_arrow_rectangles():
    return {}


def get_act_three_ability_slot_rectangle(slot, player=None):
    import pygame

    layout = get_player_hud_layout(player) if player is not None else get_act_three_hud_layout()
    value = layout["down_bar"]["abilities"]["slots"].get(f"ability_{slot}")
    return get_layout_rect(value, "hitbox") if value is not None else pygame.Rect(0, 0, 0, 0)
