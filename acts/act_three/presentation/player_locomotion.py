from dataclasses import dataclass
import math

from acts.act_three.movement_timing import (
    PLAYER_SETTLE_MS,
    PLAYER_STEP_MS,
    PLAYER_WALK_CYCLE_TILES,
)
from acts.act_three.presentation.player_motion import (
    assassin_walk_direction,
    interpolate_player_position,
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
    continuing: bool = False
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


def _smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


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
                "warlock_soul_exchange_player_origin",
            )
        )
    )


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
        state.continuing = (
            state.token is not None
            and state.destination == origin
            and 0 < started_at - state.started_at
            <= PLAYER_STEP_MS + PLAYER_SETTLE_MS
        )

        if state.continuing:
            state.phase_origin = (
                state.phase_origin + state.phase_distance
            ) % 1.0
        else:
            state.phase_origin = 0.0

        state.phase_distance = (
            math.hypot(dx, dy) / PLAYER_WALK_CYCLE_TILES
        )
        state.token = token
        state.destination = destination
        state.started_at = started_at

    progress = min(1.0, elapsed / PLAYER_STEP_MS)

    if state.continuing:
        travel_progress = progress
        position = (
            round((origin[0] + dx * progress) * tile_size),
            round((origin[1] + dy * progress) * tile_size),
        )
    else:
        travel_progress = (
            progress * 0.85 + _smoothstep(progress) * 0.15
        )
        position = interpolate_player_position(
            (
                origin[0] * tile_size,
                origin[1] * tile_size,
            ),
            destination_pixels,
            progress,
        )

    phase = (
        state.phase_origin
        + state.phase_distance * travel_progress
    ) % 1.0

    settle_progress = max(
        0.0,
        (elapsed - PLAYER_STEP_MS) / PLAYER_SETTLE_MS,
    )
    visibility = 1.0 - _smoothstep(settle_progress)
    onset = (
        1.0
        if state.continuing
        else _smoothstep(elapsed / 75.0)
    )
    strength = onset * visibility

    profile = _PROFILES.get(
        player.subclass,
        _PROFILES["berserker"],
    )
    direction_length = math.hypot(dx, dy)
    direction_x = dx / direction_length
    direction_y = dy / direction_length

    lift = math.sin(phase * math.tau) ** 2
    sway = math.sin(phase * math.tau)

    offset_x = (
        direction_x * profile.lean
        - direction_y * sway * profile.sway
    ) * strength
    offset_y = (
        direction_y * profile.lean
        + direction_x * sway * profile.sway
        - lift * profile.lift
    ) * strength

    combat_interrupted = (
        player.attack_animation_started_at >= started_at
        or player.hit_animation_started_at >= started_at
    )

    active = (
        elapsed < PLAYER_STEP_MS + PLAYER_SETTLE_MS
        and not combat_interrupted
    )

    return LocomotionPose(
        position=position,
        body_offset=(
            (round(offset_x), round(offset_y))
            if active
            else (0, 0)
        ),
        phase=phase,
        active=active,
    )


def locomotion_sprite(assets, player, pose):
    subclass = player.subclass
    direction = assassin_walk_direction(player.facing_direction)

    if subclass in ("assassin", "berserker"):
        return assets[
            f"player_{subclass}_walk_{direction}_{pose.frame(8)}"
        ]

    if subclass == "warlock":
        if player.warlock_demon_form_active:
            return assets[
                f"player_warlock_demon_walk_{pose.frame(2)}"
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
