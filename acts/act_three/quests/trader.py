from acts.act_three.quests.trader_lines import ACCEPT, CLUTTER, GREETING_REPLIES, PACK_REPLIES
from acts.act_two.consumables import store_act_two_consumable
from game.combat_log import add_log_message


SEALED_URN = "sealed_urn"
BROKEN_URN = "broken_urn"
URN_ITEMS = frozenset({SEALED_URN, BROKEN_URN})


def trader_dialogue(game_state):
    player = game_state.player
    quest = player.act_three.trader_quest
    speaker = player.subclass or "assassin"
    if player.act_three.inventory_unlocked:
        return (("trader", "Good to see you. What do you need?"),)
    if quest.get("phase") == "delivered":
        return (
            (speaker, "It's at the altar. Still sealed."),
            ("trader", "You resisted it? You're the first. The others paid dearly. I always found the vessel again, somewhere in this crypt. Darker. Fuller."),
            ("trader", "You've earned this pack, and access to my better supplies. Use them well."),
        )
    if quest.get("phase") == "broken":
        if quest.get("enemies_remaining"):
            return (("trader", "Something is still following you. Finish what you let out. Then bring me the pieces."),)
        return (
            ("trader", "The vessel... broken? What happened? How are you still alive?"),
            (speaker, "I opened it. Things came out. I killed them."),
            ("trader", "I suspected as much. Never thought anyone would be foolish enough, or fearless enough, to try it. Give me the pieces. There's nothing left in them."),
            ("trader", "You're alive, and the job is done. Take the pack. I'll sell you my better supplies, too. Try reading the warnings this time."),
        )
    if quest.get("phase") == "carrying":
        return (("trader", "How's my delivery? Not yet? I trust you're working on it. Need supplies before you go?"),)
    if not quest.get("introduced"):
        greeting, reply = GREETING_REPLIES.get(speaker, GREETING_REPLIES["assassin"])
        return (
            ("trader", "Well, look who's stopped to talk! Come closer. It's good to hear a familiar voice instead of claws on stone."),
            (speaker, greeting),
            ("trader", "After you brought back my guild seal? Of course I'm pleased. Most people down here take things. You actually returned something."),
            ("trader", "How have you been keeping? You look as though the road's been arguing with you."),
            (speaker, reply),
            ("trader", "Good. The usual supplies are here. I also buy monster parts now, along with gems, silverware and old relics. Bring what you find."),
        )
    offer = (
        ("trader", "Back already? Say, I've been watching you juggle everything on that belt. Would a proper pack help?"),
        (speaker, PACK_REPLIES.get(speaker, PACK_REPLIES["assassin"])),
        ("trader", "I have a spare. Sturdy leather, sound straps. I'd rather ask a small favour than take your last coins for it."),
        ("trader", "Take this sealed vessel to the abandoned altar. One condition: do not open it. Whatever you hear."),
        (speaker, ACCEPT.get(speaker, ACCEPT["assassin"])),
        ("trader", "Leave it at the altar, then return. You'll get the pack and first pick of my better supplies."),
    )
    if all(item is not None for item in player.act_two.consumable_slots):
        return offer + (("trader", "Though first, clear a slot on that belt. Come back when there's room for the vessel. See? You really do need that pack."),)
    return offer


def finish_trader_dialogue(game_state):
    player = game_state.player
    quest = player.act_three.trader_quest
    phase = quest.get("phase")
    if phase == "delivered" or (phase == "broken" and not quest.get("enemies_remaining")):
        slots = player.act_two.consumable_slots
        for index, item in enumerate(slots):
            if item in URN_ITEMS:
                slots[index] = None
        quest["phase"] = "rewarded"
        player.act_three.inventory_unlocked = True
        add_log_message(game_state.combat_log, "The trader gives you a pack. Inventory and improved supplies unlocked.", category="quest")
    elif phase is None and not quest.get("introduced"):
        quest["introduced"] = True
    elif phase is None and store_act_two_consumable(player, SEALED_URN):
        quest.update(phase="carrying", whisper_stage=-1, steps=0, last_position=None)
        add_log_message(game_state.combat_log, "Deliver the sealed vessel to the abandoned altar. Do not open it.", category="quest")


def note_monster_parts(player):
    quest = player.act_three.trader_quest
    if not player.act_three.inventory_unlocked and not quest.get("clutter_seen"):
        quest["clutter_seen"] = True
        quest["clutter_pending"] = True


def queue_clutter_comment(game_state):
    quest = game_state.player.act_three.trader_quest
    if quest.pop("clutter_pending", False):
        from acts.act_three.dialogue.runtime import queue_dialogue

        speaker = game_state.player.subclass or "assassin"
        queue_dialogue(game_state, speaker, CLUTTER.get(speaker, CLUTTER["assassin"]))
