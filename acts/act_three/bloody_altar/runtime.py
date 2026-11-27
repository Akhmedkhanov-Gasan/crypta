import random
import pygame

from acts.act_three.bloody_altar.catalog import PACTS_BY_ID, RARITY_WEIGHTS, eligible_pacts
from systems.grid_geometry import can_reach_adjacent_cell
from acts.act_three.rune_master.state import RuneCard, RuneMenuState
from acts.act_three.rune_master.runtime import PHASE_DURATIONS


def altar_position(floor):
    altar = floor.act_three_bloody_altar
    return tuple(altar["position"]) if altar is not None else None


def adjacent_to_altar(game_state):
    floor = game_state.floor
    target = altar_position(floor)
    return target is not None and can_reach_adjacent_cell(
        floor.map, (floor.player_column, floor.player_row), target, floor.barriers,
        target_must_be_walkable=False,
    )


def menu_altar(game_state):
    console = game_state.act_three.altar_console
    return console if console is not None else game_state.floor.act_three_bloody_altar


def open_altar(game_state, *, from_console=False, current_time=None):
    if (not from_console and not adjacent_to_altar(game_state)) or game_state.player.health <= 0:
        return False
    game_state.act_three.altar_console = (
        {"position": (game_state.floor.player_column, game_state.floor.player_row), "offers": [], "claimed": False}
        if from_console else None
    )
    altar = menu_altar(game_state)
    if altar["claimed"] or game_state.player.act_three.altar_pact_id is not None:
        from game.combat_log import add_log_message

        add_log_message(game_state.combat_log, "The bloody altar has fallen silent.", category="altar")
        return True
    if not altar["offers"]:
        choices = list(eligible_pacts(game_state.player))
        for _ in range(min(3, len(choices))):
            pact = random.choices(choices, weights=[RARITY_WEIGHTS[p.rarity] for p in choices], k=1)[0]
            altar["offers"].append(pact.id)
            choices = [candidate for candidate in choices
                       if candidate.id != pact.id and not (pact.rarity == "legendary" and candidate.rarity == "legendary")]
    state = game_state.act_three
    state.altar_menu_open = True
    state.altar_selected = None
    state.altar_confirming = False
    state.altar_hover = None
    now = pygame.time.get_ticks() if current_time is None else current_time
    state.altar_motion = RuneMenuState(
        choices=tuple(RuneCard(identifier, "pact", PACTS_BY_ID[identifier].name,
                               PACTS_BY_ID[identifier].description) for identifier in altar["offers"]),
        page="choices", pending_page="choices", started_at=now, opened_at=now,
    )
    state.sidebar_tab = "closed"
    game_state.player_attack_targets = []
    return True


def close_altar(game_state):
    state = game_state.act_three
    state.altar_menu_open = False
    state.altar_motion = None
    state.altar_console = None
    state.altar_selected = None
    state.altar_confirming = False
    state.altar_hover = None


def choose_pact(game_state, index, current_time):
    state = game_state.act_three
    menu = state.altar_motion
    if menu is None or menu.phase != "idle" or menu.pending_button_action is not None:
        return False
    if not 0 <= index < len(menu.choices):
        return False
    menu.focus = index
    if menu.selected_choice != index:
        menu.previous_choice = menu.selected_choice
        menu.selected_choice = index
        menu.selection_started_at = current_time
    state.altar_selected = index
    return True


def confirm_pact(game_state, current_time=None):
    state = game_state.act_three
    menu = state.altar_motion
    if menu is None or menu.phase != "idle" or state.altar_selected is None:
        return False
    menu.selected_choice = state.altar_selected
    menu.phase = "confirming"
    menu.started_at = pygame.time.get_ticks() if current_time is None else current_time
    menu.confirming_choice = True
    menu.pressed = None
    state.altar_confirming = True
    return True


def advance_altar(game_state, current_time):
    state = game_state.act_three
    menu = state.altar_motion
    if not state.altar_menu_open:
        return
    if game_state.player.health <= 0 or game_state.floor_transition_started_at >= 0:
        close_altar(game_state)
        return
    if menu is None:
        altar = menu_altar(game_state)
        menu = RuneMenuState(page="choices", pending_page="choices", phase="idle",
                             choices=tuple(RuneCard(identifier, "pact", PACTS_BY_ID[identifier].name,
                                                    PACTS_BY_ID[identifier].description) for identifier in altar["offers"]),
                             selected_choice=state.altar_selected, started_at=current_time, opened_at=current_time)
        state.altar_motion = menu
    if menu.pending_button_action is not None and current_time - menu.pending_button_started_at >= 180:
        action = menu.pending_button_action
        menu.pending_button_action = None
        if action == "confirm":
            confirm_pact(game_state, menu.pending_button_started_at + 180)
    while menu.phase in PHASE_DURATIONS:
        duration = PHASE_DURATIONS[menu.phase]
        if current_time - menu.started_at < duration:
            break
        menu.started_at += duration
        if menu.phase == "opening":
            menu.phase = "idle"
        elif menu.phase == "confirming":
            menu.phase = "confirmed"
        elif menu.phase == "confirmed":
            if not _accept_pact(game_state):
                close_altar(game_state)
                return
            menu.phase = "confirmation_fade"
        else:
            close_altar(game_state)
            return


def _accept_pact(game_state):
    state = game_state.act_three
    altar = menu_altar(game_state)
    player = game_state.player
    index = state.altar_selected
    if (not state.altar_menu_open or altar is None or altar["claimed"]
            or (state.altar_console is None and not adjacent_to_altar(game_state))
            or player.health <= 0 or index is None or not 0 <= index < len(altar["offers"])):
        return False
    pact = PACTS_BY_ID.get(altar["offers"][index])
    if pact is None or pact not in eligible_pacts(player):
        return False
    if pact.precursor is not None:
        player.max_health += player.act_two.bloody_pact_health_penalty
        player.act_two.bloody_pact_health_penalty = 0
        player.act_two.bloody_pact_id = None
        player.act_two.blood_hunger_healing_progress = 0.0
        player.act_two.open_wound_healing_progress = 0.0
    player.act_three.altar_pact_id = pact.id
    player.act_three.altar_attack_chain = 0
    player.act_three.altar_healing_progress = 0.0
    player.act_three.altar_lifesteal_progress = 0.0
    player.act_three.reprieve_ready = pact.id == "deaths_reprieve"
    player.act_three.reprieve_kills = 0
    if pact.id == "shattered_seal":
        player.selected_rune_id = None
        player.ability_kill_charge = min(1, player.ability_kill_charge)
    from acts.act_three.attributes import refresh_glass_heart_penalty
    from game.combat_log import add_log_message
    from game.events import GameEvent, GameEventType

    refresh_glass_heart_penalty(player)
    altar["claimed"] = True
    game_state.emit(GameEvent(type=GameEventType.ENVIRONMENT, actor="bloody altar",
                              origin=tuple(altar["position"]), data={"kind": "act_three_pact", "pact_id": pact.id}))
    add_log_message(game_state.combat_log, f"You accept {pact.name}. The sacrifice is permanent.", category="altar")
    return True
