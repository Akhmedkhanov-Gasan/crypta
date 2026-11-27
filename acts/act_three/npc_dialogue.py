TRADER_REPLIES = {
    "assassin": (
        "Still alive. You picked a conspicuous place to hide.",
        "Tell me what you need first. Then we discuss the price.",
    ),
    "archer": (
        "I've had quieter roads. Good to see a familiar face at the end of one.",
        "Another trail to follow? Next time, tell me where it leads before I set out.",
    ),
    "berserker": (
        "Still breathing. Still surrounded by shit that wants me dead. You?",
        "If you've lost another fucking seal, start looking for it yourself.",
    ),
    "paladin": (
        "Weary, but standing. I'm glad you reached this place safely.",
        "If someone needs help, I will listen. Keep your seal close this time.",
    ),
    "warlock": (
        "Alive, though the price keeps rising. I see your seal still buys you peace.",
        "A favor already? Be precise about the terms. Some debts outlive their owners.",
    ),
    "summoner": (
        "We're both here. It remembers your scent. I think that means it likes you.",
        "We can listen. But if it starts growling, we leave. Both of us.",
    ),
}


def get_npc_dialogue(game_state, npc):
    npc_type = npc["type"]
    from acts.act_three.bloody_altar.catalog import services_are_blocked

    if services_are_blocked(game_state.player):
        refusal = {
            "trader": "I know that mark. Our bargain is over. Keep your bloodstained gold and leave.",
            "blacksmith": "That altar's stench is on you. Your weapons will never touch my forge again.",
            "rune_master": "You traded yourself to the altar. I will neither bind nor change your runes.",
        }
        if npc_type in refusal:
            return ((npc_type, refusal[npc_type]),)
    if npc_type == "trader":
        from acts.act_three.quests.trader import trader_dialogue

        return trader_dialogue(game_state)
    if npc_type == "rune_master":
        from acts.act_three.quests.rune_master import rune_master_dialogue

        return rune_master_dialogue(game_state)
    if npc_type == "blacksmith":
        from acts.act_three.quests.blacksmith import blacksmith_dialogue

        return blacksmith_dialogue(game_state)

    subclass = game_state.player.subclass or "player"
    greeting, answer = TRADER_REPLIES.get(
        subclass,
        ("Still alive. Good to see you too.", "We'll talk when you're ready."),
    )
    return (
        ("trader", "Well, hello! It's been a while. How have you been holding up?"),
        (subclass, greeting),
        ("trader", "Better with my guild seal back where it belongs. I haven't forgotten what you did for me."),
        ("trader", "Actually, I may have a little job for you. Old habits, eh?"),
        (subclass, answer),
        ("trader", "No errands today. The guild sent stronger supplies once I showed them the seal. Take a look."),
    )
