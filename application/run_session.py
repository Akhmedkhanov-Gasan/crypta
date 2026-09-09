from dataclasses import is_dataclass
from enum import Enum
from importlib import import_module
import random

import pygame

from application.session_clock import restore_session_time
from game.combat_log import LogMessage
from game.persistence.run_store import (
    RunSaveStatus,
    delete_run_save,
    load_run_save,
    write_run_save,
)
from game.persistence.state_codec import (
    decode_state,
    encode_state,
)
from game.state import GameState


_STATE_MODULES = (
    "game.state",
    "game.control_state",
    "game.events",
    "acts.act_two.state",
    "acts.act_two.quests.state",
    "acts.act_three.state",
    "acts.act_one.presentation.death_scene",
    "acts.act_two.presentation.bosses.oracle_intro",
    "acts.act_two.presentation.bosses.oracle_combat",
    "acts.act_two.presentation.bosses.oracle_ground_fire",
    "acts.act_two.presentation.bosses.oracle_phase_transition",
    "acts.act_two.presentation.bosses.oracle_phase_two",
    "acts.act_two.presentation.bosses.oracle_death",
)


def _create_registry():
    registry = {
        f"{LogMessage.__module__}.{LogMessage.__name__}": LogMessage,
    }

    for module_name in _STATE_MODULES:
        module = import_module(module_name)

        for name, value in vars(module).items():
            if (
                isinstance(value, type)
                and value.__module__ == module_name
                and (
                    is_dataclass(value)
                    or issubclass(value, Enum)
                )
            ):
                registry[f"{module_name}.{name}"] = value

    return registry


def _persistent_id(value):
    if isinstance(value, pygame.Surface):
        return (
            "surface",
            value.get_size(),
            pygame.image.tostring(value, "RGBA"),
        )

    if isinstance(value, pygame.mixer.Channel):
        return ("audio_channel",)

    return None


def _persistent_load(identifier):
    if not isinstance(identifier, tuple) or not identifier:
        raise ValueError("Invalid saved resource.")

    if identifier == ("audio_channel",):
        return None

    if len(identifier) == 3 and identifier[0] == "surface":
        size, pixels = identifier[1:]

        if (
            not isinstance(size, tuple)
            or len(size) != 2
            or any(
                type(dimension) is not int
                or not 0 < dimension <= 8192
                for dimension in size
            )
            or not isinstance(pixels, bytes)
            or len(pixels) != size[0] * size[1] * 4
        ):
            raise ValueError("Invalid saved image.")

        return pygame.image.fromstring(pixels, size, "RGBA")

    raise ValueError("Unsupported saved resource.")


class RunSession:
    def __init__(self):
        self.registry = _create_registry()
        self.saved = None
        self.error = ""
        self._finished_state = None

    def load(self):
        result = load_run_save()

        if result.status is RunSaveStatus.MISSING:
            return

        if result.status is not RunSaveStatus.AVAILABLE:
            self.error = (
                "Saved run could not be loaded. "
                f"Status: {result.status.name}."
            )
            return

        try:
            saved = decode_state(
                result.snapshot,
                self.registry,
                _persistent_load,
            )

            if not isinstance(saved, dict):
                raise ValueError("Invalid saved session.")

            state = saved.get("game_state")
            ticks = saved.get("ticks")
            tracking = saved.get("progress_tracking_enabled")

            if (
                not isinstance(state, GameState)
                or state.player.health <= 0
                or state.game_won
                or type(ticks) is not int
                or ticks < 0
                or type(tracking) is not bool
                or state.visited_floors.get(state.floor_index)
                is not state.floor
            ):
                raise ValueError("Invalid or finished saved run.")

            random.Random().setstate(saved["random_state"])
            self.saved = saved
            self.error = ""
        except Exception as error:
            self.saved = None
            self.error = f"Saved run could not be loaded: {error}"

    def can_continue(self, game_state, runtime):
        if runtime.run_in_progress:
            return (
                game_state.player.health > 0
                and not game_state.game_won
            )
        return self.saved is not None

    def resume(self, runtime):
        if self.saved is None:
            raise ValueError("There is no saved run to continue.")

        saved = self.saved
        restore_session_time(saved["ticks"])
        random.setstate(saved["random_state"])
        runtime.progress_tracking_enabled = saved[
            "progress_tracking_enabled"
        ]
        self.saved = None
        self.error = ""
        return saved["game_state"]

    def discard(self):
        try:
            delete_run_save()
        except OSError as error:
            self.error = f"Saved run could not be removed: {error}"
            return False

        self.saved = None
        self.error = ""
        return True

    def save(self, game_state, runtime):
        if not runtime.run_in_progress:
            return True

        if game_state.player.health <= 0 or game_state.game_won:
            return self.discard()

        try:
            snapshot = encode_state(
                {
                    "game_state": game_state,
                    "ticks": pygame.time.get_ticks(),
                    "random_state": random.getstate(),
                    "progress_tracking_enabled": (
                        runtime.progress_tracking_enabled
                    ),
                },
                self.registry,
                _persistent_id,
            )
            decode_state(
                snapshot,
                self.registry,
                _persistent_load,
            )
            write_run_save(snapshot)
        except Exception as error:
            self.error = f"Run could not be saved: {error}"
            return False

        self.error = ""
        return True

    def invalidate_finished(self, game_state, runtime):
        if (
            not runtime.run_in_progress
            or self._finished_state is game_state
            or (
                game_state.player.health > 0
                and not game_state.game_won
            )
        ):
            return

        if self.discard():
            self._finished_state = game_state
