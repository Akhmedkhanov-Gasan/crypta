import pygame

from acts.act_three.items.inventory import ORE_ITEM_NAMES, get_inventory_slots
from acts.act_three.items.special import SPECIAL_ITEM_NAMES, SPECIAL_ITEM_DESCRIPTIONS
from acts.act_three.presentation.hud.panel_art import draw_panel_image
from acts.act_three.presentation.hud.slot_highlight import draw_slot_highlight
from acts.act_three.trader_catalog import TRADER_ITEMS, TRADER_SELL_ITEMS
from acts.act_three.presentation.descriptions.items import consumable_lines
from presentation.figma_ui import figma_rect
from presentation.tooltips import TooltipContent


def draw_inventory(screen, player, assets, panel, mouse_position, focused_slot=None):
    inventory = panel["inventory"]
    slots = inventory["slots"]
    if not player.act_three.inventory_unlocked:
        rectangle = inventory.get("seal") or inventory["rect"]
        draw_panel_image(screen, assets, "inventory_seal", rectangle)
        if mouse_position is not None and figma_rect(rectangle).collidepoint(mouse_position):
            return TooltipContent(
                "No pack", ("Find the trader and complete his delivery.",), (181, 145, 81),
            )
        return None
    draw_panel_image(
        screen,
        assets,
        "inventory_baclground",
        inventory.get("background"),
    )
    for decoration in inventory.get("decorations", ()):
        draw_panel_image(screen, assets, "inventory_decoration", decoration)

    stored_items = get_inventory_slots(player)
    sprites = {
        **assets.get("act_three_consumable_belt_sprites", {}),
        **assets.get("act_three_sell_item_sprites", {}),
        **assets.get("act_three_inventory_sprites", {}),
        **assets.get("act_three_special_item_sprites", {}),
    }
    hovered_item = None
    drag = player.act_three.item_drag
    moving = drag is not None and drag.moving
    scale = assets.get("hud_render_scale", 1.0)

    for index, name in enumerate(sorted(slots)):
        slot = slots[name]
        draw_panel_image(
            screen,
            assets,
            "slot_baclground",
            slot.get("background"),
        )
        item = stored_items[index] if index < len(stored_items) else None
        hitbox = figma_rect(slot["hitbox"])
        hovered = mouse_position is not None and hitbox.collidepoint(mouse_position)
        if moving and index < len(stored_items) and (not drag.from_belt or item is None):
            if hovered or (drag.from_belt and item is None):
                draw_slot_highlight(screen, hitbox, scale=scale, focused=hovered)
        if item is None:
            if (hovered or name == focused_slot) and not moving:
                draw_slot_highlight(screen, hitbox, scale=scale, focused=name == focused_slot)
            continue

        rectangle = figma_rect(slot["icon"])
        sprite = sprites.get(item)
        is_drag_source = moving and not drag.from_belt and drag.slot == index
        if sprite is not None and not is_drag_source:
            fitted = sprite.get_rect().fit(rectangle)
            screen.blit(
                pygame.transform.smoothscale(sprite, fitted.size),
                fitted,
            )

        if (hovered or name == focused_slot) and not moving:
            hovered_item = item
            draw_slot_highlight(screen, hitbox, scale=scale, focused=name == focused_slot)

    if moving:
        return None
    if hovered_item in ORE_ITEM_NAMES:
        return TooltipContent(
            title=ORE_ITEM_NAMES[hovered_item],
            lines=("Crafting material.", "Shift: drop in front."),
            accent=(176, 139, 214),
        )
    if hovered_item in SPECIAL_ITEM_NAMES:
        return TooltipContent(
            SPECIAL_ITEM_NAMES[hovered_item],
            (SPECIAL_ITEM_DESCRIPTIONS[hovered_item], "Shift: drop in front."),
            (181, 145, 81),
        )
    item = TRADER_ITEMS.get(hovered_item)
    if item is not None:
        return TooltipContent(
            item.name,
            (*consumable_lines(player, hovered_item), "Press 1-6 or drag to the belt.", "Shift: drop in front."),
            (181, 145, 81),
        )
    if hovered_item in TRADER_SELL_ITEMS:
        return TooltipContent(
            TRADER_SELL_ITEMS[hovered_item],
            ("Sell to a trader.", "Shift: drop in front."),
            (181, 145, 81),
        )
    return None


def draw_inventory_drag(screen, player, assets, mouse_position):
    drag = player.act_three.item_drag
    if drag is None or not drag.moving or mouse_position is None:
        return
    sprite = assets.get("act_three_inventory_sprites", {}).get(drag.item)
    if sprite is None:
        sprite = assets.get("act_three_special_item_sprites", {}).get(drag.item)
    if sprite is None:
        sprite = assets.get("act_three_sell_item_sprites", {}).get(drag.item)
    if sprite is None:
        sprite = assets.get("act_three_consumable_belt_sprites", {}).get(drag.item)
    if sprite is None:
        return
    size = max(1, round(42 * assets.get("hud_render_scale", 1.0)))
    bounds = pygame.Rect(0, 0, size, size)
    bounds.center = mouse_position
    fitted = sprite.get_rect().fit(bounds)
    screen.blit(pygame.transform.smoothscale(sprite, fitted.size), fitted)
