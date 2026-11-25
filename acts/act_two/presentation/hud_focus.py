from acts.act_two.presentation.hud import get_act_two_belt_slot_rectangles
from acts.act_two.presentation.stats_tooltips import stat_row_rectangle
from presentation.figma_ui import figma_rect
from settings import MAX_ATTRIBUTE_RANK


def character_panel_rectangles(layout, player):
    panel = layout["right_bar"]["stats_panel"]
    rectangles = {}
    pending = player.act_two.pending_attribute_upgrades
    available = player.attribute_points - sum(pending.values())
    for name, row in panel["attributes"]["rows"].items():
        rectangles[f"attribute:{name}"] = stat_row_rectangle(row)
        if available > 0 and player.attribute_ranks[name] + pending.get(name, 0) < MAX_ATTRIBUTE_RANK:
            rectangles[f"attribute:{name}:plus"] = figma_rect(row["plus_hitbox"])
        if pending.get(name, 0) > 0:
            rectangles[f"attribute:{name}:minus"] = figma_rect(row["minus_hitbox"])
    for name, row in panel["combat_stats"]["rows"].items():
        rectangles[f"combat_stat:{name}"] = stat_row_rectangle(row)
    for index, rectangle in enumerate(get_act_two_belt_slot_rectangles(layout)):
        rectangles[f"belt:{index}"] = rectangle
    if any(pending.values()):
        rectangles["confirm"] = figma_rect(panel["confirm"]["hitbox"])
    return rectangles


def resolve_panel_focus(rectangles, focus):
    if focus in rectangles:
        return focus
    if focus and focus.startswith("attribute:"):
        row = ":".join(focus.split(":")[:2])
        if row in rectangles:
            return row
    return next(iter(rectangles))


def keyboard_focus_rectangle(layout, player):
    if not player.act_two.interface_keyboard_focus:
        return None
    rectangles = character_panel_rectangles(layout, player)
    return rectangles[resolve_panel_focus(rectangles, player.act_two.interface_focus)]
