from acts.act_three.abilities.progression import is_ability_slot_unlocked
from acts.act_three.rune_master.access import has_first_rune
from game.combat_log import add_log_message


REPLIES = {
    "assassin": (
        "Someone alive? Who are you?",
        "A smith, a trader, now you. Gets crowded the higher I go.",
        "Watching me? What do you want?",
        "Another test. Of course.",
        "It's done. Your turn.",
        "Find the power first. Understood.",
    ),
    "archer": (
        "Another living soul? Who are you?",
        "First the smith and the trader, now you. More company on every floor.",
        "You were watching? You could have said hello.",
        "All right. I'll find it.",
        "Trial's over. I made it back.",
        "One step at a time, then.",
    ),
    "berserker": (
        "Someone alive? Who the hell are you?",
        "A smith, a trader, now you. Is everyone bloody living up here?",
        "You've been watching me? Could've lent a fucking hand.",
        "Fine. Let's get this bloody trial over with.",
        "Your fucking trial is done. Now keep your end of it.",
        "More strength first? Fine. I'll be back.",
    ),
    "paladin": (
        "Someone still lives here? Who are you?",
        "The smith, the trader, now you. More survivors with every ascent.",
        "Why show yourself now?",
        "Then I will prove myself.",
        "I have passed your trial.",
        "I understand. I will return when I am ready.",
    ),
    "warlock": (
        "A living resident? And who might you be?",
        "A smith, a merchant, now you. Quite a gathering up here.",
        "Watching me? What caught your interest?",
        "A trial for stronger runes. Fair enough.",
        "The trial is done. Our bargain?",
        "Power first, refinement later. Sensible.",
    ),
    "summoner": (
        "Oh! Someone's here. Easy, friend. Who are you?",
        "The smith, the trader, now you! More company the higher we go.",
        "Watching us? It knew someone was there!",
        "We'll find it together.",
        "We made it! Both of us.",
        "Come on, friend. We'll come back when we're ready.",
    ),
}


def rune_master_dialogue(game_state):
    player = game_state.player
    quest = player.act_three.rune_trial_quest
    speaker = player.subclass or "assassin"
    surprise, familiar, watched, accept, victory, unready = REPLIES.get(speaker, REPLIES["assassin"])
    if quest.get("rewarded"):
        return (("rune_master", "Back again? Let us work on your runes."),)
    if quest.get("completed"):
        return (
            (speaker, victory),
            ("rune_master", "Well done. Now I can awaken the runes of your second ability."),
        )
    lines = ()
    if not quest.get("introduced"):
        if has_first_rune(player):
            lines = (
                ("rune_master", "I watched you from afar. Now that your first runes have awakened, I'd like to see your progress myself."),
                (speaker, watched),
            )
        else:
            met_smith = player.act_three.blacksmith_quest.get("met", False)
            met_trader = game_state.act_two_quests.trader_seal.started or "trader" in game_state.act_three.npc_conversations_completed
            lines = (
                (speaker, familiar if met_smith and met_trader else surprise),
                ("rune_master", "I'm the Rune Master. I can help you strengthen your abilities."),
            )
    if not has_first_rune(player):
        lines += (("rune_master", "For your first runes, you'll need to return to the lower halls. Here, I can awaken runes for your second ability."),)
    if not is_ability_slot_unlocked(player, "q"):
        return lines + (
            ("rune_master", "First, awaken your second ability. Find your strength before you ask me to refine it."),
            (speaker, unready),
        )
    if quest.get("accepted"):
        return lines + (("rune_master", "Find the trial chamber. I'll be here when you return."),)
    return lines + (
        ("rune_master", "Want stronger runes? Find the trial chamber and prove yourself. Then come back to me."),
        (speaker, accept),
    )


def finish_rune_master_dialogue(game_state, current_time):
    player = game_state.player
    quest = player.act_three.rune_trial_quest
    quest["introduced"] = True
    if quest.get("completed"):
        if not quest.get("rewarded"):
            quest["rewarded"] = True
            add_log_message(game_state.combat_log, "The Rune Master unlocks runes for your second ability (Q).", category="quest")
        from acts.act_three.rune_master.runtime import open_menu

        game_state.act_three.npc_dialog_phase = "talk"
        open_menu(game_state, current_time)
        return True
    if is_ability_slot_unlocked(player, "q") and not quest.get("accepted"):
        quest["accepted"] = True
        add_log_message(game_state.combat_log, "Rune trial: find the trial chamber, then return to the Rune Master.", category="quest")
    return False
