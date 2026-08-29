from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from acts.act_two.consumables import (
    GUILD_SEAL,
    store_act_two_consumable,
)


def collect_guild_seal(
    game_state,
    player_position,
):
    revisit_state = (
        game_state.floor.act_one_revisit
    )

    if (
        revisit_state is None
        or revisit_state.guild_seal_position
        != player_position
    ):
        return False

    quest = game_state.act_two_quests.trader_seal

    if quest.completed:
        revisit_state.guild_seal_position = None
        return False

    if not store_act_two_consumable(
            game_state.player,
            GUILD_SEAL,
    ):
        add_log_message(
            game_state.combat_log,
            (
                "The consumable belt is full. "
                "Make room for the guild seal."
            ),
            category="warning",
        )
        return False

    quest.seal_recovered = True
    revisit_state.guild_seal_position = None

    game_state.emit(
        GameEvent(
            type=GameEventType.PICKUP,
            actor="hero",
            destination=player_position,
            data={"kind": "guild_seal"},
        )
    )

    add_log_message(
        game_state.combat_log,
        "The hero recovers the lost guild seal.",
        category="quest",
    )

    if quest.started:
        add_log_message(
            game_state.combat_log,
            "The trader will want this returned.",
            category="quest",
        )
    else:
        add_log_message(
            game_state.combat_log,
            (
                "The seal bears the mark "
                "of a merchant guild."
            ),
            category="quest",
        )

    return True


__all__ = ["collect_guild_seal"]
