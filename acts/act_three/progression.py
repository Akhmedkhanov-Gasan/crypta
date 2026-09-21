from copy import copy

from game.attributes import (
    ATTRIBUTE_ORDER,
    MAX_ATTRIBUTE_RANK,
)
from game.progression import apply_attribute_upgrade


def _pending(player):
    return player.act_three.pending_attribute_upgrades


def get_pending_attribute_points(player):
    return sum(_pending(player).values())


def queue_act_three_attribute_upgrade(player, attribute):
    if attribute not in ATTRIBUTE_ORDER:
        return False

    pending = _pending(player)

    if get_pending_attribute_points(player) >= player.attribute_points:
        return False

    current_rank = player.attribute_ranks.get(attribute)

    if current_rank is None:
        return False

    if current_rank + pending.get(attribute, 0) >= MAX_ATTRIBUTE_RANK:
        return False

    pending[attribute] += 1
    return True


def cancel_act_three_attribute_upgrade(player, attribute):
    if attribute not in ATTRIBUTE_ORDER:
        return False

    pending = _pending(player)

    if pending.get(attribute, 0) <= 0:
        return False

    pending[attribute] -= 1
    return True


def clear_act_three_attribute_upgrades(player):
    pending = _pending(player)

    for attribute in ATTRIBUTE_ORDER:
        pending[attribute] = 0


def confirm_act_three_attribute_upgrades(player):
    pending = _pending(player)
    selected_points = get_pending_attribute_points(player)

    if selected_points <= 0:
        return False

    if selected_points > player.attribute_points:
        return False

    for attribute in ATTRIBUTE_ORDER:
        amount = pending.get(attribute, 0)
        current_rank = player.attribute_ranks.get(attribute, 0)

        if current_rank + amount > MAX_ATTRIBUTE_RANK:
            return False

    for attribute in ATTRIBUTE_ORDER:
        for _ in range(pending.get(attribute, 0)):
            apply_attribute_upgrade(player, attribute)

    player.attribute_points -= selected_points
    clear_act_three_attribute_upgrades(player)
    return True


def get_act_three_attribute_preview(player):
    pending = _pending(player)

    if not any(pending.values()):
        return player

    preview = copy(player)
    preview.attribute_ranks = dict(player.attribute_ranks)

    for attribute in ATTRIBUTE_ORDER:
        for _ in range(pending.get(attribute, 0)):
            apply_attribute_upgrade(preview, attribute)

    return preview
