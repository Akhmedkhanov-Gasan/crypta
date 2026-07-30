from collections.abc import Callable
import random

from game.combat_log import add_log_message
from game.state import (
    EnemyState,
    FloorState,
    GameState,
)
from logic import get_enemy_occupied_positions
from settings import (
    ASSASSIN_TELEPORT_CHARGES,
    ASSASSIN_ULTIMATE_CHARGES,
)
from systems.player_combat import (
    attack_enemy,
    resolve_enemy_defeat,
)


OracleHitReaction = Callable[
    [EnemyState, FloorState, list[str]],
    None,
]

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
