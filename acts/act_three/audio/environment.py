import random

import pygame
import resource_store as resources

from game.events import GameEventType


ENVIRONMENT_PATH = resources.PROJECT_ROOT / "assets/audio/sounds_act_3/environment"
ENVIRONMENT_SOUNDS = {
    "chest_open": ("chest/open", 0.32),
    "chest_locked": ("chest/locked", 0.26),
    "crate_break": ("crates/break", 0.36),
    "funerary_break": ("funerary_pair/break", 0.34),
    "mining": ("mining", 0.36),
}


class EnvironmentSoundBank:
    def __init__(self, sounds):
        self.sounds = sounds
        self.master_volume = 1.0
        self._bags = {}
        self._last = {}
        self._floor = None
        self._mining_played = set()

    @classmethod
    def load(cls):
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
        except pygame.error:
            return cls({})
        sounds = {}
        for key, (directory, volume) in ENVIRONMENT_SOUNDS.items():
            variants = []
            for path in resources.glob_resources(ENVIRONMENT_PATH / directory, "*.mp3"):
                try:
                    variants.append(resources.load_sound(str(path)))
                except (OSError, pygame.error):
                    continue
            if variants:
                sounds[key] = variants
        return cls(sounds)

    def set_master_volume(self, volume):
        self.master_volume = max(0.0, min(1.0, volume))

    def _play(self, key):
        variants = self.sounds.get(key)
        if not variants or pygame.mixer.get_init() is None:
            return
        bag = self._bags.setdefault(key, [])
        if not bag:
            bag.extend(range(len(variants)))
            random.shuffle(bag)
            if len(bag) > 1 and bag[-1] == self._last.get(key):
                bag[0], bag[-1] = bag[-1], bag[0]
        index = bag[-1]
        channel = variants[index].play()
        if channel is not None:
            channel.set_volume(ENVIRONMENT_SOUNDS[key][1] * self.master_volume)
            bag.pop()
            self._last[key] = index

    def play_events(self, events):
        played = set()
        for event in events:
            key = None
            if event.type is GameEventType.CHEST_OPEN:
                key = "chest_open"
            elif event.type is GameEventType.ENVIRONMENT:
                kind = event.data.get("kind")
                if kind == "chest_locked":
                    key = "chest_locked"
                elif kind == "chest_break":
                    key = event.data.get("sound_kind", "crate_break")
            if key in ENVIRONMENT_SOUNDS and key not in played:
                self._play(key)
                played.add(key)

    def update_mining(self, game_state, current_time):
        if self._floor is not game_state.floor:
            self._floor = game_state.floor
            self._mining_played.clear()
        effects = game_state.act_three.mining_effects
        active = set()
        for effect in effects:
            token = (effect["floor_index"], tuple(effect["position"]), effect["started_at"])
            active.add(token)
            if (
                token not in self._mining_played
                and effect["floor_index"] == game_state.floor_index
                and 0 <= current_time - effect["started_at"] <= 250
            ):
                self._play("mining")
            self._mining_played.add(token)
        self._mining_played.intersection_update(active)
