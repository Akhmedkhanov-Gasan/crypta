import random

from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import BreakableCrateState, GameState

from acts.act_two.settings import (
    BREAKABLE_CRATE_EMPTY_CHANCE,
    BREAKABLE_CRATE_GOLD_CHANCE,
    BREAKABLE_CRATE_POTION_CHANCE,
)
from systems.enemy_spawning import try_spawn_crate_goblin


def break_crate(
    game_state: GameState,
    crate: BreakableCrateState,
    cause: str = "hero",
) -> bool:
    if crate.is_broken:
        return False

    roll = random.random()
    crate.is_broken = True
    if roll < BREAKABLE_CRATE_GOLD_CHANCE:
        crate.loot_kind = "gold"
    elif roll < (
        BREAKABLE_CRATE_GOLD_CHANCE
        + BREAKABLE_CRATE_POTION_CHANCE
    ):
        crate.loot_kind = "potion"
    elif roll < (
        BREAKABLE_CRATE_GOLD_CHANCE
        + BREAKABLE_CRATE_POTION_CHANCE
        + BREAKABLE_CRATE_EMPTY_CHANCE
    ):
        crate.loot_kind = None
    else:
        crate.loot_kind = None
    if cause == "shield_bash" and crate.loot_kind is None:
        crate.loot_kind = "potion"
    crate.loot_available = crate.loot_kind is not None
    crate.loot_fire_turns_remaining = (
        2
        if cause == "fire_bomb" and crate.loot_available
        else None
    )

    position = (crate.column, crate.row)
    if cause in ("fire_bomb", "shield_bash"):
        game_state.emit(
            GameEvent(
                type=GameEventType.ENVIRONMENT,
                actor="fire" if cause == "fire_bomb" else "hero",
                origin=position,
                positions=(position,),
                data={"kind": "chest_break", "cause": cause},
            )
        )
    else:
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
    if crate.loot_kind == "gold":
        loot_message = "a gold coin falls out"
    elif crate.loot_kind == "potion":
        loot_message = "a healing potion falls out"
    elif try_spawn_crate_goblin(game_state, crate):
        loot_message = "a goblin jumps out"
    else:
        loot_message = None
    if cause == "fire_bomb":
        message = "The fire bomb destroys the crate"
    elif cause == "shield_bash":
        message = "The hero crashes through the crate"
    else:
        message = "Hero smashes the crate"
    if loot_message is not None:
        message = f"{message}: {loot_message}."
    else:
        message = f"{message}. It is empty."
    add_log_message(
        game_state.combat_log,
        message,
        category="neutral",
    )
    return True


__all__ = ["break_crate"]
