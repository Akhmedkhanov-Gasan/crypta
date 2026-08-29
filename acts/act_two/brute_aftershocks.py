from acts.act_two.state import (
    BruteAftershockPhase,
    BruteAftershockState,
)
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import GameState
from systems.player_combat import damage_player


BRUTE_AFTERSHOCK_DAMAGE = 1


def create_brute_aftershocks_from_events(
    game_state: GameState,
) -> None:
    existing_cells = {
        position
        for aftershock in game_state.floor.brute_aftershocks
        for position in aftershock.cells
    }

    for event in game_state.events:
        if (
            event.type is not GameEventType.ATTACK
            or event.data.get("enemy_type") != "brute"
            or event.data.get("mode") != "cleave"
        ):
            continue

        new_cells = tuple(
            position
            for position in event.positions
            if position not in existing_cells
        )

        if not new_cells:
            continue

        game_state.floor.brute_aftershocks.append(
            BruteAftershockState(
                cells=new_cells,
                source_name=event.actor,
            )
        )
        existing_cells.update(new_cells)

        add_log_message(
            game_state.combat_log,
            (
                f"{event.actor}'s blow fractures "
                "the ground."
            ),
        )


def _damage_player_with_aftershock(
    game_state: GameState,
    erupting_cells: set[tuple[int, int]],
) -> None:
    floor = game_state.floor
    player = game_state.player
    player_position = (
        floor.player_column,
        floor.player_row,
    )

    if (
        player.health <= 0
        or player_position not in erupting_cells
    ):
        return

    damage = damage_player(
        game_state,
        BRUTE_AFTERSHOCK_DAMAGE,
        damage_kind="physical",
    )

    if damage <= 0:
        return

    game_state.emit(
        GameEvent(
            type=GameEventType.HIT,
            actor="brute aftershock",
            target="hero",
            origin=player_position,
            destination=player_position,
            amount=damage,
            data={
                "kind": "brute_aftershock",
            },
        )
    )

    add_log_message(
        game_state.combat_log,
        (
            f"The ruptured ground hits hero "
            f"for {damage}."
        ),
    )

    if player.invisibility_turns > 0:
        player.invisibility_turns = 0
        add_log_message(
            game_state.combat_log,
            "The rogue becomes visible after taking damage.",
        )

    if player.health <= 0:
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor="hero",
                destination=player_position,
                data={
                    "cause": "brute aftershock",
                },
            )
        )
        add_log_message(
            game_state.combat_log,
            "The hero has fallen.",
        )


def advance_brute_aftershocks(
    game_state: GameState,
) -> None:
    active_aftershocks = []
    erupting_cells: set[tuple[int, int]] = set()

    for aftershock in game_state.floor.brute_aftershocks:
        if (
            aftershock.phase
            is BruteAftershockPhase.ERUPTING
        ):
            continue

        aftershock.phase = (
            BruteAftershockPhase.ERUPTING
        )
        erupting_cells.update(aftershock.cells)
        active_aftershocks.append(aftershock)

    game_state.floor.brute_aftershocks = (
        active_aftershocks
    )

    if not erupting_cells:
        return

    game_state.emit(
        GameEvent(
            type=GameEventType.ENVIRONMENT,
            actor="brute aftershock",
            positions=tuple(erupting_cells),
            data={
                "kind": "brute_aftershock",
            },
        )
    )

    _damage_player_with_aftershock(
        game_state,
        erupting_cells,
    )


__all__ = [
    "advance_brute_aftershocks",
    "create_brute_aftershocks_from_events",
]
