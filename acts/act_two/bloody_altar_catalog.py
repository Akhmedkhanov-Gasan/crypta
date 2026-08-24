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
        reward="Ability damage +2.",
        sacrifice="Incoming damage +1.",
    ),
    BloodyPactDefinition(
        id="broken_seal",
        name="Broken Seal",
        reward="Ability charges after 2 hits.",
        sacrifice="Chosen rune is destroyed.",
    ),
    BloodyPactDefinition(
        id="glass_heart",
        name="Glass Heart",
        reward="Minimum and maximum damage +1.",
        sacrifice="Maximum health -4.",
    ),
    BloodyPactDefinition(
        id="blood_hunger",
        name="Blood Hunger",
        reward="Kills restore 1 health.",
        sacrifice="Potions and scrolls heal 50% less.",
    ),
)

BLOODY_PACTS_BY_ID = {pact.id: pact for pact in BLOODY_PACTS}


__all__ = [
    "BLOODY_PACTS",
    "BLOODY_PACTS_BY_ID",
    "BloodyPactDefinition",
]
