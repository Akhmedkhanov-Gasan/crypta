import random
from math import ceil

from acts.act_three.abilities.progression import is_ability_slot_unlocked
from acts.act_three.enemies.balance import act_three_enemy_config
from acts.act_three.dialogue.runtime import queue_dialogue
from acts.act_three.trials.archer import set_cell
from acts.act_three.world_geometry import reachable_cells
from game.combat_log import add_log_message
from game.state import EnemyBehaviorState, EnemyState
from logic import get_enemy_occupied_positions
from systems.grid_geometry import can_reach_adjacent_cell


WAVES = (
    ("goblin", "goblin", "goblin"),
    ("goblin", "goblin", "archer", "brute"),
    ("brute", "sentinel", "sentinel", "archer"),
    ("sentinel", "priest_ghost", "priest_ghost"),
)
DISCOVERY_LINES = {
    "assassin": "What's this? An altar, but no offering. Whatever opens it, I don't have it.",
    "archer": "What's this place? These marks lead nowhere I understand. Best leave the altar alone for now.",
    "berserker": "What the hell is this? A bloody altar. Well? Nothing. Fine, keep your secrets.",
    "paladin": "What is this altar? Its purpose is hidden from me. I should seek someone who understands these runes.",
    "warlock": "An altar, waiting for a condition I have yet to satisfy. How very particular.",
    "summoner": "What's this? Easy, friend. The altar isn't doing anything. Maybe someone knows what it's for.",
}


def trial_active(floor):
    trial = floor.rune_trial
    return trial is not None and trial["phase"] in ("opening", "active", "intermission")


def permits_destination(floor, destination):
    return not trial_active(floor) or destination in floor.rune_trial["cells"]


def _blocked_cells(game_state):
    floor = game_state.floor
    occupied = {(floor.player_column, floor.player_row)}
    occupied.update(cell for enemy in floor.enemies if enemy.health > 0 for cell in get_enemy_occupied_positions(enemy))
    occupied.update((chest.column, chest.row) for chest in floor.chests if not chest.is_open)
    occupied.update((crate.column, crate.row) for crate in floor.breakable_crates if not crate.is_broken)
    from acts.act_three.npcs import get_npc_cells

    for npc in floor.act_three_npcs:
        occupied.update(get_npc_cells(npc))
    player = game_state.player
    if player.summoner_familiar_active and player.summoner_familiar_position is not None:
        occupied.add(player.summoner_familiar_position)
    spirit = player.act_three.summoner_manifestation
    if spirit is not None and spirit["health"] > 0 and spirit["floor"] == game_state.floor_index:
        occupied.add(tuple(spirit["position"]))
    return occupied


def _spawn_wave(game_state, now):
    floor = game_state.floor
    trial = floor.rune_trial
    origin = floor.player_column, floor.player_row
    occupied = _blocked_cells(game_state)
    reachable = reachable_cells(floor.map, origin, floor.barriers)
    candidates = sorted((trial["cells"] & reachable) - occupied - set(trial["altars"]) - {trial["start"], trial["entrance"]})
    random.shuffle(candidates)
    candidates.sort(key=lambda cell: abs(cell[0] - origin[0]) + abs(cell[1] - origin[1]) < 3)
    types = WAVES[trial["wave"]]
    if len(candidates) < len(types):
        return False
    spawned = []
    left, top, right, bottom = trial["bounds"]
    for index, (enemy_type, cell) in enumerate(zip(types, candidates)):
        base = act_three_enemy_config(enemy_type, 3)
        config = {
            **base,
            "max_health": ceil(base["max_health"] * (1.0 + trial["wave"] * 0.08)),
            "aggro_radius": 99,
            "wander_chance": 0.0,
            "damage_by_mode": {
                mode: (values, weights)
                for mode, (values, weights) in base["damage_by_mode"].items()
            },
        }
        enemy = EnemyState.from_config(
            enemy_type=enemy_type, column=cell[0], row=cell[1],
            name=f"Runebound {base['display_name']} {trial['wave'] + 1}-{index + 1}",
            config=config, belongs_to_boss_group=False,
        )
        enemy.is_aggro = True
        enemy.altar_original_enemy = False
        enemy.behavior_state = EnemyBehaviorState.CHASING
        enemy.goblin_summon_used = True
        enemy.movement_bounds = left, top, right - 1, bottom - 1
        spawned.append(enemy)
    floor.enemies.extend(spawned)
    trial.update(enemies=spawned, phase="active", started_at=now, wave=trial["wave"] + 1)
    add_log_message(game_state.combat_log, f"Rune trial: wave {trial['wave']} of {len(WAVES)}.", category="quest")
    return True


def advance_trial(game_state, now):
    floor = game_state.floor
    trial = floor.rune_trial
    if trial is None or game_state.player.health <= 0 or game_state.game_won:
        return
    if game_state.floor_transition_started_at >= 0:
        return
    origin = floor.player_column, floor.player_row
    quest = game_state.player.act_three.rune_trial_quest
    if trial["phase"] == "idle":
        if game_state.dialogue.active or game_state.act_three.dialogue_queue or game_state.act_three.npc_dialog_position is not None:
            return
        if not quest.get("accepted") and not trial["discovered"]:
            if any(cell in floor.visible_cells and can_reach_adjacent_cell(
                floor.map, origin, cell, floor.barriers, target_must_be_walkable=False,
            ) for cell in trial["altars"]):
                trial["discovered"] = True
                speaker = game_state.player.subclass or "assassin"
                queue_dialogue(game_state, speaker, DISCOVERY_LINES.get(speaker, DISCOVERY_LINES["assassin"]))
            return
        if origin != trial["start"] or not quest.get("accepted") or not is_ability_slot_unlocked(game_state.player, "q"):
            return
        if quest.get("completed"):
            trial["phase"] = "completed"
            return
        set_cell(floor, trial["door"], "#")
        trial.update(phase="opening", started_at=now, last_player_cell=origin)
        add_log_message(game_state.combat_log, "The altar ignites. Violet runes seal the entrance.", category="quest")
        return
    if trial_active(floor):
        if origin not in trial["cells"]:
            floor.player_column, floor.player_row = trial.get("last_player_cell", trial["start"])
            game_state.player.movement_origin = None
            game_state.player.movement_animation_started_at = 0
        else:
            trial["last_player_cell"] = origin
        if trial["phase"] == "active":
            if any(enemy.health > 0 for enemy in trial["enemies"]):
                return
            if trial["wave"] == len(WAVES):
                set_cell(floor, trial["door"], ".")
                trial.update(phase="completed", started_at=now)
                quest["completed"] = True
                add_log_message(game_state.combat_log, "Rune trial complete. The seal falls. Return to the Rune Master to awaken your second ability's runes.", category="quest")
            else:
                trial.update(phase="intermission", started_at=now)
        elif now - trial["started_at"] >= 1400:
            _spawn_wave(game_state, now)
