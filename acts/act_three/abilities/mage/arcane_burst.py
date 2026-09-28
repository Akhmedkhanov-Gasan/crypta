from acts.act_three.settings import (
    MAGE_ARCANE_BURST_RANGE,
)
from logic import can_move_to, distance_between


def _living_oracle_pillar_at(
    floor,
    target,
):
    return any(
        enemy.type == "oracle_pillar"
        and enemy.health > 0
        and (enemy.column, enemy.row) == target
        for enemy in floor.enemies
    )


def is_valid_act_three_arcane_burst_target(
    game_state,
    target: tuple[int, int] | None,
) -> bool:
    if target is None:
        return False

    floor = game_state.floor
    target_is_pillar = _living_oracle_pillar_at(
        floor,
        target,
    )

    return (
        target in floor.visible_cells
        and (
            can_move_to(
                floor.map,
                target[0],
                target[1],
            )
            or target_is_pillar
        )
        and distance_between(
            floor.player_column,
            floor.player_row,
            target[0],
            target[1],
        )
        <= MAGE_ARCANE_BURST_RANGE
    )
