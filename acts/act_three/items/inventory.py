INVENTORY_SLOT_COUNT = 24
BLACK_ORE_CHUNK = "black_ore_chunk"


def get_inventory_slots(player):
    return tuple(player.act_three.inventory_slots)


def inventory_has_space(player):
    return any(item is None for item in player.act_three.inventory_slots)


def store_inventory_item(player, item):
    for index, stored_item in enumerate(player.act_three.inventory_slots):
        if stored_item is None:
            player.act_three.inventory_slots[index] = item
            return True
    return False
