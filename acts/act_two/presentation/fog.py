import pygame

from acts.act_two.settings import (
    FOG_EDGE_ALPHA,
    FOG_EDGE_WIDTH_PIXELS,
    FOG_EXPLORED_ALPHA,
    FOG_UNEXPLORED_ALPHA,
    VISION_RADIUS_TILES,
)
from presentation.layout import (
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
)
from settings import TILE_SIZE


_FOG_COLOR = (2, 5, 9)


def _draw_visibility_gradient(fog, center):
    outer_radius = round(VISION_RADIUS_TILES * TILE_SIZE)
    ring_count = 12

    for ring_index in range(ring_count):
        progress = ring_index / (ring_count - 1)
        radius = outer_radius - round(
            progress * FOG_EDGE_WIDTH_PIXELS
        )
        alpha = round(FOG_EDGE_ALPHA * (1 - progress) ** 1.35)
        pygame.draw.circle(
            fog,
            (*_FOG_COLOR, alpha),
            center,
            radius,
        )

    pygame.draw.circle(
        fog,
        (*_FOG_COLOR, 0),
        center,
        outer_radius - FOG_EDGE_WIDTH_PIXELS,
    )


def draw_act_two_fog_of_war(screen, act_number, floor):
    if act_number != 2:
        return

    map_width = len(floor.map[0]) * TILE_SIZE
    map_height = len(floor.map) * TILE_SIZE
    fog = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
    fog.fill((*_FOG_COLOR, FOG_UNEXPLORED_ALPHA))

    for column, row in floor.explored_cells:
        pygame.draw.rect(
            fog,
            (*_FOG_COLOR, FOG_EXPLORED_ALPHA),
            (
                column * TILE_SIZE,
                row * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
            ),
        )

    player_center = (
        floor.player_column * TILE_SIZE + TILE_SIZE // 2,
        floor.player_row * TILE_SIZE + TILE_SIZE // 2,
    )
    _draw_visibility_gradient(fog, player_center)

    # The radial light supplies the soft edge. Re-cover cells that are inside
    # that circle but hidden behind a wall or a closed door.
    for row in range(len(floor.map)):
        for column in range(len(floor.map[0])):
            position = (column, row)
            if position in floor.visible_cells:
                continue
            pygame.draw.rect(
                fog,
                (
                    *_FOG_COLOR,
                    (
                        FOG_EXPLORED_ALPHA
                        if position in floor.explored_cells
                        else FOG_UNEXPLORED_ALPHA
                    ),
                ),
                (
                    column * TILE_SIZE,
                    row * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                ),
            )

    screen.blit(fog, (MAP_OFFSET_X, MAP_OFFSET_Y))
