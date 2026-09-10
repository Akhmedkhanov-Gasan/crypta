from functools import partial

from acts.act_one.settings import ACT_ONE_BELT_SIZE
from acts.act_two.ground_items import (
    GROUND_ITEM_RULES as ACT_TWO_GROUND_ITEM_RULES,
)
from acts.act_two.presentation.bosses.oracle_combat import (
    finish_oracle_animation_before_action,
)
from acts.act_two.presentation.bosses.oracle_phase_transition import (
    oracle_cutscene_active,
)
from systems import ground_items as shared_ground_items


_RULES = {
    1: shared_ground_items.GroundItemRules(
        store_item=partial(
            shared_ground_items.store_counted_item,
            potion_limit=ACT_ONE_BELT_SIZE,
        ),
        effect_prefix="act_one",
        use_window=False,
    ),
    2: ACT_TWO_GROUND_ITEM_RULES,
    3: shared_ground_items.GroundItemRules(
        store_item=shared_ground_items.store_counted_item,
    ),
}


def ground_item_rules(game_state):
    return _RULES[game_state.floor.presentation_act]


def ground_items(game_state, current_time):
    return shared_ground_items.ground_items(
        game_state,
        current_time,
        ground_item_rules(game_state),
    )


def ground_items_at_player(game_state, current_time):
    return tuple(
        item
        for item in shared_ground_items.ground_items_at_player(
            game_state,
            current_time,
            ground_item_rules(game_state),
        )
        if item.kind != "gold"
    )


def pick_up_ground_item(game_state, item, current_time):
    return shared_ground_items.pick_up_ground_item(
        game_state,
        item,
        current_time,
        ground_item_rules(game_state),
    )


def collect_ground_gold(game_state, current_time):
    return shared_ground_items.collect_ground_gold(
        game_state,
        current_time,
        ground_item_rules(game_state),
    )


def collect_act_one_potions(game_state, current_time):
    if game_state.floor.presentation_act != 1:
        return False

    collected = False

    while True:
        potion = next(
            (
                item
                for item in ground_items_at_player(
                    game_state,
                    current_time,
                )
                if item.kind == "potion"
            ),
            None,
        )

        if potion is None:
            return collected

        if not pick_up_ground_item(
            game_state,
            potion,
            current_time,
        ):
            return collected

        collected = True


def ground_item_act_input_available(game_state):
    return (
        game_state.floor.presentation_act != 2
        or not oracle_cutscene_active(game_state.floor)
    )


def prepare_ground_item_pickup(game_state, current_time, sounds):
    if game_state.floor.presentation_act == 2:
        finish_oracle_animation_before_action(
            game_state,
            current_time,
            sounds,
        )


def play_ground_item_events(game_state, events, sounds):
    if sounds is None or not events:
        return

    if game_state.floor.presentation_act == 1:
        sounds.play_events(events)
    elif game_state.floor.presentation_act == 2:
        sounds.play_events(
            events,
            game_state.player.player_class,
            game_state.floor,
        )
