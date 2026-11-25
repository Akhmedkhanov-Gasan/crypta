import pygame

from acts.act_three.presentation.hud.layout import get_act_three_hud_layout
from acts.act_three.presentation.hud.geometry import (
    get_act_three_journal_scroll_ratio,
    get_act_three_journal_scrollbar_rectangles,
)
from presentation.display import game_viewport
from presentation.journal import scroll_journal
from settings import GAME_HEIGHT


def scroll_act_three_journal(game_state, direction):
    game_state.act_three.journal_dragging = False
    ratio = get_act_three_journal_scroll_ratio(game_state)
    game_state.act_three.journal_scroll_ratio = scroll_journal(
        get_act_three_hud_layout()["journal_panel"], game_state.combat_log,
        ratio, direction, inset=True,
    )


def handle_journal_pointer(event, game_state, screen, window_to_game_position):
    state = game_state.act_three
    if (
        game_state.sidebar_tab != "journal"
        or game_state.act_three_transition_open
        or game_state.subclass_selection_open
        or game_state.player.health <= 0
    ):
        state.journal_dragging = False
        return False
    if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        dragging = state.journal_dragging
        state.journal_dragging = False
        return dragging
    if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
        return False
    if event.type == pygame.MOUSEMOTION and state.journal_dragging and not getattr(event, "buttons", (1, 0, 0))[0]:
        state.journal_dragging = False
        return True
    mouse = getattr(event, "pos", pygame.mouse.get_pos())
    position = window_to_game_position(screen, mouse)
    if position is None and state.journal_dragging:
        viewport, _ = game_viewport(screen.get_size())
        position = (0, (mouse[1] - viewport.y) * GAME_HEIGHT / viewport.height)
    if position is None:
        return False
    layout = get_act_three_hud_layout()
    track, thumb = get_act_three_journal_scrollbar_rectangles(
        layout, get_act_three_journal_scroll_ratio(game_state),
    )
    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button != 1 or not (thumb.collidepoint(position) or track.collidepoint(position)):
            return False
        state.journal_dragging = True
        if thumb.collidepoint(position):
            state.journal_drag_offset = position[1] - thumb.top
            return True
        state.journal_drag_offset = thumb.height / 2
    elif not state.journal_dragging:
        return False
    travel = max(0, track.height - thumb.height)
    state.journal_scroll_ratio = (
        max(0.0, min(1.0, (position[1] - state.journal_drag_offset - track.top) / travel))
        if travel else 1.0
    )
    return True


def handle_journal_key(event, game_state, can_open):
    from acts.act_three.input.character_panel import set_sidebar_tab

    opened = game_state.sidebar_tab == "journal"
    if event.key == pygame.K_j:
        if not getattr(event, "repeat", False) and (opened or can_open):
            set_sidebar_tab(game_state, "closed" if opened else "journal")
        return True
    if not opened or event.key == pygame.K_TAB:
        return False
    if getattr(event, "automatic_movement", False):
        return True
    if event.key == pygame.K_ESCAPE:
        set_sidebar_tab(game_state, "closed")
    elif event.key in (pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN):
        scroll_act_three_journal(game_state, -1 if event.key in (pygame.K_w, pygame.K_UP) else 1)
    return True
