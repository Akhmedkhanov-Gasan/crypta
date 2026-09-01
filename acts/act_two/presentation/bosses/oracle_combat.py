import math
import random
from dataclasses import dataclass, field

import pygame

from acts.act_two.presentation.bosses.oracle_audio import (
    play_oracle_attack_sound,
)
from acts.act_two.presentation.bosses.oracle_balance import (
    ATTACK_REACTION_MS,
    CLOSE_RANGE_GRACE_TURNS,
    IMPACT_MS,
    LINE_CAST_CHANCE,
    LINE_DAMAGE,
    LINE_FLIGHT_MS,
    POST_ATTACK_RECOVERY_TURNS,
    RADIAL_CAST_CHANCE,
    RADIAL_COOLDOWN_TURNS,
    RADIAL_DAMAGE,
    RADIAL_FIRE_CELLS,
    RADIAL_FLIGHT_MS,
    SPHERE_DAMAGE,
    SPHERE_FLIGHT_MS,
    WARNING_LOCK_MS,
)
from acts.act_two.presentation.bosses.oracle_ground_fire import (
    OracleGroundFireState,
    add_oracle_ground_fire,
    advance_oracle_ground_fire,
)
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from logic import can_player_move_between, get_enemy_occupied_positions



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
    prepare_sound_pending: bool = False
    shot_sound_played: bool = False
    close_range_turns: int = 0
    radial_cooldown: int = 0
    impact_cells: tuple = ()
    ground_fire: OracleGroundFireState = field(
        default_factory=OracleGroundFireState
    )

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

    if state.phase == "flight":
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


def _radial_cells(floor, caster):
    occupied = get_enemy_occupied_positions(caster)
    minimum_column = min(column for column, _row in occupied)
    maximum_column = max(column for column, _row in occupied)
    minimum_row = min(row for _column, row in occupied)
    maximum_row = max(row for _column, row in occupied)

    cells = []

    for row in range(minimum_row - 1, maximum_row + 2):
        for column in range(
            minimum_column - 1,
            maximum_column + 2,
        ):
            position = (column, row)

            if position in occupied:
                continue

            if not (
                0 <= row < len(floor.map)
                and 0 <= column < len(floor.map[row])
            ):
                continue

            if (
                floor.map[row][column] in ("#", "S", "C", "B")
                or position in floor.barriers
            ):
                continue

            cells.append(position)

    return tuple(cells)


def _player_is_near_oracle(game_state, caster):
    position = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    return position in _radial_cells(game_state.floor, caster)


def _radial_fire_cells(cells):
    if not cells:
        return ()

    count = min(RADIAL_FIRE_CELLS, len(cells))
    return tuple(random.sample(list(cells), count))


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

    advance_oracle_ground_fire(game_state, state)

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
        state.paths = ()
        state.prepare_sound_pending = False
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

    if caster.oracle_phase == 2:
        from acts.act_two.presentation.bosses.oracle_phase_two import (
            take_oracle_phase_two_turn,
        )

        take_oracle_phase_two_turn(
            game_state,
            caster,
        )
        return

    if caster.oracle_phase != 1:
        return

    if floor.oracle_combat is None:
        floor.oracle_combat = OracleCombatState(caster=caster)

    state = floor.oracle_combat
    now = pygame.time.get_ticks()
    player_is_near = _player_is_near_oracle(
        game_state,
        caster,
    )

    if player_is_near:
        state.close_range_turns += 1
    else:
        state.close_range_turns = 0

    state.radial_cooldown = max(
        0,
        state.radial_cooldown - 1,
    )

    if (
        player_is_near
        and state.close_range_turns <= CLOSE_RANGE_GRACE_TURNS
    ):
        if state.phase == "warning":
            state.phase = "idle"
            state.cells = ()
            state.paths = ()
            state.prepare_sound_pending = False
            caster.oracle_cast_amount = 0.0
            caster.oracle_head_angle = 0.0
        return

    if state.phase in ("flight", "impact"):
        return

    if state.phase == "recovery" and state.rest > 0:
        state.rest -= 1
        return

    if state.phase == "warning":
        state.phase = "flight"
        state.started_at = now + ATTACK_REACTION_MS
        state.impact_at = state.started_at + {
            "sphere": SPHERE_FLIGHT_MS,
            "line": LINE_FLIGHT_MS,
            "radial": RADIAL_FLIGHT_MS,
        }[state.kind]
        state.lock_until = state.impact_at + IMPACT_MS
        state.shots += 1
        return

    if (
        player_is_near
        and state.radial_cooldown <= 0
        and random.random() < RADIAL_CAST_CHANCE
    ):
        cells = _radial_cells(floor, caster)

        if cells and _has_escape(game_state, cells):
            state.kind = "radial"
            state.cells = cells
            state.paths = ()
            state.phase = "warning"
            state.started_at = now
            state.impact_fx_at = -1
            state.lock_until = now + WARNING_LOCK_MS
            state.prepare_sound_pending = True
            state.shot_sound_played = False

            add_log_message(
                game_state.combat_log,
                (
                    "Oracle's eye swells with violent fire. "
                    "Retreat from the statue."
                ),
                category="warning",
            )
            return

    target = (floor.player_column, floor.player_row)
    ray = _ray_cells(floor, caster, target)

    if target not in ray:
        state.phase = "idle"
        caster.oracle_cast_amount = 0.0
        return

    kind = (
        "line"
        if random.random() < LINE_CAST_CHANCE
        else "sphere"
    )

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
            "Oracle's black fire misses.",
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
                data={
                    "enemy_type": "oracle",
                    "mode": kind,
                },
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
            data={
                "enemy_type": "oracle",
                "mode": kind,
            },
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

    if state.ground_fire.sound_pending:
        play_oracle_attack_sound(
            sounds,
            "line",
            "blast",
        )
        state.ground_fire.sound_pending = False

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
            and state.kind != "radial"
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
            state.rest = POST_ATTACK_RECOVERY_TURNS
        return False

    if (
        state.phase != "flight"
        or current_time < state.impact_at
    ):
        return False

    from acts.act_two.presentation.turn_events import (
        present_act_two_turn_events,
    )

    kind = state.kind

    if kind == "radial" and game_state.player.health > 0:
        play_oracle_attack_sound(
            sounds,
            "radial",
            "blast",
        )

    damage = {
        "sphere": SPHERE_DAMAGE,
        "line": LINE_DAMAGE,
        "radial": RADIAL_DAMAGE,
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
    state.impact_cells = state.cells
    state.impact_fx_at = current_time
    state.lock_until = current_time + IMPACT_MS

    if kind == "radial" and game_state.player.health > 0:
        state.radial_cooldown = RADIAL_COOLDOWN_TURNS
        add_oracle_ground_fire(
            state.ground_fire,
            _radial_fire_cells(state.cells),
        )

        add_log_message(
            game_state.combat_log,
            (
                "Scattered blackfire remains after "
                "Oracle's eruption."
            ),
            category="warning",
        )
    elif kind in ("sphere", "line") and game_state.player.health > 0:
        add_oracle_ground_fire(
            state.ground_fire,
            state.cells,
        )

        add_log_message(
            game_state.combat_log,
            (
                "Blackfire burns at the point of impact."
                if kind == "sphere"
                else "Blackfire remains across the arena."
            ),
            category="warning",
        )

    state.phase = "impact"

    return interrupted
