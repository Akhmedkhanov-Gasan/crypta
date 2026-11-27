from copy import copy

from acts.act_three.ability_scaling import basic_attack_damage_range, paladin_ground_damage_bonus
from acts.act_three.attributes import advance_chance
from acts.act_three.presentation.descriptions.combat import damage_range_text, health_lines
from game.attributes import get_attribute_definition, player_stat_changes_for_attribute_upgrade
from game.progression import apply_attribute_upgrade
from presentation.tooltips import TooltipContent


_ACCENTS = {"valor": (184, 82, 64), "instinct": (190, 151, 69), "will": (92, 128, 185), "fortitude": (139, 74, 89)}


def attribute_tooltip(player, attribute):
    rank = player.attribute_ranks.get(attribute, 0)
    change = player_stat_changes_for_attribute_upgrade(attribute, rank, rank_limit=None)
    preview = copy(player)
    preview.attribute_ranks = dict(player.attribute_ranks)
    preview.act_two = copy(player.act_two)
    preview.act_three = copy(player.act_three)
    apply_attribute_upgrade(preview, attribute)
    before, after = basic_attack_damage_range(player), basic_attack_damage_range(preview)
    crit_gain = (advance_chance(player.crit_chance, change.crit_chance) - player.crit_chance) * 100
    dodge_gain = (advance_chance(player.dodge_chance, change.dodge_chance, dodge=True) - player.dodge_chance) * 100
    if attribute == "valor":
        lines = (
            "Physical damage rises by 1 every two ranks; minimum and maximum increase alternately.",
            "+0.05 critical multiplier per rank; +1 maximum HP every two ranks.",
            f"Next rank: +{change.damage_min}-{change.damage_max} physical damage, +0.05 critical multiplier, +{preview.max_health - player.max_health} maximum HP.",
        )
        if player.player_class == "warrior":
            from acts.act_two.ability_scaling import warrior_cleave_damage_bonus

            lines += (f"Power Cleave bonus: +{warrior_cleave_damage_bonus(rank)}; next +{warrior_cleave_damage_bonus(rank + 1)}.",)
        elif player.subclass == "archer":
            lines += ("Also increases Piercing Shot and phantom damage.",)
        elif player.player_class == "mage":
            lines += ("Your magical attacks and spirits use Will for damage; Valor still grants HP and critical damage.",)
    elif attribute == "instinct":
        lines = (
            "Base gain per rank: +4 percentage points critical chance, +3 points dodge.",
            f"Next rank with diminishing returns: +{crit_gain:.2f} points critical chance, +{dodge_gain:.2f} points dodge.",
        )
        if player.subclass == "assassin":
            from acts.act_two.ability_scaling import rogue_ambush_damage_bonus

            lines += (f"Melee ambush bonus: +{rogue_ambush_damage_bonus(rank)}; next +{rogue_ambush_damage_bonus(rank + 1)}.",
                      "Shadow Reflex counters direct attacks that you dodge.")
    elif attribute == "will":
        lines = (
            "+0.03 critical multiplier per rank; base critical chance gain +1 percentage point.",
            f"Next rank: +{crit_gain:.2f} points critical chance and +0.03 critical multiplier.",
        )
        if player.player_class == "mage":
            from acts.act_two.ability_scaling import mage_arcane_burst_damage_bonus

            lines += (f"Magical attack: {damage_range_text(before)} -> {damage_range_text(after)}.",
                      f"Arcane Burst center bonus: +{mage_arcane_burst_damage_bonus(rank)} -> +{mage_arcane_burst_damage_bonus(rank + 1)}.")
        if player.subclass == "summoner":
            lines += ("Also increases familiar, totem and greater spirit damage.",)
        elif player.subclass == "paladin":
            lines += (f"Sacred Ground bonus: +{paladin_ground_damage_bonus(player)} -> +{paladin_ground_damage_bonus(preview)} per lightning hit.",)
    else:
        lines = (
            "+2 maximum HP per rank; base dodge gain +1 percentage point.",
            f"Next rank after pacts: +{preview.max_health - player.max_health} maximum HP; +{dodge_gain:.2f} points dodge.",
            *health_lines(player),
        )
    return TooltipContent(f"{get_attribute_definition(attribute).title.upper()} | {rank}", lines, _ACCENTS[attribute])
