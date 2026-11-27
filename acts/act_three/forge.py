from collections import Counter

import pygame

from acts.act_three.blacksmith.recipes import FORGE_RECIPES, IMPLEMENTED_FORGE_RANK, TEMPERING_DURATION_MS
from acts.act_three.items.inventory import get_inventory_slots, remove_inventory_item
from game.combat_log import add_log_message


FORGE_UPGRADES = ("weapon", "armor")


def forge_rank(player, upgrade):
    return getattr(player.act_three, f"{upgrade}_rank")


def forge_recipe(player, upgrade):
    return FORGE_RECIPES.get(forge_rank(player, upgrade) + 1, {})


def forge_ore_count(player, item):
    return get_inventory_slots(player).count(item)


def forge_work(player, upgrade):
    return player.act_three.forge_progress.get(upgrade, {})


def forge_progress_fraction(player, upgrade):
    recipe = forge_recipe(player, upgrade)
    work = forge_work(player, upgrade)
    fraction = sum(min(work.get(item, 0), amount) for item, amount in recipe.items()) / max(1, sum(recipe.values()))
    return fraction


def can_forge_upgrade(player, upgrade):
    from acts.act_three.bloody_altar.catalog import services_are_blocked

    if services_are_blocked(player):
        return False
    if not player.act_three.inventory_unlocked:
        return False
    if upgrade not in FORGE_UPGRADES or not player.act_three.blacksmith_quest.get("completed", False):
        return False
    if forge_rank(player, upgrade) >= IMPLEMENTED_FORGE_RANK:
        return False
    work = forge_work(player, upgrade)
    return any(forge_ore_count(player, item) > 0 and work.get(item, 0) < amount for item, amount in forge_recipe(player, upgrade).items())


def try_forge_upgrade(game_state, upgrade):
    player = game_state.player
    if not can_forge_upgrade(player, upgrade):
        return False

    recipe = forge_recipe(player, upgrade)
    owned = Counter(get_inventory_slots(player))
    work = player.act_three.forge_progress.setdefault(upgrade, {})
    for item, amount in recipe.items():
        used = min(owned[item], max(0, amount - work.get(item, 0)))
        for _ in range(used):
            remove_inventory_item(player, item)
        work[item] = work.get(item, 0) + used

    complete = all(work.get(item, 0) >= amount for item, amount in recipe.items())
    if complete:
        rank = forge_rank(player, upgrade) + 1
        setattr(player.act_three, f"{upgrade}_rank", rank)
        player.act_three.forge_progress.pop(upgrade, None)
        message = f"{upgrade.title()} upgraded to rank {rank}."
    else:
        rank = forge_rank(player, upgrade)
        message = f"{upgrade.title()} forging: {sum(work.values())}/{sum(recipe.values())} materials worked. No stat bonus until this rank is complete."
    add_log_message(game_state.combat_log, message, category="progress")

    from acts.act_three.quests.blacksmith import queue_forge_dialogue

    queue_forge_dialogue(game_state, rank, complete, pygame.time.get_ticks() + TEMPERING_DURATION_MS)
    return True
