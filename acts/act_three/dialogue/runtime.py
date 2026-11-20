from game.combat_log import add_log_message
from game.dialogue import hold_dialogue


def queue_dialogue(game_state, speaker, message, *, ready_at=0, allow_npc=False):
    game_state.act_three.dialogue_queue.append({"speaker": speaker, "message": message, "started_at": -1, "ready_at": ready_at, "allow_npc": allow_npc})


def dialogue_active(game_state):
    queue = game_state.act_three.dialogue_queue
    return bool(queue and queue[0]["started_at"] >= 0)


def advance_dialogue(game_state, current_time):
    queue = game_state.act_three.dialogue_queue
    if not queue or game_state.player.health <= 0 or game_state.floor_transition_started_at >= 0:
        return
    line = queue[0]
    if current_time < line.get("ready_at", 0):
        return
    if line["started_at"] < 0:
        if game_state.dialogue.active or (game_state.act_three.npc_dialog_position is not None and not line.get("allow_npc", False)):
            return
        line["started_at"] = current_time
        add_log_message(game_state.combat_log, line["message"], category="quest")
    elapsed = current_time - line["started_at"]
    held = hold_dialogue(game_state, "act_three_comment", elapsed, ((0, 1, line["message"]),))
    line["started_at"] += elapsed - held
    if held >= 1:
        queue.pop(0)
