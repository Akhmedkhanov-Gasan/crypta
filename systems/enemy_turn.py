import random

from acts.act_three.ai import (
    _familiar_is_preferred_target,
    _take_familiar_target_turn,
)
from acts.act_three.abilities.archer import (
    resolve_archer_barrage_zone_entry,
)
from acts.act_three.abilities.summoner import (
    damage_summoner_familiar,
    resolve_summoner_familiar_turn,
)
from bosses.oracle import update_oracle_projectiles
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState, GameState
from logic import (
    distance_between,
    get_enemy_occupied_positions,
    move_enemy_randomly,
    roll_enemy_damage,
    update_enemy_aggro,
    has_line_of_sight,
)
from systems.enemy_ai import (
    note_warden_attack_completed,
    resolve_warden_reposition,
    take_archer_turn,
    take_oracle_turn,
    take_standard_turn,
    take_warden_turn,
    try_raise_shield,
    try_start_healing,
    priest_should_join_combat,
    take_brute_turn,
    take_goblin_turn,
    goblin_should_join_combat,
    take_priest_turn,
    resolve_goblin_summon,
)
from systems.player_combat import damage_player, resolve_enemy_defeat


def _advance_enemy_bleed(game_state: GameState, enemy) -> bool:
    if enemy.bleed_turns <= 0 or enemy.bleed_damage <= 0:
        return False

    damage = min(enemy.health, enemy.bleed_damage)
    enemy.health -= damage
    enemy.bleed_turns -= 1
    game_state.emit(
        GameEvent(
            type=GameEventType.HIT,
            actor="bleed",
            target=enemy.name,
            destination=(enemy.column, enemy.row),
            amount=damage,
            data={
                "critical": False,
                "blocked": False,
                "player_class": "rogue",
                "enemy_type": enemy.type,
                "kind": "bleed",
            },
        )
    )
    add_log_message(
        game_state.combat_log,
        f"{enemy.name} bleeds for {damage} damage.",
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

    if enemy.health > 0:
        return False

    enemy.behavior_state = EnemyBehaviorState.DEAD
    game_state.emit(
        GameEvent(
            type=GameEventType.DEATH,
            actor=enemy.name,
            destination=(enemy.column, enemy.row),
            data={"enemy_type": enemy.type, "cause": "bleed"},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"{enemy.name} bleeds out.",
    )
    resolve_enemy_defeat(game_state, enemy)
    return True


def resolve_enemy_turn(
    game_state: GameState,
    player_position_before_action: tuple[int, int],
    rogue_ability_activated: bool,
    hazard_costs: dict[tuple[int, int], int] | None = None,
    goblin_summoning_enabled: bool = False,
) -> None:
    if hazard_costs is None:
        hazard_costs = {}
    update_oracle_projectiles(game_state)
    resolve_summoner_familiar_turn(game_state)

    if game_state.player.health <= 0:
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor="hero",
                destination=(
                    game_state.floor.player_column,
                    game_state.floor.player_row,
                ),
                data={"cause": "projectile"},
            )
        )
        (
            game_state.floor["player_column"],
            game_state.floor["player_row"],
        ) = player_position_before_action
        add_log_message(
            game_state.combat_log,
            "The hero has fallen.",
        )
    damaged_enemy_names = {
        event.target
        for event in game_state.events
        if (
                event.type is GameEventType.HIT
                and event.target is not None
                and event.amount is not None
                and event.amount > 0
        )
    }
    for enemy in tuple(game_state.floor.enemies):
        if game_state.player.health <= 0:
            break
        if enemy["health"] <= 0:
            enemy.behavior_state = EnemyBehaviorState.DEAD
            continue
        if not enemy["is_active"]:
            enemy.behavior_state = EnemyBehaviorState.INACTIVE
            continue

        if (
                enemy.behavior_state
                is EnemyBehaviorState.PREPARING_SUMMON
                and enemy.name in damaged_enemy_names
        ):
            enemy.behavior_state = EnemyBehaviorState.CHASING
            enemy.summon_windup_turns_remaining = 0
            enemy.summon_animation_started_at = -1

            add_log_message(
                game_state.combat_log,
                f"{enemy.name}'s summoning ritual is interrupted.",
            )
            continue

        if _advance_enemy_bleed(game_state, enemy):
            continue
        if enemy.stun_turns > 0:
            enemy.stun_turns -= 1
            enemy.attack_targets = []
            enemy.prepared_attack_mode = None
            enemy.attack_windup_turns_remaining = 0
            enemy.heal_target = None
            if enemy.stun_turns == 0:
                add_log_message(
                    game_state.combat_log,
                    f"{enemy.name} recovers from the stun.",
                )
            continue
        if game_state.player.invisibility_turns > 0:
            enemy["is_aggro"] = False
            enemy.behavior_state = EnemyBehaviorState.IDLE
            enemy["attack_targets"] = []
            enemy["prepared_attack_mode"] = None
            enemy.attack_windup_turns_remaining = 0
            enemy["heal_target"] = None
            continue
        if enemy.skip_next_movement:
            enemy.skip_next_movement = False
            enemy.attack_targets = []
            enemy.prepared_attack_mode = None
            enemy.attack_windup_turns_remaining = 0
            enemy.heal_target = None
            continue
        if enemy.binding_turns > 0:
            enemy.binding_turns -= 1
            enemy.attack_targets = []
            enemy.prepared_attack_mode = None
            enemy.attack_windup_turns_remaining = 0
            if enemy.binding_turns == 0:
                add_log_message(
                    game_state.combat_log,
                    f"{enemy.name} breaks free of the binding.",
                )
            continue

        if (
            enemy.type == "warden"
            and resolve_warden_reposition(game_state, enemy)
        ):
            continue
        if (
                enemy.behavior_state
                is EnemyBehaviorState.PREPARING_SUMMON
        ):
            if not goblin_summoning_enabled:
                enemy.behavior_state = EnemyBehaviorState.CHASING
                enemy.summon_windup_turns_remaining = 0
                enemy.summon_animation_started_at = -1
                continue

            if enemy.summon_windup_turns_remaining > 0:
                enemy.summon_windup_turns_remaining -= 1
                continue

            resolve_goblin_summon(
                game_state,
                enemy,
                hazard_costs,
            )
            continue
        if (
            enemy.behavior_state
            is EnemyBehaviorState.PREPARING_ATTACK
        ):
            if enemy.attack_windup_turns_remaining > 0:
                enemy.attack_windup_turns_remaining -= 1
                continue

            attack_targets = enemy["attack_targets"]
            attack_mode = enemy["prepared_attack_mode"]
            enemy["attack_targets"] = []
            enemy["prepared_attack_mode"] = None
            enemy.attack_windup_turns_remaining = 0
            enemy.behavior_state = EnemyBehaviorState.CHASING
            game_state.emit(
                GameEvent(
                    type=GameEventType.ATTACK,
                    actor=enemy.name,
                    origin=(enemy.column, enemy.row),
                    positions=tuple(attack_targets),
                    data={
                        "mode": attack_mode,
                        "enemy_type": enemy.type,
                    },
                )
            )

            if enemy.prepared_attack_target == "familiar":
                enemy.prepared_attack_target = "hero"
                familiar_position = (
                    game_state.player.summoner_familiar_position
                )
                if (
                    familiar_position is not None
                    and game_state.player.summoner_familiar_active
                    and familiar_position in attack_targets
                ):
                    damage = roll_enemy_damage(
                        enemy,
                        attack_mode,
                    )
                    damage = damage_summoner_familiar(
                        game_state,
                        damage,
                    )
                    game_state.emit(
                        GameEvent(
                            type=GameEventType.HIT,
                            actor=enemy.name,
                            target="familiar",
                            origin=(enemy.column, enemy.row),
                            destination=familiar_position,
                            amount=damage,
                            data={"mode": attack_mode},
                        )
                    )
                    add_log_message(
                        game_state.combat_log,
                        (
                            f"{enemy.name} hits the familiar "
                            f"for {damage}."
                        ),
                    )
                else:
                    add_log_message(
                        game_state.combat_log,
                        f"{enemy.name} misses the familiar.",
                    )
                continue

            if (
                game_state.floor["player_column"],
                game_state.floor["player_row"],
            ) in attack_targets:
                is_lethal_oracle_shockwave = (
                    enemy["type"] == "oracle"
                    and attack_mode == "shockwave"
                )

                if (
                    not is_lethal_oracle_shockwave
                    and random.random()
                    < game_state.player.dodge_chance
                ):
                    game_state.emit(
                        GameEvent(
                            type=GameEventType.DODGE,
                            actor=enemy.name,
                            target="hero",
                            origin=(enemy.column, enemy.row),
                            destination=(
                                game_state.floor.player_column,
                                game_state.floor.player_row,
                            ),
                            data={"mode": attack_mode},
                        )
                    )
                    add_log_message(
                        game_state.combat_log,
                        (
                            f"Hero dodges "
                            f"{enemy['name']}'s attack."
                        ),
                    )
                else:
                    damage = (
                        game_state.player.health
                        if is_lethal_oracle_shockwave
                        else roll_enemy_damage(
                            enemy,
                            attack_mode,
                        )
                    )
                    damage = damage_player(
                        game_state,
                        damage,
                        damage_kind=(
                            "magic"
                            if (
                                enemy.type
                                in ("priest", "priest_ghost", "oracle")
                                and attack_mode != "melee"
                            )
                            else "physical"
                        ),
                    )
                    if game_state.player.invisibility_turns > 0:
                        game_state.player.invisibility_turns = 0
                        add_log_message(
                            game_state.combat_log,
                            "The rogue becomes visible after taking damage.",
                        )
                    game_state.emit(
                        GameEvent(
                            type=GameEventType.HIT,
                            actor=enemy.name,
                            target="hero",
                            origin=(enemy.column, enemy.row),
                            destination=(
                                game_state.floor.player_column,
                                game_state.floor.player_row,
                            ),
                            amount=damage,
                            data={"mode": attack_mode},
                        )
                    )
                    add_log_message(
                        game_state.combat_log,
                        (
                            f"{enemy['name']} hits hero "
                            f"for {damage}."
                        ),
                    )
            else:
                add_log_message(
                    game_state.combat_log,
                    f"{enemy['name']} misses.",
                )

            if game_state.player.health <= 0:
                game_state.emit(
                    GameEvent(
                        type=GameEventType.DEATH,
                        actor="hero",
                        destination=(
                            game_state.floor.player_column,
                            game_state.floor.player_row,
                        ),
                        data={"cause": enemy.name},
                    )
                )
                (
                    game_state.floor["player_column"],
                    game_state.floor["player_row"],
                ) = player_position_before_action
                add_log_message(
                    game_state.combat_log,
                    "The hero has fallen.",
                )
                break

            if enemy.type == "warden":
                note_warden_attack_completed(
                    game_state,
                    enemy,
                )

            continue

        if (
            enemy.behavior_state
            is EnemyBehaviorState.PREPARING_HEAL
            and enemy["heal_target"] is not None
        ):
            heal_target = enemy["heal_target"]
            enemy["heal_target"] = None
            enemy.behavior_state = EnemyBehaviorState.CHASING

            if (
                heal_target.health > 0
                and heal_target.curse_turns > 0
            ):
                enemy.heal_cooldown = (
                    enemy.heal_cooldown_duration
                )
                add_log_message(
                    game_state.combat_log,
                    (
                        f"The curse prevents healing "
                        f"{heal_target.name}."
                    ),
                )
                continue

            if (
                    heal_target.health > 0
                    and heal_target.health < heal_target.max_health
                    and distance_between(
                enemy.column,
                enemy.row,
                heal_target.column,
                heal_target.row,
            )
                    <= enemy.heal_range
                    and has_line_of_sight(
                game_state.floor.map,
                enemy.column,
                enemy.row,
                heal_target.column,
                heal_target.row,
            )
            ):
                previous_health = heal_target["health"]
                heal_target["health"] = min(
                    heal_target["max_health"],
                    heal_target["health"]
                    + enemy["heal_amount"],
                )
                healed_amount = (
                    heal_target["health"]
                    - previous_health
                )
                game_state.emit(
                    GameEvent(
                        type=GameEventType.HEAL,
                        actor=enemy.name,
                        target=heal_target.name,
                        origin=(enemy.column, enemy.row),
                        destination=(
                            heal_target.column,
                            heal_target.row,
                        ),
                        amount=healed_amount,
                        data={"enemy_type": enemy.type},
                    )
                )
                enemy["heal_cooldown"] = (
                    enemy[
                        "heal_cooldown_duration"
                    ]
                )
                add_log_message(
                    game_state.combat_log,
                    (
                        f"{enemy['name']} heals "
                        f"{heal_target['name']} "
                        f"for {healed_amount}."
                    ),
                )
                continue

        if (
            enemy.behavior_state
            is EnemyBehaviorState.GUARDING
        ):
            if enemy["shield_turns"] > 0:
                enemy["shield_turns"] -= 1

            if enemy["shield_turns"] == 0:
                enemy["shield_direction"] = None
                enemy["shield_cooldown"] = (
                    enemy[
                        "shield_cooldown_duration"
                    ]
                )
                add_log_message(
                    game_state.combat_log,
                    (
                        f"{enemy['name']} "
                        "lowers its shield."
                    ),
                )
                enemy.behavior_state = (
                    EnemyBehaviorState.CHASING
                )

            continue

        enemy_was_aggro = enemy.is_aggro

        update_enemy_aggro(
            game_state.floor.map,
            enemy,
            game_state.floor.player_column,
            game_state.floor.player_row,
        )

        priest_joined_to_support = (
                enemy.type == "priest"
                and not enemy.is_aggro
                and priest_should_join_combat(
                    enemy,
                    game_state.floor.enemies,
                )
        )

        goblin_joined_to_support = (
            enemy.type == "goblin"
            and not enemy.is_aggro
            and goblin_should_join_combat(
                game_state,
                enemy,
            )
        )

        if (
            priest_joined_to_support
            or goblin_joined_to_support
        ):
            enemy.is_aggro = True

        if not enemy_was_aggro and enemy.is_aggro:
            enemy.behavior_state = EnemyBehaviorState.CHASING

            if priest_joined_to_support:
                message = (
                    f"{enemy.name} joins the fight "
                    "to support its allies."
                )
            elif goblin_joined_to_support:
                message = (
                    f"{enemy.name} answers "
                    "the pack's battle cry."
                )
            else:
                message = f"{enemy.name} spots the hero."

            add_log_message(
                game_state.combat_log,
                message,
            )

        occupied_positions = {
            position
            for other_enemy in game_state.floor["enemies"]
            if (
                other_enemy is not enemy
                and other_enemy["health"] > 0
            )
            for position
            in get_enemy_occupied_positions(
                other_enemy
            )
        }
        occupied_positions.update(
            (chest["column"], chest["row"])
            for chest in game_state.floor["chests"]
            if not chest["is_open"]
        )
        occupied_positions.update(
            (crate.column, crate.row)
            for crate in game_state.floor.breakable_crates
            if not crate.is_broken
        )
        occupied_positions.add(
            (
                game_state.floor["stairs_column"],
                game_state.floor["stairs_row"],
            )
        )
        occupied_positions.add(
            (
                game_state.floor.player_column,
                game_state.floor.player_row,
            )
        )
        if (
            game_state.player.summoner_familiar_active
            and game_state.player.summoner_familiar_position
            is not None
        ):
            occupied_positions.add(
                game_state.player.summoner_familiar_position
            )
        reserved_leap_target = (
            game_state.player.berserker_crushing_leap_target
        )
        if reserved_leap_target is not None:
            occupied_positions.add(reserved_leap_target)
        attack_blocking_positions = {
            (chest["column"], chest["row"])
            for chest in game_state.floor["chests"]
            if not chest["is_open"]
        }
        attack_blocking_positions.update(
            (crate.column, crate.row)
            for crate in game_state.floor.breakable_crates
            if not crate.is_broken
        )

        if _familiar_is_preferred_target(game_state, enemy):
            enemy.is_aggro = True
            enemy.behavior_state = EnemyBehaviorState.CHASING
            _take_familiar_target_turn(
                game_state,
                enemy,
                occupied_positions,
                attack_blocking_positions,
            )
            continue

        if not enemy["is_aggro"]:
            enemy.behavior_state = EnemyBehaviorState.IDLE
            previous_position = (enemy.column, enemy.row)
            (
                enemy["column"],
                enemy["row"],
            ) = move_enemy_randomly(
                game_state.floor.map,
                enemy,
                game_state.floor.player_column,
                game_state.floor.player_row,
                occupied_positions,
                game_state.floor.barriers,
                hazard_costs,
            )
            if enemy.movement_bounds is not None:
                left, top, right, bottom = enemy.movement_bounds
                if not (
                    left <= enemy.column <= right
                    and top <= enemy.row <= bottom
                ):
                    enemy.column, enemy.row = previous_position
            new_position = (enemy.column, enemy.row)

            if new_position != previous_position:
                game_state.emit(
                    GameEvent(
                        type=GameEventType.MOVE,
                        actor=enemy.name,
                        origin=previous_position,
                        destination=new_position,
                        data={"kind": "wander"},
                    )
                )
                resolve_archer_barrage_zone_entry(
                    game_state,
                    enemy,
                    previous_position,
                )
                if enemy.health <= 0:
                    continue
            enemy_was_aggro = enemy["is_aggro"]
            update_enemy_aggro(
                game_state.floor["map"],
                enemy,
                game_state.floor["player_column"],
                game_state.floor["player_row"],
            )

            if (
                not enemy_was_aggro
                and enemy["is_aggro"]
            ):
                enemy.behavior_state = (
                    EnemyBehaviorState.CHASING
                )
                add_log_message(
                    game_state.combat_log,
                    f"{enemy['name']} spots the hero.",
                )

        if (
            enemy.behavior_state
            is not EnemyBehaviorState.CHASING
        ):
            continue

        shield_is_ready = enemy.shield_cooldown == 0
        heal_is_ready = enemy.heal_cooldown == 0

        if enemy.shield_cooldown > 0:
            enemy.shield_cooldown -= 1

        if enemy.heal_cooldown > 0:
            enemy.heal_cooldown -= 1

        distance_to_player = distance_between(
            enemy.column,
            enemy.row,
            game_state.floor.player_column,
            game_state.floor.player_row,
        )

        if enemy.type == "oracle":
            take_oracle_turn(
                game_state,
                enemy,
                attack_blocking_positions,
            )
            continue

        if (
            enemy.type == "sentinel"
            and try_raise_shield(
                game_state,
                enemy,
                shield_is_ready,
                distance_to_player,
            )
        ):
            continue

        if (
            enemy.type == "priest"
            and try_start_healing(
                game_state,
                enemy,
                occupied_positions,
                heal_is_ready,
            )
        ):
            continue

        if enemy.type == "warden":
            take_warden_turn(
                game_state,
                enemy,
                occupied_positions,
                attack_blocking_positions,
            )
        elif enemy.type == "archer":
            take_archer_turn(
                game_state,
                enemy,
                occupied_positions,
                attack_blocking_positions,
                distance_to_player,
                hazard_costs,
            )
        elif enemy.type == "brute":
            take_brute_turn(
                game_state,
                enemy,
                occupied_positions,
                attack_blocking_positions,
                hazard_costs,
            )
        elif enemy.type == "priest":
            take_priest_turn(
                game_state,
                enemy,
                occupied_positions,
                attack_blocking_positions,
                hazard_costs,
            )
        elif enemy.type == "goblin":
            take_goblin_turn(
                game_state,
                enemy,
                occupied_positions,
                attack_blocking_positions,
                hazard_costs,
                summoning_enabled=goblin_summoning_enabled,
            )
        else:
            take_standard_turn(
                game_state,
                enemy,
                occupied_positions,
                attack_blocking_positions,
                hazard_costs,
            )

    if (
        game_state.player.invisibility_turns > 0
        and not rogue_ability_activated
    ):
        game_state.player.invisibility_turns -= 1

        if game_state.player.invisibility_turns == 0:
            add_log_message(
                game_state.combat_log,
                "The rogue becomes visible.",
            )
