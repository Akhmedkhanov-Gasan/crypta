import pygame

from game.combat_log import add_log_message
from game.progression import upgrade_attribute
from acts.act_three.altar import (
    player_is_next_to_upgrade_altar,
)
from acts.act_three.input.cursors import (
    set_archer_attack_cursor,
    set_archer_barrage_zone_cursor,
    set_archer_empowered_cursor,
    set_archer_leap_cursor,
    set_assassin_target_cursor,
    set_berserker_crushing_leap_cursor,
    set_paladin_shield_charge_cursor,
    set_summoner_staff_cursor,
    set_warlock_staff_cursor,
)
from acts.act_three.abilities.archer import (
    is_valid_archer_barrage_zone_anchor,
    is_valid_archer_empowered_shot_target,
    is_valid_archer_leap_target,
    place_archer_barrage_zone,
    update_archer_barrage_zone_preview,
)
from acts.act_three.abilities.assassin import (
    begin_assassin_ultimate,
    is_valid_assassin_teleport_target,
    select_assassin_ultimate_target,
)
from acts.act_three.abilities.berserker import (
    is_valid_berserker_crushing_leap_target,
    update_berserker_crushing_leap_preview,
)
from acts.act_three.abilities.paladin import (
    is_valid_paladin_shield_charge_target,
    update_paladin_shield_charge_preview,
)
from acts.act_three.abilities.warlock import (
    is_valid_warlock_curse_target,
    is_valid_warlock_soul_exchange_target,
)
from acts.act_three.combat import (
    is_valid_archer_attack_target,
    is_valid_summoner_attack_target,
    is_valid_warlock_attack_target,
)
from acts.act_three.presentation import (
    get_act_three_cell_from_position,
    get_act_three_bottom_hud_rectangles,
    get_act_three_panel_close_rectangle,
    get_act_three_popup_rectangle,
    get_act_three_sidebar_tab_rectangles,
)
from acts.act_three.presentation.altar_menu import (
    ALTAR_MENU_RECT,
    get_upgrade_altar_menu_control_at,
)
from acts.act_three.presentation.hit_testing import (
    get_upgrade_altar_screen_rect,
)
from acts.act_three.runtime import advance_act_three_transition
from levels import FLOOR_CONFIGS
from logic import get_enemy_occupied_positions
from presentation.screens import (
    get_act_three_debug_class_rectangles,
    get_subclass_selection_rectangles,
)
from settings import (
    ARCHER_LEAP_DURATION_MS,
    BERSERKER_CRUSHING_LEAP_IMPACT_MS,
    BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
    PALADIN_SHIELD_CHARGE_TRAVEL_MS,
    WARLOCK_SOUL_EXCHANGE_TRAVEL_MS,
)
def handle_act_three_pointer_event(
    event,
    game_state,
    screen,
    window_to_game_position,
):
    if (
        game_state.upgrade_altar_menu_open
        and event.type
        in (
            pygame.MOUSEMOTION,
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEWHEEL,
        )
    ):
        mouse_position = getattr(
            event,
            "pos",
            pygame.mouse.get_pos(),
        )
        game_mouse_position = window_to_game_position(
            screen,
            mouse_position,
        )
        control = (
            get_upgrade_altar_menu_control_at(
                game_mouse_position
            )
            if game_mouse_position is not None
            else None
        )
        game_state.upgrade_altar_menu_hovered_control = control

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            if control == "close" or (
                game_mouse_position is not None
                and not ALTAR_MENU_RECT.collidepoint(
                    game_mouse_position
                )
            ):
                game_state.upgrade_altar_menu_open = False
                game_state.upgrade_altar_menu_hovered_control = None
            elif control is not None and control.startswith("tab:"):
                game_state.upgrade_altar_menu_tab = control.split(
                    ":",
                    1,
                )[1]
            elif (
                control is not None
                and control.startswith("upgrade:")
                and game_state.upgrade_altar_menu_tab == "attributes"
            ):
                attribute = control.split(":", 1)[1]
                if upgrade_attribute(game_state.player, attribute):
                    add_log_message(
                        game_state.combat_log,
                        f"{attribute.title()} increased at the altar.",
                    )
        return True

    if (
        event.type == pygame.MOUSEMOTION
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and not game_state.act_three_transition_open
        and not game_state.subclass_selection_open
    ):
        game_mouse_position = window_to_game_position(
            screen,
            event.pos,
        )
        altar_rectangle = get_upgrade_altar_screen_rect(
            game_state
        )
        game_state.upgrade_altar_hovered = (
            game_mouse_position is not None
            and altar_rectangle is not None
            and altar_rectangle.collidepoint(game_mouse_position)
            and player_is_next_to_upgrade_altar(game_state)
        )
        if game_state.upgrade_altar_hovered:
            return True

    if (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button == 1
        and game_state.act_three_debug_class_selection_open
    ):
        game_mouse_position = window_to_game_position(
            screen,
            event.pos,
        )
    
        if game_mouse_position is None:
            return True
    
        class_keys = {
            "warrior": pygame.K_1,
            "rogue": pygame.K_2,
            "mage": pygame.K_3,
        }
    
        for (
            class_name,
            class_rectangle,
        ) in (
            get_act_three_debug_class_rectangles().items()
        ):
            if class_rectangle.collidepoint(
                game_mouse_position
            ):
                pygame.event.post(
                    pygame.event.Event(
                        pygame.KEYDOWN,
                        key=class_keys[class_name],
                    )
                )
                break
    elif (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button == 1
        and game_state.act_three_transition_open
    ):
        advance_act_three_transition(
            game_state,
            pygame.time.get_ticks(),
        )
    elif (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button == 1
        and game_state.subclass_selection_open
    ):
        game_mouse_position = window_to_game_position(
            screen,
            event.pos,
        )
    
        if (
            game_mouse_position is not None
            and game_state.player.subclass is None
        ):
            subclass_keys = {
                "berserker": pygame.K_1,
                "paladin": pygame.K_2,
                "assassin": pygame.K_1,
                "archer": pygame.K_2,
                "warlock": pygame.K_1,
                "summoner": pygame.K_2,
            }
    
            for (
                subclass,
                subclass_rectangle,
            ) in get_subclass_selection_rectangles(
                game_state.player.player_class
            ).items():
                if subclass_rectangle.collidepoint(
                    game_mouse_position
                ):
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=subclass_keys[subclass],
                        )
                    )
                    break
    elif (
        event.type == pygame.MOUSEMOTION
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and not game_state.act_three_transition_open
        and not game_state.subclass_selection_open
        and game_state.player.subclass in (
            "archer",
            "berserker",
            "paladin",
            "warlock",
            "summoner",
        )
    ):
        if (
            game_state.player.teleport_aiming
            or game_state.player.ultimate_aiming
            or game_state.player.ultimate_animation_active
        ):
            return True
        game_mouse_position = window_to_game_position(
            screen,
            event.pos,
        )
        target_cell = (
            get_act_three_cell_from_position(
                game_state,
                game_mouse_position,
            )
            if game_mouse_position is not None
            else None
        )
        if game_state.player.warlock_curse_aiming:
            set_warlock_staff_cursor(
                target_cell is not None
                and is_valid_warlock_curse_target(
                    game_state,
                    target_cell,
                )
            )
        elif game_state.player.warlock_soul_exchange_aiming:
            set_warlock_staff_cursor(
                target_cell is not None
                and is_valid_warlock_soul_exchange_target(
                    game_state,
                    target_cell,
                )
            )
        elif game_state.player.paladin_shield_charge_aiming:
            preview_is_valid = (
                target_cell is not None
                and is_valid_paladin_shield_charge_target(
                    game_state,
                    target_cell,
                )
            )
            update_paladin_shield_charge_preview(
                game_state,
                target_cell if preview_is_valid else None,
            )
            set_paladin_shield_charge_cursor(
                preview_is_valid
            )
        elif game_state.player.berserker_crushing_leap_aiming:
            preview_is_valid = (
                target_cell is not None
                and is_valid_berserker_crushing_leap_target(
                    game_state,
                    target_cell,
                )
            )
            update_berserker_crushing_leap_preview(
                game_state,
                target_cell if preview_is_valid else None,
            )
            set_berserker_crushing_leap_cursor(
                preview_is_valid
            )
        elif game_state.player.archer_barrage_zone_aiming:
            preview_is_valid = (
                target_cell is not None
                and is_valid_archer_barrage_zone_anchor(
                    game_state,
                    target_cell,
                )
            )
            update_archer_barrage_zone_preview(
                game_state,
                target_cell if preview_is_valid else None,
            )
            set_archer_barrage_zone_cursor(
                preview_is_valid
            )
        elif game_state.player.archer_leap_aiming:
            set_archer_leap_cursor(
                target_cell is not None
                and is_valid_archer_leap_target(
                    game_state,
                    *target_cell,
                )
            )
        elif game_state.player.archer_empowered_shot_aiming:
            set_archer_empowered_cursor(True)
        elif game_state.player.subclass == "archer":
            set_archer_attack_cursor(
                target_cell is not None
                and is_valid_archer_attack_target(
                    game_state,
                    target_cell,
                )
            )
        elif game_state.player.subclass == "warlock":
            set_warlock_staff_cursor(
                target_cell is not None
                and is_valid_warlock_attack_target(
                    game_state,
                    target_cell,
                )
            )
        elif game_state.player.subclass == "summoner":
            set_summoner_staff_cursor(
                target_cell is not None
                and is_valid_summoner_attack_target(
                    game_state,
                    target_cell,
                )
            )
    elif (
        event.type == pygame.MOUSEWHEEL
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and not game_state.act_three_transition_open
        and not game_state.subclass_selection_open
    ):
        mouse_position = getattr(event, "pos", pygame.mouse.get_pos())
        game_mouse_position = window_to_game_position(
            screen,
            mouse_position,
        )
        if (
            game_mouse_position is not None
            and get_act_three_log_panel_rect().collidepoint(
                game_mouse_position
            )
        ):
            maximum_scroll = max(
                0,
                len(game_state.combat_log) - 4,
            )
            game_state.log_scroll_offset = max(
                0,
                min(
                    maximum_scroll,
                    game_state.log_scroll_offset + event.y,
                ),
            )
    elif (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button == 1
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and not game_state.act_three_transition_open
        and not game_state.subclass_selection_open
    ):
        game_mouse_position = window_to_game_position(
            screen,
            event.pos,
        )
        altar_rectangle = get_upgrade_altar_screen_rect(
            game_state
        )
        if (
            game_mouse_position is not None
            and altar_rectangle is not None
            and altar_rectangle.collidepoint(game_mouse_position)
            and player_is_next_to_upgrade_altar(game_state)
        ):
            game_state.upgrade_altar_menu_open = True
            game_state.upgrade_altar_menu_tab = "attributes"
            game_state.upgrade_altar_hovered = False
            game_state.upgrade_altar_menu_hovered_control = None
            return True

        if (
            game_state.player.archer_leap_origin is not None
            and game_state.player.archer_leap_started_at > 0
            and pygame.time.get_ticks()
            - game_state.player.archer_leap_started_at
            < ARCHER_LEAP_DURATION_MS
        ):
            return True
        if (
            game_state.player.berserker_crushing_leap_origin
            is not None
            and game_state.player.berserker_crushing_leap_started_at
            > 0
            and pygame.time.get_ticks()
            - game_state.player.berserker_crushing_leap_started_at
            < (
                BERSERKER_CRUSHING_LEAP_TRAVEL_MS
                + BERSERKER_CRUSHING_LEAP_IMPACT_MS
            )
        ):
            return True
        if (
            game_state.player.paladin_shield_charge_origin
            is not None
            and game_state.player.paladin_shield_charge_started_at
            > 0
            and pygame.time.get_ticks()
            - game_state.player.paladin_shield_charge_started_at
            < PALADIN_SHIELD_CHARGE_TRAVEL_MS
        ):
            return True
        if (
            game_state.player.warlock_soul_exchange_player_origin
            is not None
            and game_state.player.warlock_soul_exchange_started_at
            > 0
            and pygame.time.get_ticks()
            - game_state.player.warlock_soul_exchange_started_at
            < WARLOCK_SOUL_EXCHANGE_TRAVEL_MS
        ):
            return True
        game_mouse_position = window_to_game_position(
            screen,
            event.pos,
        )
        if game_mouse_position is not None:
            if any(
                rectangle.collidepoint(game_mouse_position)
                for rectangle in get_act_three_bottom_hud_rectangles()
            ):
                return True
            for tab_name, tab_rectangle in (
                get_act_three_sidebar_tab_rectangles().items()
            ):
                if not tab_rectangle.collidepoint(game_mouse_position):
                    continue
                if tab_name == "settings":
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=pygame.K_ESCAPE,
                        )
                    )
                elif tab_name in ("inventory", "stats"):
                    game_state.sidebar_tab = (
                        "closed"
                        if game_state.sidebar_tab == tab_name
                        else tab_name
                    )
                return True
            if game_state.sidebar_tab in ("inventory", "stats"):
                if get_act_three_panel_close_rectangle().collidepoint(
                    game_mouse_position
                ):
                    game_state.sidebar_tab = "closed"
                    return True
                if get_act_three_popup_rectangle().collidepoint(
                    game_mouse_position
                ):
                    return True
            if game_state.player.ultimate_animation_active:
                return True
            elif game_state.player.warlock_curse_aiming:
                target_cell = get_act_three_cell_from_position(
                    game_state,
                    game_mouse_position,
                )
                if (
                    target_cell is not None
                    and is_valid_warlock_curse_target(
                        game_state,
                        target_cell,
                    )
                ):
                    game_state.player.warlock_curse_target = (
                        target_cell
                    )
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=pygame.K_RETURN,
                        )
                    )
            elif game_state.player.warlock_soul_exchange_aiming:
                target_cell = get_act_three_cell_from_position(
                    game_state,
                    game_mouse_position,
                )
                if (
                    target_cell is not None
                    and is_valid_warlock_soul_exchange_target(
                        game_state,
                        target_cell,
                    )
                ):
                    game_state.player.warlock_soul_exchange_target = (
                        target_cell
                    )
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=pygame.K_RETURN,
                        )
                    )
            elif game_state.player.teleport_aiming:
                target_cell = get_act_three_cell_from_position(
                    game_state,
                    game_mouse_position,
                )
                if target_cell is not None and is_valid_assassin_teleport_target(
                    game_state,
                    *target_cell,
                ):
                    game_state.player.teleport_target = target_cell
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=pygame.K_RETURN,
                        )
                    )
            elif game_state.player.paladin_shield_charge_aiming:
                target_cell = get_act_three_cell_from_position(
                    game_state,
                    game_mouse_position,
                )
                if update_paladin_shield_charge_preview(
                    game_state,
                    target_cell,
                ):
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=pygame.K_RETURN,
                        )
                    )
            elif game_state.player.berserker_crushing_leap_aiming:
                target_cell = get_act_three_cell_from_position(
                    game_state,
                    game_mouse_position,
                )
                if update_berserker_crushing_leap_preview(
                    game_state,
                    target_cell,
                ):
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=pygame.K_RETURN,
                        )
                    )
            elif game_state.player.archer_barrage_zone_aiming:
                target_cell = get_act_three_cell_from_position(
                    game_state,
                    game_mouse_position,
                )
                if update_archer_barrage_zone_preview(
                    game_state,
                    target_cell,
                ):
                    place_archer_barrage_zone(game_state)
                    set_archer_barrage_zone_cursor()
            elif game_state.player.archer_leap_aiming:
                target_cell = get_act_three_cell_from_position(
                    game_state,
                    game_mouse_position,
                )
                if (
                    target_cell is not None
                    and is_valid_archer_leap_target(
                        game_state,
                        *target_cell,
                    )
                ):
                    game_state.player.archer_leap_target = (
                        target_cell
                    )
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=pygame.K_RETURN,
                        )
                    )
            elif game_state.player.ultimate_aiming:
                target_cell = get_act_three_cell_from_position(
                    game_state,
                    game_mouse_position,
                )
                if target_cell is not None:
                    selected_enemy = next(
                        (
                            enemy
                            for enemy in game_state.floor.enemies
                            if enemy.health > 0
                            and target_cell
                            in get_enemy_occupied_positions(enemy)
                        ),
                        None,
                    )
                    if selected_enemy is not None:
                        select_assassin_ultimate_target(
                            game_state,
                            selected_enemy.name,
                        )
                        if len(game_state.player.ultimate_targets) >= 5:
                            begin_assassin_ultimate(
                                game_state,
                                pygame.time.get_ticks(),
                            )
                            set_assassin_target_cursor()
            elif game_state.player.archer_empowered_shot_aiming:
                target_cell = get_act_three_cell_from_position(
                    game_state,
                    game_mouse_position,
                )
                if (
                    target_cell is not None
                    and is_valid_archer_empowered_shot_target(
                        game_state,
                        target_cell,
                    )
                ):
                    game_state.player.archer_empowered_shot_target = (
                        target_cell
                    )
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=pygame.K_RETURN,
                        )
                    )
            else:
                archer_target_cell = (
                    get_act_three_cell_from_position(
                        game_state,
                        game_mouse_position,
                    )
                    if game_state.player.subclass == "archer"
                    else None
                )
                if (
                    archer_target_cell is not None
                    and is_valid_archer_attack_target(
                        game_state,
                        archer_target_cell,
                    )
                ):
                    game_state.player.archer_attack_target = (
                        archer_target_cell
                    )
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=pygame.K_RETURN,
                        )
                    )
                    return True
    
                warlock_target_cell = (
                    get_act_three_cell_from_position(
                        game_state,
                        game_mouse_position,
                    )
                    if game_state.player.subclass == "warlock"
                    else None
                )
                if (
                    warlock_target_cell is not None
                    and is_valid_warlock_attack_target(
                        game_state,
                        warlock_target_cell,
                    )
                ):
                    game_state.player.warlock_attack_target = (
                        warlock_target_cell
                    )
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=pygame.K_RETURN,
                        )
                    )
                    return True
    
                summoner_target_cell = (
                    get_act_three_cell_from_position(
                        game_state,
                        game_mouse_position,
                    )
                    if game_state.player.subclass == "summoner"
                    else None
                )
                if (
                    summoner_target_cell is not None
                    and is_valid_summoner_attack_target(
                        game_state,
                        summoner_target_cell,
                    )
                ):
                    game_state.player.summoner_attack_target = (
                        summoner_target_cell
                    )
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=pygame.K_RETURN,
                        )
                    )
                    return True
    
    else:
        return False

    return True
