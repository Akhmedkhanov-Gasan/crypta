from collections.abc import Callable

from game.combat_log import add_log_message
from acts.act_three.events import GameEvent, GameEventType
from game.state import (
    EnemyState,
    FloorState,
    GameState,
)
from logic import (
    direction_toward,
    get_enemy_occupied_positions,
    has_line_of_sight,
)
from acts.act_three.settings import (
    WARLOCK_CURSE_RANGE,
    WARLOCK_CURSE_TURNS,
    WARLOCK_DEMON_FORM_HEALTH_DRAIN,
    WARLOCK_DEMON_FORM_TRANSFORM_MS,
)
from acts.act_three.abilities.progression import (
    clear_ability_slot_charge,
    is_ability_slot_charged,
)

OracleHitReaction = Callable[
    [EnemyState, FloorState, list[str]],
    None,
]

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

    if not is_ability_slot_charged(player, "q"):
        add_log_message(
            game_state.combat_log,
            "Curse is not charged.",
        )
        return True

    player.warlock_curse_aiming = True
    player.warlock_curse_target = None
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
    current_time: int,
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
    player.facing_direction = direction_toward(
        floor.player_column,
        floor.player_row,
        target[0],
        target[1],
    )
    player.attack_animation_started_at = current_time
    player.warlock_curse_started_at = current_time
    player.warlock_curse_effect_target = target
    target_enemy.curse_turns = WARLOCK_CURSE_TURNS
    clear_ability_slot_charge(player, "q")
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


def request_warlock_demon_form(
    game_state: GameState,
    current_time: int,
) -> bool:
    player = game_state.player
    if player.subclass != "warlock":
        return False

    if player.health <= 0:
        return True

    transition_elapsed = (
        current_time - player.warlock_demon_form_started_at
    )
    if (
        player.warlock_demon_form_target_active is not None
        and 0
        <= transition_elapsed
        < WARLOCK_DEMON_FORM_TRANSFORM_MS
    ):
        return True

    target_active = not player.warlock_demon_form_active

    if (
        target_active
        and not is_ability_slot_charged(player, "f")
    ):
        add_log_message(
            game_state.combat_log,
            "Demon Form is not charged.",
        )
        return True

    player.warlock_demon_form_active = target_active
    player.warlock_demon_form_target_active = target_active
    player.warlock_demon_form_started_at = current_time
    player.warlock_curse_aiming = False
    player.warlock_curse_target = None
    game_state.player_attack_targets.clear()

    if target_active:
        clear_ability_slot_charge(player, "f")

    add_log_message(
        game_state.combat_log,
        (
            "The warlock embraces the Demon Form."
            if target_active
            else "The warlock releases the Demon Form."
        ),
    )
    return True

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
