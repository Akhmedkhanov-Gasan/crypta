from acts.act_three.settings import SUMMONER_FAMILIAR_CHARGES, SUMMONER_TRUE_FORM_CHARGES


def bind_summoner_rune(game_state, rune):
    player = game_state.player
    state = player.act_three
    if rune.subclass != "summoner" or state.ability_runes.get(rune.slot) == rune.id:
        return
    if rune.id == "rune_of_possession":
        from acts.act_three.abilities.summoner_possession import release_host

        release_host(game_state)
        player.summoner_familiar_active = False
        player.summoner_familiar_position = None
        player.summoner_familiar_summon_aiming = False
        player.summoner_familiar_summon_target = None
        player.summoner_familiar_summoned_at = -1
        player.summoner_familiar_movement_origin = None
        player.summoner_familiar_attack_target = None
        player.summoner_familiar_hit_position = None
        player.summoner_familiar_hit_animation_started_at = -1
        state.summoner_recall_position = None
        state.summoner_totem_anchor = None
        state.summoner_familiar_mode = "possession"
        if state.summoner_loss_turns == 0:
            player.summoner_familiar_charge = SUMMONER_FAMILIAR_CHARGES
    if rune.slot == "f":
        from acts.act_three.abilities.manifestation_targeting import cancel_manifestation_targeting

        cancel_manifestation_targeting(player)
        if state.summoner_manifestation is not None and state.summoner_manifestation["health"] > 0:
            player.summoner_true_form_charge = SUMMONER_TRUE_FORM_CHARGES
        state.summoner_manifestation = None
        if state.summoner_absorption_attacks > 0:
            state.summoner_absorption_attacks = 0
            state.summoner_absorption_attack_active = False
            player.summoner_true_form_charge = SUMMONER_TRUE_FORM_CHARGES
