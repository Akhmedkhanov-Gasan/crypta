from acts.act_three.items.drops import place_ground_drop
from acts.act_two.consumables import GUILD_SEAL, remove_act_two_consumable
from game.combat_log import add_log_message
from logic import get_enemy_occupied_positions
from systems.grid_geometry import can_reach_adjacent_cell


def _drop_cell_is_free(floor, origin, target):
    return (
        can_reach_adjacent_cell(floor.map, origin, target, floor.barriers)
        and not any(
            enemy.health > 0 and target in get_enemy_occupied_positions(enemy)
            for enemy in floor.enemies
        )
        and not any(
            not crate.is_broken and target == (crate.column, crate.row)
            for crate in floor.breakable_crates
        )
        and not any(
            not chest.is_open and target == (chest.column, chest.row)
            for chest in floor.chests
        )
    )


def discard_item(game_state, slot, current_time, *, from_belt=False, target=None):
    player = game_state.player
    slots = player.act_two.consumable_slots if from_belt else player.act_three.inventory_slots
    if not 0 <= slot < len(slots) or slots[slot] is None:
        return False

    item = slots[slot]
    if item in ("sealed_urn", "broken_urn"):
        add_log_message(game_state.combat_log, "The vessel must be returned to the trader.", category="quest")
        return False
    if item == GUILD_SEAL:
        add_log_message(
            game_state.combat_log,
            "The guild seal must be returned to the trader.",
            category="quest",
        )
        return False

    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    if target is None:
        dx, dy = player.facing_direction
        target = (origin[0] + dx, origin[1] + dy)

    if not _drop_cell_is_free(floor, origin, target):
        add_log_message(game_state.combat_log, "You cannot drop an item there.", category="warning")
        return False

    if from_belt:
        remove_act_two_consumable(player, slot)
    else:
        slots[slot] = None
    place_ground_drop(floor, item, target, current_time, animate=True)
    add_log_message(game_state.combat_log, "Hero drops an item.", category="neutral")
    return True
