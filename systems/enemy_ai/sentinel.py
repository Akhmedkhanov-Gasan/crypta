from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState
from logic import (
    can_player_move_between,
    get_enemy_occupied_positions,
    has_line_of_sight,
)


KNOCKBACK_DISTANCE = 2
WALL_COLLISION_DAMAGE = 1
CRATE_COLLISION_DAMAGE = 2


def try_raise_shield(
    game_state,
    enemy,
    shield_is_ready,
    distance_to_player,
):
    floor = game_state.floor
    state = enemy.sentinel

    if (
        not shield_is_ready
        or state.shield_raised
        or state.shield_broken
        or distance_to_player > 3
        or not has_line_of_sight(
            floor.map,
            enemy.column,
            enemy.row,
            floor.player_column,
            floor.player_row,
        )
    ):
        return False

    state.shield_raised = True
    enemy.shield_blocks_remaining = enemy.shield_durability

    add_log_message(
        game_state.combat_log,
        f"{enemy.name} raises its shield.",
        category="defense",
    )
    return True


def break_sentinel_shield(game_state, enemy):
    state = enemy.sentinel
    state.shield_broken = True
    state.recovery_turns = 1
    enemy.shield_blocks_remaining = 0
    enemy.move_every = 1
    enemy.move_counter = 0

    if enemy.prepared_attack_mode == "shield_bash":
        enemy.attack_targets = []
        enemy.prepared_attack_mode = None
        enemy.attack_windup_turns_remaining = 0
        enemy.behavior_state = EnemyBehaviorState.CHASING

    add_log_message(
        game_state.combat_log,
        f"{enemy.name}'s shield shatters. It advances more aggressively.",
        category="defense",
    )


def take_sentinel_turn(
    game_state,
    enemy,
    occupied_positions,
    attack_blocking_positions,
    hazard_costs,
):
    from systems.enemy_ai.common import (
        move_toward_player,
        movement_is_ready,
        prepare_enemy_attack,
    )

    floor = game_state.floor

    def prepare_attack():
        target = (floor.player_column, floor.player_row)
        direction = (
            target[0] - enemy.column,
            target[1] - enemy.row,
        )

        if (
            max(abs(direction[0]), abs(direction[1])) != 1
            or target in attack_blocking_positions
            or not can_player_move_between(
                floor.map,
                enemy.column,
                enemy.row,
                target[0],
                target[1],
                floor.barriers,
            )
        ):
            return False

        use_shield = (
            enemy.shield_blocks_remaining > 0
            and not enemy.sentinel.shield_broken
            and enemy.last_attack_mode != "shield_bash"
        )
        mode = "shield_bash" if use_shield else "melee"
        enemy.sentinel.bash_direction = direction
        enemy.last_attack_mode = mode
        enemy.prepared_attack_target = "hero"

        prepare_enemy_attack(game_state, enemy, [target], mode)
        return True

    if prepare_attack():
        return

    if enemy.is_immobile or not movement_is_ready(enemy):
        return

    move_toward_player(
        game_state,
        enemy,
        occupied_positions,
        hazard_costs,
    )

    if enemy.health > 0:
        prepare_attack()


def apply_sentinel_knockback(game_state, enemy):
    from acts.act_two.crates import break_crate
    from systems.player_combat import damage_player

    floor = game_state.floor
    player = game_state.player
    origin = (floor.player_column, floor.player_row)
    direction = enemy.sentinel.bash_direction

    if direction == (0, 0):
        return

    occupied = {
        position
        for candidate in floor.enemies
        if candidate.health > 0
        for position in get_enemy_occupied_positions(candidate)
    }
    occupied.update(
        (chest.column, chest.row)
        for chest in floor.chests
        if not chest.is_open
    )

    if (
        player.summoner_familiar_active
        and player.summoner_familiar_position is not None
    ):
        occupied.add(player.summoner_familiar_position)

    crates = {
        (crate.column, crate.row): crate
        for crate in floor.breakable_crates
        if not crate.is_broken
    }
    position = origin
    collision_position = None
    collision_damage = 0

    for _ in range(KNOCKBACK_DISTANCE):
        destination = (
            position[0] + direction[0],
            position[1] + direction[1],
        )

        if (
            not can_player_move_between(
                floor.map,
                position[0],
                position[1],
                destination[0],
                destination[1],
                floor.barriers,
            )
            or destination in occupied
        ):
            collision_position = destination
            collision_damage = WALL_COLLISION_DAMAGE
            break

        crate = crates.get(destination)
        if crate is not None:
            break_crate(game_state, crate, cause="shield_bash")
            position = destination
            collision_position = destination
            collision_damage = CRATE_COLLISION_DAMAGE
            break

        position = destination

    floor.player_column, floor.player_row = position
    player.stun_turns = max(player.stun_turns, 1)

    game_state.emit(
        GameEvent(
            type=GameEventType.MOVE,
            actor="hero",
            origin=origin,
            destination=position,
            data={
                "kind": "sentinel_shield_knockback",
                "direction": direction,
                "collided": collision_position is not None,
            },
        )
    )
    add_log_message(
        game_state.combat_log,
        f"{enemy.name} knocks the hero back and stuns them for one turn.",
        category="enemy_attack",
    )

    if collision_damage:
        damage = damage_player(
            game_state,
            collision_damage,
            damage_kind="physical",
        )
        game_state.emit(
            GameEvent(
                type=GameEventType.HIT,
                actor=enemy.name,
                target="hero",
                origin=collision_position,
                destination=position,
                amount=damage,
                data={
                    "mode": "shield_collision",
                    "enemy_type": enemy.type,
                },
            )
        )
        add_log_message(
            game_state.combat_log,
            f"The collision deals {damage} additional damage.",
            category="enemy_attack",
        )
