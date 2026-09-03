ACT_TWO_CONSOLE_HELP = (
    "seal     - give the trader's guild seal (Act II)",
    "rune     - open rune selection (Act II)",
    "altar    - open the bloody altar (Act II)",
    "trade    - open trading (Act II)",
)


def execute_act_two_console_command(
    game_state,
    parts,
    close_console,
):
    name = parts[0]

    if name not in ("seal", "rune", "altar", "trade"):
        return None

    if len(parts) != 1:
        return f"Usage: {name}"

    if game_state.floor.presentation_act != 2:
        return "This command is only available in Act II."

    if name == "seal":
        return _give_guild_seal(game_state)

    if name == "rune":
        return _open_rune_selection(game_state, close_console)

    if name == "altar":
        return _open_bloody_altar(game_state, close_console)

    return _open_trade(game_state, close_console)

def _give_guild_seal(game_state):
    from acts.act_two.consumables import (
        GUILD_SEAL,
        get_act_two_consumable_slots,
        store_act_two_consumable,
    )

    player = game_state.player
    quest = game_state.act_two_quests.trader_seal

    if quest.completed:
        return "The trader's seal quest is already completed."

    if (
        quest.seal_recovered
        or GUILD_SEAL in get_act_two_consumable_slots(player)
    ):
        return "The guild seal has already been recovered."

    if not store_act_two_consumable(player, GUILD_SEAL):
        return "The consumable belt is full. Make room for the seal."

    quest.seal_recovered = True

    return "Guild seal added to the belt. Return it to the trader."


def _open_rune_selection(game_state, close_console):
    from game.rune_catalog import runes_for_class

    player = game_state.player

    if not runes_for_class(player.player_class):
        return "Choose an Act II class before selecting a rune."

    if (
        game_state.rune_selection_open
        or game_state.bloody_altar_open
        or game_state.trade_screen_open
        or game_state.upgrade_screen_open
        or game_state.class_selection_open
        or game_state.subclass_selection_open
    ):
        return "Close the current selection or trade window first."

    if (
        player.directional_ability_aiming
        or player.act_two.fire_bomb_aiming
        or player.act_two.scroll_aiming_kind is not None
    ):
        return "Finish or cancel aiming before selecting a rune."

    player.act_two.rune_selection_from_console = True
    game_state.rune_selection_pending_id = None
    game_state.rune_selection_open = True
    game_state.player_attack_targets = []

    close_console()

    return "Rune selection opened."


def _open_bloody_altar(game_state, close_console):
    player = game_state.player

    if (
        game_state.rune_selection_open
        or game_state.bloody_altar_open
        or game_state.trade_screen_open
        or game_state.upgrade_screen_open
        or game_state.class_selection_open
        or game_state.subclass_selection_open
    ):
        return "Close the current selection or trade window first."

    if (
        player.directional_ability_aiming
        or player.act_two.fire_bomb_aiming
        or player.act_two.scroll_aiming_kind is not None
    ):
        return "Finish or cancel aiming before opening the altar."

    player.act_two.bloody_altar_from_console = True
    game_state.bloody_altar_pending_id = None
    game_state.bloody_altar_open = True
    game_state.player_attack_targets = []

    close_console()

    return "Bloody altar opened."


def _open_trade(game_state, close_console):
    player = game_state.player

    if (
        game_state.rune_selection_open
        or game_state.bloody_altar_open
        or game_state.trade_screen_open
        or game_state.upgrade_screen_open
        or game_state.class_selection_open
        or game_state.subclass_selection_open
    ):
        return "Close the current selection or trade window first."

    if (
        player.directional_ability_aiming
        or player.act_two.fire_bomb_aiming
        or player.act_two.scroll_aiming_kind is not None
    ):
        return "Finish or cancel aiming before opening trading."

    player.act_two.trade_from_console = True
    game_state.trade_screen_open = True
    game_state.player_attack_targets = []
    game_state.trader_dialogue_text = ""
    game_state.trader_dialogue_started_at = -1
    game_state.trader_dialogue_dismiss_started_at = -1

    close_console()

    return "Trading opened."
