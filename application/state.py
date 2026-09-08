from dataclasses import dataclass


@dataclass
class ApplicationRuntimeState:
    running: bool = True
    quit_requested: bool = False
    menu_open: bool = True
    game_started: bool = False
    run_in_progress: bool = False
    progress_tracking_enabled: bool = True
    menu_started_at: int = 0

    def request_quit(self):
        self.quit_requested = True

    def open_menu(self, current_time):
        self.menu_open = True
        self.menu_started_at = current_time

    def start_game(self):
        self.menu_open = False
        self.game_started = True
        self.run_in_progress = True

    def return_to_main_menu(self, current_time):
        self.menu_open = True
        self.game_started = False
        self.menu_started_at = current_time
