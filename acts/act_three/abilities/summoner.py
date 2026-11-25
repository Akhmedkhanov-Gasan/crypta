from collections.abc import Callable
from acts.act_three.ability_scaling import familiar_damage_range

from game.combat_log import add_log_message
from acts.act_three.abilities.progression import is_ability_slot_unlocked
from acts.act_three.events import GameEvent, GameEventType
from game.state import (
    EnemyState,
    FloorState,
    GameState,
)
from logic import (
    can_player_move_between,
    get_enemy_occupied_positions,
)
from acts.act_three.settings import (
    SUMMONER_FAMILIAR_CHARGES,
    SUMMONER_TRUE_FORM_CHARGES,
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
        or (player.summoner_familiar_active and player.act_three.summoner_possession_host is None)
    ):
        return ()
    from acts.act_three.abilities.summoner_runes import absorption_active, familiar_rune_mode

    mode = familiar_rune_mode(player)
    if mode == "totem":
        from acts.act_three.abilities.summoner_totem import totem_targets

        return totem_targets(game_state)
    if mode == "possession":
        from acts.act_three.abilities.summoner_possession import possession_targets

        return possession_targets(game_state)

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

    spirit = player.act_three.summoner_manifestation
    if spirit is not None and spirit["health"] > 0 and spirit["floor"] == game_state.floor_index:
        occupied_positions.add(tuple(spirit["position"]))

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
    from acts.act_three.abilities.summoner_runes import familiar_rune_mode

    if target is not None and familiar_rune_mode(player) != "possession":
        from acts.act_three.abilities.summoner_targeting import adjacent_direction_target

        target = adjacent_direction_target(game_state, target)
    if not player.summoner_familiar_summon_aiming or target is None:
        return False

    player.summoner_familiar_summon_target = target
    return target in summoner_familiar_summon_targets(game_state)


def select_summoner_familiar_summon_direction(
    game_state: GameState,
    direction: tuple[int, int],
) -> bool:
    origin = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    from acts.act_three.abilities.summoner_runes import familiar_rune_mode

    mode = familiar_rune_mode(game_state.player)
    if mode == "possession":
        targets = summoner_familiar_summon_targets(game_state)
        forward = [cell for cell in targets if (cell[0] - origin[0]) * direction[0] + (cell[1] - origin[1]) * direction[1] > 0]
        forward.sort(key=lambda cell: (max(abs(cell[0] - origin[0]), abs(cell[1] - origin[1])), cell))
        if forward:
            selected = game_state.player.summoner_familiar_summon_target
            index = (forward.index(selected) + 1) % len(forward) if selected in forward else 0
            return select_summoner_familiar_summon_target(game_state, forward[index])
        return False
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
    if player.subclass != "summoner" or not is_ability_slot_unlocked(player, "q"):
        return False
    from acts.act_three.abilities.summoner_runes import absorption_active, familiar_recharge_requirement

    if player.act_three.summoner_loss_turns > 0:
        add_log_message(game_state.combat_log, f"The familiar recovers in {player.act_three.summoner_loss_turns} turns.", category="warning")
        return False
    if player.act_three.summoner_possession_host is not None:
        from acts.act_three.abilities.summoner_possession import possession_targets

        targets = possession_targets(game_state)
        if not targets:
            add_log_message(game_state.combat_log, "No other host is available. The current host remains bound.", category="warning")
            return False
        player.summoner_familiar_summon_aiming = True
        player.summoner_familiar_summon_target = targets[0]
        add_log_message(game_state.combat_log, "Choose a new host and confirm with Q. Escape keeps the current host.", category="ability")
        return True

    if player.summoner_familiar_active:
        player.summoner_true_form_active = False
        if player.summoner_familiar_health > 0:
            from acts.act_three.abilities.summoner_targeting import record_familiar_recall

            record_familiar_recall(game_state)
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
        < familiar_recharge_requirement(player)
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
            "No valid familiar cells or possession targets are available.",
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
    from acts.act_three.abilities.summoner_runes import familiar_rune_mode

    player.summoner_familiar_summon_target = summon_targets[0] if familiar_rune_mode(player) == "possession" else facing_target
    add_log_message(
        game_state.combat_log,
        "Choose a familiar cell or a Possession target, then press Q again.",
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
            "Choose an available familiar cell or host.",
        )
        return False

    from acts.act_three.abilities.summoner_runes import familiar_recharge_requirement, familiar_rune_mode

    if player.act_three.summoner_possession_host is None and (player.act_three.summoner_loss_turns > 0 or (not player.debug_unlimited_abilities and player.summoner_familiar_charge < familiar_recharge_requirement(player))):
        return False
    mode = familiar_rune_mode(player)
    if mode == "possession":
        from acts.act_three.abilities.summoner_possession import possess_enemy

        return possess_enemy(game_state, target_position, current_time)
    player.act_three.summoner_familiar_mode = mode
    player.act_three.summoner_entity_floor = game_state.floor_index
    player.act_three.summoner_rune_started_at = current_time
    player.act_three.summoner_totem_anchor = target_position if mode == "totem" else None
    player.act_three.summoner_recall_requirement = 0
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
    player.summoner_familiar_death_true_form = False
    player.summoner_true_form_active = False
    player.summoner_true_form_started_at = -1
    player.summoner_true_form_ending_started_at = -1
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


def request_greater_manifestation(game_state: GameState, current_time: int) -> bool:
    player = game_state.player
    if player.subclass != "summoner" or not is_ability_slot_unlocked(player, "f"):
        return False
    from acts.act_three.abilities.summoner_ultimate import activate_summoner_ultimate

    return activate_summoner_ultimate(game_state, current_time)

def resolve_summoner_familiar_turn(game_state: GameState) -> None:
    from acts.act_three.abilities.greater_manifestation import take_manifestation_turn

    take_manifestation_turn(game_state)
    player = game_state.player
    floor = game_state.floor
    if player.subclass == "summoner" and player.act_three.summoner_loss_turns > 0:
        player.act_three.summoner_loss_turns -= 1
        if player.act_three.summoner_loss_turns == 0:
            player.summoner_familiar_charge = SUMMONER_FAMILIAR_CHARGES
    familiar_position = player.summoner_familiar_position
    if (
        player.subclass != "summoner"
        or not player.summoner_familiar_active
        or familiar_position is None
        or player.health <= 0
        or player.summoner_familiar_health <= 0
    ):
        return

    if player.summoner_familiar_skip_turn:
        player.summoner_familiar_skip_turn = False
        player.summoner_familiar_attack_target = None
        return

    if not player.summoner_true_form_active:
        if player.act_three.summoner_familiar_mode == "totem":
            from acts.act_three.abilities.summoner_totem import take_totem_turn

            take_totem_turn(game_state)
            return
        if player.act_three.summoner_familiar_mode == "possession":
            from acts.act_three.abilities.summoner_possession import take_possession_turn

            take_possession_turn(game_state)
            return

    player.summoner_familiar_attack_target = None
    from acts.act_three.abilities.summoner_follow import plan_companion_turn

    target_enemy, cells, candidate = plan_companion_turn(game_state, familiar_position)
    if target_enemy is not None:
        player.summoner_familiar_attack_started_at = player.familiar_turn_started_at
        player.summoner_familiar_attack_target = cells[0]
        game_state.emit(GameEvent(type=GameEventType.ATTACK, actor="familiar", origin=familiar_position,
                                  positions=cells, data={"kind": "summoner_familiar"}))
        damage_minimum, damage_maximum = familiar_damage_range(player)
        if attack_enemy(game_state, target_enemy, damage_minimum, damage_maximum, 0.0,
                        attacker_position=familiar_position, grant_ability_charge=False, attacker_name="familiar"):
            resolve_enemy_defeat(game_state, target_enemy)
        return
    if candidate == familiar_position:
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
    *,
    penalty_multiplier=1,
) -> int:
    player = game_state.player
    if player.act_three.summoner_possession_host is not None:
        from acts.act_three.abilities.summoner_possession import damage_host

        return damage_host(game_state, damage)
    if (
        not player.summoner_familiar_active
        or player.summoner_familiar_health <= 0
    ):
        return 0

    familiar_position = player.summoner_familiar_position
    familiar_was_true_form = (
        player.summoner_true_form_active
    )
    previous_health = player.summoner_familiar_health
    current_health = max(0, previous_health - damage)
    player.summoner_familiar_health = current_health
    damage_dealt = previous_health - current_health
    from acts.act_three.abilities.summoner_runes import summoner_ultimate_active

    if damage_dealt > 0 and not summoner_ultimate_active(player) and is_ability_slot_unlocked(player, "f"):
        player.summoner_true_form_charge = min(
            SUMMONER_TRUE_FORM_CHARGES,
            player.summoner_true_form_charge + 1,
        )
    if player.summoner_familiar_health <= 0:
        from acts.act_three.abilities.summoner_runes import familiar_lost

        familiar_lost(player, penalty_multiplier)
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
        player.summoner_true_form_base_max_health = 0
        player.summoner_familiar_charge = 0.0
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
