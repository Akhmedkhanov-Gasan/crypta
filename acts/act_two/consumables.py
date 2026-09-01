from bosses.oracle import resolve_oracle_hit_reaction
from acts.act_two.settings import (
    ARCANE_IMPULSE_SCROLL_DAMAGE,
    BINDING_SCROLL_TURNS,
    CONSUMABLE_BELT_SIZE,
    FIRE_BOMB_DAMAGE,
    FIRE_BOMB_TOTAL_TICKS,
    HEALING_SCROLL_HEALING,
    STONEFLESH_SCROLL_HITS,
)
from acts.act_two.bloody_altar import (
    adjusted_consumable_healing,
    healing_consumables_are_blocked,
)
from acts.act_two.state import DroppedConsumableState, FireZoneState
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState, GameState
from logic import (
    can_move_to,
    can_player_move_between,
    get_enemy_occupied_positions,
)
from systems.player_combat import damage_player, resolve_enemy_defeat
from acts.act_two.presentation.bosses.oracle_balance import (
    ORACLE_BINDING_TURNS,
)


POTION = "potion"
FIRE_BOMB = "fire_bomb"
KEY = "key"
GUILD_SEAL = "guild_seal"
SCROLL_OF_STONEFLESH = "scroll_of_stoneflesh"
SCROLL_OF_BINDING = "scroll_of_binding"
HEALING_SCROLL = "healing_scroll"
SCROLL_OF_ARCANE_IMPULSE = "scroll_of_arcane_impulse"
SCROLLS = (
    SCROLL_OF_STONEFLESH,
    SCROLL_OF_BINDING,
    HEALING_SCROLL,
    SCROLL_OF_ARCANE_IMPULSE,
)
TARGETED_SCROLLS = (
    SCROLL_OF_BINDING,
    SCROLL_OF_ARCANE_IMPULSE,
)


def initialize_act_two_consumable_belt(player) -> None:
    if player.act_two.consumable_belt_initialized:
        return

    potion_slots = min(player.potion_count, CONSUMABLE_BELT_SIZE)
    key_slots = min(
        player.key_count,
        CONSUMABLE_BELT_SIZE - potion_slots,
    )
    player.potion_count = potion_slots
    player.key_count = key_slots
    items = [POTION] * potion_slots + [KEY] * key_slots
    player.act_two.consumable_slots = items + [
        None
    ] * (CONSUMABLE_BELT_SIZE - len(items))
    player.act_two.consumable_belt_initialized = True


def grant_act_two_test_scrolls(player) -> None:
    existing_items = [
        item
        for item in player.act_two.consumable_slots
        if item not in SCROLLS and item is not None
    ][: CONSUMABLE_BELT_SIZE - len(SCROLLS)]
    if not existing_items:
        existing_items.append(FIRE_BOMB)
    items = [*existing_items, *SCROLLS]
    player.act_two.consumable_slots = items + [
        None
    ] * (CONSUMABLE_BELT_SIZE - len(items))
    player.potion_count = existing_items.count(POTION)
    player.key_count = existing_items.count(KEY)


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
        elif item == KEY:
            player.key_count += 1
        return True
    return False


def remove_act_two_consumable(player, slot_index: int) -> str | None:
    slots = player.act_two.consumable_slots
    if not 0 <= slot_index < len(slots):
        return None
    item = slots[slot_index]
    if item is None:
        return None
    slots[slot_index] = None
    if item == POTION:
        player.potion_count = max(0, player.potion_count - 1)
    elif item == KEY:
        player.key_count = max(0, player.key_count - 1)
    return item


def remove_act_two_consumable_kind(
    player,
    item_kind,
):
    for slot_index, stored_item in enumerate(
        player.act_two.consumable_slots
    ):
        if stored_item != item_kind:
            continue

        remove_act_two_consumable(
            player,
            slot_index,
        )
        return True

    return False


def throw_act_two_consumable(
    game_state: GameState,
    slot_index: int,
    target: tuple[int, int],
    thrown_at: int,
) -> bool:
    floor = game_state.floor
    player = game_state.player
    slots = player.act_two.consumable_slots

    if (
        0 <= slot_index < len(slots)
        and slots[slot_index] == GUILD_SEAL
    ):
        add_log_message(
            game_state.combat_log,
            "The guild seal must be returned to the trader.",
            category="quest",
        )
        return False
    origin = (floor.player_column, floor.player_row)
    if not can_player_move_between(
        floor.map,
        *origin,
        *target,
        floor.barriers,
    ):
        return False
    occupied_positions = {
        position
        for enemy in floor.enemies
        if enemy.health > 0
        for position in get_enemy_occupied_positions(enemy)
    }
    occupied_positions.update(
        (chest.column, chest.row)
        for chest in floor.chests
    )
    occupied_positions.update(
        (crate.column, crate.row)
        for crate in floor.breakable_crates
        if not crate.is_broken
    )
    occupied_positions.update(
        dropped.destination
        for dropped in floor.dropped_consumables
    )
    occupied_positions.update(floor.dropped_keys)
    occupied_positions.update(floor.dropped_gold)
    occupied_positions.update(
        (potion.column, potion.row)
        for potion in floor.potions
    )
    occupied_positions.add((floor.stairs_column, floor.stairs_row))
    if floor.boss_door is not None:
        occupied_positions.add(floor.boss_door)
    if floor.treasury_room is not None:
        occupied_positions.add(floor.treasury_room.chest_position)
        occupied_positions.update(floor.treasury_room.statue_positions)
    if floor.rune_room is not None:
        occupied_positions.add(floor.rune_room.pedestal_position)
    if target in occupied_positions:
        return False

    item = remove_act_two_consumable(player, slot_index)
    if item is None:
        return False
    floor.dropped_consumables.append(
        DroppedConsumableState(
            kind=item,
            origin=origin,
            destination=target,
            thrown_at=thrown_at,
        )
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.ENVIRONMENT,
            actor="hero",
            origin=origin,
            destination=target,
            data={"kind": "consumable_drop", "item": item},
        )
    )
    add_log_message(
        game_state.combat_log,
        "Hero drops an item.",
        category="neutral",
    )
    return True


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


def consume_act_two_key(player) -> bool:
    slot_index = next(
        (
            index
            for index, item in enumerate(player.act_two.consumable_slots)
            if item == KEY
        ),
        None,
    )
    if slot_index is None:
        return False
    player.act_two.consumable_slots[slot_index] = None
    player.key_count = max(0, player.key_count - 1)
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
        category="ability",
    )
    return True


def cancel_fire_bomb_aiming(game_state: GameState) -> None:
    game_state.player.act_two.fire_bomb_aiming = False
    game_state.player.act_two.fire_bomb_aiming_slot = None


def request_scroll_aiming(
    game_state: GameState,
    slot_index: int,
) -> bool:
    player = game_state.player
    slots = player.act_two.consumable_slots
    if (
        not 0 <= slot_index < len(slots)
        or slots[slot_index] not in TARGETED_SCROLLS
    ):
        return False
    player.act_two.scroll_aiming_kind = slots[slot_index]
    player.act_two.scroll_aiming_slot = slot_index
    add_log_message(
        game_state.combat_log,
        "Choose a visible enemy for the scroll.",
        category="ability",
    )
    return True


def cancel_scroll_aiming(game_state: GameState) -> None:
    game_state.player.act_two.scroll_aiming_kind = None
    game_state.player.act_two.scroll_aiming_slot = None


def enemy_at_scroll_target(
    game_state: GameState,
    target: tuple[int, int] | None,
):
    if target is None or target not in game_state.floor.visible_cells:
        return None
    return next(
        (
            enemy
            for enemy in game_state.floor.enemies
            if (
                enemy.health > 0
                and target in get_enemy_occupied_positions(enemy)
            )
        ),
        None,
    )


def _consume_scroll(player, slot_index: int) -> None:
    player.act_two.consumable_slots[slot_index] = None
    player.act_two.scroll_aiming_kind = None
    player.act_two.scroll_aiming_slot = None


def _damage_enemy_with_arcane_impulse(game_state, enemy) -> None:
    damage = min(ARCANE_IMPULSE_SCROLL_DAMAGE, enemy.health)
    enemy.health -= damage
    origin = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.HIT,
            actor="hero",
            target=enemy.name,
            origin=origin,
            destination=(enemy.column, enemy.row),
            amount=damage,
            data={"kind": SCROLL_OF_ARCANE_IMPULSE},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"Arcane Impulse hits {enemy.name} for {damage}.",
        category="ability",
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
            category="warning",
        )
    if enemy.type == "oracle":
        resolve_oracle_hit_reaction(
            enemy,
            game_state.floor,
            game_state.combat_log,
        )
    if enemy.health <= 0:
        enemy.behavior_state = EnemyBehaviorState.DEAD
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor=enemy.name,
                destination=(enemy.column, enemy.row),
                data={
                    "enemy_type": enemy.type,
                    "cause": SCROLL_OF_ARCANE_IMPULSE,
                },
            )
        )
        add_log_message(
            game_state.combat_log,
            f"{enemy.name} is defeated.",
            category="death",
        )
        resolve_enemy_defeat(game_state, enemy)


def use_scroll(
    game_state: GameState,
    slot_index: int,
    target: tuple[int, int] | None = None,
    effect_started_at: int = 0,
) -> bool:
    player = game_state.player
    slots = player.act_two.consumable_slots
    if (
        not 0 <= slot_index < len(slots)
        or slots[slot_index] not in SCROLLS
    ):
        return False
    scroll_kind = slots[slot_index]

    if (
            scroll_kind == HEALING_SCROLL
            and healing_consumables_are_blocked(player)
    ):
        add_log_message(
            game_state.combat_log,
            "Blood Hunger prevents you from using healing consumables.",
            category="warning",
        )
        return False

    if scroll_kind == SCROLL_OF_STONEFLESH:
        player.act_two.stoneflesh_hits = STONEFLESH_SCROLL_HITS
        player.act_two.stoneflesh_effect_started_at = effect_started_at
        message = (
            f"Stoneflesh will blunt the next "
            f"{STONEFLESH_SCROLL_HITS} physical hits."
        )
    elif scroll_kind == HEALING_SCROLL:
        if player.health >= player.max_health:
            return False
        previous_health = player.health
        player.health = min(
            player.max_health,
            player.health
            + adjusted_consumable_healing(
                player,
                HEALING_SCROLL_HEALING,
            ),
        )
        healed = player.health - previous_health
        game_state.emit(
            GameEvent(
                type=GameEventType.HEAL,
                actor="hero",
                target="hero",
                amount=healed,
                data={"kind": HEALING_SCROLL},
            )
        )
        message = f"Healing Scroll restores {healed} HP."
    else:
        enemy = enemy_at_scroll_target(game_state, target)
        if enemy is None:
            return False
        if scroll_kind == SCROLL_OF_BINDING:
            phase_two = game_state.floor.oracle_phase_two

            if (
                phase_two is not None
                and enemy.type in (
                    "oracle",
                    "oracle_pillar",
                )
            ):
                enemy = phase_two.caster

            binding_turns = (
                ORACLE_BINDING_TURNS
                if enemy.type == "oracle"
                else BINDING_SCROLL_TURNS
            )

            enemy.binding_turns = binding_turns
            enemy.attack_targets = []
            enemy.prepared_attack_mode = None
            enemy.attack_windup_turns_remaining = 0

            if (
                enemy.behavior_state
                is EnemyBehaviorState.PREPARING_ATTACK
            ):
                enemy.behavior_state = EnemyBehaviorState.CHASING

            message = (
                f"{enemy.name} is bound for "
                f"{binding_turns} turns."
            )
        else:
            player.act_two.scroll_effect_started_at = effect_started_at
            player.act_two.scroll_effect_kind = scroll_kind
            player.act_two.scroll_effect_origin = (
                game_state.floor.player_column,
                game_state.floor.player_row,
            )
            player.act_two.scroll_effect_target = (
                enemy.column,
                enemy.row,
            )
            _damage_enemy_with_arcane_impulse(game_state, enemy)
            message = None

    _consume_scroll(player, slot_index)
    game_state.run_stats.consumables_used += 1

    if message is not None:
        message_category = {
            SCROLL_OF_STONEFLESH: "buff",
            HEALING_SCROLL: "healing",
            SCROLL_OF_BINDING: "debuff",
        }.get(
            scroll_kind,
            "ability",
        )

        add_log_message(
            game_state.combat_log,
            message,
            category=message_category,
        )

    return True


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
        category="environment",
    )
    if enemy.type == "oracle_pillar":
        from acts.act_two.presentation.bosses.oracle_phase_two import (
            resolve_oracle_pillar_hit,
        )

        resolve_oracle_pillar_hit(
            game_state,
            enemy,
            damage,
        )
        return

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
        category="death",
    )
    resolve_enemy_defeat(game_state, enemy)


def _damage_player_with_fire(game_state, zone) -> None:
    floor = game_state.floor
    player = game_state.player
    player_position = (floor.player_column, floor.player_row)
    if player.health <= 0 or player_position not in zone.cells:
        return
    damage = damage_player(
        game_state,
        FIRE_BOMB_DAMAGE,
        damage_kind="fire",
    )
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
        category="enemy_attack",
    )
    if player.invisibility_turns > 0:
        player.invisibility_turns = 0
        add_log_message(
            game_state.combat_log,
            "The rogue becomes visible after taking damage.",
            category="debuff",
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
        add_log_message(
            game_state.combat_log,
            "The hero has fallen.",
            category="death",
        )


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
        if (
            enemy.type == "oracle"
            and enemy.oracle_phase == 2
        ):
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
    game_state.run_stats.consumables_used += 1
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
    add_log_message(
        game_state.combat_log,
        "The fire bomb shatters.",
        category="environment",
    )
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
    "HEALING_SCROLL",
    "KEY",
    "POTION",
    "SCROLLS",
    "SCROLL_OF_ARCANE_IMPULSE",
    "SCROLL_OF_BINDING",
    "SCROLL_OF_STONEFLESH",
    "TARGETED_SCROLLS",
    "act_two_belt_is_full",
    "advance_fire_zones",
    "cancel_fire_bomb_aiming",
    "cancel_scroll_aiming",
    "consume_act_two_potion",
    "consume_act_two_key",
    "fire_bomb_zone_cells",
    "get_act_two_consumable_slots",
    "grant_act_two_test_scrolls",
    "initialize_act_two_consumable_belt",
    "is_valid_fire_bomb_target",
    "enemy_at_scroll_target",
    "request_fire_bomb_aiming",
    "request_scroll_aiming",
    "remove_act_two_consumable",
    "store_act_two_consumable",
    "throw_fire_bomb",
    "throw_act_two_consumable",
    "use_scroll",
    "GUILD_SEAL",
    "remove_act_two_consumable_kind",
]
