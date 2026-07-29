import random
from collections.abc import Callable
from math import ceil

from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import (
    EnemyBehaviorState,
    EnemyState,
    FloorState,
    GameState,
)
from logic import (
    direction_toward,
    get_directional_line,
    get_enemy_occupied_positions,
    has_line_of_sight,
    roll_player_damage,
)
from settings import (
    ARCHER_BASIC_ATTACK_RANGE,
    ARCHER_BASIC_DAMAGE_MAX,
    ARCHER_BASIC_DAMAGE_MIN,
    ARCHER_EMPOWERED_SHOT_CHARGES,
    ARCHER_BARRAGE_ZONE_CHARGES,
    ARCHER_LEAP_CHARGES,
    BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER,
    BERSERKER_RAGE_CRITICAL_HEALTH_RATIO,
    BERSERKER_CRUSHING_LEAP_CHARGES,
    BERSERKER_LAST_RAGE_CHARGES,
    BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER,
    BERSERKER_RAGE_INJURED_HEALTH_RATIO,
    CLASS_ABILITY_KILLS,
    PALADIN_HOLY_HAND_CHARGES,
    PALADIN_HOLY_SHIELD_CHARGES,
    PALADIN_HOLY_SHIELD_DAMAGE_BONUS,
    PALADIN_HOLY_SHIELD_HEALING_PER_HIT,
    PALADIN_SHIELD_CHARGE_CHARGES,
    WARLOCK_BASIC_ATTACK_RANGE,
    WARLOCK_BASIC_DAMAGE_MAX,
    WARLOCK_BASIC_DAMAGE_MIN,
    WARLOCK_DEMON_FORM_DAMAGE_MULTIPLIER,
    WARLOCK_CURSE_CHARGES,
    WARLOCK_CURSE_DAMAGE_MULTIPLIER,
    WARLOCK_SOUL_EXCHANGE_CHARGES,
)
from settings import ASSASSIN_TELEPORT_CHARGES
from settings import ASSASSIN_ULTIMATE_CHARGES


OracleHitReaction = Callable[
    [EnemyState, FloorState, list[str]],
    None,
]


def damage_player(
    game_state: GameState,
    damage: int,
) -> int:
    player = game_state.player
    if (
        player.subclass == "paladin"
        and player.paladin_holy_shield_turns > 0
    ):
        damage = ceil(damage / 2)
    previous_health = player.health
    minimum_health = (
        1
        if (
            player.subclass == "berserker"
            and player.berserker_last_rage_turns > 0
        )
        else 0
    )
    player.health = max(
        minimum_health,
        player.health - damage,
    )
    damage_dealt = previous_health - player.health

    if (
        damage_dealt > 0
        and player.subclass == "berserker"
        and player.berserker_last_rage_turns <= 0
    ):
        player.berserker_last_rage_charge = min(
            BERSERKER_LAST_RAGE_CHARGES,
            player.berserker_last_rage_charge + 1,
        )

    return damage_dealt


def is_valid_archer_attack_target(
    game_state: GameState,
    target_cell: tuple[int, int],
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if player.subclass != "archer":
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

    distance = abs(target_cell[0] - floor.player_column) + abs(
        target_cell[1] - floor.player_row
    )
    return (
        distance <= ARCHER_BASIC_ATTACK_RANGE
        and has_line_of_sight(
            floor.map,
            floor.player_column,
            floor.player_row,
            target_cell[0],
            target_cell[1],
        )
    )


def is_valid_warlock_attack_target(
    game_state: GameState,
    target_cell: tuple[int, int],
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if player.subclass != "warlock":
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

    distance = abs(
        target_cell[0] - floor.player_column
    ) + abs(
        target_cell[1] - floor.player_row
    )
    return (
        distance <= WARLOCK_BASIC_ATTACK_RANGE
        and has_line_of_sight(
            floor.map,
            floor.player_column,
            floor.player_row,
            target_cell[0],
            target_cell[1],
        )
    )


def perform_warlock_attack(
    game_state: GameState,
    target_cell: tuple[int, int],
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    if not is_valid_warlock_attack_target(
        game_state,
        target_cell,
    ):
        return False

    player = game_state.player
    floor = game_state.floor
    hit_enemy = next(
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
        and target_cell in get_enemy_occupied_positions(enemy)
    )
    game_state.player_attack_targets = [target_cell]
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(
                floor.player_column,
                floor.player_row,
            ),
            positions=(target_cell,),
            data={"kind": "warlock_orb"},
        )
    )
    enemy_was_defeated = attack_enemy(
        game_state,
        hit_enemy,
        ceil(
            WARLOCK_BASIC_DAMAGE_MIN
            * (
                WARLOCK_DEMON_FORM_DAMAGE_MULTIPLIER
                if player.warlock_demon_form_active
                else 1
            )
        ),
        ceil(
            WARLOCK_BASIC_DAMAGE_MAX
            * (
                WARLOCK_DEMON_FORM_DAMAGE_MULTIPLIER
                if player.warlock_demon_form_active
                else 1
            )
        ),
        player.crit_chance,
        attacker_position=(
            floor.player_column,
            floor.player_row,
        ),
    )
    if hit_enemy.type == "oracle":
        oracle_hit_reaction(
            hit_enemy,
            floor,
            game_state.combat_log,
        )
    if enemy_was_defeated:
        resolve_enemy_defeat(game_state, hit_enemy)
    return True


def perform_archer_attack(
    game_state: GameState,
    target_cell: tuple[int, int],
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    if not is_valid_archer_attack_target(game_state, target_cell):
        return False

    player = game_state.player
    floor = game_state.floor
    hit_enemy = next(
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
        and target_cell in get_enemy_occupied_positions(enemy)
    )
    game_state.player_attack_targets = [target_cell]
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(floor.player_column, floor.player_row),
            positions=(target_cell,),
            data={"kind": "archer_basic"},
        )
    )
    enemy_was_defeated = attack_enemy(
        game_state,
        hit_enemy,
        ARCHER_BASIC_DAMAGE_MIN,
        ARCHER_BASIC_DAMAGE_MAX,
        player.crit_chance,
        attacker_position=(floor.player_column, floor.player_row),
    )
    if hit_enemy.type == "oracle":
        oracle_hit_reaction(
            hit_enemy,
            floor,
            game_state.combat_log,
        )
    if enemy_was_defeated:
        resolve_enemy_defeat(game_state, hit_enemy)
    return True


def attack_enemy(
    game_state: GameState,
    enemy: EnemyState,
    damage_minimum: int,
    damage_maximum: int,
    critical_chance: float,
    damage_bonus: int = 0,
    force_critical: bool = False,
    attacker_position: tuple[int, int] | None = None,
    grant_ability_charge: bool = True,
) -> bool:
    player = game_state.player
    if (
        enemy.type == "sentinel"
        and enemy.shield_turns > 0
        and attacker_position is not None
    ):
        attack_direction = direction_toward(
            enemy.column,
            enemy.row,
            attacker_position[0],
            attacker_position[1],
        )
        shield_direction = enemy.shield_direction
        vulnerable_direction = (
            -shield_direction[0],
            -shield_direction[1],
        )

        if attack_direction != vulnerable_direction:
            add_log_message(
                game_state.combat_log,
                f"{enemy.name}'s shield blocks the attack.",
            )
            return False

    damage = (
        roll_player_damage(damage_minimum, damage_maximum)
        + damage_bonus
    )
    if enemy.curse_turns > 0:
        damage = ceil(
            damage * WARLOCK_CURSE_DAMAGE_MULTIPLIER
        )
    if player.subclass == "berserker" and player.health > 0:
        health_ratio = player.health / player.max_health
        if (
            player.berserker_last_rage_turns > 0
            or health_ratio
            <= BERSERKER_RAGE_CRITICAL_HEALTH_RATIO
        ):
            damage = ceil(
                damage
                * BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER
            )
        elif health_ratio <= BERSERKER_RAGE_INJURED_HEALTH_RATIO:
            damage = ceil(
                damage
                * BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER
            )
    elif (
        player.subclass == "paladin"
        and player.paladin_holy_shield_turns > 0
    ):
        damage += PALADIN_HOLY_SHIELD_DAMAGE_BONUS
    critical_hit = (
        force_critical
        or random.random() < critical_chance
    )

    if critical_hit:
        damage *= 2

    enemy.health = max(0, enemy.health - damage)
    if (
        player.subclass == "paladin"
        and player.paladin_holy_shield_turns > 0
        and player.health < player.max_health
    ):
        previous_health = player.health
        player.health = min(
            player.max_health,
            player.health
            + PALADIN_HOLY_SHIELD_HEALING_PER_HIT,
        )
        healing = player.health - previous_health
        game_state.emit(
            GameEvent(
                type=GameEventType.HEAL,
                actor="hero",
                target="hero",
                destination=attacker_position,
                amount=healing,
                data={"kind": "paladin_holy_shield"},
            )
        )
        add_log_message(
            game_state.combat_log,
            f"Holy Shield restores {healing} health.",
        )
    if (
        grant_ability_charge
        and player.subclass == "assassin"
        and not player.ultimate_animation_active
    ):
        player.ability_kill_charge = min(
            CLASS_ABILITY_KILLS,
            player.ability_kill_charge + 1,
        )
        player.teleport_charge = min(
            ASSASSIN_TELEPORT_CHARGES,
            player.teleport_charge + 1,
        )
        player.ultimate_charge = min(
            ASSASSIN_ULTIMATE_CHARGES,
            player.ultimate_charge + 1,
        )
    elif grant_ability_charge and player.subclass == "archer":
        player.archer_empowered_shot_charge = min(
            ARCHER_EMPOWERED_SHOT_CHARGES,
            player.archer_empowered_shot_charge + 1,
        )
        player.archer_leap_charge = min(
            ARCHER_LEAP_CHARGES,
            player.archer_leap_charge + 1,
        )
        player.archer_barrage_zone_charge = min(
            ARCHER_BARRAGE_ZONE_CHARGES,
            player.archer_barrage_zone_charge + 1,
        )
    elif grant_ability_charge and player.subclass == "berserker":
        player.berserker_crushing_leap_charge = min(
            BERSERKER_CRUSHING_LEAP_CHARGES,
            player.berserker_crushing_leap_charge + 1,
        )
        if player.berserker_last_rage_turns <= 0:
            player.berserker_last_rage_charge = min(
                BERSERKER_LAST_RAGE_CHARGES,
                player.berserker_last_rage_charge + 1,
            )
    elif grant_ability_charge and player.subclass == "paladin":
        player.paladin_holy_hand_charge = min(
            PALADIN_HOLY_HAND_CHARGES,
            player.paladin_holy_hand_charge + 1,
        )
        player.paladin_shield_charge_charge = min(
            PALADIN_SHIELD_CHARGE_CHARGES,
            player.paladin_shield_charge_charge + 1,
        )
        if player.paladin_holy_shield_turns <= 0:
            player.paladin_holy_shield_charge = min(
                PALADIN_HOLY_SHIELD_CHARGES,
                player.paladin_holy_shield_charge + 1,
            )
    elif grant_ability_charge and player.subclass == "warlock":
        player.warlock_curse_charge = min(
            WARLOCK_CURSE_CHARGES,
            player.warlock_curse_charge + 1,
        )
        player.warlock_soul_exchange_charge = min(
            WARLOCK_SOUL_EXCHANGE_CHARGES,
            player.warlock_soul_exchange_charge + 1,
        )
    game_state.emit(
        GameEvent(
            type=GameEventType.HIT,
            actor="hero",
            target=enemy.name,
            origin=attacker_position,
            destination=(enemy.column, enemy.row),
            amount=damage,
            data={"critical": critical_hit},
        )
    )

    if critical_hit:
        add_log_message(
            game_state.combat_log,
            f"Critical hit on {enemy.name} for {damage}!",
        )
    else:
        add_log_message(
            game_state.combat_log,
            f"Hero hits {enemy.name} for {damage}.",
        )

    if (
        enemy.type in ("warden", "oracle")
        and enemy.health > 0
        and enemy.health <= enemy.max_health // 2
        and not enemy.second_phase_announced
    ):
        enemy.second_phase_announced = True

        if enemy.type == "oracle":
            enemy.phase_transition_pending = True

        add_log_message(
            game_state.combat_log,
            f"{enemy.name} enters phase two!",
        )

    if enemy.health <= 0:
        enemy.behavior_state = EnemyBehaviorState.DEAD
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor=enemy.name,
                destination=(enemy.column, enemy.row),
            )
        )
        add_log_message(
            game_state.combat_log,
            f"{enemy.name} is defeated.",
        )
        return True

    return False


def resolve_enemy_defeat(
    game_state: GameState,
    enemy: EnemyState,
) -> None:
    player = game_state.player
    floor = game_state.floor
    player.enemies_defeated += 1

    if enemy.type == "oracle":
        floor.projectiles.clear()

        if (
            player.player_class in ("warrior", "rogue")
            and player.subclass is None
        ):
            game_state.act_three_transition_open = True
            game_state.act_three_transition_started_at = 0
            game_state.act_three_visual_started_at = 0
            game_state.player_attack_targets = []
            add_log_message(
                game_state.combat_log,
                "The second veil begins to fall.",
            )

    if player.player_class is not None and player.subclass != "assassin":
        player.ability_kill_charge = min(
            CLASS_ABILITY_KILLS,
            player.ability_kill_charge + 1,
        )

    if not enemy.has_key:
        return

    floor.dropped_keys.append((enemy.column, enemy.row))
    enemy.has_key = False
    add_log_message(
        game_state.combat_log,
        f"{enemy.name} drops a key.",
    )


def perform_basic_attack(
    game_state: GameState,
    column_change: int,
    row_change: int,
    oracle_hit_reaction: OracleHitReaction,
) -> None:
    player = game_state.player
    floor = game_state.floor
    attack_was_from_invisibility = (
        player.player_class == "rogue"
        and player.invisibility_turns > 0
    )

    if attack_was_from_invisibility:
        player.invisibility_turns = 0
        add_log_message(
            game_state.combat_log,
            "The rogue emerges to attack.",
        )

    blocking_positions = {
        (chest["column"], chest["row"])
        for chest in floor.chests
        if not chest["is_open"]
    }
    game_state.player_attack_targets = get_directional_line(
        floor.map,
        floor.player_column,
        floor.player_row,
        column_change,
        row_change,
        1,
        blocking_positions,
    )
    living_enemies = [
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
    ]
    enemies_hit = [
        enemy
        for enemy in living_enemies
        if any(
            position in get_enemy_occupied_positions(enemy)
            for position in game_state.player_attack_targets
        )
    ]
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(floor.player_column, floor.player_row),
            positions=tuple(game_state.player_attack_targets),
            data={"kind": "basic"},
        )
    )

    for hit_enemy in enemies_hit:
        enemy_was_defeated = attack_enemy(
            game_state,
            hit_enemy,
            player.damage_min,
            player.damage_max,
            player.crit_chance,
            force_critical=attack_was_from_invisibility,
            attacker_position=(
                floor.player_column,
                floor.player_row,
            ),
        )

        if hit_enemy.type == "oracle":
            oracle_hit_reaction(
                hit_enemy,
                floor,
                game_state.combat_log,
            )

        if enemy_was_defeated:
            resolve_enemy_defeat(
                game_state,
                hit_enemy,
            )
