from acts.act_three.items.keys import CRYPTA_KEY, KEYRING_ITEMS, collect_loose_keys, combine_key_and_ring, store_key_on_ring


INVENTORY_SLOT_COUNT = 20
BLACK_ORE_CHUNK = "black_ore_chunk"
IRON_ORE_CHUNK = "iron_ore_chunk"
BLOODVEIN_ORE_CHUNK = "bloodvein_ore_chunk"
ORE_ITEM_NAMES = {
    BLACK_ORE_CHUNK: "Black ore",
    IRON_ORE_CHUNK: "Iron ore",
    BLOODVEIN_ORE_CHUNK: "Bloodvein ore",
}


def get_inventory_slots(player):
    return tuple(player.act_three.inventory_slots)


def inventory_has_space(player):
    return player.act_three.inventory_unlocked and any(item is None for item in player.act_three.inventory_slots)


def store_inventory_item(player, item):
    if not player.act_three.inventory_unlocked:
        return False
    slots = player.act_three.inventory_slots
    if item in ("key", CRYPTA_KEY):
        item = CRYPTA_KEY
        if store_key_on_ring(slots):
            return True
    if item in KEYRING_ITEMS and any(stored in KEYRING_ITEMS for stored in slots):
        return False
    for index, stored_item in enumerate(slots):
        if stored_item is None:
            slots[index] = item
            if item in KEYRING_ITEMS:
                collect_loose_keys(slots, index)
            return True
    return False


def remove_inventory_item(player, item):
    slots = player.act_three.inventory_slots
    for index, stored_item in enumerate(slots):
        if stored_item == item:
            slots[index] = None
            return True
    return False


def move_inventory_item_to_belt(player, source_index, belt_index):
    if not player.act_three.inventory_unlocked:
        return False
    from acts.act_three.trader_catalog import TRADER_ITEMS
    from acts.act_two.consumables import remove_act_two_consumable, store_act_two_consumable

    slots = player.act_three.inventory_slots
    belt = player.act_two.consumable_slots
    if not (0 <= source_index < len(slots) and 0 <= belt_index < len(belt)):
        return False
    item = slots[source_index]
    if item not in TRADER_ITEMS:
        return False
    previous_item = remove_act_two_consumable(player, belt_index)
    store_act_two_consumable(player, item, belt_index)
    slots[source_index] = previous_item
    return True


def assign_inventory_item_to_belt(game_state, source_index, belt_index):
    from acts.act_three.trader_catalog import TRADER_ITEMS, TRADER_SELL_ITEMS
    from game.combat_log import add_log_message

    player = game_state.player
    slots = get_inventory_slots(player)
    if not 0 <= source_index < len(slots) or slots[source_index] is None:
        return False

    item = slots[source_index]
    if item not in TRADER_ITEMS:
        name = TRADER_SELL_ITEMS.get(item, item.replace("_", " ").capitalize())
        message = f"{name} cannot be placed on the belt."
    elif move_inventory_item_to_belt(player, source_index, belt_index):
        return True
    else:
        message = f"Belt slot {belt_index + 1} is unavailable."

    add_log_message(game_state.combat_log, message, category="warning")
    return False


def move_belt_item_to_inventory(player, belt_index, target_index):
    if not player.act_three.inventory_unlocked:
        return False
    from acts.act_three.quests.trader import URN_ITEMS
    from acts.act_two.consumables import remove_act_two_consumable

    inventory = player.act_three.inventory_slots
    belt = player.act_two.consumable_slots
    if not 0 <= target_index < len(inventory) or inventory[target_index] is not None:
        return False
    if not 0 <= belt_index < len(belt) or belt[belt_index] is None or belt[belt_index] in URN_ITEMS:
        return False
    inventory[target_index] = remove_act_two_consumable(player, belt_index)
    return True


def _rearrange_slots(slots, source_index, target_index):
    if not (0 <= source_index < len(slots) and 0 <= target_index < len(slots)):
        return False
    if source_index == target_index or slots[source_index] is None:
        return False
    slots[source_index], slots[target_index] = slots[target_index], slots[source_index]
    return True


def rearrange_inventory(player, source_index, target_index):
    if not player.act_three.inventory_unlocked:
        return False
    if combine_key_and_ring(player.act_three.inventory_slots, source_index, target_index):
        return True
    return _rearrange_slots(player.act_three.inventory_slots, source_index, target_index)


def rearrange_belt(player, source_index, target_index):
    return _rearrange_slots(player.act_two.consumable_slots, source_index, target_index)
