import pygame

from acts.act_one.settings import (
    FLOOR_INTRO_SUBTITLES,
    PLAYER_STARTING_STATS,
)
from acts.act_two.settings import CLASS_BASE_STATS
from acts.act_three.input import (
    handle_act_three_key_event,
    handle_act_three_pointer_event,
    set_archer_attack_cursor,
    set_archer_empowered_cursor,
    set_archer_leap_cursor,
    set_assassin_target_cursor,
    set_berserker_crushing_leap_cursor,
    set_paladin_shield_charge_cursor,
    set_summoner_staff_cursor,
    set_warlock_staff_cursor,
)
from acts.act_three.runtime import (
    advance_act_three_transition,
    choose_subclass,
    clear_archer_barrage_zone,
    clear_berserker_crushing_leap,
    create_act_three_debug_transition,
)
from acts.act_three.presentation.combat_effects import (
    record_enemy_death_feedback,
    record_enemy_hit_feedback,
    record_familiar_hit_feedback,
    record_player_death_feedback,
    record_player_hit_feedback,
)
from acts.turns import resolve_enemy_turn
from bosses.oracle import resolve_oracle_hit_reaction
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.factories import create_floor_state, create_game_state
from game.progress_store import load_progress, record_act_reached
from game.progression import apply_attribute_upgrade
from acts.player_stats import apply_player_stat_transition
from levels import FLOOR_CONFIGS
from logic import get_enemy_occupied_positions
from rendering import (
    CLASS_SELECTION_READY_MS,
    FLOOR_TRANSITION_CLOSE_END_MS,
    FLOOR_TRANSITION_END_MS,
    draw_act_three_awakening,
    draw_act_three_debug_class_selection,
    draw_act_three_gameplay,
    draw_attack_markers,
    draw_act_one_boss_effects,
    draw_act_one_atmosphere,
    draw_act_two_atmosphere,
    draw_act_one_player_attack_effect,
    draw_act_two_player_attack_effect,
    draw_act_two_player_feedback_overlay,
    draw_act_one_pickup_effect,
    draw_boss_door,
    draw_chest,
    draw_class_selection_screen,
    draw_floor_transition,
    draw_coin,
    draw_dungeon,
    draw_enemy,
    draw_key,
    draw_map_frame,
    draw_oracle_emitters,
    draw_oracle_projectiles,
    draw_player,
    draw_player_attack_markers,
    draw_potion,
    draw_sidebar,
    draw_stairs,
    draw_status,
    draw_subclass_selection_screen,
    draw_upgrade_screen,
    get_upgrade_card_rectangles,
    get_class_selection_rectangles,
    load_act_one_fonts,
    load_act_three_fonts,
    load_act_three_gameplay_assets,
    load_act_three_transition_assets,
    load_act_two_fonts,
    load_act_two_sprites,
    load_menu_assets,
)
from presentation.layout import (
    ACT_THREE_AWAKENING_END_MS,
    ACT_THREE_MUSIC_PATH,
)
from presentation.menu import (
    MenuState,
    draw_menu,
    handle_menu_event,
)
from settings import (
    BACKGROUND_COLOR,
    ASSASSIN_ULTIMATE_OUTRO_MS,
    ASSASSIN_ULTIMATE_PRELUDE_MS,
    ASSASSIN_ULTIMATE_STEP_MS,
    CRIT_UPGRADE_AMOUNT,
    DAMAGE_UPGRADE_AMOUNT,
    DODGE_UPGRADE_AMOUNT,
    FPS,
    GAME_HEIGHT,
    GAME_WIDTH,
    INITIAL_WINDOW_SCALE,
    HEALTH_UPGRADE_AMOUNT,
    MAX_CRIT_CHANCE,
    MAX_DODGE_CHANCE,
)
from systems.player_actions import (
    open_chest,
    try_move_player,
    try_use_potion,
)
from systems.player_combat import (
    perform_archer_attack,
    perform_basic_attack,
    perform_summoner_attack,
    perform_warlock_attack,
)
from systems.player_abilities import (
    AbilityRequestResult,
    advance_berserker_last_rage,
    advance_paladin_holy_shield,
    advance_warlock_curses,
    advance_warlock_demon_form,
    cancel_ability_aiming,
    cast_directional_ability,
    resolve_assassin_ultimate,
    request_class_ability,
    perform_archer_empowered_shot,
    perform_berserker_crushing_leap,
    perform_paladin_shield_charge,
    perform_warlock_curse,
    perform_warlock_soul_exchange,
)
FIRST_ACT_FINAL_FLOOR = 2
FIRST_ACT_THREE_FLOOR = next(
    index
    for index, floor_config in enumerate(FLOOR_CONFIGS)
    if floor_config["act"] == 3
)
ACT_THREE_MUSIC_ENABLED = False


def get_initial_window_size():
    display_info = pygame.display.Info()
    preferred_width = int(GAME_WIDTH * INITIAL_WINDOW_SCALE)
    preferred_height = int(GAME_HEIGHT * INITIAL_WINDOW_SCALE)
    maximum_width = int(display_info.current_w * 0.9)
    maximum_height = int(display_info.current_h * 0.85)
    scale = min(
        preferred_width / GAME_WIDTH,
        preferred_height / GAME_HEIGHT,
        maximum_width / GAME_WIDTH,
        maximum_height / GAME_HEIGHT,
    )

    return (
        int(GAME_WIDTH * scale),
        int(GAME_HEIGHT * scale),
    )


def present_game(window, game_surface):
    window_width, window_height = window.get_size()
    scale = min(
        window_width / GAME_WIDTH,
        window_height / GAME_HEIGHT,
    )
    scaled_width = max(1, int(GAME_WIDTH * scale))
    scaled_height = max(1, int(GAME_HEIGHT * scale))
    scale_is_integer = abs(scale - round(scale)) < 0.001
    transform = (
        pygame.transform.scale
        if scale_is_integer
        else pygame.transform.smoothscale
    )
    scaled_surface = transform(game_surface, (scaled_width, scaled_height))
    offset_x = (window_width - scaled_width) // 2
    offset_y = (window_height - scaled_height) // 2

    window.fill(BACKGROUND_COLOR)
    window.blit(scaled_surface, (offset_x, offset_y))
    pygame.display.flip()


def window_to_game_position(window, window_position):
    window_width, window_height = window.get_size()
    scale = min(
        window_width / GAME_WIDTH,
        window_height / GAME_HEIGHT,
    )
    scaled_width = int(GAME_WIDTH * scale)
    scaled_height = int(GAME_HEIGHT * scale)
    offset_x = (window_width - scaled_width) // 2
    offset_y = (window_height - scaled_height) // 2
    mouse_x, mouse_y = window_position

    if not (
        offset_x <= mouse_x < offset_x + scaled_width
        and offset_y <= mouse_y < offset_y + scaled_height
    ):
        return None

    return (
        int((mouse_x - offset_x) / scale),
        int((mouse_y - offset_y) / scale),
    )


def _finish_upgrade_descent(game_state, started_at):
    if game_state.floor_transition_started_at >= 0:
        return

    game_state.floor_transition_started_at = started_at
    game_state.floor_transition_target_index = (
        game_state.floor_index + 1
    )
    game_state.floor_transition_swapped = False
    game_state.upgrade_screen_open = False
    game_state.upgrade_message = ""
    game_state.player_attack_targets = []


def _advance_floor_transition(game_state, current_time):
    started_at = game_state.floor_transition_started_at
    target_index = game_state.floor_transition_target_index
    if started_at < 0 or target_index is None:
        return

    elapsed = current_time - started_at
    if (
        not game_state.floor_transition_swapped
        and elapsed >= FLOOR_TRANSITION_CLOSE_END_MS
    ):
        game_state.floor_index = target_index
        game_state.floor = create_floor_state(target_index)
        game_state.floor_transition_swapped = True
        game_state.player.key_count = 0
        game_state.player_attack_targets = []
        clear_archer_barrage_zone(game_state)
        clear_berserker_crushing_leap(game_state)
        add_log_message(
            game_state.combat_log,
            f"Hero descends to floor {target_index + 1}.",
        )

    if elapsed >= FLOOR_TRANSITION_END_MS:
        game_state.floor_transition_started_at = -1
        game_state.floor_transition_target_index = None
        game_state.floor_transition_swapped = False


def _roman_floor_number(number):
    return {
        1: "I",
        2: "II",
        3: "III",
    }.get(number, str(number))


def main():
    pygame.init()

    windowed_size = get_initial_window_size()
    screen = pygame.display.set_mode(
        windowed_size,
        pygame.RESIZABLE,
    )
    game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    pygame.display.set_caption("Crypta")
    clock = pygame.time.Clock()
    act_one_fonts = load_act_one_fonts()
    title_font = act_one_fonts["title"]
    font = act_one_fonts["status"]
    log_font = act_one_fonts["text"]
    act_two_fonts = load_act_two_fonts()
    act_two_sprites = load_act_two_sprites()
    act_three_fonts = load_act_three_fonts()
    act_three_gameplay_assets = (
        load_act_three_gameplay_assets()
    )
    act_three_transition_assets = (
        load_act_three_transition_assets()
    )
    menu_assets = load_menu_assets()

    game_state = create_game_state()
    menu_progress = load_progress()
    progress_tracking_enabled = True
    menu_state = MenuState()
    menu_open = True
    game_started = False
    menu_started_at = pygame.time.get_ticks()
    act_three_music_attempted = False
    fullscreen = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                windowed_size = (
                    max(640, event.w),
                    max(360, event.h),
                )
                screen = pygame.display.set_mode(
                    windowed_size,
                    pygame.RESIZABLE,
                )
            elif menu_open:
                event_position = getattr(
                    event,
                    "pos",
                    pygame.mouse.get_pos(),
                )
                menu_action = handle_menu_event(
                    event,
                    menu_state,
                    window_to_game_position(screen, event_position),
                    game_started,
                    fullscreen,
                )

                if menu_action == "resume":
                    menu_open = False
                    game_started = True
                elif menu_action == "abandon_run":
                    if (
                        act_three_music_attempted
                        and pygame.mixer.get_init() is not None
                    ):
                        pygame.mixer.music.stop()
                    act_three_music_attempted = False
                    game_state = create_game_state()
                    progress_tracking_enabled = True
                    game_started = False
                    menu_state.page = "main"
                    menu_state.selected_index = 0
                    menu_started_at = pygame.time.get_ticks()
                    pygame.mouse.set_cursor(
                        pygame.SYSTEM_CURSOR_ARROW
                    )
                elif menu_action == "quit":
                    running = False
                elif menu_action == "toggle_fullscreen":
                    if fullscreen:
                        screen = pygame.display.set_mode(
                            windowed_size,
                            pygame.RESIZABLE,
                        )
                    else:
                        windowed_size = screen.get_size()
                        screen = pygame.display.set_mode(
                            (0, 0),
                            pygame.FULLSCREEN,
                        )
                    fullscreen = not fullscreen
                continue
            elif game_state.floor_transition_started_at >= 0:
                continue
            elif handle_act_three_pointer_event(
                event,
                game_state,
                screen,
                window_to_game_position,
            ):
                continue
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and game_state.upgrade_screen_open
            ):
                game_mouse_position = window_to_game_position(
                    screen,
                    event.pos,
                )
                if game_mouse_position is None:
                    continue

                upgrade_keys = {
                    "vitality": pygame.K_1,
                    "power": pygame.K_2,
                    "precision": pygame.K_3,
                    "evasion": pygame.K_4,
                }
                for upgrade_name, rectangle in (
                    get_upgrade_card_rectangles().items()
                ):
                    if rectangle.collidepoint(game_mouse_position):
                        pygame.event.post(
                            pygame.event.Event(
                                pygame.KEYDOWN,
                                key=upgrade_keys[upgrade_name],
                            )
                        )
                        break
                continue
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and game_state.class_selection_open
            ):
                current_time = pygame.time.get_ticks()
                transition_elapsed = (
                    current_time - game_state.class_transition_started_at
                )

                if transition_elapsed < CLASS_SELECTION_READY_MS:
                    game_state.class_transition_started_at = (
                        current_time
                        - CLASS_SELECTION_READY_MS
                        - 500
                    )
                    continue

                game_mouse_position = window_to_game_position(
                    screen,
                    event.pos,
                )

                if game_mouse_position is None:
                    continue

                class_keys = {
                    "warrior": pygame.K_1,
                    "rogue": pygame.K_2,
                    "mage": pygame.K_3,
                }

                for (
                    class_name,
                    class_rectangle,
                ) in get_class_selection_rectangles().items():
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
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    if fullscreen:
                        screen = pygame.display.set_mode(
                            windowed_size,
                            pygame.RESIZABLE,
                        )
                    else:
                        windowed_size = screen.get_size()
                        screen = pygame.display.set_mode(
                            (0, 0),
                            pygame.FULLSCREEN,
                        )

                    fullscreen = not fullscreen
                    continue

                if event.key == pygame.K_F2:
                    if (
                        act_three_music_attempted
                        and pygame.mixer.get_init() is not None
                    ):
                        pygame.mixer.music.stop()
                    act_three_music_attempted = False
                    progress_tracking_enabled = False
                    game_state = create_game_state(
                        floor_index=FIRST_ACT_FINAL_FLOOR,
                        opening_message="Debug jump: choose an Act II class.",
                    )
                    game_state.class_selection_open = True
                    game_state.class_transition_started_at = (
                        pygame.time.get_ticks()
                        - CLASS_SELECTION_READY_MS
                    )
                    continue

                if handle_act_three_key_event(
                    event,
                    game_state,
                ):
                    continue
                if event.key == pygame.K_F3:
                    if (
                        act_three_music_attempted
                        and pygame.mixer.get_init() is not None
                    ):
                        pygame.mixer.music.stop()
                    act_three_music_attempted = False
                    progress_tracking_enabled = False
                    game_state = create_game_state(
                        floor_index=FIRST_ACT_THREE_FLOOR,
                        opening_message=(
                            "Debug: choose an Act III class."
                        )
                    )
                    game_state.act_three_test_mode = True
                    game_state.act_three_debug_class_selection_open = (
                        True
                    )
                    continue

                if game_state.act_three_debug_class_selection_open:
                    class_by_key = {
                        pygame.K_1: "warrior",
                        pygame.K_KP1: "warrior",
                        pygame.K_2: "rogue",
                        pygame.K_KP2: "rogue",
                        pygame.K_3: "mage",
                        pygame.K_KP3: "mage",
                    }
                    player_class = class_by_key.get(event.key)

                    if player_class is not None:
                        if game_state.act_three_test_mode:
                            game_state.player.player_class = player_class
                            apply_player_stat_transition(
                                game_state.player,
                                PLAYER_STARTING_STATS,
                                CLASS_BASE_STATS[player_class],
                            )
                            game_state.act_three_debug_class_selection_open = False
                            game_state.subclass_selection_open = True
                        else:
                            game_state = create_act_three_debug_transition(player_class, pygame.time.get_ticks())
                    continue

                if game_state.act_three_transition_open:
                    if event.key in (
                        pygame.K_SPACE,
                        pygame.K_RETURN,
                        pygame.K_KP_ENTER,
                    ):
                        advance_act_three_transition(
                            game_state,
                            pygame.time.get_ticks(),
                        )
                    continue

                if game_state.subclass_selection_open:
                    if game_state.player.player_class == "rogue":
                        subclass_keys = {
                            pygame.K_1: "assassin",
                            pygame.K_KP1: "assassin",
                            pygame.K_2: "archer",
                            pygame.K_KP2: "archer",
                        }
                    elif game_state.player.player_class == "mage":
                        subclass_keys = {
                            pygame.K_1: "warlock",
                            pygame.K_KP1: "warlock",
                            pygame.K_2: "summoner",
                            pygame.K_KP2: "summoner",
                        }
                    else:
                        subclass_keys = {
                            pygame.K_1: "berserker",
                            pygame.K_KP1: "berserker",
                            pygame.K_2: "paladin",
                            pygame.K_KP2: "paladin",
                        }
                    subclass = subclass_keys.get(event.key)

                    if (
                        game_state.player.subclass is None
                        and subclass is not None
                    ):
                        choose_subclass(
                            game_state,
                            subclass,
                        )
                    continue

                if game_state.player.health <= 0 or game_state.game_won:
                    if event.key == pygame.K_r:
                        if (
                            act_three_music_attempted
                            and pygame.mixer.get_init() is not None
                        ):
                            pygame.mixer.music.stop()
                        act_three_music_attempted = False
                        game_state = create_game_state()
                        progress_tracking_enabled = True
                    continue

                if game_state.class_selection_open:
                    transition_elapsed = (
                        pygame.time.get_ticks()
                        - game_state.class_transition_started_at
                    )

                    if transition_elapsed < CLASS_SELECTION_READY_MS:
                        if event.key in (
                            pygame.K_SPACE,
                            pygame.K_RETURN,
                            pygame.K_KP_ENTER,
                        ):
                            game_state.class_transition_started_at = (
                                pygame.time.get_ticks()
                                - CLASS_SELECTION_READY_MS
                                - 500
                            )
                        continue

                    chosen_class = None

                    if event.key in (pygame.K_1, pygame.K_KP1):
                        chosen_class = "warrior"
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        chosen_class = "rogue"
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        chosen_class = "mage"

                    if chosen_class is None:
                        continue

                    game_state.player.player_class = chosen_class
                    apply_player_stat_transition(
                        game_state.player,
                        PLAYER_STARTING_STATS,
                        CLASS_BASE_STATS[chosen_class],
                    )

                    game_state.floor_index += 1
                    game_state.floor = create_floor_state(game_state.floor_index)
                    clear_archer_barrage_zone(game_state)
                    clear_berserker_crushing_leap(game_state)
                    game_state.player.key_count = 0
                    game_state.class_selection_open = False
                    game_state.class_transition_started_at = 0
                    game_state.player_attack_targets = []
                    add_log_message(
                        game_state.combat_log,
                        f"The hero becomes a {game_state.player.player_class}.",
                    )
                    add_log_message(
                        game_state.combat_log,
                        "Act II begins. The world gains shape.",
                    )
                    continue

                if game_state.upgrade_screen_open:
                    if event.key in (pygame.K_1, pygame.K_KP1):
                        if game_state.player.gold_count <= 0:
                            game_state.upgrade_message = "Not enough gold."
                        else:
                            game_state.player.gold_count -= 1
                            apply_attribute_upgrade(
                                game_state.player,
                                "vitality",
                            )
                            game_state.upgrade_message = (
                                "Maximum HP increased by "
                                f"{HEALTH_UPGRADE_AMOUNT}."
                            )
                            add_log_message(
                                game_state.combat_log,
                                game_state.upgrade_message,
                            )
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        if game_state.player.gold_count <= 0:
                            game_state.upgrade_message = "Not enough gold."
                        else:
                            game_state.player.gold_count -= 1
                            apply_attribute_upgrade(
                                game_state.player,
                                "power",
                            )
                            game_state.upgrade_message = (
                                "Damage increased by "
                                f"{DAMAGE_UPGRADE_AMOUNT}."
                            )
                            add_log_message(
                                game_state.combat_log,
                                game_state.upgrade_message,
                            )
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        if game_state.player.gold_count <= 0:
                            game_state.upgrade_message = "Not enough gold."
                        elif game_state.player.crit_chance >= MAX_CRIT_CHANCE:
                            game_state.upgrade_message = "Critical chance is capped."
                        else:
                            game_state.player.gold_count -= 1
                            apply_attribute_upgrade(
                                game_state.player,
                                "precision",
                            )
                            game_state.upgrade_message = (
                                "Critical chance increased by "
                                f"{round(CRIT_UPGRADE_AMOUNT * 100)}%."
                            )
                            add_log_message(
                                game_state.combat_log,
                                game_state.upgrade_message,
                            )
                    elif event.key in (pygame.K_4, pygame.K_KP4):
                        if game_state.player.gold_count <= 0:
                            game_state.upgrade_message = "Not enough gold."
                        elif game_state.player.dodge_chance >= MAX_DODGE_CHANCE:
                            game_state.upgrade_message = "Dodge chance is capped."
                        else:
                            game_state.player.gold_count -= 1
                            apply_attribute_upgrade(
                                game_state.player,
                                "evasion",
                            )
                            game_state.upgrade_message = (
                                "Dodge chance increased by "
                                f"{round(DODGE_UPGRADE_AMOUNT * 100)}%."
                            )
                            add_log_message(
                                game_state.combat_log,
                                game_state.upgrade_message,
                            )
                    elif event.key in (
                        pygame.K_RETURN,
                        pygame.K_KP_ENTER,
                    ):
                        _finish_upgrade_descent(
                            game_state,
                            pygame.time.get_ticks(),
                        )

                    continue

                game_state.clear_events()
                column_change = 0
                row_change = 0

                if event.key in (pygame.K_w, pygame.K_UP):
                    row_change = -1
                    game_state.player.facing_direction = (0, -1)
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    row_change = 1
                    game_state.player.facing_direction = (0, 1)
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    column_change = -1
                    game_state.player.facing_direction = (-1, 0)
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    column_change = 1
                    game_state.player.facing_direction = (1, 0)

                player_tried_to_move = (
                    column_change != 0 or row_change != 0
                )
                directional_ability_cast = (
                    game_state.player.player_class in ("warrior", "mage")
                    and game_state.player.directional_ability_aiming
                    and player_tried_to_move
                )
                rogue_ability_activated = False

                assassin_ability_pressed = (
                    event.key == pygame.K_1
                    and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
                    and game_state.player.subclass == "assassin"
                )
                if event.key == pygame.K_e or assassin_ability_pressed:
                    ability_request = request_class_ability(
                        game_state
                    )
                    rogue_ability_activated = (
                        ability_request
                        is AbilityRequestResult.ROGUE_ACTIVATED
                    )

                    if ability_request in (
                        AbilityRequestResult.NOT_READY,
                        AbilityRequestResult.AIMING_TOGGLED,
                    ):
                        continue

                if (
                    game_state.player.directional_ability_aiming
                    and not player_tried_to_move
                ):
                    if event.key == pygame.K_ESCAPE:
                        cancel_ability_aiming(
                            game_state
                        )
                    continue

                if event.key == pygame.K_ESCAPE:
                    menu_open = True
                    menu_state.page = "main"
                    menu_state.selected_index = 0
                    menu_started_at = pygame.time.get_ticks()
                    continue

                player_position_before_action = (
                    game_state.floor["player_column"],
                    game_state.floor["player_row"],
                )
                new_column = game_state.floor["player_column"] + column_change
                new_row = game_state.floor["player_row"] + row_change
                player_waited = event.key == pygame.K_SPACE
                living_enemies = [
                    enemy
                    for enemy in game_state.floor["enemies"]
                    if enemy["health"] > 0
                ]
                target_enemy = next(
                    (
                        enemy
                        for enemy in living_enemies
                        if (new_column, new_row)
                        in get_enemy_occupied_positions(enemy)
                    ),
                    None,
                )
                target_chest = next(
                    (
                        chest
                        for chest in game_state.floor["chests"]
                        if (
                            not chest["is_open"]
                            and (chest["column"], chest["row"])
                            == (new_column, new_row)
                        )
                    ),
                    None,
                )
                player_acted = False
                game_state.player_attack_targets = []

                if (
                    game_state.player.warlock_soul_exchange_target
                    is not None
                ):
                    exchange_target = (
                        game_state.player.warlock_soul_exchange_target
                    )
                    player_acted = perform_warlock_soul_exchange(
                        game_state,
                        exchange_target,
                        pygame.time.get_ticks(),
                    )
                    set_warlock_staff_cursor()
                elif game_state.player.warlock_curse_target is not None:
                    curse_target = (
                        game_state.player.warlock_curse_target
                    )
                    player_acted = perform_warlock_curse(
                        game_state,
                        curse_target,
                    )
                    if player_acted:
                        game_state.player.attack_animation_started_at = (
                            pygame.time.get_ticks()
                        )
                    set_warlock_staff_cursor()
                elif game_state.player.warlock_attack_target is not None:
                    warlock_target = (
                        game_state.player.warlock_attack_target
                    )
                    game_state.player.warlock_attack_target = None
                    player_acted = perform_warlock_attack(
                        game_state,
                        warlock_target,
                        resolve_oracle_hit_reaction,
                    )
                    if player_acted:
                        game_state.player.attack_animation_started_at = (
                            pygame.time.get_ticks()
                        )
                    set_warlock_staff_cursor()
                elif game_state.player.summoner_attack_target is not None:
                    summoner_target = (
                        game_state.player.summoner_attack_target
                    )
                    game_state.player.summoner_attack_target = None
                    player_acted = perform_summoner_attack(
                        game_state,
                        summoner_target,
                        resolve_oracle_hit_reaction,
                    )
                    if player_acted:
                        game_state.player.attack_animation_started_at = (
                            pygame.time.get_ticks()
                        )
                    set_summoner_staff_cursor()
                elif (
                    game_state.player.paladin_shield_charge_target
                    is not None
                ):
                    player_acted = perform_paladin_shield_charge(
                        game_state,
                        pygame.time.get_ticks(),
                        resolve_oracle_hit_reaction,
                    )
                    if player_acted:
                        set_paladin_shield_charge_cursor()
                elif (
                    game_state.player.berserker_crushing_leap_target
                    is not None
                ):
                    player_acted = perform_berserker_crushing_leap(
                        game_state,
                        pygame.time.get_ticks(),
                        resolve_oracle_hit_reaction,
                    )
                    if player_acted:
                        set_berserker_crushing_leap_cursor()
                elif game_state.player.archer_leap_target is not None:
                    leap_target = game_state.player.archer_leap_target
                    leap_origin = (
                        game_state.floor.player_column,
                        game_state.floor.player_row,
                    )
                    leap_started_at = pygame.time.get_ticks()
                    game_state.floor.player_column = leap_target[0]
                    game_state.floor.player_row = leap_target[1]
                    game_state.player.archer_leap_target = None
                    game_state.player.archer_leap_aiming = False
                    game_state.player.archer_leap_charge = 0
                    game_state.player.archer_leap_origin = leap_origin
                    game_state.player.archer_leap_started_at = (
                        leap_started_at
                    )
                    game_state.emit(
                        GameEvent(
                            type=GameEventType.MOVE,
                            actor="hero",
                            origin=leap_origin,
                            destination=leap_target,
                            data={"kind": "archer_leap"},
                        )
                    )
                    add_log_message(
                        game_state.combat_log,
                        "The archer leaps backward.",
                    )
                    set_archer_leap_cursor()
                    player_acted = True
                elif (
                    game_state.player.archer_empowered_shot_target
                    is not None
                ):
                    empowered_target = (
                        game_state.player.archer_empowered_shot_target
                    )
                    game_state.player.archer_empowered_shot_target = None
                    player_acted = perform_archer_empowered_shot(
                        game_state,
                        empowered_target,
                        resolve_oracle_hit_reaction,
                    )
                    if player_acted:
                        game_state.player.attack_animation_started_at = (
                            pygame.time.get_ticks()
                        )
                        game_state.player.archer_empowered_shot_started_at = (
                            pygame.time.get_ticks()
                        )
                    set_archer_empowered_cursor()
                elif game_state.player.archer_attack_target is not None:
                    archer_target = game_state.player.archer_attack_target
                    game_state.player.archer_attack_target = None
                    player_acted = perform_archer_attack(
                        game_state,
                        archer_target,
                        resolve_oracle_hit_reaction,
                    )
                    if player_acted:
                        game_state.player.attack_animation_started_at = (
                            pygame.time.get_ticks()
                        )
                    set_archer_attack_cursor()
                elif rogue_ability_activated:
                    player_acted = True
                elif game_state.player.teleport_target is not None:
                    teleport_target = game_state.player.teleport_target
                    teleport_origin = (
                        game_state.floor.player_column,
                        game_state.floor.player_row,
                    )
                    game_state.floor.player_column = teleport_target[0]
                    game_state.floor.player_row = teleport_target[1]
                    game_state.player.teleport_target = None
                    game_state.player.teleport_aiming = False
                    set_assassin_target_cursor()
                    game_state.player.teleport_charge = 0
                    game_state.player.teleport_camera_origin = teleport_origin
                    game_state.player.teleport_transition_started_at = (
                        pygame.time.get_ticks()
                    )
                    game_state.emit(
                        GameEvent(
                            type=GameEventType.MOVE,
                            actor="hero",
                            origin=teleport_origin,
                            destination=teleport_target,
                            data={"kind": "teleport"},
                        )
                    )
                    add_log_message(
                        game_state.combat_log,
                        "The assassin teleports through the shadows.",
                    )
                    player_acted = True
                elif directional_ability_cast:
                    player_acted = cast_directional_ability(
                        game_state,
                        column_change,
                        row_change,
                        resolve_oracle_hit_reaction,
                    )
                elif event.key == pygame.K_h:
                    player_acted = try_use_potion(game_state)
                    if player_acted:
                        game_state.player.potion_effect_started_at = (
                            pygame.time.get_ticks()
                        )
                elif player_waited:
                    player_acted = True
                elif player_tried_to_move:
                    if target_enemy:
                        if game_state.player.subclass == "warlock":
                            perform_warlock_attack(
                                game_state,
                                (new_column, new_row),
                                resolve_oracle_hit_reaction,
                            )
                        else:
                            perform_basic_attack(
                                game_state,
                                column_change,
                                row_change,
                                resolve_oracle_hit_reaction,
                            )
                        game_state.player.attack_animation_started_at = (
                            pygame.time.get_ticks()
                        )

                        player_acted = True
                    elif target_chest:
                        player_acted = open_chest(
                            game_state,
                            target_chest,
                            pygame.time.get_ticks(),
                        )
                    else:
                        player_acted = try_move_player(
                            game_state,
                            new_column,
                            new_row,
                            FIRST_ACT_FINAL_FLOOR,
                            pygame.time.get_ticks(),
                        )

                if player_acted:
                    game_state.player.familiar_turn_started_at = (
                        pygame.time.get_ticks()
                    )
                    resolve_enemy_turn(
                        game_state,
                        player_position_before_action,
                        rogue_ability_activated,
                    )
                    advance_berserker_last_rage(game_state)
                    advance_paladin_holy_shield(game_state)
                    advance_warlock_curses(game_state)
                    advance_warlock_demon_form(game_state)
                    enemy_movement_started_at = (
                        pygame.time.get_ticks()
                    )
                    record_enemy_hit_feedback(
                        game_state,
                        enemy_movement_started_at,
                    )
                    record_enemy_death_feedback(
                        game_state,
                        enemy_movement_started_at,
                    )
                    record_player_hit_feedback(
                        game_state,
                        enemy_movement_started_at,
                    )
                    record_player_death_feedback(
                        game_state,
                        enemy_movement_started_at,
                    )
                    record_familiar_hit_feedback(
                        game_state,
                        enemy_movement_started_at,
                    )
                    for barrage_shot in (
                        game_state.player.archer_barrage_shots
                    ):
                        if barrage_shot.started_at == 0:
                            barrage_shot.started_at = (
                                enemy_movement_started_at
                            )
                    moved_enemy_names = {
                        emitted_event.actor
                        for emitted_event in game_state.events
                        if emitted_event.type is GameEventType.MOVE
                    }
                    attacked_enemy_names = {
                        emitted_event.actor
                        for emitted_event in game_state.events
                        if emitted_event.type is GameEventType.ATTACK
                    }
                    healed_enemy_names = {
                        emitted_event.actor
                        for emitted_event in game_state.events
                        if emitted_event.type is GameEventType.HEAL
                    }
                    hero_attack_event = next(
                        (
                            emitted_event
                            for emitted_event in reversed(game_state.events)
                            if (
                                emitted_event.type is GameEventType.ATTACK
                                and emitted_event.actor == "hero"
                                and emitted_event.positions
                            )
                        ),
                        None,
                    )
                    if hero_attack_event is not None:
                        game_state.player.act_one_attack_target = (
                            hero_attack_event.positions[0]
                        )
                        game_state.player.act_one_attack_was_critical = any(
                            emitted_event.type is GameEventType.HIT
                            and emitted_event.actor == "hero"
                            and emitted_event.data.get("critical", False)
                            for emitted_event in game_state.events
                        )
                    dodge_event = next(
                        (
                            emitted_event
                            for emitted_event in reversed(game_state.events)
                            if (
                                emitted_event.type is GameEventType.DODGE
                                and emitted_event.target == "hero"
                            )
                        ),
                        None,
                    )
                    if current_act < 2 and dodge_event is not None:
                        game_state.player.act_one_dodge_started_at = (
                            enemy_movement_started_at
                        )
                        game_state.player.act_one_dodge_origin = (
                            dodge_event.origin
                        )
                    hero_move_event = next(
                        (
                            emitted_event
                            for emitted_event in reversed(game_state.events)
                            if (
                                emitted_event.type is GameEventType.MOVE
                                and emitted_event.actor == "hero"
                                and emitted_event.origin is not None
                            )
                        ),
                        None,
                    )
                    if current_act < 2 and hero_move_event is not None:
                        game_state.player.act_one_movement_origin = (
                            hero_move_event.origin
                        )
                        game_state.player.movement_animation_started_at = (
                            enemy_movement_started_at
                        )
                    elif current_act == 2 and hero_move_event is not None:
                        game_state.player.act_two_movement_started_at = (
                            enemy_movement_started_at
                        )
                        game_state.player.act_two_movement_origin = (
                            hero_move_event.origin
                        )
                        if hero_move_event.destination is not None:
                            game_state.player.act_two_facing_direction = (
                                hero_move_event.destination[0]
                                - hero_move_event.origin[0],
                                hero_move_event.destination[1]
                                - hero_move_event.origin[1],
                            )
                    for enemy in game_state.floor["enemies"]:
                        if enemy.name in moved_enemy_names:
                            enemy.movement_animation_started_at = (
                                enemy_movement_started_at
                            )
                            movement_event = next(
                                (
                                    emitted_event
                                    for emitted_event in reversed(
                                        game_state.events
                                    )
                                    if (
                                        emitted_event.type
                                        is GameEventType.MOVE
                                        and emitted_event.actor == enemy.name
                                        and emitted_event.origin is not None
                                    )
                                ),
                                None,
                            )
                            if movement_event is not None:
                                enemy.movement_origin = movement_event.origin
                        if (
                            enemy.name in attacked_enemy_names
                            or enemy.name in healed_enemy_names
                        ):
                            enemy.attack_animation_started_at = (
                                enemy_movement_started_at
                            )
                        if enemy.name in attacked_enemy_names:
                            attack_event = next(
                                (
                                    emitted_event
                                    for emitted_event in reversed(
                                        game_state.events
                                    )
                                    if (
                                        emitted_event.type
                                        is GameEventType.ATTACK
                                        and emitted_event.actor
                                        == enemy.name
                                    )
                                ),
                                None,
                            )
                            if attack_event is not None:
                                enemy.attack_effect_mode = (
                                    attack_event.data.get("mode")
                                )
                                enemy.attack_effect_positions = (
                                    attack_event.positions
                                )
                        if (
                            enemy.type == "warden"
                            and enemy.second_phase_announced
                            and enemy.phase_transition_started_at < 0
                        ):
                            enemy.phase_transition_started_at = (
                                enemy_movement_started_at
                            )
        if (
            game_state.upgrade_screen_open
            and game_state.player.gold_count <= 0
        ):
            _finish_upgrade_descent(
                game_state,
                pygame.time.get_ticks(),
            )

        current_time = pygame.time.get_ticks()
        _advance_floor_transition(game_state, current_time)

        if menu_open:
            draw_menu(
                game_surface,
                act_one_fonts,
                menu_state,
                current_time - menu_started_at,
                game_started,
                fullscreen,
                menu_assets,
                menu_progress.highest_act_reached,
            )
            present_game(screen, game_surface)
            clock.tick(FPS)
            continue

        if game_state.player.ultimate_animation_active:
            animation_duration = (
                ASSASSIN_ULTIMATE_PRELUDE_MS
                + len(game_state.player.ultimate_targets)
                * ASSASSIN_ULTIMATE_STEP_MS
                + ASSASSIN_ULTIMATE_OUTRO_MS
            )
            if (
                current_time
                - game_state.player.ultimate_animation_started_at
                >= animation_duration
            ):
                resolve_assassin_ultimate(
                    game_state,
                    resolve_oracle_hit_reaction,
                )
                game_state.player.ultimate_animation_active = False
                game_state.player.ultimate_animation_started_at = 0

        if (
            game_state.act_three_transition_open
            and game_state.act_three_transition_started_at == 0
        ):
            game_state.act_three_transition_started_at = (
                current_time
            )

        if (
            game_state.act_three_transition_open
            and ACT_THREE_MUSIC_ENABLED
            and not act_three_music_attempted
        ):
            act_three_music_attempted = True

            try:
                if pygame.mixer.get_init() is None:
                    pygame.mixer.init()

                pygame.mixer.music.load(
                    str(ACT_THREE_MUSIC_PATH)
                )
                pygame.mixer.music.set_volume(0.65)
                pygame.mixer.music.play(-1, fade_ms=1800)
            except pygame.error as audio_error:
                add_log_message(
                    game_state.combat_log,
                    f"Act III music unavailable: {audio_error}",
                )

        if game_state.act_three_transition_open:
            visual_elapsed = None

            if game_state.act_three_visual_started_at != 0:
                visual_elapsed = (
                    current_time
                    - game_state.act_three_visual_started_at
                )

            if (
                visual_elapsed is not None
                and visual_elapsed
                >= ACT_THREE_AWAKENING_END_MS
            ):
                game_state.act_three_transition_open = False

                if game_state.player.player_class in (
                    "warrior",
                    "rogue",
                    "mage",
                ):
                    game_state.subclass_selection_open = True
                else:
                    game_state.act_three_debug_class_selection_open = (
                        True
                    )

        current_act = FLOOR_CONFIGS[game_state.floor_index]["act"]
        current_act_floor = FLOOR_CONFIGS[game_state.floor_index][
            "act_floor"
        ]
        if (
            progress_tracking_enabled
            and current_act > menu_progress.highest_act_reached
        ):
            menu_progress = record_act_reached(
                menu_progress,
                current_act,
            )
        active_status_font = (
            act_two_fonts["status"]
            if current_act >= 2
            else font
        )
        active_heading_font = (
            act_two_fonts["sidebar_heading"]
            if current_act >= 2
            else font
        )
        active_text_font = (
            act_two_fonts["sidebar_text"]
            if current_act >= 2
            else act_one_fonts["interface"]
        )
        active_controls_font = (
            act_two_fonts["sidebar_controls"]
            if current_act >= 2
            else act_one_fonts["controls"]
        )
        game_surface.fill(BACKGROUND_COLOR)
        draw_dungeon(
            game_surface,
            game_state.floor["map"],
            current_act,
            act_two_sprites,
            current_act_floor,
            game_state.floor.visual_seed,
        )
        draw_act_one_atmosphere(
            game_surface,
            current_act,
            game_state.floor["player_column"],
            game_state.floor["player_row"],
            game_state.floor["map"],
            current_act_floor,
            game_state.floor.visual_seed,
            current_time,
        )
        draw_act_two_atmosphere(
            game_surface,
            current_act,
            game_state.floor["player_column"],
            game_state.floor["player_row"],
            game_state.floor["map"],
            current_act_floor,
            game_state.floor.visual_seed,
            current_time,
        )
        draw_map_frame(
            game_surface,
            current_act,
        )
        living_oracle = next(
            (
                enemy
                for enemy in game_state.floor["enemies"]
                if (
                    enemy["type"] == "oracle"
                    and enemy["health"] > 0
                )
            ),
            None,
        )
        draw_oracle_emitters(
            game_surface,
            game_state.floor["boss_emitters"],
            (
                living_oracle is not None
                and living_oracle["oracle_awakened"]
            ),
            act_two_sprites,
        )
        draw_player_attack_markers(
            game_surface,
            game_state.player_attack_targets,
        )
        draw_attack_markers(
            game_surface,
            game_state.floor["enemies"],
            current_act,
            current_time,
        )
        draw_act_one_boss_effects(
            game_surface,
            game_state.floor["enemies"],
            current_act,
            current_time,
            active_status_font,
        )
        if game_state.floor["boss_door"] is not None:
            living_boss_group = any(
                enemy["health"] > 0 and enemy["boss_group"]
                for enemy in game_state.floor["enemies"]
            )
            living_boss_guards = any(
                enemy["health"] > 0 and not enemy["boss_group"]
                for enemy in game_state.floor["enemies"]
            )
            boss_door_is_open = not living_boss_guards

            if game_state.floor[
                "seal_boss_door_during_fight"
            ] and game_state.floor["boss_fight_started"]:
                boss_door_is_open = (
                    not living_boss_group
                )

            draw_boss_door(
                game_surface,
                game_state.floor["boss_door"][0],
                game_state.floor["boss_door"][1],
                boss_door_is_open,
            )
        draw_stairs(
            game_surface,
            game_state.floor["stairs_column"],
            game_state.floor["stairs_row"],
            not any(
                enemy["health"] > 0
                for enemy in game_state.floor["enemies"]
            ),
            current_act,
            act_two_sprites,
        )
        for potion in game_state.floor["potions"]:
            draw_potion(
                game_surface,
                potion["column"],
                potion["row"],
                current_act,
                act_two_sprites,
            )
        for chest in game_state.floor["chests"]:
            draw_chest(
                game_surface,
                chest,
                current_act,
                act_two_sprites,
                current_time,
            )
            if chest["loot_available"]:
                draw_coin(
                    game_surface,
                    chest["column"],
                    chest["row"],
                    current_act,
                    act_two_sprites,
                )
        for dropped_key in game_state.floor["dropped_keys"]:
            draw_key(
                game_surface,
                dropped_key[0],
                dropped_key[1],
                current_act,
                act_two_sprites,
            )
        draw_player(
            game_surface,
            game_state.floor["player_column"],
            game_state.floor["player_row"],
            game_state.player.health,
            game_state.player.max_health,
            game_state.player.player_class,
            current_act,
            act_two_sprites,
            game_state.player.invisibility_turns,
            current_time,
            game_state.player.potion_effect_started_at,
            game_state.player.hit_animation_started_at,
            game_state.player.hit_origin,
            game_state.player.attack_animation_started_at,
            game_state.player.act_one_attack_target,
            (
                game_state.player.act_two_movement_started_at
                if current_act == 2
                else game_state.player.movement_animation_started_at
            ),
            (
                game_state.player.act_two_movement_origin
                if current_act == 2
                else game_state.player.act_one_movement_origin
            ),
            game_state.player.act_one_dodge_started_at,
            game_state.player.act_one_dodge_origin,
            game_state.player.death_animation_started_at,
            game_state.player.hit_damage,
            active_status_font,
            game_state.player.act_two_facing_direction,
        )
        for enemy in game_state.floor["enemies"]:
            recent_act_one_hit = (
                current_act < 2
                and enemy.hit_animation_started_at >= 0
                and 0
                <= current_time - enemy.hit_animation_started_at
                < 380
            )
            has_act_one_death_effect = (
                current_act < 2
                and enemy.death_animation_started_at >= 0
            )
            has_act_two_death_effect = (
                current_act == 2
                and enemy.type in (
                    "goblin",
                    "archer",
                    "brute",
                    "sentinel",
                    "priest",
                )
                and enemy.death_animation_started_at >= 0
            )
            if (
                enemy["health"] > 0
                or recent_act_one_hit
                or has_act_one_death_effect
                or has_act_two_death_effect
            ):
                draw_enemy(
                    game_surface,
                    enemy,
                    current_act,
                    act_two_sprites,
                    current_time,
                    active_status_font,
                )
        draw_act_one_player_attack_effect(
            game_surface,
            current_act,
            game_state.floor["player_column"],
            game_state.floor["player_row"],
            game_state.player.act_one_attack_target,
            current_time,
            game_state.player.attack_animation_started_at,
            game_state.player.act_one_attack_was_critical,
        )
        draw_act_two_player_attack_effect(
            game_surface,
            current_act,
            game_state.floor["player_column"],
            game_state.floor["player_row"],
            game_state.player.act_one_attack_target,
            game_state.player.player_class,
            current_time,
            game_state.player.attack_animation_started_at,
            game_state.player.act_one_attack_was_critical,
        )
        draw_act_one_pickup_effect(
            game_surface,
            current_act,
            game_state.player.act_one_pickup_kind,
            game_state.player.act_one_pickup_origin,
            current_time,
            game_state.player.act_one_pickup_started_at,
        )
        draw_oracle_projectiles(
            game_surface,
            game_state.floor["projectiles"],
            act_two_sprites,
        )
        draw_status(
            game_surface,
            active_status_font,
            game_state.floor_index,
            game_state.player.health,
            game_state.floor["enemies"],
            game_state.game_won,
        )
        if current_act == 2:
            draw_act_two_player_feedback_overlay(
                game_surface,
                game_state,
                act_two_fonts,
                act_two_sprites,
                current_time,
            )
        draw_sidebar(
            game_surface,
            active_heading_font,
            active_text_font,
            active_controls_font,
            game_state.combat_log,
            game_state.player.health,
            game_state.player.max_health,
            game_state.player.damage_min,
            game_state.player.damage_max,
            game_state.player.crit_chance,
            game_state.player.dodge_chance,
            game_state.player.potion_count,
            game_state.player.gold_count,
            game_state.player.key_count,
            game_state.player.enemies_defeated,
            game_state.player.player_class,
            game_state.player.ability_kill_charge,
            game_state.player.invisibility_turns,
            game_state.player.directional_ability_aiming,
            current_act,
            act_two_sprites,
        )
        if current_act >= 3:
            draw_act_three_gameplay(
                game_surface,
                game_state,
                act_three_fonts,
                act_three_gameplay_assets,
                current_time,
            )
        if game_state.upgrade_screen_open:
            active_upgrade_title_font = (
                act_three_fonts["title"]
                if current_act >= 3
                else (
                    act_two_fonts["title"]
                    if current_act >= 2
                    else title_font
                )
            )
            active_upgrade_text_font = (
                act_three_fonts["text"]
                if current_act >= 3
                else (
                    act_two_fonts["text"]
                    if current_act >= 2
                    else act_one_fonts["interface"]
                )
            )
            upgrade_mouse_position = window_to_game_position(
                screen,
                pygame.mouse.get_pos(),
            )
            draw_upgrade_screen(
                game_surface,
                active_upgrade_title_font,
                active_upgrade_text_font,
                game_state.player.gold_count,
                game_state.player.health,
                game_state.player.max_health,
                game_state.player.damage_min,
                game_state.player.damage_max,
                game_state.player.crit_chance,
                game_state.player.dodge_chance,
                game_state.upgrade_message,
                upgrade_mouse_position,
            )
        if game_state.class_selection_open:
            class_mouse_position = window_to_game_position(
                screen,
                pygame.mouse.get_pos(),
            )
            draw_class_selection_screen(
                game_surface,
                title_font,
                font,
                act_two_fonts["heading"],
                act_two_fonts["text"],
                act_two_sprites,
                (
                    pygame.time.get_ticks()
                    - game_state.class_transition_started_at
                ),
                class_mouse_position,
            )
        if game_state.act_three_debug_class_selection_open:
            debug_mouse_position = window_to_game_position(
                screen,
                pygame.mouse.get_pos(),
            )
            draw_act_three_debug_class_selection(
                game_surface,
                act_three_fonts["title"],
                act_three_fonts["heading"],
                act_three_fonts["text"],
                debug_mouse_position,
            )
        elif game_state.act_three_transition_open:
            draw_act_three_awakening(
                game_surface,
                act_three_transition_assets,
                act_three_fonts["narrative"],
                (
                    current_time
                    - game_state.act_three_transition_started_at
                ),
                (
                    None
                    if game_state.act_three_visual_started_at == 0
                    else (
                        current_time
                        - game_state.act_three_visual_started_at
                    )
                ),
                game_state.player.player_class,
            )
        elif game_state.subclass_selection_open:
            subclass_mouse_position = window_to_game_position(
                screen,
                pygame.mouse.get_pos(),
            )
            draw_subclass_selection_screen(
                game_surface,
                act_three_fonts["title"],
                act_three_fonts["heading"],
                act_three_fonts["text"],
                act_three_transition_assets,
                subclass_mouse_position,
                game_state.player.subclass,
                game_state.player.player_class,
            )
        if (
            game_state.floor_transition_started_at >= 0
            and game_state.floor_transition_target_index is not None
        ):
            target_floor_config = FLOOR_CONFIGS[
                game_state.floor_transition_target_index
            ]
            target_act = target_floor_config["act"]
            target_act_floor = target_floor_config["act_floor"]
            transition_title_font = (
                act_one_fonts["title"]
                if target_act == 1
                else act_two_fonts["title"]
                if target_act == 2
                else act_three_fonts["title"]
            )
            transition_text_font = (
                act_one_fonts["interface"]
                if target_act == 1
                else act_two_fonts["text"]
                if target_act == 2
                else act_three_fonts["text"]
            )
            draw_floor_transition(
                game_surface,
                transition_title_font,
                transition_text_font,
                (
                    current_time
                    - game_state.floor_transition_started_at
                ),
                _roman_floor_number(target_act_floor),
                (
                    FLOOR_INTRO_SUBTITLES.get(target_act_floor, "")
                    if target_act == 1
                    else "THE DESCENT CONTINUES"
                ),
            )
        present_game(screen, game_surface)
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
