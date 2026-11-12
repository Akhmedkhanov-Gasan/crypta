import pygame

from acts.act_three.input.consumables import activate_belt_slot
from acts.act_three.items.inventory import (
    get_inventory_slots,
    move_belt_item_to_inventory,
    move_inventory_item_to_belt,
    rearrange_belt,
    rearrange_inventory,
)
from acts.act_three.items.use import belt_item
from acts.act_three.presentation.hud.layout import get_act_three_hud_layout
from acts.act_three.state import ItemDragState
from presentation.figma_ui import figma_rect


DRAG_DISTANCE = 5


def _slot_at(slots, mouse_position):
    if mouse_position is None:
        return None
    return next(
        (index for index, name in enumerate(sorted(slots))
         if figma_rect(slots[name]["hitbox"]).collidepoint(mouse_position)),
        None,
    )


def _finish_drag(player, drag, mouse_position, inventory_open):
    layout = get_act_three_hud_layout()
    belt_slots = layout["down_bar"]["consumable_belt"]["slots"]
    inventory_slots = layout["right_bar"]["character_panel"]["inventory"]["slots"]
    belt_target = _slot_at(belt_slots, mouse_position)
    inventory_target = _slot_at(inventory_slots, mouse_position) if inventory_open else None
    if drag.from_belt:
        if belt_item(player, drag.slot) != drag.item:
            return
        if not drag.moving and belt_target == drag.slot:
            activate_belt_slot(player, drag.slot)
        elif drag.moving:
            if inventory_target is not None:
                move_belt_item_to_inventory(player, drag.slot, inventory_target)
            elif belt_target is not None:
                rearrange_belt(player, drag.slot, belt_target)
        return

    if not inventory_open:
        return
    items = get_inventory_slots(player)
    if not drag.moving or items[drag.slot] != drag.item:
        return
    if inventory_target is not None:
        rearrange_inventory(player, drag.slot, inventory_target)
    elif belt_target is not None:
        move_inventory_item_to_belt(player, drag.slot, belt_target)


def handle_inventory_drag(event, game_state, mouse_position, movement_available):
    player = game_state.player
    state = player.act_three
    inventory_open = game_state.sidebar_tab == "stats"
    drag = state.item_drag
    if drag is not None:
        if mouse_position is None or max(
            abs(mouse_position[0] - drag.origin[0]),
            abs(mouse_position[1] - drag.origin[1]),
        ) >= DRAG_DISTANCE:
            drag.moving = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            state.item_drag = None
            _finish_drag(player, drag, mouse_position, inventory_open)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            state.item_drag = None
        return True

    if (
        not movement_available
        or event.type != pygame.MOUSEBUTTONDOWN
        or event.button != 1
        or mouse_position is None
    ):
        return False
    layout = get_act_three_hud_layout()
    inventory = layout["right_bar"]["character_panel"]["inventory"]
    source = _slot_at(inventory["slots"], mouse_position) if inventory_open else None
    if source is not None:
        items = get_inventory_slots(player)
        if source < len(items) and items[source] is not None:
            state.item_drag = ItemDragState(source, items[source], False, mouse_position)
        return True

    belt_slots = layout["down_bar"]["consumable_belt"]["slots"]
    source = _slot_at(belt_slots, mouse_position)
    item = belt_item(player, source)
    if source is not None and item is not None:
        state.item_drag = ItemDragState(source, item, True, mouse_position)
        return True
    return False
