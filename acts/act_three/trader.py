from acts.act_three.items.inventory import store_inventory_item
from acts.act_three.trader_catalog import TRADER_ITEMS
from game.combat_log import add_log_message


def buy_trader_item(game_state, item_id):
    item = TRADER_ITEMS[item_id]
    player = game_state.player
    if player.gold_count < item.price:
        add_log_message(game_state.combat_log, "Not enough gold.", category="warning")
        return False
    if not store_inventory_item(player, item_id):
        add_log_message(game_state.combat_log, "The inventory is full.", category="warning")
        return False
    player.gold_count -= item.price
    game_state.run_stats.gold_spent += item.price
    add_log_message(
        game_state.combat_log,
        f"Purchased {item.name} for {item.price} gold.",
        category="trade",
    )
    return True
