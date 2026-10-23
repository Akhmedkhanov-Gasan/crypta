import pygame
import resource_store as resources
from presentation.dev_console import DevConsole

from application.transitions import (
    advance_floor_transition,
    complete_class_selection,
)
from acts.act_three.movement import ACT_THREE_MOVEMENT_PROFILE
from acts.act_three.movement_timing import PLAYER_STEP_MS
from acts.act_one.upgrades import (
    handle_upgrade_key_input,
    handle_upgrade_pointer_input,
)
from application.resources import load_application_resources
from application.map_navigation import MapNavigationController
from application.bootstrap import begin_application_startup
from application.debug_shortcuts import (
    create_debug_game_state,
)
from application.loading import LoadingCoordinator
from application.input_policy import (
    act_one_cutscene_active,
    console_input_available,
    continuous_movement_input_available,
    gameplay_cutscene_active,
)
from application.state import ApplicationRuntimeState
from application.run_session import RunSession
from acts.act_two.input.cutscene_skip import ActTwoCutsceneSkip
from application.ground_items import (
    GroundItemInput,
    ground_item_input_available,
)
from application.frame_overlays import draw_frame_overlays
from application.turn_feedback import present_turn_feedback
from presentation.ground_items import draw_ground_item_window
from acts.act_two.presentation.bosses.oracle_audio import (
    update_oracle_fire_audio,
)
from acts.act_two.enemies.oracle.combat import (
    finish_oracle_animation_before_action,
)
from acts.act_two.presentation.bosses.oracle_phase_transition import (
    handle_oracle_cutscene_event,
    oracle_cutscene_active,
)
from acts.act_two.class_selection import (
    apply_act_two_class_selection,
)

from acts.act_one.camera import (
    ActOneCamera,
)
from acts.act_one.input import handle_act_one_pointer_input
from acts.act_one.runtime import (
    advance_act_one_scenes,
    refresh_act_one_visibility,
    update_act_one_view,
)
from acts.act_one.presentation.renderer import draw_act_one_gameplay
from acts.act_one.player_actions import resolve_act_one_player_action
from acts.act_one.presentation.death_scene import (
    handle_act_one_death_event,
)
from application.directional_input import (
    MOVEMENT_KEYS,
    WAIT_KEYS,
    movement_direction_for_key,
)
from acts.act_two.controls import (
    CONSUMABLE_KEYS,
    visual_direction as act_two_visual_direction,
)
from application.movement_input import (
    DEFAULT_MOVEMENT_PROFILE,
    accept_movement_direction,
    begin_held_movement,
    create_held_movement_event,
    movement_event_is_current,
    movement_input_is_locked,
    release_held_movement,
    sync_movement_scope,
)
from acts.act_two.input_state import ActTwoInputRuntimeState
from acts.act_two.input.interface import ActTwoInterfaceInput
from acts.act_two.input.pointer import handle_act_two_pointer_event
from acts.act_two.input.class_selection import (
    handle_class_selection_key,
    handle_class_selection_pointer,
)
from acts.act_two.input.action_request import ActTwoActionRequest
from acts.act_two.player_actions import (
    resolve_act_two_action_request,
)
from acts.act_two.abilities import (
    select_directional_ability_direction,
)
from acts.act_two.presentation.death_score import (
    draw_act_two_death_score,
    handle_act_two_death_event,
)
from application.player_stun import stunned_wait_event
from presentation.control_effects import forced_movement_is_active
from acts.act_two.consumables import (
    advance_fire_zones,
)
from acts.act_two.traps import advance_spike_traps
from acts.act_two.treasury import update_treasury_trial
from acts.act_two.presentation.camera import ActTwoCamera
from acts.act_two.presentation.renderer import ActTwoRenderer
from acts.act_two.presentation.interface import ActTwoInterface
from acts.act_two.runtime import advance_oracle_runtime
from acts.act_two.turns import (
    act_two_combat_is_active,
    complete_act_two_player_turn,
)
from acts.act_three.input import (
    handle_act_three_key_event,
    handle_act_three_pointer_event,
)
from acts.act_three.turns import resume_barrage_turn
from presentation.cursors import (
    set_archer_attack_cursor,
    set_default_cursor,
    set_warlock_staff_cursor,
)
from acts.act_three.runtime import (
    advance_act_three_transition,
    choose_subclass,
    create_act_three_debug_transition,
)
from acts.act_three.player_actions import resolve_act_three_player_action
from acts.turns import resolve_enemy_turn
from acts.act_two.enemies.oracle.behavior import resolve_oracle_hit_reaction
from game.combat_log import add_log_message
from game.factories import (
    create_game_state,
)

from game.progress_store import (
    load_progress,
    record_act_reached,
    select_menu_theme,
)
from application.auto_movement import (
    AUTO_MOVE_INTERVAL_MS,
    accept_auto_move_event,
    create_auto_move_event,
)
from levels import FLOOR_CONFIGS
from acts.act_three.presentation import draw_act_three_gameplay
from presentation.layout import CLASS_SELECTION_READY_MS
from presentation.layout import (
    ACT_THREE_AWAKENING_END_MS,
    AWAKENING_HOLD_END_MS,
    AWAKENING_SECOND_OPEN_START_MS,
    ACT_TWO_MENU_MUSIC_PATH,
    ACT_TWO_MUSIC_PATH,
    ACT_THREE_MUSIC_PATH,
    CLASS_SELECTION_CHOICE_END_MS,
)
from acts.act_one.music import ACT_ONE_MENU_MUSIC_PATH, update_act_one_music
from presentation.display import (
    present_game,
    window_to_game_position,
)
from presentation.menu import (
    MenuState,
    draw_menu,
    draw_run_save_error,
    handle_menu_event,
)
from acts.act_three.settings import (
    ASSASSIN_ULTIMATE_OUTRO_MS,
    ASSASSIN_ULTIMATE_PRELUDE_MS,
    ASSASSIN_ULTIMATE_STEP_MS,
)
from settings import (
    BACKGROUND_COLOR,
    FPS,
    GAME_HEIGHT,
    GAME_WIDTH,
)
from systems.player_abilities import (
    AbilityRequestResult,
    advance_berserker_last_rage,
    advance_paladin_sacred_ground,
    advance_warlock_curses,
    advance_warlock_demon_form,
    cancel_ability_aiming,
    resolve_assassin_ultimate,
    request_class_ability,
    paladin_sacred_ground_impact_ready,
    perform_paladin_sacred_ground,
    resolve_paladin_sacred_ground,
)

FIRST_ACT_FINAL_FLOOR = max(
    index
    for index, config in enumerate(FLOOR_CONFIGS)
    if config["act"] == 1
)
FIRST_ACT_THREE_FLOOR = next(
    index
    for index, floor_config in enumerate(FLOOR_CONFIGS)
    if floor_config["act"] == 3
)
ACT_THREE_MUSIC_ENABLED = True


def run():
    bootstrap = begin_application_startup(fullscreen=True)
    window_state = bootstrap.window
    game_surface = bootstrap.game_surface
    clock = bootstrap.clock
    startup = bootstrap.startup

    loaded_resources = load_application_resources(startup)
    act_one_fonts = loaded_resources.act_one_fonts
    act_one_gameplay_assets = loaded_resources.act_one_gameplay_assets
    log_font = act_one_fonts["text"]
    act_two_fonts = loaded_resources.act_two_fonts
    act_two_sprites = loaded_resources.act_two_sprites
    act_two_hud_layout = loaded_resources.act_two_hud_layout
    oracle_ui_layout = loaded_resources.oracle_ui_layout
    oracle_ui_assets = loaded_resources.oracle_ui_assets
    act_two_trade_layout = loaded_resources.act_two_trade_layout
    bloody_altar_layout = loaded_resources.bloody_altar_layout
    death_score_layout = loaded_resources.death_score_layout
    death_score_assets = loaded_resources.death_score_assets
    act_three_fonts = loaded_resources.act_three_fonts
    act_three_gameplay_assets = loaded_resources.act_three_gameplay_assets
    act_three_transition_assets = loaded_resources.act_three_transition_assets
    menu_assets = loaded_resources.menu_assets
    menu_layouts = loaded_resources.menu_layouts
    menu_fonts = loaded_resources.menu_fonts
    act_one_sounds = loaded_resources.act_one_sounds
    act_two_transition_sounds = loaded_resources.act_two_transition_sounds
    act_two_sounds = loaded_resources.act_two_sounds
    act_three_sounds = loaded_resources.act_three_sounds
    if pygame.mixer.get_init() is not None:
        pygame.mixer.set_reserved(2)

    game_state = startup.load(create_game_state)
    run_session = RunSession()
    startup.load(run_session.load)
    dev_console = DevConsole()
    act_one_camera = ActOneCamera()
    act_two_camera = ActTwoCamera()
    act_two_renderer = ActTwoRenderer()
    act_two_interface = ActTwoInterface(
        act_two_fonts,
        act_two_sprites,
        act_two_hud_layout,
        act_two_trade_layout,
        bloody_altar_layout,
        oracle_ui_layout,
        oracle_ui_assets,
    )
    act_two_interface_input = ActTwoInterfaceInput(
        act_two_hud_layout,
        act_two_trade_layout,
        bloody_altar_layout,
    )
    map_navigation = MapNavigationController(act_two_hud_layout)
    act_one_world_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    menu_progress = startup.load(load_progress)

    startup.finish()
    window_state.screen = startup.window
    if not window_state.fullscreen:
        window_state.windowed_size = window_state.screen.get_size()
    del startup
    clock.tick()
    menu_state = MenuState(menu_theme=menu_progress.menu_theme)
    act_one_sounds.set_master_volume(menu_state.effects_volume)
    act_two_transition_sounds.set_master_volume(
        menu_state.effects_volume
    )
    act_two_sounds.set_master_volume(menu_state.effects_volume)
    act_three_sounds.set_master_volume(menu_state.effects_volume)
    app_runtime = ApplicationRuntimeState(
        menu_started_at=pygame.time.get_ticks(),
    )
    act_one_menu_music_playing = False
    act_two_menu_music_playing = False
    act_one_music_attempted = False
    act_one_warden_music_attempted = False
    act_one_warden_music_channel = None
    act_two_transition_audio_started = False
    act_two_eyes_close_played = False
    act_two_eyes_open_played = False
    act_two_music_attempted = False
    act_three_music_attempted = False
    act_two_input_state = ActTwoInputRuntimeState()
    ground_item_window = GroundItemInput()
    cutscene_skip = ActTwoCutsceneSkip()
    loading = LoadingCoordinator(
        window_state,
        clock,
        act_two_input_state.reset_for_loading,
    )

    while app_runtime.running:
        loading.completed = False
        current_act = game_state.floor.presentation_act
        console_available = console_input_available(
            app_runtime,
            game_state,
        )

        if not console_available:
            dev_console.close()

        if act_two_input_state.resonance_cursor_active and (
            current_act != 2
            or app_runtime.menu_open
            or game_state.player.health <= 0
            or game_state.floor_transition_started_at >= 0
        ):
            set_warlock_staff_cursor(False)
            act_two_input_state.resonance_cursor_active = False
        continuous_move_time = pygame.time.get_ticks()

        if gameplay_cutscene_active(game_state):
            act_two_input_state.reset_held_movement()
            act_two_input_state.cancel_auto_move()
            act_two_input_state.cancel_consumable_drag()

        continuous_movement_available = continuous_movement_input_available(
            app_runtime,
            game_state,
            dev_console.is_open,
            continuous_move_time,
        )
        ground_item_window.update(
            game_state,
            act_two_input_state,
            continuous_movement_available,
            continuous_move_time,
            (
                act_one_sounds
                if current_act == 1
                else act_two_sounds if current_act == 2 else None
            ),
        )
        continuous_movement_available = (
            continuous_movement_available
            and not ground_item_window.is_open
        )

        if game_state.rune_selection_open:
            act_two_input_state.cancel_auto_move()
            act_two_input_state.cancel_consumable_drag()
        if game_state.bloody_altar_open:
            act_two_input_state.cancel_auto_move()
            act_two_input_state.cancel_consumable_drag()
        movement_profile = (
            ACT_THREE_MOVEMENT_PROFILE
            if game_state.floor.presentation_act == 3
            else DEFAULT_MOVEMENT_PROFILE
        )
        sync_movement_scope(
            act_two_input_state,
            game_state.player,
            game_state.floor,
            movement_profile,
        )
        held_movement_event = create_held_movement_event(
            act_two_input_state,
            continuous_move_time,
            continuous_movement_available,
            act_two_combat_is_active(game_state),
            profile=movement_profile,
        )

        if held_movement_event is not None:
            pygame.event.post(held_movement_event)

        auto_move_event = create_auto_move_event(
            act_two_input_state,
            game_state,
            continuous_move_time,
            continuous_movement_available,
            (
                PLAYER_STEP_MS
                if current_act == 3
                else AUTO_MOVE_INTERVAL_MS
            ),
        )
        if auto_move_event is not None:
            pygame.event.post(auto_move_event)
        menu_visual_theme = (
            FLOOR_CONFIGS[game_state.floor_index]["act"]
            if app_runtime.game_started
            else menu_state.menu_theme
        )

        active_menu_layouts = menu_layouts[
            menu_visual_theme
        ]
        sacred_ground_time = pygame.time.get_ticks()
        if (
            app_runtime.game_started
            and not app_runtime.menu_open
            and current_act == 3
            and paladin_sacred_ground_impact_ready(
                game_state,
                sacred_ground_time,
            )
            and perform_paladin_sacred_ground(
                game_state,
                sacred_ground_time,
            )
        ):
            pygame.event.post(
                pygame.event.Event(
                    pygame.KEYDOWN,
                    key=pygame.K_SPACE,
                    paladin_sacred_ground_turn=True,
                )
            )

        barrage_turn = game_state.act_three.barrage_turn
        if (
            current_act == 3
            and app_runtime.game_started
            and not app_runtime.menu_open
            and barrage_turn is not None
            and pygame.time.get_ticks() >= barrage_turn.ready_at
        ):
            pygame.event.post(
                pygame.event.Event(
                    pygame.KEYDOWN,
                    key=pygame.K_UNKNOWN,
                    archer_barrage_resume=True,
                )
            )

        for event in pygame.event.get():
            if app_runtime.quit_requested:
                continue

            if loading.completed:
                if event.type == pygame.QUIT:
                    app_runtime.request_quit()
                continue

            debug_game_state = create_debug_game_state(
                event,
                pygame.time.get_ticks(),
                FIRST_ACT_FINAL_FLOOR,
                FIRST_ACT_THREE_FLOOR,
                CLASS_SELECTION_READY_MS,
            )

            if debug_game_state is not None:
                if pygame.mixer.get_init() is not None:
                    pygame.mixer.music.stop()
                    pygame.mixer.Channel(0).stop()

                if act_one_warden_music_channel is not None:
                    act_one_warden_music_channel.stop()

                act_one_music_attempted = False
                act_one_warden_music_attempted = False
                act_one_warden_music_channel = None
                act_two_music_attempted = False
                act_three_music_attempted = False
                act_two_transition_audio_started = False
                act_two_eyes_close_played = False
                act_two_eyes_open_played = False

                game_state = debug_game_state
                current_act = (
                    game_state.floor.presentation_act
                )

                app_runtime.progress_tracking_enabled = False
                app_runtime.start_game()

                act_one_camera = ActOneCamera()
                act_two_camera = ActTwoCamera()
                act_two_renderer.reset()
                ground_item_window = GroundItemInput()
                cutscene_skip = ActTwoCutsceneSkip()

                act_two_input_state.reset_for_loading()
                menu_state.pause_background = None
                menu_state.transition_from_theme = None
                set_default_cursor()
                continue

            if (
                current_act == 3
                and game_state.act_three.barrage_turn is not None
                and event.type in (
                    pygame.KEYDOWN,
                    pygame.MOUSEBUTTONDOWN,
                    pygame.MOUSEBUTTONUP,
                )
                and not getattr(
                    event,
                    "archer_barrage_resume",
                    False,
                )
                and not (
                    event.type == pygame.KEYDOWN
                    and event.key in (
                        pygame.K_F1,
                        pygame.K_F2,
                        pygame.K_F3,
                        pygame.K_F4,
                    )
                )
            ):
                continue

            if (
                act_one_cutscene_active(game_state)
                and app_runtime.game_started
                and not app_runtime.menu_open
                and event.type not in (
                    pygame.QUIT,
                    pygame.VIDEORESIZE,
                )
                and not (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                )
            ):
                act_two_input_state.reset_held_movement()
                act_two_input_state.cancel_auto_move()
                act_two_input_state.cancel_consumable_drag()
                continue

            if cutscene_skip.handle_event(
                game_state,
                event,
                enabled=(
                    app_runtime.game_started
                    and not app_runtime.menu_open
                ),
            ):
                continue

            death_menu_requested = False
            menu_state.can_continue = run_session.can_continue(
                game_state,
                app_runtime,
            )

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button in (1, 3)
            ):
                act_two_input_state.cancel_auto_move()
                act_two_input_state.reset_held_movement()
            elif (
                event.type == pygame.KEYDOWN
                and event.key in MOVEMENT_KEYS
                and not getattr(event, "automatic_movement", False)
            ):
                act_two_input_state.cancel_auto_move()
            movement_profile = (
                ACT_THREE_MOVEMENT_PROFILE
                if game_state.floor.presentation_act == 3
                else DEFAULT_MOVEMENT_PROFILE
            )
            sync_movement_scope(
                act_two_input_state,
                game_state.player,
                game_state.floor,
                movement_profile,
            )

            if not movement_event_is_current(
                act_two_input_state,
                event,
            ):
                continue

            if (
                movement_profile.step_duration_ms > 0
                and event.type == pygame.KEYDOWN
                and not getattr(event, "automatic_movement", False)
                and event.key not in MOVEMENT_KEYS
            ):
                act_two_input_state.reset_held_movement()
            if hasattr(event, "auto_move_revision"):
                if (
                    app_runtime.menu_open
                    or dev_console.is_open
                    or not continuous_movement_available
                ):
                    act_two_input_state.cancel_auto_move()
                    continue

                if not accept_auto_move_event(
                    act_two_input_state,
                    game_state,
                    event,
                    pygame.time.get_ticks(),
                ):
                    continue

            console_toggle_pressed = (
                event.type == pygame.KEYDOWN
                and (
                    event.key == pygame.K_BACKQUOTE
                    or getattr(event, "scancode", None) == 53
                )
            )

            if console_toggle_pressed and (
                console_available or dev_console.is_open
            ):
                if dev_console.is_open:
                    dev_console.close()
                elif console_available:
                    dev_console.open()
                    act_two_input_state.reset_held_movement()
                    act_two_input_state.reset_auto_move()
                    act_two_input_state.cancel_consumable_drag()
                    game_state.act_two_journal_dragging = False

                continue

            if dev_console.handle_event(event, game_state):
                continue

            if oracle_cutscene_active(game_state.floor):
                event_position = getattr(
                    event,
                    "pos",
                    pygame.mouse.get_pos(),
                )
                oracle_action = handle_oracle_cutscene_event(
                    game_state.floor,
                    event,
                    game_surface,
                    window_to_game_position(
                        window_state.screen,
                        event_position,
                    ),
                )

                act_two_input_state.reset_held_movement()
                act_two_input_state.cancel_auto_move()
                act_two_input_state.cancel_consumable_drag()

                if oracle_action == "summary":
                    game_state.game_won = True
                    game_state.run_stats.completed_floors.add(
                        game_state.floor_index
                    )
                    game_state.player.act_two.death_score_open = True
                    game_state.player.act_two.death_input_unlock_at = (
                        pygame.time.get_ticks() + 250
                    )
                    game_state.floor.oracle_death.finished = True
                elif event.type not in (
                    pygame.QUIT,
                    pygame.VIDEORESIZE,
                ):
                    continue

            if event.type == pygame.WINDOWFOCUSLOST:
                act_two_input_state.reset_held_movement()
                act_two_input_state.cancel_auto_move()
                continue
            if (
                event.type == pygame.KEYUP
                and event.key in MOVEMENT_KEYS
            ):
                release_held_movement(
                    act_two_input_state,
                    event.key,
                )
                continue

            if (
                not app_runtime.menu_open
                and current_act == 1
                and game_state.player.health <= 0
                and event.type not in (
                    pygame.QUIT,
                    pygame.VIDEORESIZE,
                )
            ):
                event_position = getattr(
                    event,
                    "pos",
                    pygame.mouse.get_pos(),
                )

                death_action = handle_act_one_death_event(
                    event,
                    game_state,
                    window_to_game_position(
                        window_state.screen,
                        event_position,
                    ),
                    pygame.time.get_ticks(),
                    game_surface.get_size(),
                )

                if death_action != "menu":
                    continue

                act_two_input_state.reset_held_movement()
                act_two_input_state.cancel_auto_move()
                act_two_input_state.cancel_consumable_drag()

                app_runtime.menu_open = True
                death_menu_requested = True

            if (
                    not app_runtime.menu_open
                    and current_act == 2
                    and (
                        game_state.player.health <= 0
                        or game_state.player.act_two.death_score_open
                    )
                    and event.type not in (
                    pygame.QUIT,
                    pygame.VIDEORESIZE,
            )
            ):
                event_position = getattr(
                    event,
                    "pos",
                    pygame.mouse.get_pos(),
                )

                death_action = handle_act_two_death_event(
                    event,
                    game_state,
                    death_score_layout,
                    window_to_game_position(
                        window_state.screen,
                        event_position,
                    ),
                    pygame.time.get_ticks(),
                )

                if death_action != "menu":
                    continue

                act_two_input_state.reset_held_movement()
                act_two_input_state.cancel_auto_move()
                act_two_input_state.cancel_consumable_drag()

                app_runtime.menu_open = True
                death_menu_requested = True
            if event.type == pygame.QUIT:
                app_runtime.request_quit()
            elif event.type == pygame.VIDEORESIZE and not window_state.fullscreen:
                window_state.resize_windowed(
                    event.w,
                    event.h,
                    (GAME_WIDTH, GAME_HEIGHT),
                )
            elif app_runtime.menu_open:
                event_position = getattr(
                    event,
                    "pos",
                    pygame.mouse.get_pos(),
                )
                if death_menu_requested:
                    menu_action = "abandon_run"
                else:
                    menu_action = handle_menu_event(
                        event,
                        menu_state,
                        window_to_game_position(
                            window_state.screen,
                            event_position,
                        ),
                        app_runtime.game_started,
                        window_state.fullscreen,
                        menu_progress.highest_act_reached,
                        menu_layout=active_menu_layouts[
                            "confirm"
                            if menu_state.page == "confirm_abandon"
                            else menu_state.page
                        ],
                    )

                if menu_action == "resume":
                    if not menu_state.can_continue:
                        continue

                    if (
                        (
                            act_one_menu_music_playing
                            or act_two_menu_music_playing
                        )
                        and pygame.mixer.get_init() is not None
                    ):
                        pygame.mixer.music.stop()

                    act_one_menu_music_playing = False
                    act_two_menu_music_playing = False

                    if not app_runtime.run_in_progress:
                        game_state = loading.run(
                            run_session.resume,
                            app_runtime,
                        )
                        current_act = game_state.floor.presentation_act
                        act_one_camera = ActOneCamera()
                        act_two_camera = ActTwoCamera()
                        act_two_renderer.reset()
                        ground_item_window = GroundItemInput()
                        act_two_input_state.reset_for_loading()
                        menu_state.pause_background = None
                        menu_state.transition_from_theme = None

                    app_runtime.start_game()
                elif menu_action in ("abandon_run", "new_run"):
                    if not run_session.discard():
                        continue

                    if (
                        (
                            act_one_music_attempted
                            or act_one_menu_music_playing
                            or act_two_menu_music_playing
                            or act_two_music_attempted
                            or act_three_music_attempted
                        )
                        and pygame.mixer.get_init() is not None
                    ):
                        pygame.mixer.music.stop()
                    if act_one_warden_music_channel is not None:
                        act_one_warden_music_channel.stop()
                    if pygame.mixer.get_init() is not None:
                        pygame.mixer.Channel(0).stop()
                    act_one_music_attempted = False
                    act_one_menu_music_playing = False
                    act_two_menu_music_playing = False
                    act_one_warden_music_attempted = False
                    act_one_warden_music_channel = None
                    act_two_transition_audio_started = False
                    act_two_eyes_close_played = False
                    act_two_eyes_open_played = False
                    act_two_music_attempted = False
                    act_three_music_attempted = False

                    if menu_action == "new_run":
                        game_state = loading.run(create_game_state)
                    else:
                        game_state = create_game_state()

                    current_act = game_state.floor.presentation_act

                    app_runtime.progress_tracking_enabled = True
                    app_runtime.game_started = False
                    app_runtime.run_in_progress = False
                    menu_state.page = "main"
                    menu_state.can_continue = False
                    menu_state.selected_index = 1
                    app_runtime.menu_started_at = pygame.time.get_ticks()

                    if menu_action == "new_run":
                        app_runtime.start_game()
                        menu_state.can_continue = True
                        menu_state.selected_index = 0

                    set_default_cursor()
                elif menu_action == "quit":
                    if app_runtime.game_started:
                        if not run_session.save(
                                game_state,
                                app_runtime,
                        ):
                            continue

                        if pygame.mixer.get_init() is not None:
                            pygame.mixer.music.stop()
                            pygame.mixer.Channel(0).stop()

                        if act_one_warden_music_channel is not None:
                            act_one_warden_music_channel.stop()

                        act_one_music_attempted = False
                        act_two_music_attempted = False
                        act_three_music_attempted = False
                        act_one_menu_music_playing = False
                        act_two_menu_music_playing = False
                        act_one_warden_music_attempted = False
                        act_one_warden_music_channel = None

                        act_two_input_state.reset_for_loading()
                        app_runtime.return_to_main_menu(
                            pygame.time.get_ticks()
                        )
                        menu_state.page = "main"
                        menu_state.selected_index = (
                            0 if menu_state.can_continue else 1
                        )
                        menu_visual_theme = menu_state.menu_theme
                        active_menu_layouts = menu_layouts[
                            menu_visual_theme
                        ]
                    else:
                        app_runtime.request_quit()
                elif menu_action == "toggle_fullscreen":
                    window_state.toggle_fullscreen()
                elif menu_action == "act_one_volume_changed":
                    act_one_sounds.set_master_volume(
                        menu_state.effects_volume
                    )
                    act_two_transition_sounds.set_master_volume(
                        menu_state.effects_volume
                    )
                    act_two_sounds.set_master_volume(
                        menu_state.effects_volume
                    )
                    act_three_sounds.set_master_volume(
                        menu_state.effects_volume
                    )
                    if (
                        act_three_music_attempted
                        and pygame.mixer.get_init() is not None
                    ):
                        act_three_sounds.set_music_volume(
                            menu_state.music_volume
                        )
                    elif (
                        (
                            act_one_music_attempted
                            or act_one_menu_music_playing
                            or act_two_menu_music_playing
                            or act_two_music_attempted
                        )
                        and pygame.mixer.get_init() is not None
                    ):
                        pygame.mixer.music.set_volume(
                            menu_state.music_volume
                        )
                    if act_one_warden_music_channel is not None:
                        act_one_warden_music_channel.set_volume(
                            menu_state.music_volume
                        )
                elif menu_action == "menu_theme_changed":
                    menu_progress = select_menu_theme(
                        menu_progress,
                        menu_state.menu_theme,
                    )
                continue
            elif game_state.floor_transition_started_at >= 0:
                continue
            elif ground_item_window.handle_event(
                    event,
                    game_state,
                    act_two_input_state,
                    (
                        act_one_sounds
                        if game_state.floor.presentation_act == 1
                        else act_two_sounds
                        if game_state.floor.presentation_act == 2
                        else None
                    ),
                    window_to_game_position(
                        window_state.screen,
                        getattr(
                            event,
                            "pos",
                            pygame.mouse.get_pos(),
                        ),
                    ),
                    game_surface.get_size(),
                    (
                            app_runtime.game_started
                            and not app_runtime.menu_open
                            and not dev_console.is_open
                    ),
                    pygame.time.get_ticks(),
            ):
                continue
            elif map_navigation.handle_event(
                    event,
                    game_state,
                    act_two_camera,
                    window_to_game_position(
                        window_state.screen,
                        getattr(event, "pos", pygame.mouse.get_pos()),
                    ),
                    enabled=continuous_movement_available,
                ):
                continue
            elif (
                current_act == 2
                and act_two_interface_input.handle_event(
                    event,
                    game_state,
                    act_two_camera,
                    act_two_input_state,
                    act_two_sounds,
                    window_to_game_position(
                        window_state.screen,
                        getattr(event, "pos", pygame.mouse.get_pos()),
                    ),
                )
            ):
                continue
            elif (
                    current_act == 3
                    and handle_act_three_pointer_event(
                event,
                game_state,
                window_state.screen,
                window_to_game_position,
                act_two_input_state,
                continuous_movement_available,
            )
            ):
                continue
            elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and game_state.upgrade_screen_open
            ):
                game_mouse_position = window_to_game_position(
                    window_state.screen,
                    event.pos,
                )

                if game_mouse_position is not None:
                    handle_upgrade_pointer_input(
                        game_state,
                        game_mouse_position,
                        pygame.time.get_ticks(),
                    )

                continue
            elif handle_class_selection_pointer(
                event,
                game_state,
                window_to_game_position(
                    window_state.screen,
                    getattr(event, "pos", pygame.mouse.get_pos()),
                ),
                pygame.time.get_ticks(),
            ):
                continue
            elif (
                current_act == 2
                and handle_act_two_pointer_event(
                    event,
                    game_state,
                    act_two_camera,
                    act_two_input_state,
                    movement_profile,
                    window_to_game_position(
                        window_state.screen,
                        getattr(event, "pos", pygame.mouse.get_pos()),
                    ),
                )
            ):
                continue
            elif handle_act_one_pointer_input(
                    event,
                    window_state.screen,
                    act_one_camera,
                    act_two_input_state,
                    game_state,
                    continuous_movement_available,
                ):
                continue
            elif event.type == pygame.KEYDOWN:
                barrage_resume = getattr(
                    event,
                    "archer_barrage_resume",
                    False,
                )
                automatic_movement = getattr(
                    event,
                    "automatic_movement",
                    False,
                )
                if (
                        (
                                event.key in MOVEMENT_KEYS
                                or getattr(event, "movement_direction", None)
                                is not None
                        )
                        and not (
                        current_act == 3
                        and (
                                game_state.player.archer_basic_aiming
                                or game_state.player.archer_piercing_aiming
                                or game_state.player.archer_barrage_zone_aiming
                        )
                )
                        and movement_input_is_locked(
                    act_two_input_state,
                    pygame.time.get_ticks(),
                )
                ):
                    act_two_input_state.reset_held_movement()
                    continue
                if not automatic_movement:
                    act_two_input_state.cancel_auto_move()
                if event.key == pygame.K_F11:
                    window_state.toggle_fullscreen()
                    continue


                if handle_act_three_key_event(
                        event,
                        game_state,
                ):
                    if movement_profile.step_duration_ms > 0:
                        act_two_input_state.reset_held_movement()
                        act_two_input_state.cancel_auto_move()
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
                            apply_act_two_class_selection(
                                game_state.player,
                                player_class,
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
                        loading.run(
                            choose_subclass,
                            game_state,
                            subclass,
                        )
                    continue

                if (
                    game_state.player.health <= 0
                    or game_state.game_won
                ) and not barrage_resume:
                    if event.key == pygame.K_r:
                        if (
                            act_three_music_attempted
                            and pygame.mixer.get_init() is not None
                        ):
                            pygame.mixer.music.stop()
                        act_three_music_attempted = False
                        game_state = loading.run(create_game_state)
                        app_runtime.progress_tracking_enabled = True
                    continue

                if handle_class_selection_key(
                    event,
                    game_state,
                    act_two_transition_sounds,
                    pygame.time.get_ticks(),
                ):
                    continue
                if handle_upgrade_key_input(
                    game_state,
                    event.key,
                    pygame.time.get_ticks(),
                ):
                    continue

                if current_act == 2 and (
                    event.key in MOVEMENT_KEYS
                    or event.key in WAIT_KEYS
                    or event.key in CONSUMABLE_KEYS
                    or event.key in (
                        pygame.K_UNKNOWN,
                        pygame.K_e,
                    )
                ):
                    oracle_interrupted_player = (
                        finish_oracle_animation_before_action(
                            game_state,
                            pygame.time.get_ticks(),
                            act_two_sounds,
                        )
                    )

                    if oracle_interrupted_player:
                        act_two_input_state.cancel_auto_move()

                    if game_state.player.health <= 0:
                        act_two_input_state.reset_held_movement()
                        act_two_input_state.cancel_auto_move()
                        continue

                stunned_action = False
                if (
                    game_state.player.stun_turns > 0
                    and not barrage_resume
                ):
                    if forced_movement_is_active(
                        game_state.player,
                        pygame.time.get_ticks(),
                    ):
                        act_two_input_state.reset_held_movement()
                        act_two_input_state.cancel_auto_move()
                        continue

                    if not (
                        event.key in MOVEMENT_KEYS
                        or event.key in WAIT_KEYS
                        or event.key in CONSUMABLE_KEYS
                        or event.key in (
                            pygame.K_UNKNOWN,
                            pygame.K_e,
                            pygame.K_h,
                            pygame.K_1,
                        )
                    ):
                        continue

                    event = stunned_wait_event(
                        game_state,
                        next(iter(WAIT_KEYS)),
                    )
                    stunned_action = True
                    act_two_input_state.reset_held_movement()
                    act_two_input_state.cancel_auto_move()

                game_state.clear_events()
                act_two_action_request = ActTwoActionRequest.from_event(
                    event,
                    game_state,
                    enabled=current_act == 2,
                )
                mage_ability_target = (
                    act_two_action_request.mage_ability_target
                )
                if (
                    current_act == 2
                    and act_two_action_request.handle_aiming(
                        event,
                        game_state,
                        act_two_input_state,
                    )
                ):
                    continue

                column_change = 0
                row_change = 0
                movement_direction = getattr(
                    event,
                    "movement_direction",
                    None,
                )
                direction_key = event.key in MOVEMENT_KEYS

                if (
                    direction_key
                    and game_state.player.directional_ability_aiming
                ):
                    act_two_input_state.reset_held_movement()
                    movement_direction = movement_direction_for_key(
                        event.key
                    )
                elif direction_key or movement_direction is not None:
                    if not continuous_movement_available:
                        act_two_input_state.reset_held_movement()
                        continue

                    if direction_key and not automatic_movement:
                        movement_direction = begin_held_movement(
                            act_two_input_state,
                            event.key,
                            pygame.time.get_ticks(),
                            profile=movement_profile,
                        )

                if movement_direction is not None:
                    if (
                        not game_state.player.directional_ability_aiming
                        and not accept_movement_direction(
                            act_two_input_state,
                            movement_direction,
                            pygame.time.get_ticks(),
                            profile=movement_profile,
                            auto_path=hasattr(event, "auto_move_revision"),
                        )
                    ):
                        continue

                    column_change, row_change = movement_direction
                    game_state.player.facing_direction = (
                        act_two_visual_direction(movement_direction)
                    )

                player_tried_to_move = (
                    column_change != 0 or row_change != 0
                )
                directional_ability_cast = (
                    game_state.player.player_class == "warrior"
                    and game_state.player.directional_ability_aiming
                    and player_tried_to_move
                )
                if (
                    directional_ability_cast
                    and current_act in (2, 3)
                    and game_state.player.player_class == "warrior"
                ):
                    directional_ability_cast = (
                        select_directional_ability_direction(
                            game_state,
                            column_change,
                            row_change,
                        )
                    )
                    if not directional_ability_cast:
                        continue
                rogue_ability_activated = False

                assassin_ability_pressed = (
                    event.key == pygame.K_1
                    and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
                    and game_state.player.subclass == "assassin"
                )
                if (
                    event.key == pygame.K_e
                    or assassin_ability_pressed
                ):
                    ability_request = request_class_ability(
                        game_state
                    )
                    if (
                        current_act == 3
                        and game_state.player.player_class
                        == "warrior"
                    ):
                        set_archer_attack_cursor(
                            game_state.player.directional_ability_aiming
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
                    and game_state.player.player_class == "mage"
                    and mage_ability_target is None
                ):
                    if event.key == pygame.K_ESCAPE:
                        cancel_ability_aiming(game_state)
                    continue

                if (
                    game_state.player.directional_ability_aiming
                    and not player_tried_to_move
                    and mage_ability_target is None
                ):
                    if event.key == pygame.K_ESCAPE:
                        cancel_ability_aiming(
                            game_state
                        )
                    continue

                if event.key == pygame.K_ESCAPE:
                    act_two_input_state.reset_held_movement()
                    act_two_input_state.cancel_auto_move()
                    act_two_input_state.cancel_consumable_drag()
                    menu_state.pause_background = game_surface.copy()
                    app_runtime.open_menu(pygame.time.get_ticks())
                    menu_state.page = "pause"
                    menu_state.selected_index = 0
                    continue

                player_position_before_action = (
                    game_state.floor["player_column"],
                    game_state.floor["player_row"],
                )
                player_waited = event.key in WAIT_KEYS
                if current_act == 1 and not player_waited:
                    game_state.player.act_one_wait_effect_started_at = -1
                if current_act == 2 and not player_waited:
                    game_state.player.act_two.wait_effect_started_at = -1
                player_acted = False
                game_state.player_attack_targets = []

                if barrage_resume:
                    player_acted = True
                elif stunned_action:
                    game_state.player.stun_turns -= 1
                    player_acted = True
                    add_log_message(
                        game_state.combat_log,
                        "The hero loses a turn recovering from the stun.",
                        category="debuff",
                    )
                elif current_act == 1:
                    act_one_action = resolve_act_one_player_action(
                        game_state,
                        event.key,
                        (column_change, row_change),
                        pygame.time.get_ticks(),
                        FIRST_ACT_FINAL_FLOOR,
                        resolve_oracle_hit_reaction,
                    )
                    if act_one_action.movement_blocked:
                        act_two_input_state.cancel_auto_move()
                        continue
                    player_acted = act_one_action.player_acted
                elif current_act == 3:
                    act_three_action = resolve_act_three_player_action(
                        game_state,
                        event,
                        (column_change, row_change),
                        mage_ability_target,
                        directional_ability_cast,
                        rogue_ability_activated,
                        FIRST_ACT_FINAL_FLOOR,
                        resolve_oracle_hit_reaction,
                    )
                    if act_three_action.movement_blocked:
                        act_two_input_state.cancel_auto_move()
                        continue
                    player_acted = act_three_action.player_acted
                elif current_act == 2:
                    act_two_action = resolve_act_two_action_request(
                        game_state,
                        event,
                        (column_change, row_change),
                        act_two_action_request,
                        directional_ability_cast,
                        rogue_ability_activated,
                        FIRST_ACT_FINAL_FLOOR,
                        resolve_oracle_hit_reaction,
                    )
                    if act_two_action.movement_blocked:
                        act_two_input_state.cancel_auto_move()
                        continue
                    if act_two_action.reset_held_movement:
                        act_two_input_state.reset_held_movement()
                    if act_two_action.trader_sound is not None:
                        act_two_sounds.play_ui_sound(
                            act_two_action.trader_sound
                        )
                    player_acted = act_two_action.player_acted
                if player_acted and not barrage_resume:
                    game_state.run_stats.turns_taken += 1
                elif automatic_movement:
                    act_two_input_state.cancel_auto_move()

                if player_acted and current_act == 2:
                    action_started_at = pygame.time.get_ticks()
                    complete_act_two_player_turn(
                        game_state,
                        player_position_before_action,
                        rogue_ability_activated,
                        act_two_input_state,
                        act_two_sounds,
                        action_started_at,
                    )

                if player_acted and current_act != 2:
                    if not barrage_resume:
                        game_state.player.familiar_turn_started_at = (
                            pygame.time.get_ticks()
                        )
                        advance_spike_traps(game_state)
                        update_treasury_trial(game_state)

                    if game_state.player.health > 0:
                        if barrage_resume:
                            resume_barrage_turn(game_state)
                        else:
                            resolve_enemy_turn(
                                game_state,
                                player_position_before_action,
                                rogue_ability_activated,
                            )

                    if game_state.act_three.barrage_turn is None:
                        if (
                            current_act == 3
                            and not getattr(
                                event,
                                "paladin_sacred_ground_turn",
                                False,
                            )
                        ):
                            resolve_paladin_sacred_ground(
                                game_state
                            )
                        if current_act == 2:
                            advance_fire_zones(game_state)
                        update_treasury_trial(game_state)
                        advance_berserker_last_rage(game_state)
                        advance_paladin_sacred_ground(game_state)
                        advance_warlock_curses(game_state)
                        advance_warlock_demon_form(game_state)

                    if game_state.act_three.barrage_turn is not None:
                        act_two_input_state.cancel_auto_move()
                        act_two_input_state.reset_held_movement()

                    present_turn_feedback(
                        game_state,
                        current_act,
                        pygame.time.get_ticks(),
                        act_two_input_state,
                        movement_profile,
                        act_one_sounds,
                        act_two_sounds,
                        act_three_sounds,
                    )
        run_session.invalidate_finished(
            game_state,
            app_runtime,
        )

        if app_runtime.quit_requested:
            if run_session.save(game_state, app_runtime):
                app_runtime.running = False
                break

            app_runtime.quit_requested = False

            if not app_runtime.menu_open:
                menu_state.pause_background = game_surface.copy()

            app_runtime.open_menu(pygame.time.get_ticks())
            menu_state.page = (
                "pause"
                if app_runtime.game_started
                else "main"
            )
            menu_state.selected_index = 0

        if loading.completed:
            continue

        current_time = pygame.time.get_ticks()

        act_one_scenes_enabled = (
            app_runtime.game_started
            and not app_runtime.menu_open
            and not loading.completed
        )
        advance_act_one_scenes(
            game_state,
            current_time,
            enabled=act_one_scenes_enabled,
        )

        advance_floor_transition(game_state, current_time)

        cutscene_skip.update(
            game_state,
            current_time,
            game_surface,
            enabled=(
                app_runtime.game_started
                and not app_runtime.menu_open
                and not loading.completed
            ),
        )

        update_oracle_fire_audio(
            game_state,
            act_two_sounds,
            enabled=(
                app_runtime.running
                and app_runtime.game_started
                and not app_runtime.menu_open
                and not game_state.class_selection_open
                and game_state.floor_transition_started_at < 0
            ),
        )

        if game_state.class_selection_open:
            awakening_elapsed = (
                current_time - game_state.class_transition_started_at
            )
            if not act_two_transition_audio_started:
                act_two_transition_audio_started = True
                if act_one_warden_music_channel is not None:
                    act_one_warden_music_channel.fadeout(1400)
                    act_one_warden_music_channel = None
                if awakening_elapsed >= AWAKENING_SECOND_OPEN_START_MS:
                    act_two_eyes_close_played = True
                if not act_two_music_attempted:
                    act_two_music_attempted = True
                    act_one_music_attempted = False
                    try:
                        if pygame.mixer.get_init() is None:
                            pygame.mixer.init()
                        resources.load_music(
                            str(ACT_TWO_MUSIC_PATH)
                        )
                        pygame.mixer.music.set_volume(
                            menu_state.music_volume
                        )
                        pygame.mixer.music.play(-1, fade_ms=1400)
                    except pygame.error as audio_error:
                        add_log_message(
                            game_state.combat_log,
                            f"Act II music unavailable: {audio_error}", category="system",
                        )

            if (
                awakening_elapsed >= AWAKENING_HOLD_END_MS
                and not act_two_eyes_close_played
            ):
                act_two_eyes_close_played = True
                act_two_transition_sounds.play("eyes_close")

            if (
                awakening_elapsed >= AWAKENING_SECOND_OPEN_START_MS
                and not act_two_eyes_open_played
            ):
                act_two_eyes_open_played = True
                act_two_transition_sounds.play("eyes_open")

        if app_runtime.menu_open:
            should_play_act_one_menu_music = (
                not app_runtime.game_started and menu_visual_theme == 1
            )
            should_play_act_two_menu_music = (
                not app_runtime.game_started and menu_visual_theme == 2
            )
            if (
                should_play_act_one_menu_music
                and not act_one_menu_music_playing
            ):
                act_one_menu_music_playing = True
                act_two_menu_music_playing = False
                try:
                    if pygame.mixer.get_init() is None:
                        pygame.mixer.init()
                    resources.load_music(
                        str(ACT_ONE_MENU_MUSIC_PATH)
                    )
                    pygame.mixer.music.set_volume(
                        menu_state.music_volume
                    )
                    pygame.mixer.music.play(-1, fade_ms=1200)
                except pygame.error as audio_error:
                    add_log_message(
                        game_state.combat_log,
                        f"Act I menu music unavailable: {audio_error}", category="system",
                    )
            elif (
                should_play_act_two_menu_music
                and not act_two_menu_music_playing
            ):
                act_one_menu_music_playing = False
                act_two_menu_music_playing = True
                try:
                    if pygame.mixer.get_init() is None:
                        pygame.mixer.init()
                    resources.load_music(
                        str(ACT_TWO_MENU_MUSIC_PATH)
                    )
                    pygame.mixer.music.set_volume(
                        menu_state.music_volume
                    )
                    pygame.mixer.music.play(-1, fade_ms=1200)
                except pygame.error as audio_error:
                    add_log_message(
                        game_state.combat_log,
                        f"Act II menu music unavailable: {audio_error}", category="system",
                    )
            elif (
                not should_play_act_one_menu_music
                and not should_play_act_two_menu_music
                and (
                    act_one_menu_music_playing
                    or act_two_menu_music_playing
                )
            ):
                if pygame.mixer.get_init() is not None:
                    pygame.mixer.music.fadeout(500)
                act_one_menu_music_playing = False
                act_two_menu_music_playing = False
            menu_state.can_continue = run_session.can_continue(
                game_state,
                app_runtime,
            )
            if (
                menu_state.page == "main"
                and not menu_state.can_continue
                and menu_state.selected_index == 0
            ):
                menu_state.selected_index = 1

            draw_menu(
                game_surface,
                menu_fonts[menu_visual_theme],
                menu_state,
                current_time - app_runtime.menu_started_at,
                app_runtime.game_started,
                window_state.fullscreen,
                menu_assets,
                menu_visual_theme,
                menu_progress.highest_act_reached,
                menu_layout=active_menu_layouts[
                    "confirm"
                    if menu_state.page == "confirm_abandon"
                    else menu_state.page
                ],
                menu_layouts=menu_layouts,
            )
            draw_run_save_error(
                game_surface,
                run_session.error,
            )
            present_game(window_state.screen, game_surface)
            clock.tick(FPS)
            continue

        if (
                current_act == 2
                and game_state.player.act_two.death_score_open
        ):
            draw_act_two_death_score(
                game_surface,
                game_state,
                death_score_layout,
                death_score_assets,
                window_to_game_position(
                    window_state.screen,
                    pygame.mouse.get_pos(),
                ),
            )
            present_game(window_state.screen, game_surface)
            clock.tick(FPS)
            continue

        if current_act == 3:
            act_three_sounds.update(
                game_state.player,
                current_time,
            )

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
                    current_time,
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
            current_act == 3
            and ACT_THREE_MUSIC_ENABLED
            and not act_three_music_attempted
        ):
            act_one_music_attempted = False
            act_two_music_attempted = False
            act_three_music_attempted = True

            try:
                if pygame.mixer.get_init() is None:
                    pygame.mixer.init()

                resources.load_music(
                    str(ACT_THREE_MUSIC_PATH)
                )
                act_three_sounds.set_music_volume(
                    menu_state.music_volume
                )
                pygame.mixer.music.play(-1, fade_ms=1800)
            except pygame.error as audio_error:
                add_log_message(
                    game_state.combat_log,
                    f"Act III music unavailable: {audio_error}", category="system",
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

        if (
            game_state.class_selection_open
            and game_state.class_selection_choice_started_at > 0
            and current_time
            - game_state.class_selection_choice_started_at
            >= CLASS_SELECTION_CHOICE_END_MS
        ):
            loading.run(
                complete_class_selection,
                game_state,
            )
            continue

        current_act = game_state.floor.presentation_act
        current_act_floor = FLOOR_CONFIGS[game_state.floor_index][
            "act_floor"
        ]
        act_two_sounds.update_fire_bomb_audio(
            game_state.floor if current_act == 2 else None,
            current_time,
        )
        (
            act_one_music_attempted,
            act_one_warden_music_attempted,
            act_one_warden_music_channel,
        ) = update_act_one_music(
            current_act,
            game_state.floor,
            menu_state.music_volume,
            game_state.combat_log,
            act_one_music_attempted,
            act_one_warden_music_attempted,
            act_one_warden_music_channel,
            act_three_music_attempted,
        )
        if (
            current_act == 2
            and not game_state.class_selection_open
            and not (
                game_state.floor.has_oracle_gate
                and game_state.floor.oracle_intro is not None
            )
            and (
                not act_two_music_attempted
                or pygame.mixer.get_init() is None
                or not pygame.mixer.music.get_busy()
            )
        ):
            act_two_music_attempted = True
            try:
                if pygame.mixer.get_init() is None:
                    pygame.mixer.init()
                resources.load_music(str(ACT_TWO_MUSIC_PATH))
                pygame.mixer.music.set_volume(
                    menu_state.music_volume
                )
                pygame.mixer.music.play(-1, fade_ms=700)
            except pygame.error as audio_error:
                add_log_message(
                    game_state.combat_log,
                    f"Act II music unavailable: {audio_error}", category="system",
                )
        refresh_act_one_visibility(game_state)

        if current_act == 2:
            advance_oracle_runtime(
                game_state,
                act_two_camera,
                current_time,
                act_two_sounds,
                menu_state.music_volume,
                act_two_input_state,
            )
        if (
            app_runtime.progress_tracking_enabled
            and current_act > menu_progress.highest_act_reached
        ):
            menu_progress = record_act_reached(
                menu_progress,
                current_act,
            )
            menu_state.menu_theme = menu_progress.menu_theme
        frame_mouse_position = window_to_game_position(
            window_state.screen,
            pygame.mouse.get_pos(),
        )

        if current_act == 1:
            update_act_one_view(
                act_one_camera,
                game_state,
                current_time,
            )
            draw_act_one_gameplay(
                game_surface,
                act_one_world_surface,
                act_one_camera,
                game_state,
                act_one_fonts,
                act_one_gameplay_assets,
                act_two_sprites,
                current_time,
                current_act_floor,
                frame_mouse_position,
            )
            draw_frame_overlays(
                game_surface,
                game_state,
                current_act,
                current_time,
                act_one_fonts,
                act_two_fonts,
                act_three_fonts,
                act_two_sprites,
                act_three_transition_assets,
                cutscene_skip,
                dev_console,
                frame_mouse_position,
            )
            present_game(window_state.screen, game_surface)
            clock.tick(FPS)
            continue

        if current_act >= 3:
            game_surface.fill(BACKGROUND_COLOR)
            map_navigation.update(game_state, act_two_camera)
            draw_act_three_gameplay(
                game_surface,
                game_state,
                act_three_fonts,
                act_three_gameplay_assets,
                current_time,
                frame_mouse_position,
            )
            map_navigation.draw(
                game_surface,
                game_state,
                frame_mouse_position,
                enabled=continuous_movement_available,
            )
            if ground_item_input_available(game_state):
                draw_ground_item_window(
                    game_surface,
                    game_state,
                    ground_item_window,
                    act_two_sprites,
                    act_two_fonts,
                    current_time,
                )
            draw_frame_overlays(
                game_surface,
                game_state,
                current_act,
                current_time,
                act_one_fonts,
                act_two_fonts,
                act_three_fonts,
                act_two_sprites,
                act_three_transition_assets,
                cutscene_skip,
                dev_console,
                frame_mouse_position,
            )
            present_game(window_state.screen, game_surface)
            clock.tick(FPS)
            continue

        game_surface.fill(BACKGROUND_COLOR)
        map_navigation.update(game_state, act_two_camera)
        oracle_world_frame = act_two_renderer.draw_gameplay(
            game_surface,
            game_state,
            act_two_camera,
            act_two_sprites,
            act_two_fonts,
            act_two_fonts["status"],
            current_time,
            current_act_floor,
            frame_mouse_position,
            act_two_input_state,
            ground_item_window,
        )
        act_two_interface.draw(
            game_surface,
            game_state,
            act_two_camera,
            map_navigation,
            ground_item_window,
            act_two_input_state,
            current_time,
            frame_mouse_position,
            oracle_world_frame,
            continuous_movement_available,
        )

        draw_frame_overlays(
            game_surface,
            game_state,
            current_act,
            current_time,
            act_one_fonts,
            act_two_fonts,
            act_three_fonts,
            act_two_sprites,
            act_three_transition_assets,
            cutscene_skip,
            dev_console,
            frame_mouse_position,
        )

        present_game(window_state.screen, game_surface)
        clock.tick(FPS)

    pygame.quit()
