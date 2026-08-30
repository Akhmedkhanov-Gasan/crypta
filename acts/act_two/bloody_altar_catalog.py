from dataclasses import dataclass


@dataclass(frozen=True)
class BloodyPactDefinition:
    id: str
    name: str
    reward: str
    sacrifice: str


BLOODY_PACTS = (
    BloodyPactDefinition(
        id="open_wound",
        name="Open Wound",
        reward="Abilities no longer require charge.",
        sacrifice="Each ability use costs 10% of maximum health.",
    ),
    BloodyPactDefinition(
        id="broken_seal",
        name="Broken Seal",
        reward="Abilities charge after 2 successful hits.",
        sacrifice="The selected rune is permanently destroyed.",
    ),
    BloodyPactDefinition(
        id="glass_heart",
        name="Glass Heart",
        reward="All damage dealt is increased by 50%.",
        sacrifice="Maximum health is permanently reduced by 25%.",
    ),
    BloodyPactDefinition(
        id="blood_hunger",
        name="Blood Hunger",
        reward="Damage dealt restores 25% of that damage as health.",
        sacrifice="Healing consumables can no longer be used.",
    ),
)

BLOODY_PACTS_BY_ID = {pact.id: pact for pact in BLOODY_PACTS}


__all__ = [
    "BLOODY_PACTS",
    "BLOODY_PACTS_BY_ID",
    "BloodyPactDefinition",
]
