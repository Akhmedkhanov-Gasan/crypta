import resource_store as resources

from acts.act_three.items.keys import CRYPTA_KEY, KEYRING_ITEMS
from acts.act_three.items.special import PICKAXE
from presentation.layout import ASSET_ROOT


def load_special_item_assets():
    root = ASSET_ROOT / "act_3" / "items"
    paths = {
        PICKAXE: root / "pickaxe.png",
        CRYPTA_KEY: root / "keys" / "crypta_key_inventory.png",
        **{item: root / "keys" / filename for item, filename in zip(KEYRING_ITEMS, ("no_keys.png", "one_key.png", "two_keys.png", "three_keys.png"))},
    }
    icons = {item: resources.load_image(path).convert_alpha() for item, path in paths.items()}
    ground_root = root / "ground_drops"
    keyring = resources.load_image(ground_root / "keyring.png").convert_alpha()
    ground = {
        PICKAXE: resources.load_image(ground_root / "pickaxe_sprite.png").convert_alpha(),
        CRYPTA_KEY: resources.load_image(ground_root / "crypta_key_ground_64.png").convert_alpha(),
        **dict.fromkeys(KEYRING_ITEMS, keyring),
    }
    ground["key"] = ground[CRYPTA_KEY]
    return icons, ground
