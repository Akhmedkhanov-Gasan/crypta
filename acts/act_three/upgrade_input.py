import pygame

from application.transitions import (
    finish_upgrade_descent,
)
from game.attributes import (
    get_attribute_definition,
)
from game.combat_log import add_log_message
from game.progression import apply_attribute_upgrade


_ATTRIBUTE_BY_KEY = {
    pygame.K_1: "valor",
    pygame.K_KP1: "valor",
    pygame.K_2: "instinct",
    pygame.K_KP2: "instinct",
    pygame.K_3: "will",
    pygame.K_KP3: "will",
    pygame.K_4: "fortitude",
    pygame.K_KP4: "fortitude",
}


def _apply_act_three_upgrade(
    game_state,
    attribute: str,
) -> None:
    title = get_attribute_definition(
        attribute
    ).title

    if game_state.player.gold_count <= 0:
        game_state.upgrade_message = (
            "Not enough gold."
        )
        return

    if not apply_attribute_upgrade(
        game_state.player,
        attribute,
    ):
        game_state.upgrade_message = (
            f"{title} is capped."
        )
        return

    game_state.player.gold_count -= 1
    game_state.run_stats.gold_spent += 1
    game_state.upgrade_message = (
        f"{title} increased."
    )
    add_log_message(
        game_state.combat_log,
        game_state.upgrade_message,
        category="progress",
    )


def handle_act_three_upgrade_input(
    game_state,
    key: int,
    current_time: int,
) -> bool:
    attribute = _ATTRIBUTE_BY_KEY.get(key)

    if attribute is not None:
        _apply_act_three_upgrade(
            game_state,
            attribute,
        )
        return True

    if key in (
        pygame.K_RETURN,
        pygame.K_KP_ENTER,
    ):
        finish_upgrade_descent(
            game_state,
            current_time,
        )
        return True

    return False


def handle_act_three_upgrade_pointer(
    game_state,
    position: tuple[int, int],
) -> bool:
    from presentation.screens import (
        get_upgrade_card_rectangles,
    )

    rectangles = get_upgrade_card_rectangles(
        show_will=True,
    )

    for attribute, rectangle in rectangles.items():
        if rectangle.collidepoint(position):
            _apply_act_three_upgrade(
                game_state,
                attribute,
            )
            return True

    return False
