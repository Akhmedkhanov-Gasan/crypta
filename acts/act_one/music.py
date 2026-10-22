import pygame
import resource_store as resources

from acts.act_one.audio import (
    warden_has_been_defeated,
    warden_music_should_play,
)
from game.combat_log import add_log_message
from presentation.layout import MUSIC_ROOT


ACT_ONE_MENU_MUSIC_PATH = MUSIC_ROOT / "act_1_menu.mp3"
ACT_ONE_MUSIC_PATH = MUSIC_ROOT / "act_1_music.mp3"
ACT_ONE_WARDEN_MUSIC_PATH = MUSIC_ROOT / "act_1_warden.mp3"


def update_act_one_music(
    current_act,
    floor,
    volume,
    combat_log,
    music_attempted,
    warden_music_attempted,
    warden_music_channel,
    other_music_active,
):
    warden_fight_started = warden_music_should_play(floor)
    warden_defeated = warden_has_been_defeated(floor)

    if (
        current_act == 1
        and warden_fight_started
        and not warden_music_attempted
    ):
        warden_music_attempted = True
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            warden_music = resources.load_sound(
                str(ACT_ONE_WARDEN_MUSIC_PATH)
            )
            pygame.mixer.music.fadeout(700)
            warden_music_channel = pygame.mixer.Channel(0)
            warden_music_channel.play(
                warden_music,
                loops=-1,
                fade_ms=700,
            )
            warden_music_channel.set_volume(volume)
        except pygame.error as audio_error:
            add_log_message(
                combat_log,
                f"Warden music unavailable: {audio_error}",
                category="system",
            )

    if (
        current_act == 1
        and warden_defeated
        and warden_music_channel is not None
    ):
        warden_music_channel.fadeout(2200)
        warden_music_channel = None

    if (
        current_act == 1
        and not warden_fight_started
        and not music_attempted
    ):
        music_attempted = True
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            resources.load_music(str(ACT_ONE_MUSIC_PATH))
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1, fade_ms=1400)
        except pygame.error as audio_error:
            add_log_message(
                combat_log,
                f"Act I music unavailable: {audio_error}",
                category="system",
            )
    elif current_act != 1 and music_attempted and not other_music_active:
        if pygame.mixer.get_init() is not None:
            pygame.mixer.music.stop()
        music_attempted = False

    if current_act != 1 and warden_music_channel is not None:
        warden_music_channel.fadeout(500)
        warden_music_channel = None
        warden_music_attempted = False

    return (
        music_attempted,
        warden_music_attempted,
        warden_music_channel,
    )
