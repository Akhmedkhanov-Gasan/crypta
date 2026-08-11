from acts.act_two.state import TreasuryTrialPhase
from acts.act_two.progression import purchase_act_two_upgrade
from enemies import ENEMY_TYPES
from game.combat_log import add_log_message
from game.state import EnemyBehaviorState, EnemyState, GameState


TREASURY_CHEST_TILE = "H"
TREASURY_GATE_TILE = "G"
TREASURY_REWARD_TILE = "R"


def _set_floor_tile(
    game_state: GameState,
    position: tuple[int, int],
    tile: str,
) -> None:
    column, row = position
    map_row = game_state.floor.map[row]
    game_state.floor.map[row] = (
        map_row[:column] + tile + map_row[column + 1 :]
    )


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

    game_state.player_attack_targets = []
    add_log_message(
        game_state.combat_log,
        "The treasury gate slams shut. Four guardians awaken.",
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
    add_log_message(
        game_state.combat_log,
        "The reliquary dissolves. A treasury blessing remains.",
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
    game_state.player.gold_count += 1
    game_state.upgrade_reward_pending = True
    game_state.upgrade_screen_open = True
    game_state.upgrade_message = "Choose one free attribute upgrade."
    game_state.player_attack_targets = []
    add_log_message(
        game_state.combat_log,
        "The hero claims the treasury blessing.",
    )
    return True


def purchase_treasury_reward_upgrade(
    game_state: GameState,
    upgrade: str,
) -> tuple[bool, str]:
    if not game_state.upgrade_reward_pending:
        return False, "No reward upgrade is pending."

    gold_before_purchase = game_state.player.gold_count
    message = purchase_act_two_upgrade(game_state.player, upgrade)
    upgraded = game_state.player.gold_count < gold_before_purchase
    if upgraded:
        game_state.upgrade_reward_pending = False
        game_state.upgrade_screen_open = False
    return upgraded, message


__all__ = [
    "activate_treasury_trial",
    "collect_treasury_reward",
    "purchase_treasury_reward_upgrade",
    "treasury_chest_is_at",
    "update_treasury_trial",
]
