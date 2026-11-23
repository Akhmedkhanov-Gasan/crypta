from acts.act_three.abilities.summoner_runes import absorption_active, nearest_summon_cell
from acts.act_three.settings import SUMMONER_FAMILIAR_CHARGES, SUMMONER_TRUE_FORM_HEALTH_BONUS


def maintain_summoner(game_state):
    player = game_state.player
    if player.subclass != "summoner":
        return
    state = player.act_three
    previous = state.summoner_entity_floor
    if previous is None:
        state.summoner_entity_floor = game_state.floor_index
    elif previous != game_state.floor_index:
        old_floor = game_state.visited_floors.get(previous)
        if state.summoner_possession_host is not None:
            if old_floor is not None:
                for enemy in old_floor.enemies:
                    if enemy.name == state.summoner_possession_host:
                        enemy.possessed_by_summoner = False
                        enemy.attack_targets.clear()
                        enemy.prepared_attack_mode = None
            state.summoner_possession_host = None
            state.summoner_possession_turns = 0
            player.summoner_familiar_active = False
            player.summoner_familiar_position = None
            player.summoner_familiar_charge = SUMMONER_FAMILIAR_CHARGES
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


def restore_summoner_state(game_state):
    player = game_state.player
    if player.subclass != "summoner":
        return
    if player.summoner_true_form_active and player.act_three.summoner_suspended_familiar is None:
        base_max = player.summoner_true_form_base_max_health or max(1, player.summoner_familiar_max_health - SUMMONER_TRUE_FORM_HEALTH_BONUS)
        player.act_three.summoner_suspended_familiar = {
            "mode": player.act_three.summoner_familiar_mode,
            "position": player.summoner_familiar_position,
            "health": min(base_max, player.summoner_familiar_health), "max_health": base_max,
            "anchor": player.act_three.summoner_totem_anchor, "floor": game_state.floor_index,
        }
        player.summoner_true_form_charge = 0
    if absorption_active(player) and player.act_three.summoner_absorption_attack_active:
        from acts.act_three.abilities.summoner_runes import finish_summoner_attack

        finish_summoner_attack(game_state)
    maintain_summoner(game_state)
