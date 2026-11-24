from acts.act_three.abilities.greater_manifestation import damage_manifestation, manifestation_alive, summon_manifestation
from acts.act_three.rune_master.definitions import ABSORPTION_ATTACKS, ABSORPTION_DAMAGE_MULTIPLIER, equipped_rune
from acts.act_three.settings import SUMMONER_TRUE_FORM_CHARGES
from game.combat_log import add_log_message


def end_absorption(game_state):
    state = game_state.player.act_three
    state.summoner_absorption_attack_active = False
    state.summoner_absorption_attacks = 0
    state.summoner_suspended_familiar = None
    add_log_message(game_state.combat_log, "The absorbed spirit's power fades.", category="ability")


def activate_summoner_ultimate(game_state, now):
    from acts.act_three.abilities.manifestation_targeting import begin_manifestation_targeting, cancel_manifestation_targeting

    player = game_state.player
    state = player.act_three
    if manifestation_alive(player):
        damage_manifestation(game_state, state.summoner_manifestation["health"], now)
        return True
    if state.summoner_absorption_attacks > 0:
        return False
    if not player.debug_unlimited_abilities and player.summoner_true_form_charge < SUMMONER_TRUE_FORM_CHARGES:
        add_log_message(game_state.combat_log, "Greater Manifestation is not fully charged.")
        return False
    rune = equipped_rune(player, "f")
    rune_id = rune.id if rune else None
    if rune_id == "rune_of_absorption":
        cancel_manifestation_targeting(player)
        state.summoner_absorption_damage = ABSORPTION_DAMAGE_MULTIPLIER
        state.summoner_absorption_origin = (game_state.floor.player_column, game_state.floor.player_row)
        state.summoner_absorption_attacks = ABSORPTION_ATTACKS
        state.summoner_absorption_attack_active = False
        add_log_message(game_state.combat_log, "The greater spirit grants six empowered attacks, increased block chance and attack range.", category="rune")
    else:
        if not state.summoner_manifestation_aiming:
            begin_manifestation_targeting(game_state)
            return False
        if not summon_manifestation(game_state, now, rune_id == "rune_of_soul_devourer", state.summoner_manifestation_target):
            return False
        cancel_manifestation_targeting(player)
    state.summoner_ultimate_rune = rune_id
    state.summoner_rune_started_at = now
    player.summoner_true_form_charge = 0
    return True
