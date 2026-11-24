from acts.act_three.abilities.catalog import get_subclass_definition
from acts.act_three.abilities.progression import is_ability_slot_unlocked
from acts.act_three.rune_master.state import RuneCard
from acts.act_three.rune_master.definitions import ABILITY_RUNES, equipped_rune
from game.rune_catalog import RUNES_BY_ID, runes_for_class
from acts.act_three.rune_master.access import can_modify_rune


ICON_ROOT = "assets/sprites/ui/act_3/skills/abilities"
READY_SUBCLASSES = frozenset({"assassin", "archer", "berserker", "paladin", "warlock", "summoner"})


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
    for slot in ("q", "e", "f"):
        ability = subclass.abilities.get(slot)
        if ability is None or not is_ability_slot_unlocked(player, slot):
            continue
        if not can_modify_rune(player, slot):
            continue
        rune = RUNES_BY_ID.get(player.selected_rune_id) if ability.inherited else None
        if rune is not None and rune.player_class != player.player_class:
            rune = None
        if not ability.inherited:
            rune = equipped_rune(player, slot)
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
    if ability.inherited and player.subclass in READY_SUBCLASSES:
        return tuple(
            RuneCard(rune.id, slot, rune.name, rune.description,
                     icon_paths(player.subclass, rune.id))
            for rune in runes_for_class(player.player_class)
        )
    definitions = tuple(rune for rune in ABILITY_RUNES if rune.subclass == player.subclass and rune.slot == slot)
    choices = [
        RuneCard(rune.id, slot, rune.name, rune.description,
                 icon_paths(player.subclass, rune.id),
                 placeholder=player.act_three.warlock_eternal_bound and slot == "f" and rune.id != "rune_of_eternal_form")
        for rune in definitions
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
