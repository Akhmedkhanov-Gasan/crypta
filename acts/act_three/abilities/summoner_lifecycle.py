from acts.act_three.abilities.summoner_runes import absorption_active, nearest_summon_cell
from acts.act_three.settings import SUMMONER_FAMILIAR_CHARGES, SUMMONER_TRUE_FORM_HEALTH_BONUS


def maintain_summoner(game_state):
    player = game_state.player
    if player.subclass != "summoner":
        return
    state = player.act_three
    if player.health <= 0 or state.summoner_entity_floor not in (None, game_state.floor_index):
        from acts.act_three.abilities.manifestation_targeting import cancel_manifestation_targeting

        cancel_manifestation_targeting(player)
    from acts.act_three.abilities.greater_manifestation import maintain_manifestation
    import pygame

    maintain_manifestation(game_state, pygame.time.get_ticks())
    previous = state.summoner_entity_floor
    if previous is None:
        state.summoner_entity_floor = game_state.floor_index
    elif previous != game_state.floor_index:
        state.summoner_cataclysm_aiming = False
        old_floor = game_state.visited_floors.get(previous)
        if state.summoner_possession_host is not None:
            from acts.act_three.abilities.summoner_possession import transfer_host

            if not transfer_host(game_state, old_floor):
                return
        elif player.summoner_familiar_active:
            if state.summoner_familiar_mode == "totem" and not player.summoner_true_form_active:
                player.summoner_familiar_active = False
                player.summoner_familiar_position = None
                player.summoner_familiar_charge = SUMMONER_FAMILIAR_CHARGES
                state.summoner_totem_anchor = None
            else:
                position = nearest_summon_cell(game_state, (game_state.floor.player_column, game_state.floor.player_row))
                player.summoner_familiar_position = position
                if position is None:
                    player.summoner_familiar_active = False
                    player.summoner_true_form_active = False
                    state.summoner_suspended_familiar = None
                    player.summoner_familiar_charge = SUMMONER_FAMILIAR_CHARGES
            player.summoner_familiar_movement_origin = None
        state.summoner_entity_floor = game_state.floor_index
    if state.summoner_possession_host is not None:
        from acts.act_three.abilities.summoner_possession import possession_host, sync_host

        host = possession_host(game_state)
        if host is not None:
            sync_host(game_state, host)
    from acts.act_three.abilities.summoner_tether import maintain_familiar_tether

    maintain_familiar_tether(game_state, pygame.time.get_ticks())


def restore_summoner_state(game_state):
    player = game_state.player
    if player.subclass != "summoner":
        return
    state = player.act_three
    from acts.act_three.abilities.manifestation_targeting import cancel_manifestation_targeting

    cancel_manifestation_targeting(player)
    state.summoner_cataclysm_aiming = False
    if state.summoner_recall_requirement > 0:
        from math import ceil

        state.summoner_loss_turns = max(state.summoner_loss_turns, ceil(max(0, state.summoner_recall_requirement - player.summoner_familiar_charge)))
        state.summoner_recall_requirement = 0
        player.summoner_familiar_charge = SUMMONER_FAMILIAR_CHARGES if state.summoner_loss_turns == 0 else 0
    if state.ability_runes.get("f") == "rune_of_cataclysm":
        state.ability_runes["f"] = "rune_of_soul_devourer"
    if player.summoner_true_form_active:
        base_max = player.summoner_true_form_base_max_health or max(1, player.summoner_familiar_max_health - SUMMONER_TRUE_FORM_HEALTH_BONUS)
        saved = state.summoner_suspended_familiar
        player.summoner_familiar_max_health = saved["max_health"] if saved is not None else base_max
        player.summoner_familiar_health = min(player.summoner_familiar_max_health, player.summoner_familiar_health)
        state.summoner_familiar_mode = saved["mode"] if saved is not None else "familiar"
        player.summoner_true_form_active = False
        player.summoner_true_form_started_at = -1
        player.summoner_true_form_ending_started_at = -1
        state.summoner_suspended_familiar = None
        player.summoner_true_form_charge = 0
    if absorption_active(player) and player.act_three.summoner_absorption_attack_active:
        from acts.act_three.abilities.summoner_runes import finish_summoner_attack

        finish_summoner_attack(game_state)
    maintain_summoner(game_state)
