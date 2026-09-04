from game.events import GameEventType


DEFAULT_ENEMY_REACTION_DELAY_MS = 200
PLAYER_BASIC_ATTACK_DURATION_MS = 310
PLAYER_ATTACK_RECOVERY_MS = 110
ACT_TWO_HIT_FEEDBACK_MS = 350
ATTACK_CONFIRMATION_PAUSE_MS = 60
ENEMY_ATTACK_DURATION_MS = 240
ENEMY_ATTACK_RECOVERY_MS = 80
PLAYER_HIT_BREATH_MS = 100


def enemy_reaction_delay(
    game_state,
    combat_active: bool,
) -> int:
    player_performed_basic_attack = any(
        (
            event.type is GameEventType.ATTACK
            and event.actor == "hero"
            and event.data.get("kind") == "basic"
        )
        for event in game_state.events
    )

    if player_performed_basic_attack:
        return PLAYER_BASIC_ATTACK_DURATION_MS

    if combat_active:
        return DEFAULT_ENEMY_REACTION_DELAY_MS

    return 0
