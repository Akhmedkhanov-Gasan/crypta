import pygame

from application.transitions import (
    finish_upgrade_descent,
)
from acts.act_two.progression import (
    get_act_two_upgrade_order,
    upgrade_act_two_attribute,
)
from game.combat_log import add_log_message


_UPGRADE_INDEX_BY_KEY = {
    pygame.K_1: 0,
    pygame.K_KP1: 0,
    pygame.K_2: 1,
    pygame.K_KP2: 1,
    pygame.K_3: 2,
    pygame.K_KP3: 2,
    pygame.K_4: 3,
    pygame.K_KP4: 3,
}


def act_two_upgrade_screen_is_available(
    game_state,
) -> bool:
    return (
        game_state.player.player_class
        in ("warrior", "rogue", "mage")
        and game_state.player.subclass is None
    )


def _apply_act_two_upgrade(
    game_state,
    upgrade: str,
) -> None:
    game_state.upgrade_message = (
        upgrade_act_two_attribute(
            game_state.player,
            upgrade,
        )
    )
    add_log_message(
        game_state.combat_log,
        game_state.upgrade_message,
        category="progress",
    )


def handle_act_two_upgrade_input(
    game_state,
    key: int,
    current_time: int,
) -> bool:
    if not act_two_upgrade_screen_is_available(
        game_state
    ):
        return False

    upgrade_order = get_act_two_upgrade_order(
        game_state.player.player_class
    )
    upgrade_index = _UPGRADE_INDEX_BY_KEY.get(key)

    if (
        upgrade_index is not None
        and upgrade_index < len(upgrade_order)
    ):
        _apply_act_two_upgrade(
            game_state,
            upgrade_order[upgrade_index],
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


def handle_act_two_upgrade_pointer(
    game_state,
    position: tuple[int, int],
) -> bool:
    from acts.act_two.presentation.upgrade import (
        get_act_two_upgrade_card_rectangles,
    )

    if not act_two_upgrade_screen_is_available(
        game_state
    ):
        return False

    rectangles = get_act_two_upgrade_card_rectangles(
        game_state.player.player_class
    )

    for upgrade, rectangle in rectangles.items():
        if rectangle.collidepoint(position):
            _apply_act_two_upgrade(
                game_state,
                upgrade,
            )
            return True

    return False
