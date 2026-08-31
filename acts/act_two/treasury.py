from acts.act_two.state import TreasuryTrialPhase
from enemies import ENEMY_TYPES
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import (
    EnemyBehaviorState,
    EnemyState,
    GameState,
    TraderState,
)


TREASURY_CHEST_TILE = "H"
TREASURY_GATE_TILE = "G"
TREASURY_REWARD_TILE = "R"


def _set_floor_state_tile(
    floor,
    position: tuple[int, int],
    tile: str,
) -> None:
    column, row = position
    map_row = floor.map[row]
    floor.map[row] = (
        map_row[:column] + tile + map_row[column + 1 :]
    )


def _set_floor_tile(
    game_state: GameState,
    position: tuple[int, int],
    tile: str,
) -> None:
    _set_floor_state_tile(
        game_state.floor,
        position,
        tile,
    )

def _treasury_trader_position(
    treasury,
) -> tuple[int, int]:
    door_column, door_row = treasury.door_position

    if door_row < treasury.y:
        return door_column + 1, treasury.y

    if door_row >= treasury.y + treasury.height:
        return (
            door_column + 1,
            treasury.y + treasury.height - 1,
        )

    if door_column < treasury.x:
        return treasury.x, door_row + 1

    return (
        treasury.x + treasury.width - 1,
        door_row + 1,
    )


def _relocate_quest_trader(game_state: GameState) -> None:
    source_floor_index = game_state.act_two_trader_floor_index

    if source_floor_index is not None:
        source_floor = game_state.visited_floors.get(
            source_floor_index
        )

        if (
            source_floor is not None
            and source_floor.quest_trader is not None
        ):
            old_trader = source_floor.quest_trader
            old_position = (
                old_trader.column,
                old_trader.row,
            )

            if (
                source_floor.map[old_position[1]][old_position[0]]
                == "M"
            ):
                _set_floor_state_tile(
                    source_floor,
                    old_position,
                    ".",
                )

            source_floor.quest_trader = None

    treasury = game_state.floor.treasury_room
    trader_position = _treasury_trader_position(treasury)

    game_state.floor.quest_trader = TraderState(
        column=trader_position[0],
        row=trader_position[1],
    )
    _set_floor_state_tile(
        game_state.floor,
        trader_position,
        "M",
    )

    game_state.act_two_trader_floor_index = game_state.floor_index


def treasury_chest_is_at(
    game_state: GameState,
    position: tuple[int, int],
) -> bool:
    treasury = game_state.floor.treasury_room
    return bool(
        treasury is not None
        and treasury.phase in (
            TreasuryTrialPhase.DORMANT,
            TreasuryTrialPhase.ACTIVE,
        )
        and position == treasury.chest_position
    )


def _next_enemy_name(game_state: GameState, enemy_type: str) -> str:
    display_name = ENEMY_TYPES[enemy_type]["display_name"]
    existing_count = sum(
        enemy.type == enemy_type
        for enemy in game_state.floor.enemies
    )
    return f"{display_name} {existing_count + 1}"


def _spawn_trial_enemy(
    game_state: GameState,
    enemy_type: str,
    position: tuple[int, int],
) -> EnemyState:
    treasury = game_state.floor.treasury_room
    enemy = EnemyState.from_config(
        enemy_type=enemy_type,
        column=position[0],
        row=position[1],
        name=_next_enemy_name(game_state, enemy_type),
        config=ENEMY_TYPES[enemy_type],
        belongs_to_boss_group=False,
    )
    enemy.treasury_trial_enemy = True
    enemy.is_aggro = True
    enemy.behavior_state = EnemyBehaviorState.CHASING
    enemy.movement_bounds = (
        treasury.x,
        treasury.y,
        treasury.x + treasury.width - 1,
        treasury.y + treasury.height - 1,
    )
    game_state.floor.enemies.append(enemy)
    return enemy


def activate_treasury_trial(game_state: GameState) -> bool:
    treasury = game_state.floor.treasury_room
    if treasury is None:
        return False

    if treasury.phase is TreasuryTrialPhase.ACTIVE:
        add_log_message(
            game_state.combat_log,
            "The sealed reliquary will not open while its guardians live.",
            category="warning",
        )
        return True

    if treasury.phase is not TreasuryTrialPhase.DORMANT:
        return False

    treasury.phase = TreasuryTrialPhase.ACTIVE
    _set_floor_tile(
        game_state,
        treasury.door_position,
        TREASURY_GATE_TILE,
    )
    enemy_types = ("archer", "archer", "brute", "brute")
    for enemy_type, spawn_position in zip(
        enemy_types,
        treasury.enemy_spawn_positions,
    ):
        _spawn_trial_enemy(game_state, enemy_type, spawn_position)

    game_state.emit(
        GameEvent(
            type=GameEventType.ENVIRONMENT,
            actor="treasury",
            origin=treasury.chest_position,
            data={"kind": "treasury_trap_activate"},
        )
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.ENVIRONMENT,
            actor="treasury gate",
            origin=treasury.door_position,
            data={"kind": "portcullis_lock"},
        )
    )

    game_state.player_attack_targets = []
    add_log_message(
        game_state.combat_log,
        "The treasury gate slams shut. Four guardians awaken.",
        category="warning",
    )
    return True


def update_treasury_trial(game_state: GameState) -> bool:
    treasury = game_state.floor.treasury_room
    if (
        treasury is None
        or treasury.phase is not TreasuryTrialPhase.ACTIVE
    ):
        return False

    trial_enemies = [
        enemy
        for enemy in game_state.floor.enemies
        if enemy.treasury_trial_enemy
    ]
    if any(enemy.health > 0 for enemy in trial_enemies):
        return False

    treasury.phase = TreasuryTrialPhase.REWARD_AVAILABLE
    _set_floor_tile(game_state, treasury.door_position, ".")
    _set_floor_tile(
        game_state,
        treasury.chest_position,
        TREASURY_REWARD_TILE,
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.ENVIRONMENT,
            actor="treasury gate",
            origin=treasury.door_position,
            data={"kind": "portcullis_unlock"},
        )
    )
    add_log_message(
        game_state.combat_log,
        "The reliquary dissolves. A treasury blessing remains.",
        category="loot",
    )
    return True


def collect_treasury_reward(
    game_state: GameState,
    position: tuple[int, int],
) -> bool:
    treasury = game_state.floor.treasury_room
    if not (
        treasury is not None
        and treasury.phase is TreasuryTrialPhase.REWARD_AVAILABLE
        and position == treasury.chest_position
    ):
        return False

    treasury.phase = TreasuryTrialPhase.CLAIMED
    game_state.player.gold_count += 10
    game_state.run_stats.gold_earned += 10
    game_state.run_stats.chests_opened += 1
    game_state.player_attack_targets = []

    _relocate_quest_trader(game_state)

    game_state.emit(
        GameEvent(
            type=GameEventType.ENVIRONMENT,
            actor="treasury reward",
            origin=position,
            data={"kind": "room_reward"},
        )
    )
    add_log_message(
        game_state.combat_log,
        "The hero claims ten treasury coins.",
        category="loot",
    )
    add_log_message(
        game_state.combat_log,
        (
            "Trader: Ah, you found the treasury. "
            "Let me help you lighten that burden."
        ),
        category="dialogue",
    )
    return True


__all__ = [
    "activate_treasury_trial",
    "collect_treasury_reward",
    "treasury_chest_is_at",
    "update_treasury_trial",
]
