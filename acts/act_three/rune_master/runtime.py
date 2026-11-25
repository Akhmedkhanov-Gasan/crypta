from acts.act_three.rune_master.catalog import available_abilities, upgrade_choices
from acts.act_three.rune_master.state import RuneMenuState
from acts.act_three.rune_master.selection import apply_rune


PHASE_DURATIONS = {
    "opening": 480,
    "fading_out": 320,
    "mist": 60,
    "revealing": 480,
    "confirming": 420,
    "confirmed": 380,
    "confirmation_fade": 260,
}
NEXT_PHASE = {
    "opening": "idle",
    "fading_out": "mist",
    "mist": "revealing",
    "revealing": "idle",
    "confirming": "confirmed",
    "confirmed": "confirmation_fade",
    "confirmation_fade": "revealing",
}


def open_menu(game_state, current_time):
    game_state.act_three.rune_menu = RuneMenuState(
        abilities=available_abilities(
            game_state.player,
            ignore_access=game_state.act_three.npc_menu_from_console == "rune_master",
        ),
        started_at=current_time, opened_at=current_time,
    )


def advance_menu(game_state, current_time):
    menu = game_state.act_three.rune_menu
    if menu is None:
        return
    if menu.pending_button_action is not None and current_time - menu.pending_button_started_at >= 180:
        action = menu.pending_button_action
        menu.pending_button_action = None
        return_to_abilities(game_state, current_time, confirm=action == "confirm")
    while menu.phase in PHASE_DURATIONS:
        duration = PHASE_DURATIONS[menu.phase]
        if current_time - menu.started_at < duration:
            break
        menu.started_at += duration
        menu.phase = NEXT_PHASE[menu.phase]
        if menu.phase == "revealing":
            if menu.page == "choices" and menu.pending_page == "abilities" and menu.confirming_choice:
                choice = menu.choices[menu.selected_choice]
                if apply_rune(game_state, choice, current_time):
                    menu.abilities = available_abilities(
                        game_state.player,
                        ignore_access=game_state.act_three.npc_menu_from_console == "rune_master",
                    )
                menu.confirming_choice = False
            menu.page = menu.pending_page
        if menu.phase == "idle":
            menu.focus = 0
            menu.keyboard_focus = False


def visible_cards(menu):
    if menu.page == "choices":
        return menu.choices
    return menu.abilities


def _transition(menu, target, current_time):
    menu.pending_page = target
    menu.phase = "fading_out"
    menu.started_at = current_time
    menu.pressed = None


def choose_card(game_state, index, current_time):
    menu = game_state.act_three.rune_menu
    if menu is None or menu.phase != "idle" or not 0 <= index < len(visible_cards(menu)):
        return
    menu.focus = index
    if menu.page == "choices":
        if menu.selected_choice == index:
            return
        menu.previous_choice = menu.selected_choice
        menu.selected_choice = index
        menu.selection_started_at = current_time
        return
    menu.selected_ability = index
    menu.selected_choice = None
    menu.previous_choice = None
    menu.selection_started_at = current_time
    menu.choices = upgrade_choices(game_state.player, menu.abilities[index].slot)
    _transition(menu, "choices", current_time)


def return_to_abilities(game_state, current_time, confirm=False):
    menu = game_state.act_three.rune_menu
    if menu is None or menu.phase != "idle" or menu.page != "choices":
        return
    if confirm:
        if menu.selected_choice is None:
            return
        if menu.choices[menu.selected_choice].placeholder:
            return
        menu.confirming_choice = True
        menu.pending_page = "abilities"
        menu.phase = "confirming"
        menu.started_at = current_time
        menu.pressed = None
        return
    _transition(menu, "abilities", current_time)
