import math
from copy import deepcopy
from functools import lru_cache

import pygame


DIRECTIONS = {
    "south": 0,
    "west": 2,
    "north": 4,
    "east": 6,
}
DOOR_DURATION_MS = 640
LIGHT_DELAY_MS = 180
LIGHT_ROTATION_MS = 360
DETECTION_PAUSE_MS = 1100
LIGHT_RANGE = 4.0
LIGHT_HALF_ANGLE = math.radians(30)


def build_trial(markers, width, height, dungeon_map):
    prefix = "shadow_step_trial_"

    if not markers.get(prefix + "door"):
        return None

    def single(name):
        values = markers.get(prefix + name, [])
        if len(values) != 1:
            raise ValueError(f"Trial requires one {name} marker")
        return values[0][0]

    eyes = [
        {
            "position": position,
            "id": int(properties["eye_id"]),
            "direction": DIRECTIONS[properties["direction"]],
        }
        for position, properties in markers.get(prefix + "eye", [])
    ]
    covers = []
    seals = [
        {
            "position": position,
            "id": int(properties["seal_id"]),
        }
        for position, properties in markers.get(prefix + "seal", [])
    ]

    if len(eyes) != 4 or {eye["id"] for eye in eyes} != {1, 2, 3, 4}:
        raise ValueError("Trial requires four distinct eye IDs")

    if len(seals) != 3 or {seal["id"] for seal in seals} != {1, 2, 3}:
        raise ValueError("Trial requires three distinct seal IDs")

    door = single("door")
    return_position = single("return")
    final_seal = single("final_seal")
    positions = (
        [door, return_position, final_seal]
        + [eye["position"] for eye in eyes]
        + covers
        + [seal["position"] for seal in seals]
    )

    if len(set(positions)) != len(positions):
        raise ValueError("Trial markers must occupy distinct cells")

    for column, row in positions:
        if not (
            0 <= column < width
            and 0 <= row < height
            and dungeon_map[row][column] == "."
        ):
            raise ValueError(
                f"Trial marker must be on free floor: {(column, row)}"
            )

    if door[1] != height - 1:
        raise ValueError("Shadow Step trial requires a south entrance")

    for column, row in [door, *covers, *[eye["position"] for eye in eyes]]:
        dungeon_map[row][column] = "#"

    return {
        "bounds": (0, 0, width, height - 1),
        "door": door,
        "return": return_position,
        "final": final_seal,
        "eyes": eyes,
        "covers": covers,
        "seals": seals,
        "phase": "closed",
        "turn": 0,
        "activated": set(),
        "opening_ms": 0,
        "animation_ms": 0,
        "cooldown_ms": 0,
        "action_stage": None,
        "action_ms": 0,
        "rotation_progress": 0.0,
        "detected_by": [],
        "last_tick": None,
    }


def shift_trial(trial, offset):
    result = deepcopy(trial)

    def shifted(position):
        return position[0] + offset[0], position[1] + offset[1]

    for name in ("door", "return", "final"):
        result[name] = shifted(result[name])

    result["covers"] = [shifted(position) for position in result["covers"]]

    for name in ("eyes", "seals"):
        for item in result[name]:
            item["position"] = shifted(item["position"])

    left, top, right, bottom = result["bounds"]
    result["bounds"] = (
        left + offset[0],
        top + offset[1],
        right + offset[0],
        bottom + offset[1],
    )
    return result


def inside_trial(trial, position):
    left, top, right, bottom = trial["bounds"]
    return (
        left <= position[0] < right
        and top <= position[1] < bottom
    )


def trial_cells(trial):
    left, top, right, bottom = trial["bounds"]
    return {
        (column, row)
        for row in range(top, bottom)
        for column in range(left, right)
    }


def eye_frame(trial, eye):
    return round(eye_direction(trial, eye)) % 8


def eye_direction(trial, eye):
    progress = trial.get("rotation_progress", 0.0)
    return (eye["direction"] + trial["turn"] + progress) % 8


@lru_cache(maxsize=4096)
def _light_ray(dungeon_map, barriers, origin, bounds, radius, ray_angle):
    from systems.grid_geometry import can_reach_adjacent_cell

    source = (origin[0] + 0.5, origin[1] + 0.5)
    ray_x = math.cos(ray_angle)
    ray_y = math.sin(ray_angle)
    step_x = 1 if ray_x >= 0 else -1
    step_y = 1 if ray_y >= 0 else -1
    delta_x = 1 / abs(ray_x) if abs(ray_x) > 1e-10 else math.inf
    delta_y = 1 / abs(ray_y) if abs(ray_y) > 1e-10 else math.inf
    next_x = delta_x * 0.5
    next_y = delta_y * 0.5
    cell = origin
    distance = radius
    left, top, right, bottom = bounds

    while min(next_x, next_y) < radius:
        crossing = min(next_x, next_y)
        cross_x = next_x <= crossing + 1e-9
        cross_y = next_y <= crossing + 1e-9
        target = (
            cell[0] + (step_x if cross_x else 0),
            cell[1] + (step_y if cross_y else 0),
        )
        if (
            not (left <= target[0] < right and top <= target[1] < bottom)
            or not can_reach_adjacent_cell(dungeon_map, cell, target, barriers)
        ):
            distance = max(0.0, crossing - 0.001)
            break
        cell = target
        if cross_x:
            next_x += delta_x
        if cross_y:
            next_y += delta_y

    return source[0] + ray_x * distance, source[1] + ray_y * distance


@lru_cache(maxsize=128)
def _light_polygon(dungeon_map, barriers, origin, frame, bounds, radius, angle):
    source = (origin[0] + 0.5, origin[1] + 0.5)
    direction = math.pi / 2 + frame * math.pi / 4
    points = [source]
    ray_count = 40

    for ray_index in range(ray_count + 1):
        ray_angle = direction - angle + angle * 2 * ray_index / ray_count
        points.append(_light_ray(
            dungeon_map, barriers, origin, bounds, radius, ray_angle,
        ))

    return tuple(points)


def eye_light_polygon(floor, trial, eye):
    if trial["phase"] != "active":
        return ()

    return _light_polygon(
        tuple(floor.map),
        frozenset(floor.barriers),
        eye["position"],
        eye_direction(trial, eye),
        tuple(trial["bounds"]),
        LIGHT_RANGE,
        LIGHT_HALF_ANGLE,
    )


def _point_in_polygon(point, polygon):
    x, y = point
    inside = False
    previous_x, previous_y = polygon[-1]

    for current_x, current_y in polygon:
        if (current_y > y) != (previous_y > y):
            crossing_x = (
                (previous_x - current_x)
                * (y - current_y)
                / (previous_y - current_y)
                + current_x
            )
            if x < crossing_x:
                inside = not inside

        previous_x, previous_y = current_x, current_y

    return inside


def eye_light_cells(floor, trial, eye):
    polygon = eye_light_polygon(floor, trial, eye)

    if not polygon:
        return set()

    return {
        (column, row)
        for column, row in trial_cells(trial)
        if (
            (column, row) != trial["return"]
            and floor.map[row][column] == "."
            and _point_in_polygon(
                (column + 0.5, row + 0.5),
                polygon,
            )
        )
    }


def light_cells(floor, trial):
    result = set()

    for eye in trial["eyes"]:
        result.update(eye_light_cells(floor, trial, eye))

    return result


def advance_trial_frame(game_state, current_time):
    trial = game_state.floor.shadow_step_trial

    if trial is None:
        return

    previous = trial["last_tick"]
    trial["last_tick"] = current_time
    elapsed = 0 if previous is None else max(
        0,
        min(50, current_time - previous),
    )
    trial["cooldown_ms"] = max(0, trial["cooldown_ms"] - elapsed)

    if trial["phase"] == "closed":
        return

    trial["animation_ms"] += elapsed

    if trial["phase"] == "opening":
        trial["opening_ms"] += elapsed

        if trial["opening_ms"] >= DOOR_DURATION_MS:
            trial["opening_ms"] = DOOR_DURATION_MS
            trial["phase"] = "active"

    if trial["phase"] != "active":
        return

    stage = trial.get("action_stage")

    if stage is None:
        return

    trial["action_ms"] += elapsed

    if stage == "caught":
        if trial["action_ms"] >= DETECTION_PAUSE_MS:
            _reset_attempt(game_state, trial, current_time)
        return

    if stage == "delay":
        if trial["action_ms"] < LIGHT_DELAY_MS:
            return
        trial["action_stage"] = "rotating"
        trial["action_ms"] = 0
        if _detect_player(game_state, trial):
            return

    if trial["action_stage"] == "rotating":
        progress = min(1.0, trial["action_ms"] / LIGHT_ROTATION_MS)
        eased = progress * progress * (3.0 - 2.0 * progress)
        previous_step = round(trial.get("rotation_progress", 0.0) * 64)
        next_step = round(eased * 64)

        for step in range(previous_step + 1, next_step + 1):
            trial["rotation_progress"] = step / 64
            if _detect_player(game_state, trial):
                return

        if progress >= 1.0:
            trial["turn"] += 1
            trial["rotation_progress"] = 0.0
            trial["action_stage"] = None
            _activate_seals(game_state, trial)


def _detect_player(game_state, trial):
    from game.combat_log import add_log_message

    floor = game_state.floor
    position = (floor.player_column, floor.player_row)

    if position == trial["return"] or not inside_trial(trial, position):
        return False

    detected_by = []

    for eye in trial["eyes"]:
        dx = position[0] - eye["position"][0]
        dy = position[1] - eye["position"][1]
        distance = math.hypot(dx, dy)
        if distance > LIGHT_RANGE:
            continue
        angle = math.atan2(dy, dx)
        direction = math.pi / 2 + eye_direction(trial, eye) * math.pi / 4
        difference = (angle - direction + math.pi) % math.tau - math.pi
        if abs(difference) > LIGHT_HALF_ANGLE:
            continue
        endpoint = _light_ray(
            tuple(floor.map), frozenset(floor.barriers), eye["position"],
            tuple(trial["bounds"]), LIGHT_RANGE, angle,
        )
        reach = math.hypot(
            endpoint[0] - eye["position"][0] - 0.5,
            endpoint[1] - eye["position"][1] - 0.5,
        )
        if distance <= reach:
            detected_by.append(eye["id"])

    if not detected_by:
        return False

    trial["action_stage"] = "caught"
    trial["action_ms"] = 0
    trial["detected_by"] = detected_by
    add_log_message(game_state.combat_log, "The eye has spotted you!")
    return True


def block_trial_key(event, game_state):
    from game.combat_log import add_log_message

    trial = game_state.floor.shadow_step_trial

    if trial is None:
        return False

    if (
        trial["phase"] == "opening"
        or trial.get("action_stage") is not None
        or trial["cooldown_ms"] > 0
    ):
        return event.key != pygame.K_ESCAPE

    position = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )

    if (
        trial["phase"] == "active"
        and (
            inside_trial(trial, position)
            or position == trial["door"]
        )
        and event.key in (
            pygame.K_q,
            pygame.K_e,
            pygame.K_f,
            pygame.K_1,
            pygame.K_h,
        )
    ):
        add_log_message(
            game_state.combat_log,
            "The ritual suppresses abilities and consumables.",
        )
        return True

    return False


def _reset_attempt(game_state, trial, current_time):
    from game.combat_log import add_log_message

    floor = game_state.floor
    player = game_state.player
    origin = (floor.player_column, floor.player_row)

    player.health = max(1, (player.health + 1) // 2)
    floor.player_column, floor.player_row = trial["return"]
    player.movement_origin = None
    player.movement_animation_started_at = 0
    player.teleport_camera_origin = origin
    player.teleport_transition_started_at = current_time
    trial["activated"].clear()
    trial["turn"] = 0
    trial["rotation_progress"] = 0.0
    trial["action_stage"] = None
    trial["action_ms"] = 0
    trial["detected_by"] = []
    trial["cooldown_ms"] = 600
    game_state.clear_events()

    add_log_message(
        game_state.combat_log,
        "The eye found you. The seals have faded.",
    )


def handle_trial_action(game_state, event, direction):
    from application.directional_input import WAIT_KEYS
    from game.combat_log import add_log_message
    from game.events import GameEvent, GameEventType
    from systems.grid_geometry import can_reach_adjacent_cell

    floor = game_state.floor
    trial = floor.shadow_step_trial

    if trial is None:
        return None

    origin = (floor.player_column, floor.player_row)
    dx, dy = direction
    target = (origin[0] + dx, origin[1] + dy)
    near_trial = (
        inside_trial(trial, origin)
        or origin == trial["door"]
        or target == trial["door"]
    )

    if not near_trial:
        return None

    if hasattr(event, "auto_move_revision"):
        return False

    if (
        trial["phase"] == "opening"
        or trial["cooldown_ms"] > 0
        or trial.get("action_stage") is not None
    ):
        return False

    if trial["phase"] == "closed":
        if target != trial["door"] or abs(dx) + abs(dy) != 1:
            return None

        if game_state.player.subclass != "assassin":
            add_log_message(
                game_state.combat_log,
                "Only an assassin may enter this sanctuary.",
            )
            return False

        trial["phase"] = "opening"
        trial["opening_ms"] = 0
        trial["animation_ms"] = 0
        trial["last_tick"] = pygame.time.get_ticks()
        game_state.player.teleport_aiming = False
        game_state.player.teleport_target = None
        game_state.player.ultimate_aiming = False
        game_state.player.ultimate_targets.clear()
        add_log_message(game_state.combat_log, "The shadow gate opens.")
        return False

    waiting = event.key in WAIT_KEYS

    if not waiting:
        if dx == 0 and dy == 0:
            return None

        if max(abs(dx), abs(dy)) != 1:
            return False

        if not (
            0 <= target[1] < len(floor.map)
            and 0 <= target[0] < len(floor.map[target[1]])
        ):
            return False

        if (
            target != trial["door"]
            and floor.map[target[1]][target[0]] != "."
        ):
            return False

        if not can_reach_adjacent_cell(
            floor.map,
            origin,
            target,
            floor.barriers,
            target_must_be_walkable=False,
        ):
            return False

        if any(
            enemy.health > 0
            and (enemy.column, enemy.row) == target
            for enemy in floor.enemies
        ):
            return False

    current_time = pygame.time.get_ticks()
    event.shadow_step_trial_turn = True

    if not waiting:
        floor.player_column, floor.player_row = target
        game_state.player.movement_animation_started_at = current_time
        game_state.emit(
            GameEvent(
                type=GameEventType.MOVE,
                actor="hero",
                origin=origin,
                destination=target,
            )
        )

    position = (floor.player_column, floor.player_row)

    if trial["phase"] == "complete":
        return True

    if not inside_trial(trial, position):
        return True

    trial["action_stage"] = "delay"
    trial["action_ms"] = 0
    trial["rotation_progress"] = 0.0
    trial["last_tick"] = current_time
    return True


def _activate_seals(game_state, trial):
    from game.combat_log import add_log_message

    floor = game_state.floor
    position = (floor.player_column, floor.player_row)

    for seal in trial["seals"]:
        if (
            seal["position"] == position
            and seal["id"] not in trial["activated"]
        ):
            trial["activated"].add(seal["id"])
            add_log_message(
                game_state.combat_log,
                f"Shadow seal awakened: {len(trial['activated'])}/3.",
            )

    if position == trial["final"] and len(trial["activated"]) == 3:
        from acts.act_three.abilities.progression import unlock_ability_slot
        from acts.act_three.settings import ASSASSIN_TELEPORT_CHARGES

        unlock_ability_slot(game_state.player, "q")
        game_state.player.teleport_charge = ASSASSIN_TELEPORT_CHARGES
        trial["phase"] = "complete"
        add_log_message(
            game_state.combat_log,
            "Trial complete. SHADOW STEP unlocked.",
        )

    return True
