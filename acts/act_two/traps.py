from acts.act_two.settings import SPIKE_TRAP_DAMAGE
from acts.act_two.state import SpikeTrapPhase
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState, GameState
from logic import get_enemy_occupied_positions
from systems.player_combat import damage_player, resolve_enemy_defeat


_NEXT_SPIKE_TRAP_PHASE = {
    SpikeTrapPhase.SAFE: SpikeTrapPhase.WARNING,
    SpikeTrapPhase.WARNING: SpikeTrapPhase.ACTIVE,
    SpikeTrapPhase.ACTIVE: SpikeTrapPhase.COOLDOWN,
    SpikeTrapPhase.COOLDOWN: SpikeTrapPhase.SAFE,
}


def _damage_player_on_trap(
    game_state: GameState,
    trap_position: tuple[int, int],
) -> None:
    floor = game_state.floor
    player = game_state.player
    if (
        player.health <= 0
        or (floor.player_column, floor.player_row) != trap_position
    ):
        return

    damage = damage_player(game_state, SPIKE_TRAP_DAMAGE)
    if damage <= 0:
        return

    game_state.emit(
        GameEvent(
            type=GameEventType.HIT,
            actor="floor spikes",
            target="hero",
            origin=trap_position,
            destination=trap_position,
            amount=damage,
            data={"kind": "spike_trap"},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"Floor spikes hit hero for {damage}.",
    )

    if player.invisibility_turns > 0:
        player.invisibility_turns = 0
        add_log_message(
            game_state.combat_log,
            "The rogue becomes visible after taking damage.",
        )

    if player.health <= 0:
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor="hero",
                destination=trap_position,
                data={"cause": "floor spikes"},
            )
        )
        add_log_message(
            game_state.combat_log,
            "The hero has fallen.",
        )


def _damage_enemies_on_trap(
    game_state: GameState,
    trap_position: tuple[int, int],
) -> None:
    for enemy in game_state.floor.enemies:
        if (
            enemy.health <= 0
            or trap_position not in get_enemy_occupied_positions(enemy)
        ):
            continue

        damage = min(SPIKE_TRAP_DAMAGE, enemy.health)
        enemy.health -= damage

        game_state.emit(
            GameEvent(
                type=GameEventType.HIT,
                actor="floor spikes",
                target=enemy.name,
                origin=trap_position,
                destination=(enemy.column, enemy.row),
                amount=damage,
                data={
                    "kind": "spike_trap",
                    "enemy_type": enemy.type,
                },
            )
        )
        add_log_message(
            game_state.combat_log,
            f"Floor spikes hit {enemy.name} for {damage}.",
        )

        if enemy.health > 0:
            continue

        enemy.behavior_state = EnemyBehaviorState.DEAD
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor=enemy.name,
                destination=(enemy.column, enemy.row),
                data={
                    "enemy_type": enemy.type,
                    "cause": "floor spikes",
                },
            )
        )
        add_log_message(
            game_state.combat_log,
            f"{enemy.name} is defeated by floor spikes.",
        )
        resolve_enemy_defeat(game_state, enemy)


def advance_spike_traps(game_state: GameState) -> None:
    for trap in game_state.floor.spike_traps:
        trap.phase = _NEXT_SPIKE_TRAP_PHASE[trap.phase]
        if trap.phase is not SpikeTrapPhase.ACTIVE:
            continue

        trap_position = (trap.column, trap.row)
        _damage_player_on_trap(game_state, trap_position)
        _damage_enemies_on_trap(game_state, trap_position)


__all__ = ["advance_spike_traps"]
