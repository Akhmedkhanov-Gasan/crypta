SUMMONER_FRAME_COUNT = 8
SUMMONER_IDLE_FRAME_DURATION_MS = 270
SUMMONER_ATTACK_DURATION_MS = 480
SUMMONER_DEATH_FRAME_DURATION_MS = 120
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


def load_summoner_animation_assets(
    assets,
    act_directory,
    tile_size,
    image_loader,
):
    summoner_directory = (
        act_directory / "player" / "summoner"
    )
    idle_directory = summoner_directory / "idle"
    no_familiar_idle_directory = (
        summoner_directory
        / "no_familiar"
        / "idle"
    )
    walk_directory = summoner_directory / "walk"
    attack_directory = summoner_directory / "attack"
    hurt_directory = summoner_directory / "hurt"
    death_directory = summoner_directory / "death"

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
                f"player_summoner_hurt_{direction}_{frame_index}"
            ] = image_loader(
                hurt_directory
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

    for direction in SUMMONER_DIRECTIONS:
        for frame_index in range(SUMMONER_FRAME_COUNT):
            source_index = frame_index + 1
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
