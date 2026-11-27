from dataclasses import dataclass
from acts.act_two.settings import ABILITY_HITS_REQUIRED
from acts.act_three.settings import (
    BERSERKER_CRUSHING_LEAP_CHARGES,
    BERSERKER_LAST_RAGE_CHARGES,
    ASSASSIN_TELEPORT_CHARGES,
    SUMMONER_FAMILIAR_CHARGES,
)


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
    charge_required=float(ABILITY_HITS_REQUIRED),
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
    charge_required=float(ABILITY_HITS_REQUIRED),
    description=(
        "Vanish from sight. Your next attack is a "
        "guaranteed critical hit."
    ),
    inherited=True,
)

def _arcane_burst(subclass):
    return AbilityDefinition(
        id="arcane_burst",
        name="ARCANE BURST",
        slot="e",
        icon_asset=f"act_three_{subclass}_arcane_burst",
        charge_required=float(ABILITY_HITS_REQUIRED),
        description="Detonate a cross at range and scatter enemies outward.",
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
                name="RENDING SPIN",
                slot="q",
                icon_asset=(
                    "act_three_berserker_crushing_leap"
                ),
                charge_required=float(
                    BERSERKER_CRUSHING_LEAP_CHARGES
                ),
                description=(
                    "Choose a direction, then dash up to three cells, "
                    "striking every enemy in your path."
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
                charge_required=float(
                    BERSERKER_LAST_RAGE_CHARGES
                ),
                description=(
                    "Gain maximum Rage and survive eight damaging hits. "
                    "No turn limit. The final hit is still protected; "
                    "dodges and fully blocked attacks do not spend protection."
                ),
            ),
        },
    ),
    "paladin": SubclassDefinition(
        id="paladin",
        parent_class="warrior",
        passive=PassiveDefinition(
            id="paladin_guard",
            name="DARK AEGIS",
            icon_asset="act_three_paladin_passive",
            description=(
                "25% chance to fully block attacks."
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
                    "Rush in a chosen direction, damaging "
                    "and stunning enemies in the path for one turn."
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
                    "Drive the blade into the earth and "
                    "corrupt the surrounding ground. "
                    "Black lightning has 6 damaging enemy hits. "
                    "Empty turns do not spend the zone. A charged recast replaces it with 6 new hits."
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
                charge_required=float(ASSASSIN_TELEPORT_CHARGES),
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
                    "Mark visible enemies within three tiles. "
                    "Strike up to five times, with multiple marks on the same target."
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
                    "Pierce enemies along a six-cell line. "
                    "Damage scales with Valor."
                ),
            ),
            "e": INVISIBILITY,
            "f": AbilityDefinition(
                id="barrage_zone",
                name="PHANTOM RETINUE",
                slot="f",
                icon_asset=(
                    "act_three_archer_barrage_zone"
                ),
                charge_required=8.0,
                description=(
                    "Summon two phantom archers with 6 shots each. "
                    "They fire within 3 cells for 25% of a basic "
                    "shot's damage, prioritizing your attack target. "
                    "Each phantom fades after its final shot."
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
                "Cast skills using HP\n"
                "instead of charges."
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
                    "it receives by 50% for six turns."
                ),
            ),
            "e": _arcane_burst("warlock"),
            "f": AbilityDefinition(
                id="demon_form",
                name="DEMON FORM",
                slot="f",
                icon_asset=(
                    "act_three_warlock_demon_form"
                ),
                charge_required=8.0,
                description=(
                    "Transform into a demon, increasing "
                    "attack damage by 75%. Each attack costs 1 HP; "
                    "kills restore 10% maximum HP. Revert with F."
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
                id="summon_familiar",
                name="SUMMON FAMILIAR",
                slot="q",
                icon_asset=(
                    "act_three_summoner_summon_familiar"
                ),
                charge_required=float(SUMMONER_FAMILIAR_CHARGES),
                description=(
                    "Summon a spiritual familiar that moves and attacks enemies independently. Q recalls it."
                ),
            ),
            "e": _arcane_burst("summoner"),
            "f": AbilityDefinition(
                id="greater_manifestation",
                name="GREATER MANIFESTATION",
                slot="f",
                icon_asset=(
                    "act_three_summoner_greater_manifestation"
                ),
                charge_required=8.0,
                description=(
                    "Choose a neighboring cell and confirm with F to summon a mighty independent spirit alongside your familiar. "
                    "Its attacks deal +3 damage and cost 1 of its own HP. F dismisses it."
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
