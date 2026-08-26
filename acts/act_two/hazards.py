from acts.act_two.state import SpikeTrapPhase
from game.state import GameState


FIRE_HAZARD_COST = 5
SPIKE_HAZARD_COST = 8


def get_act_two_enemy_hazard_costs(
    game_state: GameState,
) -> dict[tuple[int, int], int]:
    costs: dict[tuple[int, int], int] = {}

    for zone in game_state.floor.fire_zones:
        for position in zone.cells:
            costs[position] = max(
                costs.get(position, 0),
                FIRE_HAZARD_COST,
            )

    for trap in game_state.floor.spike_traps:
        if trap.phase is not SpikeTrapPhase.WARNING:
            continue

        position = (trap.column, trap.row)
        costs[position] = max(
            costs.get(position, 0),
            SPIKE_HAZARD_COST,
        )

    return costs
