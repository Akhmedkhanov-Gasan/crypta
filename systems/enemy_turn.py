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
)
from systems.enemy_ai import (
    take_archer_turn,
    take_oracle_turn,
    take_standard_turn,
    try_raise_shield,
    try_start_healing,
)
from systems.player_combat import damage_player


def resolve_enemy_turn(
    game_state: GameState,
    player_position_before_action: tuple[int, int],
    rogue_ability_activated: bool,
) -> None:
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

    for enemy in game_state.floor["enemies"]:
        if game_state.player.health <= 0:
            break
        if enemy["health"] <= 0:
            enemy.behavior_state = EnemyBehaviorState.DEAD
            continue
        if not enemy["is_active"]:
            enemy.behavior_state = EnemyBehaviorState.INACTIVE
            continue
        if game_state.player.invisibility_turns > 0:
            enemy["is_aggro"] = False
            enemy.behavior_state = EnemyBehaviorState.IDLE
            enemy["attack_targets"] = []
            enemy["prepared_attack_mode"] = None
            enemy["heal_target"] = None
            continue

        if (
            enemy.behavior_state
            is EnemyBehaviorState.PREPARING_ATTACK
        ):
            attack_targets = enemy["attack_targets"]
            attack_mode = enemy["prepared_attack_mode"]
            enemy["attack_targets"] = []
            enemy["prepared_attack_mode"] = None
            enemy.behavior_state = EnemyBehaviorState.CHASING
            game_state.emit(
                GameEvent(
                    type=GameEventType.ATTACK,
                    actor=enemy.name,
                    origin=(enemy.column, enemy.row),
                    positions=tuple(attack_targets),
                    data={"mode": attack_mode},
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
                heal_target["health"] > 0
                and heal_target["health"]
                < heal_target["max_health"]
                and distance_between(
                    enemy["column"],
                    enemy["row"],
                    heal_target["column"],
                    heal_target["row"],
                )
                == 1
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

        enemy_was_aggro = enemy["is_aggro"]
        update_enemy_aggro(
            game_state.floor["map"],
            enemy,
            game_state.floor["player_column"],
            game_state.floor["player_row"],
        )

        if not enemy_was_aggro and enemy["is_aggro"]:
            enemy.behavior_state = EnemyBehaviorState.CHASING
            add_log_message(
                game_state.combat_log,
                f"{enemy['name']} spots the hero.",
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
                game_state.floor["map"],
                enemy,
                game_state.floor["player_column"],
                game_state.floor["player_row"],
                occupied_positions,
            )
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

        if enemy.type == "archer":
            take_archer_turn(
                game_state,
                enemy,
                occupied_positions,
                attack_blocking_positions,
                distance_to_player,
            )
        else:
            take_standard_turn(
                game_state,
                enemy,
                occupied_positions,
                attack_blocking_positions,
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
