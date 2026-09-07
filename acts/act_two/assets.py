import pygame
import resource_store as resources

from settings import TILE_SIZE


def load_item_pile_sprite():
    source = resources.load_image(
        "assets/sprites/act_2/items/consumables/pile.png"
    ).convert_alpha()

    return pygame.transform.scale(
        source,
        (TILE_SIZE, TILE_SIZE),
    )


def load_pickup_hint_font():
    return resources.load_font(
        "assets/fonts/euxoi.ttf",
        22,
    )
