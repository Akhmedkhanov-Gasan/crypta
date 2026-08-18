import pygame

from acts.act_one.camera import (
    ActOneCamera,
    draw_act_one_camera_view,
    update_act_one_camera,
)
from acts.act_one.settings import (
    FLOOR_INTRO_SUBTITLES,
    PLAYER_STARTING_ATTRIBUTE_RANKS,
    PLAYER_STARTING_STATS,
)
from acts.act_two.settings import (
    CLASS_BASE_ATTRIBUTE_RANKS,
    CLASS_BASE_STATS,
)
from acts.act_two.abilities import (
    select_directional_ability_direction,
)
from acts.act_two.crates import break_crate
from acts.act_two.consumables import (
    FIRE_BOMB,
    POTION,
    advance_fire_zones,
    cancel_fire_bomb_aiming,
    get_act_two_consumable_slots,
    initialize_act_two_consumable_belt,
    is_valid_fire_bomb_target,
    request_fire_bomb_aiming,
    throw_fire_bomb,
)
from acts.act_two.progression import (
    get_act_two_upgrade_order,
    purchase_act_two_upgrade,
)
from acts.act_two.visibility import (
    position_is_visible,
    update_act_two_visibility,
)
from acts.act_two.traps import advance_spike_traps
from acts.act_two.runes import (
    interact_with_rune_pedestal,
    rune_pedestal_is_at,
    rune_wall_is_at,
    strike_wall_rune,
)
from acts.act_two.treasury import (
    activate_treasury_trial,
    purchase_treasury_reward_upgrade,
    treasury_chest_is_at,
    update_treasury_trial,
)
from acts.act_two.presentation.camera import (
    ActTwoCamera,
    act_two_screen_to_cell,
    act_two_world_surface_size,
    draw_act_two_camera_view,
    update_act_two_camera,
)
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
from game.progress_store import (
    load_progress,
    record_act_reached,
    select_menu_theme,
)
from acts.act_two.navigation import find_act_two_path
from game.progression import apply_attribute_upgrade
from acts.player_stats import (
    apply_attribute_rank_transition,
    apply_player_stat_transition,
)
from levels import FLOOR_CONFIGS
from logic import get_enemy_occupied_positions
from rendering import (
    CLASS_SELECTION_READY_MS,
    FLOOR_TRANSITION_CLOSE_END_MS,
    FLOOR_TRANSITION_END_MS,
    draw_act_three_awakening,
    draw_act_one_upgrade_screen,
    draw_act_three_debug_class_selection,
    draw_act_three_gameplay,
    draw_attack_markers,
    draw_act_one_boss_effects,
    draw_act_one_atmosphere,
    draw_act_two_atmosphere,
    draw_act_two_ability_preview,
    draw_act_two_arcane_burst_effect,
    draw_act_two_fog_of_war,
    draw_fire_bomb_flight,
    draw_fire_bomb_targeting,
    draw_fire_zones,
    draw_act_one_player_attack_effect,
    draw_act_two_player_attack_effect,
    draw_act_two_player_feedback_overlay,
    draw_act_two_wait_indicator,
    draw_act_two_power_cleave_effect,
    draw_act_two_rune_room,
    draw_act_two_upgrade_screen,
    draw_act_two_spike_traps,
    draw_act_two_treasury,
    draw_act_one_pickup_effect,
    draw_act_two_pickup_effect,
    draw_boss_door,
    draw_breakable_crate,
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
    get_act_one_upgrade_card_rectangles,
    get_act_two_upgrade_card_rectangles,
    get_act_two_belt_slot_rectangles,
    get_act_two_sidebar_button_rectangles,
    get_class_selection_rectangles,
    load_act_one_fonts,
    load_act_one_gameplay_assets,
    load_act_three_fonts,
    load_act_three_gameplay_assets,
    load_act_three_transition_assets,
    load_act_two_fonts,
    load_act_two_sprites,
    load_menu_assets,
)
from presentation.layout import (
    ACT_THREE_AWAKENING_END_MS,
    AWAKENING_HOLD_END_MS,
    AWAKENING_SECOND_OPEN_START_MS,
    ACT_ONE_MENU_MUSIC_PATH,
    ACT_ONE_MUSIC_PATH,
    ACT_ONE_WARDEN_MUSIC_PATH,
    ACT_TWO_MENU_MUSIC_PATH,
    ACT_ONE_SOUNDS_PATH,
    ACT_TWO_MUSIC_PATH,
    ACT_TWO_SOUNDS_PATH,
    ACT_THREE_MUSIC_PATH,
    CLASS_SELECTION_CHOICE_END_MS,
)
from presentation.audio import (
    ActOneSoundBank,
    ActTwoSoundBank,
    ActTwoTransitionSoundBank,
    warden_has_been_defeated,
    warden_music_should_play,
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
    FPS,
    GAME_HEIGHT,
    GAME_WIDTH,
    INITIAL_WINDOW_SCALE,
)
from systems.player_actions import (
    break_secret_passage,
    open_chest,
    try_move_player,
    try_use_potion,
)
from systems.player_combat import (
    perform_archer_attack,
    perform_basic_attack,
    perform_summoner_attack,
    perform_warlock_attack,
    remove_enemy_corpses_at_position,
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
_ACT_TWO_CONSUMABLE_KEY_ORDER = (
    pygame.K_1,
    pygame.K_2,
    pygame.K_3,
    pygame.K_4,
    pygame.K_5,
)
_ACT_TWO_CONSUMABLE_KEYS = {
    key: slot_index
    for slot_index, key in enumerate(_ACT_TWO_CONSUMABLE_KEY_ORDER)
}


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


_AMBIENT_MARGIN_CACHE = {}


def _draw_ambient_margin(window, rectangle):
    if rectangle.width <= 0 or rectangle.height <= 0:
        return

    cache_key = rectangle.size
    cached_margin = _AMBIENT_MARGIN_CACHE.get(cache_key)
    if cached_margin is not None:
        window.blit(cached_margin, rectangle)
        return

    margin = pygame.Surface(rectangle.size)
    margin.fill((6, 8, 10))
    brick_width = 72
    brick_height = 48
    for row, y in enumerate(range(0, rectangle.height, brick_height)):
        pygame.draw.line(
            margin,
            (14, 18, 20),
            (0, y),
            (rectangle.width, y),
        )
        offset = -(brick_width // 2) if row % 2 else 0
        for x in range(offset, rectangle.width, brick_width):
            pygame.draw.line(
                margin,
                (11, 15, 17),
                (x, y),
                (x, min(rectangle.height, y + brick_height)),
            )
    shade = pygame.Surface(rectangle.size, pygame.SRCALPHA)
    for x in range(rectangle.width):
        distance_from_game = rectangle.width - x
        alpha = min(178, 70 + distance_from_game // 3)
        pygame.draw.line(
            shade,
            (0, 0, 0, alpha),
            (x, 0),
            (x, rectangle.height),
        )
    margin.blit(shade, (0, 0))
    _AMBIENT_MARGIN_CACHE.clear()
    _AMBIENT_MARGIN_CACHE[cache_key] = margin
    window.blit(margin, rectangle)


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
    offset_x = window_width - scaled_width
    offset_y = (window_height - scaled_height) // 2

    window.fill(BACKGROUND_COLOR)
    if offset_x > 0:
        _draw_ambient_margin(
            window,
            pygame.Rect(0, offset_y, offset_x, scaled_height),
        )
    if offset_y > 0:
        pygame.draw.rect(
            window,
            (6, 8, 10),
            (offset_x, 0, scaled_width, offset_y),
        )
        pygame.draw.rect(
            window,
            (6, 8, 10),
            (
                offset_x,
                offset_y + scaled_height,
                scaled_width,
                window_height - scaled_height - offset_y,
            ),
        )
    window.blit(scaled_surface, (offset_x, offset_y))
    pygame.display.flip()


def _complete_class_selection(game_state):
    chosen_class = game_state.class_selection_choice
    if chosen_class is None:
        return

    game_state.floor_index += 1
    game_state.floor = create_floor_state(game_state.floor_index)
    clear_archer_barrage_zone(game_state)
    clear_berserker_crushing_leap(game_state)
    game_state.player.key_count = 0
    initialize_act_two_consumable_belt(game_state.player)
    game_state.class_selection_open = False
    game_state.class_transition_started_at = 0
    game_state.class_selection_choice = None
    game_state.class_selection_choice_started_at = 0
    game_state.player_attack_targets = []
    cancel_fire_bomb_aiming(game_state)
    add_log_message(
        game_state.combat_log,
        f"The hero becomes a {chosen_class}.",
    )
    add_log_message(
        game_state.combat_log,
        "Act II begins. The world gains shape.",
    )


def window_to_game_position(window, window_position):
    window_width, window_height = window.get_size()
    scale = min(
        window_width / GAME_WIDTH,
        window_height / GAME_HEIGHT,
    )
    scaled_width = int(GAME_WIDTH * scale)
    scaled_height = int(GAME_HEIGHT * scale)
    offset_x = window_width - scaled_width
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
        cancel_fire_bomb_aiming(game_state)
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


_ACT_TWO_MOVEMENT_KEYS = frozenset(
    (
        pygame.K_w,
        pygame.K_a,
        pygame.K_s,
        pygame.K_d,
        pygame.K_UP,
        pygame.K_LEFT,
        pygame.K_DOWN,
        pygame.K_RIGHT,
    )
)
_ACT_ONE_POTION_KEYS = {
    pygame.K_1: 0,
    pygame.K_KP1: 0,
    pygame.K_2: 1,
    pygame.K_KP2: 1,
    pygame.K_3: 2,
    pygame.K_KP3: 2,
    pygame.K_4: 3,
    pygame.K_KP4: 3,
    pygame.K_5: 4,
    pygame.K_KP5: 4,
    pygame.K_6: 5,
    pygame.K_KP6: 5,
}
_ACT_TWO_MOVE_REPEAT_DELAY_MS = 190
_ACT_TWO_MOVE_REPEAT_INTERVAL_MS = 175


def _movement_direction_for_keys(keys):
    left = bool(keys & {pygame.K_a, pygame.K_LEFT})
    right = bool(keys & {pygame.K_d, pygame.K_RIGHT})
    up = bool(keys & {pygame.K_w, pygame.K_UP})
    down = bool(keys & {pygame.K_s, pygame.K_DOWN})
    return int(right) - int(left), int(down) - int(up)


def _act_two_visual_direction(direction):
    column_change, row_change = direction
    if row_change:
        return 0, 1 if row_change > 0 else -1
    if column_change:
        return 1 if column_change > 0 else -1, 0
    return 0, 1


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
    act_one_gameplay_assets = load_act_one_gameplay_assets()
    title_font = act_one_fonts["title"]
    font = act_one_fonts["status"]
    log_font = act_one_fonts["text"]
    act_two_fonts = load_act_two_fonts()
    act_two_sprites = load_act_two_sprites()
    act_three_fonts = load_act_three_fonts()
    menu_fonts = {
        1: act_one_fonts,
        2: act_two_fonts,
        3: {
            **act_three_fonts,
            "status": act_three_fonts["sidebar_heading"],
        },
    }
    act_three_gameplay_assets = (
        load_act_three_gameplay_assets()
    )
    act_three_transition_assets = (
        load_act_three_transition_assets()
    )
    menu_assets = load_menu_assets()
    act_one_sounds = ActOneSoundBank.load(ACT_ONE_SOUNDS_PATH)
    act_two_transition_sounds = ActTwoTransitionSoundBank.load(
        ACT_TWO_SOUNDS_PATH
    )
    act_two_sounds = ActTwoSoundBank.load(ACT_TWO_SOUNDS_PATH)
    if pygame.mixer.get_init() is not None:
        pygame.mixer.set_reserved(2)

    game_state = create_game_state()
    act_one_camera = ActOneCamera()
    act_two_camera = ActTwoCamera()
    act_one_world_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    act_two_world_surface = None
    act_two_map_surface = None
    act_two_map_cache_key = None
    menu_progress = load_progress()
    progress_tracking_enabled = True
    menu_state = MenuState(menu_theme=menu_progress.menu_theme)
    act_one_sounds.set_master_volume(menu_state.effects_volume)
    act_two_transition_sounds.set_master_volume(
        menu_state.effects_volume
    )
    act_two_sounds.set_master_volume(menu_state.effects_volume)
    menu_open = True
    game_started = False
    menu_started_at = pygame.time.get_ticks()
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
    fullscreen = False
    running = True
    act_two_held_movement_keys = set()
    act_two_held_direction = (0, 0)
    act_two_next_held_move_at = 0
    act_two_auto_move_target = None
    act_two_auto_move_floor_index = None
    act_two_next_auto_move_at = 0

    while running:
        current_act = FLOOR_CONFIGS[game_state.floor_index]["act"]
        continuous_move_time = pygame.time.get_ticks()
        continuous_movement_available = (
            current_act == 2
            and not menu_open
            and game_state.floor_transition_started_at < 0
            and not game_state.class_selection_open
            and not game_state.upgrade_screen_open
            and not game_state.subclass_selection_open
            and not game_state.player.directional_ability_aiming
            and not game_state.player.act_two.fire_bomb_aiming
            and game_state.player.health > 0
            and not game_state.game_won
        )
        held_direction = _movement_direction_for_keys(
            act_two_held_movement_keys
        )
        if continuous_movement_available and held_direction != (0, 0):
            act_two_auto_move_target = None
            act_two_auto_move_floor_index = None
            if held_direction != act_two_held_direction:
                act_two_held_direction = held_direction
                act_two_next_held_move_at = (
                    continuous_move_time + _ACT_TWO_MOVE_REPEAT_DELAY_MS
                )
            elif continuous_move_time >= act_two_next_held_move_at:
                pygame.event.post(
                    pygame.event.Event(
                        pygame.KEYDOWN,
                        key=pygame.K_UNKNOWN,
                        movement_direction=held_direction,
                        automatic_movement=True,
                    )
                )
                act_two_next_held_move_at = (
                    continuous_move_time + _ACT_TWO_MOVE_REPEAT_INTERVAL_MS
                )
        else:
            act_two_held_direction = (0, 0)

        if (
            continuous_movement_available
            and not act_two_held_movement_keys
            and act_two_auto_move_target is not None
        ):
            if (
                act_two_auto_move_floor_index != game_state.floor_index
                or (
                    game_state.floor.player_column,
                    game_state.floor.player_row,
                )
                == act_two_auto_move_target
            ):
                act_two_auto_move_target = None
                act_two_auto_move_floor_index = None
            elif continuous_move_time >= act_two_next_auto_move_at:
                automatic_path = find_act_two_path(
                    game_state.floor,
                    act_two_auto_move_target,
                )
                if automatic_path:
                    next_position = automatic_path[0]
                    automatic_direction = (
                        next_position[0] - game_state.floor.player_column,
                        next_position[1] - game_state.floor.player_row,
                    )
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=pygame.K_UNKNOWN,
                            movement_direction=automatic_direction,
                            automatic_movement=True,
                        )
                    )
                    act_two_next_auto_move_at = (
                        continuous_move_time
                        + _ACT_TWO_MOVE_REPEAT_INTERVAL_MS
                    )
                else:
                    act_two_auto_move_target = None
                    act_two_auto_move_floor_index = None

        for event in pygame.event.get():
            if event.type == pygame.WINDOWFOCUSLOST:
                act_two_held_movement_keys.clear()
                act_two_held_direction = (0, 0)
                continue
            if (
                event.type == pygame.KEYUP
                and event.key in _ACT_TWO_MOVEMENT_KEYS
            ):
                act_two_held_movement_keys.discard(event.key)
                if not act_two_held_movement_keys:
                    act_two_held_direction = (0, 0)
                continue
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
                    menu_progress.highest_act_reached,
                )

                if menu_action == "resume":
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
                    menu_open = False
                    game_started = True
                elif menu_action == "abandon_run":
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
                    if (
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
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and current_act == 2
                and not game_state.class_selection_open
                and not game_state.upgrade_screen_open
                and (
                    game_mouse_position := window_to_game_position(
                        screen,
                        event.pos,
                    )
                )
                is not None
                and (
                    clicked_sidebar_button := next(
                        (
                            button_name
                            for button_name, rectangle in (
                                get_act_two_sidebar_button_rectangles().items()
                            )
                            if rectangle.collidepoint(game_mouse_position)
                        ),
                        None,
                    )
                )
                is not None
            ):
                if clicked_sidebar_button == "stats":
                    game_state.act_two_stats_open = (
                        not game_state.act_two_stats_open
                    )
                    continue
                if clicked_sidebar_button == "placeholder":
                    continue
                if clicked_sidebar_button == "settings":
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.KEYDOWN,
                            key=pygame.K_ESCAPE,
                        )
                    )
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

                act_two_upgrade_screen = (
                    FLOOR_CONFIGS[game_state.floor_index]["act"] == 2
                    and game_state.player.player_class in (
                        "warrior",
                        "rogue",
                        "mage",
                    )
                    and game_state.player.subclass is None
                )
                show_generic_intelligence = (
                    FLOOR_CONFIGS[game_state.floor_index]["act"] >= 3
                )
                generic_upgrade_keys = {
                    "strength": pygame.K_1,
                    "dexterity": pygame.K_2,
                    "vitality": (
                        pygame.K_4
                        if show_generic_intelligence
                        else pygame.K_3
                    ),
                }
                if show_generic_intelligence:
                    generic_upgrade_keys["intelligence"] = pygame.K_3
                upgrade_keys = (
                    {
                        upgrade: getattr(pygame, f"K_{index + 1}")
                        for index, upgrade in enumerate(
                            get_act_two_upgrade_order(
                                game_state.player.player_class
                            )
                        )
                    }
                    if act_two_upgrade_screen
                    else generic_upgrade_keys
                )
                if current_act == 1:
                    card_rectangles = (
                        get_act_one_upgrade_card_rectangles()
                    )
                elif act_two_upgrade_screen:
                    card_rectangles = get_act_two_upgrade_card_rectangles(
                        game_state.player.player_class
                    )
                else:
                    card_rectangles = get_upgrade_card_rectangles(
                        show_generic_intelligence
                    )
                for upgrade_name, rectangle in (
                    card_rectangles.items()
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

                if game_state.class_selection_choice is not None:
                    continue

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
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 3
                and current_act == 2
                and game_state.player.act_two.fire_bomb_aiming
            ):
                cancel_fire_bomb_aiming(game_state)
                continue
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and current_act == 2
                and not game_state.class_selection_open
                and not game_state.upgrade_screen_open
                and game_state.player.health > 0
            ):
                game_mouse_position = window_to_game_position(
                    screen,
                    event.pos,
                )
                belt_slot_clicked = False
                if game_mouse_position is not None:
                    for slot_index, rectangle in enumerate(
                        get_act_two_belt_slot_rectangles()
                    ):
                        if not rectangle.collidepoint(game_mouse_position):
                            continue
                        pygame.event.post(
                            pygame.event.Event(
                                pygame.KEYDOWN,
                                key=(
                                    _ACT_TWO_CONSUMABLE_KEY_ORDER[slot_index]
                                ),
                            )
                        )
                        belt_slot_clicked = True
                        break
                if belt_slot_clicked:
                    continue
                target_cell = (
                    act_two_screen_to_cell(
                        game_mouse_position,
                        act_two_camera,
                    )
                    if game_mouse_position is not None
                    else None
                )
                if game_state.player.act_two.fire_bomb_aiming:
                    if is_valid_fire_bomb_target(
                        game_state,
                        target_cell,
                    ):
                        pygame.event.post(
                            pygame.event.Event(
                                pygame.KEYDOWN,
                                key=pygame.K_UNKNOWN,
                                fire_bomb_target=target_cell,
                                fire_bomb_slot=(
                                    game_state.player.act_two.fire_bomb_aiming_slot
                                ),
                            )
                        )
                    continue
                if (
                    target_cell is not None
                    and target_cell in game_state.floor.visible_cells
                ):
                    automatic_path = find_act_two_path(
                        game_state.floor,
                        target_cell,
                    )
                    if automatic_path:
                        act_two_auto_move_target = target_cell
                        act_two_auto_move_floor_index = (
                            game_state.floor_index
                        )
                        act_two_next_auto_move_at = 0
                    else:
                        act_two_auto_move_target = None
                        act_two_auto_move_floor_index = None
            elif event.type == pygame.KEYDOWN:
                automatic_movement = getattr(
                    event,
                    "automatic_movement",
                    False,
                )
                if not automatic_movement:
                    act_two_auto_move_target = None
                    act_two_auto_move_floor_index = None
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

                if event.key == pygame.K_F1:
                    if (
                        act_three_music_attempted
                        and pygame.mixer.get_init() is not None
                    ):
                        pygame.mixer.music.stop()
                    act_three_music_attempted = False
                    progress_tracking_enabled = False
                    game_state = create_game_state(
                        floor_index=FIRST_ACT_FINAL_FLOOR,
                        opening_message=(
                            "Debug: replay the Act II awakening."
                        ),
                    )
                    game_state.class_selection_open = True
                    game_state.class_transition_started_at = (
                        pygame.time.get_ticks()
                    )
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
                            apply_attribute_rank_transition(
                                game_state.player,
                                PLAYER_STARTING_ATTRIBUTE_RANKS,
                                CLASS_BASE_ATTRIBUTE_RANKS[player_class],
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
                    if game_state.class_selection_choice is not None:
                        continue
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
                    apply_attribute_rank_transition(
                        game_state.player,
                        PLAYER_STARTING_ATTRIBUTE_RANKS,
                        CLASS_BASE_ATTRIBUTE_RANKS[chosen_class],
                    )
                    game_state.class_selection_choice = chosen_class
                    game_state.class_selection_choice_started_at = (
                        pygame.time.get_ticks()
                    )
                    act_two_transition_sounds.play("class_select")
                    continue

                if game_state.upgrade_screen_open:
                    current_upgrade_act = FLOOR_CONFIGS[
                        game_state.floor_index
                    ]["act"]
                    act_two_upgrade_screen = (
                        current_upgrade_act == 2
                        and game_state.player.player_class in (
                            "warrior",
                            "rogue",
                            "mage",
                        )
                        and game_state.player.subclass is None
                    )
                    if act_two_upgrade_screen and event.key in (
                        pygame.K_1,
                        pygame.K_KP1,
                        pygame.K_2,
                        pygame.K_KP2,
                        pygame.K_3,
                        pygame.K_KP3,
                        pygame.K_4,
                        pygame.K_KP4,
                    ):
                        upgrade_index = {
                            pygame.K_1: 0,
                            pygame.K_KP1: 0,
                            pygame.K_2: 1,
                            pygame.K_KP2: 1,
                            pygame.K_3: 2,
                            pygame.K_KP3: 2,
                            pygame.K_4: 3,
                            pygame.K_KP4: 3,
                        }[event.key]
                        upgrade = get_act_two_upgrade_order(
                            game_state.player.player_class
                        )[upgrade_index]
                        if game_state.upgrade_reward_pending:
                            (
                                upgraded,
                                game_state.upgrade_message,
                            ) = purchase_treasury_reward_upgrade(
                                game_state,
                                upgrade,
                            )
                        else:
                            game_state.upgrade_message = (
                                purchase_act_two_upgrade(
                                    game_state.player,
                                    upgrade,
                                )
                            )
                        add_log_message(
                            game_state.combat_log,
                            game_state.upgrade_message,
                        )
                        continue
                    attribute_keys = {
                        pygame.K_1: "strength",
                        pygame.K_KP1: "strength",
                        pygame.K_2: "dexterity",
                        pygame.K_KP2: "dexterity",
                        pygame.K_3: "vitality",
                        pygame.K_KP3: "vitality",
                    }
                    if FLOOR_CONFIGS[game_state.floor_index]["act"] >= 3:
                        attribute_keys.update(
                            {
                                pygame.K_3: "intelligence",
                                pygame.K_KP3: "intelligence",
                                pygame.K_4: "vitality",
                                pygame.K_KP4: "vitality",
                            }
                        )
                    if event.key in attribute_keys:
                        attribute = attribute_keys[event.key]
                        if (
                            current_upgrade_act == 1
                            and game_state.act_one_upgrades_remaining <= 0
                        ):
                            game_state.upgrade_message = (
                                "All blessings chosen. Press Enter."
                            )
                        elif (
                            current_upgrade_act != 1
                            and game_state.player.gold_count <= 0
                        ):
                            game_state.upgrade_message = "Not enough gold."
                        elif apply_attribute_upgrade(
                            game_state.player,
                            attribute,
                        ):
                            if current_upgrade_act == 1:
                                game_state.act_one_upgrades_remaining -= 1
                            else:
                                game_state.player.gold_count -= 1
                            game_state.upgrade_message = (
                                f"{attribute.title()} increased."
                            )
                            add_log_message(
                                game_state.combat_log,
                                game_state.upgrade_message,
                            )
                            if (
                                current_upgrade_act == 1
                                and game_state.act_one_upgrades_remaining <= 0
                            ):
                                _finish_upgrade_descent(
                                    game_state,
                                    pygame.time.get_ticks(),
                                )
                        else:
                            game_state.upgrade_message = (
                                f"{attribute.title()} is capped."
                            )
                    elif event.key in (
                        pygame.K_RETURN,
                        pygame.K_KP_ENTER,
                    ) and (
                        not game_state.upgrade_reward_pending
                        and (
                            current_upgrade_act != 1
                            or game_state.act_one_upgrades_remaining <= 0
                        )
                    ):
                        _finish_upgrade_descent(
                            game_state,
                            pygame.time.get_ticks(),
                        )

                    continue

                game_state.clear_events()
                fire_bomb_target = getattr(
                    event,
                    "fire_bomb_target",
                    None,
                )
                fire_bomb_slot = getattr(
                    event,
                    "fire_bomb_slot",
                    None,
                )
                consumable_slot = (
                    _ACT_TWO_CONSUMABLE_KEYS.get(event.key)
                    if current_act == 2
                    else None
                )
                act_one_potion_slot = (
                    _ACT_ONE_POTION_KEYS.get(event.key)
                    if current_act == 1
                    else None
                )
                consumable_slots = get_act_two_consumable_slots(
                    game_state.player
                )
                selected_consumable = (
                    consumable_slots[consumable_slot]
                    if consumable_slot is not None
                    else None
                )
                if (
                    current_act == 2
                    and game_state.player.act_two.fire_bomb_aiming
                    and fire_bomb_target is None
                ):
                    if (
                        event.key == pygame.K_ESCAPE
                        or selected_consumable == FIRE_BOMB
                    ):
                        cancel_fire_bomb_aiming(game_state)
                    continue
                if selected_consumable == FIRE_BOMB:
                    act_two_held_movement_keys.clear()
                    act_two_held_direction = (0, 0)
                    request_fire_bomb_aiming(
                        game_state,
                        consumable_slot,
                    )
                    continue

                column_change = 0
                row_change = 0
                movement_direction = getattr(
                    event,
                    "movement_direction",
                    None,
                )
                if (
                    current_act == 2
                    and event.key in _ACT_TWO_MOVEMENT_KEYS
                    and not automatic_movement
                ):
                    act_two_held_movement_keys.add(event.key)
                    movement_direction = _movement_direction_for_keys(
                        act_two_held_movement_keys
                    )
                    act_two_held_direction = movement_direction
                    act_two_next_held_move_at = (
                        pygame.time.get_ticks()
                        + _ACT_TWO_MOVE_REPEAT_DELAY_MS
                    )

                if movement_direction is not None:
                    column_change, row_change = movement_direction
                    game_state.player.facing_direction = (
                        _act_two_visual_direction(movement_direction)
                    )
                elif event.key in (pygame.K_w, pygame.K_UP):
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
                if (
                    directional_ability_cast
                    and FLOOR_CONFIGS[game_state.floor_index]["act"] == 2
                    and game_state.player.player_class in ("warrior", "mage")
                    and game_state.player.subclass is None
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
                    act_two_held_movement_keys.clear()
                    act_two_held_direction = (0, 0)
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
                if current_act == 2 and not player_waited:
                    game_state.player.act_two.wait_effect_started_at = -1
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
                target_breakable_crate = next(
                    (
                        crate
                        for crate in game_state.floor.breakable_crates
                        if (
                            not crate.is_broken
                            and (crate.column, crate.row)
                            == (new_column, new_row)
                        )
                    ),
                    None,
                )
                target_treasury_chest = (
                    player_tried_to_move
                    and treasury_chest_is_at(
                        game_state,
                        (new_column, new_row),
                    )
                )
                target_rune_wall = (
                    player_tried_to_move
                    and rune_wall_is_at(
                        game_state,
                        (new_column, new_row),
                    )
                )
                target_rune_pedestal = (
                    player_tried_to_move
                    and rune_pedestal_is_at(
                        game_state,
                        (new_column, new_row),
                    )
                )
                target_secret_wall = (
                    player_tried_to_move
                    and 0 <= new_row < len(game_state.floor["map"])
                    and 0
                    <= new_column
                    < len(game_state.floor["map"][new_row])
                    and game_state.floor["map"][new_row][new_column]
                    == "S"
                )
                player_acted = False
                game_state.player_attack_targets = []

                if fire_bomb_target is not None and fire_bomb_slot is not None:
                    player_acted = throw_fire_bomb(
                        game_state,
                        fire_bomb_slot,
                        fire_bomb_target,
                        pygame.time.get_ticks(),
                    )
                elif (
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
                    if player_acted:
                        ability_started_at = pygame.time.get_ticks()
                        game_state.player.attack_animation_started_at = (
                            ability_started_at
                        )
                        if current_act == 2:
                            game_state.player.act_two.ability_effect_started_at = (
                                ability_started_at
                            )
                            game_state.player.act_two.ability_effect_direction = (
                                column_change,
                                row_change,
                            )
                elif (
                    current_act == 2
                    and selected_consumable == POTION
                ):
                    player_acted = try_use_potion(
                        game_state,
                        consumable_slot,
                    )
                    if player_acted:
                        game_state.player.potion_effect_started_at = (
                            pygame.time.get_ticks()
                        )
                elif (
                    current_act == 1
                    and act_one_potion_slot is not None
                    and act_one_potion_slot
                    < game_state.player.potion_count
                ):
                    player_acted = try_use_potion(game_state)
                    if player_acted:
                        game_state.player.potion_effect_started_at = (
                            pygame.time.get_ticks()
                        )
                elif current_act >= 3 and event.key == pygame.K_h:
                    player_acted = try_use_potion(game_state)
                    if player_acted:
                        game_state.player.potion_effect_started_at = (
                            pygame.time.get_ticks()
                        )
                elif player_waited:
                    if current_act == 2:
                        game_state.player.act_two.wait_effect_started_at = (
                            pygame.time.get_ticks()
                        )
                    player_acted = True
                elif player_tried_to_move:
                    if current_act == 2:
                        movement_attempt_started_at = pygame.time.get_ticks()
                        attempted_direction = (
                            column_change,
                            row_change,
                        )
                        game_state.player.act_two_movement_started_at = 0
                        game_state.player.act_two_movement_origin = None
                        game_state.player.act_two_facing_direction = (
                            _act_two_visual_direction(attempted_direction)
                        )
                        game_state.player.act_two_blocked_movement_started_at = (
                            movement_attempt_started_at
                        )
                        game_state.player.act_two_blocked_movement_direction = (
                            attempted_direction
                        )
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
                    elif target_rune_wall:
                        player_acted = strike_wall_rune(
                            game_state,
                            (new_column, new_row),
                            pygame.time.get_ticks(),
                        )
                    elif target_rune_pedestal:
                        player_acted = interact_with_rune_pedestal(
                            game_state
                        )
                    elif target_treasury_chest:
                        player_acted = activate_treasury_trial(
                            game_state
                        )
                    elif target_chest:
                        player_acted = open_chest(
                            game_state,
                            target_chest,
                            pygame.time.get_ticks(),
                        )
                    elif target_breakable_crate:
                        player_acted = break_crate(
                            game_state,
                            target_breakable_crate,
                        )
                        if player_acted:
                            game_state.player.attack_animation_started_at = (
                                pygame.time.get_ticks()
                            )
                    elif target_secret_wall:
                        player_acted = break_secret_passage(
                            game_state,
                            new_column,
                            new_row,
                        )
                        if player_acted:
                            game_state.player.attack_animation_started_at = (
                                pygame.time.get_ticks()
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
                    advance_spike_traps(game_state)
                    update_treasury_trial(game_state)
                    if game_state.player.health > 0:
                        resolve_enemy_turn(
                            game_state,
                            player_position_before_action,
                            rogue_ability_activated,
                        )
                    if current_act == 2:
                        advance_fire_zones(game_state)
                    update_treasury_trial(game_state)
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
                    if current_act == 2 and game_state.player.health <= 0:
                        remove_enemy_corpses_at_position(
                            game_state.floor,
                            (
                                game_state.floor.player_column,
                                game_state.floor.player_row,
                            ),
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
                                _act_two_visual_direction(
                                    (
                                        hero_move_event.destination[0]
                                        - hero_move_event.origin[0],
                                        hero_move_event.destination[1]
                                        - hero_move_event.origin[1],
                                    )
                                )
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
                        elif enemy.name in healed_enemy_names:
                            enemy.attack_effect_mode = "heal"
                            enemy.attack_effect_positions = ()
                        if (
                            enemy.type == "warden"
                            and enemy.second_phase_announced
                            and enemy.phase_transition_started_at < 0
                        ):
                            enemy.phase_transition_started_at = (
                                enemy_movement_started_at
                            )
                    if current_act == 1:
                        act_one_sounds.play_events(game_state.events)
                    elif current_act == 2:
                        if any(
                            emitted_event.target == "hero"
                            and emitted_event.type
                            in (GameEventType.HIT, GameEventType.DODGE)
                            for emitted_event in game_state.events
                        ):
                            act_two_auto_move_target = None
                            act_two_auto_move_floor_index = None
                        act_two_sounds.play_events(
                            game_state.events,
                            game_state.player.player_class,
                            game_state.floor,
                        )
        if (
            game_state.upgrade_screen_open
            and game_state.player.gold_count <= 0
            and FLOOR_CONFIGS[game_state.floor_index]["act"] != 1
        ):
            _finish_upgrade_descent(
                game_state,
                pygame.time.get_ticks(),
            )

        current_time = pygame.time.get_ticks()
        _advance_floor_transition(game_state, current_time)

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
                        pygame.mixer.music.load(
                            str(ACT_TWO_MUSIC_PATH)
                        )
                        pygame.mixer.music.set_volume(
                            menu_state.music_volume
                        )
                        pygame.mixer.music.play(-1, fade_ms=1400)
                    except pygame.error as audio_error:
                        add_log_message(
                            game_state.combat_log,
                            f"Act II music unavailable: {audio_error}",
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

        if menu_open:
            menu_visual_theme = (
                FLOOR_CONFIGS[game_state.floor_index]["act"]
                if game_started
                else menu_state.menu_theme
            )
            should_play_act_one_menu_music = (
                not game_started and menu_visual_theme == 1
            )
            should_play_act_two_menu_music = (
                not game_started and menu_visual_theme == 2
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
                    pygame.mixer.music.load(
                        str(ACT_ONE_MENU_MUSIC_PATH)
                    )
                    pygame.mixer.music.set_volume(
                        menu_state.music_volume
                    )
                    pygame.mixer.music.play(-1, fade_ms=1200)
                except pygame.error as audio_error:
                    add_log_message(
                        game_state.combat_log,
                        f"Act I menu music unavailable: {audio_error}",
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
                    pygame.mixer.music.load(
                        str(ACT_TWO_MENU_MUSIC_PATH)
                    )
                    pygame.mixer.music.set_volume(
                        menu_state.music_volume
                    )
                    pygame.mixer.music.play(-1, fade_ms=1200)
                except pygame.error as audio_error:
                    add_log_message(
                        game_state.combat_log,
                        f"Act II menu music unavailable: {audio_error}",
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
            draw_menu(
                game_surface,
                menu_fonts[menu_visual_theme],
                menu_state,
                current_time - menu_started_at,
                game_started,
                fullscreen,
                menu_assets,
                menu_visual_theme,
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
            act_one_music_attempted = False
            act_two_music_attempted = False
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

        if (
            game_state.class_selection_open
            and game_state.class_selection_choice_started_at > 0
            and current_time
            - game_state.class_selection_choice_started_at
            >= CLASS_SELECTION_CHOICE_END_MS
        ):
            _complete_class_selection(game_state)

        current_act = FLOOR_CONFIGS[game_state.floor_index]["act"]
        current_act_floor = FLOOR_CONFIGS[game_state.floor_index][
            "act_floor"
        ]
        act_two_sounds.update_fire_bomb_audio(
            game_state.floor if current_act == 2 else None,
            current_time,
        )
        warden_fight_started = warden_music_should_play(
            game_state.floor
        )
        warden_defeated = warden_has_been_defeated(
            game_state.floor
        )
        if (
            current_act == 1
            and warden_fight_started
            and not act_one_warden_music_attempted
        ):
            act_one_warden_music_attempted = True
            try:
                if pygame.mixer.get_init() is None:
                    pygame.mixer.init()
                warden_music = pygame.mixer.Sound(
                    str(ACT_ONE_WARDEN_MUSIC_PATH)
                )
                pygame.mixer.music.fadeout(700)
                act_one_warden_music_channel = pygame.mixer.Channel(0)
                act_one_warden_music_channel.play(
                    warden_music,
                    loops=-1,
                    fade_ms=700,
                )
                act_one_warden_music_channel.set_volume(
                    menu_state.music_volume
                )
            except pygame.error as audio_error:
                add_log_message(
                    game_state.combat_log,
                    f"Warden music unavailable: {audio_error}",
                )
        if (
            current_act == 1
            and warden_defeated
            and act_one_warden_music_channel is not None
        ):
            act_one_warden_music_channel.fadeout(2200)
            act_one_warden_music_channel = None
        if (
            current_act == 1
            and not warden_fight_started
            and not act_one_music_attempted
        ):
            act_one_music_attempted = True
            try:
                if pygame.mixer.get_init() is None:
                    pygame.mixer.init()
                pygame.mixer.music.load(str(ACT_ONE_MUSIC_PATH))
                pygame.mixer.music.set_volume(menu_state.music_volume)
                pygame.mixer.music.play(-1, fade_ms=1400)
            except pygame.error as audio_error:
                add_log_message(
                    game_state.combat_log,
                    f"Act I music unavailable: {audio_error}",
                )
        elif (
            current_act != 1
            and act_one_music_attempted
            and not act_three_music_attempted
        ):
            if pygame.mixer.get_init() is not None:
                pygame.mixer.music.stop()
            act_one_music_attempted = False
        if (
            current_act != 1
            and act_one_warden_music_channel is not None
        ):
            act_one_warden_music_channel.fadeout(500)
            act_one_warden_music_channel = None
            act_one_warden_music_attempted = False
        if (
            current_act == 2
            and not game_state.class_selection_open
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
                pygame.mixer.music.load(str(ACT_TWO_MUSIC_PATH))
                pygame.mixer.music.set_volume(
                    menu_state.music_volume
                )
                pygame.mixer.music.play(-1, fade_ms=700)
            except pygame.error as audio_error:
                add_log_message(
                    game_state.combat_log,
                    f"Act II music unavailable: {audio_error}",
                )
        if current_act == 2:
            update_act_two_visibility(game_state.floor)
        if (
            progress_tracking_enabled
            and current_act > menu_progress.highest_act_reached
        ):
            menu_progress = record_act_reached(
                menu_progress,
                current_act,
            )
            menu_state.menu_theme = menu_progress.menu_theme
        active_status_font = (
            act_two_fonts["status"]
            if current_act >= 2
            else font
        )
        active_heading_font = (
            act_two_fonts["sidebar_heading"]
            if current_act >= 2
            else act_one_fonts["hud"]
        )
        active_text_font = (
            act_two_fonts["log"]
            if current_act == 2
            else act_two_fonts["sidebar_text"]
            if current_act >= 3
            else act_one_fonts["hud_small"]
        )
        active_controls_font = (
            act_two_fonts["sidebar_controls"]
            if current_act >= 2
            else act_one_fonts["controls"]
        )
        active_ability_font = (
            act_two_fonts["ability_text"]
            if current_act == 2
            else active_text_font
        )
        game_surface.fill(BACKGROUND_COLOR)
        if current_act == 1:
            update_act_one_camera(
                act_one_camera,
                game_state.floor["map"],
                game_state.floor["player_column"],
                game_state.floor["player_row"],
                game_state.floor_index,
                current_time,
            )
        if current_act == 2:
            update_act_two_camera(
                act_two_camera,
                game_state.floor["map"],
                game_state.floor["player_column"],
                game_state.floor["player_row"],
                game_state.floor_index,
                current_time,
            )
            world_size = act_two_world_surface_size(
                game_state.floor["map"]
            )
            if (
                act_two_world_surface is None
                or act_two_world_surface.get_size() != world_size
            ):
                act_two_world_surface = pygame.Surface(world_size)
                act_two_map_surface = None
                act_two_map_cache_key = None
            floor_decor_excluded_positions = {
                (
                    game_state.floor.stairs_column,
                    game_state.floor.stairs_row,
                ),
                *(
                    (chest.column, chest.row)
                    for chest in game_state.floor.chests
                ),
                *(
                    (crate.column, crate.row)
                    for crate in game_state.floor.breakable_crates
                ),
                *(
                    (potion.column, potion.row)
                    for potion in game_state.floor.potions
                ),
                *(
                    (trap.column, trap.row)
                    for trap in game_state.floor.spike_traps
                ),
                *game_state.floor.boss_columns,
                *game_state.floor.boss_emitters,
            }
            if game_state.floor.boss_door is not None:
                floor_decor_excluded_positions.add(
                    game_state.floor.boss_door
                )
            if game_state.floor.upgrade_altar is not None:
                floor_decor_excluded_positions.add(
                    game_state.floor.upgrade_altar
                )
            if game_state.floor.treasury_room is not None:
                treasury_room = game_state.floor.treasury_room
                floor_decor_excluded_positions.update(
                    {
                        treasury_room.door_position,
                        treasury_room.chest_position,
                        *treasury_room.statue_positions,
                    }
                )
            if game_state.floor.rune_room is not None:
                rune_room = game_state.floor.rune_room
                floor_decor_excluded_positions.update(
                    {
                        rune_room.door_position,
                        rune_room.pedestal_position,
                        *rune_room.floor_rune_positions,
                    }
                )
            floor_decor_excluded_positions = tuple(
                sorted(floor_decor_excluded_positions)
            )
            map_cache_key = (
                game_state.floor_index,
                game_state.floor.visual_seed,
                tuple(game_state.floor["map"]),
                floor_decor_excluded_positions,
            )
            if act_two_map_cache_key != map_cache_key:
                act_two_map_surface = pygame.Surface(world_size)
                act_two_map_surface.fill(BACKGROUND_COLOR)
                draw_dungeon(
                    act_two_map_surface,
                    game_state.floor["map"],
                    current_act,
                    act_two_sprites,
                    current_act_floor,
                    game_state.floor.visual_seed,
                    floor_decor_excluded_positions,
                )
                act_two_map_cache_key = map_cache_key
            act_two_world_surface.fill(BACKGROUND_COLOR)
            act_two_world_surface.blit(act_two_map_surface, (0, 0))
            world_target = act_two_world_surface
        else:
            world_target = (
                act_one_world_surface
                if current_act == 1
                else game_surface
            )
            world_target.fill(BACKGROUND_COLOR)
            draw_dungeon(
                world_target,
                game_state.floor["map"],
                current_act,
                act_two_sprites,
                current_act_floor,
                game_state.floor.visual_seed,
            )
        draw_act_one_atmosphere(
            world_target,
            current_act,
            game_state.floor["player_column"],
            game_state.floor["player_row"],
            game_state.floor["map"],
            current_act_floor,
            game_state.floor.visual_seed,
            current_time,
        )
        if current_act == 2:
            draw_act_two_atmosphere(
                world_target,
                game_state.floor["player_column"],
                game_state.floor["player_row"],
                game_state.floor["map"],
                current_act_floor,
                game_state.floor.visual_seed,
                current_time,
            )
            draw_act_two_spike_traps(
                world_target,
                game_state.floor.spike_traps,
                act_two_sprites,
                game_state.floor.visible_cells,
                current_time,
            )
            draw_act_two_treasury(
                world_target,
                game_state.floor.treasury_room,
                act_two_sprites,
                game_state.floor.visible_cells,
                current_time,
            )
            draw_act_two_rune_room(
                world_target,
                game_state.floor.rune_room,
                act_two_sprites,
                game_state.floor.visible_cells,
                current_time,
            )
            draw_fire_zones(
                world_target,
                game_state,
                act_two_sprites,
                current_time,
            )
        if current_act != 2:
            draw_map_frame(
                world_target,
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
        if current_act == 2:
            draw_oracle_emitters(
                world_target,
                [
                    position
                    for position in game_state.floor["boss_emitters"]
                    if position_is_visible(
                        game_state.floor,
                        position[0],
                        position[1],
                    )
                ],
                (
                    living_oracle is not None
                    and living_oracle["oracle_awakened"]
                ),
                act_two_sprites,
            )
        act_two_ability_effect_duration = (
            620
            if game_state.player.player_class == "mage"
            else 460
        )
        act_two_ability_effect_elapsed = (
            current_time
            - game_state.player.act_two.ability_effect_started_at
        )
        act_two_ability_effect_active = (
            current_act == 2
            and game_state.player.act_two.ability_effect_started_at > 0
            and game_state.player.act_two.ability_effect_started_at
            == game_state.player.attack_animation_started_at
            and 0
            <= act_two_ability_effect_elapsed
            < act_two_ability_effect_duration
        )
        act_two_targets_belong_to_directional_ability = (
            current_act == 2
            and game_state.player.act_two.ability_effect_started_at > 0
            and game_state.player.act_two.ability_effect_started_at
            == game_state.player.attack_animation_started_at
        )
        act_two_ability_visual_owns_targets = (
            current_act == 2
            and game_state.player.player_class in ("warrior", "mage")
            and (
                game_state.player.directional_ability_aiming
                or act_two_targets_belong_to_directional_ability
            )
        )
        draw_player_attack_markers(
            world_target,
            (
                []
                if act_two_ability_visual_owns_targets
                else
                [
                    position
                    for position in game_state.player_attack_targets
                    if position_is_visible(
                        game_state.floor,
                        position[0],
                        position[1],
                    )
                ]
                if current_act == 2
                else game_state.player_attack_targets
            ),
        )
        if current_act == 2:
            draw_act_two_ability_preview(
                world_target,
                game_state,
                current_time,
            )
        draw_attack_markers(
            world_target,
            game_state.floor["enemies"],
            current_act,
            current_time,
            (
                game_state.floor.visible_cells
                if current_act == 2
                else None
            ),
            (
                (
                    game_state.floor["player_column"],
                    game_state.floor["player_row"],
                )
                if current_act == 2
                else None
            ),
        )
        draw_act_one_boss_effects(
            world_target,
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
                world_target,
                game_state.floor["boss_door"][0],
                game_state.floor["boss_door"][1],
                boss_door_is_open,
            )
        stairs_are_open = not any(
            enemy["health"] > 0
            for enemy in game_state.floor["enemies"]
        )
        if current_act == 2:
            remembered_stairs_open = (
                game_state.floor.act_two_remembered_stairs_open
            )
        else:
            remembered_stairs_open = stairs_are_open
        if remembered_stairs_open is not None:
            draw_stairs(
                world_target,
                game_state.floor["stairs_column"],
                game_state.floor["stairs_row"],
                remembered_stairs_open,
                current_act,
                act_two_sprites,
            )
        for potion in game_state.floor["potions"]:
            if (
                current_act == 2
                and not position_is_visible(
                    game_state.floor,
                    potion["column"],
                    potion["row"],
                )
            ):
                continue
            draw_potion(
                world_target,
                potion["column"],
                potion["row"],
                current_act,
                (
                    act_one_gameplay_assets
                    if current_act == 1
                    else act_two_sprites
                ),
            )
        if current_act == 2:
            for crate in game_state.floor.breakable_crates:
                crate_is_visible = position_is_visible(
                    game_state.floor,
                    crate.column,
                    crate.row,
                )
                remembered_crate = (
                    {
                        "column": crate.column,
                        "row": crate.row,
                        "variant": crate.variant,
                        "is_broken": crate.is_broken,
                        "loot_kind": crate.loot_kind,
                        "loot_available": crate.loot_available,
                    }
                    if crate_is_visible
                    else game_state.floor.act_two_remembered_crates.get(
                        (crate.column, crate.row)
                    )
                )
                if remembered_crate is None:
                    continue
                draw_breakable_crate(
                    world_target,
                    remembered_crate,
                    act_two_sprites,
                )
                if remembered_crate["loot_available"]:
                    draw_loot = (
                        draw_potion
                        if remembered_crate["loot_kind"] == "potion"
                        else draw_coin
                    )
                    draw_loot(
                        world_target,
                        remembered_crate["column"],
                        remembered_crate["row"],
                        current_act,
                        act_two_sprites,
                    )
        for chest in game_state.floor["chests"]:
            remembered_chest = chest
            if current_act == 2:
                chest_is_visible = position_is_visible(
                    game_state.floor,
                    chest["column"],
                    chest["row"],
                )
                if not chest_is_visible:
                    remembered_chest = (
                        game_state.floor.act_two_remembered_chests.get(
                            (chest["column"], chest["row"])
                        )
                    )
                    if remembered_chest is None:
                        continue
            draw_chest(
                world_target,
                remembered_chest,
                current_act,
                act_two_sprites,
                current_time,
            )
            if remembered_chest["loot_available"]:
                if remembered_chest.get("contains") == "potion":
                    draw_potion(
                        world_target,
                        remembered_chest["column"],
                        remembered_chest["row"],
                        current_act,
                        act_two_sprites,
                    )
                else:
                    draw_coin(
                        world_target,
                        remembered_chest["column"],
                        remembered_chest["row"],
                        current_act,
                        act_two_sprites,
                    )
        for dropped_key in game_state.floor["dropped_keys"]:
            if (
                current_act == 2
                and not position_is_visible(
                    game_state.floor,
                    dropped_key[0],
                    dropped_key[1],
                )
            ):
                continue
            draw_key(
                world_target,
                dropped_key[0],
                dropped_key[1],
                current_act,
                act_two_sprites,
            )
        draw_player(
            world_target,
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
            game_state.player.act_two_blocked_movement_started_at,
            game_state.player.act_two_blocked_movement_direction,
        )
        if current_act == 2 and game_state.player.health > 0:
            draw_act_two_wait_indicator(
                world_target,
                game_state.floor.player_column,
                game_state.floor.player_row,
                current_time,
                game_state.player.act_two.wait_effect_started_at,
            )
        for enemy in game_state.floor["enemies"]:
            if (
                current_act == 2
                and not any(
                    position in game_state.floor.visible_cells
                    for position in get_enemy_occupied_positions(enemy)
                )
            ):
                continue
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
                    world_target,
                    enemy,
                    current_act,
                    act_two_sprites,
                    current_time,
                    active_status_font,
                )
        if current_act == 2:
            draw_attack_markers(
                world_target,
                game_state.floor["enemies"],
                current_act,
                current_time,
                game_state.floor.visible_cells,
                (
                    game_state.floor["player_column"],
                    game_state.floor["player_row"],
                ),
                foreground=True,
            )
        draw_act_one_player_attack_effect(
            world_target,
            current_act,
            game_state.floor["player_column"],
            game_state.floor["player_row"],
            game_state.player.act_one_attack_target,
            current_time,
            game_state.player.attack_animation_started_at,
            game_state.player.act_one_attack_was_critical,
        )
        if current_act == 2:
            mage_ability_effect_active = (
                game_state.player.player_class == "mage"
                and act_two_ability_effect_active
            )
            draw_act_two_player_attack_effect(
                world_target,
                game_state.floor["player_column"],
                game_state.floor["player_row"],
                (
                    None
                    if mage_ability_effect_active
                    else game_state.player.act_one_attack_target
                ),
                game_state.player.player_class,
                current_time,
                game_state.player.attack_animation_started_at,
                game_state.player.act_one_attack_was_critical,
            )
            draw_act_two_power_cleave_effect(
                world_target,
                game_state,
                current_time,
            )
            draw_act_two_arcane_burst_effect(
                world_target,
                game_state,
                current_time,
            )
        draw_act_one_pickup_effect(
            world_target,
            current_act,
            game_state.player.act_one_pickup_kind,
            game_state.player.act_one_pickup_origin,
            current_time,
            game_state.player.act_one_pickup_started_at,
        )
        if current_act == 2:
            draw_act_two_pickup_effect(
                world_target,
                act_two_sprites,
                game_state.player.act_two_pickup_kind,
                game_state.player.act_two_pickup_origin,
                current_time,
                game_state.player.act_two_pickup_started_at,
            )
        if current_act == 2:
            draw_oracle_projectiles(
                world_target,
                [
                    projectile
                    for projectile in game_state.floor["projectiles"]
                    if position_is_visible(
                        game_state.floor,
                        projectile["column"],
                        projectile["row"],
                    )
                ],
                act_two_sprites,
            )
            draw_fire_bomb_flight(
                world_target,
                game_state,
                act_two_sprites,
                current_time,
            )
            fire_bomb_mouse_position = window_to_game_position(
                screen,
                pygame.mouse.get_pos(),
            )
            fire_bomb_target = (
                act_two_screen_to_cell(
                    fire_bomb_mouse_position,
                    act_two_camera,
                )
                if fire_bomb_mouse_position is not None
                else None
            )
            draw_fire_bomb_targeting(
                world_target,
                game_state,
                fire_bomb_target,
            )
            draw_act_two_fog_of_war(
                world_target,
                current_act,
                game_state.floor,
            )
            draw_act_two_camera_view(
                game_surface,
                world_target,
                act_two_camera,
            )
        elif current_act == 1:
            draw_act_one_camera_view(
                game_surface,
                act_one_world_surface,
                act_one_camera,
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
                act_two_camera,
            )
        draw_sidebar(
            game_surface,
            active_heading_font,
            active_text_font,
            active_controls_font,
            active_ability_font,
            game_state.combat_log,
            game_state.player.health,
            game_state.player.max_health,
            game_state.player.damage_min,
            game_state.player.damage_max,
            game_state.player.crit_chance,
            game_state.player.dodge_chance,
            game_state.player.critical_damage_multiplier,
            game_state.player.spell_power,
            game_state.player.attribute_ranks,
            game_state.player.potion_count,
            get_act_two_consumable_slots(game_state.player),
            game_state.player.gold_count,
            game_state.player.key_count,
            game_state.player.enemies_defeated,
            game_state.player.player_class,
            game_state.player.level,
            game_state.player.experience,
            game_state.player.ability_kill_charge,
            game_state.player.invisibility_turns,
            game_state.player.directional_ability_aiming,
            game_state.act_two_stats_open,
            window_to_game_position(
                screen,
                pygame.mouse.get_pos(),
            ),
            current_act,
            (
                act_one_gameplay_assets
                if current_act == 1
                else act_two_sprites
            ),
        )
        if current_act >= 3:
            draw_act_three_gameplay(
                game_surface,
                game_state,
                act_three_fonts,
                act_three_gameplay_assets,
                current_time,
                window_to_game_position(
                    screen,
                    pygame.mouse.get_pos(),
                ),
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
            if current_act == 1:
                draw_act_one_upgrade_screen(
                    game_surface,
                    act_one_gameplay_assets["act_one_upgrade"],
                    active_upgrade_text_font,
                    game_state.act_one_upgrades_remaining,
                    game_state.upgrade_message,
                    upgrade_mouse_position,
                )
            elif (
                current_act == 2
                and game_state.player.player_class in (
                    "warrior",
                    "rogue",
                    "mage",
                )
                and game_state.player.subclass is None
            ):
                draw_act_two_upgrade_screen(
                    game_surface,
                    active_upgrade_title_font,
                    active_upgrade_text_font,
                    game_state.player,
                    act_two_sprites,
                    game_state.upgrade_message,
                    upgrade_mouse_position,
                    game_state.upgrade_reward_pending,
                )
            else:
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
                    game_state.player.critical_damage_multiplier,
                    game_state.player.spell_power,
                    game_state.player.attribute_ranks,
                    game_state.upgrade_message,
                    upgrade_mouse_position,
                    show_intelligence=(current_act >= 2),
                )
        if game_state.class_selection_open:
            class_mouse_position = window_to_game_position(
                screen,
                pygame.mouse.get_pos(),
            )
            draw_class_selection_screen(
                game_surface,
                act_two_fonts["title"],
                act_two_fonts["heading"],
                act_two_fonts["heading"],
                act_two_fonts["text"],
                act_two_sprites,
                (
                    pygame.time.get_ticks()
                    - game_state.class_transition_started_at
                ),
                class_mouse_position,
                game_state.class_selection_choice,
                (
                    None
                    if game_state.class_selection_choice_started_at == 0
                    else (
                        current_time
                        - game_state.class_selection_choice_started_at
                    )
                ),
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
