import pygame
import pytest

from presentation.menu import (
    MenuState,
    get_menu_theme_rectangles,
    handle_menu_event,
)


def test_act_one_audio_sliders_have_quieter_effects_by_default():
    menu_state = MenuState()

    assert menu_state.music_volume == 0.55
    assert menu_state.effects_volume == 0.65


def test_keyboard_adjusts_selected_audio_slider():
    menu_state = MenuState(page="settings", selected_index=1)
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)

    action = handle_menu_event(
        event,
        menu_state,
        None,
        game_started=True,
        fullscreen=False,
    )

    assert action == "act_one_volume_changed"
    assert menu_state.music_volume == pytest.approx(0.60)


def test_audio_slider_values_are_clamped():
    menu_state = MenuState(
        page="settings",
        selected_index=2,
        effects_volume=1.0,
    )
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)

    handle_menu_event(
        event,
        menu_state,
        None,
        game_started=True,
        fullscreen=False,
    )

    assert menu_state.effects_volume == 1.0


def test_unlocked_menu_theme_can_be_selected_with_mouse():
    menu_state = MenuState()
    theme_three = get_menu_theme_rectangles()[2]
    event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        button=1,
    )

    action = handle_menu_event(
        event,
        menu_state,
        theme_three.center,
        game_started=False,
        fullscreen=False,
        highest_unlocked_theme=3,
    )

    assert action == "menu_theme_changed"
    assert menu_state.menu_theme == 3


def test_locked_menu_theme_cannot_be_selected():
    menu_state = MenuState()
    theme_two = get_menu_theme_rectangles()[1]
    event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        button=1,
    )

    action = handle_menu_event(
        event,
        menu_state,
        theme_two.center,
        game_started=False,
        fullscreen=False,
        highest_unlocked_theme=1,
    )

    assert action is None
    assert menu_state.menu_theme == 1
