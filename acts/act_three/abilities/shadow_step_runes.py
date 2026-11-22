from acts.act_three.combat.stun import apply_act_three_enemy_stun
from acts.act_three.rune_master.definitions import (
    DISPLACEMENT_STUN_TURNS, DOPPELGANGER_INVISIBILITY_TURNS, has_ability_rune,
)
from logic import get_enemy_occupied_positions


def displacement_target(game_state, target):
    if not has_ability_rune(game_state.player, "rune_of_displacement"):
        return None
    return next((
        enemy for enemy in game_state.floor.enemies
        if enemy.health > 0 and target in get_enemy_occupied_positions(enemy)
        and len(get_enemy_occupied_positions(enemy)) == 1
        and not enemy.is_immobile
        and enemy.type not in ("warden", "oracle", "oracle_pillar", "lantern_warden")
    ), None)


def resolve_shadow_step_rune(game_state, origin, target, current_time):
    enemy = displacement_target(game_state, target)
    if enemy is not None:
        enemy.column, enemy.row = origin
        enemy.movement_origin = None
        apply_act_three_enemy_stun(game_state, enemy, DISPLACEMENT_STUN_TURNS, current_time)
    player = game_state.player
    if has_ability_rune(player, "rune_of_the_doppelganger"):
        player.invisibility_turns = max(player.invisibility_turns, DOPPELGANGER_INVISIBILITY_TURNS)
        player.veil_triggered_this_turn = True
