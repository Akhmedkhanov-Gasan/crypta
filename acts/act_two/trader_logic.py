from acts.act_two.consumables import (
    GUILD_SEAL,
    remove_act_two_consumable_kind,
    store_act_two_consumable,
)
from acts.act_two.trader_catalog import (
    DEFAULT_TRADER_STOCK,
    TRADER_ITEMS,
)
from game.combat_log import add_log_message


def interact_with_trader(
    game_state,
    dialogue_started_at,
):
    quest = game_state.act_two_quests.trader_seal

    if quest.completed:
        game_state.trader_dialogue_text = ""
        game_state.trader_dialogue_started_at = -1
        game_state.trader_dialogue_dismiss_started_at = -1
        game_state.trade_screen_open = True

        add_log_message(
            game_state.combat_log,
            (
                "Trader: Good to see you again. "
                "Take a look at my wares."
            ),
            category="dialogue",
        )
        return "trader_normal"

    if quest.seal_recovered:
        quest.started = True
        quest.completed = True
        remove_act_two_consumable_kind(
            game_state.player,
            GUILD_SEAL,
        )

        game_state.trader_dialogue_text = ""
        game_state.trader_dialogue_started_at = -1
        game_state.trader_dialogue_dismiss_started_at = -1
        game_state.trade_screen_open = True

        add_log_message(
            game_state.combat_log,
            (
                "Trader: You found the guild seal... "
                "I thought it was lost with them. "
                "Thank you. Let us trade."
            ),
            category="dialogue",
        )
        add_log_message(
            game_state.combat_log,
            "The trader's wares are now available.",
            category="quest",
        )
        return "trader_normal"

    if not quest.started:
        quest.started = True

        dialogue = (
            "I cannot trade without my guild seal. "
            "My group carried it when we were attacked. "
            "I was afraid... and I left them behind. "
            "Please, return to the upper crypt "
            "and find the seal."
        )
    else:
        dialogue = (
            "Please, find the guild seal. "
            "It should still be near the remains "
            "of my group in the upper crypt."
        )

    game_state.trader_dialogue_text = dialogue
    game_state.trader_dialogue_started_at = (
        dialogue_started_at
    )
    game_state.trader_dialogue_dismiss_started_at = -1
    add_log_message(
        game_state.combat_log,
        f"Trader: {dialogue}",
        category="dialogue",
    )

    return "trader_meeting"


def buy_trader_item(game_state, slot_name):
    quest = game_state.act_two_quests.trader_seal

    if not quest.completed:
        add_log_message(
            game_state.combat_log,
            "The trader cannot trade without the guild seal.",
            category="warning",
        )
        return False
    item_id = DEFAULT_TRADER_STOCK.get(slot_name)

    if item_id is None:
        return False

    item = TRADER_ITEMS[item_id]
    player = game_state.player

    if player.gold_count < item.price:
        add_log_message(
            game_state.combat_log,
            "Not enough gold.",
            category="warning",
        )
        return False

    if not store_act_two_consumable(player, item.id):
        add_log_message(
            game_state.combat_log,
            "The consumable belt is full.",
            category="warning",
        )
        return False

    player.gold_count -= item.price

    add_log_message(
        game_state.combat_log,
        f"Purchased {item.name} for {item.price} gold.",
        category="trade",
    )
    return True
