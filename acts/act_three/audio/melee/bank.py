import random

import pygame
import resource_store as resources

from acts.act_three.audio.melee.profiles import (
    ATTACK_PROFILES,
    CONTACT_DELAY_MS,
    PLAYER_AUDIO_PATH,
)
from acts.act_three.settings import (
    ASSASSIN_SHADOW_REFLEX_DAGGER_RELEASE_MS,
    ASSASSIN_SHADOW_REFLEX_DAGGER_TRAVEL_MS,
)
from game.events import GameEventType


class MeleeAttackSoundBank:
    def __init__(self, sounds):
        self.sounds = sounds
        self.master_volume = 1.0
        self._bags = {}
        self._last = {}
        self._pending = []
        self._player = None
        self._subclass = None

    @classmethod
    def load(cls):
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            if pygame.mixer.get_num_channels() < 16:
                pygame.mixer.set_num_channels(16)
        except pygame.error:
            return cls({})
        sounds = {}
        for subclass, layers in ATTACK_PROFILES.items():
            for key, (directory, volume) in layers.items():
                variants = []
                for path in resources.glob_resources(PLAYER_AUDIO_PATH / subclass / directory, "*.mp3"):
                    try:
                        variants.append(resources.load_sound(str(path)))
                    except (OSError, pygame.error):
                        continue
                if variants:
                    sounds[subclass, key] = variants
        return cls(sounds)

    def set_master_volume(self, volume):
        self.master_volume = max(0.0, min(1.0, volume))

    def _play(self, subclass, layer):
        key = subclass, layer
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
            channel.set_volume(ATTACK_PROFILES[subclass][layer][1] * self.master_volume)
            bag.pop()
            self._last[key] = index

    def update(self, player, current_time):
        if self._player is not player or self._subclass != player.subclass:
            self._pending.clear()
            self._player = player
            self._subclass = player.subclass
        if player.health <= 0:
            self._pending.clear()
            return
        pending, self._pending = self._pending, []
        for due_at, subclass, layer in pending:
            if current_time < due_at:
                self._pending.append((due_at, subclass, layer))
            elif current_time - due_at <= 250:
                self._play(subclass, layer)

    def play_events(self, events, player):
        now = pygame.time.get_ticks()
        self.update(player, now)
        subclass = player.subclass
        if subclass not in ATTACK_PROFILES or player.health <= 0:
            return
        events = tuple(events)
        for index, attack in enumerate(events):
            if (
                attack.type is not GameEventType.ATTACK
                or attack.actor != "hero"
                or attack.data.get("kind") not in (
                    "basic", "assassin_shadow_reflex", "environment_attack", "secret_wall",
                )
            ):
                continue
            end = next(
                (i for i in range(index + 1, len(events))
                 if events[i].type is GameEventType.ATTACK and events[i].actor == "hero"),
                len(events),
            )
            hits = [
                event for event in events[index + 1:end]
                if event.type is GameEventType.HIT
                and event.actor == "hero"
                and event.target not in (None, "hero", "familiar")
                and (event.destination in attack.positions or event.target == attack.target)
            ]
            contact = attack.data.get("kind") in ("environment_attack", "secret_wall") or any(
                event.data.get("blocked", False) or (event.amount or 0) > 0
                for event in hits
            )
            delay = CONTACT_DELAY_MS
            if attack.data.get("ranged", False):
                delay = ASSASSIN_SHADOW_REFLEX_DAGGER_RELEASE_MS + ASSASSIN_SHADOW_REFLEX_DAGGER_TRAVEL_MS
            if contact:
                self._pending.append((now + delay, subclass, "hit"))
            else:
                self._play(subclass, "miss")
