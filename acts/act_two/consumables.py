from bosses.oracle import resolve_oracle_hit_reaction
from acts.act_two.settings import (
    CONSUMABLE_BELT_SIZE,
    FIRE_BOMB_DAMAGE,
    FIRE_BOMB_TOTAL_TICKS,
)
from acts.act_two.state import FireZoneState
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState, GameState
from logic import can_move_to, get_enemy_occupied_positions
from systems.player_combat import damage_player, resolve_enemy_defeat


POTION = "potion"
FIRE_BOMB = "fire_bomb"


def initialize_act_two_consumable_belt(player) -> None:
    if player.act_two.consumable_belt_initialized:
        return

    potion_slots = min(
        player.potion_count,
        CONSUMABLE_BELT_SIZE - 1,
    )
    player.potion_count = potion_slots
    items = [POTION] * potion_slots + [FIRE_BOMB]
    player.act_two.consumable_slots = items + [
        None
    ] * (CONSUMABLE_BELT_SIZE - len(items))
    player.act_two.consumable_belt_initialized = True


def get_act_two_consumable_slots(player) -> tuple[str | None, ...]:
    return tuple(player.act_two.consumable_slots)


def act_two_belt_is_full(player) -> bool:
    return all(item is not None for item in player.act_two.consumable_slots)


def store_act_two_consumable(player, item: str) -> bool:
    for slot_index, stored_item in enumerate(
        player.act_two.consumable_slots
    ):
        if stored_item is not None:
            continue
        player.act_two.consumable_slots[slot_index] = item
        if item == POTION:
            player.potion_count += 1
        return True
    return False


def consume_act_two_potion(player, slot_index: int | None = None) -> bool:
    slots = player.act_two.consumable_slots
    if slot_index is None:
        slot_index = next(
            (
                index
                for index, item in enumerate(slots)
                if item == POTION
            ),
            None,
        )
    if (
        slot_index is None
        or not 0 <= slot_index < len(slots)
        or slots[slot_index] != POTION
    ):
        return False
    slots[slot_index] = None
    player.potion_count = max(0, player.potion_count - 1)
    return True


def request_fire_bomb_aiming(game_state: GameState, slot_index: int) -> bool:
    player = game_state.player
    slots = player.act_two.consumable_slots
    if (
        not 0 <= slot_index < len(slots)
        or slots[slot_index] != FIRE_BOMB
    ):
        return False
    player.act_two.fire_bomb_aiming = True
    player.act_two.fire_bomb_aiming_slot = slot_index
    add_log_message(
        game_state.combat_log,
        "Choose a visible tile for the fire bomb.",
    )
    return True


def cancel_fire_bomb_aiming(game_state: GameState) -> None:
    game_state.player.act_two.fire_bomb_aiming = False
    game_state.player.act_two.fire_bomb_aiming_slot = None


def fire_bomb_zone_cells(
    dungeon_map: list[str],
    center: tuple[int, int],
) -> tuple[tuple[int, int], ...]:
    center_column, center_row = center
    return tuple(
        (column, row)
        for row in range(center_row - 1, center_row + 2)
        for column in range(center_column - 1, center_column + 2)
        if can_move_to(dungeon_map, column, row)
    )


def is_valid_fire_bomb_target(
    game_state: GameState,
    target: tuple[int, int] | None,
) -> bool:
    return (
        target is not None
        and target in game_state.floor.visible_cells
        and can_move_to(game_state.floor.map, target[0], target[1])
    )


def _damage_enemy_with_fire(game_state, enemy, position) -> None:
    damage = min(FIRE_BOMB_DAMAGE, enemy.health)
    if damage <= 0:
        return
    enemy.health -= damage
    game_state.emit(
        GameEvent(
            type=GameEventType.HIT,
            actor="fire",
            target=enemy.name,
            origin=position,
            destination=(enemy.column, enemy.row),
            amount=damage,
            data={"kind": "fire_bomb", "enemy_type": enemy.type},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"Fire burns {enemy.name} for {damage}.",
    )

    if (
        enemy.type in ("warden", "oracle")
        and enemy.health > 0
        and enemy.health <= enemy.max_health // 2
        and not enemy.second_phase_announced
    ):
        enemy.second_phase_announced = True
        if enemy.type == "oracle":
            enemy.phase_transition_pending = True
        add_log_message(
            game_state.combat_log,
            f"{enemy.name} enters phase two!",
        )

    if enemy.type == "oracle":
        resolve_oracle_hit_reaction(
            enemy,
            game_state.floor,
            game_state.combat_log,
        )

    if enemy.health > 0:
        return
    enemy.behavior_state = EnemyBehaviorState.DEAD
    game_state.emit(
        GameEvent(
            type=GameEventType.DEATH,
            actor=enemy.name,
            destination=(enemy.column, enemy.row),
            data={"enemy_type": enemy.type, "cause": "fire"},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"{enemy.name} is defeated.",
    )
    resolve_enemy_defeat(game_state, enemy)


def _damage_player_with_fire(game_state, zone) -> None:
    floor = game_state.floor
    player = game_state.player
    player_position = (floor.player_column, floor.player_row)
    if player.health <= 0 or player_position not in zone.cells:
        return
    damage = damage_player(game_state, FIRE_BOMB_DAMAGE)
    if damage <= 0:
        return
    game_state.emit(
        GameEvent(
            type=GameEventType.HIT,
            actor="fire",
            target="hero",
            origin=zone.center,
            destination=player_position,
            amount=damage,
            data={"kind": "fire_bomb"},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"Fire burns hero for {damage}.",
    )
    if player.invisibility_turns > 0:
        player.invisibility_turns = 0
        add_log_message(
            game_state.combat_log,
            "The rogue becomes visible after taking damage.",
        )
    if player.health <= 0:
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor="hero",
                destination=player_position,
                data={"cause": "fire"},
            )
        )
        add_log_message(game_state.combat_log, "The hero has fallen.")


def apply_fire_zone_tick(game_state: GameState, zone: FireZoneState) -> None:
    zone_cells = set(zone.cells)
    from acts.act_two.crates import break_crate

    for crate in game_state.floor.breakable_crates:
        if (
            not crate.is_broken
            and (crate.column, crate.row) in zone_cells
        ):
            break_crate(game_state, crate, cause="fire_bomb")
    for enemy in game_state.floor.enemies:
        if enemy.health <= 0:
            continue
        occupied_positions = get_enemy_occupied_positions(enemy)
        burning_positions = zone_cells.intersection(occupied_positions)
        if burning_positions:
            _damage_enemy_with_fire(
                game_state,
                enemy,
                next(iter(burning_positions)),
            )
    _damage_player_with_fire(game_state, zone)


def throw_fire_bomb(
    game_state: GameState,
    slot_index: int,
    target: tuple[int, int],
    started_at: int,
) -> bool:
    player = game_state.player
    if (
        not is_valid_fire_bomb_target(game_state, target)
        or not 0 <= slot_index < len(player.act_two.consumable_slots)
        or player.act_two.consumable_slots[slot_index] != FIRE_BOMB
    ):
        return False

    player.act_two.consumable_slots[slot_index] = None
    player.act_two.fire_bomb_aiming = False
    player.act_two.fire_bomb_aiming_slot = None
    origin = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    zone = FireZoneState(
        center=target,
        cells=fire_bomb_zone_cells(game_state.floor.map, target),
        origin=origin,
        created_at=started_at,
        ticks_remaining=FIRE_BOMB_TOTAL_TICKS - 1,
    )
    game_state.floor.fire_zones.append(zone)
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=origin,
            positions=zone.cells,
            data={"kind": "fire_bomb", "target": target},
        )
    )
    add_log_message(game_state.combat_log, "The fire bomb shatters.")
    apply_fire_zone_tick(game_state, zone)
    return True


def advance_fire_zones(game_state: GameState) -> None:
    from acts.act_two.crates import advance_burning_crate_loot

    active_zones = []
    burning_cells = set()
    for zone in game_state.floor.fire_zones:
        if zone.skip_next_advance:
            zone.skip_next_advance = False
            active_zones.append(zone)
            continue
        if zone.ticks_remaining <= 0:
            continue
        burning_cells.update(zone.cells)
        apply_fire_zone_tick(game_state, zone)
        zone.ticks_remaining -= 1
        if zone.ticks_remaining > 0:
            active_zones.append(zone)
    advance_burning_crate_loot(game_state, burning_cells)
    game_state.floor.fire_zones = active_zones


__all__ = [
    "FIRE_BOMB",
    "POTION",
    "act_two_belt_is_full",
    "advance_fire_zones",
    "cancel_fire_bomb_aiming",
    "consume_act_two_potion",
    "fire_bomb_zone_cells",
    "get_act_two_consumable_slots",
    "initialize_act_two_consumable_belt",
    "is_valid_fire_bomb_target",
    "request_fire_bomb_aiming",
    "store_act_two_consumable",
    "throw_fire_bomb",
]
