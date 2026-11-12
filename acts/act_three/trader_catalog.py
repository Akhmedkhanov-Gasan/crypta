from dataclasses import dataclass


@dataclass(frozen=True)
class TraderItem:
    name: str
    price: int
    description: str


POTION_HEALING = 6
HEALING_SCROLL_HEALING = 12
REGENERATION_HEALING = 3
REGENERATION_TICKS = 3
IRONBLOOD_HEALING = 5
ARCANE_IMPULSE_DAMAGE = 8
FIRE_BOMB_IMPACT = 5
FIRE_BOMB_TICK = 3
SPRING_TRAP_DAMAGE = 8
BLAST_CHARGE_DAMAGE = 6

TRADER_ITEMS = {
    "potion": TraderItem("Potion", 5, f"Restores {POTION_HEALING} HP."),
    "healing_scroll": TraderItem("Healing Scroll", 9, f"Restores {HEALING_SCROLL_HEALING} HP."),
    "regeneration_draught": TraderItem(
        "Regeneration Draught", 7,
        f"Restores {REGENERATION_HEALING} HP now and for the next {REGENERATION_TICKS - 1} turns.",
    ),
    "ironblood_tonic": TraderItem(
        "Ironblood Tonic", 8, f"Restores {IRONBLOOD_HEALING} HP and halves the next hit this turn.",
    ),
    "scroll_of_arcane_impulse": TraderItem(
        "Scroll of Arcane Impulse", 7, f"Deals {ARCANE_IMPULSE_DAMAGE} magic damage to a visible enemy.",
    ),
    "scroll_of_binding": TraderItem("Scroll of Binding", 8, "Binds one visible enemy for 5 turns."),
    "scroll_of_stoneflesh": TraderItem(
        "Scroll of Stoneflesh", 10, "Reduces the next 6 physical hits by 60%.",
    ),
    "fire_bomb": TraderItem(
        "Fire Bomb", 12, f"Deals {FIRE_BOMB_IMPACT} damage on impact and ignites a 3x3 area for {FIRE_BOMB_TICK} damage per tick.",
    ),
    "flash_bomb": TraderItem("Flash Bomb", 9, "Stuns enemies in a 3x3 area for one turn."),
    "spring_trap": TraderItem(
        "Spring Trap", 8, f"Places a trap that deals {SPRING_TRAP_DAMAGE} damage and stuns its first victim for one turn.",
    ),
    "blast_charge": TraderItem(
        "Blast Charge", 11, f"Deals {BLAST_CHARGE_DAMAGE} damage in a cross and pushes enemies away.",
    ),
}

TRADER_STOCK = {
    "healing": ("potion", "healing_scroll", "regeneration_draught", "ironblood_tonic"),
    "scrolls": ("scroll_of_arcane_impulse", "scroll_of_binding", "healing_scroll", "scroll_of_stoneflesh"),
    "bombs": ("fire_bomb", "flash_bomb", "spring_trap", "blast_charge"),
    "sell": (),
}

TRADER_SELL_ITEMS = {
    "gemstone": "Gemstone",
    "monster_parts": "Monster Parts",
    "silverware": "Silverware",
    "burial_relic": "Burial Relic",
}
