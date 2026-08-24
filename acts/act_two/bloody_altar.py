from acts.act_two.bloody_altar_catalog import BLOODY_PACTS_BY_ID
from acts.player_stats import PlayerStatChanges, apply_player_stat_changes
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import GameState


OPEN_WOUND = "open_wound"
BROKEN_SEAL = "broken_seal"
GLASS_HEART = "glass_heart"
BLOOD_HUNGER = "blood_hunger"


def has_bloody_pact(player, pact_id: str) -> bool:
    return player.act_two.bloody_pact_id == pact_id


def bloody_pact_is_available(player, pact_id: str) -> bool:
    if pact_id not in BLOODY_PACTS_BY_ID:
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
        )
        return True

    game_state.bloody_altar_open = True
    game_state.bloody_altar_pending_id = None
    game_state.player_attack_targets = []
    add_log_message(
        game_state.combat_log,
        "The altar offers four bloody pacts.",
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
        apply_player_stat_changes(
            player,
            PlayerStatChanges(
                max_health=-4,
                damage_min=1,
                damage_max=1,
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
    )
    return True


def cancel_bloody_altar(game_state: GameState) -> None:
    game_state.bloody_altar_open = False
    game_state.bloody_altar_pending_id = None


def adjusted_consumable_healing(player, amount: int) -> int:
    if has_bloody_pact(player, BLOOD_HUNGER):
        return max(1, amount // 2)
    return amount


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
    "interact_with_bloody_altar",
    "select_bloody_pact",
]
