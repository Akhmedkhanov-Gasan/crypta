"""Mutable state and operations for the application window."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ApplicationWindowState:
    screen: Any
    windowed_size: tuple[int, int]
    fullscreen: bool

    def resize_windowed(self, width, height, minimum_size):
        import pygame

        minimum_width, minimum_height = minimum_size
        self.windowed_size = (
            max(minimum_width, width),
            max(minimum_height, height),
        )
        self.screen = pygame.display.set_mode(
            self.windowed_size,
            pygame.RESIZABLE,
        )

    def toggle_fullscreen(self):
        import pygame

        if self.fullscreen:
            self.screen = pygame.display.set_mode(
                self.windowed_size,
                pygame.RESIZABLE,
            )
        else:
            self.windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode(
                (0, 0),
                pygame.FULLSCREEN,
            )

        self.fullscreen = not self.fullscreen
