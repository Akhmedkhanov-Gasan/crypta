import pygame

from acts.mage_targeting import mage_aiming
from acts.act_two.presentation.cartography import full_map_close_rectangle


def map_input_available(game_state):
    return (
        not game_state.act_two_stats_open
        and not game_state.act_two_journal_open
        and not game_state.dialogue.active
        and not mage_aiming(game_state.player)
    )


def handle_map_event(event, game_state, available, mouse_position, surface_size, hud_layout=None):
    if game_state.act_two_map_open:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                return False
            if event.key in (pygame.K_m, pygame.K_ESCAPE) and not getattr(event, "repeat", False):
                game_state.act_two_map_open = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if mouse_position is not None and full_map_close_rectangle(surface_size, hud_layout).collidepoint(mouse_position):
                game_state.act_two_map_open = False
        return event.type in (
            pygame.KEYDOWN,
            pygame.KEYUP,
            pygame.TEXTINPUT,
            pygame.MOUSEMOTION,
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEWHEEL,
        )
    if available and event.type == pygame.KEYDOWN and event.key == pygame.K_m:
        if not getattr(event, "repeat", False) and not getattr(event, "automatic_movement", False):
            game_state.act_two_map_open = True
        return True
    return False
