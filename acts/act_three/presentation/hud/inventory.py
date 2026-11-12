import pygame

from acts.act_three.items.inventory import BLACK_ORE_CHUNK, get_inventory_slots
from acts.act_three.presentation.hud.panel_art import draw_panel_image
from acts.act_three.trader_catalog import TRADER_ITEMS
from presentation.figma_ui import figma_rect
from presentation.tooltips import TooltipContent


def draw_inventory(screen, player, assets, panel, mouse_position):
    inventory = panel["inventory"]
    slots = inventory["slots"]
    draw_panel_image(
        screen,
        assets,
        "inventory_baclground",
        inventory.get("background"),
    )
    stored_items = get_inventory_slots(player)
    sprites = {
        **assets.get("act_three_consumable_belt_sprites", {}),
        **assets.get("act_three_inventory_sprites", {}),
    }
    hovered_item = None
    drag = player.act_three.item_drag
    moving = drag is not None and drag.moving

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
                color = (195, 151, 88) if hovered else (113, 86, 57)
                pygame.draw.rect(screen, color, hitbox, width=2 if hovered else 1)
        if item is None:
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

        if hovered and not moving:
            hovered_item = item
            pygame.draw.rect(screen, (181, 145, 81), hitbox, width=1)

    if moving:
        return None
    if hovered_item == BLACK_ORE_CHUNK:
        return TooltipContent(
            title="Black ore",
            lines=("Crafting material.",),
            accent=(176, 139, 214),
        )
    item = TRADER_ITEMS.get(hovered_item)
    if item is not None:
        return TooltipContent(
            item.name, (item.description, "Drag to an empty belt slot."), (181, 145, 81),
        )
    return None


def draw_inventory_drag(screen, player, assets, mouse_position):
    drag = player.act_three.item_drag
    if drag is None or not drag.moving or mouse_position is None:
        return
    sprite = assets.get("act_three_inventory_sprites", {}).get(drag.item)
    if sprite is None:
        sprite = assets.get("act_three_consumable_belt_sprites", {}).get(drag.item)
    if sprite is None:
        return
    size = max(1, round(42 * assets.get("hud_render_scale", 1.0)))
    bounds = pygame.Rect(0, 0, size, size)
    bounds.center = mouse_position
    fitted = sprite.get_rect().fit(bounds)
    screen.blit(pygame.transform.smoothscale(sprite, fitted.size), fitted)
