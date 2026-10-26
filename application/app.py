import pygame
from presentation.dev_console import DevConsole

from application.resources import load_application_resources
from application.map_navigation import MapNavigationController
from application.bootstrap import begin_application_startup
from application.debug_shortcuts import (
    create_debug_game_state,
)
from application.loading import LoadingCoordinator
from application.state import ApplicationRuntimeState
from application.run_session import RunSession
from acts.act_two.input.cutscene_skip import ActTwoCutsceneSkip
from application.ground_items import GroundItemInput
from application.gameplay_renderer import GameplayRenderer
from application.frame_updates import ApplicationFrameUpdater
from application.frame_input import prepare_frame_input
from application.keyboard import GameplayKeyboardController
from application.pointer import GameplayPointerController
from application.event_gate import ApplicationEventGate
from application.modal_events import ApplicationModalController
from application.menu_runtime import ApplicationMenuRuntime
from application.menu_actions import MenuActionState

from acts.act_one.camera import (
    ActOneCamera,
)
from acts.act_two.input_state import ActTwoInputRuntimeState
from acts.act_two.input.interface import ActTwoInterfaceInput
from acts.act_two.presentation.death_score import draw_act_two_death_score
from acts.act_two.presentation.camera import ActTwoCamera
from acts.act_two.presentation.renderer import ActTwoRenderer
from acts.act_two.presentation.interface import ActTwoInterface
from acts.act_two.runtime import ActTwoAudioRuntime
from presentation.cursors import (
    set_default_cursor,
)
from acts.act_three.runtime import ActThreeAudioRuntime
from game.factories import (
    create_game_state,
)

from game.progress_store import load_progress
from levels import FLOOR_CONFIGS
from presentation.layout import CLASS_SELECTION_READY_MS
from presentation.display import (
    present_game,
    window_to_game_position,
)
from presentation.menu import MenuState
from settings import FPS, GAME_HEIGHT, GAME_WIDTH

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


def run():
    bootstrap = begin_application_startup(fullscreen=True)
    window_state = bootstrap.window
    game_surface = bootstrap.game_surface
    clock = bootstrap.clock
    startup = bootstrap.startup

    loaded_resources = load_application_resources(startup)
    act_one_fonts = loaded_resources.act_one_fonts
    act_one_gameplay_assets = loaded_resources.act_one_gameplay_assets
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
    act_two_audio_runtime = ActTwoAudioRuntime()
    act_three_audio_runtime = ActThreeAudioRuntime()
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
    menu_runtime = ApplicationMenuRuntime()
    act_one_sounds.set_master_volume(menu_state.effects_volume)
    act_two_transition_sounds.set_master_volume(
        menu_state.effects_volume
    )
    act_two_sounds.set_master_volume(menu_state.effects_volume)
    act_three_sounds.set_master_volume(menu_state.effects_volume)
    app_runtime = ApplicationRuntimeState(
        menu_started_at=pygame.time.get_ticks(),
    )
    act_one_music_attempted = False
    act_one_warden_music_attempted = False
    act_one_warden_music_channel = None
    act_two_input_state = ActTwoInputRuntimeState()
    ground_item_window = GroundItemInput()
    cutscene_skip = ActTwoCutsceneSkip()
    loading = LoadingCoordinator(
        window_state,
        clock,
        act_two_input_state.reset_for_loading,
    )
    gameplay_renderer = GameplayRenderer(
        act_one_fonts,
        act_one_gameplay_assets,
        act_two_fonts,
        act_two_sprites,
        act_three_fonts,
        act_three_gameplay_assets,
        act_three_transition_assets,
        act_one_world_surface,
        act_two_renderer,
        act_two_interface,
        map_navigation,
        cutscene_skip,
        dev_console,
    )
    frame_updater = ApplicationFrameUpdater(
        loading,
        cutscene_skip,
        act_two_audio_runtime,
        act_three_audio_runtime,
        act_two_input_state,
        act_one_sounds,
        act_two_transition_sounds,
        act_two_sounds,
        act_three_sounds,
    )
    keyboard = GameplayKeyboardController(
        loading,
        window_state,
        act_two_input_state,
        act_three_audio_runtime,
        act_two_transition_sounds,
        act_one_sounds,
        act_two_sounds,
        act_three_sounds,
        FIRST_ACT_FINAL_FLOOR,
    )
    pointer = GameplayPointerController(
        map_navigation,
        act_two_interface_input,
        act_two_input_state,
        act_one_sounds,
        act_two_sounds,
    )
    event_gate = ApplicationEventGate(
        act_two_input_state,
        cutscene_skip,
        dev_console,
    )
    modal_events = ApplicationModalController(
        window_state,
        game_surface,
        run_session,
        loading,
        act_two_renderer,
        act_two_input_state,
        menu_runtime,
        act_two_audio_runtime,
        act_three_audio_runtime,
        act_one_sounds,
        act_two_transition_sounds,
        act_two_sounds,
        act_three_sounds,
        death_score_layout,
    )

    while app_runtime.running:
        loading.completed = False
        frame_input = prepare_frame_input(
            game_state,
            app_runtime,
            menu_state,
            menu_layouts,
            dev_console,
            act_two_input_state,
            ground_item_window,
            act_one_sounds,
            act_two_sounds,
        )
        current_act = frame_input.current_act
        continuous_movement_available = (
            frame_input.continuous_movement_available
        )
        movement_profile = frame_input.movement_profile
        menu_visual_theme = frame_input.menu_visual_theme
        active_menu_layouts = frame_input.active_menu_layouts
        console_available = frame_input.console_available

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
                act_two_audio_runtime.reset()
                act_three_audio_runtime.reset()

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
                act_two_input_state.reset_for_loading()
                menu_state.pause_background = None
                menu_state.transition_from_theme = None
                set_default_cursor()
                continue

            gate_result = event_gate.handle(
                event,
                game_state,
                app_runtime,
                current_act,
                continuous_movement_available,
                console_available,
            )
            movement_profile = gate_result.movement_profile
            if gate_result.handled:
                continue

            modal_result = modal_events.handle(
                event,
                MenuActionState(
                    game_state,
                    act_one_camera,
                    act_two_camera,
                    ground_item_window,
                    menu_progress,
                    act_one_music_attempted,
                    act_one_warden_music_attempted,
                    act_one_warden_music_channel,
                ),
                app_runtime,
                menu_state,
                current_act,
                active_menu_layouts,
            )
            modal_state = modal_result.state
            game_state = modal_state.game_state
            act_one_camera = modal_state.act_one_camera
            act_two_camera = modal_state.act_two_camera
            ground_item_window = modal_state.ground_item_window
            menu_progress = modal_state.menu_progress
            act_one_music_attempted = modal_state.act_one_music_attempted
            act_one_warden_music_attempted = (
                modal_state.act_one_warden_music_attempted
            )
            act_one_warden_music_channel = (
                modal_state.act_one_warden_music_channel
            )
            if modal_result.handled:
                continue
            if pointer.handle(
                event,
                game_state,
                app_runtime,
                dev_console,
                window_state.screen,
                game_surface,
                current_act,
                act_one_camera,
                act_two_camera,
                ground_item_window,
                continuous_movement_available,
                movement_profile,
            ):
                continue
            elif event.type == pygame.KEYDOWN:
                game_state = keyboard.handle(
                    event,
                    game_state,
                    app_runtime,
                    menu_state,
                    game_surface,
                    current_act,
                    continuous_movement_available,
                    movement_profile,
                )
                continue
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

        (
            act_one_music_attempted,
            act_one_warden_music_channel,
        ) = frame_updater.advance_shared(
            game_state,
            app_runtime,
            game_surface,
            current_time,
            menu_state.music_volume,
            act_one_music_attempted,
            act_one_warden_music_channel,
        )

        if app_runtime.menu_open:
            menu_runtime.draw(
                window_state.screen,
                game_surface,
                clock,
                game_state,
                app_runtime,
                run_session,
                menu_state,
                menu_visual_theme,
                active_menu_layouts,
                menu_layouts,
                menu_fonts,
                menu_assets,
                menu_progress.highest_act_reached,
                current_time,
                window_state.fullscreen,
            )
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

        frame_state = frame_updater.advance_gameplay(
            game_state,
            app_runtime,
            menu_state,
            menu_progress,
            current_act,
            current_time,
            act_one_music_attempted,
            act_one_warden_music_attempted,
            act_one_warden_music_channel,
            act_two_camera,
        )
        if frame_state.skip_frame:
            continue
        (
            current_act,
            current_act_floor,
            menu_progress,
            act_one_music_attempted,
            act_one_warden_music_attempted,
            act_one_warden_music_channel,
        ) = (
            frame_state.current_act,
            frame_state.current_act_floor,
            frame_state.menu_progress,
            frame_state.act_one_music_attempted,
            frame_state.act_one_warden_music_attempted,
            frame_state.act_one_warden_music_channel,
        )
        gameplay_renderer.draw(
            window_state.screen,
            game_surface,
            clock,
            game_state,
            current_act,
            current_act_floor,
            current_time,
            act_one_camera,
            act_two_camera,
            act_two_input_state,
            ground_item_window,
            continuous_movement_available,
        )

    pygame.quit()
