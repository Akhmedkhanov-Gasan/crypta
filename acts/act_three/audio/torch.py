import pygame
import resource_store as resources


TORCH_PATH = resources.PROJECT_ROOT / "assets/audio/sounds_act_3/environment/ambience/torch/torch_01.mp3"
TORCH_VOLUME = 0.12
TORCH_RANGE = 5


class TorchAmbience:
    def __init__(self):
        try:
            self.sound = resources.load_sound(str(TORCH_PATH))
        except (OSError, pygame.error):
            self.sound = None
        self._channel = None
        self._gain = 0.0

    def _owns_channel(self):
        return (
            self._channel is not None
            and self._channel.get_busy()
            and self._channel.get_sound() is self.sound
        )

    def update(self, game_state, elapsed_ms, volume):
        if self.sound is None:
            return
        floor = game_state.floor
        distance = min(
            (max(abs(x - floor.player_column), abs(y - floor.player_row))
             for x, y in floor.torches if (x, y) in floor.visible_cells),
            default=TORCH_RANGE,
        )
        target = max(0.0, 1.0 - distance / TORCH_RANGE) if game_state.player.health > 0 else 0.0
        change = elapsed_ms / 1000.0
        self._gain += max(-change, min(change, target - self._gain))
        if self._gain <= 0.001:
            self.stop()
            return
        if not self._owns_channel():
            self._channel = pygame.mixer.Channel(1)
            self._channel.play(self.sound, loops=-1, fade_ms=800)
        self._channel.set_volume(self._gain * TORCH_VOLUME * volume)

    def pause(self, paused):
        if self._owns_channel():
            if paused:
                self._channel.pause()
            else:
                self._channel.unpause()

    def stop(self):
        if self._owns_channel():
            self._channel.stop()
        self._channel = None
        self._gain = 0.0
