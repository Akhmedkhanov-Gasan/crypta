from acts.act_two.settings import (
    FLOOR_DECOR_CLUSTER_PERCENT,
    FLOOR_DECOR_CLUSTER_SIZE_TILES,
    FLOOR_DECOR_DENSE_PERCENT,
    FLOOR_DECOR_MIN_SPACING_TILES,
    FLOOR_DECOR_SPARSE_PERCENT,
    FLOOR_DECOR_VARIANT_WEIGHTS,
    FLOOR_TILE_VARIANT_WEIGHTS,
    WALL_DECOR_MIN_SPACING_TILES,
    WALL_OVERLAY_MIN_SPACING_TILES,
    WALL_OVERLAY_VARIANT_WEIGHTS,
    WALL_TILE_VARIANT_WEIGHTS,
    WALL_TORCH_MIN_SPACING_TILES,
    WALL_WEAR_REPEAT_MIN_SPACING_TILES,
)


_EXPOSED_WALL_SPRITES = {
    "wall_torch",
    "wall_chains",
    "wall_iron_shackle",
    "wall_skull_niche",
}
_WEAR_WALL_SPRITES = {
    "wall_broken",
    "wall_damp",
}
_SPACED_WALL_SPRITES = {
    "wall_chains",
    "wall_iron_shackle",
    "wall_skull_niche",
}
_WALL_OVERLAY_BASE_SPRITES = {
    "wall",
    "wall_broken",
    "wall_damp",
}


def _tile_noise(column, row, visual_seed, salt=0):
    return (
        column * 73856093
        ^ row * 19349663
        ^ visual_seed * 83492791
        ^ salt * 2654435761
    ) & 0x7FFFFFFF


def _wall_is_exposed(dungeon_map, column, row):
    for column_change, row_change in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        neighbor_column = column + column_change
        neighbor_row = row + row_change
        if (
            0 <= neighbor_row < len(dungeon_map)
            and 0 <= neighbor_column < len(dungeon_map[neighbor_row])
            and dungeon_map[neighbor_row][neighbor_column] != "#"
        ):
            return True
    return False


def floor_sprite_name(
    column,
    row,
    visual_seed,
    floor_number,
):
    total_weight = sum(
        weight for _, weight in FLOOR_TILE_VARIANT_WEIGHTS
    )
    if total_weight <= 0:
        return "floor"

    noise = _tile_noise(
        column,
        row,
        visual_seed,
        floor_number + 307,
    )
    selection = noise % total_weight
    for sprite_name, weight in FLOOR_TILE_VARIANT_WEIGHTS:
        if selection < weight:
            return sprite_name
        selection -= weight
    return "floor"


def _mix_noise(noise):
    noise ^= noise >> 16
    noise = (noise * 0x7FEB352D) & 0xFFFFFFFF
    noise ^= noise >> 15
    noise = (noise * 0x846CA68B) & 0xFFFFFFFF
    noise ^= noise >> 16
    return noise


def _floor_decor_candidate_sprite_name(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
    excluded_positions=(),
):
    if (
        dungeon_map[row][column] != "."
        or (column, row) in excluded_positions
    ):
        return None

    cluster_size = max(1, FLOOR_DECOR_CLUSTER_SIZE_TILES)
    cluster_noise = _mix_noise(
        _tile_noise(
            column // cluster_size,
            row // cluster_size,
            visual_seed,
            floor_number + 941,
        )
    )
    in_decor_cluster = (
        cluster_noise % 100 < FLOOR_DECOR_CLUSTER_PERCENT
    )
    placement_percent = (
        FLOOR_DECOR_DENSE_PERCENT
        if in_decor_cluster
        else FLOOR_DECOR_SPARSE_PERCENT
    )
    placement_noise = _mix_noise(
        _tile_noise(
            column,
            row,
            visual_seed,
            floor_number + 977,
        )
    )
    if placement_noise % 100 >= placement_percent:
        return None

    total_weight = sum(
        weight for _, weight in FLOOR_DECOR_VARIANT_WEIGHTS
    )
    if total_weight <= 0:
        return None
    selection = (placement_noise // 100) % total_weight
    for sprite_name, weight in FLOOR_DECOR_VARIANT_WEIGHTS:
        if selection < weight:
            return sprite_name
        selection -= weight
    return None


def _floor_decor_priority(
    column,
    row,
    visual_seed,
    floor_number,
):
    return _mix_noise(
        _tile_noise(
            column,
            row,
            visual_seed,
            floor_number + 1013,
        )
    )


def floor_decor_sprite_name(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
    excluded_positions=(),
):
    selected_sprite = _floor_decor_candidate_sprite_name(
        dungeon_map,
        column,
        row,
        visual_seed,
        floor_number,
        excluded_positions,
    )
    if selected_sprite is None:
        return None

    radius = max(0, FLOOR_DECOR_MIN_SPACING_TILES - 1)
    current_rank = (
        _floor_decor_priority(
            column,
            row,
            visual_seed,
            floor_number,
        ),
        row,
        column,
    )
    for neighbor_row in range(
        max(0, row - radius),
        min(len(dungeon_map), row + radius + 1),
    ):
        for neighbor_column in range(
            max(0, column - radius),
            min(len(dungeon_map[neighbor_row]), column + radius + 1),
        ):
            if neighbor_column == column and neighbor_row == row:
                continue
            if _floor_decor_candidate_sprite_name(
                dungeon_map,
                neighbor_column,
                neighbor_row,
                visual_seed,
                floor_number,
                excluded_positions,
            ) is None:
                continue
            neighbor_rank = (
                _floor_decor_priority(
                    neighbor_column,
                    neighbor_row,
                    visual_seed,
                    floor_number,
                ),
                neighbor_row,
                neighbor_column,
            )
            if neighbor_rank < current_rank:
                return None
    return selected_sprite


def _wall_candidate_sprite_name(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
):
    total_weight = sum(
        weight for _, weight in WALL_TILE_VARIANT_WEIGHTS
    )
    if total_weight <= 0:
        return "wall"

    noise = _tile_noise(
        column,
        row,
        visual_seed,
        floor_number + 509,
    )
    # Avalanche the coordinate hash before applying small percentage buckets.
    # Straight corridor coordinates otherwise over-favor a few modulo values.
    noise = _mix_noise(noise)
    selection = noise % total_weight
    selected_sprite = "wall"
    for sprite_name, weight in WALL_TILE_VARIANT_WEIGHTS:
        if selection < weight:
            selected_sprite = sprite_name
            break
        selection -= weight

    if (
        selected_sprite in _EXPOSED_WALL_SPRITES
        and not _wall_is_exposed(dungeon_map, column, row)
    ):
        return "wall"
    return selected_sprite


def _wall_variant_priority(
    column,
    row,
    visual_seed,
    floor_number,
):
    return _mix_noise(
        _tile_noise(
            column,
            row,
            visual_seed,
            floor_number + 829,
        )
    )


def _wall_variant_wins_spacing(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
    selected_sprite,
    radius,
    competing_sprites,
):
    current_rank = (
        _wall_variant_priority(
            column,
            row,
            visual_seed,
            floor_number,
        ),
        row,
        column,
    )
    for neighbor_row in range(
        max(0, row - radius),
        min(len(dungeon_map), row + radius + 1),
    ):
        for neighbor_column in range(
            max(0, column - radius),
            min(len(dungeon_map[neighbor_row]), column + radius + 1),
        ):
            if neighbor_column == column and neighbor_row == row:
                continue
            if dungeon_map[neighbor_row][neighbor_column] != "#":
                continue
            neighbor_sprite = _wall_candidate_sprite_name(
                dungeon_map,
                neighbor_column,
                neighbor_row,
                visual_seed,
                floor_number,
            )
            if neighbor_sprite not in competing_sprites:
                continue
            neighbor_rank = (
                _wall_variant_priority(
                    neighbor_column,
                    neighbor_row,
                    visual_seed,
                    floor_number,
                ),
                neighbor_row,
                neighbor_column,
            )
            if neighbor_rank < current_rank:
                return False
    return True


def wall_sprite_name(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
):
    selected_sprite = _wall_candidate_sprite_name(
        dungeon_map,
        column,
        row,
        visual_seed,
        floor_number,
    )
    if selected_sprite in _WEAR_WALL_SPRITES:
        if not _wall_variant_wins_spacing(
            dungeon_map,
            column,
            row,
            visual_seed,
            floor_number,
            selected_sprite,
            WALL_WEAR_REPEAT_MIN_SPACING_TILES - 1,
            {selected_sprite},
        ):
            return "wall"
    elif selected_sprite in _SPACED_WALL_SPRITES:
        if not _wall_variant_wins_spacing(
            dungeon_map,
            column,
            row,
            visual_seed,
            floor_number,
            selected_sprite,
            WALL_DECOR_MIN_SPACING_TILES - 1,
            _SPACED_WALL_SPRITES,
        ):
            return "wall"
    elif selected_sprite == "wall_torch":
        if not _wall_variant_wins_spacing(
            dungeon_map,
            column,
            row,
            visual_seed,
            floor_number,
            selected_sprite,
            WALL_TORCH_MIN_SPACING_TILES - 1,
            {"wall_torch"},
        ):
            return "wall"
    return selected_sprite


def _wall_overlay_candidate_sprite_name(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
):
    if (
        dungeon_map[row][column] != "#"
        or not _wall_is_exposed(dungeon_map, column, row)
    ):
        return None
    base_sprite = wall_sprite_name(
        dungeon_map,
        column,
        row,
        visual_seed,
        floor_number,
    )
    if base_sprite not in _WALL_OVERLAY_BASE_SPRITES:
        return None

    total_weight = sum(
        weight for _, weight in WALL_OVERLAY_VARIANT_WEIGHTS
    )
    if total_weight <= 0:
        return None
    noise = _mix_noise(
        _tile_noise(
            column,
            row,
            visual_seed,
            floor_number + 1097,
        )
    )
    selection = noise % total_weight
    for sprite_name, weight in WALL_OVERLAY_VARIANT_WEIGHTS:
        if selection < weight:
            return sprite_name
        selection -= weight
    return None


def _wall_overlay_priority(
    column,
    row,
    visual_seed,
    floor_number,
):
    return _mix_noise(
        _tile_noise(
            column,
            row,
            visual_seed,
            floor_number + 1129,
        )
    )


def _wall_overlay_wins_spacing(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
    radius,
    competing_sprites=None,
):
    current_rank = (
        _wall_overlay_priority(
            column,
            row,
            visual_seed,
            floor_number,
        ),
        row,
        column,
    )
    for neighbor_row in range(
        max(0, row - radius),
        min(len(dungeon_map), row + radius + 1),
    ):
        for neighbor_column in range(
            max(0, column - radius),
            min(len(dungeon_map[neighbor_row]), column + radius + 1),
        ):
            if neighbor_column == column and neighbor_row == row:
                continue
            if dungeon_map[neighbor_row][neighbor_column] != "#":
                continue
            neighbor_sprite = (
                _wall_overlay_candidate_sprite_name(
                    dungeon_map,
                    neighbor_column,
                    neighbor_row,
                    visual_seed,
                    floor_number,
                )
            )
            if neighbor_sprite is None:
                continue
            if (
                competing_sprites is not None
                and neighbor_sprite not in competing_sprites
            ):
                continue
            neighbor_rank = (
                _wall_overlay_priority(
                    neighbor_column,
                    neighbor_row,
                    visual_seed,
                    floor_number,
                ),
                neighbor_row,
                neighbor_column,
            )
            if neighbor_rank < current_rank:
                return False
    return True


def wall_overlay_sprite_name(
    dungeon_map,
    column,
    row,
    visual_seed,
    floor_number,
):
    selected_sprite = _wall_overlay_candidate_sprite_name(
        dungeon_map,
        column,
        row,
        visual_seed,
        floor_number,
    )
    if selected_sprite is None:
        return None

    if not _wall_overlay_wins_spacing(
        dungeon_map,
        column,
        row,
        visual_seed,
        floor_number,
        max(0, WALL_OVERLAY_MIN_SPACING_TILES - 1),
    ):
        return None
    return selected_sprite
