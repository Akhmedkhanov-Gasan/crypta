from acts.act_two.state import BruteAftershockPhase


def player_attack_warnings(game_state):
    floor = game_state.floor
    position = (floor.player_column, floor.player_row)

    warnings = [
        enemy.attack_targets
        for enemy in floor.enemies
        if enemy.health > 0
        and position in enemy.attack_targets
    ]
    warnings.extend(
        aftershock
        for aftershock in floor.brute_aftershocks
        if aftershock.phase is BruteAftershockPhase.WARNING
        and position in aftershock.cells
    )

    oracle = floor.oracle_combat
    if (
        oracle is not None
        and oracle.caster.health > 0
        and oracle.phase == "warning"
        and position in oracle.cells
    ):
        warnings.append(oracle.cells)

    oracle_phase_two = floor.oracle_phase_two
    if (
        oracle_phase_two is not None
        and oracle_phase_two.caster.health > 0
    ):
        warnings.extend(
            cells
            for cells in (
                oracle_phase_two.primary_cells,
                oracle_phase_two.secondary_cells,
                oracle_phase_two.chaos_cells,
            )
            if position in cells
        )

    return tuple(warnings)
