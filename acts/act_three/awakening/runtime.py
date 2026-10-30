from acts.act_three.awakening.dialogue import (
    ARRIVAL, ARRIVAL_END_MS, BLACKOUT_MS, FAREWELL, FAREWELL_END_MS,
    TRANSFORM_MS, answer_timeline,
)
from acts.act_three.awakening.state import AwakeningScene
from game.combat_log import add_log_message
from levels import FLOOR_CONFIGS
from acts.act_three.awakening.staging import read_awakening_markers


def _nearby_cell(floor, origin):
    occupied = {(e.column, e.row) for e in floor.enemies if e.health > 0}
    candidates = [
        (column, row)
        for row, line in enumerate(floor.map)
        for column, tile in enumerate(line)
        if tile == "." and (column, row) != origin
        and (column, row) not in occupied
    ]
    return min(
        candidates,
        key=lambda cell: abs(cell[0] - (origin[0] - 2)) + abs(cell[1] - origin[1]),
        default=origin,
    )


def reveal_awakening_arena(game_state):
    floor = game_state.floor
    scene = game_state.act_three.awakening
    if scene is None or scene.world_swapped or floor.boss_room is None:
        return
    room = floor.boss_room
    cells = {
        (column, row)
        for row in range(max(0, room.y - 1), min(len(floor.map), room.y + room.height + 1))
        for column in range(max(0, room.x - 1), min(len(floor.map[row]), room.x + room.width + 1))
    }
    floor.visible_cells.update(cells)
    floor.explored_cells.update(cells)


def begin_awakening(game_state, current_time):
    if game_state.act_three.awakening is not None:
        return
    floor = game_state.floor
    death = floor.oracle_death
    boss = death.position if death is not None else (
        floor.player_column - 2, floor.player_row,
    )
    if death is not None:
        death.finished = True
        death.caster.health = 0
    floor.projectiles.clear()
    game_state.act_three.awakening = AwakeningScene(
        updated_at=current_time,
        old_man_position=_nearby_cell(floor, (floor.player_column, floor.player_row)),
        boss_position=boss,
    )
    game_state.act_three_transition_open = True
    game_state.act_three_transition_started_at = current_time
    game_state.game_won = False
    game_state.player_attack_targets.clear()
    game_state.player.act_two_movement_origin = None
    game_state.player.directional_ability_aiming = False
    game_state.player.act_two.fire_bomb_aiming = False
    game_state.act_two_stats_open = False
    game_state.act_two_journal_open = False
    reveal_awakening_arena(game_state)


def _set_phase(scene, phase, current_time):
    scene.phase = phase
    scene.elapsed = 0
    scene.updated_at = current_time
    scene.logged_lines = 0


def enter_act_three(game_state):
    scene = game_state.act_three.awakening
    if scene.world_swapped:
        return
    from game.factories import create_floor_state

    target = next(i for i, config in enumerate(FLOOR_CONFIGS) if config["act"] == 3)
    game_state.run_stats.completed_floors.add(game_state.floor_index)
    floor = game_state.visited_floors.get(target)
    if floor is None:
        floor = create_floor_state(target)
        game_state.visited_floors[target] = floor
    game_state.floor_index = target
    game_state.floor = floor
    scene.world_swapped = True

    markers = read_awakening_markers(FLOOR_CONFIGS[target]["map_path"], floor)
    missing = {"awakening_player", "awakening_old_man"} - markers.keys()
    if missing:
        add_log_message(
            game_state.combat_log,
            "Missing saved TMX awakening markers: " + ", ".join(sorted(missing)) + ". Using fallback positions.",
            category="system",
        )
    player_position = markers.get("awakening_player", (floor.player_column, floor.player_row))
    floor.player_column, floor.player_row = player_position
    scene.old_man_position = markers.get("awakening_old_man", _nearby_cell(floor, player_position))
    game_state.player.facing_direction = (
        (1, 0) if scene.old_man_position[0] > player_position[0] else (-1, 0)
    )
    game_state.player.movement_origin = None
    game_state.player.movement_animation_started_at = 0
    game_state.player.key_count = 0
    game_state.player_attack_targets.clear()


def show_subclass_selection(game_state, current_time):
    scene = game_state.act_three.awakening
    enter_act_three(game_state)
    _set_phase(scene, "choice", current_time)
    game_state.act_three_transition_open = False
    if game_state.player.player_class in ("rogue", "warrior", "mage"):
        game_state.subclass_selection_open = True
    else:
        game_state.act_three_debug_class_selection_open = True


def skip_awakening(game_state, current_time):
    scene = game_state.act_three.awakening
    if scene.phase in ("transformation", "answer"):
        finish_awakening(game_state)
    else:
        show_subclass_selection(game_state, current_time)


def finish_awakening(game_state):
    game_state.act_three.awakening.phase = "complete"
    game_state.act_three_transition_open = False
    game_state.subclass_selection_open = False
    add_log_message(game_state.combat_log, "Act III begins. The world is alive.", category="progress")


def advance_awakening(game_state, current_time):
    scene = game_state.act_three.awakening
    if scene is None or scene.phase in ("choice", "complete"):
        return
    if not scene.paused:
        scene.elapsed += max(0, min(50, current_time - scene.updated_at))
    scene.updated_at = current_time
    timeline = {
        "farewell": FAREWELL,
        "arrival": ARRIVAL,
    }.get(scene.phase, ())
    if scene.phase == "answer":
        timeline = answer_timeline(game_state.player.subclass)
    while scene.logged_lines < len(timeline) and scene.elapsed >= timeline[scene.logged_lines][0]:
        _, _, speaker, text = timeline[scene.logged_lines]
        add_log_message(game_state.combat_log, f"{speaker}: {text}", category="dialogue")
        scene.logged_lines += 1
    if scene.phase == "farewell" and scene.elapsed >= FAREWELL_END_MS:
        _set_phase(scene, "blackout", current_time)
    elif scene.phase == "blackout" and scene.elapsed >= BLACKOUT_MS:
        enter_act_three(game_state)
        _set_phase(scene, "arrival", current_time)
    elif scene.phase == "arrival" and scene.elapsed >= ARRIVAL_END_MS:
        show_subclass_selection(game_state, current_time)
    elif scene.phase == "transformation" and scene.elapsed >= TRANSFORM_MS:
        _set_phase(scene, "answer", current_time)
    elif scene.phase == "answer" and scene.elapsed >= timeline[-1][1] + 650:
        finish_awakening(game_state)
