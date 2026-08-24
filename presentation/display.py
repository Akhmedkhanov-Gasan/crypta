import math
import sys

import pygame

from settings import BACKGROUND_COLOR, GAME_HEIGHT, GAME_WIDTH


_AMBIENT_BACKGROUND_CACHE = {}


def enable_high_dpi():
    """Prevent Windows from bitmap-scaling the completed game window."""
    if sys.platform != "win32":
        return

    try:
        import ctypes

        ctypes.windll.user32.SetProcessDpiAwarenessContext(
            ctypes.c_void_p(-4)
        )
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def get_initial_window_size():
    """Prefer the native canvas so the first frame is never resampled."""
    display_info = pygame.display.Info()
    if (
        display_info.current_w >= GAME_WIDTH
        and display_info.current_h >= GAME_HEIGHT
    ):
        return GAME_WIDTH, GAME_HEIGHT

    scale = min(
        display_info.current_w / GAME_WIDTH,
        display_info.current_h / GAME_HEIGHT,
    )
    return (
        max(1, int(GAME_WIDTH * scale)),
        max(1, int(GAME_HEIGHT * scale)),
    )


def game_viewport(window_size):
    """Return a centered viewport using integer upscale factors when possible."""
    window_width, window_height = window_size
    available_scale = min(
        window_width / GAME_WIDTH,
        window_height / GAME_HEIGHT,
    )
    scale = (
        max(1, math.floor(available_scale))
        if available_scale >= 1
        else available_scale
    )
    width = max(1, round(GAME_WIDTH * scale))
    height = max(1, round(GAME_HEIGHT * scale))
    return (
        pygame.Rect(
            (window_width - width) // 2,
            (window_height - height) // 2,
            width,
            height,
        ),
        scale,
    )


def _ambient_background(size):
    cached = _AMBIENT_BACKGROUND_CACHE.get(size)
    if cached is not None:
        return cached

    width, height = size
    background = pygame.Surface(size)
    background.fill(BACKGROUND_COLOR)
    brick_width = 72
    brick_height = 48
    for row, y in enumerate(range(0, height, brick_height)):
        pygame.draw.line(background, (14, 18, 20), (0, y), (width, y))
        offset = -(brick_width // 2) if row % 2 else 0
        for x in range(offset, width, brick_width):
            pygame.draw.line(
                background,
                (11, 15, 17),
                (x, y),
                (x, min(height, y + brick_height)),
            )

    veil = pygame.Surface(size, pygame.SRCALPHA)
    veil.fill((0, 0, 0, 118))
    background.blit(veil, (0, 0))
    _AMBIENT_BACKGROUND_CACHE.clear()
    _AMBIENT_BACKGROUND_CACHE[size] = background
    return background


def present_game(window, game_surface):
    viewport, scale = game_viewport(window.get_size())
    window.blit(_ambient_background(window.get_size()), (0, 0))

    if viewport.size == game_surface.get_size():
        presented_surface = game_surface
    elif scale >= 1 and abs(scale - round(scale)) < 0.001:
        presented_surface = pygame.transform.scale(
            game_surface,
            viewport.size,
        )
    else:
        presented_surface = pygame.transform.smoothscale(
            game_surface,
            viewport.size,
        )

    window.blit(presented_surface, viewport)
    pygame.display.flip()


def window_to_game_position(window, window_position):
    viewport, scale = game_viewport(window.get_size())
    mouse_x, mouse_y = window_position
    if not viewport.collidepoint(mouse_x, mouse_y):
        return None

    return (
        min(GAME_WIDTH - 1, int((mouse_x - viewport.x) / scale)),
        min(GAME_HEIGHT - 1, int((mouse_y - viewport.y) / scale)),
    )


__all__ = [
    "enable_high_dpi",
    "game_viewport",
    "get_initial_window_size",
    "present_game",
    "window_to_game_position",
]
