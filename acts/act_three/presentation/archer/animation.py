from acts.act_three.presentation.player_motion import (
    assassin_hurt_direction,
)


ARCHER_FRAME_COUNT = 8
ARCHER_DEATH_FRAME_DURATION_MS = 120


def archer_hurt_sprite(assets, player, frame_index=0):
    direction = assassin_hurt_direction(
        player.facing_direction
    )
    return assets[
        f"player_archer_hurt_{direction}_{frame_index}"
    ]


def load_archer_animation_assets(
    assets,
    act_directory,
    tile_size,
    image_loader,
):
    archer_directory = act_directory / "player" / "archer"

    for animation in ("idle", "walk", "attack", "hurt", "death"):
        for direction in ("down", "left", "right", "up"):
            for frame_index in range(ARCHER_FRAME_COUNT):
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
