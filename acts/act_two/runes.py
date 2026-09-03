from game.rune_catalog import RUNES_BY_ID, runes_for_class
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
            category="rune",
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
            category="rune",
        )
    else:
        room.phase = RunePuzzlePhase.REWARD_AVAILABLE
        add_log_message(
            game_state.combat_log,
            "The third rune awakens. A blessing forms on the pedestal.",
            category="rune",
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
            category="warning",
        )
        return True

    if room.phase is RunePuzzlePhase.CLAIMED:
        selected_rune = RUNES_BY_ID.get(
            game_state.player.selected_rune_id
        )
        add_log_message(
            game_state.combat_log,
            (
                f"The pedestal bears {selected_rune.name}."
                if selected_rune is not None
                else "The pedestal's blessing has already been claimed."
            ),
            category="rune",
        )
        return True

    available_runes = runes_for_class(game_state.player.player_class)
    if not available_runes:
        add_log_message(
            game_state.combat_log,
            "The pedestal does not answer an unbound soul.",
            category="warning",
        )
        return True

    if game_state.rune_selection_open:
        return True

    game_state.rune_selection_open = True
    game_state.rune_selection_pending_id = None
    game_state.player_attack_targets = []
    game_state.emit(
        GameEvent(
            type=GameEventType.ENVIRONMENT,
            actor="rune pedestal",
            origin=room.pedestal_position,
            data={
                "kind": "rune_selection_opened",
                "rune_ids": tuple(rune.id for rune in available_runes),
            },
        )
    )
    add_log_message(
        game_state.combat_log,
        "The pedestal offers three runes. Choose one blessing.",
        category="rune",
    )
    return True


def select_rune(game_state: GameState, rune_id: str) -> bool:
    player = game_state.player
    room = game_state.floor.rune_room
    rune = RUNES_BY_ID.get(rune_id)
    from_console = player.act_two.rune_selection_from_console

    if (
        not game_state.rune_selection_open
        or rune is None
        or rune.player_class != player.player_class
    ):
        return False

    if from_console:
        if game_state.floor.presentation_act != 2:
            return False
    elif (
        room is None
        or room.phase is not RunePuzzlePhase.REWARD_AVAILABLE
        or player.selected_rune_id is not None
    ):
        return False

    player.selected_rune_id = rune.id

    if from_console or rune.id in (
        "rune_of_resonance",
        "rune_of_impact",
    ):
        player.ability_kill_charge = 0
        player.directional_ability_aiming = False
        player.act_two.selected_ability_direction = None
        game_state.player_attack_targets = []

    if from_console or rune.id == "rune_of_the_veil":
        player.ability_kill_charge = 0
        player.invisibility_turns = 0
        player.veil_triggered_this_turn = False

    if from_console:
        actor = "console"
        origin = (
            game_state.floor.player_column,
            game_state.floor.player_row,
        )
    else:
        actor = "rune pedestal"
        origin = room.pedestal_position
        room.phase = RunePuzzlePhase.CLAIMED

    cancel_rune_selection(game_state)

    game_state.emit(
        GameEvent(
            type=GameEventType.ENVIRONMENT,
            actor=actor,
            origin=origin,
            data={
                "kind": "rune_selected",
                "rune_id": rune.id,
                "player_class": rune.player_class,
            },
        )
    )
    add_log_message(
        game_state.combat_log,
        f"The hero binds {rune.name}.",
        category="rune",
    )
    return True


def cancel_rune_selection(game_state: GameState) -> None:
    game_state.rune_selection_open = False
    game_state.rune_selection_pending_id = None
    game_state.player.act_two.rune_selection_from_console = False


__all__ = [
    "cancel_rune_selection",
    "interact_with_rune_pedestal",
    "rune_pedestal_is_at",
    "rune_wall_is_at",
    "select_rune",
    "strike_wall_rune",
]
