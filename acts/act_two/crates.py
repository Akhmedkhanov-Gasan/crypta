import random

from acts.act_two.settings import (
    BREAKABLE_CRATE_EMPTY_CHANCE,
    BREAKABLE_CRATE_GOLD_CHANCE,
    BREAKABLE_CRATE_POTION_CHANCE,
)
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import BreakableCrateState, GameState


def break_crate(
    game_state: GameState,
    crate: BreakableCrateState,
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
    crate.loot_available = crate.loot_kind is not None

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
    if crate.loot_kind == "gold":
        message = "Hero smashes the crate: a gold coin falls out."
    elif crate.loot_kind == "potion":
        message = "Hero smashes the crate: a healing potion falls out."
    else:
        message = "Hero smashes the crate. It is empty."
    add_log_message(game_state.combat_log, message)
    return True


def collect_crate_loot(
    game_state: GameState,
    position: tuple[int, int],
) -> str | None:
    crate = next(
        (
            candidate
            for candidate in game_state.floor.breakable_crates
            if (
                candidate.is_broken
                and candidate.loot_available
                and (candidate.column, candidate.row) == position
            )
        ),
        None,
    )
    if crate is None:
        return None

    loot_kind = crate.loot_kind
    crate.loot_available = False
    if loot_kind == "potion":
        game_state.player.potion_count += 1
    elif loot_kind == "gold":
        game_state.player.gold_count += 1
    return loot_kind


__all__ = ["break_crate", "collect_crate_loot"]
