from collections.abc import Callable
from enum import Enum, auto
import random

from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import (
    ArcherBarrageShotState,
    EnemyBehaviorState,
    EnemyState,
    FloorState,
    GameState,
)
from logic import (
    can_move_to,
    direction_toward,
    distance_between,
    get_directional_line,
    get_enemy_occupied_positions,
    has_line_of_sight,
    move_enemy_toward_position,
)
from settings import (
    CLASS_ABILITY_KILLS,
    ASSASSIN_INVISIBILITY_TURNS,
    ASSASSIN_TELEPORT_CHARGES,
    ASSASSIN_ULTIMATE_CHARGES,
    ARCHER_EMPOWERED_SHOT_CHARGES,
    ARCHER_EMPOWERED_SHOT_DAMAGE_MAX,
    ARCHER_EMPOWERED_SHOT_DAMAGE_MIN,
    ARCHER_BARRAGE_ZONE_CHARGES,
    ARCHER_BARRAGE_ZONE_SIZE,
    ARCHER_LEAP_CHARGES,
    ARCHER_LEAP_RANGE,
    BERSERKER_CRUSHING_LEAP_CHARGES,
    BERSERKER_CRUSHING_LEAP_RANGE,
    BERSERKER_LAST_RAGE_CHARGES,
    BERSERKER_LAST_RAGE_TURNS,
    MAGE_SPELL_DAMAGE_BONUS,
    MAGE_SPELL_RANGE,
    PALADIN_HOLY_HAND_CHARGES,
    PALADIN_HOLY_HAND_HEALING,
    PALADIN_HOLY_SHIELD_CHARGES,
    PALADIN_HOLY_SHIELD_TURNS,
    PALADIN_SHIELD_CHARGE_CHARGES,
    PALADIN_SHIELD_CHARGE_RANGE,
    ROGUE_INVISIBILITY_TURNS,
    SUMMONER_FAMILIAR_CHARGES,
    SUMMONER_BOND_CHARGES,
    SUMMONER_TRUE_FORM_CHARGES,
    SUMMONER_TRUE_FORM_DAMAGE_BONUS,
    SUMMONER_TRUE_FORM_HEALTH_BONUS,
    WARLOCK_CURSE_CHARGES,
    WARLOCK_CURSE_RANGE,
    WARLOCK_CURSE_TURNS,
    WARLOCK_DEMON_FORM_HEALTH_DRAIN,
    WARLOCK_SOUL_EXCHANGE_CHARGES,
    WARLOCK_SOUL_EXCHANGE_RANGE,
    WARRIOR_STRIKE_DAMAGE_BONUS,
)
from systems.player_combat import (
    attack_enemy,
    resolve_enemy_defeat,
)


OracleHitReaction = Callable[
    [EnemyState, FloorState, list[str]],
    None,
]


class AbilityRequestResult(Enum):
    IGNORED = auto()
    NOT_READY = auto()
    ROGUE_ACTIVATED = auto()
    AIMING_TOGGLED = auto()


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


def request_class_ability(
    game_state: GameState,
) -> AbilityRequestResult:
    player = game_state.player

    if player.player_class is None:
        return AbilityRequestResult.IGNORED

    if player.ability_kill_charge < CLASS_ABILITY_KILLS:
        add_log_message(
            game_state.combat_log,
            "Class ability is not charged.",
        )
        return AbilityRequestResult.NOT_READY

    if player.player_class == "rogue":
        player.ability_kill_charge = 0
        player.invisibility_turns = (
            ASSASSIN_INVISIBILITY_TURNS
            if player.subclass == "assassin"
            else ROGUE_INVISIBILITY_TURNS
        )

        for enemy in game_state.floor.enemies:
            enemy.is_aggro = False
            enemy.behavior_state = EnemyBehaviorState.IDLE
            enemy.attack_targets = []
            enemy.prepared_attack_mode = None
            enemy.heal_target = None

        add_log_message(
            game_state.combat_log,
            "The rogue vanishes from sight.",
        )
        return AbilityRequestResult.ROGUE_ACTIVATED

    if player.player_class in ("warrior", "mage"):
        player.directional_ability_aiming = (
            not player.directional_ability_aiming
        )
        add_log_message(
            game_state.combat_log,
            (
                "Choose an ability direction."
                if player.directional_ability_aiming
                else "Ability aiming cancelled."
            ),
        )
        return AbilityRequestResult.AIMING_TOGGLED

    return AbilityRequestResult.IGNORED


def cancel_ability_aiming(game_state: GameState) -> None:
    game_state.player.directional_ability_aiming = False
    add_log_message(
        game_state.combat_log,
        "Ability aiming cancelled.",
    )


def request_archer_empowered_shot(game_state: GameState) -> bool:
    player = game_state.player
    if player.subclass != "archer":
        return False

    if player.archer_empowered_shot_aiming:
        player.archer_empowered_shot_aiming = False
        player.archer_empowered_shot_target = None
        add_log_message(
            game_state.combat_log,
            "Empowered Shot aiming cancelled.",
        )
        return True

    if player.archer_empowered_shot_charge < ARCHER_EMPOWERED_SHOT_CHARGES:
        add_log_message(
            game_state.combat_log,
            "Empowered Shot is not charged.",
        )
        return True

    player.archer_leap_aiming = False
    player.archer_leap_target = None
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    player.archer_empowered_shot_aiming = True
    player.archer_empowered_shot_target = None
    add_log_message(
        game_state.combat_log,
        "Choose a visible enemy for Empowered Shot.",
    )
    return True


def cancel_archer_empowered_shot(game_state: GameState) -> None:
    game_state.player.archer_empowered_shot_aiming = False
    game_state.player.archer_empowered_shot_target = None
    add_log_message(
        game_state.combat_log,
        "Empowered Shot aiming cancelled.",
    )


def is_valid_archer_empowered_shot_target(
    game_state: GameState,
    target_cell: tuple[int, int],
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if player.subclass != "archer" or not player.archer_empowered_shot_aiming:
        return False
    if not (0 <= target_cell[1] < len(floor.map)):
        return False
    if not (0 <= target_cell[0] < len(floor.map[0])):
        return False

    target_enemy = next(
        (
            enemy
            for enemy in floor.enemies
            if enemy.health > 0
            and target_cell in get_enemy_occupied_positions(enemy)
        ),
        None,
    )
    if target_enemy is None:
        return False

    return has_line_of_sight(
        floor.map,
        floor.player_column,
        floor.player_row,
        target_cell[0],
        target_cell[1],
    )


def perform_archer_empowered_shot(
    game_state: GameState,
    target_cell: tuple[int, int],
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    if not is_valid_archer_empowered_shot_target(game_state, target_cell):
        return False

    player = game_state.player
    floor = game_state.floor
    hit_enemy = next(
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
        and target_cell in get_enemy_occupied_positions(enemy)
    )
    origin = (floor.player_column, floor.player_row)
    player.archer_empowered_shot_aiming = False
    player.archer_empowered_shot_target = target_cell
    player.archer_empowered_shot_started_at = 0
    player.archer_empowered_shot_charge = 0
    game_state.player_attack_targets = [target_cell]
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=origin,
            positions=(target_cell,),
            data={"kind": "archer_empowered_shot"},
        )
    )
    enemy_was_defeated = attack_enemy(
        game_state,
        hit_enemy,
        ARCHER_EMPOWERED_SHOT_DAMAGE_MIN,
        ARCHER_EMPOWERED_SHOT_DAMAGE_MAX,
        player.crit_chance,
        attacker_position=origin,
    )
    if hit_enemy.type == "oracle":
        oracle_hit_reaction(hit_enemy, floor, game_state.combat_log)
    if enemy_was_defeated:
        resolve_enemy_defeat(game_state, hit_enemy)
    return True


def request_archer_leap(game_state: GameState) -> bool:
    player = game_state.player
    if player.subclass != "archer":
        return False

    if player.archer_leap_aiming:
        player.archer_leap_aiming = False
        player.archer_leap_target = None
        add_log_message(
            game_state.combat_log,
            "Leap aiming cancelled.",
        )
        return True

    if player.archer_leap_charge < ARCHER_LEAP_CHARGES:
        add_log_message(
            game_state.combat_log,
            "Leap is not charged.",
        )
        return True

    player.archer_empowered_shot_aiming = False
    player.archer_empowered_shot_target = None
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    player.archer_leap_aiming = True
    player.archer_leap_target = None
    add_log_message(
        game_state.combat_log,
        "Choose a visible cell for Leap.",
    )
    return True


def cancel_archer_leap(game_state: GameState) -> None:
    game_state.player.archer_leap_aiming = False
    game_state.player.archer_leap_target = None
    add_log_message(
        game_state.combat_log,
        "Leap aiming cancelled.",
    )


def is_valid_archer_leap_target(
    game_state: GameState,
    column: int,
    row: int,
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if player.subclass != "archer" or not player.archer_leap_aiming:
        return False
    if not (0 <= row < len(floor.map)):
        return False
    if not (0 <= column < len(floor.map[0])):
        return False
    if floor.map[row][column] in ("#", "C"):
        return False

    origin = (floor.player_column, floor.player_row)
    if (column, row) == origin:
        return False
    if (
        abs(column - origin[0]) + abs(row - origin[1])
        > ARCHER_LEAP_RANGE
    ):
        return False
    if not has_line_of_sight(
        floor.map,
        origin[0],
        origin[1],
        column,
        row,
    ):
        return False
    if any(
        enemy.health > 0
        and (column, row) in get_enemy_occupied_positions(enemy)
        for enemy in floor.enemies
    ):
        return False
    if any(
        not chest.is_open
        and (column, row) == (chest.column, chest.row)
        for chest in floor.chests
    ):
        return False
    return True


def get_berserker_crushing_leap_cells(
    game_state: GameState,
    target: tuple[int, int],
) -> list[tuple[int, int]]:
    dungeon_map = game_state.floor.map
    cells = []
    for row_change in (-1, 0, 1):
        for column_change in (-1, 0, 1):
            if column_change == 0 and row_change == 0:
                continue
            column = target[0] + column_change
            row = target[1] + row_change
            if not (
                0 <= row < len(dungeon_map)
                and 0 <= column < len(dungeon_map[0])
            ):
                continue
            if can_move_to(dungeon_map, column, row):
                cells.append((column, row))
    return cells


def is_valid_berserker_crushing_leap_target(
    game_state: GameState,
    target: tuple[int, int],
) -> bool:
    player = game_state.player
    floor = game_state.floor
    column, row = target
    if (
        player.subclass != "berserker"
        or not player.berserker_crushing_leap_aiming
    ):
        return False
    if not (
        0 <= row < len(floor.map)
        and 0 <= column < len(floor.map[0])
    ):
        return False
    if not can_move_to(floor.map, column, row):
        return False

    origin = (floor.player_column, floor.player_row)
    if target == origin:
        return False
    if (
        abs(column - origin[0]) + abs(row - origin[1])
        > BERSERKER_CRUSHING_LEAP_RANGE
    ):
        return False
    if not has_line_of_sight(
        floor.map,
        origin[0],
        origin[1],
        column,
        row,
    ):
        return False
    if any(
        enemy.health > 0
        and target in get_enemy_occupied_positions(enemy)
        for enemy in floor.enemies
    ):
        return False
    if any(
        not chest.is_open
        and target == (chest.column, chest.row)
        for chest in floor.chests
    ):
        return False
    return True


def request_berserker_crushing_leap(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if player.subclass != "berserker":
        return False

    if player.berserker_crushing_leap_aiming:
        cancel_berserker_crushing_leap(game_state)
        return True

    if (
        player.berserker_crushing_leap_charge
        < BERSERKER_CRUSHING_LEAP_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Crushing Leap is not charged.",
        )
        return True

    player.berserker_crushing_leap_aiming = True
    player.berserker_crushing_leap_target = None
    player.berserker_crushing_leap_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Choose a landing cell for Crushing Leap.",
    )
    return True


def cancel_berserker_crushing_leap(
    game_state: GameState,
) -> None:
    player = game_state.player
    player.berserker_crushing_leap_aiming = False
    player.berserker_crushing_leap_target = None
    player.berserker_crushing_leap_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Crushing Leap aiming cancelled.",
    )


def update_berserker_crushing_leap_preview(
    game_state: GameState,
    target: tuple[int, int] | None,
) -> bool:
    player = game_state.player
    if (
        target is None
        or not is_valid_berserker_crushing_leap_target(
            game_state,
            target,
        )
    ):
        player.berserker_crushing_leap_target = None
        player.berserker_crushing_leap_preview_cells.clear()
        return False

    player.berserker_crushing_leap_target = target
    player.berserker_crushing_leap_preview_cells = (
        get_berserker_crushing_leap_cells(
            game_state,
            target,
        )
    )
    return True


def perform_berserker_crushing_leap(
    game_state: GameState,
    current_time: int,
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    player = game_state.player
    floor = game_state.floor
    target = player.berserker_crushing_leap_target
    if (
        target is None
        or not is_valid_berserker_crushing_leap_target(
            game_state,
            target,
        )
    ):
        return False

    origin = (floor.player_column, floor.player_row)
    impact_cells = get_berserker_crushing_leap_cells(
        game_state,
        target,
    )
    floor.player_column, floor.player_row = target
    player.berserker_crushing_leap_charge = 0
    player.berserker_crushing_leap_aiming = False
    player.berserker_crushing_leap_target = None
    player.berserker_crushing_leap_preview_cells = list(
        impact_cells
    )
    player.berserker_crushing_leap_origin = origin
    player.berserker_crushing_leap_started_at = current_time

    game_state.emit(
        GameEvent(
            type=GameEventType.MOVE,
            actor="hero",
            origin=origin,
            destination=target,
            data={"kind": "berserker_crushing_leap"},
        )
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=target,
            positions=tuple(impact_cells),
            data={"kind": "berserker_crushing_leap"},
        )
    )

    enemies_hit = [
        enemy
        for enemy in floor.enemies
        if (
            enemy.health > 0
            and any(
                position in impact_cells
                for position in get_enemy_occupied_positions(
                    enemy
                )
            )
        )
    ]
    if not enemies_hit:
        add_log_message(
            game_state.combat_log,
            "Crushing Leap hits nothing.",
        )

    for enemy in enemies_hit:
        enemy_was_defeated = attack_enemy(
            game_state,
            enemy,
            player.damage_min,
            player.damage_max,
            player.crit_chance,
            attacker_position=target,
        )
        if enemy.type == "oracle":
            oracle_hit_reaction(
                enemy,
                floor,
                game_state.combat_log,
            )
        if enemy_was_defeated:
            resolve_enemy_defeat(game_state, enemy)

    add_log_message(
        game_state.combat_log,
        "The berserker crashes into the battlefield.",
    )
    return True


def request_berserker_last_rage(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if player.subclass != "berserker":
        return False

    if player.berserker_last_rage_turns > 0:
        add_log_message(
            game_state.combat_log,
            "Last Rage is already active.",
        )
        return True
    if (
        player.berserker_last_rage_charge
        < BERSERKER_LAST_RAGE_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Last Rage is not charged.",
        )
        return True

    player.berserker_last_rage_charge = 0
    player.berserker_last_rage_turns = (
        BERSERKER_LAST_RAGE_TURNS
    )
    player.berserker_crushing_leap_aiming = False
    player.berserker_crushing_leap_target = None
    player.berserker_crushing_leap_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Last Rage ignites. The berserker cannot die.",
    )
    return True


def advance_berserker_last_rage(
    game_state: GameState,
) -> None:
    player = game_state.player
    if (
        player.subclass != "berserker"
        or player.berserker_last_rage_turns <= 0
    ):
        return

    player.berserker_last_rage_turns -= 1
    if player.berserker_last_rage_turns == 0:
        add_log_message(
            game_state.combat_log,
            "Last Rage fades. Death can claim the berserker again.",
        )


def request_paladin_holy_hand(
    game_state: GameState,
    current_time: int,
) -> bool:
    player = game_state.player
    if player.subclass != "paladin":
        return False

    if player.health >= player.max_health:
        add_log_message(
            game_state.combat_log,
            "Holy Hand is not needed at full health.",
        )
        return True
    if (
        player.paladin_holy_hand_charge
        < PALADIN_HOLY_HAND_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Holy Hand is not charged.",
        )
        return True

    previous_health = player.health
    player.health = min(
        player.max_health,
        player.health + PALADIN_HOLY_HAND_HEALING,
    )
    healing = player.health - previous_health
    player.paladin_holy_hand_charge = 0
    player.paladin_holy_hand_started_at = current_time
    game_state.emit(
        GameEvent(
            type=GameEventType.HEAL,
            actor="hero",
            target="hero",
            destination=(
                game_state.floor.player_column,
                game_state.floor.player_row,
            ),
            amount=healing,
            data={"kind": "paladin_holy_hand"},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"Holy Hand restores {healing} health.",
    )
    return True


def request_paladin_holy_shield(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if player.subclass != "paladin":
        return False

    if player.paladin_holy_shield_turns > 0:
        add_log_message(
            game_state.combat_log,
            "Holy Shield is already active.",
        )
        return True
    if (
        player.paladin_holy_shield_charge
        < PALADIN_HOLY_SHIELD_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Holy Shield is not charged.",
        )
        return True

    player.paladin_holy_shield_charge = 0
    player.paladin_holy_shield_turns = (
        PALADIN_HOLY_SHIELD_TURNS
    )
    player.paladin_shield_charge_aiming = False
    player.paladin_shield_charge_target = None
    player.paladin_shield_charge_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Holy Shield surrounds the paladin.",
    )
    return True


def advance_paladin_holy_shield(
    game_state: GameState,
) -> None:
    player = game_state.player
    if (
        player.subclass != "paladin"
        or player.paladin_holy_shield_turns <= 0
    ):
        return

    player.paladin_holy_shield_turns -= 1
    if player.paladin_holy_shield_turns == 0:
        add_log_message(
            game_state.combat_log,
            "Holy Shield fades.",
        )


def is_valid_warlock_curse_target(
    game_state: GameState,
    target: tuple[int, int],
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if (
        player.subclass != "warlock"
        or not player.warlock_curse_aiming
    ):
        return False

    target_enemy = next(
        (
            enemy
            for enemy in floor.enemies
            if enemy.health > 0
            and target in get_enemy_occupied_positions(enemy)
        ),
        None,
    )
    if target_enemy is None:
        return False

    distance = abs(
        target[0] - floor.player_column
    ) + abs(
        target[1] - floor.player_row
    )
    return (
        distance <= WARLOCK_CURSE_RANGE
        and has_line_of_sight(
            floor.map,
            floor.player_column,
            floor.player_row,
            target[0],
            target[1],
        )
    )


def request_warlock_curse(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if player.subclass != "warlock":
        return False

    if player.warlock_curse_aiming:
        cancel_warlock_curse(game_state)
        return True
    if player.warlock_curse_charge < WARLOCK_CURSE_CHARGES:
        add_log_message(
            game_state.combat_log,
            "Curse is not charged.",
        )
        return True

    player.warlock_curse_aiming = True
    player.warlock_curse_target = None
    player.warlock_soul_exchange_aiming = False
    player.warlock_soul_exchange_target = None
    add_log_message(
        game_state.combat_log,
        "Choose an enemy to curse.",
    )
    return True


def cancel_warlock_curse(
    game_state: GameState,
) -> None:
    player = game_state.player
    player.warlock_curse_aiming = False
    player.warlock_curse_target = None
    add_log_message(
        game_state.combat_log,
        "Curse aiming cancelled.",
    )


def perform_warlock_curse(
    game_state: GameState,
    target: tuple[int, int],
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if not is_valid_warlock_curse_target(
        game_state,
        target,
    ):
        return False

    target_enemy = next(
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
        and target in get_enemy_occupied_positions(enemy)
    )
    target_enemy.curse_turns = WARLOCK_CURSE_TURNS
    player.warlock_curse_charge = 0
    player.warlock_curse_aiming = False
    player.warlock_curse_target = None
    player.warlock_newly_cursed_enemy = target_enemy.name
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            target=target_enemy.name,
            origin=(
                floor.player_column,
                floor.player_row,
            ),
            destination=target,
            data={"kind": "warlock_curse"},
        )
    )
    add_log_message(
        game_state.combat_log,
        (
            f"{target_enemy.name} is cursed for "
            f"{WARLOCK_CURSE_TURNS} turns."
        ),
    )
    return True


def advance_warlock_curses(
    game_state: GameState,
) -> None:
    newly_cursed_enemy = (
        game_state.player.warlock_newly_cursed_enemy
    )
    for enemy in game_state.floor.enemies:
        if (
            enemy.health <= 0
            or enemy.curse_turns <= 0
            or enemy.name == newly_cursed_enemy
        ):
            continue
        enemy.curse_turns -= 1
        if enemy.curse_turns == 0:
            add_log_message(
                game_state.combat_log,
                f"The curse on {enemy.name} fades.",
            )
    game_state.player.warlock_newly_cursed_enemy = None


def advance_warlock_demon_form(
    game_state: GameState,
) -> None:
    player = game_state.player
    if (
        player.subclass != "warlock"
        or not player.warlock_demon_form_active
        or player.health <= 0
    ):
        return

    player.health = max(
        0,
        player.health - WARLOCK_DEMON_FORM_HEALTH_DRAIN,
    )
    add_log_message(
        game_state.combat_log,
        f"Demon Form consumes {WARLOCK_DEMON_FORM_HEALTH_DRAIN} HP.",
    )
    if player.health <= 0:
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor="hero",
                destination=(
                    game_state.floor.player_column,
                    game_state.floor.player_row,
                ),
                data={"cause": "demon_form"},
            )
        )


def is_valid_warlock_soul_exchange_target(
    game_state: GameState,
    target: tuple[int, int],
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if (
        player.subclass != "warlock"
        or not player.warlock_soul_exchange_aiming
    ):
        return False

    target_enemy = next(
        (
            enemy
            for enemy in floor.enemies
            if enemy.health > 0
            and target in get_enemy_occupied_positions(enemy)
        ),
        None,
    )
    if (
        target_enemy is None
        or target_enemy.footprint_width != 1
        or target_enemy.footprint_height != 1
    ):
        return False

    distance = abs(
        target[0] - floor.player_column
    ) + abs(
        target[1] - floor.player_row
    )
    return (
        distance <= WARLOCK_SOUL_EXCHANGE_RANGE
        and has_line_of_sight(
            floor.map,
            floor.player_column,
            floor.player_row,
            target_enemy.column,
            target_enemy.row,
        )
    )


def request_warlock_soul_exchange(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if player.subclass != "warlock":
        return False

    if player.warlock_soul_exchange_aiming:
        cancel_warlock_soul_exchange(game_state)
        return True
    if (
        player.warlock_soul_exchange_charge
        < WARLOCK_SOUL_EXCHANGE_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Soul Exchange is not charged.",
        )
        return True

    player.warlock_curse_aiming = False
    player.warlock_curse_target = None
    player.warlock_soul_exchange_aiming = True
    player.warlock_soul_exchange_target = None
    add_log_message(
        game_state.combat_log,
        "Choose an enemy for Soul Exchange.",
    )
    return True


def cancel_warlock_soul_exchange(
    game_state: GameState,
) -> None:
    player = game_state.player
    player.warlock_soul_exchange_aiming = False
    player.warlock_soul_exchange_target = None
    add_log_message(
        game_state.combat_log,
        "Soul Exchange aiming cancelled.",
    )


def perform_warlock_soul_exchange(
    game_state: GameState,
    target: tuple[int, int],
    current_time: int,
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if not is_valid_warlock_soul_exchange_target(
        game_state,
        target,
    ):
        return False

    target_enemy = next(
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
        and target in get_enemy_occupied_positions(enemy)
    )
    player_origin = (
        floor.player_column,
        floor.player_row,
    )
    enemy_origin = (
        target_enemy.column,
        target_enemy.row,
    )
    floor.player_column, floor.player_row = enemy_origin
    target_enemy.column, target_enemy.row = player_origin

    player.warlock_soul_exchange_charge = 0
    player.warlock_soul_exchange_aiming = False
    player.warlock_soul_exchange_target = None
    player.warlock_soul_exchange_player_origin = (
        player_origin
    )
    player.warlock_soul_exchange_enemy_origin = (
        enemy_origin
    )
    player.warlock_soul_exchange_enemy_name = (
        target_enemy.name
    )
    player.warlock_soul_exchange_started_at = current_time
    game_state.emit(
        GameEvent(
            type=GameEventType.MOVE,
            actor="hero",
            target=target_enemy.name,
            origin=player_origin,
            destination=enemy_origin,
            data={"kind": "warlock_soul_exchange"},
        )
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.MOVE,
            actor=target_enemy.name,
            target="hero",
            origin=enemy_origin,
            destination=player_origin,
            data={"kind": "warlock_soul_exchange"},
        )
    )
    add_log_message(
        game_state.combat_log,
        (
            f"The warlock exchanges places with "
            f"{target_enemy.name}."
        ),
    )
    return True


def get_paladin_shield_charge_path(
    game_state: GameState,
    target: tuple[int, int],
) -> list[tuple[int, int]]:
    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    target_column, target_row = target
    current_column, current_row = origin
    column_distance = abs(target_column - current_column)
    row_distance = abs(target_row - current_row)
    column_step = 1 if current_column < target_column else -1
    row_step = 1 if current_row < target_row else -1
    error = column_distance - row_distance
    path = []

    while (current_column, current_row) != target:
        doubled_error = error * 2
        if doubled_error > -row_distance:
            error -= row_distance
            current_column += column_step
        if doubled_error < column_distance:
            error += column_distance
            current_row += row_step
        path.append((current_column, current_row))

    return path


def _get_paladin_shield_charge_destination(
    game_state: GameState,
    path: list[tuple[int, int]],
) -> tuple[int, int]:
    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    occupied_positions = {
        position
        for enemy in floor.enemies
        if enemy.health > 0
        for position in get_enemy_occupied_positions(enemy)
    }
    if path and path[-1] not in occupied_positions:
        return path[-1]
    for position in reversed(path[:-1]):
        if position not in occupied_positions:
            return position
    return origin


def is_valid_paladin_shield_charge_target(
    game_state: GameState,
    target: tuple[int, int],
) -> bool:
    player = game_state.player
    floor = game_state.floor
    column, row = target
    origin = (floor.player_column, floor.player_row)
    if (
        player.subclass != "paladin"
        or not player.paladin_shield_charge_aiming
        or target == origin
    ):
        return False
    if not (
        0 <= row < len(floor.map)
        and 0 <= column < len(floor.map[0])
        and can_move_to(floor.map, column, row)
    ):
        return False
    if (
        max(
            abs(column - origin[0]),
            abs(row - origin[1]),
        )
        > PALADIN_SHIELD_CHARGE_RANGE
    ):
        return False
    if not has_line_of_sight(
        floor.map,
        origin[0],
        origin[1],
        column,
        row,
    ):
        return False

    path = get_paladin_shield_charge_path(
        game_state,
        target,
    )
    blocked_by_chest = any(
        not chest.is_open
        and (chest.column, chest.row) in path
        for chest in floor.chests
    )
    return bool(path) and not blocked_by_chest


def request_paladin_shield_charge(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if player.subclass != "paladin":
        return False

    if player.paladin_shield_charge_aiming:
        cancel_paladin_shield_charge(game_state)
        return True
    if (
        player.paladin_shield_charge_charge
        < PALADIN_SHIELD_CHARGE_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Shield Charge is not charged.",
        )
        return True

    player.paladin_shield_charge_aiming = True
    player.paladin_shield_charge_target = None
    player.paladin_shield_charge_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Choose a cell or enemy for Shield Charge.",
    )
    return True


def cancel_paladin_shield_charge(
    game_state: GameState,
) -> None:
    player = game_state.player
    player.paladin_shield_charge_aiming = False
    player.paladin_shield_charge_target = None
    player.paladin_shield_charge_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Shield Charge aiming cancelled.",
    )


def update_paladin_shield_charge_preview(
    game_state: GameState,
    target: tuple[int, int] | None,
) -> bool:
    player = game_state.player
    if (
        target is None
        or not is_valid_paladin_shield_charge_target(
            game_state,
            target,
        )
    ):
        player.paladin_shield_charge_target = None
        player.paladin_shield_charge_preview_cells.clear()
        return False

    player.paladin_shield_charge_target = target
    player.paladin_shield_charge_preview_cells = (
        get_paladin_shield_charge_path(
            game_state,
            target,
        )
    )
    return True


def perform_paladin_shield_charge(
    game_state: GameState,
    current_time: int,
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    player = game_state.player
    floor = game_state.floor
    target = player.paladin_shield_charge_target
    if (
        target is None
        or not is_valid_paladin_shield_charge_target(
            game_state,
            target,
        )
    ):
        return False

    origin = (floor.player_column, floor.player_row)
    path = get_paladin_shield_charge_path(
        game_state,
        target,
    )
    destination = _get_paladin_shield_charge_destination(
        game_state,
        path,
    )
    enemies_hit = [
        enemy
        for enemy in floor.enemies
        if (
            enemy.health > 0
            and any(
                position in path
                for position in get_enemy_occupied_positions(
                    enemy
                )
            )
        )
    ]

    floor.player_column, floor.player_row = destination
    player.paladin_shield_charge_charge = 0
    player.paladin_shield_charge_aiming = False
    player.paladin_shield_charge_target = None
    player.paladin_shield_charge_preview_cells.clear()
    player.paladin_shield_charge_origin = origin
    player.paladin_shield_charge_started_at = current_time
    game_state.emit(
        GameEvent(
            type=GameEventType.MOVE,
            actor="hero",
            origin=origin,
            destination=destination,
            positions=tuple(path),
            data={"kind": "paladin_shield_charge"},
        )
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=origin,
            destination=target,
            positions=tuple(path),
            data={"kind": "paladin_shield_charge"},
        )
    )

    for enemy in enemies_hit:
        enemy_was_defeated = attack_enemy(
            game_state,
            enemy,
            player.damage_min,
            player.damage_max,
            player.crit_chance,
            attacker_position=destination,
            grant_ability_charge=False,
        )
        if enemy.type == "oracle":
            oracle_hit_reaction(
                enemy,
                floor,
                game_state.combat_log,
            )
        if enemy_was_defeated:
            resolve_enemy_defeat(game_state, enemy)

    add_log_message(
        game_state.combat_log,
        (
            f"Shield Charge strikes {len(enemies_hit)} target(s)."
            if enemies_hit
            else "The paladin charges across the battlefield."
        ),
    )
    return True


def get_archer_barrage_zone_cells(
    game_state: GameState,
    anchor: tuple[int, int],
) -> list[tuple[int, int]]:
    dungeon_map = game_state.floor.map
    start_column = anchor[0] - 2
    start_row = anchor[1] - 2
    cells = []

    for row in range(
        start_row,
        start_row + ARCHER_BARRAGE_ZONE_SIZE,
    ):
        for column in range(
            start_column,
            start_column + ARCHER_BARRAGE_ZONE_SIZE,
        ):
            if not (
                0 <= row < len(dungeon_map)
                and 0 <= column < len(dungeon_map[0])
            ):
                continue
            if can_move_to(dungeon_map, column, row):
                cells.append((column, row))

    return cells


def is_valid_archer_barrage_zone_anchor(
    game_state: GameState,
    anchor: tuple[int, int],
) -> bool:
    player = game_state.player
    dungeon_map = game_state.floor.map
    column, row = anchor
    return (
        player.subclass == "archer"
        and player.archer_barrage_zone_aiming
        and 0 <= row < len(dungeon_map)
        and 0 <= column < len(dungeon_map[0])
        and can_move_to(dungeon_map, column, row)
    )


def request_archer_barrage_zone(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if player.subclass != "archer":
        return False

    if player.archer_barrage_zone_aiming:
        cancel_archer_barrage_zone(game_state)
        return True

    if (
        player.archer_barrage_zone_charge
        < ARCHER_BARRAGE_ZONE_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Barrage Zone is not charged.",
        )
        return True

    player.archer_empowered_shot_aiming = False
    player.archer_empowered_shot_target = None
    player.archer_leap_aiming = False
    player.archer_leap_target = None
    player.archer_barrage_zone_aiming = True
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Choose an area for Barrage Zone.",
    )
    return True


def cancel_archer_barrage_zone(
    game_state: GameState,
) -> None:
    player = game_state.player
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Barrage Zone aiming cancelled.",
    )


def update_archer_barrage_zone_preview(
    game_state: GameState,
    anchor: tuple[int, int] | None,
) -> bool:
    player = game_state.player
    if (
        anchor is None
        or not is_valid_archer_barrage_zone_anchor(
            game_state,
            anchor,
        )
    ):
        player.archer_barrage_zone_anchor = None
        player.archer_barrage_zone_preview_cells.clear()
        return False

    player.archer_barrage_zone_anchor = anchor
    player.archer_barrage_zone_preview_cells = (
        get_archer_barrage_zone_cells(
            game_state,
            anchor,
        )
    )
    return bool(player.archer_barrage_zone_preview_cells)


def place_archer_barrage_zone(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if (
        not player.archer_barrage_zone_aiming
        or player.archer_barrage_zone_anchor is None
        or not player.archer_barrage_zone_preview_cells
    ):
        return False

    player.archer_barrage_zone_cells = list(
        dict.fromkeys(
            (
                *player.archer_barrage_zone_cells,
                *player.archer_barrage_zone_preview_cells,
            )
        )
    )
    player.archer_barrage_zone_charge = 0
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Barrage Zone is deployed.",
    )
    return True


def _archer_barrage_visual_origin(
    game_state: GameState,
    enemy: EnemyState,
) -> tuple[int, int]:
    floor = game_state.floor
    blocked_positions = {
        position
        for living_enemy in floor.enemies
        if living_enemy.health > 0
        for position in get_enemy_occupied_positions(
            living_enemy
        )
    }
    candidates = []
    for column_change, row_change in (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    ):
        column = enemy.column + column_change
        row = enemy.row + row_change
        if not (
            0 <= row < len(floor.map)
            and 0 <= column < len(floor.map[0])
            and can_move_to(floor.map, column, row)
            and (column, row) not in blocked_positions
        ):
            continue
        candidates.append((column, row))

    if not candidates:
        return (
            floor.player_column,
            floor.player_row,
        )

    return min(
        candidates,
        key=lambda position: (
            abs(position[0] - floor.player_column)
            + abs(position[1] - floor.player_row)
        ),
    )


def resolve_archer_barrage_zone_entry(
    game_state: GameState,
    enemy: EnemyState,
    previous_position: tuple[int, int],
) -> bool:
    player = game_state.player
    zone_cells = set(player.archer_barrage_zone_cells)
    if (
        player.subclass != "archer"
        or not zone_cells
        or enemy.health <= 0
    ):
        return False

    current_cells = get_enemy_occupied_positions(enemy)
    if (
        previous_position == (enemy.column, enemy.row)
        or not current_cells & zone_cells
    ):
        return False

    triggered_cells = current_cells & zone_cells
    player.archer_barrage_zone_cells = [
        cell
        for cell in player.archer_barrage_zone_cells
        if cell not in triggered_cells
    ]

    shot_origin = _archer_barrage_visual_origin(
        game_state,
        enemy,
    )
    shot_target = (
        enemy.column,
        enemy.row,
    )
    player.archer_barrage_shots.append(
        ArcherBarrageShotState(
            origin=shot_origin,
            target=shot_target,
        )
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            target=enemy.name,
            origin=shot_origin,
            positions=(shot_target,),
            data={"kind": "archer_barrage_zone"},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"Barrage Zone fires at {enemy.name}.",
    )
    previous_health = enemy.health
    enemy_was_defeated = attack_enemy(
        game_state,
        enemy,
        ARCHER_EMPOWERED_SHOT_DAMAGE_MIN,
        ARCHER_EMPOWERED_SHOT_DAMAGE_MAX,
        player.crit_chance,
        attacker_position=shot_origin,
        grant_ability_charge=False,
    )
    dealt_damage = enemy.health < previous_health

    if enemy.type == "oracle":
        from bosses.oracle import resolve_oracle_hit_reaction

        resolve_oracle_hit_reaction(
            enemy,
            game_state.floor,
            game_state.combat_log,
        )
    if enemy_was_defeated:
        resolve_enemy_defeat(game_state, enemy)

    return dealt_damage


def request_assassin_teleport(game_state: GameState) -> bool:
    player = game_state.player

    if player.subclass != "assassin":
        return False

    if player.teleport_aiming:
        player.teleport_aiming = False
        add_log_message(
            game_state.combat_log,
            "Teleport aiming cancelled.",
        )
        return True

    if player.teleport_charge < ASSASSIN_TELEPORT_CHARGES:
        add_log_message(
            game_state.combat_log,
            "Teleport is not charged.",
        )
        return True

    player.teleport_aiming = True
    add_log_message(
        game_state.combat_log,
        "Choose a free cell for teleportation.",
    )
    return True


def cancel_assassin_teleport(game_state: GameState) -> None:
    game_state.player.teleport_aiming = False
    game_state.player.teleport_target = None
    add_log_message(
        game_state.combat_log,
        "Teleport aiming cancelled.",
    )


def is_valid_assassin_teleport_target(
    game_state: GameState,
    column: int,
    row: int,
) -> bool:
    floor = game_state.floor

    if game_state.player.subclass != "assassin":
        return False
    if not game_state.player.teleport_aiming:
        return False
    if not (0 <= row < len(floor.map)):
        return False
    if not (0 <= column < len(floor.map[0])):
        return False
    if floor.map[row][column] in ("#", "C"):
        return False
    if (column, row) == (floor.player_column, floor.player_row):
        return False
    if any(
        enemy.health > 0
        and (column, row) in get_enemy_occupied_positions(enemy)
        for enemy in floor.enemies
    ):
        return False
    if any(
        not chest.is_open
        and (column, row) == (chest.column, chest.row)
        for chest in floor.chests
    ):
        return False
    return True


def request_assassin_ultimate(game_state: GameState) -> bool:
    player = game_state.player

    if player.subclass != "assassin":
        return False

    if player.ultimate_aiming:
        player.ultimate_aiming = False
        player.ultimate_targets.clear()
        player.ultimate_visual_variants.clear()
        add_log_message(
            game_state.combat_log,
            "Ultimate targeting cancelled.",
        )
        return True

    if player.ultimate_charge < ASSASSIN_ULTIMATE_CHARGES:
        add_log_message(
            game_state.combat_log,
            "Killing Spree is not charged.",
        )
        return True

    player.ultimate_aiming = True
    player.ultimate_targets.clear()
    add_log_message(
        game_state.combat_log,
        "Choose up to five targets for Killing Spree.",
    )
    return True


def cancel_assassin_ultimate(game_state: GameState) -> None:
    game_state.player.ultimate_aiming = False
    game_state.player.ultimate_targets.clear()
    game_state.player.ultimate_visual_variants.clear()
    add_log_message(
        game_state.combat_log,
        "Ultimate targeting cancelled.",
    )


def select_assassin_ultimate_target(
    game_state: GameState,
    enemy_name: str,
) -> bool:
    player = game_state.player
    if not player.ultimate_aiming:
        return False
    enemy = next(
        (
            enemy
            for enemy in game_state.floor.enemies
            if enemy.name == enemy_name and enemy.health > 0
        ),
        None,
    )
    if enemy is None:
        return False

    player.ultimate_targets.append(enemy_name)
    add_log_message(
        game_state.combat_log,
        f"Target {len(player.ultimate_targets)}/5: {enemy.name}.",
    )
    return True


def begin_assassin_ultimate(
    game_state: GameState,
    current_time: int,
) -> bool:
    player = game_state.player
    if not player.ultimate_aiming or not player.ultimate_targets:
        return False

    player.ultimate_aiming = False
    player.ultimate_charge = 0
    player.ultimate_visual_variants = []
    previous_variant = None
    for _ in player.ultimate_targets:
        available_variants = [
            variant
            for variant in range(3)
            if variant != previous_variant
        ]
        previous_variant = random.choice(available_variants)
        player.ultimate_visual_variants.append(previous_variant)
    player.ultimate_animation_started_at = current_time
    player.ultimate_animation_active = True
    add_log_message(
        game_state.combat_log,
        "Killing Spree begins.",
    )
    return True


def resolve_assassin_ultimate(
    game_state: GameState,
    oracle_hit_reaction: OracleHitReaction,
) -> None:
    player = game_state.player
    selected_targets = tuple(player.ultimate_targets)
    player.ultimate_targets.clear()
    player.ultimate_visual_variants.clear()

    for enemy_name in selected_targets:
        enemy = next(
            (
                enemy
                for enemy in game_state.floor.enemies
                if enemy.name == enemy_name and enemy.health > 0
            ),
            None,
        )
        if enemy is None:
            continue

        enemy_was_defeated = attack_enemy(
            game_state,
            enemy,
            player.damage_min,
            player.damage_max,
            player.crit_chance,
            attacker_position=(
                game_state.floor.player_column,
                game_state.floor.player_row,
            ),
        )
        if enemy.type == "oracle":
            oracle_hit_reaction(
                enemy,
                game_state.floor,
                game_state.combat_log,
            )
        if enemy_was_defeated:
            resolve_enemy_defeat(game_state, enemy)


def cast_directional_ability(
    game_state: GameState,
    column_change: int,
    row_change: int,
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    player = game_state.player
    floor = game_state.floor

    if player.player_class not in ("warrior", "mage"):
        return False

    player.directional_ability_aiming = False
    player.ability_kill_charge = 0
    blocking_positions = {
        (chest["column"], chest["row"])
        for chest in floor.chests
        if not chest["is_open"]
    }

    if player.player_class == "warrior":
        maximum_range = 1
        damage_bonus = WARRIOR_STRIKE_DAMAGE_BONUS
        ability_name = "power strike"
    else:
        maximum_range = MAGE_SPELL_RANGE
        damage_bonus = MAGE_SPELL_DAMAGE_BONUS
        ability_name = "arcane burst"

    game_state.player_attack_targets = get_directional_line(
        floor.map,
        floor.player_column,
        floor.player_row,
        column_change,
        row_change,
        maximum_range,
        blocking_positions,
    )
    ability_targets = [
        enemy
        for enemy in floor.enemies
        if (
            enemy.health > 0
            and any(
                position in get_enemy_occupied_positions(enemy)
                for position in game_state.player_attack_targets
            )
        )
    ]

    if not ability_targets:
        add_log_message(
            game_state.combat_log,
            f"The {ability_name} hits nothing.",
        )

    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(floor.player_column, floor.player_row),
            positions=tuple(game_state.player_attack_targets),
            data={
                "kind": "ability",
                "ability": ability_name,
            },
        )
    )

    for ability_target in ability_targets:
        enemy_was_defeated = attack_enemy(
            game_state,
            ability_target,
            player.damage_min,
            player.damage_max,
            player.crit_chance,
            damage_bonus=damage_bonus,
            attacker_position=(
                floor.player_column,
                floor.player_row,
            ),
        )

        if ability_target.type == "oracle":
            oracle_hit_reaction(
                ability_target,
                floor,
                game_state.combat_log,
            )

        if enemy_was_defeated:
            resolve_enemy_defeat(
                game_state,
                ability_target,
            )

    return True
