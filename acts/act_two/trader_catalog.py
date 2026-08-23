from dataclasses import dataclass

from acts.act_two.consumables import (
    HEALING_SCROLL,
    POTION,
    SCROLL_OF_ARCANE_IMPULSE,
    SCROLL_OF_BINDING,
    SCROLL_OF_STONEFLESH,
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
        description="Restores health.",
        price=1,
        sprite_name="trader_potion",
    ),

    SCROLL_OF_BINDING: TraderItem(
        id=SCROLL_OF_BINDING,
        name="Scroll of Binding",
        description="Binds an enemy.",
        price=10,
        sprite_name="trader_scroll_of_binding",
    ),

    SCROLL_OF_ARCANE_IMPULSE: TraderItem(
        id=SCROLL_OF_ARCANE_IMPULSE,
        name="Scroll of Impulse",
        description="Strikes an enemy with arcane force.",
        price=10,
        sprite_name="trader_scroll_of_arcane_impulse",
    ),

    HEALING_SCROLL: TraderItem(
        id=HEALING_SCROLL,
        name="Healing Scroll",
        description="Restores a large amount of health.",
        price=10,
        sprite_name="trader_healing_scroll",
    ),

    SCROLL_OF_STONEFLESH: TraderItem(
        id=SCROLL_OF_STONEFLESH,
        name="Scroll of Stoneflesh",
        description="Reduces incoming physical damage.",
        price=10,
        sprite_name="trader_scroll_of_stoneflesh",
    ),
}

DEFAULT_TRADER_STOCK = {
    "slot_left_01": POTION,
    "slot_left_02": SCROLL_OF_BINDING,
    "slot_left_03": SCROLL_OF_ARCANE_IMPULSE,
    "slot_left_04": HEALING_SCROLL,
    "slot_left_05": SCROLL_OF_STONEFLESH,

    # "slot_right_01": POTION,
    # "slot_right_02": SCROLL_OF_BINDING,
    # "slot_right_03": SCROLL_OF_ARCANE_IMPULSE,
    # "slot_right_04": HEALING_SCROLL,
    # "slot_right_05": SCROLL_OF_STONEFLESH,
}