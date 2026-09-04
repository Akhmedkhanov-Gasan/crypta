"""Mutable lifecycle state of the running application."""

from dataclasses import dataclass


@dataclass
class ApplicationRuntimeState:
    running: bool = True
    menu_open: bool = True
    game_started: bool = False
    progress_tracking_enabled: bool = True
    menu_started_at: int = 0

    def request_quit(self):
        self.running = False

    def open_menu(self, current_time):
        self.menu_open = True
        self.menu_started_at = current_time

    def start_game(self):
        self.menu_open = False
        self.game_started = True
