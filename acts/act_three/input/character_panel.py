import pygame

from acts.act_three.input.consumables import BELT_SLOTS_BY_KEY
from acts.mage_targeting import mage_aiming
from acts.act_three.items.inventory import assign_inventory_item_to_belt
from acts.act_three.presentation.hud.geometry import (
    get_character_panel_focus_rectangles,
    resolve_character_panel_focus,
)
from acts.act_three.presentation.hud.layout import get_act_three_hud_layout
from acts.act_three.progression import (
    cancel_act_three_attribute_upgrade,
    clear_act_three_attribute_upgrades,
    confirm_act_three_attribute_upgrades,
    queue_act_three_attribute_upgrade,
)
from application.directional_input import CHORD_MOVEMENT_KEYS, movement_direction_for_key
from game.combat_log import add_log_message


def can_open_character_panel(game_state, movement_available):
    player = game_state.player
    return (
        movement_available
        and game_state.act_three.barrage_turn is None
        and not mage_aiming(player)
        and not player.archer_basic_aiming
        and not player.archer_piercing_aiming
        and not player.summoner_aiming
        and not player.summoner_familiar_summon_aiming
    )


def set_sidebar_tab(game_state, tab):
    if game_state.sidebar_tab == "stats":
        clear_act_three_attribute_upgrades(game_state.player)
        game_state.player.act_three.item_drag = None
    game_state.sidebar_tab = tab
    game_state.act_three.character_panel_focus = None
    game_state.act_three.character_panel_keyboard_focus = tab == "stats"


def confirm_character_panel_upgrades(game_state):
    if confirm_act_three_attribute_upgrades(game_state.player):
        add_log_message(
            game_state.combat_log, "Attribute upgrades confirmed.", category="progress",
        )


def activate_character_attribute(game_state, name, action):
    game_state.act_three.character_panel_focus = f"attribute:{name}:{action}"
    change = queue_act_three_attribute_upgrade if action == "plus" else cancel_act_three_attribute_upgrade
    change(game_state.player, name)


def _move_focus(rectangles, focus, direction):
    origin = rectangles[focus].center
    dx, dy = direction
    candidates = []
    for name, rectangle in rectangles.items():
        x = rectangle.centerx - origin[0]
        y = rectangle.centery - origin[1]
        forward = x * dx + y * dy
        if forward <= 0:
            continue
        sideways = abs(x * dy - y * dx)
        candidates.append((forward + 3 * sideways, sideways, name))
    return min(candidates)[2] if candidates else focus


def handle_character_panel_key(event, game_state, can_open):
    state = game_state.act_three
    panel_open = game_state.sidebar_tab == "stats"
    if event.key == pygame.K_TAB:
        if panel_open:
            if not getattr(event, "repeat", False):
                set_sidebar_tab(game_state, "closed")
            return True
        if can_open and not getattr(event, "repeat", False):
            set_sidebar_tab(game_state, "stats")
            return True
        return False
    if not panel_open:
        return False

    if getattr(event, "automatic_movement", False):
        return True
    if event.key == pygame.K_ESCAPE:
        if game_state.player.act_three.item_drag is not None:
            game_state.player.act_three.item_drag = None
        else:
            set_sidebar_tab(game_state, "closed")
        return True
    if game_state.player.act_three.item_drag is not None:
        return True

    panel = get_act_three_hud_layout()["right_bar"]["character_panel"]
    rectangles = get_character_panel_focus_rectangles(panel, game_state.player)
    focus = resolve_character_panel_focus(rectangles, state.character_panel_focus)
    state.character_panel_focus = focus
    state.character_panel_keyboard_focus = True

    if event.key in CHORD_MOVEMENT_KEYS:
        state.character_panel_focus = _move_focus(
            rectangles, focus, movement_direction_for_key(event.key),
        )
    elif event.key == pygame.K_SPACE and not getattr(event, "repeat", False):
        confirm_character_panel_upgrades(game_state)
    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and not getattr(event, "repeat", False):
        if focus.startswith("attribute:"):
            _, name, *actions = focus.split(":")
            activate_character_attribute(game_state, name, actions[0] if actions else "plus")
        elif focus == "confirm":
            confirm_character_panel_upgrades(game_state)
    elif focus.startswith("inventory:") and not getattr(event, "repeat", False):
        belt_slot = BELT_SLOTS_BY_KEY.get(event.key)
        if belt_slot is not None:
            slot_name = focus.split(":", 1)[1]
            source_index = sorted(panel["inventory"]["slots"]).index(slot_name)
            assign_inventory_item_to_belt(game_state, source_index, belt_slot)
    return True
