import pygame

from acts.act_two.presentation.awakening_timing import (
    CLASS_SELECTION_READY_MS,
)
from acts.act_two.presentation.bosses.oracle_intro import (
    INTRO_END_MS,
    SKIP_FADE_MS as INTRO_SKIP_FADE_MS,
    oracle_intro_active,
)
from acts.act_two.presentation.bosses.oracle_credits import (
    BUTTON_FADE_MS,
    BUTTON_START_MS,
)
from acts.act_two.presentation.bosses.oracle_death import (
    CREDITS_START_MS,
    SKIP_FADE_MS as DEATH_SKIP_FADE_MS,
    oracle_death_active,
)
from acts.act_two.presentation.bosses.oracle_phase_transition import (
    SKIP_FADE_MS as PHASE_SKIP_FADE_MS,
    TRANSITION_END_MS,
    oracle_phase_transition_active,
)


HOLD_DURATION_MS = 1500
HINT_DURATION_MS = 3000

DEATH_SKIP_END_MS = (
    CREDITS_START_MS
    + BUTTON_START_MS
    + BUTTON_FADE_MS
)


class ActTwoCutsceneSkip:
    def __init__(self):
        self.target = None
        self.holding = False
        self.consume_space = False
        self.held_ms = 0
        self.updated_at = None
        self.visible_until = 0

    @property
    def progress(self):
        return min(1.0, self.held_ms / HOLD_DURATION_MS)

    def is_visible(self, current_time):
        return self.target is not None and (
            self.holding or current_time < self.visible_until
        )

    def _select(self, game_state, current_time, enabled):
        if not enabled:
            return None, None, 0, 0

        if (
            game_state.class_selection_open
            and game_state.class_selection_choice is None
            and current_time - game_state.class_transition_started_at
            < CLASS_SELECTION_READY_MS
        ):
            return (
                (
                    "awakening",
                    id(game_state),
                    game_state.class_transition_started_at,
                ),
                None,
                0,
                0,
            )

        floor = game_state.floor

        if oracle_intro_active(floor):
            scene = floor.oracle_intro
            if scene.skip_frame is None:
                return (
                    ("intro", id(scene)),
                    scene,
                    INTRO_END_MS,
                    INTRO_SKIP_FADE_MS,
                )

        if oracle_phase_transition_active(floor):
            scene = floor.oracle_phase_transition
            if scene.skip_frame is None:
                return (
                    ("phase", id(scene)),
                    scene,
                    TRANSITION_END_MS,
                    PHASE_SKIP_FADE_MS,
                )

        if oracle_death_active(floor):
            scene = floor.oracle_death
            if (
                scene.skip_frame is None
                and scene.elapsed < DEATH_SKIP_END_MS
            ):
                return (
                    ("death", id(scene)),
                    scene,
                    DEATH_SKIP_END_MS,
                    DEATH_SKIP_FADE_MS,
                )

        return None, None, 0, 0

    def _sync(self, game_state, current_time, enabled):
        target, scene, end_ms, fade_ms = self._select(
            game_state,
            current_time,
            enabled,
        )

        if target != self.target:
            self.target = target
            self.holding = False
            self.held_ms = 0
            self.updated_at = current_time
            self.visible_until = 0

        return scene, end_ms, fade_ms

    def handle_event(self, game_state, event, enabled):
        current_time = pygame.time.get_ticks()
        self._sync(game_state, current_time, enabled)

        if event.type == pygame.WINDOWFOCUSLOST:
            self.holding = False
            self.consume_space = False
            self.held_ms = 0
            self.updated_at = current_time
            return False

        if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            consumed = self.consume_space
            self.consume_space = False
            self.holding = False
            self.held_ms = 0
            if self.target is not None:
                self.visible_until = current_time + HINT_DURATION_MS
            return consumed or self.target is not None

        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_SPACE
            and self.consume_space
        ):
            return True

        if self.target is None:
            return False

        if event.type in (
            pygame.KEYDOWN,
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEWHEEL,
        ):
            self.visible_until = current_time + HINT_DURATION_MS

            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_SPACE
                and not getattr(event, "repeat", False)
                and pygame.key.get_focused()
            ):
                self.consume_space = True
                self.holding = True
                self.held_ms = 0
                self.updated_at = current_time

            return True

        return event.type in (
            pygame.KEYUP,
            pygame.MOUSEBUTTONUP,
        )

    def update(self, game_state, current_time, frame, enabled):
        scene, end_ms, fade_ms = self._sync(
            game_state,
            current_time,
            enabled,
        )
        delta = (
            0
            if self.updated_at is None
            else max(0, min(50, current_time - self.updated_at))
        )
        self.updated_at = current_time

        if self.target is None or not self.holding:
            return

        if (
            not pygame.key.get_focused()
            or not pygame.key.get_pressed()[pygame.K_SPACE]
            or (scene is not None and scene.paused)
        ):
            self.holding = False
            self.held_ms = 0
            return

        self.visible_until = current_time + HINT_DURATION_MS
        self.held_ms = min(
            HOLD_DURATION_MS,
            self.held_ms + delta,
        )

        if self.held_ms < HOLD_DURATION_MS:
            return

        if self.target[0] == "awakening":
            game_state.class_transition_started_at = (
                current_time - CLASS_SELECTION_READY_MS - 500
            )
        else:
            scene.skip_frame = frame.copy()
            scene.elapsed = max(scene.elapsed, end_ms - fade_ms)
            scene.skip_started_elapsed = scene.elapsed

        self.target = None
        self.holding = False
        self.held_ms = 0
        self.visible_until = 0
