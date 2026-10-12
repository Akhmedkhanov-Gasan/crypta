import pygame

from acts.act_three.abilities.archer_barrage_zone import (
    ArcherBarrageTurnInterrupt,
    resolve_archer_barrage_hits,
)
from acts.act_three.ai.registry import (
    ACT_THREE_ENEMY_TURN_HANDLERS,
)
from acts.act_three.presentation.archer.barrage_zone import (
    BARRAGE_SHOT_MS,
)
from acts.act_three.state import ArcherBarrageTurnState
from game.events import GameEventType


def _shared_enemy_turn(game_state, turn, enemy_id, prelude, postlude):
    from systems.enemy_turn import resolve_enemy_turn as shared_turn

    return shared_turn(
        game_state,
        turn.player_position_before_action,
        turn.rogue_ability_activated,
        enemy_turn_handlers=ACT_THREE_ENEMY_TURN_HANDLERS,
        selected_enemy_id=enemy_id,
        run_prelude=prelude,
        run_postlude=postlude,
        initial_damaged_enemy_names=turn.damaged_enemy_names,
    )


def _advance_enemy_turn(game_state, turn):
    while turn.next_index < len(turn.enemy_ids):
        enemy_id = turn.enemy_ids[turn.next_index]
        turn.next_index += 1

        if not any(
            id(enemy) == enemy_id
            for enemy in game_state.floor.enemies
        ):
            continue

        try:
            _shared_enemy_turn(
                game_state,
                turn,
                enemy_id,
                not turn.prelude_done,
                False,
            )
        except ArcherBarrageTurnInterrupt:
            turn.prelude_done = True
            turn.ready_at = (
                pygame.time.get_ticks() + BARRAGE_SHOT_MS
            )
            game_state.act_three.barrage_turn = turn
            return

        turn.prelude_done = True
        if game_state.player.health <= 0:
            break

    _shared_enemy_turn(
        game_state,
        turn,
        -1,
        not turn.prelude_done,
        True,
    )
    game_state.act_three.barrage_turn = None


def resolve_enemy_turn(
    game_state,
    player_position_before_action,
    rogue_ability_activated,
):
    damaged_enemy_names = frozenset(
        event.target
        for event in game_state.events
        if (
            event.type is GameEventType.HIT
            and event.target is not None
            and event.amount is not None
            and event.amount > 0
        )
    )
    turn = ArcherBarrageTurnState(
        enemy_ids=tuple(
            id(enemy)
            for enemy in game_state.floor.enemies
        ),
        next_index=0,
        player_position_before_action=(
            player_position_before_action
        ),
        rogue_ability_activated=rogue_ability_activated,
        damaged_enemy_names=damaged_enemy_names,
    )

    if game_state.player.archer_barrage_pending_hits:
        turn.ready_at = (
            pygame.time.get_ticks() + BARRAGE_SHOT_MS
        )
        game_state.act_three.barrage_turn = turn
        return

    _advance_enemy_turn(game_state, turn)


def resume_barrage_turn(game_state):
    turn = game_state.act_three.barrage_turn
    if turn is None:
        return False

    resolve_archer_barrage_hits(game_state)
    game_state.act_three.barrage_turn = None

    if game_state.player.health > 0:
        _advance_enemy_turn(game_state, turn)

    return True
