import pygame

from acts.act_three.cartography.geometry import close_rectangle, map_rectangle, map_viewport
from acts.act_three.cartography.lifecycle import map_visible
from acts.act_three.presentation.hud.layout import get_act_three_hud_layout


def handle_map_event(event, game_state, available, position, current_time):
    from acts.act_three.input.character_panel import can_open_character_panel

    state = game_state.act_three
    layout = get_act_three_hud_layout()
    if state.map_open:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            return False
        if event.type == pygame.WINDOWFOCUSLOST:
            state.map_drag_anchor = None
        if state.map_closing_at < 0:
            close_key = event.type == pygame.KEYDOWN and event.key in (pygame.K_m, pygame.K_ESCAPE) and not getattr(event, "repeat", False)
            close_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and position is not None and close_rectangle(layout).collidepoint(position)
            if close_key or close_click:
                state.map_closing_at = current_time
                state.map_drag_anchor = None
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                state.map_zoom = 1.0
                state.map_offset = (0.0, 0.0)
                state.map_drag_anchor = None
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and position is not None and map_viewport(layout, True).collidepoint(position):
                state.map_drag_anchor = position
                state.map_drag_offset = state.map_offset
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                state.map_drag_anchor = None
            elif event.type == pygame.MOUSEMOTION and state.map_drag_anchor is not None and position is not None:
                state.map_offset = (
                    state.map_drag_offset[0] + position[0] - state.map_drag_anchor[0],
                    state.map_drag_offset[1] + position[1] - state.map_drag_anchor[1],
                )
            elif event.type == pygame.MOUSEWHEEL and position is not None and map_viewport(layout, True).collidepoint(position):
                previous = state.map_zoom
                state.map_zoom = max(1.0, min(4.0, previous * 1.25 ** event.y))
                center = map_viewport(layout, True).center
                ratio = state.map_zoom / previous
                state.map_offset = tuple(
                    position[index] - center[index] - (position[index] - center[index] - state.map_offset[index]) * ratio
                    for index in (0, 1)
                )
                state.map_drag_anchor = None
        return event.type in (
            pygame.KEYDOWN, pygame.KEYUP, pygame.TEXTINPUT, pygame.MOUSEMOTION,
            pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL,
        )
    visible = map_visible(game_state)
    over_minimap = visible and position is not None and map_rectangle(layout).collidepoint(position)
    pointer_event = event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL)
    if not available or not visible or not can_open_character_panel(game_state, available):
        return over_minimap and pointer_event
    key = event.type == pygame.KEYDOWN and event.key == pygame.K_m
    click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and position is not None and map_rectangle(layout).collidepoint(position)
    if (key and not getattr(event, "repeat", False) and not getattr(event, "automatic_movement", False)) or click:
        state.map_open = True
        state.map_opened_at = current_time
        state.map_closing_at = -1
        state.map_zoom = 1.0
        state.map_offset = (0.0, 0.0)
        state.map_drag_anchor = None
        return True
    return over_minimap and pointer_event
