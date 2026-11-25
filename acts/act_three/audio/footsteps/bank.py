import random

import pygame
import resource_store as resources

from acts.act_three.audio.footsteps.profiles import (
    FOOTSTEP_PROFILES,
    FOOTSTEPS_PATH,
    PLAYER_FOOTSTEP_CATEGORIES,
)
from game.events import GameEventType
from acts.act_three.movement import (
    ACT_THREE_MOVEMENT_PROFILE,
    player_special_movement_active,
)
from acts.act_three.movement_timing import PLAYER_STEP_MS, player_footfall_delay


class FootstepSoundBank:
    def __init__(self, sounds):
        self.sounds = sounds
        self.master_volume = 1.0
        self._bags = {}
        self._last_variants = {}
        self._pending_step = None
        self._player = None
        self._category = None
        self._voices = []

    @classmethod
    def load(cls):
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
        except pygame.error:
            return cls({})

        sounds = {}
        for category, profile in FOOTSTEP_PROFILES.items():
            variants = []
            for filename in profile.filenames:
                try:
                    variants.append(
                        resources.load_sound(
                            str(FOOTSTEPS_PATH / category / filename)
                        )
                    )
                except (FileNotFoundError, pygame.error):
                    continue
            if variants:
                sounds[category] = variants
        return cls(sounds)

    def set_master_volume(self, volume):
        self.master_volume = max(0.0, min(1.0, volume))

    def _variant_index(self, category):
        bag = self._bags.setdefault(category, [])
        if not bag:
            bag.extend(range(len(self.sounds[category])))
            random.shuffle(bag)
            if (
                len(bag) > 1
                and bag[-1] == self._last_variants.get(category)
            ):
                bag[0], bag[-1] = bag[-1], bag[0]
        return bag[-1]

    def play_events(self, events, player):
        now = pygame.time.get_ticks()
        self.update(player, now)
        category = PLAYER_FOOTSTEP_CATEGORIES.get(player.subclass)
        if self._player is not player or self._category != category:
            self._player = player
            self._category = category
            self._pending_step = None

        events = tuple(events)
        if player.health <= 0 or any(
            event.type is GameEventType.DEATH
            and event.actor == "hero"
            for event in events
        ):
            self._pending_step = None
            return

        moves = [
            event
            for event in events
            if event.type is GameEventType.MOVE
            and event.actor == "hero"
        ]
        move = next(
            (
                event
                for event in reversed(moves)
                if event.data.get("kind") in (None, "walk")
                and event.origin is not None
                and event.destination is not None
                and max(
                    abs(event.destination[0] - event.origin[0]),
                    abs(event.destination[1] - event.origin[1]),
                ) == 1
            ),
            None,
        )
        if move is None:
            if moves:
                self._pending_step = None
            return

        direction = (
            move.destination[0] - move.origin[0],
            move.destination[1] - move.origin[1],
        )
        step_ms = ACT_THREE_MOVEMENT_PROFILE.step_duration_for(direction)
        started_at = player.movement_animation_started_at
        self._pending_step = (
            started_at + player_footfall_delay(step_ms),
            started_at,
        )

    def update(self, player, current_time):
        if self._pending_step is None:
            return

        contact_at, started_at = self._pending_step
        if (
            player is not self._player
            or PLAYER_FOOTSTEP_CATEGORIES.get(player.subclass) != self._category
            or player.health <= 0
            or player_special_movement_active(player)
            or player.movement_origin is None
            or player.movement_animation_started_at < started_at
            or player.attack_animation_started_at >= started_at
            or player.hit_animation_started_at >= started_at
        ):
            self._pending_step = None
            return

        if current_time < contact_at:
            return

        self._pending_step = None
        if current_time - contact_at > PLAYER_STEP_MS:
            return

        self._play_step()

    def _play_step(self):
        category = self._category
        variants = self.sounds.get(category)
        if not variants or pygame.mixer.get_init() is None:
            return

        profile = FOOTSTEP_PROFILES[category]
        self._voices[:] = [
            (channel, sound)
            for channel, sound in self._voices
            if channel.get_busy() and channel.get_sound() is sound
        ]
        if len(self._voices) >= profile.max_voices:
            channel, _ = self._voices.pop(0)
            channel.stop()

        variant_index = self._variant_index(category)
        channel = variants[variant_index].play()
        if channel is None:
            return

        channel.set_volume(profile.volume * self.master_volume)
        self._voices.append((channel, variants[variant_index]))
        self._bags[category].pop()
        self._last_variants[category] = variant_index
