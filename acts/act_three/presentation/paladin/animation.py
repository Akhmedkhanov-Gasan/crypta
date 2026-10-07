from acts.act_three.presentation.combat_effects import (
    _animated_player_death_frame,
)


PALADIN_FRAME_COUNT = 8
PALADIN_IDLE_FRAME_DURATION_MS = 270
PALADIN_DEATH_FRAME_DURATION_MS = 120


def paladin_death_frame(player, current_time):
    return _animated_player_death_frame(
        player,
        current_time,
        PALADIN_FRAME_COUNT,
        PALADIN_DEATH_FRAME_DURATION_MS,
    )


def paladin_idle_frame(current_time):
    return (
        current_time // PALADIN_IDLE_FRAME_DURATION_MS
    ) % PALADIN_FRAME_COUNT


def load_paladin_animation_assets(
    assets,
    act_directory,
    tile_size,
    image_loader,
):
    paladin_directory = (
        act_directory / "player" / "paladin"
    )

    for animation in (
        "idle",
        "walk",
        "attack",
        "hurt",
        "death",
        "block",
        "shield_charge",
    ):
        for direction in ("down", "left", "right", "up"):
            frame_prefix = f"{animation}_{direction}"
            frame_directory = (
                paladin_directory
                / animation
                / frame_prefix
            )

            for frame_index in range(PALADIN_FRAME_COUNT):
                source_index = frame_index + 1
                assets[
                    f"player_paladin_{frame_prefix}_{frame_index}"
                ] = image_loader(
                    frame_directory
                    / f"{frame_prefix}_{source_index:02d}.png",
                    (tile_size, tile_size),
                )
    assets["player_paladin_hurt"] = assets[
        "player_paladin_hurt_down_0"
    ]
