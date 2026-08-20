import pygame

from presentation.camera import (
    PixelCamera,
    camera_render_rectangle,
    camera_world_view_size,
    change_pixel_camera_zoom,
    draw_pixel_camera_view,
    pixel_camera_screen_to_world,
    update_pixel_camera,
)
from presentation.layout import (
    ACT_TWO_VIEW_HEIGHT,
    ACT_TWO_VIEW_WIDTH,
    ACT_TWO_VIEW_X,
    ACT_TWO_VIEW_Y,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
)
from settings import BACKGROUND_COLOR, GAME_HEIGHT, GAME_WIDTH, TILE_SIZE


_DEAD_ZONE = (
    TILE_SIZE * 2,
    TILE_SIZE * 2,
    TILE_SIZE + TILE_SIZE // 2,
    TILE_SIZE * 3 // 4,
)
_VIEWPORT = pygame.Rect(
    ACT_TWO_VIEW_X,
    ACT_TWO_VIEW_Y,
    ACT_TWO_VIEW_WIDTH,
    ACT_TWO_VIEW_HEIGHT,
)


class ActTwoCamera(PixelCamera):
    pass


def _map_world_size(dungeon_map):
    return len(dungeon_map[0]) * TILE_SIZE, len(dungeon_map) * TILE_SIZE


def _player_focus(player_column, player_row):
    return (
        player_column * TILE_SIZE + TILE_SIZE / 2,
        player_row * TILE_SIZE + TILE_SIZE / 2,
    )


def act_two_world_surface_size(dungeon_map) -> tuple[int, int]:
    map_width, map_height = _map_world_size(dungeon_map)
    return (
        MAP_OFFSET_X + max(map_width, GAME_WIDTH),
        MAP_OFFSET_Y + max(map_height, GAME_HEIGHT),
    )


def update_act_two_camera(
    camera,
    dungeon_map,
    player_column,
    player_row,
    floor_index,
    current_time,
):
    update_pixel_camera(
        camera,
        _map_world_size(dungeon_map),
        _VIEWPORT,
        _player_focus(player_column, player_row),
        floor_index,
        current_time,
        _DEAD_ZONE,
        constrain_to_world=False,
    )


def change_act_two_camera_zoom(
    camera,
    dungeon_map,
    player_column,
    player_row,
    direction,
):
    return change_pixel_camera_zoom(
        camera,
        direction,
        _map_world_size(dungeon_map),
        _VIEWPORT,
        _player_focus(player_column, player_row),
        constrain_to_world=False,
    )


def _draw_camera_vignette(screen, render_rectangle):
    vignette = pygame.Surface(render_rectangle.size, pygame.SRCALPHA)
    for inset, alpha, width in (
        (0, 92, 28),
        (24, 51, 22),
        (47, 25, 18),
    ):
        if (
            render_rectangle.width <= inset * 2
            or render_rectangle.height <= inset * 2
        ):
            continue
        pygame.draw.rect(
            vignette,
            (1, 3, 7, alpha),
            (
                inset,
                inset,
                render_rectangle.width - inset * 2,
                render_rectangle.height - inset * 2,
            ),
            width=width,
        )
    screen.blit(vignette, render_rectangle)


def draw_act_two_camera_view(screen, world_surface, camera):
    render_rectangle = draw_pixel_camera_view(
        screen,
        world_surface,
        camera,
        _VIEWPORT,
        source_origin=(MAP_OFFSET_X, MAP_OFFSET_Y),
        background=BACKGROUND_COLOR,
    )
    _draw_camera_vignette(screen, render_rectangle)


def act_two_screen_to_cell(position, camera):
    world_position = pixel_camera_screen_to_world(
        position,
        camera,
        _VIEWPORT,
    )
    if world_position is None:
        return None
    return world_position[0] // TILE_SIZE, world_position[1] // TILE_SIZE


def act_two_camera_zoom_label(camera):
    render_rectangle = camera_render_rectangle(_VIEWPORT, camera.zoom)
    view_size = camera_world_view_size(_VIEWPORT, camera.zoom)
    return f"{camera.zoom}x ({view_size[0]}x{view_size[1]})", render_rectangle


__all__ = [
    "ActTwoCamera",
    "act_two_camera_zoom_label",
    "act_two_screen_to_cell",
    "act_two_world_surface_size",
    "change_act_two_camera_zoom",
    "draw_act_two_camera_view",
    "update_act_two_camera",
]
