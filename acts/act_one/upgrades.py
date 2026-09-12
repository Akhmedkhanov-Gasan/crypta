import pygame

from application.transitions import (
    finish_upgrade_descent,
)
from game.attributes import (
    MAX_CRITICAL_DAMAGE_MULTIPLIER,
    MAX_CRIT_CHANCE,
    MAX_DODGE_CHANCE,
    get_attribute_definition,
)
from game.combat_log import add_log_message
from game.progression import apply_attribute_upgrade
from game.attributes import (
    player_stat_changes_for_attribute_upgrade,
)


ACT_ONE_ATTRIBUTE_KEYS = {
    pygame.K_1: "valor",
    pygame.K_KP1: "valor",
    pygame.K_2: "instinct",
    pygame.K_KP2: "instinct",
    pygame.K_3: "fortitude",
    pygame.K_KP3: "fortitude",
}


def get_act_one_attribute_title(
    attribute: str,
) -> str:
    return get_attribute_definition(
        attribute
    ).title


def get_act_one_attribute_summary(
    attribute: str,
) -> str:
    return get_attribute_definition(
        attribute
    ).summary


def get_act_one_upgrade_preview_lines(
    player,
    attribute: str,
) -> tuple[str, ...]:
    rank = player.attribute_ranks[attribute]
    change = player_stat_changes_for_attribute_upgrade(
        attribute,
        rank,
    )
    lines = []

    if change.damage_min or change.damage_max:
        lines.append(
            (
                f"DAMAGE {player.damage_min}-"
                f"{player.damage_max}  ->  "
                f"{player.damage_min + change.damage_min}-"
                f"{player.damage_max + change.damage_max}"
            )
        )

    if change.max_health:
        lines.append(
            (
                f"HP {player.max_health}  ->  "
                f"{player.max_health + change.max_health}"
            )
        )

    if change.crit_chance:
        next_crit = min(
            MAX_CRIT_CHANCE,
            player.crit_chance + change.crit_chance,
        )
        lines.append(
            (
                f"CRIT {player.crit_chance:.0%}"
                f"  ->  {next_crit:.0%}"
            )
        )

    if change.dodge_chance:
        next_dodge = min(
            MAX_DODGE_CHANCE,
            player.dodge_chance + change.dodge_chance,
        )
        lines.append(
            (
                f"DODGE {player.dodge_chance:.0%}"
                f"  ->  {next_dodge:.0%}"
            )
        )

    if change.critical_damage_multiplier:
        next_critical_damage = min(
            MAX_CRITICAL_DAMAGE_MULTIPLIER,
            player.critical_damage_multiplier
            + change.critical_damage_multiplier,
        )
        lines.append(
            (
                "CRIT DAMAGE "
                f"x{player.critical_damage_multiplier:.2f}"
                f"  ->  x{next_critical_damage:.2f}"
            )
        )

    return tuple(lines)


def handle_act_one_upgrade_input(
    game_state,
    key: int,
    current_time: int,
) -> bool:
    if key in (
        pygame.K_RETURN,
        pygame.K_KP_ENTER,
    ):
        if game_state.act_one_upgrades_remaining > 0:
            return True

        finish_upgrade_descent(
            game_state,
            current_time,
        )
        return True

    attribute = ACT_ONE_ATTRIBUTE_KEYS.get(key)
    if attribute is None:
        return False

    attribute_title = get_act_one_attribute_title(
        attribute
    )

    if game_state.act_one_upgrades_remaining <= 0:
        game_state.upgrade_message = (
            "All blessings chosen. Press Enter."
        )
        return True

    if not apply_attribute_upgrade(
        game_state.player,
        attribute,
    ):
        game_state.upgrade_message = (
            f"{attribute_title} is capped."
        )
        return True

    game_state.act_one_upgrades_remaining -= 1
    game_state.upgrade_message = (
        f"{attribute_title} increased."
    )
    add_log_message(
        game_state.combat_log,
        game_state.upgrade_message,
        category="progress",
    )

    if game_state.act_one_upgrades_remaining <= 0:
        finish_upgrade_descent(
            game_state,
            current_time,
        )

    return True


def handle_act_one_upgrade_pointer(
    game_state,
    position: tuple[int, int],
    current_time: int,
) -> bool:
    from presentation.screens import (
        get_upgrade_card_rectangles,
    )

    rectangles = get_upgrade_card_rectangles(False)
    keys_by_attribute = {
        "valor": pygame.K_1,
        "instinct": pygame.K_2,
        "fortitude": pygame.K_3,
    }

    for attribute, rectangle in rectangles.items():
        if rectangle.collidepoint(position):
            return handle_act_one_upgrade_input(
                game_state,
                keys_by_attribute[attribute],
                current_time,
            )

    return False