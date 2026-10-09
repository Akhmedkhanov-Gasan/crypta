def load_archer_animation_assets(
    assets,
    act_directory,
    tile_size,
    image_loader,
):
    archer_directory = act_directory / "player" / "archer"

    for animation in ("idle", "walk", "attack"):
        for direction in ("down", "left", "right", "up"):
            for frame_index in range(8):
                source_index = frame_index + 1
                assets[
                    f"player_archer_{animation}_{direction}_{frame_index}"
                ] = image_loader(
                    archer_directory
                    / animation
                    / f"{animation}_{direction}"
                    / f"{animation}_{direction}_{source_index:02d}.png",
                    (tile_size, tile_size),
                )
