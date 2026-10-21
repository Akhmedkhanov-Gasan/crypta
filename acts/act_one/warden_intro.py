import pygame

from game.combat_log import add_log_message
from game.state import EnemyBehaviorState
from settings import TILE_SIZE


CAMERA_PAN_END_MS = 1800
BOSS_RISE_START_MS = 1100
BOSS_RISE_END_MS = 2800
DIALOGUE_START_MS = 3200
DIALOGUE_END_MS = 6800
ARCHER_APPEAR_START_MS = 6900
ARCHER_APPEAR_END_MS = 8200
INTRO_END_MS = 9000
SKIP_HOLD_MS = 1000
HUD_FADE_OUT_MS = 360
HUD_FADE_IN_MS = 800

WARDEN_LINE = (
    "The living always mistake an open door for freedom."
)


def _progress(value, start, end):
    if value <= start:
        return 0.0
    if value >= end:
        return 1.0

    progress = (value - start) / (end - start)
    return progress * progress * (3.0 - 2.0 * progress)


def warden_intro_active(floor):
    state = getattr(
        floor,
        "act_one_warden_intro",
        None,
    )
    return (
        state is not None
        and state.started
        and not state.finished
    )


def begin_warden_intro(
    game_state,
    current_time,
):
    floor = game_state.floor
    state = getattr(
        floor,
        "act_one_warden_intro",
        None,
    )

    if (
        state is None
        or state.started
        or state.finished
    ):
        return False

    state.started = True
    state.elapsed = 0
    state.skip_held_ms = 0
    state.updated_at = current_time
    floor.boss_fight_started = True

    for enemy in floor.enemies:
        if not enemy.boss_group:
            continue

        enemy.is_active = False
        enemy.is_aggro = False
        enemy.behavior_state = EnemyBehaviorState.INACTIVE

        if enemy.type == "warden":
            enemy.intro_pose_progress = 0.0
            enemy.intro_spawn_progress = 1.0
        elif enemy.type == "archer":
            enemy.intro_spawn_progress = 0.0

    add_log_message(
        game_state.combat_log,
        "The chamber seals behind the hero.",
    )

    return True


def _finish_warden_intro(
    game_state,
    current_time,
):
    floor = game_state.floor
    state = floor.act_one_warden_intro

    state.elapsed = INTRO_END_MS
    state.finished = True
    state.skip_held_ms = 0
    state.updated_at = current_time

    for enemy in floor.enemies:
        if not enemy.boss_group or enemy.health <= 0:
            continue

        enemy.intro_pose_progress = 1.0
        enemy.intro_spawn_progress = 1.0
        enemy.is_active = True
        enemy.is_aggro = True
        enemy.behavior_state = EnemyBehaviorState.CHASING

    add_log_message(
        game_state.combat_log,
        "The Crypt Warden rises.",
    )


def update_warden_intro(
    game_state,
    current_time,
    enabled,
):
    floor = game_state.floor
    state = getattr(
        floor,
        "act_one_warden_intro",
        None,
    )

    if (
        state is None
        or not state.started
        or state.finished
    ):
        return

    if state.updated_at < 0:
        state.updated_at = current_time

    delta = max(
        0,
        min(
            50,
            current_time - state.updated_at,
        ),
    )
    state.updated_at = current_time

    if not enabled:
        state.skip_held_ms = 0
        return

    state.elapsed = min(
        INTRO_END_MS,
        state.elapsed + delta,
    )

    holding_space = (
        pygame.key.get_focused()
        and pygame.key.get_pressed()[pygame.K_SPACE]
    )

    if holding_space:
        state.skip_held_ms = min(
            SKIP_HOLD_MS,
            state.skip_held_ms + delta,
        )
    else:
        state.skip_held_ms = 0

    boss_progress = _progress(
        state.elapsed,
        BOSS_RISE_START_MS,
        BOSS_RISE_END_MS,
    )
    archer_progress = _progress(
        state.elapsed,
        ARCHER_APPEAR_START_MS,
        ARCHER_APPEAR_END_MS,
    )

    for enemy in floor.enemies:
        if not enemy.boss_group:
            continue

        if enemy.type == "warden":
            enemy.intro_pose_progress = boss_progress
        elif enemy.type == "archer":
            enemy.intro_spawn_progress = archer_progress

    if (
        state.skip_held_ms >= SKIP_HOLD_MS
        or state.elapsed >= INTRO_END_MS
    ):
        _finish_warden_intro(
            game_state,
            current_time,
        )


def warden_intro_camera_focus(floor):
    state = getattr(
        floor,
        "act_one_warden_intro",
        None,
    )

    if (
        state is None
        or not state.started
        or state.finished
    ):
        return None

    warden = next(
        (
            enemy
            for enemy in floor.enemies
            if enemy.type == "warden"
            and enemy.health > 0
        ),
        None,
    )

    if warden is None:
        return None

    camera_progress = _progress(
        state.elapsed,
        0,
        CAMERA_PAN_END_MS,
    )
    player_focus = (
        floor.player_column * TILE_SIZE
        + TILE_SIZE / 2,
        floor.player_row * TILE_SIZE
        + TILE_SIZE / 2,
    )
    warden_focus = (
        warden.column * TILE_SIZE
        + TILE_SIZE / 2,
        warden.row * TILE_SIZE
        + TILE_SIZE / 5,
    )

    return (
        player_focus[0]
        + (
            warden_focus[0]
            - player_focus[0]
        )
        * camera_progress,
        player_focus[1]
        + (
            warden_focus[1]
            - player_focus[1]
        )
        * camera_progress,
    )


def warden_intro_hud_opacity(
    floor,
    current_time,
):
    state = getattr(
        floor,
        "act_one_warden_intro",
        None,
    )

    if state is None or not state.started:
        return 255

    if not state.finished:
        fade = _progress(
            state.elapsed,
            0,
            HUD_FADE_OUT_MS,
        )
        return round(
            255 * (1.0 - fade)
        )

    if state.updated_at < 0:
        return 255

    fade = _progress(
        current_time,
        state.updated_at,
        state.updated_at + HUD_FADE_IN_MS,
    )
    return round(255 * fade)


def warden_intro_enemy_visible(
    floor,
    enemy,
):
    state = getattr(
        floor,
        "act_one_warden_intro",
        None,
    )

    if (
        state is None
        or not enemy.boss_group
        or enemy.type != "archer"
    ):
        return True

    return enemy.intro_spawn_progress > 0.08
