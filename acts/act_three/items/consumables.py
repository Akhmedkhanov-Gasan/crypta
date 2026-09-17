from dataclasses import dataclass


@dataclass(frozen=True)
class ConsumablePresentation:
    id: str
    ground_filename: str
    belt_filename: str
    original_filename: str


def _presentation(item_id):
    return ConsumablePresentation(
        id=item_id,
        ground_filename=f"{item_id}.png",
        belt_filename=f"{item_id}_belt.png",
        original_filename=f"{item_id}_original.png",
    )


ACT_THREE_CONSUMABLES = {
    item_id: _presentation(item_id)
    for item_id in (
        "potion",
        "fire_bomb",
        "key",
        "scroll_of_stoneflesh",
        "scroll_of_binding",
        "healing_scroll",
        "scroll_of_arcane_impulse",
        "guild_seal",
    )
}


def get_consumable_presentation(item_id):
    return ACT_THREE_CONSUMABLES.get(item_id)
