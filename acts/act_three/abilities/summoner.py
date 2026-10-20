from collections.abc import Callable

from game.combat_log import add_log_message
from acts.act_three.events import GameEvent, GameEventType
from game.state import (
    EnemyState,
    FloorState,
    GameState,
)
from logic import (
    can_player_move_between,
    distance_between,
    get_enemy_occupied_positions,
    move_enemy_toward_position,
)
from acts.act_three.settings import (
    SUMMONER_FAMILIAR_AGGRO_RANGE,
    SUMMONER_FAMILIAR_CHARGES,
    SUMMONER_FAMILIAR_LEASH_RANGE,
    SUMMONER_BOND_CHARGES,
    SUMMONER_TRUE_FORM_CHARGES,
    SUMMONER_TRUE_FORM_HEALTH_BONUS,
    SUMMONER_TRUE_FORM_HEALTH_DRAIN,
)
from systems.player_combat import (
    attack_enemy,
    resolve_enemy_defeat,
)


OracleHitReaction = Callable[
    [EnemyState, FloorState, list[str]],
    None,
]


_SUMMONER_FAMILIAR_SUMMON_DIRECTIONS = (
    (-1, -1),
    (0, -1),
    (1, -1),
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 1),
    (-1, 0),
)


def summoner_familiar_summon_targets(
    game_state: GameState,
) -> tuple[tuple[int, int], ...]:
    player = game_state.player
    floor = game_state.floor
    if (
        player.subclass != "summoner"
        or player.summoner_familiar_active
    ):
        return ()

    origin = (
        floor.player_column,
        floor.player_row,
    )
    occupied_positions = {
        *(
            position
            for enemy in floor.enemies
            if enemy.health > 0
            for position in get_enemy_occupied_positions(enemy)
        ),
        *(
            (chest.column, chest.row)
            for chest in floor.chests
            if not chest.is_open
        ),
        *(
            (crate.column, crate.row)
            for crate in floor.breakable_crates
            if not crate.is_broken
        ),
        (
            floor.stairs_column,
            floor.stairs_row,
        ),
    }

    return tuple(
        (
            origin[0] + direction[0],
            origin[1] + direction[1],
        )
        for direction in _SUMMONER_FAMILIAR_SUMMON_DIRECTIONS
        if (
            (
                origin[0] + direction[0],
                origin[1] + direction[1],
            )
            not in occupied_positions
            and can_player_move_between(
                floor.map,
                origin[0],
                origin[1],
                origin[0] + direction[0],
                origin[1] + direction[1],
                floor.barriers,
            )
        )
    )


def select_summoner_familiar_summon_target(
    game_state: GameState,
    target: tuple[int, int] | None,
) -> bool:
    player = game_state.player
    if (
        not player.summoner_familiar_summon_aiming
        or target not in summoner_familiar_summon_targets(
            game_state
        )
    ):
        player.summoner_familiar_summon_target = None
        return False

    player.summoner_familiar_summon_target = target
    return True


def select_summoner_familiar_summon_direction(
    game_state: GameState,
    direction: tuple[int, int],
) -> bool:
    origin = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    return select_summoner_familiar_summon_target(
        game_state,
        (
            origin[0] + direction[0],
            origin[1] + direction[1],
        ),
    )


def cancel_summoner_familiar_summon(
    game_state: GameState,
) -> None:
    player = game_state.player
    player.summoner_familiar_summon_aiming = False
    player.summoner_familiar_summon_target = None
    add_log_message(
        game_state.combat_log,
        "Familiar summoning cancelled.",
    )


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
            player.summoner_familiar_summon_aiming = False
            player.summoner_familiar_summon_target = None
            player.summoner_familiar_summoned_at = -1
            player.summoner_familiar_movement_origin = None
            player.summoner_familiar_attack_target = None
            player.summoner_true_form_started_at = -1
            player.summoner_true_form_ending_started_at = -1
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

    if (
        not player.debug_unlimited_abilities
        and player.summoner_familiar_charge
        < SUMMONER_FAMILIAR_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "The familiar is not charged yet.",
        )
        return True

    summon_targets = summoner_familiar_summon_targets(
        game_state
    )
    if not summon_targets:
        add_log_message(
            game_state.combat_log,
            "There is no room to summon the familiar.",
        )
        return True

    player.summoner_aiming = False
    player.summoner_aim_target = None
    player.summoner_familiar_summon_aiming = True

    facing_target = (
        game_state.floor.player_column
        + player.facing_direction[0],
        game_state.floor.player_row
        + player.facing_direction[1],
    )
    player.summoner_familiar_summon_target = (
        facing_target
        if facing_target in summon_targets
        else summon_targets[0]
    )
    add_log_message(
        game_state.combat_log,
        "Choose a neighboring cell and press Q again.",
    )
    return True


def confirm_summoner_familiar_summon(
    game_state: GameState,
    current_time: int,
) -> bool:
    player = game_state.player
    floor = game_state.floor
    target_position = player.summoner_familiar_summon_target

    if (
        player.subclass != "summoner"
        or not player.summoner_familiar_summon_aiming
        or target_position
        not in summoner_familiar_summon_targets(game_state)
    ):
        add_log_message(
            game_state.combat_log,
            "Choose an available neighboring cell.",
        )
        return False

    player_position = (
        floor.player_column,
        floor.player_row,
    )
    if target_position[0] < player_position[0]:
        summon_direction = "right"
    elif target_position[0] > player_position[0]:
        summon_direction = "left"
    else:
        summon_direction = (
            "right"
            if player.facing_direction[0] > 0
            else "left"
        )

    player.summoner_familiar_summon_aiming = False
    player.summoner_familiar_summon_target = None
    player.summoner_familiar_charge = 0.0
    player.summoner_familiar_death_penalty = False
    player.summoner_familiar_death_true_form = False
    player.summoner_true_form_active = False
    player.summoner_true_form_started_at = -1
    player.summoner_true_form_ending_started_at = -1
    player.summoner_true_form_charge = (
        SUMMONER_TRUE_FORM_CHARGES
    )
    player.summoner_true_form_base_max_health = 0

    player.summoner_familiar_active = True
    player.summoner_familiar_position = target_position
    player.summoner_familiar_summoned_at = current_time
    player.summoner_familiar_summon_direction = (
        summon_direction
    )
    player.summoner_familiar_skip_turn = True
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
    player.summoner_familiar_attack_target = None
    player.summoner_familiar_hit_animation_started_at = -1
    player.summoner_familiar_hit_damage = 0
    player.summoner_familiar_hit_origin = None
    player.summoner_familiar_hit_position = None

    game_state.emit(
        GameEvent(
            type=GameEventType.SUMMON,
            actor="familiar",
            origin=player_position,
            destination=target_position,
            data={"kind": "summoner_familiar"},
        )
    )
    add_log_message(
        game_state.combat_log,
        "The familiar answers the summoner's call.",
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
    if (
        not player.debug_unlimited_abilities
        and player.summoner_bond_charge < SUMMONER_BOND_CHARGES
    ):
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

def request_summoner_true_form(
    game_state: GameState,
    current_time: int,
) -> bool:
    player = game_state.player
    if player.subclass != "summoner":
        return False
    if not player.summoner_familiar_active:
        add_log_message(
            game_state.combat_log,
            "The familiar must be present to enter its true form.",
        )
        return False

    if player.summoner_true_form_active:
        base_max_health = max(
            1,
            player.summoner_true_form_base_max_health,
        )
        player.summoner_true_form_active = False
        player.summoner_true_form_started_at = -1
        player.summoner_true_form_ending_started_at = (
            current_time
        )
        player.summoner_familiar_skip_turn = True
        player.summoner_true_form_charge = 0
        player.summoner_true_form_base_max_health = 0
        player.summoner_familiar_max_health = base_max_health
        player.summoner_familiar_health = min(
            player.summoner_familiar_health,
            base_max_health,
        )
        if player.summoner_bond_active:
            player.health = min(
                player.health,
                player.summoner_familiar_health,
            )
        add_log_message(
            game_state.combat_log,
            "The familiar abandons its true form. Its power is exhausted.",
        )
        return True

    if (
        not player.debug_unlimited_abilities
        and player.summoner_true_form_charge
        < SUMMONER_TRUE_FORM_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "True Form is not fully charged.",
        )
        return False

    player.summoner_true_form_active = True
    player.summoner_true_form_started_at = current_time
    player.summoner_true_form_ending_started_at = -1
    player.summoner_familiar_skip_turn = True
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

    familiar_position = player.summoner_familiar_position
    player.summoner_familiar_death_true_form = True
    player.summoner_true_form_active = False
    player.summoner_true_form_started_at = -1
    player.summoner_true_form_ending_started_at = -1
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
            destination=familiar_position,
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


def _familiar_distance_to_enemy(
    familiar_position,
    enemy,
):
    return min(
        distance_between(
            familiar_position[0],
            familiar_position[1],
            position[0],
            position[1],
        )
        for position in get_enemy_occupied_positions(enemy)
    )


def _enemy_is_attacking_summoner(
    game_state: GameState,
    enemy,
) -> bool:
    return (
        enemy.health > 0
        and enemy.is_aggro
        and enemy.prepared_attack_target != "familiar"
    )


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

    if player.summoner_true_form_active:
        damage_summoner_familiar(
            game_state,
            SUMMONER_TRUE_FORM_HEALTH_DRAIN,
        )
        if (
            not player.summoner_familiar_active
            or player.summoner_familiar_health <= 0
        ):
            return
        familiar_position = (
            player.summoner_familiar_position
        )

    if player.summoner_familiar_skip_turn:
        player.summoner_familiar_skip_turn = False
        player.summoner_familiar_attack_target = None
        return

    player.summoner_familiar_attack_target = None
    player_position = (floor.player_column, floor.player_row)

    summoner_threats = [
        enemy
        for enemy in floor.enemies
        if _enemy_is_attacking_summoner(
            game_state,
            enemy,
        )
    ]
    target_enemy = min(
        summoner_threats,
        key=lambda enemy: (
            _familiar_distance_to_enemy(
                player_position,
                enemy,
            ),
            _familiar_distance_to_enemy(
                familiar_position,
                enemy,
            ),
        ),
        default=None,
    )
    protecting_summoner = target_enemy is not None

    if target_enemy is None:
        nearby_enemies = [
            enemy
            for enemy in floor.enemies
            if (
                enemy.health > 0
                and _familiar_distance_to_enemy(
                    familiar_position,
                    enemy,
                ) <= SUMMONER_FAMILIAR_AGGRO_RANGE
            )
        ]
        target_enemy = min(
            nearby_enemies,
            key=lambda enemy: _familiar_distance_to_enemy(
                familiar_position,
                enemy,
            ),
            default=None,
        )

    if target_enemy is None:
        if distance_between(
            familiar_position[0],
            familiar_position[1],
            player_position[0],
            player_position[1],
        ) <= SUMMONER_FAMILIAR_LEASH_RANGE:
            return
        target_position = player_position
    else:
        target_position = min(
            get_enemy_occupied_positions(target_enemy),
            key=lambda position: distance_between(
                familiar_position[0],
                familiar_position[1],
                position[0],
                position[1],
            ),
        )

    if target_enemy is not None:
        adjacent_target = next(
            (
                position
                for position in get_enemy_occupied_positions(
                    target_enemy
                )
                if max(
                    abs(
                        familiar_position[0]
                        - position[0]
                    ),
                    abs(
                        familiar_position[1]
                        - position[1]
                    ),
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
            player.summoner_familiar_attack_target = (
                adjacent_target
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
    if (
        not protecting_summoner
        and distance_between(
            candidate[0],
            candidate[1],
            player_position[0],
            player_position[1],
        ) > SUMMONER_FAMILIAR_LEASH_RANGE
    ):
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

    familiar_position = player.summoner_familiar_position
    familiar_was_true_form = (
        player.summoner_true_form_active
    )
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
        player.summoner_familiar_death_true_form = (
            familiar_was_true_form
        )
        player.summoner_familiar_active = False
        player.summoner_familiar_position = None
        player.summoner_familiar_summon_aiming = False
        player.summoner_familiar_summon_target = None
        player.summoner_familiar_summoned_at = -1
        player.summoner_familiar_attack_target = None
        player.summoner_true_form_active = False
        player.summoner_true_form_started_at = -1
        player.summoner_true_form_ending_started_at = -1
        player.summoner_true_form_charge = 0
        player.summoner_true_form_base_max_health = 0
        player.summoner_familiar_charge = 0.0
        player.summoner_familiar_death_penalty = True
        player.summoner_bond_active = False
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor="familiar",
                destination=familiar_position,
                data={
                    "kind": (
                        "summoner_true_form"
                        if familiar_was_true_form
                        else "summoner_familiar"
                    )
                },
            )
        )
        add_log_message(
            game_state.combat_log,
            "The familiar is defeated.",
        )
    return damage_dealt
