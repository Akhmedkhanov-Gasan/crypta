from acts.act_three.abilities.progression import is_ability_slot_unlocked
from acts.act_three.rune_master.definitions import ABILITY_RUNES_BY_ID
from game.combat_log import add_log_message
from game.rune_catalog import RUNES_BY_ID


def apply_rune(game_state, card):
    player = game_state.player
    if card.placeholder or not is_ability_slot_unlocked(player, card.slot):
        return False
    if card.slot == "e":
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
        player.act_three.ability_runes[card.slot] = rune.id
    add_log_message(game_state.combat_log, f"{rune.name} bound to {card.slot.upper()}.", category="rune")
    return True
