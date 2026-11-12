import pygame

from acts.act_three.items.use import belt_item, valid_consumable_target
from presentation.layout import ACT_THREE_TILE_SIZE


def draw_consumable_cells(context, game_state, assets):
    tile_size = ACT_THREE_TILE_SIZE

    def tile_rect(cell):
        return pygame.Rect(
            cell[0] * tile_size - context.camera_x,
            cell[1] * tile_size - context.camera_y,
            tile_size,
            tile_size,
        )

    fire_cells = {cell for zone in context.floor.fire_zones for cell in zone.cells}
    visible_fire = fire_cells.intersection(context.floor.visible_cells)
    if visible_fire:
        fire_tile = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        fire_tile.fill((208, 77, 22, 88))
        for cell in visible_fire:
            context.view_surface.blit(fire_tile, tile_rect(cell))

    traps = context.floor.act_three_spring_traps.intersection(context.floor.visible_cells)
    if traps:
        sprite = assets.get("act_three_consumable_ground_sprites", {}).get("spring_trap")
        if sprite is not None:
            marker = pygame.transform.smoothscale(sprite, (tile_size // 2, tile_size // 2))
            for cell in traps:
                context.view_surface.blit(marker, marker.get_rect(center=tile_rect(cell).center))

    player = game_state.player
    state = player.act_three
    target = state.consumable_aim_target
    if state.consumable_aim_slot is None or target not in context.floor.visible_cells:
        return
    item_id = belt_item(player, state.consumable_aim_slot)
    color = (214, 176, 97) if valid_consumable_target(game_state, item_id, target) else (159, 58, 48)
    pygame.draw.rect(context.view_surface, color, tile_rect(target), width=2)
