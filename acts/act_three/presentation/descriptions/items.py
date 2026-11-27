from copy import copy

from acts.act_three.bloody_altar.catalog import has_pact
from acts.act_three.trader_catalog import trader_item
from game.healing import heal_player, healing_is_blocked


def healing_lines(player):
    from acts.act_two.bloody_altar import has_bloody_pact
    from acts.act_three.abilities.berserker_runes import rage_blocks_healing

    lines = []
    if has_bloody_pact(player, "open_wound"):
        lines.append("Open Wound: all healing x0.75.")
    if has_pact(player, "insatiable_edge"):
        lines.append("Insatiable Edge: all healing x0.60.")
    elif has_pact(player, "crimson_rupture"):
        lines.append("Crimson Rupture: all healing x0.40.")
    elif has_pact(player, "deaths_reprieve") and not player.act_three.reprieve_ready:
        lines.append("Death's Reprieve is spent: healing x0.50 until recharged.")
    if has_bloody_pact(player, "blood_hunger"):
        lines.append("Blood Hunger forbids healing items; direct damage heals for 25% of damage dealt.")
    if has_pact(player, "endless_hunger"):
        lines.append("Endless Hunger: only its 40% direct-damage lifesteal can heal you.")
    if rage_blocks_healing(player):
        lines.append("The active Last Rage rune prevents receiving healing.")
    return tuple(lines)


def consumable_lines(player, item_id):
    item = trader_item(player, item_id)
    lines = (item.description,)
    if item_id not in ("potion", "healing_scroll", "regeneration_draught", "ironblood_tonic"):
        return lines
    from acts.act_three.trader_catalog import (
        POTION_HEALING, HEALING_SCROLL_HEALING, IRONBLOOD_HEALING, REGENERATION_HEALING,
    )
    from acts.act_two.bloody_altar import healing_consumables_are_blocked

    if healing_consumables_are_blocked(player) or healing_is_blocked(player):
        return (*lines, *healing_lines(player))
    amount = {
        "potion": POTION_HEALING if player.act_three.inventory_unlocked else 4,
        "healing_scroll": HEALING_SCROLL_HEALING if player.act_three.inventory_unlocked else 8,
        "ironblood_tonic": IRONBLOOD_HEALING,
        "regeneration_draught": REGENERATION_HEALING,
    }[item_id]
    preview = copy(player)
    preview.act_two = copy(player.act_two)
    preview.act_three = copy(player.act_three)
    restored = heal_player(preview, amount)
    return (*lines, f"Restores {restored} HP now after active effects and missing-HP limit.", *healing_lines(player))
