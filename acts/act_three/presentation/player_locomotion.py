from dataclasses import dataclass
from acts.act_three.abilities.summoner_runes import familiar_is_away

from presentation.movement import sample_movement_travel
from acts.act_three.movement import (
    ACT_THREE_MOVEMENT_PROFILE,
    player_special_movement_active,
)
from acts.act_three.movement_timing import (
    PLAYER_POSE_HOLD_MS,
    PLAYER_WALK_PHASE_PER_STEP,
    PLAYER_WALK_START_PHASE,
    player_footfall_delay,
)
from acts.act_three.presentation.player_motion import (
    assassin_walk_direction,
)


@dataclass(frozen=True)
class LocomotionPose:
    position: tuple[int, int]
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
    step_ms: int = 0
    last_sample_at: int = -1


_STATE = None


def _walk_progress(progress):
    return progress + 0.3 * progress * (1.0 - progress)


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

    if player.health <= 0 or player_special_movement_active(player):
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

    step_ms = ACT_THREE_MOVEMENT_PROFILE.step_duration_for((dx, dy))
    travel_ms = player_footfall_delay(step_ms)

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
            <= state.step_ms + PLAYER_POSE_HOLD_MS
            and not combat_between_steps
        )

        if continuing:
            previous_progress = min(
                1.0,
                step_interval / player_footfall_delay(state.step_ms),
            )
            state.phase_origin = (
                state.phase_origin
                + PLAYER_WALK_PHASE_PER_STEP * previous_progress
            ) % 1.0
        else:
            state.phase_origin = PLAYER_WALK_START_PHASE
        state.token = token
        state.destination = destination
        state.started_at = started_at
        state.step_ms = step_ms

    travel = sample_movement_travel(
        (
            origin[0] * tile_size,
            origin[1] * tile_size,
        ),
        destination_pixels,
        elapsed,
        travel_ms,
        easing=_walk_progress,
    )

    phase = (
        state.phase_origin
        + PLAYER_WALK_PHASE_PER_STEP * travel.progress
    ) % 1.0

    combat_interrupted = (
        player.attack_animation_started_at >= started_at
        or player.hit_animation_started_at >= started_at
    )
    active = (
        elapsed < step_ms + PLAYER_POSE_HOLD_MS
        and not combat_interrupted
    )

    return LocomotionPose(
        position=travel.position,
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

    if subclass == "summoner":
        if familiar_is_away(player):
            return assets[
                (
                    "player_summoner_no_familiar_walk_"
                    f"{direction}_{pose.frame(8)}"
                )
            ]

        return assets[
            f"player_summoner_walk_{direction}_{pose.frame(8)}"
        ]

    return assets[
        f"player_{subclass}_walk_{pose.frame(2)}"
    ]
