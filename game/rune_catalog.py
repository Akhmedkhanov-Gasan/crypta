from dataclasses import dataclass


@dataclass(frozen=True)
class RuneDefinition:
    id: str
    player_class: str
    name: str
    icon_filename: str
    original_filename: str
    description: str


RUNE_DEFINITIONS = (
    RuneDefinition(
        id="rune_of_impact",
        player_class="warrior",
        name="Rune of Impact",
        icon_filename="rune_of_impact.png",
        original_filename="rune_of_impact_original.png",
        description=(
            "Passive: 25% chance to block attacks. "
            "Replaces Power Cleave."
        ),
    ),
    RuneDefinition(
        id="rune_of_reaping",
        player_class="warrior",
        name="Rune of Reaping",
        icon_filename="rune_of_reaping.png",
        original_filename="rune_of_reaping_original.png",
        description=(
            "Each enemy struck by Power Cleave restores 1 ability charge."
        ),
    ),
    RuneDefinition(
        id="rune_of_aftershock",
        player_class="warrior",
        name="Rune of Aftershock",
        icon_filename="rune_of_aftershock.png",
        original_filename="rune_of_aftershock_original.png",
        description=(
            "Power Cleave strikes enemies again after knockback for "
            "50% damage."
        ),
    ),
    RuneDefinition(
        id="rune_of_the_shade",
        player_class="rogue",
        name="Rune of the Shade",
        icon_filename="rune_of the_shade.png",
        original_filename="rune_of the_shade_original.png",
        description=(
            "A kill made from invisibility renews the rogue's concealment."
        ),
    ),
    RuneDefinition(
        id="rune_of_cruelty",
        player_class="rogue",
        name="Rune of Cruelty",
        icon_filename="rune_of_cruelty.png",
        original_filename="rune_of_cruelty_original.png",
        description=(
            "An attack from invisibility also causes bleeding for "
            "30% of the hit's damage per turn for 3 turns."
        ),
    ),
    RuneDefinition(
        id="rune_of_the_veil",
        player_class="rogue",
        name="Rune of the Veil",
        icon_filename="rune_of the_veil.png",
        original_filename="rune_of the_veil_original.png",
        description=(
            "Passive: critical hits grant 2 turns of invisibility. "
            "Stealth attacks use your normal critical chance. "
            "Replaces the active invisibility ability."
        ),
    ),
    RuneDefinition(
        id="rune_of_fracture",
        player_class="mage",
        name="Rune of Fracture",
        icon_filename="rune_of_fracture.png",
        original_filename="rune_of_fracture_original.png",
        description=(
            "Arcane Burst strikes a 3x3 area for basic attack damage."
            "Additional enemy adds 25% damage."
        ),
    ),
    RuneDefinition(
        id="rune_of_resonance",
        player_class="mage",
        name="Rune of Resonance",
        icon_filename="rune_of_resonance.png",
        original_filename="rune_of_resonance_original.png",
        description=(
            "Attack in four directions, up to 2 cells. "
            "Arcane Burst is disabled."
        ),
    ),
    RuneDefinition(
        id="rune_of_concentration",
        player_class="mage",
        name="Rune of Concentration",
        icon_filename="rune_of_concentration.png",
        original_filename="rune_of_concentration_original.png",
        description=(
            "Arcane Burst instantly strikes one cell for 100% bonus "
            "damage without knockback."
        ),
    ),
)

RUNES_BY_ID = {rune.id: rune for rune in RUNE_DEFINITIONS}
RUNES_BY_CLASS = {
    player_class: tuple(
        rune
        for rune in RUNE_DEFINITIONS
        if rune.player_class == player_class
    )
    for player_class in ("warrior", "rogue", "mage")
}


def runes_for_class(player_class: str | None) -> tuple[RuneDefinition, ...]:
    return RUNES_BY_CLASS.get(player_class, ())


__all__ = [
    "RUNE_DEFINITIONS",
    "RUNES_BY_CLASS",
    "RUNES_BY_ID",
    "RuneDefinition",
    "runes_for_class",
]
