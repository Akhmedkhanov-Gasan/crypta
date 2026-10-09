from dataclasses import dataclass
import math

from presentation.movement import (
    sample_movement_travel,
    smoothstep,
)
from acts.act_three.movement_timing import (
    PLAYER_POSE_HOLD_MS,
    PLAYER_SETTLE_MS,
    PLAYER_STEP_MS,
    PLAYER_TRAVEL_MS,
    PLAYER_WALK_CYCLE_TILES,
)
from acts.act_three.presentation.player_motion import (
    assassin_walk_direction,
)


@dataclass(frozen=True)
class MovementProfile:
    lift: float
    lean: float
    sway: float


@dataclass(frozen=True)
class LocomotionPose:
    position: tuple[int, int]
    body_offset: tuple[int, int]
    phase: float
    active: bool

    def frame(self, count):
        return int(self.phase * count) % count


@dataclass
class LocomotionState:
    player: object
    floor: object
    token: tuple | None = None
    destination: tuple[int, int] | None = None
    started_at: int = -1
    phase_origin: float = 0.0
    phase_distance: float = 0.0
    last_sample_at: int = -1


_PROFILES = {
    "assassin": MovementProfile(0.8, 1.5, 0.5),
    "berserker": MovementProfile(1.8, 1.0, 0.8),
    "warlock": MovementProfile(0.5, 0.5, 0.2),
    "paladin": MovementProfile(1.2, 0.7, 0.4),
    "archer": MovementProfile(1.0, 1.2, 0.5),
    "summoner": MovementProfile(0.7, 0.6, 0.3),
}

_STATE = None


def _special_movement_active(player):
    return (
        player.ultimate_animation_active
        or any(
            getattr(player, name, None) is not None
            for name in (
                "teleport_camera_origin",
                "archer_leap_origin",
                "berserker_crushing_leap_origin",
                "paladin_shield_charge_origin",
            )
        )
    )


def _sample_body_offset(profile, direction, progress, phase, elapsed):
    dx, dy = direction
    direction_length = math.hypot(dx, dy)
    direction_x = dx / direction_length
    direction_y = dy / direction_length

    stride = math.sin(math.pi * progress)
    sway = math.sin(math.tau * phase) * stride

    offset_x = (
        direction_x * profile.lean * stride
        - direction_y * profile.sway * sway
    )
    offset_y = (
        direction_y * profile.lean * stride
        + direction_x * profile.sway * sway
        - profile.lift * stride
    )

    if elapsed >= PLAYER_TRAVEL_MS:
        settle_progress = max(
            0.0,
            min(
                1.0,
                (elapsed - PLAYER_TRAVEL_MS) / PLAYER_SETTLE_MS,
            ),
        )
        landing = math.sin(math.pi * settle_progress)
        offset_x = -direction_x * profile.lean * 0.35 * landing
        offset_y = (
            profile.lift * 0.5
            - direction_y * profile.lean * 0.35
        ) * landing

    return round(offset_x), round(offset_y)


def sample_player_locomotion(
    player,
    floor,
    current_time,
    tile_size,
):
    global _STATE

    destination = (
        floor.player_column,
        floor.player_row,
    )
    destination_pixels = (
        destination[0] * tile_size,
        destination[1] * tile_size,
    )
    idle_pose = LocomotionPose(
        position=destination_pixels,
        body_offset=(0, 0),
        phase=0.0,
        active=False,
    )

    if (
        _STATE is None
        or _STATE.player is not player
        or _STATE.floor is not floor
        or current_time < _STATE.last_sample_at
    ):
        _STATE = LocomotionState(player, floor)

    state = _STATE
    state.last_sample_at = current_time

    if player.health <= 0 or _special_movement_active(player):
        state.token = None
        state.destination = None
        return idle_pose

    origin = player.movement_origin
    started_at = player.movement_animation_started_at

    if origin is None or started_at <= 0:
        state.token = None
        state.destination = None
        return idle_pose

    origin = tuple(origin)
    elapsed = current_time - started_at

    if elapsed < 0:
        return idle_pose

    dx = destination[0] - origin[0]
    dy = destination[1] - origin[1]

    if max(abs(dx), abs(dy)) != 1:
        state.token = None
        state.destination = None
        return idle_pose

    token = (
        started_at,
        origin,
        destination,
    )

    if token != state.token:
        step_interval = started_at - state.started_at
        combat_between_steps = (
            state.started_at
            <= player.attack_animation_started_at
            < started_at
            or state.started_at
            <= player.hit_animation_started_at
            < started_at
        )
        continuing = (
            state.token is not None
            and state.destination == origin
            and 0 < step_interval
            <= PLAYER_STEP_MS + PLAYER_POSE_HOLD_MS
            and not combat_between_steps
        )

        if continuing:
            previous_progress = smoothstep(
                step_interval / PLAYER_TRAVEL_MS
            )
            state.phase_origin = (
                state.phase_origin
                + state.phase_distance * previous_progress
            ) % 1.0
        else:
            state.phase_origin = 0.0

        state.phase_distance = (
            math.hypot(dx, dy) / PLAYER_WALK_CYCLE_TILES
        )
        state.token = token
        state.destination = destination
        state.started_at = started_at

    travel = sample_movement_travel(
        (
            origin[0] * tile_size,
            origin[1] * tile_size,
        ),
        destination_pixels,
        elapsed,
        PLAYER_TRAVEL_MS,
    )

    phase = (
        state.phase_origin
        + state.phase_distance * travel.eased_progress
    ) % 1.0

    combat_interrupted = (
        player.attack_animation_started_at >= started_at
        or player.hit_animation_started_at >= started_at
    )
    active = (
        elapsed < PLAYER_STEP_MS + PLAYER_POSE_HOLD_MS
        and not combat_interrupted
    )

    profile = _PROFILES.get(
        player.subclass,
        _PROFILES["berserker"],
    )
    body_offset = (
        _sample_body_offset(
            profile,
            (dx, dy),
            travel.progress,
            phase,
            elapsed,
        )
        if active
        else (0, 0)
    )

    return LocomotionPose(
        position=travel.position,
        body_offset=body_offset,
        phase=phase,
        active=active,
    )


def locomotion_sprite(assets, player, pose):
    subclass = player.subclass
    direction = assassin_walk_direction(player.facing_direction)

    if subclass in ("archer", "assassin", "berserker", "paladin"):
        return assets[
            f"player_{subclass}_walk_{direction}_{pose.frame(8)}"
        ]

    if subclass == "warlock":
        if player.warlock_demon_form_active:
            return assets[
                (
                    "player_warlock_demon_walk_"
                    f"{direction}_{pose.frame(8)}"
                )
            ]

        return assets[
            f"player_warlock_walk_{direction}_{pose.frame(8)}"
        ]

    if subclass == "summoner" and player.summoner_familiar_active:
        return assets[
            f"player_summoner_no_familiar_walk_{pose.frame(2)}"
        ]

    return assets[
        f"player_{subclass}_walk_{pose.frame(2)}"
    ]
