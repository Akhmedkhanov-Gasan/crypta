def _load_directional_animation(
    assets,
    enemy_directory,
    enemy_type,
    action,
    directions,
    frame_count,
    tile_size,
    image_loader,
):
    action_directory = enemy_directory / action

    for direction in directions:
        direction_directory = (
            action_directory
            / f"{action}_{direction}"
        )

        for frame_index in range(frame_count):
            source_index = frame_index + 1

            assets[
                (
                    f"enemy_{enemy_type}_{action}_"
                    f"{direction}_{frame_index}"
                )
            ] = image_loader(
                direction_directory
                / (
                    f"{action}_{direction}_"
                    f"{source_index:02d}.png"
                ),
                (tile_size, tile_size),
            )


def _load_archer_assets(
    assets,
    enemies_directory,
    tile_size,
    image_loader,
):
    enemy_type = "archer"
    enemy_directory = (
        enemies_directory / enemy_type
    )
    directions = (
        "down",
        "left",
        "right",
        "up",
    )

    for action in (
        "idle",
        "walk",
        "attack",
        "backhop",
        "death",
    ):
        _load_directional_animation(
            assets,
            enemy_directory,
            enemy_type,
            action,
            directions,
            8,
            tile_size,
            image_loader,
        )

    for frame_index in range(3):
        assets[
            f"enemy_archer_idle_{frame_index}"
        ] = assets[
            f"enemy_archer_idle_down_{frame_index}"
        ]

    for frame_index in range(2):
        assets[
            f"enemy_archer_walk_{frame_index}"
        ] = assets[
            f"enemy_archer_walk_down_{frame_index}"
        ]
        assets[
            f"enemy_archer_death_{frame_index}"
        ] = assets[
            (
                "enemy_archer_death_down_"
                f"{frame_index * 7}"
            )
        ]

    assets["enemy_archer_attack"] = assets[
        "enemy_archer_attack_down_0"
    ]


def _load_legacy_enemy_assets(
    assets,
    enemies_directory,
    enemy_type,
    tile_size,
    image_loader,
):
    enemy_directory = (
        enemies_directory / enemy_type
    )

    for frame_index in range(3):
        assets[
            f"enemy_{enemy_type}_idle_{frame_index}"
        ] = image_loader(
            enemy_directory
            / "idle"
            / f"idle_{frame_index:02d}.png",
            (tile_size, tile_size),
        )

    for frame_index in range(2):
        assets[
            f"enemy_{enemy_type}_walk_{frame_index}"
        ] = image_loader(
            enemy_directory
            / "walk"
            / f"walk_{frame_index:02d}.png",
            (tile_size, tile_size),
        )

        assets[
            f"enemy_{enemy_type}_death_{frame_index}"
        ] = image_loader(
            enemy_directory
            / "death"
            / f"death_{frame_index:02d}.png",
            (tile_size, tile_size),
        )


def load_enemy_animation_assets(
    assets,
    act_directory,
    tile_size,
    image_loader,
):
    enemies_directory = (
        act_directory / "enemies"
    )

    _load_archer_assets(
        assets,
        enemies_directory,
        tile_size,
        image_loader,
    )

    for enemy_type in (
        "brute",
        "priest",
        "sentinel",
    ):
        _load_legacy_enemy_assets(
            assets,
            enemies_directory,
            enemy_type,
            tile_size,
            image_loader,
        )

    for enemy_type in (
        "brute",
        "sentinel",
    ):
        assets[
            f"enemy_{enemy_type}_attack"
        ] = image_loader(
            enemies_directory
            / enemy_type
            / "attack"
            / "attack_00.png",
            (tile_size, tile_size),
        )

    assets["sentinel_guard"] = image_loader(
        enemies_directory
        / "sentinel"
        / "guard.png",
        (tile_size, tile_size),
    )

    assets["priest_heal_cast"] = image_loader(
        enemies_directory
        / "priest"
        / "heal_cast.png",
        (tile_size, tile_size),
    )
