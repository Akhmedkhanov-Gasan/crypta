from functools import lru_cache

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE
_TILED_FLIP_HORIZONTAL = 0x80000000
_TILED_FLIP_VERTICAL = 0x40000000
_TILED_FLIP_MASK = (
    _TILED_FLIP_HORIZONTAL
    | _TILED_FLIP_VERTICAL
)
_TILE_VARIANTS = {}


def _tile_for_gid(tiles, gid):
    flip_flags = gid & _TILED_FLIP_MASK
    base_gid = gid & ~_TILED_FLIP_MASK
    tile = tiles.get(base_gid)

    if tile is None or not flip_flags:
        return tile

    key = (id(tile), flip_flags)
    variant = _TILE_VARIANTS.get(key)

    if variant is None:
        variant = pygame.transform.flip(
            tile,
            bool(flip_flags & _TILED_FLIP_HORIZONTAL),
            bool(flip_flags & _TILED_FLIP_VERTICAL),
        )
        _TILE_VARIANTS[key] = variant

    return variant


def _layer_number(layer_name):
    suffix = layer_name.rsplit("_", 1)[-1]
    return int(suffix) if suffix.isdigit() else 0


def layer_names_by_prefix(floor, *prefixes):
    ordered_names = []

    for prefix in prefixes:
        matching_names = [
            layer_name
            for layer_name in floor.tile_layers
            if (
                layer_name == prefix
                or layer_name.startswith(f"{prefix}_")
            )
        ]

        if prefix == "WallsBack":
            matching_names.sort(
                key=_layer_number,
                reverse=True,
            )

        ordered_names.extend(matching_names)

    return tuple(ordered_names)


def draw_tile_layers(
    surface,
    floor,
    assets,
    layer_names,
    first_column,
    first_row,
    last_column,
    last_row,
    camera_x,
    camera_y,
):
    tiles = assets.get("tmx_tiles", {})

    for layer_name in layer_names:
        layer = floor.tile_layers.get(layer_name, [])

        for row in range(first_row, min(last_row, len(layer))):
            row_data = layer[row]

            for column in range(
                first_column,
                min(last_column, len(row_data)),
            ):
                tile = _tile_for_gid(
                    tiles,
                    row_data[column],
                )
                if tile is None:
                    continue

                surface.blit(
                    tile,
                    (
                        column * ACT_THREE_TILE_SIZE - camera_x,
                        row * ACT_THREE_TILE_SIZE - camera_y,
                    ),
                )


_TILE_SHADOWS = {}


def _tile_shadow(tile, opacity):
    key = (id(tile), opacity)
    shadow = _TILE_SHADOWS.get(key)

    if shadow is None:
        shadow = tile.copy()
        shadow.fill(
            (0, 0, 0, opacity),
            special_flags=pygame.BLEND_RGBA_MULT,
        )
        _TILE_SHADOWS[key] = shadow

    return shadow


def draw_tile_layer_shadows(
    surface,
    floor,
    assets,
    layer_names,
    first_column,
    first_row,
    last_column,
    last_row,
    camera_x,
    camera_y,
):
    tiles = assets.get("tmx_tiles", {})

    shadow_passes = (
        (7, 11, 55),
        (3, 6, 110),
    )

    for offset_x, offset_y, opacity in shadow_passes:
        for layer_name in layer_names:
            layer = floor.tile_layers.get(layer_name, [])

            for row in range(
                first_row,
                min(last_row, len(layer)),
            ):
                row_data = layer[row]

                for column in range(
                    first_column,
                    min(last_column, len(row_data)),
                ):
                    tile = _tile_for_gid(
                        tiles,
                        row_data[column],
                    )

                    if tile is None:
                        continue

                    surface.blit(
                        _tile_shadow(tile, opacity),
                        (
                            column * ACT_THREE_TILE_SIZE
                            - camera_x
                            + offset_x,
                            row * ACT_THREE_TILE_SIZE
                            - camera_y
                            + offset_y,
                        ),
                    )


@lru_cache(maxsize=4)
def _foreground_fade_mask(tile_size):
    inner_radius = round(tile_size * 0.55)
    outer_radius = round(tile_size * 1.6)
    size = outer_radius * 2 + 2
    center = (outer_radius + 1, outer_radius + 1)
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    mask.fill((255, 255, 255, 255))

    radius_span = max(1, outer_radius - inner_radius)

    for radius in range(outer_radius, inner_radius, -1):
        progress = (outer_radius - radius) / radius_span
        progress = progress * progress * (3 - 2 * progress)
        alpha = round(255 - 183 * progress)

        pygame.draw.circle(
            mask,
            (255, 255, 255, alpha),
            center,
            radius,
        )

    pygame.draw.circle(
        mask,
        (255, 255, 255, 72),
        center,
        inner_radius,
    )

    return mask


def draw_fading_foreground_layers(
    surface,
    floor,
    assets,
    layer_names,
    first_column,
    first_row,
    last_column,
    last_row,
    camera_x,
    camera_y,
    player_position,
):
    foreground = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )

    draw_tile_layers(
        foreground,
        floor,
        assets,
        layer_names,
        first_column,
        first_row,
        last_column,
        last_row,
        camera_x,
        camera_y,
    )

    mask = _foreground_fade_mask(ACT_THREE_TILE_SIZE)
    player_center = (
        round(player_position[0] + ACT_THREE_TILE_SIZE / 2),
        round(player_position[1] + ACT_THREE_TILE_SIZE / 2),
    )

    foreground.blit(
        mask,
        (
            player_center[0] - mask.get_width() // 2,
            player_center[1] - mask.get_height() // 2,
        ),
        special_flags=pygame.BLEND_RGBA_MULT,
    )

    surface.blit(foreground, (0, 0))
