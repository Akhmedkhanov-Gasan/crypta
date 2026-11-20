from acts.act_three.dialogue.runtime import queue_dialogue
from acts.act_three.items.inventory import IRON_ORE_CHUNK, get_inventory_slots, remove_inventory_item, store_inventory_item
from acts.act_three.items.keys import KEYRING_ITEMS
from acts.act_three.items.special import PICKAXE
from game.combat_log import add_log_message


VICTORY_LINES = {
    "assassin": "Stay dead this time. Let's see what you were sitting on.",
    "archer": "Finally. That lantern won't be watching anyone again. Time to search the heap.",
    "berserker": "And stay the fuck down. Now, what were you guarding?",
    "paladin": "May those trapped souls find peace. I should search what remains.",
    "warlock": "Your light has gone out. Let's see what was worth all that trouble.",
    "summoner": "It's over. Easy, friend. Let's check the remains before we leave.",
}
PICKAXE_LINES = {
    "assassin": "There it is. The blacksmith's pickaxe. He mentioned iron here; that vein should do for a first try.",
    "archer": "Aha, the pickaxe the blacksmith told me about. He said there was iron here. I'll try that vein.",
    "berserker": "So that's the bloody pickaxe. The smith said there was iron here. Let's hit that vein for a change.",
    "paladin": "The pickaxe the blacksmith spoke of. He mentioned iron in these rooms. I should try that vein.",
    "warlock": "A pickaxe, just as the blacksmith promised. He mentioned iron nearby. Let's test it on that vein.",
    "summoner": "Found it! The blacksmith's pickaxe. He said there was iron here. Come on, let's try that vein.",
}

BLACKSMITH_REPLIES = {
    "assassin": (
        "Someone else alive down here? Wasn't expecting that.",
        "A blacksmith, then. Could you do something about my equipment?",
        "I'll need something to dig it out with.",
        "Of course it's guarded. What do you need first?",
        "Here's your iron. That heap nearly buried me with it.",
    ),
    "archer": (
        "Another living soul? I thought I'd be walking these halls alone.",
        "You work steel? My equipment could use some attention.",
        "Where would I find a pickaxe?",
        "I'll watch my step. What should I bring back?",
        "Found the pickaxe. And the iron you asked for.",
    ),
    "berserker": (
        "Well, shit. Someone down here who isn't trying to kill me.",
        "A smith? Good. My gear's taken a beating.",
        "And I dig it out with my fucking hands?",
        "Wouldn't be this place without something trying to eat me. What ore first?",
        "Your iron. Next time, mention how big the bloody guard is.",
    ),
    "paladin": (
        "Someone still lives here? I had almost given up hope.",
        "Then perhaps you could help mend my equipment.",
        "I have no tools for mining. Where should I look?",
        "I'll be careful. What would you have me bring first?",
        "I found the pickaxe and brought you iron, as promised.",
    ),
    "warlock": (
        "A living resident? This crypt still has a few surprises left.",
        "A blacksmith. What would it cost to improve my equipment?",
        "Ore needs a pickaxe. I seem to be missing one.",
        "Naturally, there's a catch. What should I bring you first?",
        "Iron, as agreed. Your old pickaxe had acquired a rather unpleasant keeper.",
    ),
    "summoner": (
        "Oh! Someone lives here? We thought we were the only ones.",
        "You're a blacksmith? Could you help with my equipment?",
        "Do you know where we could find a pickaxe?",
        "We'll keep close. What should we look for first?",
        "We found it! And brought you a piece of iron.",
    ),
}


def has_pickaxe(player):
    return PICKAXE in get_inventory_slots(player)


def claim_pickaxe_drop(game_state, enemy):
    from game.floor_identity import tower_floor_number

    encounter = game_state.floor.lantern_encounter
    quest = game_state.player.act_three.blacksmith_quest
    if tower_floor_number(game_state.floor_index) != 9 or encounter is None or encounter["enemy"] is not enemy or quest.get("pickaxe_spawned"):
        return False
    quest["pickaxe_spawned"] = True
    return True


def note_pickaxe_pickup(player):
    quest = player.act_three.blacksmith_quest
    if not quest.get("pickaxe_recovered"):
        quest["pickaxe_recovered"] = True
        quest["pickaxe_comment_pending"] = True


def on_loot_closed(game_state):
    quest = game_state.player.act_three.blacksmith_quest
    if quest.pop("pickaxe_comment_pending", False):
        speaker = game_state.player.subclass or "assassin"
        queue_dialogue(game_state, speaker, PICKAXE_LINES.get(speaker, PICKAXE_LINES["assassin"]))


def blacksmith_dialogue(game_state):
    player = game_state.player
    quest = player.act_three.blacksmith_quest
    speaker = player.subclass or "assassin"
    surprise, equipment, tools, danger, delivery = BLACKSMITH_REPLIES.get(speaker, BLACKSMITH_REPLIES["assassin"])
    if not quest.get("introduced"):
        return (
            (speaker, surprise),
            ("blacksmith", "I'm the blacksmith. Lived here so long, I've stopped being surprised by anything. Even visitors."),
            (speaker, equipment),
            ("blacksmith", "I can improve weapons and armour. Bring me ore. You'll find veins throughout the crypt, even in the old passages."),
            (speaker, tools),
            ("blacksmith", "There's a pickaxe in a rubbish heap in the distant rooms. Mind yourself. Something dangerous has settled there."),
            (speaker, danger),
            ("blacksmith", "One piece of iron. There's a vein near that heap. Bring it back, then we'll put the forge to work."),
        )
    if not quest.get("completed") and quest.get("pickaxe_recovered") and IRON_ORE_CHUNK in get_inventory_slots(player):
        return (
            (speaker, delivery),
            ("blacksmith", "Good iron. Here, take this keyring for your trouble. Holds three keys; the rest stay loose."),
            (speaker, "And my equipment?"),
            ("blacksmith", "Now we can start. Bring black ore for improvements. Let's see what you're carrying."),
        )
    if quest.get("completed"):
        return (("blacksmith", "Back for more? Show me what needs work."),)
    if quest.get("pickaxe_recovered"):
        return (
            (speaker, "I've got the pickaxe. We ready to start?"),
            ("blacksmith", "Nearly. Bring me one piece of iron first. Try the vein near that heap."),
        )
    return (
        (speaker, "About that equipment..."),
        ("blacksmith", "Find the pickaxe in the distant rubbish heap, then bring me one piece of iron. The forge can wait."),
    )


def finish_blacksmith_dialogue(game_state):
    player = game_state.player
    quest = player.act_three.blacksmith_quest
    if not quest.get("introduced"):
        quest["introduced"] = True
        return False
    if not quest.get("completed") and quest.get("pickaxe_recovered"):
        if remove_inventory_item(player, IRON_ORE_CHUNK):
            if not store_inventory_item(player, KEYRING_ITEMS[0]):
                store_inventory_item(player, IRON_ORE_CHUNK)
                return False
            quest["completed"] = True
            add_log_message(game_state.combat_log, "Iron delivered. The blacksmith gives you a keyring and opens the forge.", category="quest")
    return quest.get("completed", False)
