from acts.act_two.state import RunePuzzlePhase
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import GameState


def rune_wall_is_at(
    game_state: GameState,
    position: tuple[int, int],
) -> bool:
    room = game_state.floor.rune_room
    return bool(room is not None and position in room.wall_rune_positions)


def strike_wall_rune(
    game_state: GameState,
    position: tuple[int, int],
    current_time: int | None = None,
) -> bool:
    room = game_state.floor.rune_room
    if room is None or position not in room.wall_rune_positions:
        return False

    rune_index = room.wall_rune_positions.index(position)
    rune_activated = rune_index not in room.activated_runes
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(
                game_state.floor.player_column,
                game_state.floor.player_row,
            ),
            positions=(position,),
            data={
                "kind": "wall_rune",
                "rune_index": rune_index,
                "activated": rune_activated,
            },
        )
    )
    if not rune_activated:
        add_log_message(
            game_state.combat_log,
            "This wall rune is already awake.",
        )
        return True

    room.activated_runes.add(rune_index)
    if current_time is not None:
        room.activation_effect_started_at[rune_index] = current_time
    remaining = len(room.wall_rune_positions) - len(room.activated_runes)
    if remaining > 0:
        add_log_message(
            game_state.combat_log,
            f"A wall rune awakens. {remaining} remain.",
        )
    else:
        room.phase = RunePuzzlePhase.REWARD_AVAILABLE
        add_log_message(
            game_state.combat_log,
            "The third rune awakens. A blessing forms on the pedestal.",
        )
    return True


def rune_pedestal_is_at(
    game_state: GameState,
    position: tuple[int, int],
) -> bool:
    room = game_state.floor.rune_room
    return bool(room is not None and position == room.pedestal_position)


def interact_with_rune_pedestal(game_state: GameState) -> bool:
    room = game_state.floor.rune_room
    if room is None:
        return False

    if room.phase is RunePuzzlePhase.DORMANT:
        remaining = len(room.wall_rune_positions) - len(room.activated_runes)
        add_log_message(
            game_state.combat_log,
            f"The pedestal is empty. {remaining} runes remain dormant.",
        )
        return True

    if room.phase is RunePuzzlePhase.CLAIMED:
        return False

    room.phase = RunePuzzlePhase.CLAIMED
    game_state.player.gold_count += 2
    game_state.player_attack_targets = []
    game_state.emit(
        GameEvent(
            type=GameEventType.ENVIRONMENT,
            actor="rune reward",
            origin=room.pedestal_position,
            data={"kind": "room_reward"},
        )
    )
    add_log_message(
        game_state.combat_log,
        "The rune pedestal yields an ancient coin.",
    )
    return True


__all__ = [
    "interact_with_rune_pedestal",
    "rune_pedestal_is_at",
    "rune_wall_is_at",
    "strike_wall_rune",
]
