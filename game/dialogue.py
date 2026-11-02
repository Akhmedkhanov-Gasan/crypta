from dataclasses import dataclass

import pygame


@dataclass
class DialogueState:
    track: str = ""
    completed_until: int = -1
    start: int = -1
    end: int = -1
    ready_at: int = -1
    elapsed: int = 0
    typing_end: int = -1
    revealed: bool = False

    @property
    def active(self):
        return self.start >= 0


def dialogue_visible_characters(state, count):
    return None if state is not None and state.active and state.revealed else count


def hold_dialogue(game_state, track, elapsed, timeline):
    state = game_state.dialogue
    if state.track != track or elapsed < state.completed_until:
        state.track = track
        state.completed_until = -1
        state.ready_at = -1
    previous_start = state.start
    state.start = -1
    state.end = -1
    for cue in timeline:
        start, end = cue[:2]
        if end <= state.completed_until:
            continue
        if elapsed < start:
            break
        if previous_start != start or state.ready_at < 0:
            text = cue[-1] if len(cue) > 2 and isinstance(cue[-1], str) else ""
            interval = (
                78 if track == "act_one_intro"
                else 32 if track == "act_two_choice"
                else 34 if track == "act_two_awakening" or track.startswith("act_three_awakening:")
                else 0
            )
            state.typing_end = start + len(text) * interval
            state.revealed = False
            duration = max(5500, len(text) * interval + len(text.split()) * 330 + 1800)
            state.ready_at = pygame.time.get_ticks() + duration
        if pygame.time.get_ticks() >= state.ready_at:
            state.completed_until = end
            state.ready_at = -1
            return max(elapsed, end)
        state.start = start
        state.end = end
        state.elapsed = min(elapsed, end - 1)
        return state.elapsed
    return elapsed

