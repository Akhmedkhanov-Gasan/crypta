import random
from collections import deque

from acts.act_three.dialogue.runtime import queue_dialogue
from acts.act_three.enemies.balance import enemy_config_for_spawn
from acts.act_three.npcs import get_npc_cells
from acts.act_three.quests.trader import BROKEN_URN, SEALED_URN, queue_clutter_comment
from acts.act_three.quests.trader_lines import ALTAR_FAILED, DELIVERED, OPENED, RESIST, TEMPTATIONS, URN_VICTORY
from acts.act_three.world_geometry import reachable_cells
from enemies import ENEMY_TYPES
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState, EnemyState
from logic import get_enemy_occupied_positions
from systems.grid_geometry import can_reach_adjacent_cell


def _distances(floor):
    altar = floor.trader_altar
    if altar is None:
        return {}
    distances = {}
    pending = deque()
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        cell = altar[0] + dx, altar[1] + dy
        if can_reach_adjacent_cell(floor.map, cell, altar, floor.barriers, target_must_be_walkable=False):
            x, y = cell
            if 0 <= y < len(floor.map) and 0 <= x < len(floor.map[y]) and floor.map[y][x] == ".":
                distances[cell] = 1
                pending.append(cell)
    while pending:
        cell = pending.popleft()
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            neighbor = cell[0] + dx, cell[1] + dy
            if neighbor not in distances and can_reach_adjacent_cell(floor.map, cell, neighbor, floor.barriers):
                distances[neighbor] = distances[cell] + 1
                pending.append(neighbor)
    return distances


def advance_trader_quest(game_state, current_time):
    player = game_state.player
    quest = player.act_three.trader_quest
    queue_clutter_comment(game_state)
    if quest.get("phase") == "broken":
        floors = {id(floor): floor for floor in (*game_state.visited_floors.values(), game_state.floor)}
        quest["enemies_remaining"] = any(
            enemy.health > 0 and enemy.trader_urn_enemy
            for floor in floors.values() for enemy in floor.enemies
        )
        if (
            not quest["enemies_remaining"] and not quest.get("victory_comment_queued")
            and player.health > 0 and not game_state.game_won
        ):
            quest["victory_comment_queued"] = True
            speaker = player.subclass or "assassin"
            queue_dialogue(
                game_state, speaker, URN_VICTORY.get(speaker, URN_VICTORY["assassin"]),
                ready_at=current_time + 1800,
            )
        return
    if quest.get("phase") != "carrying" or game_state.floor.trader_altar is None:
        return
    if (
        player.health <= 0 or game_state.game_won or game_state.floor_transition_started_at >= 0
        or game_state.act_three.npc_dialog_position is not None
        or game_state.act_three.npc_menu_from_console is not None
        or game_state.dialogue.active or game_state.act_three.dialogue_queue
    ):
        return
    position = game_state.floor.player_column, game_state.floor.player_row
    if quest.get("last_position") == (game_state.floor_index, position):
        return
    quest["last_position"] = game_state.floor_index, position
    quest["steps"] = quest.get("steps", 0) + 1
    distances = _distances(game_state.floor)
    distance = distances.get(position)
    if distance is None:
        return
    initial = quest.setdefault("initial_distance", distance)
    stage = 0
    if distance <= 8 or distance <= initial * 0.18:
        stage = 3
    elif distance <= 16 or distance <= initial * 0.4:
        stage = 2
    elif distance <= initial * 0.7:
        stage = 1
    if stage <= quest.get("whisper_stage", -1) or quest["steps"] - quest.get("last_whisper_step", -8) < 8:
        return
    quest.update(whisper_stage=stage, last_whisper_step=quest["steps"])
    speaker = player.subclass or "assassin"
    if stage == 0:
        queue_dialogue(game_state, speaker, "Something is scratching inside the vessel. Best keep moving.")
    else:
        queue_dialogue(game_state, "sealed_urn", TEMPTATIONS.get(speaker, TEMPTATIONS["assassin"])[stage - 1])
        queue_dialogue(game_state, speaker, RESIST.get(speaker, RESIST["assassin"])[stage - 1])
    from acts.act_three.presentation.urn_effects import play_urn_sound

    play_urn_sound(stage)


def open_urn(game_state, slot, current_time):
    player = game_state.player
    quest = player.act_three.trader_quest
    if quest.get("phase") != "carrying" or player.act_two.consumable_slots[slot] != SEALED_URN:
        return False
    floor = game_state.floor
    origin = floor.player_column, floor.player_row
    occupied = {origin}
    for enemy in floor.enemies:
        if enemy.health > 0:
            occupied.update(get_enemy_occupied_positions(enemy))
    for npc in floor.act_three_npcs:
        occupied.update(get_npc_cells(npc))
    occupied.update((crate.column, crate.row) for crate in floor.breakable_crates if not crate.is_broken)
    occupied.update((chest.column, chest.row) for chest in floor.chests if not chest.is_open)
    if player.summoner_familiar_active and player.summoner_familiar_position is not None:
        occupied.add(player.summoner_familiar_position)
    manifestation = player.act_three.summoner_manifestation
    if manifestation is not None and manifestation["health"] > 0 and manifestation["floor"] == game_state.floor_index:
        occupied.add(tuple(manifestation["position"]))
    cells = list(reachable_cells(floor.map, origin, floor.barriers) - occupied - floor.trial_safe_cells)
    random.shuffle(cells)
    cells.sort(key=lambda cell: abs(cell[0] - origin[0]) + abs(cell[1] - origin[1]))
    enemy_types = ("goblin", "archer", "priest_ghost", "priest_ghost")
    if len(cells) < len(enemy_types):
        add_log_message(game_state.combat_log, "There is no room to open the vessel here.", category="warning")
        return False
    for index, (enemy_type, cell) in enumerate(zip(enemy_types, cells)):
        enemy = EnemyState.from_config(
            enemy_type=enemy_type, column=cell[0], row=cell[1],
            name=f"Unsealed {ENEMY_TYPES[enemy_type]['display_name']} {index + 1}",
            config=enemy_config_for_spawn(game_state, enemy_type, cell), belongs_to_boss_group=False,
        )
        enemy.is_summoned = True
        enemy.trader_urn_enemy = True
        enemy.goblin_summon_used = True
        enemy.summon_spawn_animation_started_at = current_time
        enemy.is_aggro = True
        enemy.behavior_state = EnemyBehaviorState.CHASING
        floor.enemies.append(enemy)
        game_state.emit(GameEvent(
            type=GameEventType.SUMMON, actor="sealed_urn", target=enemy.name,
            origin=origin, destination=cell, data={"enemy_type": enemy_type},
        ))
    player.act_two.consumable_slots[slot] = BROKEN_URN
    quest.update(phase="broken", enemies_remaining=True)
    floor.trader_urn_effect = {"position": origin, "started_at": current_time, "kind": "burst"}
    speaker = player.subclass or "assassin"
    queue_dialogue(game_state, speaker, OPENED.get(speaker, OPENED["assassin"]))
    from acts.act_three.presentation.urn_effects import play_urn_sound

    play_urn_sound(3)
    return True


def interact_with_trader_altar(game_state, target, current_time):
    if target != game_state.floor.trader_altar:
        return None
    player = game_state.player
    quest = player.act_three.trader_quest
    speaker = player.subclass or "assassin"
    if quest.get("phase") == "carrying" and SEALED_URN in player.act_two.consumable_slots:
        player.act_two.consumable_slots[player.act_two.consumable_slots.index(SEALED_URN)] = None
        quest["phase"] = "delivered"
        game_state.floor.trader_urn_effect = {"position": target, "started_at": current_time, "kind": "altar"}
        from acts.act_three.presentation.urn_audio import play_urn_cry

        play_urn_cry()
        queue_dialogue(game_state, speaker, DELIVERED.get(speaker, DELIVERED["assassin"]), ready_at=current_time + 3800)
        add_log_message(game_state.combat_log, "The altar accepts the sealed vessel. Return to the trader for your pack.", category="quest")
        return True
    if quest.get("phase") == "broken" and not quest.get("altar_rejected"):
        quest["altar_rejected"] = True
        queue_dialogue(game_state, speaker, ALTAR_FAILED.get(speaker, ALTAR_FAILED["assassin"]))
    return False
