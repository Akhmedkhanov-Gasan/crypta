from acts.act_two.consumables import (
    POTION,
    act_two_belt_is_full,
    store_act_two_consumable,
)
from acts.crates import break_crate
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import GameState


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
