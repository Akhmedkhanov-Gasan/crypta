import pygame

from acts.act_three.rune_master.layout import get_layout
from acts.act_three.rune_master.motion import card_hitbox, card_poses
from acts.act_three.rune_master.runtime import choose_card, visible_cards
from presentation.figma_ui import figma_rect


def _control_at(menu, position, current_time):
    if position is None:
        return None
    layout = get_layout()
    if figma_rect(layout["close_hitbox"]).collidepoint(position):
        return "close"
    if menu.phase != "idle":
        return None
    if menu.page == "choices":
        if figma_rect(layout["return_button"]["hitbox"]).collidepoint(position):
            return "back"
        if menu.selected_choice is not None and not menu.choices[menu.selected_choice].placeholder and figma_rect(layout["confirm_button"]["hitbox"]).collidepoint(position):
            return "confirm"
    for pose in reversed(card_poses(menu, layout, current_time)):
        if card_hitbox(layout, pose).collidepoint(position):
            return f"card:{pose.index}"
    return None


def _activate(control, game_state, current_time):
    if control == "close":
        from acts.act_three.npcs import close_npc_dialog

        close_npc_dialog(game_state, current_time)
    elif control in ("back", "confirm"):
        menu = game_state.act_three.rune_menu
        if menu.phase != "idle" or menu.page != "choices" or menu.pending_button_action is not None:
            return
        if control == "confirm" and (menu.selected_choice is None or menu.choices[menu.selected_choice].placeholder):
            return
        menu.pending_button_action = control
        menu.pending_button_started_at = current_time
    elif control is not None and control.startswith("card:"):
        choose_card(game_state, int(control.split(":")[1]), current_time)


def handle_rune_menu_event(event, game_state, mouse_position):
    menu = game_state.act_three.rune_menu
    if menu is None:
        return False
    current_time = pygame.time.get_ticks()
    if event.type == pygame.MOUSEMOTION:
        menu.keyboard_focus = False
    if event.type == pygame.WINDOWFOCUSLOST:
        menu.pressed = None
        return True
    if menu.pending_button_action is not None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            _activate("close", game_state, current_time)
        return True
    if event.type == pygame.KEYDOWN:
        if getattr(event, "automatic_movement", False) or getattr(event, "repeat", False):
            return True
        if event.key == pygame.K_ESCAPE:
            _activate("close", game_state, current_time)
        elif menu.phase == "idle":
            count = len(visible_cards(menu))
            if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d) and count:
                menu.keyboard_focus = True
                delta = -1 if event.key in (pygame.K_LEFT, pygame.K_a) else 1
                menu.focus = (menu.focus + delta) % count
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                menu.keyboard_focus = True
                choose_card(game_state, event.key - pygame.K_1, current_time)
            elif event.key == pygame.K_BACKSPACE:
                _activate("back", game_state, current_time)
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                if menu.page == "choices" and menu.selected_choice is not None and event.key != pygame.K_SPACE:
                    _activate("confirm", game_state, current_time)
                else:
                    choose_card(game_state, menu.focus, current_time)
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        menu.pressed = _control_at(menu, mouse_position, current_time)
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        control = _control_at(menu, mouse_position, current_time)
        pressed = menu.pressed
        menu.pressed = None
        if pressed is not None and pressed == control:
            _activate(control, game_state, current_time)
    return True
