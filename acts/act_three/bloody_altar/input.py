import pygame

from acts.act_three.bloody_altar.presentation import get_layout
from acts.act_three.bloody_altar.motion import hitbox, poses
from acts.act_three.bloody_altar.runtime import advance_altar, choose_pact, close_altar
from presentation.figma_ui import figma_rect


def _control_at(menu, position, current_time):
    if position is None:
        return None
    layout = get_layout()
    if figma_rect(layout["close_hitbox"]).collidepoint(position):
        return "close"
    if menu.phase != "idle" or menu.pending_button_action is not None:
        return None
    if menu.selected_choice is not None and figma_rect(layout["confirm_button"]["hitbox"]).collidepoint(position):
        return "confirm"
    for pose in reversed(poses(menu, layout, current_time)):
        if hitbox(layout, pose).collidepoint(position):
            return f"card:{pose.index}"
    return None


def _activate(game_state, control, current_time):
    menu = game_state.act_three.altar_motion
    if control == "close":
        close_altar(game_state)
    elif control == "confirm":
        if menu.phase != "idle" or menu.pending_button_action is not None:
            return
        if control == "confirm" and menu.selected_choice is None:
            return
        menu.pending_button_action = control
        menu.pending_button_started_at = current_time
    elif control is not None and control.startswith("card:"):
        choose_pact(game_state, int(control.split(":")[1]), current_time)


def handle_key(event, game_state):
    if not game_state.act_three.altar_menu_open:
        return False
    now = pygame.time.get_ticks()
    advance_altar(game_state, now)
    menu = game_state.act_three.altar_motion
    if menu is None:
        return True
    if getattr(event, "repeat", False) or getattr(event, "automatic_movement", False):
        return True
    if event.key == pygame.K_ESCAPE:
        _activate(game_state, "close", now)
    elif menu.phase == "idle" and menu.pending_button_action is None:
        count = len(menu.choices)
        if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d) and count:
            menu.keyboard_focus = True
            delta = -1 if event.key in (pygame.K_LEFT, pygame.K_a) else 1
            menu.focus = (menu.focus + delta) % count
        elif pygame.K_1 <= event.key <= pygame.K_3:
            menu.keyboard_focus = True
            choose_pact(game_state, event.key - pygame.K_1, now)
        elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            if menu.selected_choice is not None and (event.key != pygame.K_SPACE or menu.selected_choice == menu.focus):
                _activate(game_state, "confirm", now)
            else:
                menu.keyboard_focus = True
                choose_pact(game_state, menu.focus, now)
    return True


def handle_pointer(event, game_state, position):
    if not game_state.act_three.altar_menu_open:
        return False
    now = pygame.time.get_ticks()
    advance_altar(game_state, now)
    menu = game_state.act_three.altar_motion
    if menu is None:
        return True
    if event.type == pygame.MOUSEMOTION:
        menu.keyboard_focus = False
    if event.type == pygame.WINDOWFOCUSLOST:
        menu.pressed = None
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
        _activate(game_state, "close", now)
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        menu.pressed = _control_at(menu, position, now)
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        pressed = menu.pressed
        menu.pressed = None
        control = _control_at(menu, position, now)
        if pressed is not None and pressed == control:
            _activate(game_state, control, now)
    return True
