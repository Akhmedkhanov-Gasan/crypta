from acts.act_two.presentation.camera import change_act_two_camera_zoom
from acts.act_two.presentation.camera_controls import (
    create_act_two_camera_controls,
)
from acts.act_two.presentation.bosses.oracle_phase_transition import (
    oracle_cutscene_active,
)
from acts.act_three.presentation.camera import (
    act_three_camera_controls_offset,
)
from presentation.map_navigation import (
    get_map_navigation,
    record_map_position,
)


_BLOCKING_SCREENS = (
    "class_selection_open",
    "upgrade_screen_open",
    "rune_selection_open",
    "bloody_altar_open",
    "trade_screen_open",
    "subclass_selection_open",
    "act_three_transition_open",
    "act_three_debug_class_selection_open",
    "upgrade_altar_menu_open",
)


class MapNavigationController:
    def __init__(self, hud_layout):
        self.controls = create_act_two_camera_controls(hud_layout)

    def _visible(self, game_state):
        return (
            game_state.floor.presentation_act in (2, 3)
            and game_state.player.health > 0
            and not game_state.game_won
            and game_state.floor_transition_started_at < 0
            and not any(
                getattr(game_state, name, False)
                for name in _BLOCKING_SCREENS
            )
            and not oracle_cutscene_active(game_state.floor)
        )

    def _offset(self, game_state):
        if game_state.floor.presentation_act == 3:
            return act_three_camera_controls_offset(
                self.controls.rectangle
            )
        return (0, 0)

    def _sync_act_two_camera(self, game_state, camera):
        if (
            game_state.floor.presentation_act != 2
            or oracle_cutscene_active(game_state.floor)
        ):
            return

        floor = game_state.floor
        target_zoom = 1 if get_map_navigation(floor).overview else 2

        if camera.zoom != target_zoom:
            change_act_two_camera_zoom(
                camera,
                floor.map,
                floor.player_column,
                floor.player_row,
                1 if target_zoom > camera.zoom else -1,
            )

    def update(self, game_state, act_two_camera):
        floor = game_state.floor
        if floor.presentation_act not in (2, 3):
            return

        if game_state.player.health > 0:
            record_map_position(floor)

        if floor.presentation_act == 3 and game_state.player.health <= 0:
            get_map_navigation(floor).overview = False

        self._sync_act_two_camera(game_state, act_two_camera)

    def handle_event(
        self,
        event,
        game_state,
        act_two_camera,
        position,
        enabled,
    ):
        if not self._visible(game_state):
            return False

        direction = self.controls.event_direction(
            event,
            position,
            self._offset(game_state),
        )
        if direction is None:
            return False

        if enabled and direction:
            get_map_navigation(game_state.floor).overview = direction < 0
            self._sync_act_two_camera(game_state, act_two_camera)

        return True

    def draw(
        self,
        screen,
        game_state,
        mouse_position,
        enabled,
    ):
        if not self._visible(game_state):
            return

        self.controls.draw(
            screen,
            get_map_navigation(game_state.floor).overview,
            mouse_position,
            enabled,
            self._offset(game_state),
        )
