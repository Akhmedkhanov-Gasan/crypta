"""Transitions between floors, acts, and application scenes."""

from levels import FLOOR_CONFIGS
from presentation.transition_timing import (
    FLOOR_TRANSITION_CLOSE_END_MS,
    FLOOR_TRANSITION_END_MS,
)


def complete_class_selection(game_state):
    chosen_class = game_state.class_selection_choice
    if chosen_class is None:
        return

    from acts.act_three.runtime import (
        clear_archer_barrage_zone,
        clear_berserker_crushing_leap,
    )
    from acts.act_two.consumables import (
        cancel_fire_bomb_aiming,
        cancel_scroll_aiming,
        initialize_act_two_consumable_belt,
    )
    from game.combat_log import add_log_message
    from game.factories import (
        create_floor_state,
        prepare_act_one_revisit_floors,
    )

    prepare_act_one_revisit_floors(game_state)

    if game_state.oracle_debug_mode:
        game_state.floor_index = next(
            index
            for index, config in enumerate(FLOOR_CONFIGS)
            if config["act"] == 2 and config["act_floor"] == 4
        )
    else:
        game_state.run_stats.completed_floors.add(
            game_state.floor_index
        )
        game_state.floor_index += 1

    next_floor = game_state.visited_floors.get(game_state.floor_index)
    if next_floor is None:
        next_floor = create_floor_state(
            game_state.floor_index,
            spawn_quest_trader=(
                game_state.floor_index
                == game_state.act_two_trader_floor_index
            ),
        )
        game_state.visited_floors[game_state.floor_index] = next_floor

    game_state.floor = next_floor

    entrance_passage = next(
        (
            passage
            for passage in next_floor.passages
            if passage.passage_id == "entrance"
        ),
        None,
    )
    if entrance_passage is not None:
        (
            next_floor.player_column,
            next_floor.player_row,
        ) = entrance_passage.trigger_position

    clear_archer_barrage_zone(game_state)
    clear_berserker_crushing_leap(game_state)
    game_state.player.key_count = 0
    initialize_act_two_consumable_belt(game_state.player)
    game_state.class_selection_open = False
    game_state.class_transition_started_at = 0
    game_state.class_selection_choice = None
    game_state.class_selection_preview_ranks.clear()
    game_state.class_selection_choice_started_at = 0
    game_state.player_attack_targets = []
    cancel_fire_bomb_aiming(game_state)
    cancel_scroll_aiming(game_state)

    add_log_message(
        game_state.combat_log,
        f"The hero becomes a {chosen_class}.",
        category="progress",
    )
    add_log_message(
        game_state.combat_log,
        (
            "Debug: Act II, floor IV."
            if game_state.oracle_debug_mode
            else "Act II begins. The world gains shape."
        ),
        category="progress",
    )


def finish_upgrade_descent(game_state, started_at):
    if game_state.floor_transition_started_at >= 0:
        return

    game_state.floor_transition_started_at = started_at
    game_state.floor_transition_target_index = game_state.floor_index + 1
    game_state.floor_transition_swapped = False
    game_state.upgrade_screen_open = False
    game_state.upgrade_message = ""
    game_state.player_attack_targets = []


def advance_floor_transition(game_state, current_time):
    started_at = game_state.floor_transition_started_at
    target_index = game_state.floor_transition_target_index
    if started_at < 0 or target_index is None:
        return

    elapsed = current_time - started_at
    if (
        not game_state.floor_transition_swapped
        and elapsed >= FLOOR_TRANSITION_CLOSE_END_MS
    ):
        from acts.act_three.runtime import (
            clear_archer_barrage_zone,
            clear_berserker_crushing_leap,
        )
        from acts.act_two.consumables import (
            cancel_fire_bomb_aiming,
            cancel_scroll_aiming,
        )
        from game.combat_log import add_log_message
        from game.factories import create_floor_state

        target_floor = game_state.visited_floors.get(target_index)

        if target_floor is None:
            target_floor = create_floor_state(
                target_index,
                spawn_quest_trader=(
                    target_index
                    == game_state.act_two_trader_floor_index
                ),
            )
            game_state.visited_floors[target_index] = target_floor

        if target_index > game_state.floor_index:
            game_state.run_stats.completed_floors.add(
                game_state.floor_index
            )

        game_state.floor_index = target_index
        game_state.floor = target_floor

        target_passage_id = game_state.floor_transition_target_passage_id
        if target_passage_id is not None:
            target_passage = next(
                (
                    passage
                    for passage in target_floor.passages
                    if passage.passage_id == target_passage_id
                ),
                None,
            )
            if target_passage is None:
                raise RuntimeError(
                    "Target passage not found: "
                    f"{target_passage_id!r} on floor {target_index}"
                )

            (
                target_floor.player_column,
                target_floor.player_row,
            ) = target_passage.trigger_position

        game_state.floor_transition_swapped = True
        if FLOOR_CONFIGS[target_index]["act"] != 2:
            game_state.player.key_count = 0
        game_state.player_attack_targets = []
        cancel_fire_bomb_aiming(game_state)
        cancel_scroll_aiming(game_state)
        clear_archer_barrage_zone(game_state)
        clear_berserker_crushing_leap(game_state)
        add_log_message(
            game_state.combat_log,
            f"Hero descends to floor {target_index + 1}.",
            category="progress",
        )

    if elapsed >= FLOOR_TRANSITION_END_MS:
        game_state.floor_transition_started_at = -1
        game_state.floor_transition_target_index = None
        game_state.floor_transition_target_passage_id = None
        game_state.floor_transition_swapped = False
