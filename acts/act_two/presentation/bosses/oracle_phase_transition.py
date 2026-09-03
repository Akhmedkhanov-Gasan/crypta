import math
import random
from dataclasses import dataclass
from functools import lru_cache

import pygame

from acts.act_two.presentation.bosses.oracle_death import (
    handle_oracle_death_event,
    oracle_death_active,
)
from acts.act_two.presentation.bosses.oracle_intro import (
    handle_oracle_intro_event,
    oracle_intro_active,
)
from acts.act_two.presentation.bosses.oracle_phase_two import (
    initialize_oracle_phase_two,
)
from game.combat_log import add_log_message
from game.state import EnemyBehaviorState
from logic import get_enemy_occupied_positions
from presentation.layout import FONT_ROOT, PROJECT_ROOT
from settings import GAME_HEIGHT, GAME_WIDTH, TILE_SIZE


HUD_FADE_MS = 600
CAMERA_FOCUS_MS = 1500
TREMOR_START_MS = 650
DETACH_START_MS = 1900
DETACH_END_MS = 3900
DIALOGUE_START_MS = 4100
DIALOGUE_LINE_MS = 2300
RUSH_START_MS = 13700
RUSH_END_MS = 15500
CAMERA_RETURN_START_MS = 13700
CAMERA_RETURN_END_MS = 16400
HUD_RETURN_START_MS = 15700
TRANSITION_END_MS = 16600
SKIP_FADE_MS = 750

PHASE_ONE_BACKGROUND_VOLUME = 0.16
PHASE_TWO_MUSIC_VOLUME = 0.70
TRANSITION_SOUND_VOLUME = 0.85

DIALOGUE = (
    "NO... I SAW THIS WOUND...",
    "I SAW YOUR HAND BEFORE YOU RAISED IT!",
    "HE SAID YOU WOULD BREAK!!",
    "THEN BREAK!!!",
)


@dataclass
class OraclePhaseTransitionState:
    base_position: tuple[int, int]
    target_position: tuple[int, int]
    updated_at: int
    music_volume: float
    phase_one_music_volume: float
    elapsed: int = 0
    finished: bool = False
    paused: bool = False
    logged_lines: int = 0
    camera_origin: tuple[float, float] | None = None
    skip_frame: pygame.Surface | None = None
    skip_started_elapsed: int = -1
    transition_sound_played: bool = False
    transition_channel: pygame.mixer.Channel | None = None


def _smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _mix(start, end, progress):
    return start + (end - start) * progress

@lru_cache(maxsize=1)
def _load_transition_sounds():
    root = (
        PROJECT_ROOT
        / "assets/audio/sounds_act_2/oracle/fase_2"
    )
    sounds = []

    for index in (1, 2):
        path = root / f"oracle_fase_transition_{index}.mp3"

        try:
            sounds.append(
                pygame.mixer.Sound(str(path))
            )
        except (OSError, pygame.error):
            continue

    return tuple(sounds)


def _play_transition_sound(scene, sounds):
    if pygame.mixer.get_init() is None:
        return

    variants = _load_transition_sounds()

    if not variants:
        return

    sound = random.choice(variants)
    channel = sound.play()

    if channel is None:
        return

    channel.set_volume(
        max(
            0.0,
            min(
                1.0,
                sounds.master_volume
                * TRANSITION_SOUND_VOLUME,
            ),
        )
    )
    scene.transition_channel = channel


def _update_phase_one_music(scene, elapsed):
    if pygame.mixer.get_init() is None:
        return

    if elapsed < DETACH_START_MS:
        return

    progress = _smooth(
        (elapsed - DETACH_START_MS)
        / (DETACH_END_MS - DETACH_START_MS)
    )
    background_volume = min(
        1.0,
        scene.music_volume
        * PHASE_ONE_BACKGROUND_VOLUME,
    )
    volume = _mix(
        scene.phase_one_music_volume,
        background_volume,
        progress,
    )

    pygame.mixer.music.set_volume(
        max(0.0, min(1.0, volume))
    )


def _start_phase_two_music(game_state, scene):
    path = (
        PROJECT_ROOT
        / "assets/audio/sounds_act_2/oracle/oracle_fase_2.mp3"
    )

    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()

        pygame.mixer.music.load(str(path))
        pygame.mixer.music.set_volume(
            min(
                1.0,
                scene.music_volume
                * PHASE_TWO_MUSIC_VOLUME,
            )
        )
        pygame.mixer.music.play(
            -1,
            fade_ms=1800,
        )
    except (OSError, pygame.error) as error:
        add_log_message(
            game_state.combat_log,
            f"Oracle phase two music unavailable: {error}",
            category="system",
        )


def _oracle(floor):
    return next(
        (
            enemy
            for enemy in floor.enemies
            if enemy.type == "oracle" and enemy.health > 0
        ),
        None,
    )


def oracle_phase_transition_active(floor):
    scene = floor.oracle_phase_transition
    return scene is not None and not scene.finished


def oracle_cutscene_active(floor):
    return (
        oracle_intro_active(floor)
        or oracle_phase_transition_active(floor)
        or oracle_death_active(floor)
    )


def _head_cells(position):
    column, row = position
    return {
        (column, row),
        (column + 1, row),
        (column, row + 1),
        (column + 1, row + 1),
    }


def _base_cells(position):
    column, row = position
    return {
        (cell_column, cell_row)
        for cell_row in range(row - 1, row + 2)
        for cell_column in range(column - 1, column + 2)
    }


def _valid_head_position(floor, oracle, position, player_position):
    cells = _head_cells(position)
    blocked = {
        *floor.boss_columns,
        *floor.boss_emitters,
        *_base_cells((oracle.column, oracle.row)),
        *(
            (crate.column, crate.row)
            for crate in floor.breakable_crates
            if not crate.is_broken
        ),
        *(
            position
            for enemy in floor.enemies
            if enemy is not oracle and enemy.health > 0
            for position in get_enemy_occupied_positions(enemy)
        ),
    }

    if player_position in cells or cells & blocked:
        return False

    for column, row in cells:
        if not (
            0 <= row < len(floor.map)
            and 0 <= column < len(floor.map[row])
            and floor.map[row][column] == "."
        ):
            return False

    return min(
        max(
            abs(column - player_position[0]),
            abs(row - player_position[1]),
        )
        for column, row in cells
    ) == 1


def _choose_head_target(floor, oracle):
    player_position = (
        floor.player_column,
        floor.player_row,
    )
    player_column, player_row = player_position

    candidates = (
        (player_column + 1, player_row - 1),
        (player_column - 2, player_row - 1),
        (player_column - 1, player_row + 1),
        (player_column - 1, player_row - 2),
        (player_column + 1, player_row + 1),
        (player_column - 2, player_row + 1),
        (player_column + 1, player_row - 2),
        (player_column - 2, player_row - 2),
    )

    valid = tuple(
        position
        for position in candidates
        if _valid_head_position(
            floor,
            oracle,
            position,
            player_position,
        )
    )

    if valid:
        return min(
            valid,
            key=lambda position: (
                abs(position[0] - oracle.column)
                + abs(position[1] - oracle.row)
            ),
        )

    for row in range(len(floor.map) - 1):
        for column in range(len(floor.map[row]) - 1):
            position = (column, row)

            if _valid_head_position(
                floor,
                oracle,
                position,
                player_position,
            ):
                return position

    return (
        player_column + 1,
        player_row - 1,
    )


def _clear_first_phase(floor):
    floor.projectiles.clear()
    floor.oracle_combat = None


def _start_transition(
    game_state,
    camera,
    current_time,
    oracle,
    music_volume,
):
    floor = game_state.floor
    base_position = (oracle.column, oracle.row)

    phase_one_music_volume = (
        pygame.mixer.music.get_volume()
        if pygame.mixer.get_init() is not None
        else 0.0
    )

    floor.oracle_phase_transition = OraclePhaseTransitionState(
        base_position=base_position,
        target_position=_choose_head_target(floor, oracle),
        updated_at=current_time,
        music_volume=music_volume,
        phase_one_music_volume=phase_one_music_volume,
        camera_origin=(camera.x, camera.y),
    )

    oracle.phase_transition_pending = False
    oracle.second_phase_announced = True
    oracle.binding_turns = 0
    oracle.oracle_phase = 0
    oracle.oracle_base_column = oracle.column
    oracle.oracle_base_row = oracle.row
    oracle.oracle_phase_elapsed = 0
    oracle.oracle_phase_detached = False
    oracle.oracle_render_column = oracle.column - 0.5
    oracle.oracle_render_row = oracle.row - 0.5
    oracle.oracle_cast_amount = 0.0
    oracle.oracle_head_angle = 0.0
    oracle.is_active = False
    oracle.behavior_state = EnemyBehaviorState.INACTIVE

    game_state.player_attack_targets = []
    game_state.act_two_stats_open = False
    game_state.act_two_journal_open = False
    game_state.player.directional_ability_aiming = False
    game_state.player.act_two.fire_bomb_aiming = False

    _clear_first_phase(floor)


def _block_oracle_base(floor, position):
    dungeon = [list(row) for row in floor.map]

    for column, row in _base_cells(position):
        if (
            0 <= row < len(dungeon)
            and 0 <= column < len(dungeon[row])
        ):
            dungeon[row][column] = "C"

    floor.map = [
        "".join(row)
        for row in dungeon
    ]


def _finish_transition(game_state, oracle, scene):
    floor = game_state.floor

    _block_oracle_base(
        floor,
        scene.base_position,
    )

    oracle.column, oracle.row = scene.target_position
    oracle.footprint_width = 2
    oracle.footprint_height = 2
    oracle.is_immobile = False
    oracle.is_active = True
    oracle.is_aggro = True
    oracle.behavior_state = EnemyBehaviorState.CHASING
    oracle.oracle_phase = 2
    oracle.oracle_phase_detached = True
    oracle.oracle_render_column = None
    oracle.oracle_render_row = None
    oracle.oracle_phase_two_eye = "idle"
    oracle.oracle_phase_two_opening_attack_pending = True
    oracle.oracle_cast_amount = 0.0
    oracle.oracle_head_angle = 0.0

    if (
        scene.skip_frame is not None
        and scene.transition_channel is not None
        and scene.transition_channel.get_busy()
    ):
        scene.transition_channel.fadeout(250)

    _start_phase_two_music(
        game_state,
        scene,
    )

    initialize_oracle_phase_two(
        game_state,
        oracle,
        pygame.time.get_ticks(),
    )

    scene.finished = True
    scene.skip_frame = None
    floor.oracle_combat = None


def update_oracle_phase_transition(
    game_state,
    camera,
    current_time,
    sounds,
    music_volume,
):
    floor = game_state.floor
    oracle = _oracle(floor)

    if oracle is None:
        return

    if floor.oracle_phase_transition is None:
        if (
            oracle.phase_transition_pending
            and oracle.oracle_phase == 1
        ):
            _start_transition(
                game_state,
                camera,
                current_time,
                oracle,
                music_volume,
            )
        else:
            return

    if not oracle_phase_transition_active(floor):
        return

    scene = floor.oracle_phase_transition
    delta = max(
        0,
        min(50, current_time - scene.updated_at),
    )
    scene.updated_at = current_time

    if not scene.paused:
        scene.elapsed = min(
            TRANSITION_END_MS,
            scene.elapsed + delta,
        )

    elapsed = scene.elapsed
    if (
        elapsed >= DETACH_START_MS
        and not scene.transition_sound_played
    ):
        scene.transition_sound_played = True

        if scene.skip_frame is None:
            _play_transition_sound(
                scene,
                sounds,
            )

    _update_phase_one_music(
        scene,
        elapsed,
    )
    oracle.oracle_phase_elapsed = elapsed
    oracle.oracle_phase_detached = elapsed >= DETACH_START_MS

    start_column = scene.base_position[0] - 0.5
    start_row = scene.base_position[1] - 0.5
    hover_column = start_column
    hover_row = start_row - 0.8

    if elapsed < DETACH_START_MS:
        oracle.oracle_render_column = start_column
        oracle.oracle_render_row = start_row
    elif elapsed < DETACH_END_MS:
        progress = _smooth(
            (elapsed - DETACH_START_MS)
            / (DETACH_END_MS - DETACH_START_MS)
        )
        oracle.oracle_render_column = _mix(
            start_column,
            hover_column,
            progress,
        )
        oracle.oracle_render_row = _mix(
            start_row,
            hover_row,
            progress,
        )
    elif elapsed < RUSH_START_MS:
        oracle.oracle_render_column = (
                hover_column
                + math.sin(elapsed / 460) * 0.020
        )
        oracle.oracle_render_row = (
                hover_row
                + math.sin(elapsed / 570) * 0.030
        )
    else:
        progress = _smooth(
            (elapsed - RUSH_START_MS)
            / (RUSH_END_MS - RUSH_START_MS)
        )
        oracle.oracle_render_column = _mix(
            hover_column,
            scene.target_position[0],
            progress,
        )
        oracle.oracle_render_row = _mix(
            hover_row,
            scene.target_position[1],
            progress,
        )
        oracle.oracle_phase_two_eye = "cast"

    while (
        scene.logged_lines < len(DIALOGUE)
        and elapsed
        >= DIALOGUE_START_MS
        + scene.logged_lines * DIALOGUE_LINE_MS
    ):
        add_log_message(
            game_state.combat_log,
            "Oracle: " + DIALOGUE[scene.logged_lines],
            category="dialogue",
        )
        scene.logged_lines += 1

    view_width = GAME_WIDTH / camera.zoom
    view_height = GAME_HEIGHT / camera.zoom

    boss_focus = (
        (scene.base_position[0] + 0.5) * TILE_SIZE
        - view_width / 2,
        (scene.base_position[1] + 0.5) * TILE_SIZE
        - view_height / 2,
    )
    player_focus = (
        (floor.player_column + 0.5) * TILE_SIZE
        - view_width / 2,
        (floor.player_row + 0.5) * TILE_SIZE
        - view_height / 2,
    )

    if scene.skip_frame is not None:
        camera.x, camera.y = player_focus
    elif elapsed < CAMERA_RETURN_START_MS:
        progress = _smooth(elapsed / CAMERA_FOCUS_MS)
        camera.x = _mix(
            scene.camera_origin[0],
            boss_focus[0],
            progress,
        )
        camera.y = _mix(
            scene.camera_origin[1],
            boss_focus[1],
            progress,
        )
    else:
        progress = _smooth(
            (elapsed - CAMERA_RETURN_START_MS)
            / (
                CAMERA_RETURN_END_MS
                - CAMERA_RETURN_START_MS
            )
        )
        camera.x = _mix(
            boss_focus[0],
            player_focus[0],
            progress,
        )
        camera.y = _mix(
            boss_focus[1],
            player_focus[1],
            progress,
        )

    camera.target_x = camera.x
    camera.target_y = camera.y
    camera.floor_index = game_state.floor_index
    camera.updated_at = current_time

    if elapsed >= TRANSITION_END_MS:
        _finish_transition(
            game_state,
            oracle,
            scene,
        )


def handle_oracle_cutscene_event(
    floor,
    event,
    frame,
    mouse_position=None,
):
    if oracle_death_active(floor):
        return handle_oracle_death_event(
            floor,
            event,
            mouse_position,
        )

    if oracle_intro_active(floor):
        handle_oracle_intro_event(
            floor,
            event,
            frame,
        )
        return

    scene = floor.oracle_phase_transition

    if scene is None or scene.finished:
        return

    if event.type == pygame.WINDOWFOCUSLOST:
        scene.paused = True
    elif event.type == pygame.WINDOWFOCUSGAINED:
        scene.paused = False
    elif (
        event.type == pygame.KEYDOWN
        and event.key == pygame.K_SPACE
        and scene.skip_frame is None
    ):
        scene.skip_frame = frame.copy()
        scene.elapsed = max(
            scene.elapsed,
            TRANSITION_END_MS - SKIP_FADE_MS,
        )
        scene.skip_started_elapsed = scene.elapsed


@lru_cache(maxsize=1)
def _dialogue_font():
    return pygame.font.Font(
        str(FONT_ROOT / "IsWasted.ttf"),
        38,
    )


def _text_surface(text):
    font = _dialogue_font()
    foreground = font.render(
        text,
        True,
        (202, 66, 66),
    )
    outline = font.render(
        text,
        True,
        (12, 2, 4),
    )
    surface = pygame.Surface(
        (
            foreground.get_width() + 16,
            foreground.get_height() + 16,
        ),
        pygame.SRCALPHA,
    )
    rectangle = foreground.get_rect(
        center=(
            surface.get_width() // 2,
            surface.get_height() // 2,
        ),
    )

    for dx, dy in (
        (-3, -3), (0, -3), (3, -3),
        (-3, 0), (3, 0),
        (-3, 3), (0, 3), (3, 3),
    ):
        surface.blit(
            outline,
            rectangle.move(dx, dy),
        )

    surface.blit(foreground, rectangle)
    return surface


def draw_oracle_phase_transition(
    screen,
    world_frame,
    floor,
):
    if (
        world_frame is None
        or not oracle_phase_transition_active(floor)
    ):
        return

    scene = floor.oracle_phase_transition
    elapsed = scene.elapsed

    if scene.skip_frame is not None:
        duration = max(
            1,
            TRANSITION_END_MS - scene.skip_started_elapsed,
        )
        progress = _smooth(
            (elapsed - scene.skip_started_elapsed) / duration
        )
        scene.skip_frame.set_alpha(
            round(255 * (1.0 - progress))
        )
        screen.blit(scene.skip_frame, (0, 0))
        return

    hud_visibility = max(
        1.0 - _smooth(elapsed / HUD_FADE_MS),
        _smooth(
            (elapsed - HUD_RETURN_START_MS)
            / (TRANSITION_END_MS - HUD_RETURN_START_MS)
        ),
    )

    complete_frame = screen.copy()
    screen.blit(world_frame, (0, 0))
    complete_frame.set_alpha(
        round(255 * hud_visibility)
    )
    screen.blit(complete_frame, (0, 0))

    bar_height = round(
        72 * (1.0 - hud_visibility)
    )

    if bar_height > 0:
        pygame.draw.rect(
            screen,
            (0, 0, 0),
            (0, 0, GAME_WIDTH, bar_height),
        )
        pygame.draw.rect(
            screen,
            (0, 0, 0),
            (
                0,
                GAME_HEIGHT - bar_height,
                GAME_WIDTH,
                bar_height,
            ),
        )

    dialogue_elapsed = elapsed - DIALOGUE_START_MS
    duration = len(DIALOGUE) * DIALOGUE_LINE_MS

    if 0 <= dialogue_elapsed < duration:
        index = dialogue_elapsed // DIALOGUE_LINE_MS
        local_time = dialogue_elapsed % DIALOGUE_LINE_MS
        alpha = min(
            _smooth(local_time / 180),
            _smooth(
                (DIALOGUE_LINE_MS - local_time) / 320
            ),
        )
        intensity = math.sin(
            math.pi * local_time / DIALOGUE_LINE_MS
        )
        offset_x = round(
            math.sin(elapsed / 31) * 2 * intensity
        )
        offset_y = round(
            math.sin(elapsed / 47) * intensity
        )

        text = _text_surface(DIALOGUE[index])
        text.set_alpha(round(255 * alpha))
        screen.blit(
            text,
            text.get_rect(
                midbottom=(
                    GAME_WIDTH // 2 + offset_x,
                    GAME_HEIGHT - 86 + offset_y,
                ),
            ),
        )
