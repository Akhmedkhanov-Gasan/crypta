import pygame

from acts.act_three.summoner_trial import busy, interact, handle_action


def handle_pointer(event, game_state, convert, movement_state):
    trial = game_state.floor.summoner_trial
    if trial is None:
        return False
    if busy(trial):
        movement_state.cancel_auto_move()
        movement_state.reset_held_movement()
        return event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.MOUSEWHEEL)
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return False
    from acts.act_three.presentation.hit_testing import get_act_three_cell_from_position
    from application.auto_movement import start_auto_move

    position = convert(event.pos)
    if position is None:
        return False
    cell = get_act_three_cell_from_position(game_state, position)
    origin = game_state.floor.player_column, game_state.floor.player_row
    if cell == trial["door"] and trial["phase"] == "closed":
        if max(abs(cell[0] - origin[0]), abs(cell[1] - origin[1])) <= 1:
            movement_state.cancel_auto_move()
            handle_action(game_state, event, (cell[0] - origin[0], cell[1] - origin[1]))
        else:
            start_auto_move(movement_state, game_state, cell)
        return True
    if trial["phase"] != "active":
        return False
    side = trial["side"]
    index = next((i for i in range(3) if trial["parts"][i] == side and cell == trial["positions"][side][i]), None)
    boat = cell in (trial["docks"][side], (trial["docks"][side][0] + 1, trial["docks"][side][1]))
    if index is None and not boat:
        return False
    if index is not None:
        nearby = abs(origin[0] - cell[0]) + abs(origin[1] - cell[1]) == 1
    else:
        nearby = max(abs(origin[0] - trial["starts"][side][0]), abs(origin[1] - trial["starts"][side][1])) <= 1
    if nearby:
        movement_state.cancel_auto_move()
        interact(game_state, ("part", index) if index is not None else ("boat", None))
    elif boat:
        start_auto_move(movement_state, game_state, trial["starts"][side])
    else:
        candidates = [(cell[0] + dx, cell[1] + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))]
        candidates = [candidate for candidate in candidates if 0 <= candidate[1] < len(game_state.floor.map) and 0 <= candidate[0] < len(game_state.floor.map[candidate[1]]) and game_state.floor.map[candidate[1]][candidate[0]] == "."]
        if candidates:
            target = min(candidates, key=lambda item: abs(item[0] - origin[0]) + abs(item[1] - origin[1]))
            start_auto_move(movement_state, game_state, target)
    return True
