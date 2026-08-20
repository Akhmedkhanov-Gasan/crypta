from dataclasses import dataclass
import math

import pygame


PIXEL_CAMERA_ZOOM_LEVELS = (1, 2, 3)


@dataclass
class PixelCamera:
    x: float = 0.0
    y: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    zoom: int = 2
    floor_index: int = -1
    updated_at: int = -1


def camera_render_rectangle(viewport, zoom):
    render_width = viewport.width // zoom * zoom
    render_height = viewport.height // zoom * zoom
    return pygame.Rect(
        viewport.x + (viewport.width - render_width) // 2,
        viewport.y + (viewport.height - render_height) // 2,
        render_width,
        render_height,
    )


def camera_world_view_size(viewport, zoom):
    render_rectangle = camera_render_rectangle(viewport, zoom)
    return (
        render_rectangle.width // zoom,
        render_rectangle.height // zoom,
    )


def _clamp(value, maximum):
    return max(0.0, min(float(maximum), float(value)))


def _camera_limits(world_size, viewport, zoom):
    view_width, view_height = camera_world_view_size(viewport, zoom)
    return (
        max(0, world_size[0] - view_width),
        max(0, world_size[1] - view_height),
    )


def center_pixel_camera(camera, world_size, viewport, focus):
    view_width, view_height = camera_world_view_size(
        viewport,
        camera.zoom,
    )
    maximum_x, maximum_y = _camera_limits(
        world_size,
        viewport,
        camera.zoom,
    )
    camera.x = _clamp(focus[0] - view_width / 2, maximum_x)
    camera.y = _clamp(focus[1] - view_height / 2, maximum_y)
    camera.target_x = camera.x
    camera.target_y = camera.y


def change_pixel_camera_zoom(
    camera,
    direction,
    world_size,
    viewport,
    focus,
    zoom_levels=PIXEL_CAMERA_ZOOM_LEVELS,
):
    current_index = zoom_levels.index(camera.zoom)
    next_index = max(
        0,
        min(len(zoom_levels) - 1, current_index + direction),
    )
    next_zoom = zoom_levels[next_index]
    if next_zoom == camera.zoom:
        return False
    camera.zoom = next_zoom
    center_pixel_camera(camera, world_size, viewport, focus)
    return True


def update_pixel_camera(
    camera,
    world_size,
    viewport,
    focus,
    floor_index,
    current_time,
    dead_zone,
    response_ms=145,
):
    view_width, view_height = camera_world_view_size(
        viewport,
        camera.zoom,
    )
    maximum_x, maximum_y = _camera_limits(
        world_size,
        viewport,
        camera.zoom,
    )
    if camera.floor_index != floor_index or camera.updated_at < 0:
        center_pixel_camera(camera, world_size, viewport, focus)
        camera.floor_index = floor_index
        camera.updated_at = current_time
        return

    center_x = camera.target_x + view_width / 2
    center_y = camera.target_y + view_height / 2
    if focus[0] < center_x - dead_zone[0]:
        camera.target_x = focus[0] + dead_zone[0] - view_width / 2
    elif focus[0] > center_x + dead_zone[0]:
        camera.target_x = focus[0] - dead_zone[0] - view_width / 2
    if focus[1] < center_y - dead_zone[1]:
        camera.target_y = focus[1] + dead_zone[1] - view_height / 2
    elif focus[1] > center_y + dead_zone[1]:
        camera.target_y = focus[1] - dead_zone[1] - view_height / 2

    camera.target_x = _clamp(camera.target_x, maximum_x)
    camera.target_y = _clamp(camera.target_y, maximum_y)
    elapsed = max(0, min(50, current_time - camera.updated_at))
    blend = 1 - math.exp(-elapsed / response_ms)
    camera.x += (camera.target_x - camera.x) * blend
    camera.y += (camera.target_y - camera.y) * blend
    if abs(camera.target_x - camera.x) < 0.05:
        camera.x = camera.target_x
    if abs(camera.target_y - camera.y) < 0.05:
        camera.y = camera.target_y
    camera.updated_at = current_time


def draw_pixel_camera_view(
    screen,
    world_surface,
    camera,
    viewport,
    source_origin=(0, 0),
    background=(0, 0, 0),
):
    render_rectangle = camera_render_rectangle(viewport, camera.zoom)
    view_width, view_height = camera_world_view_size(
        viewport,
        camera.zoom,
    )
    source_rectangle = pygame.Rect(
        source_origin[0] + round(camera.x),
        source_origin[1] + round(camera.y),
        view_width,
        view_height,
    )
    view = pygame.Surface((view_width, view_height))
    view.fill(background)
    visible_rectangle = source_rectangle.clip(world_surface.get_rect())
    if visible_rectangle.width > 0 and visible_rectangle.height > 0:
        destination = (
            visible_rectangle.x - source_rectangle.x,
            visible_rectangle.y - source_rectangle.y,
        )
        view.blit(
            world_surface.subsurface(visible_rectangle),
            destination,
        )
    screen.blit(
        pygame.transform.scale(view, render_rectangle.size),
        render_rectangle,
    )
    return render_rectangle


def pixel_camera_screen_to_world(position, camera, viewport):
    render_rectangle = camera_render_rectangle(viewport, camera.zoom)
    if not render_rectangle.collidepoint(position):
        return None
    return (
        (position[0] - render_rectangle.x) // camera.zoom
        + round(camera.x),
        (position[1] - render_rectangle.y) // camera.zoom
        + round(camera.y),
    )


__all__ = [
    "PIXEL_CAMERA_ZOOM_LEVELS",
    "PixelCamera",
    "camera_render_rectangle",
    "camera_world_view_size",
    "center_pixel_camera",
    "change_pixel_camera_zoom",
    "draw_pixel_camera_view",
    "pixel_camera_screen_to_world",
    "update_pixel_camera",
]
