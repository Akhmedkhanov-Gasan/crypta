from systems.grid_geometry import can_reach_adjacent_cell


NPC_FOOTPRINTS = {
    "blacksmith": (2, 1),
}
NPC_FRAME_COUNT = 8
NPC_TRANSITION_FRAME_MS = 90
NPC_LOOP_FRAME_MS = 150
NPC_TRANSITION_MS = NPC_FRAME_COUNT * NPC_TRANSITION_FRAME_MS


def get_npc_cells(npc):
    column, row = npc["position"]
    width, height = NPC_FOOTPRINTS[npc["type"]]
    return {
        (column + dx, row + dy)
        for dy in range(height)
        for dx in range(width)
    }


def get_npc_at(floor, position):
    return next(
        (
            npc
            for npc in floor.act_three_npcs
            if position in get_npc_cells(npc)
        ),
        None,
    )


def open_npc_dialog(game_state, npc, current_time):
    state = game_state.act_three
    floor = game_state.floor
    if (
        state.npc_dialog_position is not None
        or game_state.player.health <= 0
        or game_state.game_won
    ):
        return False

    cells = get_npc_cells(npc)
    origin = (floor.player_column, floor.player_row)
    if not cells.intersection(floor.visible_cells):
        return False
    if not any(
        can_reach_adjacent_cell(
            floor.map,
            origin,
            target,
            floor.barriers,
            target_must_be_walkable=False,
        )
        for target in cells
    ):
        return False

    state.npc_dialog_position = npc["position"]
    state.npc_dialog_floor_index = game_state.floor_index
    state.npc_dialog_phase = "opening"
    state.npc_dialog_started_at = current_time
    return True


def close_npc_dialog(game_state, current_time):
    state = game_state.act_three
    if state.npc_dialog_phase not in ("opening", "talk"):
        return

    frame = NPC_FRAME_COUNT - 1
    if state.npc_dialog_phase == "opening":
        frame = min(
            frame,
            max(0, current_time - state.npc_dialog_started_at)
            // NPC_TRANSITION_FRAME_MS,
        )

    state.npc_dialog_phase = "closing"
    state.npc_dialog_started_at = (
        current_time
        - (NPC_FRAME_COUNT - 1 - frame) * NPC_TRANSITION_FRAME_MS
    )


def advance_npc_dialog(game_state, current_time):
    state = game_state.act_three
    if state.npc_dialog_position is None:
        return

    npc = get_npc_at(game_state.floor, state.npc_dialog_position)
    if (
        state.npc_dialog_floor_index != game_state.floor_index
        or npc is None
        or game_state.player.health <= 0
        or game_state.game_won
    ):
        state.npc_dialog_position = None
        state.npc_dialog_floor_index = -1
        state.npc_dialog_phase = "closed"
        state.npc_dialog_started_at = 0
        return

    elapsed = max(0, current_time - state.npc_dialog_started_at)
    if elapsed < NPC_TRANSITION_MS:
        return

    if state.npc_dialog_phase == "opening":
        state.npc_dialog_phase = "talk"
        state.npc_dialog_started_at += NPC_TRANSITION_MS
    elif state.npc_dialog_phase == "closing":
        state.npc_dialog_position = None
        state.npc_dialog_floor_index = -1
        state.npc_dialog_phase = "closed"
        state.npc_dialog_started_at = 0


def get_npc_animation(game_state, npc, current_time):
    state = game_state.act_three
    if (
        state.npc_dialog_floor_index != game_state.floor_index
        or state.npc_dialog_position != npc["position"]
    ):
        return (
            "work_down",
            current_time // NPC_LOOP_FRAME_MS % NPC_FRAME_COUNT,
        )

    elapsed = max(0, current_time - state.npc_dialog_started_at)
    if state.npc_dialog_phase in ("opening", "closing"):
        frame = min(
            NPC_FRAME_COUNT - 1,
            elapsed // NPC_TRANSITION_FRAME_MS,
        )
        if state.npc_dialog_phase == "closing":
            frame = NPC_FRAME_COUNT - 1 - frame
        return "talk_start_down", frame

    return (
        "talk_idle_down",
        elapsed // NPC_LOOP_FRAME_MS % NPC_FRAME_COUNT,
    )
