from acts.act_two.consumables import store_act_two_consumable
from acts.act_two.quests.trader_seal import collect_guild_seal
from acts.act_two.state import TreasuryTrialPhase
from acts.act_two.treasury import collect_treasury_reward
from acts.act_two.visibility import update_act_two_visibility
from systems.ground_items import GroundItem, GroundItemRules


def extra_ground_items(game_state):
    items = []
    floor = game_state.floor
    revisit = floor.act_one_revisit

    if (
        revisit is not None
        and revisit.guild_seal_position is not None
        and not game_state.act_two_quests.trader_seal.completed
    ):
        items.append(
            GroundItem(
                "seal",
                0,
                revisit.guild_seal_position,
                "guild_seal",
            )
        )

    treasury = floor.treasury_room
    if (
        treasury is not None
        and treasury.phase is TreasuryTrialPhase.REWARD_AVAILABLE
    ):
        items.append(
            GroundItem(
                "treasury",
                0,
                treasury.chest_position,
                "gold",
                10,
            )
        )

    return tuple(items)


def collect_special_item(game_state, item):
    if item.source == "seal":
        return collect_guild_seal(game_state, item.position)

    if item.source == "treasury":
        return collect_treasury_reward(game_state, item.position)

    return None


def after_ground_item_pickup(game_state):
    update_act_two_visibility(game_state.floor)


GROUND_ITEM_RULES = GroundItemRules(
    store_item=store_act_two_consumable,
    locked_chest_gold=3,
    effect_prefix="act_two",
    extra_items=extra_ground_items,
    collect_special=collect_special_item,
    after_pickup=after_ground_item_pickup,
)