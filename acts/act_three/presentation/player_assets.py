def load_assassin_animation_assets(
    assets,
    act_directory,
    tile_size,
    image_loader,
):
    assassin_directory = (
        act_directory / "player" / "assassin"
    )
    idle_directory = assassin_directory / "idle"
    walk_directory = assassin_directory / "walk"
    idle_directions = (
        "left",
        "right",
        "up",
    )
    walk_directions = (
        "down",
        "left",
        "right",
        "up",
    )

    for frame_index in range(8):
        source_index = frame_index + 1

        assets[
            f"player_assassin_idle_{frame_index}"
        ] = image_loader(
            idle_directory / f"idle_{source_index:02d}.png",
            (tile_size, tile_size),
        )

        for direction in idle_directions:
            assets[
                f"player_assassin_idle_{direction}_{frame_index}"
            ] = image_loader(
                idle_directory
                / f"idle_{direction}"
                / f"idle_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )

        for direction in walk_directions:
            assets[
                f"player_assassin_walk_{direction}_{frame_index}"
            ] = image_loader(
                walk_directory
                / f"walk_{direction}"
                / f"walk_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )
