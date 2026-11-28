import resource_store as resources

from acts.act_three.combat.pacing import PLAYER_BASIC_ATTACK_DURATION_MS


PLAYER_AUDIO_PATH = resources.PROJECT_ROOT / "assets/audio/sounds_act_3/player"
CONTACT_DELAY_MS = round(PLAYER_BASIC_ATTACK_DURATION_MS * 0.45)
ATTACK_PROFILES = {
    "assassin": {
        "hit": ("attack/hit", 0.42),
        "miss": ("attack/miss", 0.28),
    },
    "berserker": {
        "hit": ("attack/hit", 0.38),
        "miss": ("attack/miss", 0.26),
    },
}
