from acts.act_three.abilities.catalog import get_subclass_definition
from acts.act_three.abilities.progression import is_ability_slot_unlocked
from acts.act_three.rune_master.state import RuneCard
from game.rune_catalog import RUNES_BY_ID, runes_for_class


ICON_ROOT = "assets/sprites/ui/act_3/skills/abilities"
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
ARCHER_RUNES = {
    "piercing_shot": (
        ("rune_of_emerald_piercing_shot", "Rune of Emerald Piercing Shot"),
        ("rune_of_splitfang_arrow", "Rune of Splitfang Arrow"),
    ),
    "barrage_zone": (
        ("rune_of_phantom_archer", "Rune of Phantom Archer"),
        ("rune_of_spectral_archers", "Rune of Spectral Archers"),
    ),
}
SUBCLASS_RUNES = {"assassin": ASSASSIN_RUNES, "archer": ARCHER_RUNES}


def icon_paths(owner, identifier, fallback=None):
    from acts.act_three.presentation.ability_assets import ability_icon_filename

    filename = ability_icon_filename(owner, identifier)
    paths = tuple(
        f"{ICON_ROOT}/{size}/{owner}/{filename}"
        for size in ("rune_master_icon", "icon")
    )
    return paths + ((str(fallback),) if fallback is not None else ())


def available_abilities(player):
    from acts.act_three.presentation.ability_assets import ACT_THREE_ABILITY_ICON_PATHS, ability_icon_key

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
        owner = player.subclass
        identifier = rune.id if rune else ability.id
        fallback = ACT_THREE_ABILITY_ICON_PATHS.get(
            ability_icon_key(player, ability),
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
    if ability.inherited and player.subclass in SUBCLASS_RUNES:
        return tuple(
            RuneCard(rune.id, slot, rune.name, rune.description,
                     icon_paths(player.subclass, rune.id))
            for rune in runes_for_class(player.player_class)
        )
    definitions = SUBCLASS_RUNES.get(player.subclass, {}).get(ability.id, ())
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
