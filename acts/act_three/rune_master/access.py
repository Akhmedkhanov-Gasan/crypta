from game.rune_catalog import RUNES_BY_ID


def has_first_rune(player):
    rune = RUNES_BY_ID.get(player.selected_rune_id)
    return rune is not None and rune.player_class == player.player_class


def can_modify_rune(player, slot):
    if slot == "e":
        return has_first_rune(player)
    if slot == "q":
        return player.act_three.rune_trial_quest.get("rewarded", False)
    return slot == "f"
