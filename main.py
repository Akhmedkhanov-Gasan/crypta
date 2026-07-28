import pygame

from bosses.oracle import resolve_oracle_hit_reaction
from game.combat_log import add_log_message
from game.events import GameEventType
from game.factories import create_floor_state, create_game_state
from levels import FLOOR_CONFIGS
from logic import get_enemy_occupied_positions
from rendering import (
    CLASS_SELECTION_READY_MS,
    draw_act_three_awakening,
    draw_act_three_debug_class_selection,
    draw_act_three_gameplay,
    draw_attack_markers,
    draw_boss_door,
    draw_chest,
    draw_class_selection_screen,
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
    get_class_selection_rectangles,
    get_act_three_debug_class_rectangles,
    get_act_three_sidebar_tab_rectangles,
    get_subclass_selection_rectangles,
    load_act_one_fonts,
    load_act_three_fonts,
    load_act_three_gameplay_assets,
    load_act_three_transition_assets,
    load_act_two_fonts,
    load_act_two_sprites,
)
from presentation.layout import (
    ACT_THREE_AWAKENING_END_MS,
    ACT_THREE_MUSIC_PATH,
    ACT_THREE_NARRATIVE_READY_MS,
)
from settings import (
    BACKGROUND_COLOR,
    CLASS_ABILITY_KILLS,
    CRIT_UPGRADE_AMOUNT,
    DODGE_UPGRADE_AMOUNT,
    FPS,
    GAME_HEIGHT,
    GAME_WIDTH,
    INITIAL_WINDOW_SCALE,
    MAX_CRIT_CHANCE,
    MAX_DODGE_CHANCE,
)
from systems.player_actions import (
    open_chest,
    try_move_player,
    try_use_potion,
)
from systems.player_combat import (
    perform_basic_attack,
)
from systems.player_abilities import (
    AbilityRequestResult,
    cancel_ability_aiming,
    cast_directional_ability,
    request_class_ability,
)
from systems.enemy_turn import resolve_enemy_turn

FIRST_ACT_FINAL_FLOOR = 2
ACT_THREE_MUSIC_ENABLED = False
SECOND_ACT_FINAL_FLOOR = max(
    index
    for index, floor_config in enumerate(FLOOR_CONFIGS)
    if floor_config["act"] == 2
)


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
    scaled_surface = pygame.transform.scale(
        game_surface,
        (scaled_width, scaled_height),
    )
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


def create_oracle_debug_state(
    player_class,
    opening_message,
):
    debug_state = create_game_state(
        floor_index=SECOND_ACT_FINAL_FLOOR,
        opening_message=opening_message,
    )
    debug_player = debug_state.player
    debug_player.player_class = player_class

    if debug_player.player_class == "warrior":
        debug_player.max_health += 4
    elif debug_player.player_class == "rogue":
        debug_player.max_health = max(
            1,
            debug_player.max_health - 2,
        )
        debug_player.crit_chance = 0.10
        debug_player.dodge_chance = 0.10

    debug_player.health = debug_player.max_health
    debug_player.damage_min = 5
    debug_player.damage_max = 6
    debug_player.potion_count = 2
    debug_player.ability_kill_charge = CLASS_ABILITY_KILLS

    return debug_state


def advance_act_three_transition(game_state, current_time):
    narrative_elapsed = (
        current_time
        - game_state.act_three_transition_started_at
    )

    if game_state.act_three_visual_started_at == 0:
        if narrative_elapsed < ACT_THREE_NARRATIVE_READY_MS:
            game_state.act_three_transition_started_at = (
                current_time - ACT_THREE_NARRATIVE_READY_MS
            )
        else:
            game_state.act_three_visual_started_at = current_time
        return

    game_state.act_three_visual_started_at = (
        current_time - ACT_THREE_AWAKENING_END_MS
    )


def create_act_three_debug_transition(
    player_class,
    current_time,
):
    debug_state = create_oracle_debug_state(
        player_class,
        (
            "Debug jump: "
            f"{player_class.title()} Act III awakening."
        ),
    )

    for enemy in debug_state.floor.enemies:
        enemy.health = 0

    debug_state.floor.projectiles.clear()
    debug_state.act_three_transition_open = True
    debug_state.act_three_transition_started_at = current_time

    return debug_state


def choose_subclass(game_state, subclass):
    game_state.player.subclass = subclass
    if not game_state.act_three_test_mode:
        game_state.floor_index += 1
        game_state.floor = create_floor_state(game_state.floor_index)
    game_state.player.key_count = 0
    game_state.player_attack_targets = []
    game_state.subclass_selection_open = False
    display_name = {
        "berserker": "Berserker",
        "paladin": "Paladin",
        "assassin": "Assassin",
        "archer": "Archer",
        "warlock": "Warlock",
        "summoner": "Summoner",
    }[subclass]
    class_name = game_state.player.player_class
    add_log_message(
        game_state.combat_log,
        (
            f"The {class_name} chooses the path "
            f"of the {display_name}."
        ),
    )
    add_log_message(
        game_state.combat_log,
        "Act III begins. The world is alive.",
    )


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

    game_state = create_game_state()
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
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and game_state.act_three_debug_class_selection_open
            ):
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
                if game_mouse_position is not None:
                    for tab_name, tab_rectangle in (
                        get_act_three_sidebar_tab_rectangles().items()
                    ):
                        if tab_rectangle.collidepoint(
                            game_mouse_position
                        ):
                            game_state.sidebar_tab = tab_name
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
                    game_state = create_oracle_debug_state(
                        game_state.player.player_class or "warrior",
                        "Debug jump: Oracle arena.",
                    )
                    continue

                if event.key == pygame.K_F3:
                    if (
                        act_three_music_attempted
                        and pygame.mixer.get_init() is not None
                    ):
                        pygame.mixer.music.stop()
                    act_three_music_attempted = False
                    game_state = create_game_state(
                        opening_message=(
                            "Debug: choose an Act III class."
                        )
                    )
                    game_state.act_three_debug_class_selection_open = (
                        True
                    )
                    continue

                if event.key == pygame.K_F1:
                    game_state = create_game_state(
                        floor_index=len(FLOOR_CONFIGS) - 1,
                        opening_message="Act III test room: choose a class.",
                    )
                    game_state.act_three_test_mode = True
                    game_state.act_three_debug_class_selection_open = True
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
                            if player_class == "warrior":
                                game_state.player.max_health += 4
                                game_state.player.health += 4
                            elif player_class == "rogue":
                                game_state.player.max_health = max(
                                    1, game_state.player.max_health - 2
                                )
                                game_state.player.health = max(
                                    1, game_state.player.health - 2
                                )
                                game_state.player.crit_chance = 0.10
                                game_state.player.dodge_chance = 0.10
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

                    if game_state.player.player_class == "warrior":
                        game_state.player.max_health += 4
                        game_state.player.health += 4
                    elif game_state.player.player_class == "rogue":
                        game_state.player.max_health = max(
                            1,
                            game_state.player.max_health - 2,
                        )
                        game_state.player.health = max(
                            1,
                            game_state.player.health - 2,
                        )
                        game_state.player.crit_chance = min(
                            MAX_CRIT_CHANCE,
                            game_state.player.crit_chance + 0.10,
                        )
                        game_state.player.dodge_chance = min(
                            MAX_DODGE_CHANCE,
                            game_state.player.dodge_chance + 0.10,
                        )

                    game_state.floor_index += 1
                    game_state.floor = create_floor_state(game_state.floor_index)
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
                            game_state.player.max_health += 2
                            game_state.player.health += 2
                            game_state.upgrade_message = "Maximum HP increased by 2."
                            add_log_message(
                                game_state.combat_log,
                                game_state.upgrade_message,
                            )
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        if game_state.player.gold_count <= 0:
                            game_state.upgrade_message = "Not enough gold."
                        else:
                            game_state.player.gold_count -= 1
                            game_state.player.damage_min += 1
                            game_state.player.damage_max += 1
                            game_state.upgrade_message = "Damage increased by 1."
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
                            game_state.player.crit_chance = min(
                                MAX_CRIT_CHANCE,
                                game_state.player.crit_chance
                                + CRIT_UPGRADE_AMOUNT,
                            )
                            game_state.upgrade_message = "Critical chance increased by 5%."
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
                            game_state.player.dodge_chance = min(
                                MAX_DODGE_CHANCE,
                                game_state.player.dodge_chance
                                + DODGE_UPGRADE_AMOUNT,
                            )
                            game_state.upgrade_message = "Dodge chance increased by 5%."
                            add_log_message(
                                game_state.combat_log,
                                game_state.upgrade_message,
                            )
                    elif event.key in (
                        pygame.K_RETURN,
                        pygame.K_KP_ENTER,
                    ):
                        game_state.floor_index += 1
                        game_state.floor = create_floor_state(game_state.floor_index)
                        game_state.player.key_count = 0
                        game_state.upgrade_screen_open = False
                        game_state.upgrade_message = ""
                        game_state.player_attack_targets = []
                        add_log_message(
                            game_state.combat_log,
                            f"Hero descends to floor {game_state.floor_index + 1}.",
                        )

                    continue

                game_state.clear_events()
                column_change = 0
                row_change = 0

                if event.key in (pygame.K_w, pygame.K_UP):
                    row_change = -1
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    row_change = 1
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    column_change = -1
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    column_change = 1

                player_tried_to_move = (
                    column_change != 0 or row_change != 0
                )
                directional_ability_cast = (
                    game_state.player.player_class in ("warrior", "mage")
                    and game_state.player.directional_ability_aiming
                    and player_tried_to_move
                )
                rogue_ability_activated = False

                if event.key == pygame.K_e:
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

                if rogue_ability_activated:
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
                elif player_waited:
                    player_acted = True
                elif player_tried_to_move:
                    if target_enemy:
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
                    resolve_enemy_turn(
                        game_state,
                        player_position_before_action,
                        rogue_ability_activated,
                    )
                    enemy_movement_started_at = (
                        pygame.time.get_ticks()
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
                    for enemy in game_state.floor["enemies"]:
                        if enemy.name in moved_enemy_names:
                            enemy.movement_animation_started_at = (
                                enemy_movement_started_at
                            )
                        if (
                            enemy.name in attacked_enemy_names
                            or enemy.name in healed_enemy_names
                        ):
                            enemy.attack_animation_started_at = (
                                enemy_movement_started_at
                            )
        current_time = pygame.time.get_ticks()

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
        active_status_font = (
            act_two_fonts["status"]
            if current_act >= 2
            else font
        )
        active_heading_font = (
            act_two_fonts["heading"]
            if current_act >= 2
            else font
        )
        active_text_font = (
            act_two_fonts["text"]
            if current_act >= 2
            else log_font
        )
        active_controls_font = (
            act_two_fonts["controls"]
            if current_act >= 2
            else act_one_fonts["controls"]
        )
        game_surface.fill(BACKGROUND_COLOR)
        draw_dungeon(
            game_surface,
            game_state.floor["map"],
            current_act,
            act_two_sprites,
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
        )
        if game_state.floor["boss_door"] is not None:
            living_boss_group = any(
                enemy["health"] > 0 and enemy["boss_group"]
                for enemy in game_state.floor["enemies"]
            )
            boss_door_is_open = game_state.floor[
                "boss_fight_started"
            ]

            if game_state.floor[
                "seal_boss_door_during_fight"
            ]:
                boss_door_is_open = (
                    game_state.floor["boss_fight_started"]
                    and not living_boss_group
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
        )
        for enemy in game_state.floor["enemies"]:
            if enemy["health"] > 0:
                draw_enemy(
                    game_surface,
                    enemy,
                    current_act,
                    act_two_sprites,
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
                    act_two_fonts["status"]
                    if current_act >= 2
                    else font
                )
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
        present_game(screen, game_surface)
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
