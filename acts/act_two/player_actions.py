from dataclasses import dataclass

from acts.act_two.bloody_altar import (
    bloody_altar_is_at,
    interact_with_bloody_altar,
)
from acts.act_two.crates import break_crate
from acts.act_two.runes import (
    interact_with_rune_pedestal,
    rune_pedestal_is_at,
    rune_wall_is_at,
    strike_wall_rune,
)
from acts.act_two.trader_logic import interact_with_trader
from acts.act_two.treasury import (
    activate_treasury_trial,
    treasury_chest_is_at,
)
from game.combat_log import add_log_message
from logic import get_enemy_occupied_positions
from systems.grid_geometry import can_reach_adjacent_cell
from systems.player_actions import (
    break_secret_passage,
    open_chest,
)
from systems.player_combat import (
    perform_basic_attack,
    perform_warlock_attack,
)


@dataclass(frozen=True)
class ActTwoCellTargets:
    enemy: object | None = None
    chest: object | None = None
    breakable_crate: object | None = None
    treasury_chest: bool = False
    rune_wall: bool = False
    rune_pedestal: bool = False
    trader: bool = False
    bloody_altar: bool = False
    secret_wall: bool = False


@dataclass(frozen=True)
class ActTwoCellActionResult:
    handled: bool
    player_acted: bool = False
    reset_held_movement: bool = False
    trader_sound: str | None = None


def find_act_two_cell_targets(
    game_state,
    target: tuple[int, int],
    player_tried_to_move: bool,
) -> ActTwoCellTargets:
    if not player_tried_to_move:
        return ActTwoCellTargets()

    floor = game_state.floor
    origin = (
        floor.player_column,
        floor.player_row,
    )

    if not can_reach_adjacent_cell(
        floor.map,
        origin,
        target,
        floor.barriers,
        target_must_be_walkable=False,
    ):
        return ActTwoCellTargets()

    enemy = next(
        (
            candidate
            for candidate in floor.enemies
            if (
                candidate.health > 0
                and target
                in get_enemy_occupied_positions(candidate)
            )
        ),
        None,
    )

    chest = next(
        (
            candidate
            for candidate in floor.chests
            if (
                not candidate.is_open
                and (
                    candidate.column,
                    candidate.row,
                )
                == target
            )
        ),
        None,
    )

    breakable_crate = next(
        (
            candidate
            for candidate in floor.breakable_crates
            if (
                not candidate.is_broken
                and (
                    candidate.column,
                    candidate.row,
                )
                == target
            )
        ),
        None,
    )

    trader = any(
        candidate is not None
        and (
            candidate.column,
            candidate.row,
        )
        == target
        for candidate in (
            floor.trader,
            floor.quest_trader,
        )
    )

    target_column, target_row = target
    secret_wall = (
        0 <= target_row < len(floor.map)
        and 0 <= target_column < len(floor.map[target_row])
        and floor.map[target_row][target_column] == "S"
    )

    return ActTwoCellTargets(
        enemy=enemy,
        chest=chest,
        breakable_crate=breakable_crate,
        treasury_chest=treasury_chest_is_at(
            game_state,
            target,
        ),
        rune_wall=rune_wall_is_at(
            game_state,
            target,
        ),
        rune_pedestal=rune_pedestal_is_at(
            game_state,
            target,
        ),
        trader=trader,
        bloody_altar=bloody_altar_is_at(
            game_state,
            target,
        ),
        secret_wall=secret_wall,
    )


def resolve_act_two_cell_action(
    game_state,
    targets: ActTwoCellTargets,
    target: tuple[int, int],
    direction: tuple[int, int],
    current_time: int,
    oracle_hit_reaction,
) -> ActTwoCellActionResult:
    if (
        targets.enemy is not None
        and game_state.player.player_class == "mage"
        and game_state.player.selected_rune_id
        == "rune_of_resonance"
    ):
        add_log_message(
            game_state.combat_log,
            "Rune of Resonance attacks by clicking an enemy.",
            category="rune",
        )
        return ActTwoCellActionResult(
            handled=True,
            reset_held_movement=True,
        )

    if targets.enemy is not None:
        if game_state.player.subclass == "warlock":
            perform_warlock_attack(
                game_state,
                target,
                oracle_hit_reaction,
            )
        else:
            perform_basic_attack(
                game_state,
                direction[0],
                direction[1],
                oracle_hit_reaction,
            )

        game_state.player.attack_animation_started_at = current_time

        return ActTwoCellActionResult(
            handled=True,
            player_acted=True,
        )

    if targets.rune_wall:
        return ActTwoCellActionResult(
            handled=True,
            player_acted=strike_wall_rune(
                game_state,
                target,
                current_time,
            ),
        )

    if targets.rune_pedestal:
        return ActTwoCellActionResult(
            handled=True,
            player_acted=interact_with_rune_pedestal(
                game_state
            ),
        )

    if targets.treasury_chest:
        return ActTwoCellActionResult(
            handled=True,
            player_acted=activate_treasury_trial(
                game_state
            ),
        )

    if targets.trader:
        return ActTwoCellActionResult(
            handled=True,
            reset_held_movement=True,
            trader_sound=interact_with_trader(
                game_state
            ),
        )

    if targets.bloody_altar:
        interact_with_bloody_altar(game_state)

        return ActTwoCellActionResult(
            handled=True,
            reset_held_movement=True,
        )

    if targets.chest is not None:
        return ActTwoCellActionResult(
            handled=True,
            player_acted=open_chest(
                game_state,
                targets.chest,
                current_time,
            ),
        )

    if targets.breakable_crate is not None:
        player_acted = break_crate(
            game_state,
            targets.breakable_crate,
        )

        if player_acted:
            game_state.player.attack_animation_started_at = current_time

        return ActTwoCellActionResult(
            handled=True,
            player_acted=player_acted,
        )

    if targets.secret_wall:
        player_acted = break_secret_passage(
            game_state,
            target[0],
            target[1],
        )

        if player_acted:
            game_state.player.attack_animation_started_at = current_time

        return ActTwoCellActionResult(
            handled=True,
            player_acted=player_acted,
        )

    return ActTwoCellActionResult(
        handled=False,
    )
