import pygame

from game.state import GameState

from acts.act_two.class_selection import apply_act_two_class_selection
from acts.act_two.presentation.awakening import get_awakening_hitboxes
from presentation.layout import CLASS_SELECTION_READY_MS


_CLASS_BY_KEY = {
    pygame.K_1: "warrior",
    pygame.K_KP1: "warrior",
    pygame.K_2: "rogue",
    pygame.K_KP2: "rogue",
    pygame.K_3: "mage",
    pygame.K_KP3: "mage",
}


def handle_class_selection_pointer(
    event,
    game_state: GameState,
    mouse_position,
    current_time,
) -> bool:
    if not (
        game_state.class_selection_open
        and event.type == pygame.MOUSEBUTTONDOWN
        and event.button == 1
    ):
        return False
    if (
        game_state.class_selection_choice is not None
        or current_time - game_state.class_transition_started_at
        < CLASS_SELECTION_READY_MS
        or mouse_position is None
    ):
        return True

    for class_name, rectangle in get_awakening_hitboxes().items():
        if rectangle.collidepoint(mouse_position):
            pygame.event.post(
                pygame.event.Event(
                    pygame.KEYDOWN,
                    key=next(
                        key
                        for key, mapped_class in _CLASS_BY_KEY.items()
                        if mapped_class == class_name
                    ),
                )
            )
            break
    return True


def handle_class_selection_key(
    event,
    game_state: GameState,
    transition_sounds,
    current_time,
) -> bool:
    if not game_state.class_selection_open:
        return False
    if (
        game_state.class_selection_choice is not None
        or current_time - game_state.class_transition_started_at
        < CLASS_SELECTION_READY_MS
    ):
        return True

    chosen_class = _CLASS_BY_KEY.get(event.key)
    if chosen_class is None:
        return True
    game_state.class_selection_preview_ranks = apply_act_two_class_selection(
        game_state.player,
        chosen_class,
    )
    game_state.class_selection_choice = chosen_class
    game_state.class_selection_choice_started_at = current_time
    game_state.player.act_two_facing_direction = (0, 1)
    transition_sounds.play("class_select")
    return True


__all__ = [
    "handle_class_selection_key",
    "handle_class_selection_pointer",
]
