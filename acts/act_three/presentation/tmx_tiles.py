from pathlib import Path

import pygame

import resource_store as resources


def _load_image(path):
    path = Path(path)
    if not resources.is_file(path):
        raise FileNotFoundError(f"Missing TMX image: {path}")
    return resources.load_image(str(path)).convert_alpha()


def _scale_tile(surface, tile_size):
    if surface.get_size() == (tile_size, tile_size):
        return surface
    return pygame.transform.scale(surface, (tile_size, tile_size))


def _load_atlas_tiles(
    tiles,
    tileset_root,
    tileset_directory,
    first_gid,
    tile_size,
):
    image = tileset_root.find("image")
    if image is None or not image.get("source"):
        return

    atlas = _load_image(tileset_directory / image.get("source"))
    source_width = int(tileset_root.get("tilewidth", tile_size))
    source_height = int(tileset_root.get("tileheight", tile_size))
    margin = int(tileset_root.get("margin", 0))
    spacing = int(tileset_root.get("spacing", 0))
    columns = int(tileset_root.get("columns", 0))
    tile_count = int(tileset_root.get("tilecount", 0))

    if columns <= 0:
        columns = max(
            1,
            (atlas.get_width() - margin * 2 + spacing)
            // (source_width + spacing),
        )

    if tile_count <= 0:
        rows = max(
            1,
            (atlas.get_height() - margin * 2 + spacing)
            // (source_height + spacing),
        )
        tile_count = columns * rows

    for local_id in range(tile_count):
        column = local_id % columns
        row = local_id // columns
        source_x = margin + column * (source_width + spacing)
        source_y = margin + row * (source_height + spacing)
        source_rectangle = pygame.Rect(
            source_x,
            source_y,
            source_width,
            source_height,
        )

        if not atlas.get_rect().contains(source_rectangle):
            continue

        tile = atlas.subsurface(source_rectangle).copy()
        tiles[first_gid + local_id] = _scale_tile(tile, tile_size)


def _load_collection_tiles(
    tiles,
    tileset_root,
    tileset_directory,
    first_gid,
    tile_size,
):
    for tile_node in tileset_root.findall("tile"):
        image = tile_node.find("image")
        if image is None or not image.get("source"):
            continue

        local_id = int(tile_node.get("id", 0))
        surface = _load_image(
            tileset_directory / image.get("source")
        )
        tiles[first_gid + local_id] = _scale_tile(
            surface,
            tile_size,
        )


def load_tmx_tiles(map_path, tile_size):
    map_path = Path(map_path)
    map_root = resources.load_xml(map_path).getroot()
    tiles = {}

    for tileset_reference in map_root.findall("tileset"):
        first_gid = int(tileset_reference.get("firstgid", 1))
        source = tileset_reference.get("source")

        if source:
            tileset_path = map_path.parent / source
            if not resources.is_file(tileset_path):
                raise FileNotFoundError(
                    f"Missing external tileset: {tileset_path}"
                )
            tileset_root = resources.load_xml(
                tileset_path
            ).getroot()
            tileset_directory = tileset_path.parent
        else:
            tileset_root = tileset_reference
            tileset_directory = map_path.parent

        _load_atlas_tiles(
            tiles,
            tileset_root,
            tileset_directory,
            first_gid,
            tile_size,
        )
        _load_collection_tiles(
            tiles,
            tileset_root,
            tileset_directory,
            first_gid,
            tile_size,
        )

    return tiles
