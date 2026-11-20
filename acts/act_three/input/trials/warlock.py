import pygame

from acts.act_three.trials.warlock import is_spirit, slide
from acts.act_three.presentation.trials.warlock import board_rect


def handle_pointer(event, game_state, convert, movement_state):
    trial = game_state.floor.curse_trial
    if trial is not None and trial["phase"] == "body_rite":
        movement_state.cancel_auto_move()
        movement_state.reset_held_movement()
        return event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.MOUSEWHEEL)
    if not is_spirit(trial):
        return False
    movement_state.cancel_auto_move()
    movement_state.reset_held_movement()
    if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
        return False
    if trial["phase"] != "active":
        return True
    position = convert(getattr(event, "pos", pygame.mouse.get_pos()))
    if position is None:
        return True
    rect = board_rect(trial)
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and rect.collidepoint(position):
        left, top, right, bottom = trial["bounds"]
        bottom += 1
        cell = left + int((position[0] - rect.x) * (right - left) / rect.width), top + int((position[1] - rect.y) * (bottom - top) / rect.height)
        if cell in trial["parts"]:
            trial["selected"] = trial["parts"].index(cell)
            trial["drag"] = position
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        origin = trial["drag"]
        trial["drag"] = None
        if origin is not None:
            dx, dy = position[0] - origin[0], position[1] - origin[1]
            if max(abs(dx), abs(dy)) >= 12:
                direction = (1 if dx > 0 else -1, 0) if abs(dx) >= abs(dy) else (0, 1 if dy > 0 else -1)
                slide(game_state, direction)
    return True
