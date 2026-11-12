from acts.act_three.equipment import MAX_EQUIPMENT_RANK
from acts.act_three.items.inventory import (
    BLACK_ORE_CHUNK,
    get_inventory_slots,
    remove_inventory_item,
)
from game.combat_log import add_log_message


FORGE_UPGRADES = ("weapon", "armor")


def forge_rank(player, upgrade):
    return getattr(player.act_three, f"{upgrade}_rank")


def forge_ore_count(player):
    return get_inventory_slots(player).count(BLACK_ORE_CHUNK)


def can_forge_upgrade(player, upgrade):
    return (
        upgrade in FORGE_UPGRADES
        and forge_rank(player, upgrade) < MAX_EQUIPMENT_RANK
        and forge_ore_count(player) > 0
    )


def try_forge_upgrade(game_state, upgrade):
    player = game_state.player
    if upgrade not in FORGE_UPGRADES:
        return False

    rank = forge_rank(player, upgrade)
    if rank >= MAX_EQUIPMENT_RANK or not remove_inventory_item(player, BLACK_ORE_CHUNK):
        return False

    setattr(player.act_three, f"{upgrade}_rank", rank + 1)
    add_log_message(
        game_state.combat_log,
        f"{upgrade.title()} upgraded to rank {rank + 1}.",
        category="progress",
    )
    return True
