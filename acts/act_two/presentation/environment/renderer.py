import pygame

from acts.act_two.presentation.environment.tiles import (
    _tile_noise,
    floor_decor_sprite_name,
    floor_sprite_name,
    wall_overlay_sprite_name,
    wall_sprite_name,
)
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


_GRID_COLOR = (20, 22, 28)
_MORTAR_DARK = (17, 20, 25)
_MORTAR_LIGHT = (56, 61, 66)
_DAMP_COLOR = (20, 49, 53)
_RUNE_COLOR = (61, 116, 123)
_PLAIN_FLOOR_TILES = {"r", "R", "G", "H", "P", "T"}
_DETAILED_FLOOR_SPRITES = {
    "floor_fissure",
    "floor_fissure_cross",
    "floor_puddle",
    "floor_rubble_heavy",
    "floor_drain",
    "floor_burial_seal",
}


def _open_neighbor(dungeon_map, column, row, dc, dr):
    neighbor_column = column + dc
    neighbor_row = row + dr
    return (
        0 <= neighbor_row < len(dungeon_map)
        and 0 <= neighbor_column < len(dungeon_map[neighbor_row])
        and dungeon_map[neighbor_row][neighbor_column] != "#"
    )


def _draw_crack(screen, x, y, variant, wall=False):
    crack_color = (25, 24, 30) if wall else (13, 14, 18)
    faint_edge = (62, 58, 66) if wall else (42, 41, 48)
    crack_paths = (
        ((6, 8), (13, 13), (11, 20), (18, 25)),
        ((25, 5), (19, 11), (22, 17), (14, 23), (16, 28)),
        ((7, 24), (13, 18), (20, 20), (26, 13)),
        ((5, 13), (12, 15), (17, 9), (25, 11), (28, 6)),
    )
    path = crack_paths[variant % len(crack_paths)]
    points = [(x + point_x, y + point_y) for point_x, point_y in path]
    pygame.draw.lines(screen, faint_edge, False, points, 2)
    pygame.draw.lines(screen, crack_color, False, points)
    branch_index = min(2, len(path) - 2)
    branch_x, branch_y = path[branch_index]
    branch_direction = -1 if variant % 2 else 1
    pygame.draw.line(
        screen,
        crack_color,
        (x + branch_x, y + branch_y),
        (x + branch_x + branch_direction * 5, y + branch_y + 5),
    )


def _draw_floor_detail(screen, x, y, noise, floor_number):
    if noise % 11 == 0:
        stain = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.ellipse(
            stain,
            (*_DAMP_COLOR, 34 + floor_number * 5),
            (4 + noise % 7, 16 + noise % 5, 19, 8),
        )
        pygame.draw.ellipse(
            stain,
            (47, 69, 66, 22),
            (8 + noise % 4, 18 + noise % 3, 11, 3),
        )
        screen.blit(stain, (x, y))

    if noise % max(7, 12 - floor_number) == 2:
        _draw_crack(screen, x, y, noise // 7)

    if noise % 41 == 9:
        pygame.draw.circle(
            screen,
            (42, 49, 48),
            (x + 7 + noise % 17, y + 7 + (noise // 17) % 17),
            1,
        )
        pygame.draw.circle(
            screen,
            (29, 42, 42),
            (x + 11 + noise % 13, y + 12 + (noise // 13) % 13),
            1,
        )


def _draw_wall_detail(
    screen,
    dungeon_map,
    column,
    row,
    x,
    y,
    noise,
    allow_decor=True,
):
    if _open_neighbor(dungeon_map, column, row, 0, 1):
        pygame.draw.line(
            screen,
            _MORTAR_DARK,
            (x + 1, y + TILE_SIZE - 2),
            (x + TILE_SIZE - 2, y + TILE_SIZE - 2),
            3,
        )
        pygame.draw.line(
            screen,
            _MORTAR_LIGHT,
            (x + 2, y + TILE_SIZE - 5),
            (x + TILE_SIZE - 3, y + TILE_SIZE - 5),
        )
    if _open_neighbor(dungeon_map, column, row, 1, 0):
        pygame.draw.line(
            screen,
            _MORTAR_DARK,
            (x + TILE_SIZE - 2, y + 2),
            (x + TILE_SIZE - 2, y + TILE_SIZE - 2),
            2,
        )
    if _open_neighbor(dungeon_map, column, row, -1, 0):
        pygame.draw.line(
            screen,
            _MORTAR_LIGHT,
            (x + 2, y + 3),
            (x + 2, y + TILE_SIZE - 3),
        )

    if not allow_decor:
        return
    if noise % 37 == 4:
        rune = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pulse_color = (*_RUNE_COLOR, 112)
        center_x = 10 + noise % 12
        pygame.draw.line(rune, pulse_color, (center_x, 8), (center_x, 23), 1)
        pygame.draw.lines(
            rune,
            pulse_color,
            False,
            ((center_x - 5, 12), (center_x, 17), (center_x + 5, 11)),
            1,
        )
        screen.blit(rune, (x, y))
    elif noise % 17 == 3:
        _draw_crack(screen, x, y, noise // 17, wall=True)


def _draw_wall(
    screen,
    sprites,
    dungeon_map,
    tile,
    column,
    row,
    rectangle,
    visual_seed,
    floor_number,
    detail_noise,
):
    texture_name = (
        (
            "wall_secret"
            if _tile_noise(
                column,
                row,
                visual_seed,
                floor_number + 1301,
            )
            & 1
            else "wall_secret_2"
        )
        if tile == "S"
        else wall_sprite_name(
            dungeon_map,
            column,
            row,
            visual_seed,
            floor_number,
        )
    )
    screen.blit(sprites[texture_name], rectangle)
    _draw_wall_detail(
        screen,
        dungeon_map,
        column,
        row,
        rectangle.x,
        rectangle.y,
        detail_noise,
        allow_decor=(tile == "#" and texture_name == "wall"),
    )
    overlay_name = (
        wall_overlay_sprite_name(
            dungeon_map,
            column,
            row,
            visual_seed,
            floor_number,
        )
        if tile == "#"
        else None
    )
    if overlay_name is None:
        return
    overlay = sprites[overlay_name]
    if overlay_name == "decor_wall_cobweb" and detail_noise & 1:
        overlay = pygame.transform.flip(overlay, True, False)
    screen.blit(overlay, rectangle)


def _draw_floor(
    screen,
    sprites,
    dungeon_map,
    tile,
    column,
    row,
    rectangle,
    visual_seed,
    floor_number,
    detail_noise,
    excluded_positions,
):
    texture_name = (
        "floor"
        if tile in _PLAIN_FLOOR_TILES
        else floor_sprite_name(column, row, visual_seed, floor_number)
    )
    screen.blit(sprites[texture_name], rectangle)
    if (
        tile not in _PLAIN_FLOOR_TILES
        and texture_name not in _DETAILED_FLOOR_SPRITES
    ):
        _draw_floor_detail(
            screen,
            rectangle.x,
            rectangle.y,
            detail_noise,
            floor_number,
        )
    if tile != ".":
        return
    decor_name = floor_decor_sprite_name(
        dungeon_map,
        column,
        row,
        visual_seed,
        floor_number,
        excluded_positions,
    )
    if decor_name is not None:
        screen.blit(sprites[decor_name], rectangle)


def draw_dungeon(
    screen,
    dungeon_map,
    sprites,
    floor_number=1,
    visual_seed=0,
    floor_decor_excluded_positions=(),
):
    visual_map = [row.replace("S", "#") for row in dungeon_map]
    for row_index, row in enumerate(dungeon_map):
        for column_index, tile in enumerate(row):
            rectangle = pygame.Rect(
                MAP_OFFSET_X + column_index * TILE_SIZE,
                MAP_OFFSET_Y + row_index * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
            )
            detail_noise = _tile_noise(
                column_index,
                row_index,
                visual_seed,
                floor_number + 101,
            )
            if tile in ("#", "S"):
                _draw_wall(
                    screen,
                    sprites,
                    visual_map,
                    tile,
                    column_index,
                    row_index,
                    rectangle,
                    visual_seed,
                    floor_number,
                    detail_noise,
                )
            else:
                _draw_floor(
                    screen,
                    sprites,
                    visual_map,
                    tile,
                    column_index,
                    row_index,
                    rectangle,
                    visual_seed,
                    floor_number,
                    detail_noise,
                    floor_decor_excluded_positions,
                )

            if tile == "C":
                screen.blit(sprites["pillar"], rectangle)
            pygame.draw.rect(screen, _GRID_COLOR, rectangle, 1)
