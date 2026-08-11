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
) -> bool:
    room = game_state.floor.rune_room
    if room is None or position not in room.wall_rune_positions:
        return False

    rune_index = room.wall_rune_positions.index(position)
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(
                game_state.floor.player_column,
                game_state.floor.player_row,
            ),
            positions=(position,),
            data={"kind": "wall_rune", "rune_index": rune_index},
        )
    )
    if rune_index in room.activated_runes:
        add_log_message(
            game_state.combat_log,
            "This wall rune is already awake.",
        )
        return True

    room.activated_runes.add(rune_index)
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
    game_state.player.gold_count += 1
    game_state.upgrade_reward_pending = True
    game_state.upgrade_screen_open = True
    game_state.upgrade_message = "Choose one attribute upgrade."
    game_state.player_attack_targets = []
    add_log_message(
        game_state.combat_log,
        "The hero claims the rune pedestal blessing.",
    )
    return True


__all__ = [
    "interact_with_rune_pedestal",
    "rune_pedestal_is_at",
    "rune_wall_is_at",
    "strike_wall_rune",
]
