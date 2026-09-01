import math
import random
from dataclasses import dataclass
from functools import lru_cache

import pygame


from acts.act_two.presentation.bosses.oracle_credits import (
    draw_oracle_credits,
    handle_oracle_credits_event,
    start_oracle_credits,
)
from game.combat_log import add_log_message
from presentation.layout import (
    FONT_ROOT,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    PROJECT_ROOT,
)
from settings import (
    GAME_HEIGHT,
    GAME_WIDTH,
    TILE_SIZE,
)


HUD_FADE_MS = 700
CAMERA_FOCUS_MS = 1300
FIRST_FRAME_END_MS = 2800
SECOND_FRAME_END_MS = 5600
DIALOGUE_START_MS = 5800
DIALOGUE_LINE_MS = 2300
DEATH_CROSSFADE_MS = 700
DEATH_SOUND_VOLUME = 0.90

DIALOGUE = (
    "Go then, child...",
    "But know this, your journey will not end well.",
    "You cannot change your fate. No man can.",
)

DIALOGUE_END_MS = (
    DIALOGUE_START_MS
    + len(DIALOGUE) * DIALOGUE_LINE_MS
)
CREDITS_START_MS = DIALOGUE_END_MS + 900


@dataclass
class OracleDeathState:
    caster: object
    position: tuple[int, int]
    updated_at: int
    camera_origin: tuple[float, float]
    elapsed: int = 0
    paused: bool = False
    logged_lines: int = 0
    credits_music_started: bool = False
    finished: bool = False


def _smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _mix(start, end, progress):
    return start + (end - start) * progress


def oracle_death_active(floor):
    scene = floor.oracle_death
    return scene is not None and not scene.finished


@lru_cache(maxsize=1)
def _load_death_sounds():
    root = (
        PROJECT_ROOT
        / "assets/audio/sounds_act_2/oracle/death"
    )
    variants = []

    for index in (1, 2):
        path = root / f"oracle_death_{index}.mp3"

        try:
            variants.append(
                pygame.mixer.Sound(str(path))
            )
        except (OSError, pygame.error):
            continue

    return tuple(variants)


def _play_death_sound(sounds):
    if pygame.mixer.get_init() is None:
        return

    variants = _load_death_sounds()

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
                * DEATH_SOUND_VOLUME,
            ),
        )
    )


def _start_oracle_death(
    game_state,
    camera,
    current_time,
    sounds,
):
    floor = game_state.floor
    phase_two = floor.oracle_phase_two
    oracle = phase_two.caster

    floor.oracle_death = OracleDeathState(
        caster=oracle,
        position=(oracle.column, oracle.row),
        updated_at=current_time,
        camera_origin=(camera.x, camera.y),
    )

    oracle.oracle_death_started_at = current_time
    oracle.oracle_death_elapsed = 0
    oracle.oracle_phase_two_eye = "idle"
    oracle.oracle_render_column = None
    oracle.oracle_render_row = None
    oracle.attack_targets = []
    oracle.prepared_attack_mode = None
    oracle.attack_windup_turns_remaining = 0

    game_state.player_attack_targets = []
    game_state.act_two_stats_open = False
    game_state.act_two_journal_open = False
    game_state.player.directional_ability_aiming = False
    game_state.player.act_two.fire_bomb_aiming = False

    floor.projectiles.clear()

    if pygame.mixer.get_init() is not None:
        pygame.mixer.music.fadeout(2600)

    _play_death_sound(sounds)


def update_oracle_death(
    game_state,
    camera,
    current_time,
    sounds,
    music_volume,
):
    floor = game_state.floor
    phase_two = floor.oracle_phase_two

    if floor.oracle_death is None:
        if (
            phase_two is None
            or not phase_two.defeated_pending
        ):
            return

        _start_oracle_death(
            game_state,
            camera,
            current_time,
            sounds,
        )

    scene = floor.oracle_death

    if scene.finished:
        return

    delta = max(
        0,
        min(
            50,
            current_time - scene.updated_at,
        ),
    )
    scene.updated_at = current_time

    if not scene.paused:
        scene.elapsed += delta

    scene.caster.oracle_death_elapsed = scene.elapsed

    view_width = GAME_WIDTH / camera.zoom
    view_height = GAME_HEIGHT / camera.zoom

    focus_x = (
        (scene.position[0] + 1.0) * TILE_SIZE
        - view_width / 2
    )
    focus_y = (
        (scene.position[1] + 1.0) * TILE_SIZE
        - view_height / 2
    )

    progress = _smooth(
        scene.elapsed / CAMERA_FOCUS_MS
    )

    camera.x = _mix(
        scene.camera_origin[0],
        focus_x,
        progress,
    )
    camera.y = _mix(
        scene.camera_origin[1],
        focus_y,
        progress,
    )
    camera.target_x = camera.x
    camera.target_y = camera.y
    camera.floor_index = game_state.floor_index
    camera.updated_at = current_time

    while (
        scene.logged_lines < len(DIALOGUE)
        and scene.elapsed
        >= (
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

    if scene.elapsed >= CREDITS_START_MS:
        start_oracle_credits(
            game_state,
            scene,
            music_volume,
        )


def handle_oracle_death_event(
    floor,
    event,
    mouse_position=None,
):
    scene = floor.oracle_death

    if scene is None or scene.finished:
        return None

    if event.type == pygame.WINDOWFOCUSLOST:
        scene.paused = True
        return None

    if event.type == pygame.WINDOWFOCUSGAINED:
        scene.paused = False
        return None

    if scene.elapsed < CREDITS_START_MS:
        return None

    return handle_oracle_credits_event(
        event,
        scene.elapsed - CREDITS_START_MS,
        mouse_position,
    )


@lru_cache(maxsize=1)
def _load_death_frames():
    root = (
        PROJECT_ROOT
        / "assets/sprites/act_2/bosses/oracle/death"
    )
    maximum_width = TILE_SIZE * 2
    maximum_height = TILE_SIZE * 2 - 12
    frames = []

    for index in range(3):
        source = pygame.image.load(
            str(
                root
                / f"oracle_death_original_{index:02d}.png"
            )
        ).convert_alpha()

        bounds = source.get_bounding_rect(
            min_alpha=8,
        )

        if bounds.width > 0 and bounds.height > 0:
            source = source.subsurface(
                bounds,
            ).copy()

        scale = min(
            maximum_width / source.get_width(),
            maximum_height / source.get_height(),
        )
        size = (
            max(
                1,
                round(source.get_width() * scale),
            ),
            max(
                1,
                round(source.get_height() * scale),
            ),
        )

        frames.append(
            pygame.transform.scale(
                source,
                size,
            )
        )

    return tuple(frames)


def _draw_death_frame(
    surface,
    frame,
    anchor,
    angle,
    opacity,
):
    image = pygame.transform.rotate(
        frame,
        angle,
    )

    if opacity < 1.0:
        image = image.copy()
        image.set_alpha(
            round(255 * opacity)
        )

    surface.blit(
        image,
        image.get_rect(
            midbottom=(
                round(anchor[0]),
                round(anchor[1]),
            ),
        ),
    )


def draw_oracle_death_sprite(
    screen,
    enemy,
):
    if enemy.oracle_death_started_at < 0:
        return False

    elapsed = enemy.oracle_death_elapsed
    frames = _load_death_frames()

    if elapsed < FIRST_FRAME_END_MS:
        progress = _smooth(
            elapsed / FIRST_FRAME_END_MS
        )
        offset_x = (
            math.sin(elapsed / 210) * 0.65
            + progress
        )
        offset_y = (
            -10.0
            + progress * 5.0
            + math.sin(elapsed / 290) * 0.25
        )
        angle = (
            math.sin(elapsed / 360) * 0.35
            + progress * 0.8
        )

        fade_progress = _smooth(
            (
                elapsed
                - (
                    FIRST_FRAME_END_MS
                    - DEATH_CROSSFADE_MS
                )
            )
            / DEATH_CROSSFADE_MS
        )

        visible_frames = (
            (frames[0], 1.0 - fade_progress),
            (frames[1], fade_progress),
        )
    elif elapsed < SECOND_FRAME_END_MS:
        local_time = (
            elapsed - FIRST_FRAME_END_MS
        )
        duration = (
            SECOND_FRAME_END_MS
            - FIRST_FRAME_END_MS
        )
        progress = _smooth(
            local_time / duration
        )
        offset_x = (
            1.0
            + progress * 2.0
            + math.sin(elapsed / 330) * 0.35
        )
        offset_y = (
            -5.0
            + progress * 5.0
        )
        angle = (
            0.8
            + progress * 3.2
        )

        fade_progress = _smooth(
            (
                elapsed
                - (
                    SECOND_FRAME_END_MS
                    - DEATH_CROSSFADE_MS
                )
            )
            / DEATH_CROSSFADE_MS
        )

        visible_frames = (
            (frames[1], 1.0 - fade_progress),
            (frames[2], fade_progress),
        )
    else:
        offset_x = 3.0
        offset_y = 0.0
        angle = 0.0
        visible_frames = (
            (frames[2], 1.0),
        )

    size = TILE_SIZE * 2
    surface = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )
    anchor = (
        TILE_SIZE + offset_x,
        size + offset_y,
    )

    for frame, opacity in visible_frames:
        if opacity <= 0.0:
            continue

        _draw_death_frame(
            surface,
            frame,
            anchor,
            angle,
            opacity,
        )

    screen.blit(
        surface,
        (
            MAP_OFFSET_X
            + enemy.column * TILE_SIZE,
            MAP_OFFSET_Y
            + enemy.row * TILE_SIZE,
        ),
    )

    return True


def _draw_collapse_pulse(
    surface,
    center,
    elapsed,
    start_time,
):
    progress = (
        elapsed - start_time
    ) / 620

    if progress < 0.0 or progress >= 1.0:
        return

    visibility = 1.0 - progress
    radius = round(
        TILE_SIZE * (
            0.18 + progress * 0.72
        )
    )

    pygame.draw.circle(
        surface,
        (
            126,
            35,
            42,
            round(105 * visibility),
        ),
        center,
        radius,
        max(
            1,
            round(3 * visibility),
        ),
    )

    pygame.draw.circle(
        surface,
        (
            42,
            12,
            18,
            round(125 * visibility),
        ),
        center,
        round(radius * 0.68),
        max(
            1,
            round(2 * visibility),
        ),
    )


def draw_oracle_death_fx(
    screen,
    floor,
    current_time,
):
    scene = floor.oracle_death

    if scene is None:
        return

    elapsed = scene.elapsed
    size = TILE_SIZE * 2
    effect = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )
    center = (
        TILE_SIZE,
        round(TILE_SIZE * 1.35),
    )

    _draw_collapse_pulse(
        effect,
        center,
        elapsed,
        FIRST_FRAME_END_MS - 250,
    )
    _draw_collapse_pulse(
        effect,
        center,
        elapsed,
        SECOND_FRAME_END_MS - 180,
    )

    dust_start = FIRST_FRAME_END_MS - 400
    dust_end = SECOND_FRAME_END_MS + 1500

    if dust_start <= elapsed < dust_end:
        local_time = elapsed - dust_start

        for index in range(12):
            delay = index * 105
            age = local_time - delay

            if age < 0:
                continue

            lifetime = 1250 + index % 4 * 160
            progress = age / lifetime

            if progress >= 1.0:
                continue

            direction = (
                -1
                if index % 2 == 0
                else 1
            )
            distance = 6 + index % 4 * 6
            x = (
                center[0]
                + direction
                * distance
                * _smooth(progress)
                + math.sin(
                    age / 190 + index
                )
                * 1.5
            )
            y = (
                size - 10
                - progress
                * (
                    9 + index % 3 * 4
                )
            )
            alpha = round(
                55
                * math.sin(
                    math.pi * progress
                )
            )
            radius = 2 + index % 2

            pygame.draw.circle(
                effect,
                (
                    88,
                    74,
                    70,
                    alpha,
                ),
                (
                    round(x),
                    round(y),
                ),
                radius,
            )

    screen.blit(
        effect,
        (
            MAP_OFFSET_X
            + scene.position[0] * TILE_SIZE,
            MAP_OFFSET_Y
            + scene.position[1] * TILE_SIZE,
        ),
    )


@lru_cache(maxsize=1)
def _dialogue_font():
    return pygame.font.Font(
        str(FONT_ROOT / "Almendra-Bold.ttf"),
        34,
    )


def _dialogue_surface(text):
    font = _dialogue_font()
    foreground = font.render(
        text,
        True,
        (198, 188, 174),
    )
    outline = font.render(
        text,
        True,
        (8, 6, 7),
    )
    surface = pygame.Surface(
        (
            foreground.get_width() + 18,
            foreground.get_height() + 18,
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
        (-3, -3),
        (0, -3),
        (3, -3),
        (-3, 0),
        (3, 0),
        (-3, 3),
        (0, 3),
        (3, 3),
    ):
        surface.blit(
            outline,
            rectangle.move(dx, dy),
        )

    surface.blit(
        foreground,
        rectangle,
    )
    return surface


def draw_oracle_death_overlay(
    screen,
    world_frame,
    floor,
    mouse_position=None,
):
    if (
        world_frame is None
        or not oracle_death_active(floor)
    ):
        return

    scene = floor.oracle_death
    elapsed = scene.elapsed
    if elapsed >= CREDITS_START_MS:
        draw_oracle_credits(
            screen,
            elapsed - CREDITS_START_MS,
            mouse_position,
        )
        return
    hud_visibility = (
        1.0
        - _smooth(elapsed / HUD_FADE_MS)
    )

    complete_frame = screen.copy()
    screen.blit(world_frame, (0, 0))
    complete_frame.set_alpha(
        round(255 * hud_visibility)
    )
    screen.blit(
        complete_frame,
        (0, 0),
    )

    bar_height = round(
        72 * (1.0 - hud_visibility)
    )

    if bar_height > 0:
        pygame.draw.rect(
            screen,
            (0, 0, 0),
            (
                0,
                0,
                GAME_WIDTH,
                bar_height,
            ),
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

    if not (
            DIALOGUE_START_MS
            <= elapsed
            < DIALOGUE_END_MS
    ):
        return

    dialogue_elapsed = (
            elapsed - DIALOGUE_START_MS
    )
    index = min(
        len(DIALOGUE) - 1,
        dialogue_elapsed // DIALOGUE_LINE_MS,
    )
    local_time = (
            dialogue_elapsed % DIALOGUE_LINE_MS
    )
    alpha = min(
        _smooth(local_time / 420),
        _smooth(
            (
                    DIALOGUE_LINE_MS
                    - local_time
            )
            / 600
        ),
    )

    text = _dialogue_surface(
        DIALOGUE[index]
    )
    text.set_alpha(
        round(255 * alpha)
    )

    screen.blit(
        text,
        text.get_rect(
            center=(
                GAME_WIDTH // 2,
                GAME_HEIGHT - 112,
            ),
        ),
    )
