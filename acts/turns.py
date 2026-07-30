from collections.abc import Callable

from acts.act_one.turns import (
    resolve_enemy_turn as resolve_act_one_enemy_turn,
)
from acts.act_three.turns import (
    resolve_enemy_turn as resolve_act_three_enemy_turn,
)
from acts.act_two.turns import (
    resolve_enemy_turn as resolve_act_two_enemy_turn,
)
from levels import FLOOR_CONFIGS


TurnResolver = Callable[..., None]

_TURN_RESOLVERS: dict[int, TurnResolver] = {
    1: resolve_act_one_enemy_turn,
    2: resolve_act_two_enemy_turn,
    3: resolve_act_three_enemy_turn,
}


def resolve_enemy_turn(game_state, *args, **kwargs):
    act_number = FLOOR_CONFIGS[game_state.floor_index]["act"]

    try:
        resolver = _TURN_RESOLVERS[act_number]
    except KeyError as error:
        raise ValueError(
            f"No turn resolver registered for Act {act_number}."
        ) from error

    return resolver(game_state, *args, **kwargs)
