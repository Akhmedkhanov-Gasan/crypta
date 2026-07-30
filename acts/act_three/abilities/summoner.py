from collections.abc import Callable

from game.combat_log import add_log_message
from acts.act_three.events import GameEvent, GameEventType
from game.state import (
    EnemyState,
    FloorState,
    GameState,
)
from logic import (
    can_move_to,
    distance_between,
    get_enemy_occupied_positions,
    move_enemy_toward_position,
)
from settings import (
    SUMMONER_FAMILIAR_CHARGES,
    SUMMONER_BOND_CHARGES,
    SUMMONER_TRUE_FORM_CHARGES,
    SUMMONER_TRUE_FORM_HEALTH_BONUS,
)
from systems.player_combat import (
    attack_enemy,
    resolve_enemy_defeat,
)


OracleHitReaction = Callable[
    [EnemyState, FloorState, list[str]],
    None,
]

def release_summoner_familiar(game_state: GameState) -> bool:
    player = game_state.player
    if player.subclass != "summoner":
        return False

    if player.summoner_familiar_active:
        if player.summoner_bond_active:
            break_summoner_bond(game_state)
        player.summoner_true_form_active = False
        if player.summoner_familiar_health > 0:
            health_ratio = (
                player.summoner_familiar_health
                / player.summoner_familiar_max_health
            )
            player.summoner_familiar_charge = (
                SUMMONER_FAMILIAR_CHARGES * health_ratio
            )
            player.summoner_familiar_active = False
            player.summoner_familiar_position = None
            player.summoner_familiar_movement_origin = None
            add_log_message(
                game_state.combat_log,
                "The familiar returns to its master.",
            )
            return True
        add_log_message(
            game_state.combat_log,
            "The familiar is already released.",
        )
        return True

    if player.summoner_familiar_charge < SUMMONER_FAMILIAR_CHARGES:
        add_log_message(
            game_state.combat_log,
            "The familiar is not charged yet.",
        )
        return True

    player.summoner_familiar_charge = 0.0
    player.summoner_familiar_death_penalty = False
    player.summoner_true_form_active = False
    player.summoner_true_form_charge = SUMMONER_TRUE_FORM_CHARGES
    player.summoner_true_form_base_max_health = 0

    direction_column, direction_row = player.facing_direction
    target_position = (
        game_state.floor.player_column + direction_column,
        game_state.floor.player_row + direction_row,
    )
    if not can_move_to(
        game_state.floor.map,
        target_position[0],
        target_position[1],
    ):
        add_log_message(
            game_state.combat_log,
            "There is no room to release the familiar.",
        )
        return True
    occupied_positions = {
        (
            game_state.floor.player_column,
            game_state.floor.player_row,
        ),
        *(
            position
            for enemy in game_state.floor.enemies
            if enemy.health > 0
            for position in get_enemy_occupied_positions(enemy)
        ),
        *(
            (chest["column"], chest["row"])
            for chest in game_state.floor.chests
            if not chest["is_open"]
        ),
    }
    if target_position in occupied_positions:
        add_log_message(
            game_state.combat_log,
            "There is no room to release the familiar.",
        )
        return True

    player.summoner_familiar_active = True
    player.summoner_familiar_position = target_position
    player.summoner_familiar_max_health = max(
        1,
        player.max_health // 2,
    )
    player.summoner_familiar_health = (
        player.summoner_familiar_max_health
    )
    player.summoner_familiar_movement_origin = None
    player.summoner_familiar_movement_started_at = 0
    player.summoner_familiar_attack_started_at = 0
    add_log_message(
        game_state.combat_log,
        "The familiar is released beside the summoner.",
    )
    return True

def request_summoner_bond(game_state: GameState) -> bool:
    player = game_state.player
    if player.subclass != "summoner":
        return False
    if player.summoner_bond_active:
        add_log_message(
            game_state.combat_log,
            "The summoner and familiar are already bonded.",
        )
        return True
    if (
        not player.summoner_familiar_active
        or player.summoner_familiar_health <= 0
    ):
        add_log_message(
            game_state.combat_log,
            "The familiar must be present to form the bond.",
        )
        return True
    if player.summoner_bond_charge < SUMMONER_BOND_CHARGES:
        add_log_message(
            game_state.combat_log,
            "Bond is not charged.",
        )
        return True

    player.summoner_bond_charge = 0
    player.summoner_bond_active = True
    player.summoner_bond_player_max_health = player.max_health
    player.summoner_bond_familiar_max_health = (
        player.summoner_familiar_max_health
    )
    shared_max_health = (
        player.summoner_bond_player_max_health
        + player.summoner_bond_familiar_max_health
    )
    shared_health = player.health + player.summoner_familiar_health
    player.max_health = shared_max_health
    player.health = min(shared_max_health, shared_health)
    player.summoner_familiar_max_health = shared_max_health
    player.summoner_familiar_health = player.health
    add_log_message(
        game_state.combat_log,
        "The summoner and familiar are bound by a shared life force.",
    )
    return True

def request_summoner_true_form(game_state: GameState) -> bool:
    player = game_state.player
    if player.subclass != "summoner":
        return False
    if not player.summoner_familiar_active:
        add_log_message(
            game_state.combat_log,
            "The familiar must be present to enter its true form.",
        )
        return True
    if player.summoner_true_form_active:
        player.summoner_true_form_active = False
        player.summoner_familiar_max_health = max(
            1,
            player.summoner_true_form_base_max_health,
        )
        player.summoner_familiar_health = min(
            player.summoner_familiar_health,
            player.summoner_familiar_max_health,
        )
        player.summoner_true_form_base_max_health = 0
        add_log_message(
            game_state.combat_log,
            "The familiar returns to its normal form.",
        )
        return True
    if player.summoner_true_form_charge < SUMMONER_TRUE_FORM_CHARGES:
        add_log_message(
            game_state.combat_log,
            "True Form is not fully charged.",
        )
        return True
    player.summoner_true_form_active = True
    player.summoner_true_form_base_max_health = (
        player.summoner_familiar_max_health
    )
    player.summoner_familiar_max_health += (
        SUMMONER_TRUE_FORM_HEALTH_BONUS
    )
    player.summoner_familiar_health += (
        SUMMONER_TRUE_FORM_HEALTH_BONUS
    )
    add_log_message(
        game_state.combat_log,
        "The familiar assumes its astral true form.",
    )
    return True

def deplete_summoner_true_form(game_state: GameState) -> None:
    player = game_state.player
    if not player.summoner_true_form_active:
        return
    player.summoner_true_form_active = False
    player.summoner_true_form_charge = 0
    player.summoner_familiar_health = 0
    player.summoner_familiar_active = False
    player.summoner_familiar_position = None
    player.summoner_true_form_base_max_health = 0
    player.summoner_familiar_death_penalty = True
    game_state.emit(
        GameEvent(
            type=GameEventType.DEATH,
            actor="familiar",
            data={"kind": "summoner_true_form_depleted"},
        )
    )
    add_log_message(
        game_state.combat_log,
        "The astral form fades after exhausting its power.",
    )

def break_summoner_bond(game_state: GameState) -> None:
    player = game_state.player
    if not player.summoner_bond_active:
        return

    shared_health = max(0, player.health)
    player_max_health = max(1, player.summoner_bond_player_max_health)
    familiar_max_health = max(
        1,
        player.summoner_bond_familiar_max_health,
    )
    total_max_health = player_max_health + familiar_max_health
    player.health = min(
        player_max_health,
        round(shared_health * player_max_health / total_max_health),
    )
    player.max_health = player_max_health
    player.summoner_familiar_max_health = familiar_max_health
    player.summoner_familiar_health = min(
        familiar_max_health,
        max(0, shared_health - player.health),
    )
    player.summoner_bond_active = False
    player.summoner_bond_player_max_health = 0
    player.summoner_bond_familiar_max_health = 0

def resolve_summoner_familiar_turn(game_state: GameState) -> None:
    player = game_state.player
    floor = game_state.floor
    familiar_position = player.summoner_familiar_position
    if (
        player.subclass != "summoner"
        or not player.summoner_familiar_active
        or familiar_position is None
        or player.health <= 0
        or player.summoner_familiar_health <= 0
    ):
        return

    player_position = (floor.player_column, floor.player_row)
    if distance_between(
        familiar_position[0],
        familiar_position[1],
        player_position[0],
        player_position[1],
    ) > 3:
        target_position = player_position
        target_enemy = None
    else:
        nearby_enemies = [
            enemy
            for enemy in floor.enemies
            if enemy.health > 0
            and distance_between(
                enemy.column,
                enemy.row,
                player_position[0],
                player_position[1],
            ) <= 3
        ]
        target_enemy = min(
            nearby_enemies,
            key=lambda enemy: distance_between(
                familiar_position[0],
                familiar_position[1],
                enemy.column,
                enemy.row,
            ),
            default=None,
        )
        if target_enemy is None:
            return
        target_position = (target_enemy.column, target_enemy.row)

    if target_enemy is not None:
        adjacent_target = next(
            (
                position
                for position in get_enemy_occupied_positions(
                    target_enemy
                )
                if distance_between(
                    familiar_position[0],
                    familiar_position[1],
                    position[0],
                    position[1],
                ) == 1
            ),
            None,
        )
        if adjacent_target is not None:
            true_form_attack = player.summoner_true_form_active
            if true_form_attack:
                player.summoner_true_form_charge = max(
                    0,
                    player.summoner_true_form_charge - 1,
                )
            player.summoner_familiar_attack_started_at = (
                game_state.player.familiar_turn_started_at
            )
            game_state.emit(
                GameEvent(
                    type=GameEventType.ATTACK,
                    actor="familiar",
                    origin=familiar_position,
                    positions=(adjacent_target,),
                    data={"kind": "summoner_familiar"},
                )
            )
            enemy_was_defeated = attack_enemy(
                game_state,
                target_enemy,
                player.damage_min,
                player.damage_max,
                0.0,
                attacker_position=familiar_position,
                grant_ability_charge=False,
                attacker_name="familiar",
            )
            if enemy_was_defeated:
                resolve_enemy_defeat(game_state, target_enemy)
            if true_form_attack and player.summoner_true_form_charge <= 0:
                deplete_summoner_true_form(game_state)
            return

    occupied_positions = {
        player_position,
        *(
            position
            for enemy in floor.enemies
            if enemy.health > 0
            for position in get_enemy_occupied_positions(enemy)
        ),
        *(
            (chest["column"], chest["row"])
            for chest in floor.chests
            if not chest["is_open"]
        ),
    }
    familiar_proxy = {
        "column": familiar_position[0],
        "row": familiar_position[1],
    }
    candidate = move_enemy_toward_position(
        floor.map,
        familiar_proxy,
        target_position[0],
        target_position[1],
        occupied_positions,
    )
    if candidate == familiar_position and target_enemy is not None:
        candidate = move_enemy_toward_position(
            floor.map,
            familiar_proxy,
            player_position[0],
            player_position[1],
            occupied_positions,
        )
    if candidate == familiar_position:
        return
    if distance_between(
        candidate[0],
        candidate[1],
        player_position[0],
        player_position[1],
    ) > 3:
        return
    player.summoner_familiar_movement_origin = familiar_position
    player.summoner_familiar_position = candidate
    player.summoner_familiar_movement_started_at = (
        game_state.player.familiar_turn_started_at
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.MOVE,
            actor="familiar",
            origin=familiar_position,
            destination=candidate,
            data={"kind": "summoner_familiar"},
        )
    )

def damage_summoner_familiar(
    game_state: GameState,
    damage: int,
) -> int:
    player = game_state.player
    if (
        not player.summoner_familiar_active
        or player.summoner_familiar_health <= 0
    ):
        return 0

    previous_health = (
        player.health
        if player.summoner_bond_active
        else player.summoner_familiar_health
    )
    current_health = max(0, previous_health - damage)
    if player.summoner_bond_active:
        player.health = current_health
        player.summoner_familiar_health = current_health
    else:
        player.summoner_familiar_health = current_health
    damage_dealt = previous_health - current_health
    if damage_dealt > 0 and player.summoner_bond_active:
        player.summoner_bond_charge = min(
            SUMMONER_BOND_CHARGES,
            player.summoner_bond_charge + 1,
        )
    if damage_dealt > 0 and not player.summoner_true_form_active:
        player.summoner_true_form_charge = min(
            SUMMONER_TRUE_FORM_CHARGES,
            player.summoner_true_form_charge + 1,
        )
    if player.summoner_familiar_health <= 0:
        player.summoner_familiar_active = False
        player.summoner_familiar_position = None
        player.summoner_true_form_active = False
        player.summoner_true_form_charge = 0
        player.summoner_true_form_base_max_health = 0
        player.summoner_familiar_charge = 0.0
        player.summoner_familiar_death_penalty = True
        player.summoner_bond_active = False
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor="familiar",
                data={"kind": "summoner_familiar"},
            )
        )
        add_log_message(
            game_state.combat_log,
            "The familiar is defeated.",
        )
    return damage_dealt
