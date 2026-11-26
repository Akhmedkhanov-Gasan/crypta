from acts.act_three.items.keys import CRYPTA_KEY, KEYRING_ITEMS


PICKAXE = "pickaxe"
SPECIAL_ITEM_NAMES = {
    PICKAXE: "Pickaxe",
    CRYPTA_KEY: "Crypt key",
    **{item: f"Keyring ({count}/3)" for count, item in enumerate(KEYRING_ITEMS)},
}
SPECIAL_ITEM_DESCRIPTIONS = {
    PICKAXE: "Required to mine ore. Keep it in your inventory.",
    CRYPTA_KEY: "Opens one locked crypt chest. Consumed on use.",
    **{item: "Holds up to 3 keys. Drag a loose key onto the ring." for item in KEYRING_ITEMS},
}
