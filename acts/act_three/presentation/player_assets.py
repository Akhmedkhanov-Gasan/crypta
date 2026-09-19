from acts.act_three.presentation.player_motion import (
    ASSASSIN_HURT_FRAME_COUNTS,
)


def load_berserker_animation_assets(
    assets,
    act_directory,
    tile_size,
    image_loader,
):
    berserker_directory = (
        act_directory
        / "player"
        / "berserker"
    )
    idle_directory = berserker_directory / "idle"
    walk_directory = berserker_directory / "walk"
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
            f"player_berserker_idle_{frame_index}"
        ] = image_loader(
            idle_directory / f"idle_{source_index:02d}.png",
            (tile_size, tile_size),
        )

        for direction in idle_directions:
            assets[
                f"player_berserker_idle_{direction}_{frame_index}"
            ] = image_loader(
                idle_directory
                / f"idle_{direction}"
                / f"idle_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )

        for direction in walk_directions:
            assets[
                f"player_berserker_walk_{direction}_{frame_index}"
            ] = image_loader(
                walk_directory
                / f"walk_{direction}"
                / f"walk_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )


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
    attack_directory = assassin_directory / "attack"
    hurt_directory = assassin_directory / "hurt"
    death_directory = assassin_directory / "death"
    shadow_step_directory = (
        assassin_directory / "shadow_step"
    )
    killing_spree_directory = (
        assassin_directory / "killing_spree"
    )
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
    attack_directions = (
        "down",
        "left",
        "right",
        "up",
    )
    shadow_step_directions = (
        "left",
        "right",
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

        for direction in attack_directions:
            assets[
                f"player_assassin_attack_{direction}_{frame_index}"
            ] = image_loader(
                attack_directory
                / f"attack_{direction}"
                / f"attack_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )
        for direction in shadow_step_directions:
            assets[
                f"player_assassin_shadow_step_{direction}_{frame_index}"
            ] = image_loader(
                shadow_step_directory
                / f"shadow_step_{direction}"
                / f"shadow_step_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )

        assets[
            f"player_assassin_death_{frame_index}"
        ] = image_loader(
            death_directory
            / f"death_{source_index:02d}.png",
            (tile_size, tile_size),
        )
    for variant_index in range(4):
        for phase_index in range(2):
            source_index = (
                variant_index * 2
                + phase_index
                + 1
            )
            assets[
                (
                    "player_assassin_killing_spree_"
                    f"{variant_index}_{phase_index}"
                )
            ] = image_loader(
                killing_spree_directory
                / f"killing_spree_{source_index:02d}.png",
                (tile_size, tile_size),
            )
    for direction, frame_count in (
        ASSASSIN_HURT_FRAME_COUNTS.items()
    ):
        for frame_index in range(frame_count):
            source_index = frame_index + 1
            assets[
                f"player_assassin_hurt_{direction}_{frame_index}"
            ] = image_loader(
                hurt_directory
                / f"hurt_{direction}"
                / f"hurt_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )

    assets["player_assassin_hurt"] = assets[
        "player_assassin_hurt_down_0"
    ]

    assets["player_assassin_attack"] = assets[
        "player_assassin_attack_right_0"
    ]
