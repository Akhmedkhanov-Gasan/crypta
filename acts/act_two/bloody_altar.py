from math import ceil

from acts.act_two.bloody_altar_catalog import BLOODY_PACTS_BY_ID
from acts.player_stats import PlayerStatChanges, apply_player_stat_changes
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import GameState


OPEN_WOUND = "open_wound"
BROKEN_SEAL = "broken_seal"
GLASS_HEART = "glass_heart"
BLOOD_HUNGER = "blood_hunger"
BLOODY_PACT_ORDER = (
    OPEN_WOUND,
    BROKEN_SEAL,
    GLASS_HEART,
    BLOOD_HUNGER,
)
OPEN_WOUND_HEALTH_COST_RATIO = 0.10
GLASS_HEART_DAMAGE_MULTIPLIER = 1.50
GLASS_HEART_HEALTH_PENALTY_RATIO = 0.25
BLOOD_HUNGER_LIFESTEAL_RATIO = 0.25
_BLOODY_PACT_IDS = frozenset(BLOODY_PACT_ORDER)

def has_bloody_pact(player, pact_id: str) -> bool:
    return player.act_two.bloody_pact_id == pact_id


def bloody_pact_is_available(player, pact_id: str) -> bool:
    if pact_id not in _BLOODY_PACT_IDS:
        return False
    if pact_id == BROKEN_SEAL:
        return player.act_two.selected_rune_id is not None
    return True


def bloody_altar_is_at(
    game_state: GameState,
    position: tuple[int, int],
) -> bool:
    altar = game_state.floor.bloody_altar
    return bool(
        altar is not None
        and (altar.column, altar.row) == position
    )


def interact_with_bloody_altar(game_state: GameState) -> bool:
    altar = game_state.floor.bloody_altar
    if altar is None:
        return False
    if altar.claimed or game_state.player.act_two.bloody_pact_id is not None:
        add_log_message(
            game_state.combat_log,
            "The bloody altar has fallen silent.",
            category="altar",
        )
        return True

    game_state.bloody_altar_open = True
    game_state.bloody_altar_pending_id = None
    game_state.player_attack_targets = []
    add_log_message(
        game_state.combat_log,
        "The altar offers four bloody pacts.",
        category="altar",
    )
    return True


def select_bloody_pact(game_state: GameState, pact_id: str) -> bool:
    if (
        not game_state.bloody_altar_open
        or not bloody_pact_is_available(game_state.player, pact_id)
    ):
        return False
    game_state.bloody_altar_pending_id = pact_id
    return True


def confirm_bloody_pact(game_state: GameState) -> bool:
    altar = game_state.floor.bloody_altar
    pact_id = game_state.bloody_altar_pending_id
    pact = BLOODY_PACTS_BY_ID.get(pact_id)
    if (
        altar is None
        or altar.claimed
        or pact is None
        or game_state.player.act_two.bloody_pact_id is not None
        or not bloody_pact_is_available(game_state.player, pact.id)
    ):
        return False

    player = game_state.player
    if pact.id == BROKEN_SEAL:
        player.act_two.selected_rune_id = None
        player.ability_kill_charge = min(2, player.ability_kill_charge)
    elif pact.id == GLASS_HEART:
        health_penalty = max(
            1,
            ceil(
                player.max_health
                * GLASS_HEART_HEALTH_PENALTY_RATIO
            ),
        )

        apply_player_stat_changes(
            player,
            PlayerStatChanges(
                max_health=-health_penalty,
            ),
        )

    player.act_two.bloody_pact_id = pact.id
    altar.claimed = True
    game_state.bloody_altar_open = False
    game_state.bloody_altar_pending_id = None
    game_state.emit(
        GameEvent(
            type=GameEventType.ENVIRONMENT,
            actor="bloody altar",
            origin=(altar.column, altar.row),
            data={"kind": "bloody_pact", "pact_id": pact.id},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"The hero accepts {pact.name}.",
        category="altar",
    )
    return True


def cancel_bloody_altar(game_state: GameState) -> None:
    game_state.bloody_altar_open = False
    game_state.bloody_altar_pending_id = None


def adjusted_consumable_healing(player, amount: int) -> int:
    if healing_consumables_are_blocked(player):
        return 0
    return amount


def open_wound_ability_health_cost(player) -> int:
    return max(
        1,
        ceil(
            player.max_health
            * OPEN_WOUND_HEALTH_COST_RATIO
        ),
    )


def open_wound_ability_is_affordable(player) -> bool:
    if not has_bloody_pact(player, OPEN_WOUND):
        return True

    return (
        player.health
        > open_wound_ability_health_cost(player)
    )


def pay_open_wound_ability_cost(
    game_state: GameState,
) -> bool:
    player = game_state.player

    if not has_bloody_pact(player, OPEN_WOUND):
        return True

    health_cost = open_wound_ability_health_cost(player)

    if player.health <= health_cost:
        add_log_message(
            game_state.combat_log,
            "Not enough health to invoke Open Wound.",
            category="warning",
        )
        return False

    player.health -= health_cost

    add_log_message(
        game_state.combat_log,
        (
            f"Open Wound consumes "
            f"{health_cost} health."
        ),
        category="altar",
    )
    return True


def adjusted_outgoing_damage(
    player,
    damage: int,
) -> int:
    if has_bloody_pact(player, GLASS_HEART):
        damage = ceil(
            damage
            * GLASS_HEART_DAMAGE_MULTIPLIER
        )

    return damage


def healing_consumables_are_blocked(player) -> bool:
    return has_bloody_pact(player, BLOOD_HUNGER)


__all__ = [
    "BLOOD_HUNGER",
    "BROKEN_SEAL",
    "GLASS_HEART",
    "OPEN_WOUND",
    "adjusted_consumable_healing",
    "bloody_altar_is_at",
    "bloody_pact_is_available",
    "cancel_bloody_altar",
    "confirm_bloody_pact",
    "has_bloody_pact",
    "healing_consumables_are_blocked",
    "interact_with_bloody_altar",
    "select_bloody_pact",
    "adjusted_outgoing_damage",
]
