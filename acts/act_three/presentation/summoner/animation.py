SUMMONER_FRAME_COUNT = 8
SUMMONER_IDLE_FRAME_DURATION_MS = 270
SUMMONER_ATTACK_DURATION_MS = 480
SUMMONER_DEATH_FRAME_DURATION_MS = 120
SUMMONER_FAMILIAR_CAST_FRAME_DURATION_MS = 120
SUMMONER_FAMILIAR_CAST_FIRST_FRAME = 2
SUMMONER_FAMILIAR_CAST_LAST_FRAME = 4
SUMMONER_FAMILIAR_CAST_DURATION_MS = (
    (
        SUMMONER_FAMILIAR_CAST_LAST_FRAME
        - SUMMONER_FAMILIAR_CAST_FIRST_FRAME
        + 1
    )
    * SUMMONER_FAMILIAR_CAST_FRAME_DURATION_MS
)
SUMMONER_DIRECTIONS = (
    "down",
    "left",
    "right",
    "up",
)


def summoner_idle_frame(current_time):
    return (
        current_time // SUMMONER_IDLE_FRAME_DURATION_MS
    ) % SUMMONER_FRAME_COUNT


def _summoner_familiar_cast_direction(
    player,
    player_position,
    target_position,
):
    if target_position is None:
        dx, dy = player.facing_direction
    else:
        dx = target_position[0] - player_position[0]
        dy = target_position[1] - player_position[1]

    if abs(dx) >= abs(dy) and dx != 0:
        return "right" if dx > 0 else "left"

    if dy != 0:
        return "down" if dy > 0 else "up"

    return "right" if player.facing_direction[0] > 0 else "left"


def summoner_familiar_cast_sprite(
    assets,
    player,
    player_position,
    current_time,
):
    if player.summoner_familiar_summon_aiming:
        target_position = (
            player.summoner_familiar_summon_target
        )
        frame = SUMMONER_FAMILIAR_CAST_FIRST_FRAME
    else:
        cast_elapsed = (
            current_time
            - player.summoner_familiar_summoned_at
        )
        if (
            not player.summoner_familiar_active
            or player.summoner_familiar_summoned_at < 0
            or cast_elapsed < 0
            or cast_elapsed
            >= SUMMONER_FAMILIAR_CAST_DURATION_MS
        ):
            return None

        target_position = player.summoner_familiar_position
        frame = min(
            SUMMONER_FAMILIAR_CAST_LAST_FRAME,
            SUMMONER_FAMILIAR_CAST_FIRST_FRAME
            + cast_elapsed
            // SUMMONER_FAMILIAR_CAST_FRAME_DURATION_MS,
        )

    direction = _summoner_familiar_cast_direction(
        player,
        player_position,
        target_position,
    )
    return assets[
        f"player_summoner_attack_{direction}_{frame}"
    ]


def load_summoner_animation_assets(
    assets,
    act_directory,
    tile_size,
    image_loader,
):
    summoner_directory = (
        act_directory / "player" / "summoner"
    )
    no_familiar_directory = (
        summoner_directory / "no_familiar"
    )

    idle_directory = summoner_directory / "idle"
    walk_directory = summoner_directory / "walk"
    attack_directory = summoner_directory / "attack"
    hurt_directory = summoner_directory / "hurt"
    death_directory = summoner_directory / "death"

    no_familiar_idle_directory = (
        no_familiar_directory / "idle"
    )
    no_familiar_walk_directory = (
        no_familiar_directory / "walk"
    )
    no_familiar_attack_directory = (
        no_familiar_directory / "attack"
    )
    no_familiar_hurt_directory = (
        no_familiar_directory / "hurt"
    )

    for direction in SUMMONER_DIRECTIONS:
        for frame_index in range(SUMMONER_FRAME_COUNT):
            source_index = frame_index + 1

            assets[
                f"player_summoner_idle_{direction}_{frame_index}"
            ] = image_loader(
                idle_directory
                / f"idle_{direction}"
                / f"idle_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )

            assets[
                (
                    "player_summoner_no_familiar_idle_"
                    f"{direction}_{frame_index}"
                )
            ] = image_loader(
                no_familiar_idle_directory
                / f"idle_{direction}"
                / f"idle_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )

            assets[
                f"player_summoner_walk_{direction}_{frame_index}"
            ] = image_loader(
                walk_directory
                / f"walk_{direction}"
                / f"walk_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )

            assets[
                (
                    "player_summoner_no_familiar_walk_"
                    f"{direction}_{frame_index}"
                )
            ] = image_loader(
                no_familiar_walk_directory
                / f"walk_{direction}"
                / f"walk_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )

            assets[
                f"player_summoner_hurt_{direction}_{frame_index}"
            ] = image_loader(
                hurt_directory
                / f"hurt_{direction}"
                / f"hurt_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )

            assets[
                (
                    "player_summoner_no_familiar_hurt_"
                    f"{direction}_{frame_index}"
                )
            ] = image_loader(
                no_familiar_hurt_directory
                / f"hurt_{direction}"
                / f"hurt_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )

            assets[
                f"player_summoner_death_{direction}_{frame_index}"
            ] = image_loader(
                death_directory
                / f"death_{direction}"
                / f"death_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )

            assets[
                (
                    "player_summoner_attack_"
                    f"{direction}_{frame_index}"
                )
            ] = image_loader(
                attack_directory
                / f"attack_{direction}"
                / (
                    f"attack_{direction}_"
                    f"{source_index:02d}.png"
                ),
                (tile_size, tile_size),
            )

            assets[
                (
                    "player_summoner_no_familiar_attack_"
                    f"{direction}_{frame_index}"
                )
            ] = image_loader(
                no_familiar_attack_directory
                / f"attack_{direction}"
                / (
                    f"attack_{direction}_"
                    f"{source_index:02d}.png"
                ),
                (tile_size, tile_size),
            )
