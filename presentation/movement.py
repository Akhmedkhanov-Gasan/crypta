from dataclasses import dataclass


@dataclass(frozen=True)
class MovementTravel:
    position: tuple[int, int]
    progress: float
    eased_progress: float


def smoothstep(progress):
    progress = max(0.0, min(1.0, progress))
    return progress * progress * (3.0 - 2.0 * progress)


def smootherstep(progress):
    progress = max(0.0, min(1.0, progress))
    return (
        progress
        * progress
        * progress
        * (progress * (progress * 6.0 - 15.0) + 10.0)
    )


def sample_movement_travel(
    origin,
    destination,
    elapsed,
    travel_ms,
    *,
    easing=smoothstep,
):
    if travel_ms <= 0:
        raise ValueError("travel_ms must be greater than zero")

    progress = max(0.0, min(1.0, elapsed / travel_ms))
    eased_progress = easing(progress)

    position = (
        round(
            origin[0]
            + (destination[0] - origin[0]) * eased_progress
        ),
        round(
            origin[1]
            + (destination[1] - origin[1]) * eased_progress
        ),
    )

    return MovementTravel(
        position=position,
        progress=progress,
        eased_progress=eased_progress,
    )
