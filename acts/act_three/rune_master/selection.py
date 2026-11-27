from acts.act_three.abilities.progression import is_ability_slot_unlocked
from acts.act_three.rune_master.definitions import ABILITY_RUNES_BY_ID
from game.combat_log import add_log_message
from game.rune_catalog import RUNES_BY_ID
from acts.act_three.rune_master.access import can_modify_rune
from acts.act_two.bloody_altar import BROKEN_SEAL, has_bloody_pact


def apply_rune(game_state, card, current_time=None):
    player = game_state.player
    from acts.act_three.bloody_altar.catalog import has_pact, services_are_blocked

    if services_are_blocked(player):
        return False
    console_access = game_state.act_three.npc_menu_from_console == "rune_master"
    if card.placeholder or not is_ability_slot_unlocked(player, card.slot) or (not console_access and not can_modify_rune(player, card.slot)):
        return False
    if card.slot == "f" and player.act_three.warlock_eternal_bound and card.id != "rune_of_eternal_form":
        add_log_message(game_state.combat_log, "Eternal Form is bound for the rest of this run.", category="warning")
        return False
    if card.slot == "e":
        if has_bloody_pact(player, BROKEN_SEAL) or has_pact(player, "shattered_seal"):
            return False
        rune = RUNES_BY_ID.get(card.id)
        if rune is None or rune.player_class != player.player_class:
            return False
        player.selected_rune_id = rune.id
        player.ability_kill_charge = 0
        player.invisibility_turns = 0
        player.veil_triggered_this_turn = False
    else:
        rune = ABILITY_RUNES_BY_ID.get(card.id)
        if rune is None or rune.subclass != player.subclass or rune.slot != card.slot:
            return False
        from acts.act_three.abilities.summoner_rune_binding import bind_summoner_rune

        bind_summoner_rune(game_state, rune)
        player.act_three.ability_runes[card.slot] = rune.id
        if card.id == "rune_of_spirit_totem":
            from acts.act_three.abilities.summoner_targeting import bind_totem

            bind_totem(game_state, current_time)
        if card.id == "rune_of_eternal_form":
            from acts.act_three.abilities.warlock_runes import bind_eternal_form

            bind_eternal_form(game_state, current_time)
        if card.id == "rune_of_tower_shield":
            player.paladin_shield_charge_aiming = False
            player.paladin_shield_charge_target = None
            player.paladin_shield_charge_preview_cells.clear()
    add_log_message(game_state.combat_log, f"{rune.name} bound to {card.slot.upper()}.", category="rune")
    return True
