import pygame
import resource_store as resources

from acts.act_three.items.consumables import (
    ACT_THREE_CONSUMABLES,
)
from acts.act_three.trader_catalog import TRADER_ITEMS, TRADER_SELL_ITEMS
from presentation.layout import ASSET_ROOT


_CONSUMABLE_ROOT = (
    ASSET_ROOT
    / "act_3"
    / "items"
    / "consumables"
)
_BELT_ROOT = _CONSUMABLE_ROOT / "belt"
_GROUND_ROOT = _CONSUMABLE_ROOT / "on_ground"
_ORIGINAL_ROOT = _CONSUMABLE_ROOT / "original"
_ART_FILENAMES = {
    "fire_bomb": "fire_bomb2.png",
    "scroll_of_arcane_impulse": "scroll_of_impulse.png",
}


def _load_optional_image(path):
    if not resources.is_file(path):
        return None

    return resources.load_image(
        str(path)
    ).convert_alpha()


def _fit_icon(image):
    if image is None or max(image.get_size()) <= 128:
        return image
    size = image.get_rect().fit(pygame.Rect(0, 0, 128, 128)).size
    return pygame.transform.smoothscale(image, size)


def load_act_three_consumable_assets():
    belt_sprites = {}
    ground_sprites = {}
    original_sprites = {}

    for item_id in dict.fromkeys((*ACT_THREE_CONSUMABLES, *TRADER_ITEMS)):
        item_art = _load_optional_image(
            _CONSUMABLE_ROOT / _ART_FILENAMES.get(item_id, f"{item_id}.png")
        )
        presentation = ACT_THREE_CONSUMABLES.get(item_id)
        if item_art is not None:
            icon = _fit_icon(item_art)
            belt_sprites[item_id] = icon
            ground_sprites[item_id] = icon
            original_sprites[item_id] = item_art
            continue
        if presentation is None:
            continue
        belt_image = _load_optional_image(
            _BELT_ROOT
            / presentation.belt_filename
        )
        ground_image = _load_optional_image(
            _GROUND_ROOT
            / presentation.ground_filename
        )
        original_image = _load_optional_image(
            _ORIGINAL_ROOT
            / presentation.original_filename
        )

        if belt_image is not None:
            belt_sprites[item_id] = belt_image

        if ground_image is not None:
            ground_sprites[item_id] = ground_image

        if original_image is not None:
            original_sprites[item_id] = original_image

    return {
        "act_three_consumable_belt_sprites": belt_sprites,
        "act_three_consumable_ground_sprites": ground_sprites,
        "act_three_consumable_original_sprites": original_sprites,
        "act_three_sell_item_sprites": {
            item_id: _fit_icon(_load_optional_image(_CONSUMABLE_ROOT / f"{item_id}.png"))
            for item_id in TRADER_SELL_ITEMS
        },
    }
