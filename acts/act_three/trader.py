from acts.act_three.items.inventory import remove_inventory_item, store_inventory_item
from acts.act_three.trader_catalog import TRADER_SELL_ITEMS, TRADER_SELL_PRICES, trader_item, trader_stock
from acts.act_two.consumables import remove_act_two_consumable, store_act_two_consumable
from game.combat_log import add_log_message


def buy_trader_item(game_state, item_id):
    player = game_state.player
    from acts.act_three.bloody_altar.catalog import services_are_blocked

    if services_are_blocked(player):
        return False
    if not any(item_id in trader_stock(player, tab) for tab in ("healing", "scrolls", "bombs")):
        return False
    item = trader_item(player, item_id)
    if player.gold_count < item.price:
        add_log_message(game_state.combat_log, "Not enough gold.", category="warning")
        return False
    store = store_inventory_item if player.act_three.inventory_unlocked else store_act_two_consumable
    if not store(player, item_id):
        message = "The inventory is full." if player.act_three.inventory_unlocked else "The belt is full. Complete the trader's delivery to earn a pack."
        add_log_message(game_state.combat_log, message, category="warning")
        return False
    player.gold_count -= item.price
    game_state.run_stats.gold_spent += item.price
    add_log_message(
        game_state.combat_log,
        f"Purchased {item.name} for {item.price} gold.",
        category="trade",
    )
    return True


def sell_trader_item(game_state, item_id):
    from acts.act_three.bloody_altar.catalog import services_are_blocked

    if services_are_blocked(game_state.player):
        return False
    if item_id not in TRADER_SELL_ITEMS:
        return False
    price = TRADER_SELL_PRICES[item_id]
    name = TRADER_SELL_ITEMS[item_id]
    player = game_state.player
    removed = remove_inventory_item(player, item_id)
    if not removed and item_id in player.act_two.consumable_slots:
        remove_act_two_consumable(player, player.act_two.consumable_slots.index(item_id))
        removed = True
    if not removed:
        add_log_message(game_state.combat_log, f"No {name} to sell.", category="warning")
        return False
    player.gold_count += price
    game_state.run_stats.gold_earned += price
    add_log_message(game_state.combat_log, f"Sold {name} for {price} gold.", category="trade")
    return True
