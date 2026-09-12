from presentation.tooltips import TooltipContent


_CONSUMABLE_NAMES = {
    "potion": "POTION",
    "fire_bomb": "FIRE BOMB",
    "key": "KEY",
    "scroll_of_stoneflesh": "STONEFLESH",
    "scroll_of_binding": "BINDING",
    "healing_scroll": "HEALING",
    "scroll_of_arcane_impulse": "IMPULSE",
    "guild_seal": "GUILD SEAL",
}

_CONSUMABLE_DESCRIPTIONS = {
    "potion": "Restores 4 health.",
    "fire_bomb": (
        "Ignites a 3x3 area. The explosion deals damage immediately, "
        "then the fire continues damaging anything standing inside."
    ),
    "key": "Opens one locked chest.",
    "scroll_of_stoneflesh": (
        "Reduces the next 6 instances of incoming physical damage by 60%."
    ),
    "scroll_of_binding": (
        "Prevents one visible enemy from acting for 5 turns."
    ),
    "healing_scroll": "Restores 8 health.",
    "scroll_of_arcane_impulse": (
        "Deals 5 magic damage to one visible enemy."
    ),
    "guild_seal": (
        "The trader's lost guild seal. It cannot be used or discarded."
    ),
}

_ABILITY_NAMES = {
    "warrior": "POWER CLEAVE",
    "rogue": "INVISIBILITY",
    "mage": "ARCANE BURST",
}

_ABILITY_DESCRIPTIONS = {
    "warrior": (
        "Sweep three tiles ahead, damage every enemy in the area and "
        "knock surviving targets backward. Damage scales with Valor."
    ),
    "rogue": (
        "Vanish for 5 turns. Enemies lose sight of you. Your next attack "
        "gains damage from Instinct and becomes a guaranteed critical."
    ),
    "mage": (
        "Detonate a cross at range and scatter surviving enemies outward. "
        "The center deals full damage and outer cells deal half damage. "
        "Damage scales with Will."
    ),
}

_CONSUMABLE_ACCENT = (181, 145, 81)
_ABILITY_ACCENT = (126, 105, 168)
_STATUS_ACCENT = (103, 151, 157)


def consumable_tooltip_content(
    item,
    healing_blocked,
):
    description = (
        "Blood Hunger prevents the use of this healing item."
        if healing_blocked
        else _CONSUMABLE_DESCRIPTIONS.get(
            item,
            "Consumable item.",
        )
    )

    return TooltipContent(
        title=_CONSUMABLE_NAMES.get(item, "ITEM"),
        lines=(description,),
        accent=_CONSUMABLE_ACCENT,
    )


def ability_tooltip_content(
    player_class,
    selected_rune,
):
    if selected_rune is not None:
        return TooltipContent(
            title=selected_rune.name.upper(),
            lines=(selected_rune.description,),
            accent=_ABILITY_ACCENT,
        )

    return TooltipContent(
        title=_ABILITY_NAMES.get(
            player_class,
            "ABILITY",
        ),
        lines=(
            _ABILITY_DESCRIPTIONS.get(
                player_class,
                "Choose a class to unlock its ability.",
            ),
        ),
        accent=_ABILITY_ACCENT,
    )


def status_tooltip_content(
    name,
    description,
):
    return TooltipContent(
        title=name.upper(),
        lines=(description,),
        accent=_STATUS_ACCENT,
    )
