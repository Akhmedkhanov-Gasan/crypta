from game.combat_log import add_log_message
from game.state import EnemyState, GameState
from logic import (
    can_move_between,
    direction_toward,
    get_enemy_occupied_positions,
    has_line_of_sight,
)


SENTINEL_COUNTER_KNOCKBACK_DISTANCE = 2


def try_raise_shield(
    game_state: GameState,
    enemy: EnemyState,
    shield_is_ready: bool,
    distance_to_player: int,
) -> bool:
    floor = game_state.floor

    if (
        not shield_is_ready
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

    enemy.shield_blocks_remaining = (
        enemy.shield_durability
    )

    add_log_message(
        game_state.combat_log,
        (
            f"{enemy.name} raises its shield "
            f"with {enemy.shield_durability} guard."
        ),
        category="defense",
    )
    return True


def sentinel_counter_knockback_destination(
    game_state: GameState,
    sentinel: EnemyState,
) -> tuple[tuple[int, int], bool]:
    floor = game_state.floor
    origin = (
        floor.player_column,
        floor.player_row,
    )
    direction = direction_toward(
        sentinel.column,
        sentinel.row,
        origin[0],
        origin[1],
    )

    blocking_positions = {
        position
        for enemy in floor.enemies
        if enemy.health > 0
        for position in get_enemy_occupied_positions(enemy)
    }
    blocking_positions.update(
        (chest.column, chest.row)
        for chest in floor.chests
        if not chest.is_open
    )
    blocking_positions.update(
        (crate.column, crate.row)
        for crate in floor.breakable_crates
        if not crate.is_broken
    )

    if (
        game_state.player.summoner_familiar_active
        and game_state.player.summoner_familiar_position
        is not None
    ):
        blocking_positions.add(
            game_state.player.summoner_familiar_position
        )

    current_position = origin
    collided = False

    for _ in range(SENTINEL_COUNTER_KNOCKBACK_DISTANCE):
        destination = (
            current_position[0] + direction[0],
            current_position[1] + direction[1],
        )

        if (
            not can_move_between(
                floor.map,
                current_position[0],
                current_position[1],
                destination[0],
                destination[1],
                floor.barriers,
            )
            or destination in blocking_positions
        ):
            collided = True
            break

        current_position = destination

    return current_position, collided
