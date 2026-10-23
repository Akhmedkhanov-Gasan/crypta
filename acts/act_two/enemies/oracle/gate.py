from acts.act_two.presentation.bosses.oracle_intro import (
    start_oracle_intro,
)


def update_oracle_gate(floor, current_time):
    if not floor.has_oracle_gate:
        return

    living_boss_exists = any(
        enemy.boss_group and enemy.health > 0
        for enemy in floor.enemies
    )

    if not living_boss_exists:
        floor.oracle_gate_opened = True
        floor.oracle_gate_opening_started_at = -1


def oracle_gate_allows_entry(game_state, current_time):
    floor = game_state.floor

    if not floor.has_oracle_gate:
        return True

    living_boss_exists = any(
        enemy.boss_group and enemy.health > 0
        for enemy in floor.enemies
    )

    if not living_boss_exists:
        return True

    if floor.oracle_intro is None:
        start_oracle_intro(game_state, current_time)
        return False

    return (
        floor.oracle_intro.finished
        and floor.oracle_gate_opened
    )
