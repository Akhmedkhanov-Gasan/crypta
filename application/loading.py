"""Reusable loading-screen lifecycle for application transitions."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LoadingResult:
    screen: Any
    windowed_size: tuple[int, int]
    value: Any = None


class LoadingCoordinator:
    def __init__(self, window, clock, before_loading=None):
        self.window = window
        self.clock = clock
        self.before_loading = before_loading
        self.completed = False

    def run(self, loader=None, *args, **kwargs):
        if self.before_loading is not None:
            self.before_loading()

        result = run_loading_screen(
            self.window.screen,
            self.window.windowed_size,
            self.window.fullscreen,
            self.clock,
            loader,
            *args,
            **kwargs,
        )
        self.window.screen = result.screen
        self.window.windowed_size = result.windowed_size
        self.completed = True
        return result.value


def run_loading_screen(
    screen,
    windowed_size,
    fullscreen,
    clock,
    loader=None,
    *args,
    **kwargs,
):
    import pygame

    from presentation.startup import StartupScreen

    cursor_visible = pygame.mouse.get_visible()
    pygame.mouse.set_visible(False)

    try:
        loading = StartupScreen(screen, fullscreen=fullscreen)
        value = None

        if loader is not None:
            value = loading.load(loader, *args, **kwargs)

        loading.finish()
        screen = loading.window

        if not fullscreen:
            windowed_size = screen.get_size()

        clock.tick()
        return LoadingResult(
            screen=screen,
            windowed_size=windowed_size,
            value=value,
        )
    finally:
        if pygame.display.get_init():
            pygame.mouse.set_visible(cursor_visible)
