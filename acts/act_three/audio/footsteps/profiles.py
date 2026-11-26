from dataclasses import dataclass

import resource_store as resources


FOOTSTEPS_PATH = (
    resources.PROJECT_ROOT
    / "assets"
    / "audio"
    / "sounds_act_3"
    / "player"
    / "footsteps"
)


@dataclass(frozen=True)
class FootstepProfile:
    filenames: tuple[str, ...]
    volume: float = 0.32
    max_voices: int = 4


FOOTSTEP_PROFILES = {
    "light_leather": FootstepProfile(
        filenames=tuple(
            f"light_leather_{index:02d}.mp3"
            for index in range(1, 9)
        ),
    ),
    "cloth": FootstepProfile(
        filenames=tuple(
            f"cloth_{index:02d}.mp3"
            for index in range(1, 9)
        ),
    ),
    "heavy_armor": FootstepProfile(
        filenames=tuple(
            f"heavy_armor_{index:02d}.mp3"
            for index in range(1, 9)
        ),
    ),
}


PLAYER_FOOTSTEP_CATEGORIES = {
    "assassin": "light_leather",
    "archer": "light_leather",
    "warlock": "cloth",
    "summoner": "cloth",
    "paladin": "heavy_armor",
    "berserker": "heavy_armor",
}
