"""Creation of the application window and startup presentation."""

from dataclasses import dataclass
from typing import Any

from application.window import ApplicationWindowState


@dataclass(frozen=True)
class BootstrapContext:
    window: ApplicationWindowState
    game_surface: Any
    clock: Any
    startup: Any


def begin_application_startup(fullscreen=True):
    import pygame
    import resource_store as resources

    from presentation.display import (
        enable_high_dpi,
        get_initial_window_size,
    )
    from presentation.layout import ASSET_ROOT
    from presentation.startup import StartupScreen
    from settings import GAME_HEIGHT, GAME_WIDTH

    enable_high_dpi()
    pygame.init()

    icon_path = ASSET_ROOT / "ui" / "icon" / "crypta.png"
    pygame.display.set_icon(resources.load_image(str(icon_path)))

    windowed_size = get_initial_window_size()
    display_flags = pygame.FULLSCREEN if fullscreen else 0
    display_size = (0, 0) if fullscreen else windowed_size
    screen = pygame.display.set_mode(display_size, display_flags)
    game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    pygame.display.set_caption("Crypta")
    clock = pygame.time.Clock()
    startup = StartupScreen(screen, fullscreen=fullscreen)
    startup.show_logo()

    return BootstrapContext(
        window=ApplicationWindowState(
            screen=screen,
            windowed_size=windowed_size,
            fullscreen=fullscreen,
        ),
        game_surface=game_surface,
        clock=clock,
        startup=startup,
    )
