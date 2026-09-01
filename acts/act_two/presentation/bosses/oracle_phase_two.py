import math
import random
from dataclasses import dataclass, field
from functools import lru_cache

import pygame

from acts.act_two.presentation.bosses.oracle_audio import (
    play_oracle_attack_sound,
)
from acts.act_two.presentation.bosses.oracle_balance import (
    PHASE_TWO_BLACKFIRE_CHANCE,
    PHASE_TWO_HAZARD_CELLS,
    PHASE_TWO_HAZARD_DAMAGE,
    PHASE_TWO_HAZARD_TURNS,
    PHASE_TWO_IMPACT_MS,
    PHASE_TWO_PILLAR_HINT_MS,
    PHASE_TWO_PRIMARY_DAMAGE,
    PHASE_TWO_SECONDARY_DAMAGE,
    PHASE_TWO_TELEPORT_CHANCE,
    PHASE_TWO_TELEPORT_MS,
    PHASE_TWO_RECOVERY_INTERVAL,
    PHASE_TWO_ATTACK_SEQUENCE,
    PHASE_TWO_LINE_DAMAGE,
    PHASE_TWO_CHAOS_BRANCH_CHANCE,
    PHASE_TWO_CHAOS_PATHS,
)
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState, EnemyState
from logic import (
    can_move_to,
    can_player_move_between,
    get_enemy_occupied_positions,
)
from presentation.layout import (
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    PROJECT_ROOT,
)
from settings import TILE_SIZE


@dataclass
class OraclePhaseTwoState:
    caster: object
    pillars: tuple = ()
    primary_cells: tuple = ()
    secondary_cells: tuple = ()
    secondary_kind: str = "echo"
    leave_fire_pending: bool = False
    chaos_paths: tuple = ()
    chaos_cells: tuple = ()
    attack_index: int = 0
    hazards: dict = field(default_factory=dict)
    broken_pillars: set = field(default_factory=set)
    pillar_break_started_at: dict = field(default_factory=dict)
    pillar_flash_started_at: int = -1
    impact_cells: tuple = ()
    impact_started_at: int = -1
    teleport_origin: tuple | None = None
    teleport_target: tuple | None = None
    teleport_started_at: int = -1
    prepare_sound_pending: bool = False
    blast_sound_pending: bool = False
    turn: int = 0
    head_hits: int = 0
    defeated_pending: bool = False


def initialize_oracle_phase_two(
    game_state,
    oracle,
    current_time,
):
    floor = game_state.floor

    if floor.oracle_phase_two is not None:
        return floor.oracle_phase_two

    positions = tuple(floor.boss_columns)
    pillar_count = len(positions)
    phase_health = max(
        1,
        oracle.max_health // 2,
    )
    oracle.health = phase_health

    base_health, remainder = divmod(
        phase_health,
        max(1, pillar_count),
    )
    pillars = []

    for index, position in enumerate(positions):
        column, row = position
        pillar_health = (
            base_health
            + (
                1
                if index < remainder
                else 0
            )
        )

        pillar = EnemyState(
            type="oracle_pillar",
            column=column,
            row=row,
            health=pillar_health,
            max_health=pillar_health,
            name=f"Oracle Pillar {index + 1}",
            aggro_radius=0,
            wander_chance=0.0,
            move_every=99,
            attack_kind="none",
            attack_range=0,
            damage_by_mode={},
            color=(0, 0, 0),
            sleeping_color=(0, 0, 0),
            retreat_jump_chance=0.0,
            behavior_state=EnemyBehaviorState.INACTIVE,
            is_immobile=True,
            is_active=False,
            is_summoned=True,
        )
        floor.enemies.append(pillar)
        pillars.append(pillar)

    state = OraclePhaseTwoState(
        caster=oracle,
        pillars=tuple(pillars),
        pillar_flash_started_at=current_time,
    )

    floor.oracle_phase_two = state

    oracle.bleed_turns = 0
    oracle.bleed_damage = 0
    oracle.binding_turns = 0
    oracle.stun_turns = 0
    oracle.curse_turns = 0
    oracle.attack_targets = []
    oracle.prepared_attack_mode = None
    oracle.attack_windup_turns_remaining = 0

    return state


def oracle_phase_two_pillar_at(floor, position):
    state = floor.oracle_phase_two

    if state is None:
        return None

    return next(
        (
            pillar
            for pillar in state.pillars
            if (pillar.column, pillar.row) == position
        ),
        None,
    )


def reject_oracle_phase_two_head_hit(
    game_state,
    enemy,
    attacker_name="hero",
    attacker_position=None,
):
    if enemy.type != "oracle" or enemy.oracle_phase != 2:
        return False

    state = game_state.floor.oracle_phase_two

    if state is None:
        return False

    state.head_hits += 1
    state.pillar_flash_started_at = pygame.time.get_ticks()

    game_state.emit(
        GameEvent(
            type=GameEventType.HIT,
            actor=attacker_name,
            target=enemy.name,
            origin=attacker_position,
            destination=(enemy.column, enemy.row),
            amount=0,
            data={
                "blocked": True,
                "enemy_type": "oracle",
                "mode": "phase_two_immune",
                "player_class": game_state.player.player_class,
            },
        )
    )

    add_log_message(
        game_state.combat_log,
        (
            "The blow passes through Oracle's severed vessel. "
            "The pillars answer with a violent pulse."
            if state.head_hits == 1
            else "Oracle's severed vessel rejects the blow."
        ),
        category="defense",
    )

    return True


def resolve_oracle_pillar_hit(
    game_state,
    pillar,
    damage_dealt,
):
    floor = game_state.floor
    state = floor.oracle_phase_two

    if (
        state is None
        or pillar.type != "oracle_pillar"
        or damage_dealt <= 0
    ):
        return

    position = (pillar.column, pillar.row)
    now = pygame.time.get_ticks()
    oracle = state.caster

    state.pillar_flash_started_at = now
    oracle.health = max(
        1,
        oracle.health - damage_dealt,
    )

    if pillar.health > 0:
        return

    if position in state.broken_pillars:
        return

    state.broken_pillars.add(position)
    state.pillar_break_started_at[position] = now

    living_pillars = [
        current
        for current in state.pillars
        if current.health > 0
    ]

    if living_pillars:
        add_log_message(
            game_state.combat_log,
            (
                f"{pillar.name} collapses. "
                f"{len(living_pillars)} anchors remain."
            ),
            category="warning",
        )
        return

    oracle.health = 1
    oracle.oracle_phase_two_eye = "idle"
    oracle.oracle_render_column = None
    oracle.oracle_render_row = None
    oracle.attack_targets = []
    oracle.prepared_attack_mode = None
    oracle.attack_windup_turns_remaining = 0

    state.primary_cells = ()
    state.secondary_cells = ()
    state.chaos_paths = ()
    state.chaos_cells = ()
    state.impact_cells = ()
    state.impact_started_at = -1
    state.teleport_origin = None
    state.teleport_target = None
    state.teleport_started_at = -1
    state.hazards.clear()
    state.prepare_sound_pending = False
    state.blast_sound_pending = False
    state.defeated_pending = True

    add_log_message(
        game_state.combat_log,
        "The final pillar breaks. Oracle's power collapses.",
        category="warning",
    )


def _living_pillars(state):
    return tuple(
        pillar
        for pillar in state.pillars
        if pillar.health > 0
    )


def _walkable(floor, position):
    return can_move_to(
        floor.map,
        position[0],
        position[1],
    )


def _enemy_cells(floor, ignored=None):
    occupied = set()

    for enemy in floor.enemies:
        if enemy is ignored or enemy.health <= 0:
            continue
        occupied.update(get_enemy_occupied_positions(enemy))

    return occupied


def _player_has_escape(game_state, dangerous):
    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    occupied = _enemy_cells(floor)

    for dx, dy in (
        (-1, -1),
        (0, -1),
        (1, -1),
        (-1, 0),
        (1, 0),
        (-1, 1),
        (0, 1),
        (1, 1),
    ):
        destination = (
            origin[0] + dx,
            origin[1] + dy,
        )

        if destination in dangerous or destination in occupied:
            continue

        if can_player_move_between(
            floor.map,
            origin[0],
            origin[1],
            destination[0],
            destination[1],
            floor.barriers,
        ):
            return True

    return False


def _secondary_patterns(game_state):
    floor = game_state.floor
    column = floor.player_column
    row = floor.player_row
    primary = {(column, row)}
    occupied = _enemy_cells(floor)

    candidates = [
        position
        for position in (
            (column - 1, row - 1),
            (column, row - 1),
            (column + 1, row - 1),
            (column - 1, row),
            (column + 1, row),
            (column - 1, row + 1),
            (column, row + 1),
            (column + 1, row + 1),
        )
        if (
            _walkable(floor, position)
            and position not in occupied
        )
    ]
    random.shuffle(candidates)

    for position in candidates:
        dangerous = primary | {position}

        if _player_has_escape(
            game_state,
            dangerous,
        ):
            return (position,)

    return ()

def _jagged_path(
    game_state,
    horizontal,
    reserved,
):
    floor = game_state.floor
    room = floor.boss_room

    if room is None:
        return ()

    minimum_column = room.x + 1
    maximum_column = room.x + room.width - 2
    minimum_row = room.y + 1
    maximum_row = room.y + room.height - 2
    occupied = _enemy_cells(floor)
    player_position = (
        floor.player_column,
        floor.player_row,
    )
    cells = []

    if horizontal:
        current_row = random.randint(
            minimum_row,
            maximum_row,
        )

        for column in range(
            minimum_column,
            maximum_column + 1,
        ):
            if random.random() < 0.34:
                current_row = max(
                    minimum_row,
                    min(
                        maximum_row,
                        current_row
                        + random.choice((-1, 1)),
                    ),
                )

            position = (column, current_row)

            if (
                _walkable(floor, position)
                and position not in occupied
                and position not in reserved
                and position != player_position
            ):
                cells.append(position)

            if (
                random.random()
                < PHASE_TWO_CHAOS_BRANCH_CHANCE
            ):
                branch = (
                    column,
                    current_row
                    + random.choice((-1, 1)),
                )

                if (
                    minimum_row
                    <= branch[1]
                    <= maximum_row
                    and _walkable(floor, branch)
                    and branch not in occupied
                    and branch not in reserved
                    and branch != player_position
                ):
                    cells.append(branch)
    else:
        current_column = random.randint(
            minimum_column,
            maximum_column,
        )

        for row in range(
            minimum_row,
            maximum_row + 1,
        ):
            if random.random() < 0.34:
                current_column = max(
                    minimum_column,
                    min(
                        maximum_column,
                        current_column
                        + random.choice((-1, 1)),
                    ),
                )

            position = (current_column, row)

            if (
                _walkable(floor, position)
                and position not in occupied
                and position not in reserved
                and position != player_position
            ):
                cells.append(position)

            if (
                random.random()
                < PHASE_TWO_CHAOS_BRANCH_CHANCE
            ):
                branch = (
                    current_column
                    + random.choice((-1, 1)),
                    row,
                )

                if (
                    minimum_column
                    <= branch[0]
                    <= maximum_column
                    and _walkable(floor, branch)
                    and branch not in occupied
                    and branch not in reserved
                    and branch != player_position
                ):
                    cells.append(branch)

    return tuple(
        dict.fromkeys(cells)
    )


def _chaos_paths(game_state, reserved):
    for _attempt in range(20):
        orientations = [True, False]
        random.shuffle(orientations)
        paths = []

        for index in range(
            PHASE_TWO_CHAOS_PATHS
        ):
            path = _jagged_path(
                game_state,
                orientations[index % 2],
                reserved,
            )

            if path:
                paths.append(path)

        cells = {
            cell
            for path in paths
            for cell in path
        }

        if (
            cells
            and _player_has_escape(
                game_state,
                set(reserved) | cells,
            )
        ):
            return tuple(paths)

    return ()


def _valid_teleport_positions(game_state, caster):
    floor = game_state.floor
    room = floor.boss_room

    if room is None:
        return ()

    blocked = _enemy_cells(floor, ignored=caster)
    blocked.add((floor.player_column, floor.player_row))
    positions = []

    for row in range(room.y, room.y + room.height - 1):
        for column in range(room.x, room.x + room.width - 1):
            footprint = {
                (column, row),
                (column + 1, row),
                (column, row + 1),
                (column + 1, row + 1),
            }

            if footprint & blocked:
                continue

            if not all(
                _walkable(floor, position)
                for position in footprint
            ):
                continue

            if (column, row) == (caster.column, caster.row):
                continue

            positions.append((column, row))

    return tuple(positions)


def _teleport(game_state, state, current_time):
    caster = state.caster
    positions = _valid_teleport_positions(
        game_state,
        caster,
    )

    if not positions:
        return

    player_position = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )

    preferred = [
        position
        for position in positions
        if 1 <= max(
            abs(position[0] - player_position[0]),
            abs(position[1] - player_position[1]),
        ) <= 5
    ]

    target = random.choice(preferred or list(positions))
    origin = (
        caster.oracle_render_column
        if caster.oracle_render_column is not None
        else float(caster.column),
        caster.oracle_render_row
        if caster.oracle_render_row is not None
        else float(caster.row),
    )

    state.teleport_origin = origin
    state.teleport_target = target
    state.teleport_started_at = current_time

    caster.column, caster.row = target
    caster.oracle_render_column = origin[0]
    caster.oracle_render_row = origin[1]


def _damage_player(game_state, state, damage, mode, dodgeable):
    from systems.player_combat import damage_player

    player = game_state.player
    floor = game_state.floor
    position = (floor.player_column, floor.player_row)

    if player.health <= 0:
        return

    if dodgeable and random.random() < player.dodge_chance:
        game_state.emit(
            GameEvent(
                type=GameEventType.DODGE,
                actor=state.caster.name,
                target="hero",
                origin=(
                    state.caster.column,
                    state.caster.row,
                ),
                destination=position,
                data={
                    "enemy_type": "oracle",
                    "mode": mode,
                },
            )
        )
        add_log_message(
            game_state.combat_log,
            "The hero evades Oracle's assault.",
            category="defense",
        )
        return

    dealt = damage_player(
        game_state,
        damage,
        damage_kind="magic",
    )

    game_state.emit(
        GameEvent(
            type=GameEventType.HIT,
            actor=state.caster.name,
            target="hero",
            origin=(
                state.caster.column,
                state.caster.row,
            ),
            destination=position,
            amount=dealt,
            data={
                "enemy_type": "oracle",
                "mode": mode,
            },
        )
    )

    add_log_message(
        game_state.combat_log,
        f"Oracle's {mode.replace('_', ' ')} deals {dealt} damage.",
        category="enemy_attack",
    )

    if player.invisibility_turns > 0 and dealt > 0:
        player.invisibility_turns = 0

    if player.health <= 0:
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor="hero",
                destination=position,
                data={"cause": state.caster.name},
            )
        )
        add_log_message(
            game_state.combat_log,
            "The hero has fallen.",
            category="death",
        )


def _advance_hazards(game_state, state):
    position = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )

    if position in state.hazards:
        _damage_player(
            game_state,
            state,
            PHASE_TWO_HAZARD_DAMAGE,
            "living black fire",
            False,
        )

    remaining = {}

    for cell, turns in state.hazards.items():
        if turns > 1:
            remaining[cell] = turns - 1

    state.hazards = remaining


def advance_oracle_phase_two_hazards(game_state):
    state = game_state.floor.oracle_phase_two

    if (
        state is None
        or state.defeated_pending
        or game_state.player.health <= 0
        or not state.hazards
    ):
        return

    _advance_hazards(
        game_state,
        state,
    )


def _resolve_attacks(game_state, state, current_time):
    if (
        not state.primary_cells
        and not state.secondary_cells
        and not state.chaos_cells
    ):
        return

    player_position = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    point_cells = tuple(
        dict.fromkeys(
            state.primary_cells
            + state.secondary_cells
        )
    )
    impact_cells = tuple(
        dict.fromkeys(
            point_cells
            + state.chaos_cells
        )
    )

    state.impact_cells = impact_cells
    state.impact_started_at = current_time
    state.blast_sound_pending = True

    if player_position in state.primary_cells:
        _damage_player(
            game_state,
            state,
            PHASE_TWO_PRIMARY_DAMAGE,
            "gaze",
            True,
        )

    if (
        game_state.player.health > 0
        and player_position in state.secondary_cells
    ):
        _damage_player(
            game_state,
            state,
            PHASE_TWO_SECONDARY_DAMAGE,
            "echo",
            True,
        )

    if (
        game_state.player.health > 0
        and player_position in state.chaos_cells
    ):
        _damage_player(
            game_state,
            state,
            PHASE_TWO_LINE_DAMAGE,
            "rupture wave",
            True,
        )

    occupied = _enemy_cells(
        game_state.floor,
    )

    chaos_fire = [
        cell
        for cell in state.chaos_cells
        if cell not in occupied
    ]

    for cell in chaos_fire:
        state.hazards[cell] = max(
            state.hazards.get(cell, 0),
            PHASE_TWO_HAZARD_TURNS,
        )

    if state.leave_fire_pending:
        point_fire = [
            cell
            for cell in point_cells
            if cell not in occupied
        ]
        count = min(
            PHASE_TWO_HAZARD_CELLS,
            len(point_fire),
        )

        if count > 0:
            for cell in random.sample(
                point_fire,
                count,
            ):
                state.hazards[cell] = max(
                    state.hazards.get(cell, 0),
                    PHASE_TWO_HAZARD_TURNS,
                )

    state.primary_cells = ()
    state.secondary_cells = ()
    state.chaos_paths = ()
    state.chaos_cells = ()
    state.leave_fire_pending = False


def _prepare_attacks(
    game_state,
    state,
    attack_kind,
):
    floor = game_state.floor
    target = (
        floor.player_column,
        floor.player_row,
    )
    secondary = (
        _secondary_patterns(game_state)
        if attack_kind == "double"
        else ()
    )
    reserved = {
        target,
        *secondary,
    }
    chaos_paths = _chaos_paths(
        game_state,
        reserved,
    )
    chaos_cells = tuple(
        dict.fromkeys(
            cell
            for path in chaos_paths
            for cell in path
        )
    )

    state.primary_cells = (target,)
    state.secondary_cells = secondary
    state.secondary_kind = "echo"
    state.chaos_paths = chaos_paths
    state.chaos_cells = chaos_cells
    state.leave_fire_pending = (
        random.random()
        < PHASE_TWO_BLACKFIRE_CHANCE
    )
    state.prepare_sound_pending = True
    state.caster.oracle_phase_two_eye = "shockwave"

    message = (
        "Oracle marks two possible steps."
        if secondary
        else "Oracle fixes its gaze upon the hero."
    )

    if chaos_cells:
        message += " Rupture waves spread blindly through the hall."

    if state.leave_fire_pending:
        message += " Black fire gathers beneath the gaze."

    add_log_message(
        game_state.combat_log,
        message,
        category="warning",
    )


def take_oracle_phase_two_turn(game_state, caster):
    floor = game_state.floor
    state = floor.oracle_phase_two
    current_time = pygame.time.get_ticks()

    if state is None:
        state = initialize_oracle_phase_two(
            game_state,
            caster,
            current_time,
        )

    if state.defeated_pending or game_state.player.health <= 0:
        return

    _resolve_attacks(
        game_state,
        state,
        current_time,
    )

    if game_state.player.health <= 0:
        return

    state.turn += 1

    recovery_turn = (
        state.turn
        % PHASE_TWO_RECOVERY_INTERVAL
        == 0
    )

    if recovery_turn:
        state.primary_cells = ()
        state.secondary_cells = ()
        state.chaos_paths = ()
        state.chaos_cells = ()
        state.leave_fire_pending = False
        state.prepare_sound_pending = False
        caster.oracle_phase_two_eye = "idle"

        add_log_message(
            game_state.combat_log,
            "Oracle's severed vessel recoils. Strike the pillars.",
            category="warning",
        )
        return

    should_teleport = (
        caster.oracle_phase_two_opening_attack_pending
        or random.random() < PHASE_TWO_TELEPORT_CHANCE
    )

    if should_teleport:
        _teleport(
            game_state,
            state,
            current_time,
        )

    caster.oracle_phase_two_opening_attack_pending = False

    attack_kind = PHASE_TWO_ATTACK_SEQUENCE[
        state.attack_index
        % len(PHASE_TWO_ATTACK_SEQUENCE)
    ]
    state.attack_index += 1

    _prepare_attacks(
        game_state,
        state,
        attack_kind,
    )


def update_oracle_phase_two(
    game_state,
    current_time,
    sounds,
):
    state = game_state.floor.oracle_phase_two

    if state is None:
        return

    caster = state.caster

    if state.prepare_sound_pending:
        play_oracle_attack_sound(
            sounds,
            "line",
            "prepare",
        )
        state.prepare_sound_pending = False

    if state.blast_sound_pending:
        play_oracle_attack_sound(
            sounds,
            "line",
            "blast",
        )
        state.blast_sound_pending = False

    if (
        state.teleport_started_at >= 0
        and state.teleport_origin is not None
        and state.teleport_target is not None
    ):
        progress = max(
            0.0,
            min(
                1.0,
                (
                    current_time - state.teleport_started_at
                )
                / PHASE_TWO_TELEPORT_MS,
            ),
        )
        smooth = progress * progress * (3.0 - 2.0 * progress)

        caster.oracle_render_column = (
            state.teleport_origin[0]
            + (
                state.teleport_target[0]
                - state.teleport_origin[0]
            )
            * smooth
        )
        caster.oracle_render_row = (
            state.teleport_origin[1]
            + (
                state.teleport_target[1]
                - state.teleport_origin[1]
            )
            * smooth
        )

        if progress >= 1.0:
            caster.oracle_render_column = None
            caster.oracle_render_row = None
            state.teleport_origin = None
            state.teleport_target = None
            state.teleport_started_at = -1

    if (
        not state.primary_cells
        and not state.secondary_cells
        and not state.defeated_pending
    ):
        caster.oracle_phase_two_eye = "idle"


def _cell_position(cell):
    return (
        MAP_OFFSET_X + cell[0] * TILE_SIZE,
        MAP_OFFSET_Y + cell[1] * TILE_SIZE,
    )


def _draw_warning_cell(
    screen,
    cell,
    color,
    current_time,
    kind,
):
    position = _cell_position(cell)
    phase = (
        current_time / 170
        + cell[0] * 0.41
        + cell[1] * 0.27
    )
    pulse = (math.sin(phase) + 1.0) * 0.5
    rotation = current_time / 520
    center = TILE_SIZE // 2
    surface = pygame.Surface(
        (TILE_SIZE, TILE_SIZE),
        pygame.SRCALPHA,
    )

    pygame.draw.rect(
        surface,
        (
            12,
            3,
            8,
            round(75 + pulse * 35),
        ),
        surface.get_rect().inflate(-3, -3),
    )
    pygame.draw.rect(
        surface,
        (
            *color,
            round(125 + pulse * 85),
        ),
        surface.get_rect().inflate(-3, -3),
        2,
    )
    pygame.draw.rect(
        surface,
        (
            *color,
            round(55 + pulse * 45),
        ),
        surface.get_rect().inflate(-8, -8),
        1,
    )

    radius = round(10 + pulse * 2)
    diamond = []

    for index in range(4):
        angle = (
            rotation
            + math.pi * 0.25
            + index * math.pi * 0.5
        )
        diamond.append(
            (
                round(
                    center
                    + math.cos(angle) * radius
                ),
                round(
                    center
                    + math.sin(angle) * radius
                ),
            )
        )

    pygame.draw.polygon(
        surface,
        (
            *color,
            round(150 + pulse * 75),
        ),
        diamond,
        2,
    )
    pygame.draw.circle(
        surface,
        (
            224,
            111,
            106,
            round(160 + pulse * 80),
        ),
        (center, center),
        round(5 + pulse * 2),
        1,
    )
    pygame.draw.circle(
        surface,
        (
            244,
            178,
            156,
            round(180 + pulse * 70),
        ),
        (center, center),
        2,
    )

    if kind == "horizontal":
        pygame.draw.line(
            surface,
            (
                *color,
                round(190 + pulse * 55),
            ),
            (4, center),
            (TILE_SIZE - 4, center),
            2,
        )
    elif kind == "vertical":
        pygame.draw.line(
            surface,
            (
                *color,
                round(190 + pulse * 55),
            ),
            (center, 4),
            (center, TILE_SIZE - 4),
            2,
        )
    elif kind == "chaos":
        pygame.draw.line(
            surface,
            (
                *color,
                round(210 + pulse * 45),
            ),
            (5, center + 7),
            (center - 5, center - 4),
            2,
        )
        pygame.draw.line(
            surface,
            (
                218,
                78,
                82,
                round(175 + pulse * 70),
            ),
            (center - 5, center - 4),
            (center + 3, center + 3),
            2,
        )
        pygame.draw.line(
            surface,
            (
                *color,
                round(210 + pulse * 45),
            ),
            (center + 3, center + 3),
            (TILE_SIZE - 5, center - 8),
            2,
        )
    else:
        for index in range(4):
            angle = index * math.pi * 0.5
            inner = (
                round(
                    center
                    + math.cos(angle) * 7
                ),
                round(
                    center
                    + math.sin(angle) * 7
                ),
            )
            outer = (
                round(
                    center
                    + math.cos(angle) * 13
                ),
                round(
                    center
                    + math.sin(angle) * 13
                ),
            )
            pygame.draw.line(
                surface,
                (
                    *color,
                    round(115 + pulse * 85),
                ),
                inner,
                outer,
                1,
            )

    corner_length = 6

    for corner_x, corner_y, dx, dy in (
        (3, 3, 1, 1),
        (TILE_SIZE - 4, 3, -1, 1),
        (3, TILE_SIZE - 4, 1, -1),
        (TILE_SIZE - 4, TILE_SIZE - 4, -1, -1),
    ):
        pygame.draw.line(
            surface,
            (
                *color,
                round(100 + pulse * 70),
            ),
            (corner_x, corner_y),
            (
                corner_x + dx * corner_length,
                corner_y,
            ),
            1,
        )
        pygame.draw.line(
            surface,
            (
                *color,
                round(100 + pulse * 70),
            ),
            (corner_x, corner_y),
            (
                corner_x,
                corner_y + dy * corner_length,
            ),
            1,
        )

    screen.blit(
        surface,
        position,
    )

@lru_cache(maxsize=1)
def _load_phase_two_blackfire():
    root = (
            PROJECT_ROOT
            / "assets/sprites/act_2/bosses/oracle/blackfire"
    )
    frames = []

    for index in range(5):
        source = pygame.image.load(
            str(
                root
                / f"blackfire_{index:02d}.png"
            )
        ).convert_alpha()
        frames.append(
            pygame.transform.scale(
                source,
                (TILE_SIZE, TILE_SIZE),
            )
        )

    return tuple(frames)

def _draw_hazard_cell(screen, cell, current_time):
    position = _cell_position(cell)
    frames = _load_phase_two_blackfire()
    frame = (
        (
            current_time
            + cell[0] * 71
            + cell[1] * 113
        )
        // 120
    ) % len(frames)

    screen.blit(
        frames[frame],
        position,
    )


def draw_oracle_phase_two_fx(
    screen,
    floor,
    current_time,
):
    state = floor.oracle_phase_two

    if state is None:
        return
    _draw_chaos_paths(
        screen,
        state.chaos_paths,
        current_time,
    )

    for cell in state.chaos_cells:
        if cell in floor.visible_cells:
            _draw_warning_cell(
                screen,
                cell,
                (105, 20, 32),
                current_time,
                "chaos",
            )
    for cell in state.hazards:
        if cell in floor.visible_cells:
            _draw_hazard_cell(
                screen,
                cell,
                current_time,
            )

    for cell in state.secondary_cells:
        if cell in floor.visible_cells:
            _draw_warning_cell(
                screen,
                cell,
                (118, 25, 35),
                current_time,
                state.secondary_kind,
            )

    for cell in state.primary_cells:
        if cell in floor.visible_cells:
            _draw_warning_cell(
                screen,
                cell,
                (190, 42, 45),
                current_time,
                "gaze",
            )

    if (
        state.impact_started_at >= 0
        and current_time - state.impact_started_at
        < PHASE_TWO_IMPACT_MS
    ):
        progress = (
            current_time - state.impact_started_at
        ) / PHASE_TWO_IMPACT_MS
        visibility = 1.0 - progress

        for cell in state.impact_cells:
            if cell not in floor.visible_cells:
                continue

            surface = pygame.Surface(
                (TILE_SIZE, TILE_SIZE),
                pygame.SRCALPHA,
            )
            center = (
                TILE_SIZE // 2,
                TILE_SIZE // 2,
            )
            radius = round(
                5 + progress * (TILE_SIZE * 0.42)
            )
            alpha = round(
                210 * visibility
            )

            pygame.draw.circle(
                surface,
                (
                    157,
                    35,
                    45,
                    alpha,
                ),
                center,
                radius,
                max(
                    1,
                    round(3 * visibility),
                ),
            )

            points = []

            for index in range(4):
                angle = (
                    current_time / 190
                    + index * math.pi * 0.5
                )
                points.append(
                    (
                        round(
                            center[0]
                            + math.cos(angle)
                            * radius
                            * 0.72
                        ),
                        round(
                            center[1]
                            + math.sin(angle)
                            * radius
                            * 0.72
                        ),
                    )
                )

            pygame.draw.polygon(
                surface,
                (
                    218,
                    86,
                    76,
                    round(175 * visibility),
                ),
                points,
                max(
                    1,
                    round(2 * visibility),
                ),
            )

            for index in range(6):
                angle = (
                    index * math.tau / 6
                    + cell[0] * 0.37
                    + cell[1] * 0.19
                )
                inner_radius = radius * 0.35
                outer_radius = radius * 0.95
                start = (
                    round(
                        center[0]
                        + math.cos(angle)
                        * inner_radius
                    ),
                    round(
                        center[1]
                        + math.sin(angle)
                        * inner_radius
                    ),
                )
                end = (
                    round(
                        center[0]
                        + math.cos(angle)
                        * outer_radius
                    ),
                    round(
                        center[1]
                        + math.sin(angle)
                        * outer_radius
                    ),
                )

                pygame.draw.line(
                    surface,
                    (
                        192,
                        55,
                        59,
                        round(150 * visibility),
                    ),
                    start,
                    end,
                    1,
                )

            screen.blit(
                surface,
                _cell_position(cell),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

    if (
        state.teleport_started_at >= 0
        and state.teleport_origin is not None
        and state.teleport_target is not None
    ):
        progress = max(
            0.0,
            min(
                1.0,
                (
                    current_time - state.teleport_started_at
                )
                / PHASE_TWO_TELEPORT_MS,
            ),
        )
        effect = pygame.Surface(
            (TILE_SIZE * 3, TILE_SIZE * 3),
            pygame.SRCALPHA,
        )
        center = (
            effect.get_width() // 2,
            effect.get_height() // 2,
        )
        radius = round(
            TILE_SIZE * (0.4 + progress * 0.9)
        )
        alpha = round(150 * (1.0 - progress))

        pygame.draw.circle(
            effect,
            (105, 18, 30, alpha),
            center,
            radius,
            3,
        )

        for position in (
            state.teleport_origin,
            state.teleport_target,
        ):
            screen.blit(
                effect,
                (
                    MAP_OFFSET_X
                    + round(position[0] * TILE_SIZE)
                    - TILE_SIZE // 2,
                    MAP_OFFSET_Y
                    + round(position[1] * TILE_SIZE)
                    - TILE_SIZE // 2,
                ),
            )


def _draw_chaos_paths(
    screen,
    paths,
    current_time,
):
    pulse = (
        math.sin(current_time / 105)
        + 1.0
    ) * 0.5
    overlay = pygame.Surface(
        screen.get_size(),
        pygame.SRCALPHA,
    )

    for path in paths:
        for first, second in zip(
            path,
            path[1:],
        ):
            if max(
                abs(first[0] - second[0]),
                abs(first[1] - second[1]),
            ) > 1:
                continue

            first_center = (
                MAP_OFFSET_X
                + first[0] * TILE_SIZE
                + TILE_SIZE // 2,
                MAP_OFFSET_Y
                + first[1] * TILE_SIZE
                + TILE_SIZE // 2,
            )
            second_center = (
                MAP_OFFSET_X
                + second[0] * TILE_SIZE
                + TILE_SIZE // 2,
                MAP_OFFSET_Y
                + second[1] * TILE_SIZE
                + TILE_SIZE // 2,
            )
            middle = (
                round(
                    (first_center[0] + second_center[0])
                    / 2
                    + math.sin(
                        current_time / 90
                        + first[0]
                        + second[1]
                    )
                    * 4
                ),
                round(
                    (first_center[1] + second_center[1])
                    / 2
                    + math.cos(
                        current_time / 110
                        + first[1]
                        + second[0]
                    )
                    * 4
                ),
            )

            pygame.draw.lines(
                overlay,
                (
                    18,
                    3,
                    8,
                    round(125 + pulse * 45),
                ),
                False,
                (
                    first_center,
                    middle,
                    second_center,
                ),
                7,
            )
            pygame.draw.lines(
                overlay,
                (
                    132,
                    25,
                    38,
                    round(155 + pulse * 75),
                ),
                False,
                (
                    first_center,
                    middle,
                    second_center,
                ),
                2,
            )

    screen.blit(
        overlay,
        (0, 0),
    )


def oracle_phase_two_pillar_flash(floor, current_time):
    state = floor.oracle_phase_two

    if state is None or state.pillar_flash_started_at < 0:
        return 0.0

    age = current_time - state.pillar_flash_started_at

    if age < 0 or age >= PHASE_TWO_PILLAR_HINT_MS:
        return 0.0

    progress = age / PHASE_TWO_PILLAR_HINT_MS
    return math.sin(progress * math.pi)
