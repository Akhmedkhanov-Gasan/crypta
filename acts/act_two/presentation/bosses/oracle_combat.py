import math
import random
from dataclasses import dataclass

import pygame

from acts.act_two.presentation.bosses.oracle_audio import (
    play_oracle_attack_sound,
    stop_oracle_fire_audio,
)
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from logic import can_player_move_between, get_enemy_occupied_positions


SPHERE_DAMAGE = 2
LINE_DAMAGE = 2
BLAST_DAMAGE = 3
BLACKFIRE_TURNS = 2

REACTION_MS = 260
SPHERE_FLIGHT_MS = 420
LINE_FLIGHT_MS = 560
BLAST_WINDUP_MS = 220
IMPACT_MS = 320
WARNING_LOCK_MS = 300


@dataclass
class OracleCombatState:
    caster: object
    phase: str = "idle"
    kind: str = "sphere"
    cells: tuple = ()
    paths: tuple = ()
    shots: int = 0
    rest: int = 0
    started_at: int = 0
    impact_at: int = 0
    lock_until: int = 0
    impact_fx_at: int = -1
    impact_kind: str = "sphere"
    fire_turns_remaining: int = 0
    prepare_sound_pending: bool = False
    shot_sound_played: bool = False

def finish_oracle_animation_before_action(
    game_state,
    current_time,
    sounds,
):
    state = game_state.floor.oracle_combat

    if state is None:
        return False

    if state.caster.health <= 0:
        return update_oracle_combat(
            game_state,
            current_time,
            sounds,
        )

    interrupted = False

    if state.phase in ("flight", "blast"):
        state.impact_at = current_time
        interrupted = update_oracle_combat(
            game_state,
            current_time,
            sounds,
        )

    if state.phase == "impact":
        state.lock_until = current_time
        update_oracle_combat(
            game_state,
            current_time,
            sounds,
        )

    return interrupted


def _ray_cells(floor, caster, target):
    column = caster.column
    row = caster.row
    dx = target[0] - column
    dy = target[1] - row

    if dx == 0 and dy == 0:
        return ()

    step_x = 1 if dx > 0 else -1 if dx < 0 else 0
    step_y = 1 if dy > 0 else -1 if dy < 0 else 0

    delta_x = 1 / abs(dx) if dx else math.inf
    delta_y = 1 / abs(dy) if dy else math.inf
    next_x = delta_x / 2
    next_y = delta_y / 2

    occupied = get_enemy_occupied_positions(caster)
    result = []

    for _ in range(len(floor.map) * len(floor.map[0])):
        if abs(next_x - next_y) < 0.000001:
            column += step_x
            row += step_y
            next_x += delta_x
            next_y += delta_y
        elif next_x < next_y:
            column += step_x
            next_x += delta_x
        else:
            row += step_y
            next_y += delta_y

        if not (
            0 <= row < len(floor.map)
            and 0 <= column < len(floor.map[row])
        ):
            break

        position = (column, row)

        if (
            floor.map[row][column] in ("#", "S", "C", "B")
            or position in floor.barriers
        ):
            break

        if position not in occupied:
            result.append(position)

    return tuple(result)


def _has_escape(game_state, cells):
    floor = game_state.floor
    column = floor.player_column
    row = floor.player_row
    occupied = set()

    for enemy in floor.enemies:
        if enemy.health > 0:
            occupied.update(get_enemy_occupied_positions(enemy))

    for dx, dy in (
        (-1, -1), (0, -1), (1, -1),
        (-1, 0), (1, 0),
        (-1, 1), (0, 1), (1, 1),
    ):
        destination = (column + dx, row + dy)

        if destination in cells or destination in occupied:
            continue

        if can_player_move_between(
            floor.map,
            column,
            row,
            destination[0],
            destination[1],
            floor.barriers,
        ):
            return True

    return False


def _line_paths(game_state, caster, target, primary):
    dx = target[0] - caster.column
    dy = target[1] - caster.row

    angles = [
        (-30, 30),
        (-45, 25),
        (-25, 45),
        (-45, 45),
        (-60, 30),
        (-30, 60),
    ]
    random.shuffle(angles)

    fallback = (primary,)

    for pair in angles:
        paths = [primary]
        covered = set(primary)

        for degrees in pair:
            angle = math.radians(degrees)
            destination = (
                caster.column
                + dx * math.cos(angle)
                - dy * math.sin(angle),
                caster.row
                + dx * math.sin(angle)
                + dy * math.cos(angle),
            )
            ray = _ray_cells(
                game_state.floor,
                caster,
                destination,
            )

            if len(set(ray) - covered) < 2:
                continue

            candidate = covered | set(ray)

            if not _has_escape(game_state, candidate):
                continue

            paths.append(ray)
            covered = candidate

        if len(paths) == 3:
            return tuple(paths)

        if len(paths) > len(fallback):
            fallback = tuple(paths)

    return fallback


def advance_oracle_fire(game_state):
    floor = game_state.floor
    state = floor.oracle_combat

    if state is None:
        return

    if state.caster.health <= 0:
        floor.oracle_combat = None
        return

    now = pygame.time.get_ticks()

    if state.phase == "embers":
        state.fire_turns_remaining = max(
            0,
            state.fire_turns_remaining - 1,
        )

        if state.fire_turns_remaining > 0:
            return

        state.phase = "blast"
        state.started_at = now + REACTION_MS
        state.impact_at = state.started_at + BLAST_WINDUP_MS
        state.lock_until = state.impact_at + IMPACT_MS
        return

    caster = state.caster
    interrupted = (
        caster.stun_turns > 0
        or caster.binding_turns > 0
        or caster.skip_next_movement
        or game_state.player.invisibility_turns > 0
    )

    if state.phase == "warning" and interrupted:
        state.phase = "recovery"
        state.rest = 0
        state.cells = ()
        caster.oracle_cast_amount = 0.0
        caster.oracle_head_angle = 0.0

        add_log_message(
            game_state.combat_log,
            "Oracle's casting is interrupted.",
            category="defense",
        )


def take_oracle_combat_turn(game_state, caster):
    floor = game_state.floor

    if (
        not floor.has_oracle_gate
        or floor.oracle_intro is None
        or not floor.oracle_intro.finished
        or caster.health <= 0
        or not caster.is_active
    ):
        return

    if floor.oracle_combat is None:
        floor.oracle_combat = OracleCombatState(caster=caster)

    state = floor.oracle_combat
    now = pygame.time.get_ticks()

    if state.phase in ("flight", "impact", "embers", "blast"):
        return

    if state.phase == "recovery" and state.rest > 0:
        state.rest -= 1
        return

    if state.phase == "warning":
        state.phase = "flight"
        state.started_at = now + REACTION_MS
        duration = (
            SPHERE_FLIGHT_MS
            if state.kind == "sphere"
            else LINE_FLIGHT_MS
        )
        state.impact_at = state.started_at + duration
        state.lock_until = state.impact_at + IMPACT_MS
        state.shots += 1
        return

    target = (floor.player_column, floor.player_row)
    ray = _ray_cells(floor, caster, target)

    if target not in ray:
        state.phase = "idle"
        caster.oracle_cast_amount = 0.0
        return

    kind = "line" if state.shots % 3 == 2 else "sphere"

    if kind == "line":
        paths = _line_paths(
            game_state,
            caster,
            target,
            ray,
        )
    else:
        paths = ((target,),)

    cells = tuple(
        dict.fromkeys(
            position
            for path in paths
            for position in path
        )
    )

    if not _has_escape(game_state, cells):
        kind = "sphere"
        paths = ((target,),)
        cells = (target,)

    if not _has_escape(game_state, cells):
        state.phase = "idle"
        return

    state.kind = kind
    state.cells = cells
    state.paths = paths
    state.phase = "warning"
    state.started_at = now
    state.impact_fx_at = -1
    state.lock_until = now + WARNING_LOCK_MS
    state.prepare_sound_pending = True
    state.shot_sound_played = False

    add_log_message(
        game_state.combat_log,
        (
            "Oracle gathers black fire. Move off the mark."
            if kind == "sphere"
            else "Oracle marks paths of black fire."
        ),
        category="warning",
    )


def _strike(game_state, state, damage, kind):
    from systems.player_combat import damage_player

    floor = game_state.floor
    player = game_state.player
    position = (floor.player_column, floor.player_row)
    caster = state.caster

    if player.health <= 0:
        return

    if position not in state.cells:
        add_log_message(
            game_state.combat_log,
            (
                "The blackfire erupts on empty stone."
                if kind == "blast"
                else "Oracle's black fire misses."
            ),
            category="defense",
        )
        return

    if random.random() < player.dodge_chance:
        game_state.emit(
            GameEvent(
                type=GameEventType.DODGE,
                actor=caster.name,
                target="hero",
                origin=(caster.column, caster.row),
                destination=position,
                data={"enemy_type": "oracle", "mode": kind},
            ),
        )
        add_log_message(
            game_state.combat_log,
            "The hero evades Oracle's black fire.",
            category="defense",
        )
        return

    dealt = damage_player(
        game_state,
        damage,
        damage_kind="magic",
    )

    if dealt > 0 and player.invisibility_turns > 0:
        player.invisibility_turns = 0

    game_state.emit(
        GameEvent(
            type=GameEventType.HIT,
            actor=caster.name,
            target="hero",
            origin=(caster.column, caster.row),
            destination=position,
            amount=dealt,
            data={"enemy_type": "oracle", "mode": kind},
        ),
    )
    add_log_message(
        game_state.combat_log,
        f"Oracle's black fire deals {dealt} damage.",
        category="enemy_attack",
    )

    if player.health <= 0:
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor="hero",
                destination=position,
                data={"cause": caster.name},
            ),
        )
        add_log_message(
            game_state.combat_log,
            "The hero has fallen.",
            category="death",
        )


def update_oracle_combat(game_state, current_time, sounds):
    floor = game_state.floor
    state = floor.oracle_combat

    if state is None:
        return False

    caster = state.caster

    if caster.health <= 0:
        caster.oracle_cast_amount = 0.0
        caster.oracle_head_angle = 0.0
        floor.oracle_combat = None
        return False

    if (
        game_state.player.health > 0
        and state.phase in ("warning", "flight")
    ):
        if state.prepare_sound_pending:
            play_oracle_attack_sound(
                sounds,
                state.kind,
                "prepare",
            )
            state.prepare_sound_pending = False

        if (
            state.phase == "flight"
            and not state.shot_sound_played
            and (
                current_time >= state.started_at
                or current_time >= state.impact_at
            )
        ):
            play_oracle_attack_sound(
                sounds,
                state.kind,
                "shot",
            )
            state.shot_sound_played = True

    age = max(0, current_time - state.started_at)

    if state.phase == "warning":
        caster.oracle_cast_amount = (
            0.75 + math.sin(age / 180) * 0.15
        )
        caster.oracle_head_angle = -min(1.0, age / 500)
    elif state.phase == "flight":
        progress = max(
            0.0,
            min(
                1.0,
                age / max(1, state.impact_at - state.started_at),
            ),
        )
        caster.oracle_cast_amount = 1.0
        caster.oracle_head_angle = -math.cos(math.pi * progress)
    else:
        caster.oracle_cast_amount = 0.0
        caster.oracle_head_angle = 0.0

    if state.phase == "impact":
        if current_time >= state.lock_until:
            state.phase = "recovery"
            state.rest = 1
        return False

    if (
        state.phase not in ("flight", "blast")
        or current_time < state.impact_at
    ):
        return False

    from acts.act_two.presentation.turn_events import (
        present_act_two_turn_events,
    )

    kind = "blast" if state.phase == "blast" else state.kind

    if kind == "blast":
        stop_oracle_fire_audio()

        if game_state.player.health > 0:
            play_oracle_attack_sound(
                sounds,
                "line",
                "blast",
            )

    damage = {
        "sphere": SPHERE_DAMAGE,
        "line": LINE_DAMAGE,
        "blast": BLAST_DAMAGE,
    }[kind]

    saved_events = game_state.events
    game_state.events = []

    try:
        _strike(game_state, state, damage, kind)
        interrupted = present_act_two_turn_events(
            game_state,
            current_time,
            0,
        )
        sounds.play_events(
            game_state.events,
            game_state.player.player_class,
            floor,
        )
    finally:
        game_state.events = saved_events

    state.impact_kind = kind
    state.impact_fx_at = current_time
    state.lock_until = current_time + IMPACT_MS

    if kind == "line" and game_state.player.health > 0:
        state.phase = "embers"
        state.fire_turns_remaining = BLACKFIRE_TURNS
        add_log_message(
            game_state.combat_log,
            (
                "The blackfire will erupt after "
                f"{BLACKFIRE_TURNS} actions."
            ),
            category="warning",
        )
    else:
        state.phase = "impact"

    return interrupted
