import pygame

from acts.act_three.items.inventory import BLACK_ORE_CHUNK, get_inventory_slots
from acts.act_three.presentation.hud.panel_art import draw_panel_image
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

    for index, name in enumerate(sorted(slots)):
        slot = slots[name]
        draw_panel_image(
            screen,
            assets,
            "slot_baclground",
            slot.get("background"),
        )
        item = stored_items[index] if index < len(stored_items) else None
        if item is None:
            continue

        rectangle = figma_rect(slot["icon"])
        sprite = sprites.get(item)
        if sprite is not None:
            screen.blit(
                pygame.transform.smoothscale(sprite, rectangle.size),
                rectangle,
            )

        hitbox = figma_rect(slot["hitbox"])
        if mouse_position is not None and hitbox.collidepoint(mouse_position):
            hovered_item = item
            pygame.draw.rect(screen, (181, 145, 81), hitbox, width=1)

    if hovered_item == BLACK_ORE_CHUNK:
        return TooltipContent(
            title="Black ore",
            lines=("Crafting material.",),
            accent=(176, 139, 214),
        )
    return None
