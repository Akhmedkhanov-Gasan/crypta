import math

from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


_DROPPED_ITEM_FLIGHT_MS = 340


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


def draw_fire_bomb(screen, column, row, sprites):
    screen.blit(sprites["fire_bomb"], _position(column, row))


def draw_scroll(screen, column, row, kind, sprites):
    screen.blit(sprites[kind], _position(column, row))


def draw_dropped_consumables(
    screen,
    dropped_consumables,
    visible_cells,
    sprites,
    current_time,
):
    for dropped in dropped_consumables:
        if dropped.destination not in visible_cells:
            continue
        origin_x, origin_y = _position(*dropped.origin)
        target_x, target_y = _position(*dropped.destination)
        elapsed = current_time - dropped.thrown_at
        progress = max(
            0.0,
            min(1.0, elapsed / _DROPPED_ITEM_FLIGHT_MS),
        )
        eased = 1 - (1 - progress) ** 2
        draw_x = origin_x + (target_x - origin_x) * eased
        draw_y = (
            origin_y
            + (target_y - origin_y) * eased
            - math.sin(progress * math.pi) * 18
        )
        sprite_name = {
            "potion": "potion",
            "fire_bomb": "fire_bomb",
            "key": "key",
        }.get(dropped.kind, dropped.kind)
        screen.blit(
            sprites[sprite_name],
            (round(draw_x), round(draw_y)),
        )


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
