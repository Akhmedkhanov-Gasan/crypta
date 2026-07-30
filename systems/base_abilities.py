from collections.abc import Callable
from enum import Enum, auto

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
)
from settings import (
    CLASS_ABILITY_KILLS,
    ASSASSIN_INVISIBILITY_TURNS,
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
