from acts.act_three.tile_catalog import (
    ENVIRONMENT_OBJECTS_TILESET_PATH,
    TILED_GID_MASK,
    tileset_catalog,
)


CRATE_TILE_IDS = (0, 18, 36)


def get_breakable_environment_object(floor, position):
    return next(
        (crate for crate in floor.breakable_crates
         if not crate.is_broken and (crate.column, crate.row) == position),
        None,
    )


def breakable_environment_gids():
    first_gid, tileset = tileset_catalog()[ENVIRONMENT_OBJECTS_TILESET_PATH]
    return {
        first_gid + int(tile.get("id"))
        for tile in tileset.findall("tile")
        if tile.find("./properties/property[@name='breakable'][@value='true']") is not None
    }


def extract_breakable_environment_objects(layers):
    breakable_gids = breakable_environment_gids()
    crates = {}

    for layer in layers.values():
        for row, tiles in enumerate(layer):
            for column, gid in enumerate(tiles):
                if (gid & TILED_GID_MASK) not in breakable_gids:
                    continue
                position = (column, row)
                crates[position] = {"position": position, "variant": gid}
                tiles[column] = 0

    return list(crates.values())
