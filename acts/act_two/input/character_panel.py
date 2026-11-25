import pygame

from acts.act_two.consumables import cancel_fire_bomb_aiming, cancel_scroll_aiming
from acts.act_two.controls import CONSUMABLE_KEYS
from acts.act_two.presentation.hud_focus import character_panel_rectangles, resolve_panel_focus
from acts.act_two.progression import (
    cancel_queued_act_two_attribute_upgrade,
    confirm_queued_act_two_attribute_upgrades,
    queue_act_two_attribute_upgrade,
)
from application.directional_input import CHORD_MOVEMENT_KEYS, movement_direction_for_key
from game.combat_log import add_log_message
from presentation.directional_focus import move_focus
from presentation.journal import scroll_journal
from systems.player_abilities import cancel_ability_aiming


def set_panel_open(game_state, opened):
    player = game_state.player
    game_state.act_two_stats_open = opened
    game_state.act_two_journal_open = False
    player.act_two.interface_focus = None
    player.act_two.interface_keyboard_focus = opened
    if not opened:
        for name in player.act_two.pending_attribute_upgrades:
            player.act_two.pending_attribute_upgrades[name] = 0
    else:
        cancel_ability_aiming(game_state)
        cancel_fire_bomb_aiming(game_state)
        cancel_scroll_aiming(game_state)


def handle_panel_key(event, game_state, layout):
    if event.type != pygame.KEYDOWN:
        return False
    if getattr(event, "dropped_consumable_slot", None) is not None:
        return False
    player = game_state.player
    if getattr(event, "automatic_movement", False) and (game_state.act_two_stats_open or game_state.act_two_journal_open):
        return True
    if event.key == pygame.K_TAB:
        if not getattr(event, "repeat", False):
            set_panel_open(game_state, not game_state.act_two_stats_open)
        return True
    if event.key == pygame.K_j:
        if not getattr(event, "repeat", False):
            opened = not game_state.act_two_journal_open
            set_panel_open(game_state, False)
            cancel_ability_aiming(game_state)
            cancel_fire_bomb_aiming(game_state)
            cancel_scroll_aiming(game_state)
            game_state.act_two_journal_open = opened
            game_state.act_two_journal_scroll = 1.0
            game_state.act_two_journal_dragging = False
        return True
    if game_state.act_two_journal_open:
        if event.key == pygame.K_ESCAPE:
            game_state.act_two_journal_open = False
        elif event.key in (pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN):
            direction = -1 if event.key in (pygame.K_w, pygame.K_UP) else 1
            game_state.act_two_journal_scroll = scroll_journal(
                layout["journal_panel"], game_state.combat_log,
                game_state.act_two_journal_scroll, direction,
            )
        return True
    if not game_state.act_two_stats_open:
        return False
    if event.key == pygame.K_ESCAPE:
        set_panel_open(game_state, False)
        return True
    if getattr(event, "automatic_movement", False):
        return True
    rectangles = character_panel_rectangles(layout, player)
    focus = resolve_panel_focus(rectangles, player.act_two.interface_focus)
    player.act_two.interface_focus = focus
    player.act_two.interface_keyboard_focus = True
    if event.key in CHORD_MOVEMENT_KEYS:
        player.act_two.interface_focus = move_focus(rectangles, focus, movement_direction_for_key(event.key))
    elif not getattr(event, "repeat", False):
        if event.key == pygame.K_SPACE or (focus == "confirm" and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)):
            confirmed, message = confirm_queued_act_two_attribute_upgrades(player)
            if confirmed:
                add_log_message(game_state.combat_log, message, category="progress")
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and focus.startswith("attribute:"):
            _, name, *action = focus.split(":")
            change = cancel_queued_act_two_attribute_upgrade if action == ["minus"] else queue_act_two_attribute_upgrade
            change(player, name)
        elif focus.startswith("belt:"):
            source = int(focus.split(":")[1])
            destination = CONSUMABLE_KEYS.get(event.key)
            if destination is not None:
                slots = player.act_two.consumable_slots
                slots[source], slots[destination] = slots[destination], slots[source]
                player.act_two.interface_focus = f"belt:{destination}"
            elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                if player.act_two.consumable_slots[source] is not None:
                    dx, dy = player.act_two_facing_direction
                    target = (game_state.floor.player_column + dx, game_state.floor.player_row + dy)
                    pygame.event.post(pygame.event.Event(
                        pygame.KEYDOWN,
                        key=pygame.K_UNKNOWN,
                        dropped_consumable_slot=source,
                        dropped_consumable_target=target,
                        dropped_consumable_started_at=pygame.time.get_ticks(),
                    ))
    return True
