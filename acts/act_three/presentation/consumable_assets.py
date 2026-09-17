import resource_store as resources

from acts.act_three.items.consumables import (
    ACT_THREE_CONSUMABLES,
)
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


def _load_optional_image(path):
    if not resources.is_file(path):
        return None

    return resources.load_image(
        str(path)
    ).convert_alpha()


def load_act_three_consumable_assets():
    belt_sprites = {}
    ground_sprites = {}
    original_sprites = {}

    for item_id, presentation in (
        ACT_THREE_CONSUMABLES.items()
    ):
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
    }