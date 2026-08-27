from dataclasses import dataclass

from acts.act_two.consumables import (
    HEALING_SCROLL,
    POTION,
    SCROLL_OF_ARCANE_IMPULSE,
    SCROLL_OF_BINDING,
    SCROLL_OF_STONEFLESH,
    FIRE_BOMB,
)


@dataclass(frozen=True)
class TraderItem:
    id: str
    name: str
    description: str
    price: int
    sprite_name: str

TRADER_ITEMS = {
    POTION: TraderItem(
        id=POTION,
        name="Potion",
        description="Restores 4 HP.",
        price=2,
        sprite_name="trader_potion",
    ),

    SCROLL_OF_BINDING: TraderItem(
        id=SCROLL_OF_BINDING,
        name="Scroll of Binding",
        description=(
            "Prevents one visible enemy from acting for 5 turns."
        ),
        price=6,
        sprite_name="trader_scroll_of_binding",
    ),

    SCROLL_OF_ARCANE_IMPULSE: TraderItem(
        id=SCROLL_OF_ARCANE_IMPULSE,
        name="Scroll of Arcane Impulse",
        description=(
            "Deals 5 magic damage to one visible enemy."
        ),
        price=4,
        sprite_name="trader_scroll_of_arcane_impulse",
    ),

    HEALING_SCROLL: TraderItem(
        id=HEALING_SCROLL,
        name="Healing Scroll",
        description="Restores 6 HP.",
        price=4,
        sprite_name="trader_healing_scroll",
    ),

    SCROLL_OF_STONEFLESH: TraderItem(
        id=SCROLL_OF_STONEFLESH,
        name="Scroll of Stoneflesh",
        description=(
            "Reduces the next 6 physical hits by 60%."
        ),
        price=6,
        sprite_name="trader_scroll_of_stoneflesh",
    ),

    FIRE_BOMB: TraderItem(
        id=FIRE_BOMB,
        name="Fire Bomb",
        description=(
            "Ignites a 3x3 area for 9 ticks, dealing 1 damage per tick."
        ),
        price=5,
        sprite_name="fire_bomb",
    ),
}

DEFAULT_TRADER_STOCK = {
    "slot_01": POTION,
    "slot_02": SCROLL_OF_BINDING,
    "slot_03": SCROLL_OF_ARCANE_IMPULSE,
    "slot_04": HEALING_SCROLL,
    "slot_05": SCROLL_OF_STONEFLESH,
    "slot_06": FIRE_BOMB,
}
