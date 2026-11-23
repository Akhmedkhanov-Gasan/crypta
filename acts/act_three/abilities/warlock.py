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
    WARLOCK_DEMON_FORM_TRANSFORM_MS,
)
from acts.act_three.abilities.progression import (
    clear_ability_slot_charge,
    is_ability_slot_charged,
    is_ability_slot_unlocked,
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
    if (
        not is_ability_slot_charged(player, "q")
        or not is_valid_warlock_curse_target(game_state, target)
    ):
        player.warlock_curse_target = None
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
    from acts.act_three.abilities.warlock_runes import apply_curse_rune

    apply_curse_rune(game_state, target_enemy)
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
            f"{target_enemy.name} is maddened for {target_enemy.madness_turns} actions."
            if target_enemy.madness_turns else f"{target_enemy.name} is cursed for {target_enemy.curse_turns} turns."
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
            or enemy.name in game_state.player.act_three.warlock_newly_cursed_enemies
        ):
            continue
        enemy.curse_turns -= 1
        if enemy.curse_turns == 0:
            add_log_message(
                game_state.combat_log,
                f"The curse on {enemy.name} fades.",
            )

    game_state.player.warlock_newly_cursed_enemy = None
    game_state.player.act_three.warlock_newly_cursed_enemies.clear()


def request_warlock_demon_form(
    game_state: GameState,
    current_time: int,
) -> bool:
    player = game_state.player
    if player.subclass != "warlock" or not is_ability_slot_unlocked(player, "f"):
        return False

    if player.health <= 0:
        return False

    transition_elapsed = (
        current_time - player.warlock_demon_form_started_at
    )
    if (
        player.warlock_demon_form_target_active is not None
        and 0
        <= transition_elapsed
        < WARLOCK_DEMON_FORM_TRANSFORM_MS
    ):
        return False

    target_active = not player.warlock_demon_form_active
    from acts.act_three.rune_master.definitions import equipped_rune

    if player.act_three.warlock_eternal_bound:
        add_log_message(game_state.combat_log, "Eternal Form cannot be reversed during this run.", category="rune")
        return False
    rune = equipped_rune(player, "f")
    free = rune is not None and rune.id == "rune_of_blood_pact"

    if (
        target_active
        and not free
        and not is_ability_slot_charged(player, "f")
    ):
        add_log_message(
            game_state.combat_log,
            "Demon Form is not charged.",
        )
        return False

    player.warlock_demon_form_active = target_active
    player.warlock_demon_form_target_active = target_active
    player.warlock_demon_form_started_at = current_time
    player.warlock_curse_aiming = False
    player.warlock_curse_target = None
    game_state.player_attack_targets.clear()

    if target_active:
        player.act_three.warlock_demon_rune = rune.id if rune else None
        player.act_three.warlock_eternal_bound = rune is not None and rune.id == "rune_of_eternal_form"
        clear_ability_slot_charge(player, "f")
    player.act_three.warlock_blood_attacks = 0
    player.act_three.warlock_demon_healing_progress = 0.0

    add_log_message(
        game_state.combat_log,
        (
            "The warlock embraces the Demon Form."
            if target_active
            else "The warlock releases the Demon Form."
        ),
    )
    return True

