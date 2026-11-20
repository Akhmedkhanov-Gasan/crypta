import math

from game.combat_log import add_log_message
from game.dialogue import hold_dialogue
from acts.act_three.enemies.lantern_warden.settings import WARDEN_DEATH_DURATION_MS


AWAKEN_START_MS = 900
AWAKEN_END_MS = 3300
ENCOUNTER_END_MS = 4400
CURSE_DIALOGUE_MS = 2100

ENTRY_LINES = {
    "assassin": "Too quiet. Even the rats avoid this place.",
    "archer": "I don't like this. Something is watching from that rubbish.",
    "berserker": "This heap stinks of something worse than death.",
    "paladin": "There is something foul beneath this refuse.",
    "warlock": "Something here is pretending to be dead.",
    "summoner": "My companion won't go near that heap. Neither should I.",
}
CURSE_LINES = {
    "assassin": "Shit. The rubbish fights back.",
    "archer": "Shit! That was not a pile of rubbish!",
    "berserker": "Bloody hell. Come on, then!",
    "paladin": "Damn this cursed place!",
    "warlock": "Oh, shit. That thing is still alive.",
    "summoner": "Shit! Stay close to me!",
}


def build_encounter(root, tile_size, width, height, by_name, connectors):
    wardens = by_name.get("lantern_warden", [])
    markers = root.findall(".//object[@name='awaken_zone']")
    if not wardens or not markers:
        return None
    marker = markers[0]
    x = float(marker.get("x", 0))
    y = float(marker.get("y", 0))
    zone_width = max(1, float(marker.get("width", tile_size)))
    zone_height = max(1, float(marker.get("height", tile_size)))
    entrance = next((item for item in connectors if item["name"] == "exit_south"), None)
    if entrance is None:
        return None
    ex, ey = entrance["position"]
    return {
        "position": wardens[0][0],
        "entrance": (ex, ey - 1),
        "bounds": (0, 0, width, height),
        "zone": (math.floor(x / tile_size), math.floor(y / tile_size),
                 math.ceil((x + zone_width) / tile_size), math.ceil((y + zone_height) / tile_size)),
        "phase": "sleeping",
        "started_at": -1,
        "entry_at": -1,
        "enemy": None,
    }


def shift_encounter(encounter, offset):
    shifted = dict(encounter)
    dx, dy = offset
    for name in ("position", "entrance"):
        x, y = shifted[name]
        shifted[name] = (x + dx, y + dy)
    for name in ("zone", "bounds"):
        left, top, right, bottom = shifted[name]
        shifted[name] = (left + dx, top + dy, right + dx, bottom + dy)
    return shifted


def initialize_encounter(floor):
    encounter = floor.lantern_encounter
    enemy = next((enemy for enemy in floor.enemies
                  if enemy.type == "lantern_warden"
                  and (enemy.column, enemy.row) == encounter["position"]), None)
    if enemy is None:
        floor.lantern_encounter = None
        return
    floor.enemies.remove(enemy)
    encounter["enemy"] = enemy


def cinematic_active(floor):
    encounter = floor.lantern_encounter
    return encounter is not None and encounter["phase"] in ("entry_dialogue", "awakening", "dying")


def encounter_dialogue(game_state):
    encounter = game_state.floor.lantern_encounter
    if encounter is None:
        return None
    speaker = game_state.player.subclass or "assassin"
    if encounter["phase"] == "entry_dialogue":
        return speaker, ENTRY_LINES.get(speaker, ENTRY_LINES["assassin"])
    if encounter["phase"] == "awakening" and game_state.dialogue.active and game_state.dialogue.track == "lantern_awakening":
        return speaker, CURSE_LINES.get(speaker, CURSE_LINES["assassin"])
    return None


def _inside(position, bounds):
    return bounds[0] <= position[0] < bounds[2] and bounds[1] <= position[1] < bounds[3]


def advance_encounter(game_state, current_time):
    floor = game_state.floor
    encounter = floor.lantern_encounter
    if encounter is None or game_state.player.health <= 0:
        return
    position = (floor.player_column, floor.player_row)
    if encounter["phase"] == "sleeping" and encounter["entry_at"] < 0 and _inside(position, encounter["bounds"]):
        encounter["entry_at"] = current_time
        encounter["phase"] = "entry_dialogue"
        add_log_message(game_state.combat_log, ENTRY_LINES.get(game_state.player.subclass, ENTRY_LINES["assassin"]), category="warning")
    if encounter["phase"] == "entry_dialogue":
        _, message = encounter_dialogue(game_state)
        elapsed = current_time - encounter["entry_at"]
        held = hold_dialogue(game_state, "lantern_entry", elapsed, ((0, 1, message),))
        encounter["entry_at"] += elapsed - held
        if held < 1:
            return
        encounter["phase"] = "sleeping"
    if encounter["phase"] == "sleeping":
        if _inside(position, encounter["zone"]):
            encounter["phase"] = "awakening"
            encounter["started_at"] = current_time
            encounter["origin"] = position
    elif encounter["phase"] == "awakening":
        elapsed = current_time - encounter["started_at"]
        message = CURSE_LINES.get(game_state.player.subclass, CURSE_LINES["assassin"])
        held = hold_dialogue(game_state, "lantern_awakening", elapsed, ((CURSE_DIALOGUE_MS, CURSE_DIALOGUE_MS + 1, message),))
        encounter["started_at"] += elapsed - held
        elapsed = held
        if elapsed >= CURSE_DIALOGUE_MS and not encounter.get("curse_spoken", False):
            encounter["curse_spoken"] = True
            add_log_message(game_state.combat_log, message, category="warning")
        if elapsed >= ENCOUNTER_END_MS:
            enemy = encounter["enemy"]
            enemy.is_aggro = True
            floor.enemies.append(enemy)
            encounter["phase"] = "combat"
            add_log_message(game_state.combat_log, "The Lantern Warden awakens. Its lantern burns with hungry souls.", category="warning")
    elif encounter["phase"] == "combat" and encounter["enemy"].health <= 0:
        encounter["phase"] = "dying"
        add_log_message(game_state.combat_log, "The Lantern Warden falls. The heap is silent again.", category="warning")
    elif encounter["phase"] == "dying":
        enemy = encounter["enemy"]
        if enemy.death_animation_started_at >= 0 and current_time - enemy.death_animation_started_at >= WARDEN_DEATH_DURATION_MS:
            from acts.act_three.dialogue.runtime import queue_dialogue
            from acts.act_three.quests.blacksmith import VICTORY_LINES

            speaker = game_state.player.subclass or "assassin"
            queue_dialogue(game_state, speaker, VICTORY_LINES.get(speaker, VICTORY_LINES["assassin"]))
            encounter["phase"] = "defeated"


def camera_focus(floor, current_time):
    if floor.lantern_encounter is None or floor.lantern_encounter["phase"] != "awakening":
        return None
    encounter = floor.lantern_encounter
    elapsed = current_time - encounter["started_at"]
    progress = min(1.0, max(0.0, elapsed / AWAKEN_START_MS))
    if elapsed > AWAKEN_END_MS:
        progress = 1.0 - min(1.0, (elapsed - AWAKEN_END_MS) / (ENCOUNTER_END_MS - AWAKEN_END_MS))
    progress = progress * progress * (3 - 2 * progress)
    origin = encounter["origin"]
    target = encounter["position"]
    return tuple(origin[index] + (target[index] + 0.5 - origin[index]) * progress for index in range(2))
