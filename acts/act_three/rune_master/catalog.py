from acts.act_three.abilities.catalog import get_subclass_definition
from acts.act_three.abilities.progression import is_ability_slot_unlocked
from acts.act_three.rune_master.state import RuneCard
from game.rune_catalog import RUNES_BY_ID, runes_for_class


ICON_ROOT = "assets/sprites/ui/act_3/skills/abilities/runes"
ASSASSIN_RUNES = {
    "shadow_step": (
        ("rune_of_displacement", "Rune of Displacement"),
        ("rune_of_the_doppelganger", "Rune of the Doppelganger"),
    ),
    "killing_spree": (
        ("rune_of_carnage", "Rune of Carnage"),
        ("rune_of_the_executioner", "Rune of the Executioner"),
    ),
}


def icon_paths(owner, identifier, fallback=None):
    names = [f"{identifier}.png"]
    if identifier == "rune_of_the_doppelganger":
        names.append("rune_of the_doppelganger.png")
    paths = tuple(
        f"{ICON_ROOT}/{size}/{owner}/{name}"
        for size in ("rune_master", "icon")
        for name in names
    )
    return paths + ((str(fallback),) if fallback is not None else ())


def available_abilities(player):
    from acts.act_three.presentation.ability_assets import ACT_THREE_ABILITY_ICON_PATHS

    subclass = get_subclass_definition(player.subclass)
    if subclass is None:
        return ()
    cards = []
    for slot in ("e", "q", "f"):
        ability = subclass.abilities.get(slot)
        if ability is None or not is_ability_slot_unlocked(player, slot):
            continue
        rune = RUNES_BY_ID.get(player.selected_rune_id) if ability.inherited else None
        if rune is not None and rune.player_class != player.player_class:
            rune = None
        owner = player.player_class if ability.inherited else player.subclass
        identifier = rune.id if rune else ability.id
        fallback = ACT_THREE_ABILITY_ICON_PATHS.get(
            f"act_three_{rune.id}" if rune else ability.icon_asset,
        )
        cards.append(RuneCard(
            identifier, slot,
            rune.name if rune else ability.name,
            rune.description if rune else ability.description,
            icon_paths(owner, identifier, fallback),
        ))
    return tuple(cards)


def upgrade_choices(player, slot):
    subclass = get_subclass_definition(player.subclass)
    ability = subclass.abilities[slot]
    selected_rune = RUNES_BY_ID.get(player.selected_rune_id)
    if ability.inherited and (
        selected_rune is None or selected_rune.player_class != player.player_class
    ):
        return tuple(
            RuneCard(rune.id, slot, rune.name, rune.description,
                     icon_paths(player.player_class, rune.id))
            for rune in runes_for_class(player.player_class)
        )
    definitions = ASSASSIN_RUNES.get(ability.id, ()) if player.subclass == "assassin" else ()
    choices = [
        RuneCard(identifier, slot, name,
                 f"{ability.name.title()} modification. Effect pending.",
                 icon_paths(player.subclass, identifier))
        for identifier, name in definitions
    ]
    choice_count = 3 if ability.inherited else 2
    while len(choices) < choice_count:
        number = len(choices) + 1
        choices.append(RuneCard(
            f"{ability.id}_preview_{number}", slot, f"Rune variant {number}",
            "Preview slot. Rune artwork and effect are not configured.",
            placeholder=True,
        ))
    return tuple(choices)
