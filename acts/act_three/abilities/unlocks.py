from acts.act_three.abilities.progression import unlock_ability_slot
from acts.act_three.balance import ULTIMATE_UNLOCK_TOWER_FLOOR
from game.combat_log import add_log_message
from game.floor_identity import tower_floor_number
from levels import FLOOR_CONFIGS


def unlock_ultimate_after_boss(game_state, enemy):
    player = game_state.player
    if (game_state.floor.presentation_act != 3 or player.subclass is None
            or enemy.health > 0 or enemy.is_summoned or "f" in player.unlocked_ability_slots):
        return False
    boss_type = FLOOR_CONFIGS[game_state.floor_index].get("ultimate_unlock_boss")
    if boss_type is None or enemy.type != boss_type:
        return False
    if tower_floor_number(game_state.floor_index) != ULTIMATE_UNLOCK_TOWER_FLOOR:
        return False
    unlock_ability_slot(player, "f")
    add_log_message(
        game_state.combat_log,
        "The fallen guardian's power awakens your ultimate ability (F).",
        category="progress",
    )
    return True
