from collections.abc import Callable
from enum import Enum, auto
import random

from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import (
    EnemyBehaviorState,
    EnemyState,
    FloorState,
    GameState,
)
from logic import (
    get_directional_line,
    get_enemy_occupied_positions,
    has_line_of_sight,
)
from settings import (
    CLASS_ABILITY_KILLS,
    ASSASSIN_INVISIBILITY_TURNS,
    ASSASSIN_TELEPORT_CHARGES,
    ASSASSIN_ULTIMATE_CHARGES,
    ARCHER_EMPOWERED_SHOT_CHARGES,
    ARCHER_EMPOWERED_SHOT_DAMAGE_MAX,
    ARCHER_EMPOWERED_SHOT_DAMAGE_MIN,
    MAGE_SPELL_DAMAGE_BONUS,
    MAGE_SPELL_RANGE,
    ROGUE_INVISIBILITY_TURNS,
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
