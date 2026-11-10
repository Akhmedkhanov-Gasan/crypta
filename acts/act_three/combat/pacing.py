PLAYER_BASIC_ATTACK_DURATION_MS = 320
PLAYER_ATTACK_RECOVERY_MS = 110
SUMMONER_BASIC_ATTACK_DURATION_MS = 480


def player_attack_recovery_until(player):
    started_at = player.attack_animation_started_at
    if started_at <= 0:
        return 0

    duration = (
        SUMMONER_BASIC_ATTACK_DURATION_MS
        if player.subclass == "summoner"
        else PLAYER_BASIC_ATTACK_DURATION_MS
    )
    return started_at + duration + PLAYER_ATTACK_RECOVERY_MS


def player_attack_recovery_active(player, current_time):
    return (
        player.attack_animation_started_at > 0
        and player.attack_animation_started_at <= current_time
        < player_attack_recovery_until(player)
    )
