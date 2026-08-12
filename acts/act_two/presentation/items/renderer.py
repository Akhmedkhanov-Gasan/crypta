from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


def _position(column, row):
    return (
        MAP_OFFSET_X + column * TILE_SIZE,
        MAP_OFFSET_Y + row * TILE_SIZE,
    )


def draw_key(screen, column, row, sprites):
    screen.blit(sprites["key"], _position(column, row))


def draw_potion(screen, column, row, sprites):
    screen.blit(sprites["potion"], _position(column, row))


def draw_coin(screen, column, row, sprites):
    screen.blit(sprites["coin"], _position(column, row))


def draw_chest(screen, chest, sprites):
    prefix = (
        "stash"
        if chest.get("appearance", "standard") == "stash"
        else "chest"
    )
    state = "open" if chest["is_open"] else "closed"
    screen.blit(
        sprites[f"{prefix}_{state}"],
        _position(chest["column"], chest["row"]),
    )


def draw_stairs(screen, column, row, is_open, sprites):
    sprite_name = "stairs_open" if is_open else "stairs_locked"
    screen.blit(sprites[sprite_name], _position(column, row))


def draw_breakable_crate(screen, crate, sprites):
    suffix = "_broken" if crate["is_broken"] else ""
    sprite_name = f"breakable_crate_{crate['variant']}{suffix}"
    screen.blit(
        sprites[sprite_name],
        _position(crate["column"], crate["row"]),
    )
