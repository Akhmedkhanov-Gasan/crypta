import random

from acts.act_two.consumables import (
    POTION,
    act_two_belt_is_full,
    store_act_two_consumable,
)
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
    crate.loot_available = crate.loot_kind is not None
    crate.loot_fire_turns_remaining = (
        2
        if cause == "fire_bomb" and crate.loot_available
        else None
    )

    position = (crate.column, crate.row)
    if cause == "fire_bomb":
        game_state.emit(
            GameEvent(
                type=GameEventType.ENVIRONMENT,
                actor="fire",
                origin=position,
                positions=(position,),
                data={"kind": "chest_break", "cause": "fire_bomb"},
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
    else:
        loot_message = None
    if cause == "fire_bomb":
        message = "The fire bomb destroys the crate"
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
    if (
        loot_kind == "potion"
        and act_two_belt_is_full(game_state.player)
    ):
        add_log_message(
            game_state.combat_log,
            "The consumable belt is full.",
            category="warning",
        )
        return None

    crate.loot_available = False
    crate.loot_fire_turns_remaining = None
    if loot_kind == "potion":
        store_act_two_consumable(game_state.player, POTION)
    elif loot_kind == "gold":
        game_state.player.gold_count += 1
        game_state.run_stats.gold_earned += 1
    return loot_kind


def advance_burning_crate_loot(
    game_state: GameState,
    burning_cells: set[tuple[int, int]],
) -> None:
    for crate in game_state.floor.breakable_crates:
        position = (crate.column, crate.row)
        if (
            not crate.loot_available
            or crate.loot_fire_turns_remaining is None
            or position not in burning_cells
        ):
            continue
        crate.loot_fire_turns_remaining -= 1
        if crate.loot_fire_turns_remaining > 0:
            continue
        burned_loot = crate.loot_kind
        crate.loot_available = False
        crate.loot_fire_turns_remaining = None
        game_state.emit(
            GameEvent(
                type=GameEventType.ENVIRONMENT,
                actor="fire",
                destination=position,
                data={"kind": "loot_burned", "loot": burned_loot},
            )
        )
        add_log_message(
            game_state.combat_log,
            (
                "The dropped potion burns away."
                if burned_loot == "potion"
                else "The dropped gold is lost in the fire."
            ),
            category="environment",
        )


__all__ = [
    "advance_burning_crate_loot",
    "break_crate",
    "collect_crate_loot",
]
