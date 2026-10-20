SUMMONER_TRUE_FORM_FRAME_COUNT = 8
SUMMONER_TRUE_FORM_TRANSFORM_DURATION_MS = 880
SUMMONER_TRUE_FORM_ATTACK_DURATION_MS = 480
SUMMONER_TRUE_FORM_HURT_DURATION_MS = 320
SUMMONER_TRUE_FORM_MOVE_DURATION_MS = 180
SUMMONER_TRUE_FORM_IDLE_FRAME_DURATION_MS = 240

_TRUE_FORM_DIRECTIONS = (
    "down",
    "left",
    "right",
    "up",
)
_TRUE_FORM_ANIMATIONS = (
    "idle",
    "walk",
    "attack",
    "hurt",
    "death",
)


def load_summoner_true_form_assets(
    assets,
    act_directory,
    tile_size,
    image_loader,
):
    true_form_directory = (
        act_directory
        / "player"
        / "summoner"
        / "true_form"
    )

    for animation in _TRUE_FORM_ANIMATIONS:
        animation_directory = (
            true_form_directory / animation
        )

        for direction in _TRUE_FORM_DIRECTIONS:
            direction_directory = (
                animation_directory
                / f"{animation}_{direction}"
            )

            for frame_index in range(
                SUMMONER_TRUE_FORM_FRAME_COUNT
            ):
                source_index = frame_index + 1
                assets[
                    (
                        "summoner_true_form_"
                        f"{animation}_{direction}_{frame_index}"
                    )
                ] = image_loader(
                    direction_directory
                    / (
                        f"{animation}_{direction}_"
                        f"{source_index:02d}.png"
                    ),
                    (tile_size, tile_size),
                )

    transform_directory = (
        true_form_directory / "transform"
    )
    for frame_index in range(
        SUMMONER_TRUE_FORM_FRAME_COUNT
    ):
        source_index = frame_index + 1
        assets[
            f"summoner_true_form_transform_{frame_index}"
        ] = image_loader(
            transform_directory
            / f"transform_{source_index:02d}.png",
            (tile_size, tile_size),
        )


def _true_form_frame(elapsed, duration):
    progress = max(
        0.0,
        min(1.0, elapsed / duration),
    )
    return min(
        SUMMONER_TRUE_FORM_FRAME_COUNT - 1,
        int(progress * SUMMONER_TRUE_FORM_FRAME_COUNT),
    )


def summoner_true_form_direction(player):
    familiar_position = (
        player.summoner_familiar_position
        or player.summoner_familiar_hit_position
    )
    attack_target = player.summoner_familiar_attack_target
    movement_origin = (
        player.summoner_familiar_movement_origin
    )

    if (
        familiar_position is not None
        and attack_target is not None
    ):
        direction_column = (
            attack_target[0] - familiar_position[0]
        )
        direction_row = (
            attack_target[1] - familiar_position[1]
        )
    elif (
        familiar_position is not None
        and movement_origin is not None
    ):
        direction_column = (
            familiar_position[0] - movement_origin[0]
        )
        direction_row = (
            familiar_position[1] - movement_origin[1]
        )
    else:
        direction_column, direction_row = (
            player.facing_direction
        )

    if abs(direction_column) >= abs(direction_row):
        if direction_column < 0:
            return "left"
        if direction_column > 0:
            return "right"

    if direction_row < 0:
        return "up"

    return "down"


def summoner_true_form_transform_active(
    player,
    current_time,
):
    elapsed = (
        current_time
        - player.summoner_true_form_started_at
    )
    return (
        player.summoner_true_form_active
        and player.summoner_true_form_started_at >= 0
        and 0
        <= elapsed
        < SUMMONER_TRUE_FORM_TRANSFORM_DURATION_MS
    )


def summoner_true_form_reverse_transform_active(
    player,
    current_time,
):
    elapsed = (
        current_time
        - player.summoner_true_form_ending_started_at
    )
    return (
        player.summoner_true_form_ending_started_at >= 0
        and 0
        <= elapsed
        < SUMMONER_TRUE_FORM_TRANSFORM_DURATION_MS
    )


def summoner_true_form_visual_active(
    player,
    current_time,
):
    return (
        player.summoner_true_form_active
        or summoner_true_form_reverse_transform_active(
            player,
            current_time,
        )
    )


def summoner_true_form_transition_progress(
    player,
    current_time,
):
    if summoner_true_form_transform_active(
        player,
        current_time,
    ):
        elapsed = (
            current_time
            - player.summoner_true_form_started_at
        )
        return max(
            0.0,
            min(
                1.0,
                elapsed
                / SUMMONER_TRUE_FORM_TRANSFORM_DURATION_MS,
            ),
        )

    if summoner_true_form_reverse_transform_active(
        player,
        current_time,
    ):
        elapsed = (
            current_time
            - player.summoner_true_form_ending_started_at
        )
        return 1 - max(
            0.0,
            min(
                1.0,
                elapsed
                / SUMMONER_TRUE_FORM_TRANSFORM_DURATION_MS,
            ),
        )

    return None


def summoner_true_form_sprite(
    assets,
    player,
    current_time,
):
    transform_elapsed = (
        current_time
        - player.summoner_true_form_started_at
    )
    if summoner_true_form_transform_active(
        player,
        current_time,
    ):
        frame = _true_form_frame(
            transform_elapsed,
            SUMMONER_TRUE_FORM_TRANSFORM_DURATION_MS,
        )
        return assets[
            f"summoner_true_form_transform_{frame}"
        ]

    reverse_elapsed = (
        current_time
        - player.summoner_true_form_ending_started_at
    )
    if summoner_true_form_reverse_transform_active(
        player,
        current_time,
    ):
        frame = (
            SUMMONER_TRUE_FORM_FRAME_COUNT
            - 1
            - _true_form_frame(
                reverse_elapsed,
                SUMMONER_TRUE_FORM_TRANSFORM_DURATION_MS,
            )
        )
        return assets[
            f"summoner_true_form_transform_{frame}"
        ]

    if not player.summoner_true_form_active:
        return None

    direction = summoner_true_form_direction(player)
    hit_elapsed = (
        current_time
        - player.summoner_familiar_hit_animation_started_at
    )
    if (
        player.summoner_familiar_hit_animation_started_at >= 0
        and 0
        <= hit_elapsed
        < SUMMONER_TRUE_FORM_HURT_DURATION_MS
    ):
        frame = _true_form_frame(
            hit_elapsed,
            SUMMONER_TRUE_FORM_HURT_DURATION_MS,
        )
        return assets[
            (
                "summoner_true_form_hurt_"
                f"{direction}_{frame}"
            )
        ]

    attack_elapsed = (
        current_time
        - player.summoner_familiar_attack_started_at
    )
    if (
        0
        <= attack_elapsed
        < SUMMONER_TRUE_FORM_ATTACK_DURATION_MS
    ):
        frame = _true_form_frame(
            attack_elapsed,
            SUMMONER_TRUE_FORM_ATTACK_DURATION_MS,
        )
        return assets[
            (
                "summoner_true_form_attack_"
                f"{direction}_{frame}"
            )
        ]

    movement_elapsed = (
        current_time
        - player.summoner_familiar_movement_started_at
    )
    if (
        player.summoner_familiar_movement_origin is not None
        and 0
        <= movement_elapsed
        < SUMMONER_TRUE_FORM_MOVE_DURATION_MS
    ):
        frame = _true_form_frame(
            movement_elapsed,
            SUMMONER_TRUE_FORM_MOVE_DURATION_MS,
        )
        return assets[
            (
                "summoner_true_form_walk_"
                f"{direction}_{frame}"
            )
        ]

    frame = (
        current_time
        // SUMMONER_TRUE_FORM_IDLE_FRAME_DURATION_MS
    ) % SUMMONER_TRUE_FORM_FRAME_COUNT
    return assets[
        f"summoner_true_form_idle_{direction}_{frame}"
    ]
