from collections.abc import Callable
from enum import Enum, auto

from acts.act_two.abilities import (
    ability_charge_required,
    clear_act_two_ability_selection,
    get_warrior_cleave_cells,
)
from acts.act_two.progression import (
    get_warrior_upgrade_rank,
)
from acts.act_two.settings import (
    MAGE_ARCANE_BURST_BASE_DAMAGE_BONUS,
    MAGE_ARCANE_BURST_RANGE,
    MAGE_ARCANE_BURST_SPELL_POWER_SCALING,
    WARRIOR_CLEAVE_DAMAGE_BONUS,
    WARRIOR_CLEAVE_DAMAGE_PER_RANK,
)
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
    ASSASSIN_INVISIBILITY_TURNS,
    ROGUE_INVISIBILITY_TURNS,
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

    required_charge = ability_charge_required(player)
    if player.ability_kill_charge < required_charge:
        add_log_message(
            game_state.combat_log,
            (
                "Class ability is not charged "
                f"({player.ability_kill_charge}/{required_charge} hits)."
            ),
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
        clear_act_two_ability_selection(game_state)
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
    clear_act_two_ability_selection(game_state)
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
    blocking_positions = {
        (chest["column"], chest["row"])
        for chest in floor.chests
        if not chest["is_open"]
    }
    blocking_positions.update(
        (crate.column, crate.row)
        for crate in floor.breakable_crates
        if not crate.is_broken
    )

    if player.player_class == "warrior":
        maximum_range = 1
        cleave_rank = get_warrior_upgrade_rank(
            player,
            "warrior_cleave",
        )
        rhythm_rank = get_warrior_upgrade_rank(
            player,
            "warrior_rhythm",
        )
        damage_bonus = (
            WARRIOR_CLEAVE_DAMAGE_BONUS
            + cleave_rank * WARRIOR_CLEAVE_DAMAGE_PER_RANK
        )
        ability_name = "power cleave"
        player.ability_kill_charge = rhythm_rank
    else:
        maximum_range = MAGE_ARCANE_BURST_RANGE
        damage_bonus = (
            MAGE_ARCANE_BURST_BASE_DAMAGE_BONUS
            + player.spell_power
            * MAGE_ARCANE_BURST_SPELL_POWER_SCALING
        )
        ability_name = "arcane burst"
        player.ability_kill_charge = 0

    if player.player_class == "warrior":
        game_state.player_attack_targets = get_warrior_cleave_cells(
            floor,
            column_change,
            row_change,
        )
    else:
        game_state.player_attack_targets = get_directional_line(
            floor.map,
            floor.player_column,
            floor.player_row,
            column_change,
            row_change,
            maximum_range,
            blocking_positions,
        )
    player.act_two.selected_ability_direction = None
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
            grant_ability_charge=False,
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
