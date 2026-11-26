from functools import partial

from acts.act_one.settings import ACT_ONE_BELT_SIZE
from acts.act_three.items.inventory import ORE_ITEM_NAMES, store_inventory_item
from acts.act_three.items.special import PICKAXE, SPECIAL_ITEM_NAMES
from acts.act_three.trader_catalog import TRADER_ITEMS, TRADER_SELL_ITEMS
from acts.act_two.consumables import store_act_two_consumable
from acts.act_two.ground_items import (
    GROUND_ITEM_RULES as ACT_TWO_GROUND_ITEM_RULES,
)
from acts.act_two.enemies.oracle.combat import (
    finish_oracle_animation_before_action,
)
from acts.act_two.presentation.bosses.oracle_phase_transition import (
    oracle_cutscene_active,
)
from systems import ground_items as shared_ground_items


def _store_act_three_item(player, kind):
    if not player.act_three.inventory_unlocked:
        stored = store_act_two_consumable(player, kind)
        if stored and kind == "monster_parts":
            from acts.act_three.quests.trader import note_monster_parts

            note_monster_parts(player)
        if stored and kind == PICKAXE:
            from acts.act_three.quests.blacksmith import note_pickaxe_pickup

            note_pickaxe_pickup(player)
        return stored
    if kind in TRADER_ITEMS:
        return store_act_two_consumable(player, kind) or store_inventory_item(player, kind)
    if kind in ORE_ITEM_NAMES or kind in TRADER_SELL_ITEMS or kind in SPECIAL_ITEM_NAMES or kind == "key":
        stored = store_inventory_item(player, kind)
        if stored and kind == PICKAXE:
            from acts.act_three.quests.blacksmith import note_pickaxe_pickup

            note_pickaxe_pickup(player)
        return stored
    return shared_ground_items.store_counted_item(player, kind)


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
        store_item=_store_act_three_item,
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
