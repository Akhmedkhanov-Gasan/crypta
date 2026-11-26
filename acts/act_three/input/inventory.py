import pygame

from acts.act_three.input.consumables import activate_belt_slot
from acts.act_three.items.discard import discard_item
from acts.act_three.items.inventory import (
    assign_inventory_item_to_belt,
    get_inventory_slots,
    move_belt_item_to_inventory,
    rearrange_belt,
    rearrange_inventory,
)
from acts.act_three.items.use import belt_item
from acts.act_three.presentation.hit_testing import get_act_three_cell_from_position
from acts.act_three.presentation.hud.geometry import (
    get_act_three_bottom_hud_rectangles,
    get_act_three_popup_rectangle,
    get_act_three_sidebar_tab_rectangles,
)
from acts.act_three.presentation.hud.layout import get_player_hud_layout
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


def _drop_dragged_item(game_state, drag, mouse_position):
    target = get_act_three_cell_from_position(game_state, mouse_position)
    if target is None:
        return

    hud_rectangles = (
        *get_act_three_bottom_hud_rectangles(game_state.player),
        *get_act_three_sidebar_tab_rectangles().values(),
    )
    if game_state.sidebar_tab in ("stats", "journal"):
        hud_rectangles += (get_act_three_popup_rectangle(game_state.sidebar_tab),)
    if any(rectangle.collidepoint(mouse_position) for rectangle in hud_rectangles):
        return

    discard_item(
        game_state, drag.slot, pygame.time.get_ticks(),
        from_belt=drag.from_belt, target=target,
    )


def _finish_drag(game_state, drag, mouse_position, inventory_open):
    player = game_state.player
    layout = get_player_hud_layout(player)
    belt_slots = layout["down_bar"]["consumable_belt"]["slots"]
    inventory_slots = layout["right_bar"]["character_panel"]["inventory"]["slots"]
    belt_target = _slot_at(belt_slots, mouse_position)
    inventory_target = _slot_at(inventory_slots, mouse_position) if inventory_open else None
    if drag.from_belt:
        if belt_item(player, drag.slot) != drag.item:
            return
        if not drag.moving and belt_target == drag.slot and not inventory_open:
            activate_belt_slot(player, drag.slot)
        elif drag.moving:
            if inventory_target is not None:
                move_belt_item_to_inventory(player, drag.slot, inventory_target)
            elif belt_target is not None:
                rearrange_belt(player, drag.slot, belt_target)
            else:
                _drop_dragged_item(game_state, drag, mouse_position)
        return

    if not inventory_open:
        return
    items = get_inventory_slots(player)
    if not drag.moving or items[drag.slot] != drag.item:
        return
    if inventory_target is not None:
        rearrange_inventory(player, drag.slot, inventory_target)
    elif belt_target is not None:
        assign_inventory_item_to_belt(game_state, drag.slot, belt_target)
    else:
        _drop_dragged_item(game_state, drag, mouse_position)


def handle_inventory_drag(event, game_state, mouse_position, movement_available):
    player = game_state.player
    state = player.act_three
    inventory_open = game_state.sidebar_tab == "stats" and player.act_three.inventory_unlocked
    drag = state.item_drag
    if drag is not None:
        if mouse_position is None or max(
            abs(mouse_position[0] - drag.origin[0]),
            abs(mouse_position[1] - drag.origin[1]),
        ) >= DRAG_DISTANCE:
            drag.moving = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            state.item_drag = None
            _finish_drag(game_state, drag, mouse_position, inventory_open)
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
    layout = get_player_hud_layout(player)
    inventory = layout["right_bar"]["character_panel"]["inventory"]
    source = _slot_at(inventory["slots"], mouse_position) if inventory_open else None
    if source is not None:
        game_state.act_three.character_panel_focus = f"inventory:{sorted(inventory['slots'])[source]}"
        items = get_inventory_slots(player)
        if source < len(items) and items[source] is not None:
            state.item_drag = ItemDragState(source, items[source], False, mouse_position)
        return True

    belt_slots = layout["down_bar"]["consumable_belt"]["slots"]
    source = _slot_at(belt_slots, mouse_position)
    item = belt_item(player, source)
    if source is not None and inventory_open:
        state.character_panel_focus = f"belt:{sorted(belt_slots)[source]}"
    if source is not None and item is not None:
        state.item_drag = ItemDragState(source, item, True, mouse_position)
        return True
    return source is not None and inventory_open
