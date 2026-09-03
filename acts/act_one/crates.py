import random

from levels import ACT_ONE_CRATE_POTION_CHANCE
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import PotionState


def break_act_one_crate(game_state, crate):
    if crate.is_broken:
        return False

    if crate.loot_kind is None:
        crate.loot_kind = (
            "potion"
            if random.random() < ACT_ONE_CRATE_POTION_CHANCE
            else None
        )

    crate.is_broken = True
    crate.loot_available = False
    game_state.run_stats.crates_broken += 1
    position = (crate.column, crate.row)

    game_state.player_attack_targets = [position]
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(
                game_state.floor.player_column,
                game_state.floor.player_row,
            ),
            positions=(position,),
            data={"kind": "breakable_crate"},
        )
    )

    if crate.loot_kind == "potion":
        game_state.floor.potions.append(
            PotionState(
                column=crate.column,
                row=crate.row,
            )
        )
        message = "The crate breaks. A healing potion falls out."
    else:
        message = "The crate breaks. It is empty."

    add_log_message(
        game_state.combat_log,
        message,
        category="loot",
    )

    return True
