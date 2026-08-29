from collections.abc import Callable
from enum import Enum, auto
from math import ceil

from acts.act_two.abilities import (
    ability_charge_required,
    clear_act_two_ability_selection,
    get_mage_arcane_burst_cells,
    get_warrior_cleave_cells,
    is_valid_mage_arcane_burst_target,
)
from acts.act_two.bloody_altar import (
    BROKEN_SEAL,
    OPEN_WOUND,
    has_bloody_pact,
    open_wound_ability_is_affordable,
    pay_open_wound_ability_cost,
)
from acts.act_two.progression import (
    get_warrior_upgrade_rank,
)
from acts.act_two.settings import (
    MAGE_ARCANE_BURST_BASE_DAMAGE_BONUS,
    MAGE_ARCANE_BURST_EDGE_DAMAGE_MULTIPLIER,
    MAGE_ARCANE_BURST_SPELL_POWER_SCALING,
    MAGE_CONCENTRATION_DAMAGE_MULTIPLIER,
    MAGE_FRACTURE_DAMAGE_PER_NEIGHBOR,
    ROGUE_VEIL_DURATION_MULTIPLIER,
    WARRIOR_AFTERSHOCK_DAMAGE_MULTIPLIER,
    WARRIOR_CLEAVE_COLLISION_DAMAGE,
    WARRIOR_CLEAVE_DAMAGE_BONUS,
    WARRIOR_CLEAVE_DAMAGE_PER_RANK,
    WARRIOR_IMPACT_STUN_TURNS,
)
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import (
    EnemyBehaviorState,
    EnemyState,
    FloorState,
    GameState,
)
from logic import can_move_between, get_enemy_occupied_positions
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
            category="warning",
        )
        return AbilityRequestResult.NOT_READY

    if player.player_class == "rogue":
        if not pay_open_wound_ability_cost(game_state):
            return AbilityRequestResult.NOT_READY

        player.ability_kill_charge = 0
        invisibility_turns = (
            ASSASSIN_INVISIBILITY_TURNS
            if player.subclass == "assassin"
            else ROGUE_INVISIBILITY_TURNS
        )
        if (
            player.subclass is None
            and player.act_two.selected_rune_id == "rune_of_the_veil"
        ):
            invisibility_turns *= ROGUE_VEIL_DURATION_MULTIPLIER
        player.invisibility_turns = invisibility_turns

        for enemy in game_state.floor.enemies:
            enemy.is_aggro = False
            enemy.behavior_state = EnemyBehaviorState.IDLE
            enemy.attack_targets = []
            enemy.prepared_attack_mode = None
            enemy.attack_windup_turns_remaining = 0
            enemy.heal_target = None

        game_state.emit(
            GameEvent(
                type=GameEventType.ABILITY,
                actor="hero",
                destination=(
                    game_state.floor.player_column,
                    game_state.floor.player_row,
                ),
                data={"ability": "invisibility"},
            )
        )

        add_log_message(
            game_state.combat_log,
            "The rogue vanishes from sight.",
            category="ability",
        )
        return AbilityRequestResult.ROGUE_ACTIVATED
    if (
            player.player_class in ("warrior", "mage")
            and not player.directional_ability_aiming
            and not open_wound_ability_is_affordable(player)
    ):
        add_log_message(
            game_state.combat_log,
            "Not enough health to invoke Open Wound.",
            category="warning",
        )
        return AbilityRequestResult.NOT_READY
    if player.player_class in ("warrior", "mage"):
        player.directional_ability_aiming = (
            not player.directional_ability_aiming
        )
        clear_act_two_ability_selection(game_state)
        add_log_message(
            game_state.combat_log,
            (
                (
                    "Choose a target cell."
                    if player.player_class == "mage"
                    else "Choose an ability direction."
                )
                if player.directional_ability_aiming
                else "Ability aiming cancelled."
            ),
            category="ability",
        )
        return AbilityRequestResult.AIMING_TOGGLED

    return AbilityRequestResult.IGNORED

def cancel_ability_aiming(game_state: GameState) -> None:
    game_state.player.directional_ability_aiming = False
    game_state.player.act_two.ability_effect_target = None
    clear_act_two_ability_selection(game_state)
    add_log_message(
        game_state.combat_log,
        "Ability aiming cancelled.",
        category="ability",
    )


def _warrior_cleave_knockback(
    game_state: GameState,
    enemy: EnemyState,
    direction: tuple[int, int],
) -> tuple[tuple[int, int] | None, bool, bool]:
    """Return destination, collision state, and terrain collision state."""
    if (
        enemy.is_immobile
        or enemy.footprint_width != 1
        or enemy.footprint_height != 1
    ):
        return None, False, False

    floor = game_state.floor
    origin = (enemy.column, enemy.row)
    destination = (
        origin[0] + direction[0],
        origin[1] + direction[1],
    )
    if not can_move_between(
        floor.map,
        *origin,
        *destination,
        floor.barriers,
    ):
        return None, True, True

    enemy_positions = {
        position
        for other_enemy in floor.enemies
        if other_enemy is not enemy and other_enemy.health > 0
        for position in get_enemy_occupied_positions(other_enemy)
    }
    if destination in enemy_positions:
        return None, True, False

    occupied_positions = set(enemy_positions)
    occupied_positions.update(
        (chest.column, chest.row)
        for chest in floor.chests
        if not chest.is_open
    )
    occupied_positions.update(
        (crate.column, crate.row)
        for crate in floor.breakable_crates
        if not crate.is_broken
    )
    occupied_positions.add((floor.player_column, floor.player_row))
    occupied_positions.add((floor.stairs_column, floor.stairs_row))
    if (
        game_state.player.summoner_familiar_active
        and game_state.player.summoner_familiar_position is not None
    ):
        occupied_positions.add(
            game_state.player.summoner_familiar_position
        )

    if destination in occupied_positions:
        return None, False, False
    return destination, False, False


def _apply_forced_knockback(
    game_state: GameState,
    enemy: EnemyState,
    destination: tuple[int, int],
    movement_kind: str,
) -> None:
    origin = (enemy.column, enemy.row)
    enemy.column, enemy.row = destination
    enemy.skip_next_movement = True
    game_state.emit(
        GameEvent(
            type=GameEventType.MOVE,
            actor=enemy.name,
            origin=origin,
            destination=destination,
            data={"kind": movement_kind},
        )
    )

def cast_directional_ability(
    game_state: GameState,
    column_change: int,
    row_change: int,
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    player = game_state.player
    floor = game_state.floor

    if player.player_class != "warrior":
        return False
    if not pay_open_wound_ability_cost(game_state):
        player.directional_ability_aiming = False
        return False
    player.directional_ability_aiming = False
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
            + cleave_rank
            * WARRIOR_CLEAVE_DAMAGE_PER_RANK
    )
    ability_name = "power cleave"
    selected_rune_id = player.act_two.selected_rune_id
    game_state.player_attack_targets = get_warrior_cleave_cells(
        floor,
        column_change,
        row_change,
    )
    player.act_two.selected_ability_direction = None
    player.act_two.ability_effect_target = None
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
    player.act_two.ability_effect_cells = tuple(
        game_state.player_attack_targets
    )
    player.act_two.ability_effect_hit_positions = tuple(
        position
        for ability_target in ability_targets
        for position in get_enemy_occupied_positions(ability_target)
        if position in game_state.player_attack_targets
    )

    player.act_two.ability_effect_kind = "power_cleave"
    player.act_two.ability_effect_aftershock_positions = ()
    aftershock_positions = []
    if has_bloody_pact(player, BROKEN_SEAL):
        player.ability_kill_charge = 0
    else:
        player.ability_kill_charge = min(
            ability_charge_required(player),
            rhythm_rank
            + (
                len(ability_targets)
                if selected_rune_id == "rune_of_reaping"
                else 0
            ),
        )
    if selected_rune_id == "rune_of_reaping" and ability_targets:
        add_log_message(
            game_state.combat_log,
            f"Rune of Reaping restores {len(ability_targets)} charge.",
            category="rune",
        )

    add_log_message(
        game_state.combat_log,
        f"The {ability_name} hits nothing.",
        category="ability",
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
        knockback_destination = None
        knockback_collision = False
        terrain_blocks_knockback = False
        (
            knockback_destination,
            knockback_collision,
            terrain_blocks_knockback,
        ) = _warrior_cleave_knockback(
            game_state,
            ability_target,
            (column_change, row_change),
        )
        enemy_was_defeated = attack_enemy(
            game_state,
            ability_target,
            player.damage_min,
            player.damage_max,
            player.crit_chance,
            damage_bonus=(
                damage_bonus
                + (
                    WARRIOR_CLEAVE_COLLISION_DAMAGE
                    if terrain_blocks_knockback
                    else 0
                )
            ),
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

        if terrain_blocks_knockback and not enemy_was_defeated:
            add_log_message(
                game_state.combat_log,
                f"{ability_target.name} slams into the wall.",
                category="environment",
            )

        if (
            knockback_collision
            and not enemy_was_defeated
            and selected_rune_id == "rune_of_impact"
        ):
            ability_target.stun_turns = max(
                ability_target.stun_turns,
                WARRIOR_IMPACT_STUN_TURNS,
            )
            ability_target.skip_next_movement = False
            ability_target.attack_targets = []
            ability_target.prepared_attack_mode = None
            ability_target.attack_windup_turns_remaining = 0
            add_log_message(
                game_state.combat_log,
                f"Rune of Impact stuns {ability_target.name} for 2 turns.",
                category="rune",
            )

        if knockback_destination is not None and not enemy_was_defeated:
            _apply_forced_knockback(
                game_state,
                ability_target,
                knockback_destination,
                "power_cleave_knockback",
            )
            add_log_message(
                game_state.combat_log,
                f"Power Cleave knocks {ability_target.name} back.",
                category="ability",
            )

            if selected_rune_id == "rune_of_aftershock":
                aftershock_positions.append(knockback_destination)
                game_state.emit(
                    GameEvent(
                        type=GameEventType.ATTACK,
                        actor="hero",
                        origin=(floor.player_column, floor.player_row),
                        positions=(knockback_destination,),
                        data={
                            "kind": "aftershock",
                            "ability": "power cleave",
                        },
                    )
                )
                aftershock_minimum = max(
                    1,
                    ceil(
                        (player.damage_min + damage_bonus)
                        * WARRIOR_AFTERSHOCK_DAMAGE_MULTIPLIER
                    ),
                )
                aftershock_maximum = max(
                    aftershock_minimum,
                    ceil(
                        (player.damage_max + damage_bonus)
                        * WARRIOR_AFTERSHOCK_DAMAGE_MULTIPLIER
                    ),
                )
                aftershock_event_start = len(game_state.events)
                enemy_was_defeated = attack_enemy(
                    game_state,
                    ability_target,
                    aftershock_minimum,
                    aftershock_maximum,
                    player.crit_chance,
                    grant_ability_charge=False,
                    attacker_position=(
                        floor.player_column,
                        floor.player_row,
                    ),
                )
                for event in game_state.events[aftershock_event_start:]:
                    if (
                        event.type is GameEventType.HIT
                        and event.target == ability_target.name
                    ):
                        event.data["kind"] = "aftershock"
                    elif (
                        event.type is GameEventType.DEATH
                        and event.actor == ability_target.name
                    ):
                        event.data["cause"] = "aftershock"
                add_log_message(
                    game_state.combat_log,
                    f"Rune of Aftershock strikes {ability_target.name}.",
                    category="rune",
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

    player.act_two.ability_effect_aftershock_positions = tuple(
        aftershock_positions
    )
    return True


def _mage_burst_knockback_destination(
    game_state: GameState,
    enemy: EnemyState,
    center: tuple[int, int],
) -> tuple[int, int] | None:
    if (
        enemy.is_immobile
        or enemy.footprint_width != 1
        or enemy.footprint_height != 1
    ):
        return None

    direction = (
        enemy.column - center[0],
        enemy.row - center[1],
    )
    if direction not in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        return None

    floor = game_state.floor
    origin = (enemy.column, enemy.row)
    destination = (
        origin[0] + direction[0],
        origin[1] + direction[1],
    )
    if not can_move_between(
        floor.map,
        *origin,
        *destination,
        floor.barriers,
    ):
        return None

    occupied = {
        position
        for other_enemy in floor.enemies
        if other_enemy is not enemy and other_enemy.health > 0
        for position in get_enemy_occupied_positions(other_enemy)
    }
    occupied.update(
        (chest.column, chest.row)
        for chest in floor.chests
        if not chest.is_open
    )
    occupied.update(
        (crate.column, crate.row)
        for crate in floor.breakable_crates
        if not crate.is_broken
    )
    occupied.update(
        {
            (floor.player_column, floor.player_row),
            (floor.stairs_column, floor.stairs_row),
        }
    )
    if (
        game_state.player.summoner_familiar_active
        and game_state.player.summoner_familiar_position is not None
    ):
        occupied.add(game_state.player.summoner_familiar_position)
    return None if destination in occupied else destination


def cast_mage_arcane_burst(
    game_state: GameState,
    target: tuple[int, int],
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if (
        player.player_class != "mage"
        or not player.directional_ability_aiming
        or not is_valid_mage_arcane_burst_target(game_state, target)
    ):
        return False
    if not pay_open_wound_ability_cost(game_state):
        player.directional_ability_aiming = False
        return False

    concentration_active = (
        player.act_two.selected_rune_id == "rune_of_concentration"
    )
    player.directional_ability_aiming = False
    player.ability_kill_charge = 0
    player.act_two.selected_ability_direction = None
    player.act_two.ability_effect_target = None
    cells = (
        [target]
        if concentration_active
        else get_mage_arcane_burst_cells(floor, target)
    )
    game_state.player_attack_targets = cells
    player.act_two.ability_effect_target = target
    player.act_two.ability_effect_cells = tuple(cells)
    player.act_two.ability_effect_kind = (
        "concentration_release"
        if concentration_active
        else "arcane_burst"
    )

    targets = [
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
        and any(
            position in get_enemy_occupied_positions(enemy)
            for position in cells
        )
    ]
    player.act_two.ability_effect_hit_positions = tuple(
        position
        for enemy in targets
        for position in get_enemy_occupied_positions(enemy)
        if position in cells
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(floor.player_column, floor.player_row),
            positions=tuple(cells),
            data={"kind": "ability", "ability": "arcane burst"},
        )
    )
    if not targets:
        add_log_message(
            game_state.combat_log,
            "The arcane burst hits nothing.",
            category="ability",
        )

    full_damage_bonus = (
        MAGE_ARCANE_BURST_BASE_DAMAGE_BONUS
        + player.spell_power * MAGE_ARCANE_BURST_SPELL_POWER_SCALING
    )
    for enemy in targets:
        occupied = get_enemy_occupied_positions(enemy)
        center_hit = target in occupied
        if center_hit:
            if concentration_active:
                damage_minimum = ceil(
                    player.damage_min
                    * MAGE_CONCENTRATION_DAMAGE_MULTIPLIER
                )
                damage_maximum = ceil(
                    player.damage_max
                    * MAGE_CONCENTRATION_DAMAGE_MULTIPLIER
                )
                damage_bonus = ceil(
                    full_damage_bonus
                    * MAGE_CONCENTRATION_DAMAGE_MULTIPLIER
                )
                neighboring_enemy_count = 0
                fracture_multiplier = 1.0
            else:
                neighboring_enemy_count = sum(
                    1
                    for other_enemy in targets
                    if (
                        other_enemy is not enemy
                        and any(
                            position
                            in (
                                (target[0], target[1] - 1),
                                (target[0] + 1, target[1]),
                                (target[0], target[1] + 1),
                                (target[0] - 1, target[1]),
                            )
                            for position in get_enemy_occupied_positions(
                                other_enemy
                            )
                        )
                    )
                )
                fracture_multiplier = (
                    1.0
                    + neighboring_enemy_count
                    * MAGE_FRACTURE_DAMAGE_PER_NEIGHBOR
                    if player.act_two.selected_rune_id == "rune_of_fracture"
                    else 1.0
                )
                damage_minimum = ceil(
                    player.damage_min * fracture_multiplier
                )
                damage_maximum = ceil(
                    player.damage_max * fracture_multiplier
                )
                damage_bonus = ceil(
                    full_damage_bonus * fracture_multiplier
                )
            if (
                player.act_two.selected_rune_id == "rune_of_fracture"
                and neighboring_enemy_count > 0
            ):
                bonus_percent = round(
                    neighboring_enemy_count
                    * MAGE_FRACTURE_DAMAGE_PER_NEIGHBOR
                    * 100
                )
                add_log_message(
                    game_state.combat_log,
                    f"Rune of Fracture amplifies the center by "
                    f"{bonus_percent}%.",
                    category="rune",
                )
        else:
            damage_minimum = max(
                1,
                ceil(
                    player.damage_min
                    * MAGE_ARCANE_BURST_EDGE_DAMAGE_MULTIPLIER
                ),
            )
            damage_maximum = max(
                damage_minimum,
                ceil(
                    player.damage_max
                    * MAGE_ARCANE_BURST_EDGE_DAMAGE_MULTIPLIER
                ),
            )
            damage_bonus = ceil(
                full_damage_bonus
                * MAGE_ARCANE_BURST_EDGE_DAMAGE_MULTIPLIER
            )

        defeated = attack_enemy(
            game_state,
            enemy,
            damage_minimum,
            damage_maximum,
            player.crit_chance,
            damage_bonus=damage_bonus,
            grant_ability_charge=False,
            attacker_position=(floor.player_column, floor.player_row),
        )
        if enemy.type == "oracle":
            oracle_hit_reaction(enemy, floor, game_state.combat_log)

        if not concentration_active and not center_hit and not defeated:
            destination = _mage_burst_knockback_destination(
                game_state,
                enemy,
                target,
            )
            if destination is not None:
                _apply_forced_knockback(
                    game_state,
                    enemy,
                    destination,
                    "arcane_burst_knockback",
                )
                add_log_message(
                    game_state.combat_log,
                    f"Arcane Burst hurls {enemy.name} outward.",
                    category="ability",
                )

        if defeated:
            resolve_enemy_defeat(game_state, enemy)

    if (
        player.act_two.selected_rune_id == "rune_of_resonance"
        and targets
    ):
        player.ability_kill_charge = min(
            ability_charge_required(player),
            len(targets),
        )
        add_log_message(
            game_state.combat_log,
            f"Rune of Resonance restores {len(targets)} charge.",
            category="rune",
        )

    return True
