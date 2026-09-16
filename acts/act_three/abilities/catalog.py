from dataclasses import dataclass


@dataclass(frozen=True)
class AbilityDefinition:
    id: str
    name: str
    slot: str
    icon_asset: str
    charge_required: float
    description: str
    inherited: bool = False


@dataclass(frozen=True)
class PassiveDefinition:
    id: str
    name: str
    icon_asset: str
    description: str


@dataclass(frozen=True)
class SubclassDefinition:
    id: str
    parent_class: str
    passive: PassiveDefinition
    abilities: dict[str, AbilityDefinition]


POWER_CLEAVE = AbilityDefinition(
    id="power_cleave",
    name="POWER CLEAVE",
    slot="e",
    icon_asset="act_three_power_cleave",
    charge_required=2.0,
    description=(
        "Sweep three tiles ahead and knock enemies back."
    ),
    inherited=True,
)

INVISIBILITY = AbilityDefinition(
    id="invisibility",
    name="INVISIBILITY",
    slot="e",
    icon_asset="act_three_invisibility",
    charge_required=2.0,
    description=(
        "Vanish from sight. Your next attack is a "
        "guaranteed critical hit."
    ),
    inherited=True,
)

ARCANE_BURST = AbilityDefinition(
    id="arcane_burst",
    name="ARCANE BURST",
    slot="e",
    icon_asset="act_three_arcane_burst",
    charge_required=2.0,
    description=(
        "Detonate a cross at range and scatter enemies "
        "outward."
    ),
    inherited=True,
)


SUBCLASS_DEFINITIONS = {
    "berserker": SubclassDefinition(
        id="berserker",
        parent_class="warrior",
        passive=PassiveDefinition(
            id="rage",
            name="RAGE",
            icon_asset="act_three_berserker_passive",
            description=(
                "Physical damage rises\n"
                "as health falls."
            ),
        ),
        abilities={
            "q": AbilityDefinition(
                id="crushing_leap",
                name="CRUSHING LEAP",
                slot="q",
                icon_asset=(
                    "act_three_berserker_crushing_leap"
                ),
                charge_required=4.0,
                description=(
                    "Leap to a visible cell and damage "
                    "adjacent enemies on landing."
                ),
            ),
            "e": POWER_CLEAVE,
            "f": AbilityDefinition(
                id="last_rage",
                name="LAST RAGE",
                slot="f",
                icon_asset=(
                    "act_three_berserker_last_rage"
                ),
                charge_required=8.0,
                description=(
                    "Refuse death for five turns and gain "
                    "the maximum Rage bonus."
                ),
            ),
        },
    ),
    "paladin": SubclassDefinition(
        id="paladin",
        parent_class="warrior",
        passive=PassiveDefinition(
            id="hold_the_line",
            name="HOLD THE LINE",
            icon_asset="act_three_paladin_passive",
            description=(
                "Remain in place to brace\n"
                "against the next direct hit."
            ),
        ),
        abilities={
            "q": AbilityDefinition(
                id="shield_charge",
                name="SHIELD CHARGE",
                slot="q",
                icon_asset=(
                    "act_three_paladin_shield_charge"
                ),
                charge_required=4.0,
                description=(
                    "Rush forward, damage enemies in the "
                    "path and push them aside."
                ),
            ),
            "e": POWER_CLEAVE,
            "f": AbilityDefinition(
                id="sacred_ground",
                name="SACRED GROUND",
                slot="f",
                icon_asset=(
                    "act_three_paladin_sacred_ground"
                ),
                charge_required=8.0,
                description=(
                    "Consecrate a 4 by 4 area. Enemies "
                    "inside are paralyzed for two turns."
                ),
            ),
        },
    ),
    "assassin": SubclassDefinition(
        id="assassin",
        parent_class="rogue",
        passive=PassiveDefinition(
            id="shadow_reflex",
            name="SHADOW REFLEX",
            icon_asset="act_three_assassin_passive",
            description=(
                "Dodging a direct attack\n"
                "triggers a counterattack."
            ),
        ),
        abilities={
            "q": AbilityDefinition(
                id="shadow_step",
                name="SHADOW STEP",
                slot="q",
                icon_asset=(
                    "act_three_assassin_shadow_step"
                ),
                charge_required=4.0,
                description=(
                    "Teleport to a visible unoccupied cell."
                ),
            ),
            "e": INVISIBILITY,
            "f": AbilityDefinition(
                id="killing_spree",
                name="KILLING SPREE",
                slot="f",
                icon_asset=(
                    "act_three_assassin_killing_spree"
                ),
                charge_required=8.0,
                description=(
                    "Strike up to three visible enemies "
                    "in rapid succession."
                ),
            ),
        },
    ),
    "archer": SubclassDefinition(
        id="archer",
        parent_class="rogue",
        passive=PassiveDefinition(
            id="marksman",
            name="MARKSMAN",
            icon_asset="act_three_archer_passive",
            description=(
                "Basic attacks can strike\n"
                "visible enemies from range."
            ),
        ),
        abilities={
            "q": AbilityDefinition(
                id="piercing_shot",
                name="PIERCING SHOT",
                slot="q",
                icon_asset=(
                    "act_three_archer_piercing_shot"
                ),
                charge_required=4.0,
                description=(
                    "Fire through the first target and hit "
                    "one additional enemy behind it."
                ),
            ),
            "e": INVISIBILITY,
            "f": AbilityDefinition(
                id="barrage_zone",
                name="BARRAGE ZONE",
                slot="f",
                icon_asset=(
                    "act_three_archer_barrage_zone"
                ),
                charge_required=8.0,
                description=(
                    "Prepare an area that fires at enemies "
                    "entering its cells."
                ),
            ),
        },
    ),
    "warlock": SubclassDefinition(
        id="warlock",
        parent_class="mage",
        passive=PassiveDefinition(
            id="blood_magic",
            name="BLOOD MAGIC",
            icon_asset="act_three_warlock_passive",
            description=(
                "Spend health to cast abilities\n"
                "before they are charged."
            ),
        ),
        abilities={
            "q": AbilityDefinition(
                id="curse",
                name="CURSE",
                slot="q",
                icon_asset="act_three_warlock_curse",
                charge_required=4.0,
                description=(
                    "Curse an enemy, increasing the damage "
                    "it receives for five turns."
                ),
            ),
            "e": ARCANE_BURST,
            "f": AbilityDefinition(
                id="demon_form",
                name="DEMON FORM",
                slot="f",
                icon_asset=(
                    "act_three_warlock_demon_form"
                ),
                charge_required=8.0,
                description=(
                    "Transform for five turns, increasing "
                    "damage while draining health."
                ),
            ),
        },
    ),
    "summoner": SubclassDefinition(
        id="summoner",
        parent_class="mage",
        passive=PassiveDefinition(
            id="astral_familiar",
            name="ASTRAL FAMILIAR",
            icon_asset="act_three_summoner_passive",
            description=(
                "Release a bonded familiar\n"
                "to fight independently."
            ),
        ),
        abilities={
            "q": AbilityDefinition(
                id="release_familiar",
                name="RELEASE FAMILIAR",
                slot="q",
                icon_asset=(
                    "act_three_summoner_release_familiar"
                ),
                charge_required=4.0,
                description=(
                    "Release the bonded familiar onto the "
                    "battlefield or recall it."
                ),
            ),
            "e": ARCANE_BURST,
            "f": AbilityDefinition(
                id="true_form",
                name="TRUE FORM",
                slot="f",
                icon_asset=(
                    "act_three_summoner_true_form"
                ),
                charge_required=8.0,
                description=(
                    "Empower the released familiar for "
                    "five of its actions."
                ),
            ),
        },
    ),
}


def get_subclass_definition(subclass):
    return SUBCLASS_DEFINITIONS.get(subclass)


def get_ability_definition(
    subclass,
    slot,
):
    definition = get_subclass_definition(subclass)

    if definition is None:
        return None

    return definition.abilities.get(slot)


def get_passive_definition(subclass):
    definition = get_subclass_definition(subclass)

    if definition is None:
        return None

    return definition.passive
