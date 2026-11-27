from math import ceil, exp

from acts.act_three.balance import (
    CRIT_ASYMPTOTE,
    CRIT_DIMINISHING_THRESHOLD,
    DODGE_ASYMPTOTE,
    DODGE_DIMINISHING_THRESHOLD,
)


def advance_chance(current, change, *, dodge=False):
    if change <= 0:
        return max(0.0, current + change)
    threshold = DODGE_DIMINISHING_THRESHOLD if dodge else CRIT_DIMINISHING_THRESHOLD
    asymptote = DODGE_ASYMPTOTE if dodge else CRIT_ASYMPTOTE
    linear = min(change, max(0.0, threshold - current))
    current += linear
    remaining = change - linear
    if remaining <= 0 or current >= asymptote:
        return current
    return asymptote - (asymptote - current) * exp(-remaining / (asymptote - threshold))


def refresh_glass_heart_penalty(player):
    from acts.act_two.bloody_altar import GLASS_HEART, GLASS_HEART_HEALTH_PENALTY_RATIO, has_bloody_pact

    if not has_bloody_pact(player, GLASS_HEART):
        return
    maximum = player.max_health + player.act_two.bloody_pact_health_penalty
    penalty = min(maximum - 1, ceil(maximum * GLASS_HEART_HEALTH_PENALTY_RATIO))
    player.act_two.bloody_pact_health_penalty = penalty
    player.max_health = maximum - penalty
    player.health = min(player.health, player.max_health)
