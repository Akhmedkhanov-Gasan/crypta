from acts.act_one.settings import (
    PLAYER_STARTING_ATTRIBUTE_RANKS,
    PLAYER_STARTING_STATS,
)
from acts.act_two.presentation.awakening_timing import (
    AWAKENING_WORLD_SWAP_MS,
)
from acts.act_two.progression import (
    transfer_mage_valor_investment,
)
from acts.act_two.settings import (
    CLASS_BASE_ATTRIBUTE_RANKS,
    CLASS_STARTING_STATS,
)
from acts.act_two.visibility import update_act_two_visibility
from game.attributes import (
    apply_attribute_rank_transition,
    apply_player_stat_transition,
)


AWAKENING_PLAYER_POSITION = (18, 7)


def begin_act_two_awakening(game_state, current_time) -> bool:
    if (
        game_state.class_selection_open
        or game_state.player.player_class is not None
        or game_state.floor.presentation_act != 1
    ):
        return False

    wardens = [
        enemy
        for enemy in game_state.floor.enemies
        if enemy.type == "warden"
    ]
    if not wardens or any(warden.health > 0 for warden in wardens):
        return False

    game_state.class_selection_open = True
    game_state.class_transition_started_at = current_time
    game_state.class_transition_world_swapped = False
    game_state.class_selection_choice = None
    game_state.class_selection_choice_started_at = 0
    game_state.class_selection_preview_ranks.clear()
    game_state.player_attack_targets = []
    return True


def advance_act_two_awakening(game_state, current_time) -> None:
    if (
        not game_state.class_selection_open
        or game_state.class_transition_world_swapped
        or game_state.oracle_debug_mode
    ):
        return

    elapsed = current_time - game_state.class_transition_started_at
    if elapsed < AWAKENING_WORLD_SWAP_MS:
        return

    from game.factories import prepare_act_one_revisit_floors

    prepare_act_one_revisit_floors(game_state)

    awakened_floor = game_state.visited_floors[
        game_state.floor_index
    ]
    game_state.floor = awakened_floor

    (
        awakened_floor.player_column,
        awakened_floor.player_row,
    ) = AWAKENING_PLAYER_POSITION

    awakened_floor.visible_cells.clear()
    awakened_floor.explored_cells.clear()
    update_act_two_visibility(awakened_floor)

    player = game_state.player
    player.act_two_facing_direction = (-1, 0)
    player.act_two_movement_origin = None
    player.act_two_blocked_movement_started_at = -1
    player.act_one_attack_target = None

    game_state.class_transition_world_swapped = True


def apply_act_two_class_selection(
    player,
    chosen_class: str,
) -> dict[str, int]:
    previous_ranks = dict(player.attribute_ranks)
    previous_health = player.health

    player.player_class = chosen_class

    apply_player_stat_transition(
        player,
        PLAYER_STARTING_STATS,
        CLASS_STARTING_STATS[chosen_class],
    )
    apply_attribute_rank_transition(
        player,
        PLAYER_STARTING_ATTRIBUTE_RANKS,
        CLASS_BASE_ATTRIBUTE_RANKS[chosen_class],
    )
    transfer_mage_valor_investment(
        player,
        previous_ranks,
    )

    player.health = min(
        previous_health,
        player.max_health,
    )

    return previous_ranks


__all__ = [
    "AWAKENING_PLAYER_POSITION",
    "advance_act_two_awakening",
    "apply_act_two_class_selection",
    "begin_act_two_awakening",
]
