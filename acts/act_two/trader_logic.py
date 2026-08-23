from acts.act_two.consumables import store_act_two_consumable
from acts.act_two.trader_catalog import (
    DEFAULT_TRADER_STOCK,
    TRADER_ITEMS,
)
from game.combat_log import add_log_message


def buy_trader_item(game_state, slot_name):
    item_id = DEFAULT_TRADER_STOCK.get(slot_name)

    if item_id is None:
        return False

    item = TRADER_ITEMS[item_id]
    player = game_state.player

    if player.gold_count < item.price:
        add_log_message(
            game_state.combat_log,
            "Not enough gold.",
        )
        return False

    if not store_act_two_consumable(player, item.id):
        add_log_message(
            game_state.combat_log,
            "The consumable belt is full.",
        )
        return False

    player.gold_count -= item.price

    add_log_message(
        game_state.combat_log,
        f"Purchased {item.name} for {item.price} gold.",
    )
    return True
