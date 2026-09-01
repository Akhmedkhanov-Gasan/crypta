import math
from dataclasses import dataclass
from functools import lru_cache

import pygame

from acts.act_two.presentation.movement import (
    MAGE_MOVE_DURATION_MS,
    MAGE_MOVE_TRAVEL_MS,
    ROGUE_MOVE_DURATION_MS,
    ROGUE_MOVE_TRAVEL_MS,
    WARRIOR_MOVE_DURATION_MS,
    WARRIOR_MOVE_TRAVEL_MS,
)
from game.combat_log import add_log_message
from presentation.layout import FONT_ROOT, PROJECT_ROOT
from settings import GAME_HEIGHT, GAME_WIDTH, TILE_SIZE


HUD_FADE_MS = 650
GATE_HALF_MS = 650
GATE_OPEN_MS = 1250
WALK_START_MS = 1450
STEP_MS = 680
STEP_TRAVEL_MS = 540
WALK_END_MS = WALK_START_MS + STEP_MS * 4
LIGHT_START_MS = WALK_END_MS + 350
LIGHT_INTERVAL_MS = 650
PAN_END_MS = WALK_END_MS + 4500
BOSS_REVEAL_START_MS = PAN_END_MS - 650
EYES_START_MS = PAN_END_MS + 1600
EYES_DURATION_MS = 3800
NAME_START_MS = EYES_START_MS + EYES_DURATION_MS + 250
DIALOGUE_START_MS = NAME_START_MS + 3200
DIALOGUE_LINE_MS = 4000

DIALOGUE = (
    "He has come, just as I foresaw… Just as YOU said.",
    "But I cannot grant YOUR request.",
    "He will not become what YOU wish him to be. I see it…",
)

RETURN_START_MS = (
    DIALOGUE_START_MS + len(DIALOGUE) * DIALOGUE_LINE_MS
)
RETURN_DURATION_MS = 2000
HUD_RETURN_START_MS = RETURN_START_MS + 1200
INTRO_END_MS = RETURN_START_MS + RETURN_DURATION_MS
SKIP_FADE_MS = 800

_INTRO_SEEN = False

_MOVEMENT_TIMINGS = {
    "warrior": (WARRIOR_MOVE_DURATION_MS, WARRIOR_MOVE_TRAVEL_MS),
    "rogue": (ROGUE_MOVE_DURATION_MS, ROGUE_MOVE_TRAVEL_MS),
    "mage": (MAGE_MOVE_DURATION_MS, MAGE_MOVE_TRAVEL_MS),
}


@dataclass
class OracleIntroState:
    origin: tuple[int, int]
    path: tuple[tuple[int, int], ...]
    updated_at: int
    can_skip: bool
    elapsed: int = 0
    finished: bool = False
    paused: bool = False
    logged_lines: int = 0
    camera_origin: tuple[float, float] | None = None
    player_position: tuple[float, float] | None = None
    skip_frame: pygame.Surface | None = None
    skip_started_elapsed: int = -1


def _smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _mix(start, end, progress):
    return start + (end - start) * progress


def oracle_intro_active(floor):
    scene = floor.oracle_intro
    return (
        floor.has_oracle_gate
        and scene is not None
        and not scene.finished
    )


def start_oracle_intro(game_state, current_time):
    floor = game_state.floor
    if floor.oracle_intro is not None:
        return

    column, row = floor.boss_door
    origin = (floor.player_column, floor.player_row)

    floor.oracle_intro = OracleIntroState(
        origin=origin,
        path=tuple((column, row - index) for index in range(4)),
        updated_at=current_time,
        can_skip=True,
        player_position=origin,
    )
    floor.oracle_gate_opening_started_at = -1

    game_state.act_two_stats_open = False
    game_state.act_two_journal_open = False
    game_state.player.act_two_movement_origin = None
    game_state.player.act_two_movement_started_at = -1
    game_state.player.act_two_blocked_movement_started_at = -1

    music_path = (
        PROJECT_ROOT
        / "assets/audio/sounds_act_2/oracle/oracle_fase_1.mp3"
    )

    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()

        music_volume = pygame.mixer.music.get_volume()

        pygame.mixer.music.load(str(music_path))
        pygame.mixer.music.set_volume(
            min(1.0, music_volume * 0.7)
        )
        pygame.mixer.music.play(-1, fade_ms=2500)

    except (pygame.error, OSError) as error:
        add_log_message(
            game_state.combat_log,
            f"Oracle music unavailable: {error}",
            category="system",
        )


def oracle_gate_sprite(floor):
    if not oracle_intro_active(floor):
        return None

    elapsed = floor.oracle_intro.elapsed

    if elapsed < GATE_HALF_MS:
        return "gate_closed"
    if elapsed < GATE_OPEN_MS:
        return "gate_half_open"
    if elapsed < WALK_END_MS + 250:
        return "gate_open"
    if elapsed < WALK_END_MS + 700:
        return "gate_half_open"
    return "gate_closed"


def oracle_pillar_light(floor, column, row):
    scene = floor.oracle_intro
    if scene is None:
        return 0.0, 0.0
    if scene.finished:
        return 1.0, 0.0

    order = sorted(
        floor.boss_columns,
        key=lambda position: (-position[1], position[0]),
    )
    index = order.index((column, row))
    age = scene.elapsed - (
        LIGHT_START_MS + index * LIGHT_INTERVAL_MS
    )

    level = _smooth(age / 650)
    flash = (
        math.sin(math.pi * age / 650)
        if 0 < age < 650
        else 0.0
    )
    return level, flash


def oracle_boss_light(floor):
    scene = floor.oracle_intro
    if scene is None:
        return 0.0
    if scene.finished:
        return 1.0
    return _smooth(
        (scene.elapsed - BOSS_REVEAL_START_MS) / 650
    )


def oracle_player_position(floor):
    scene = floor.oracle_intro
    if oracle_intro_active(floor):
        return scene.player_position
    return floor.player_column, floor.player_row


def update_oracle_intro(game_state, camera, current_time):
    global _INTRO_SEEN

    floor = game_state.floor
    if not oracle_intro_active(floor):
        return

    scene = floor.oracle_intro
    delta = max(0, min(50, current_time - scene.updated_at))
    scene.updated_at = current_time

    if not scene.paused:
        scene.elapsed = min(INTRO_END_MS, scene.elapsed + delta)

    elapsed = scene.elapsed
    player = game_state.player

    if scene.camera_origin is None:
        scene.camera_origin = (camera.x, camera.y)

    floor.oracle_gate_opened = elapsed >= GATE_OPEN_MS
    floor.boss_fight_started = elapsed >= WALK_END_MS

    if elapsed < WALK_START_MS:
        floor.player_column, floor.player_row = scene.origin
        scene.player_position = scene.origin
        player.act_two_movement_origin = None
        player.act_two_movement_started_at = -1

    elif elapsed < WALK_END_MS:
        walk_elapsed = elapsed - WALK_START_MS
        step_index = min(3, walk_elapsed // STEP_MS)
        step_elapsed = walk_elapsed % STEP_MS
        destination = scene.path[step_index]
        origin = (
            scene.origin
            if step_index == 0
            else scene.path[step_index - 1]
        )

        floor.player_column, floor.player_row = destination
        player.act_two_facing_direction = (0, -1)

        duration, travel_duration = _MOVEMENT_TIMINGS[
            player.player_class
        ]
        progress = min(1.0, step_elapsed / STEP_TRAVEL_MS)

        if progress < 1.0:
            player.act_two_movement_origin = origin
            player.act_two_movement_started_at = max(
                1,
                current_time - round(progress * duration),
            )
        else:
            player.act_two_movement_origin = None
            player.act_two_movement_started_at = -1

        travel = _smooth(progress * duration / travel_duration)
        scene.player_position = (
            _mix(origin[0], destination[0], travel),
            _mix(origin[1], destination[1], travel),
        )

    else:
        floor.player_column, floor.player_row = scene.path[-1]
        scene.player_position = scene.path[-1]
        player.act_two_movement_origin = None
        player.act_two_movement_started_at = -1

    eye_progress = max(
        0.0,
        min(
            1.0,
            (elapsed - EYES_START_MS) / EYES_DURATION_MS,
        ),
    )
    head_angle = (
        2.0 * math.sin(math.pi * eye_progress) ** 2
    )

    oracle = next(
        enemy
        for enemy in floor.enemies
        if enemy["type"] == "oracle"
    )
    oracle.oracle_eye_progress = eye_progress
    oracle.oracle_head_angle = head_angle

    if elapsed >= RETURN_START_MS:
        from game.state import EnemyBehaviorState

        oracle.oracle_awakened = True
        oracle.is_active = True
        oracle.is_aggro = True
        oracle.behavior_state = EnemyBehaviorState.CHASING

    while (
        scene.logged_lines < len(DIALOGUE)
        and elapsed >= (
            DIALOGUE_START_MS
            + scene.logged_lines * DIALOGUE_LINE_MS
        )
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
        (oracle.column + 0.5) * TILE_SIZE - view_width / 2,
        (oracle.row + 0.5) * TILE_SIZE - view_height / 2,
    )
    player_focus = (
        (scene.path[-1][0] + 0.5) * TILE_SIZE - view_width / 2,
        (scene.path[-1][1] + 0.5) * TILE_SIZE - view_height / 2,
    )

    if scene.skip_frame is not None:
        camera.x, camera.y = player_focus
    elif elapsed < RETURN_START_MS:
        player_column, player_row = scene.player_position

        follow_position = (
            scene.camera_origin[0]
            + (player_column - scene.origin[0]) * TILE_SIZE,
            scene.camera_origin[1]
            + (player_row - scene.origin[1]) * TILE_SIZE,
        )

        pan_start = WALK_END_MS - STEP_MS
        progress = _smooth(
            (elapsed - pan_start)
            / (PAN_END_MS - pan_start)
        )

        camera.x = _mix(
            follow_position[0],
            boss_focus[0],
            progress,
        )
        camera.y = _mix(
            follow_position[1],
            boss_focus[1],
            progress,
        )
    else:
        progress = _smooth(
            (elapsed - RETURN_START_MS) / RETURN_DURATION_MS
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

    if elapsed >= INTRO_END_MS:
        scene.finished = True
        scene.skip_frame = None
        oracle.oracle_eye_progress = 1.0
        oracle.oracle_head_angle = 0.0
        _INTRO_SEEN = True


def handle_oracle_intro_event(floor, event, frame):
    scene = floor.oracle_intro

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
            INTRO_END_MS - SKIP_FADE_MS,
        )
        scene.skip_started_elapsed = scene.elapsed


@lru_cache(maxsize=1)
def _dialogue_font():
    return pygame.font.Font(
        str(FONT_ROOT / "Almendra-Bold.ttf"),
        24,
    )


def _text_surface(text, font, width):
    lines = []
    line = ""

    for word in text.split():
        candidate = f"{line} {word}".strip()
        if line and font.size(candidate)[0] > width:
            lines.append(line)
            line = word
        else:
            line = candidate

    if line:
        lines.append(line)

    line_height = font.get_linesize()
    surface = pygame.Surface(
        (width + 8, len(lines) * line_height + 8),
        pygame.SRCALPHA,
    )

    for index, line in enumerate(lines):
        foreground = font.render(line, True, (199, 188, 169))
        outline = font.render(line, True, (5, 4, 6))
        rectangle = foreground.get_rect(
            midtop=(surface.get_width() // 2, 4 + index * line_height),
        )

        for dx, dy in (
            (-2, -2), (0, -2), (2, -2),
            (-2, 0), (2, 0),
            (-2, 2), (0, 2), (2, 2),
        ):
            surface.blit(outline, rectangle.move(dx, dy))

        surface.blit(foreground, rectangle)

    return surface


def draw_oracle_intro(screen, world_frame, floor, layout, assets):
    if world_frame is None or not oracle_intro_active(floor):
        return

    scene = floor.oracle_intro
    elapsed = scene.elapsed

    if scene.skip_frame is not None:
        duration = max(
            1,
            INTRO_END_MS - scene.skip_started_elapsed,
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
            / (INTRO_END_MS - HUD_RETURN_START_MS)
        ),
    )

    complete_frame = screen.copy()
    screen.blit(world_frame, (0, 0))
    complete_frame.set_alpha(round(255 * hud_visibility))
    screen.blit(complete_frame, (0, 0))

    bar_height = round(64 * (1.0 - hud_visibility))
    if bar_height > 0:
        pygame.draw.rect(
            screen,
            (0, 0, 0),
            (0, 0, GAME_WIDTH, bar_height),
        )
        pygame.draw.rect(
            screen,
            (0, 0, 0),
            (0, GAME_HEIGHT - bar_height, GAME_WIDTH, bar_height),
        )

    introduction = layout["oracle_introduce"]
    name_elapsed = elapsed - NAME_START_MS
    fade_in = max(1, int(introduction["fade_in_ms"]))
    fade_out = max(1, int(introduction["fade_out_ms"]))
    name_end = fade_in + 1800 + fade_out

    if 0 <= name_elapsed < name_end:
        alpha = min(
            _smooth(name_elapsed / fade_in),
            _smooth((name_end - name_elapsed) / fade_out),
        )
        image = assets["introduce"].copy()
        image.set_alpha(round(255 * alpha))
        screen.blit(image, assets["introduce_rect"])

    dialogue_elapsed = elapsed - DIALOGUE_START_MS
    if 0 <= dialogue_elapsed < len(DIALOGUE) * DIALOGUE_LINE_MS:
        index = dialogue_elapsed // DIALOGUE_LINE_MS
        local_time = dialogue_elapsed % DIALOGUE_LINE_MS
        alpha = min(
            _smooth(local_time / 350),
            _smooth((DIALOGUE_LINE_MS - local_time) / 550),
        )

        text = _text_surface(
            DIALOGUE[index],
            _dialogue_font(),
            GAME_WIDTH - 180,
        )
        text.set_alpha(round(255 * alpha))
        screen.blit(
            text,
            text.get_rect(
                midbottom=(GAME_WIDTH // 2, GAME_HEIGHT - 88),
            ),
        )
