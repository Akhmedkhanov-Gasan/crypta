from acts.act_three.ai.registry import (
    ACT_THREE_ENEMY_TURN_HANDLERS,
)


def resolve_enemy_turn(game_state, *args, **kwargs):
    from systems.enemy_turn import resolve_enemy_turn as shared_turn

    return shared_turn(
        game_state,
        *args,
        enemy_turn_handlers=ACT_THREE_ENEMY_TURN_HANDLERS,
        **kwargs,
    )
