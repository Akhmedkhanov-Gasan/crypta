import pygame

from acts.act_three.combat.stun import apply_act_three_enemy_stun
from acts.act_three.trader_catalog import (
    ARCANE_IMPULSE_DAMAGE,
    BLAST_CHARGE_DAMAGE,
    FIRE_BOMB_IMPACT,
    HEALING_SCROLL_HEALING,
    IRONBLOOD_HEALING,
    POTION_HEALING,
    REGENERATION_HEALING,
    REGENERATION_TICKS,
    SPRING_TRAP_DAMAGE,
    TRADER_ITEMS,
)
from acts.act_two.bloody_altar import healing_consumables_are_blocked
from acts.act_two.consumables import (
    FIRE_BOMB,
    POTION,
    SCROLLS,
    TARGETED_SCROLLS,
    enemy_at_scroll_target,
    fire_bomb_zone_cells,
    is_valid_fire_bomb_target,
    remove_act_two_consumable,
    throw_fire_bomb,
    use_scroll,
)
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.healing import heal_player
from game.state import EnemyBehaviorState
from logic import can_player_move_between, get_enemy_occupied_positions
from systems.grid_geometry import can_reach_adjacent_cell
from systems.player_actions import try_use_potion
from systems.player_combat import resolve_enemy_defeat


HEALING_ITEMS = frozenset({"potion", "healing_scroll", "ironblood_tonic", "regeneration_draught"})
TARGETED_ITEMS = frozenset((*TARGETED_SCROLLS, FIRE_BOMB, "flash_bomb", "blast_charge", "spring_trap"))
CROSS_OFFSETS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))


def belt_item(player, slot):
    slots = player.act_two.consumable_slots
    return slots[slot] if slot is not None and 0 <= slot < len(slots) else None


def _heal(game_state, item_id, amount):
    healed = heal_player(game_state.player, amount)
    if healed <= 0:
        return
    game_state.emit(GameEvent(
        type=GameEventType.HEAL,
        actor="hero",
        target="hero",
        amount=healed,
        data={"kind": item_id},
    ))
    add_log_message(game_state.combat_log, f"{TRADER_ITEMS[item_id].name} restores {healed} HP.", category="healing")


def advance_regeneration(game_state):
    player = game_state.player
    ticks = player.act_three.regeneration_ticks
    if ticks <= 0:
        return
    player.act_three.regeneration_ticks -= 1
    if ticks < REGENERATION_TICKS and not healing_consumables_are_blocked(player):
        _heal(game_state, "regeneration_draught", REGENERATION_HEALING)


def _occupied(floor, target, except_enemy=None):
    return any(
        enemy.health > 0 and enemy is not except_enemy and target in get_enemy_occupied_positions(enemy)
        for enemy in floor.enemies
    )


def valid_consumable_target(game_state, item_id, target):
    if item_id not in TARGETED_ITEMS:
        return False
    if item_id in TARGETED_SCROLLS:
        return enemy_at_scroll_target(game_state, target) is not None
    if not is_valid_fire_bomb_target(game_state, target):
        return False
    if item_id != "spring_trap":
        return True
    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    return (
        target not in floor.act_three_spring_traps
        and not _occupied(floor, target)
        and can_reach_adjacent_cell(floor.map, origin, target, floor.barriers)
    )


def _damage_enemy(game_state, enemy, amount, item_id):
    amount = min(enemy.health, amount)
    enemy.health -= amount
    destination = (enemy.column, enemy.row)
    game_state.emit(GameEvent(
        type=GameEventType.HIT,
        actor="hero",
        target=enemy.name,
        destination=destination,
        amount=amount,
        data={"kind": item_id, "enemy_type": enemy.type, "critical": False},
    ))
    add_log_message(
        game_state.combat_log,
        f"{TRADER_ITEMS[item_id].name} hits {enemy.name} for {amount}.",
        category="ability",
    )
    if enemy.health > 0:
        return
    enemy.behavior_state = EnemyBehaviorState.DEAD
    game_state.emit(GameEvent(
        type=GameEventType.DEATH,
        actor="hero",
        target=enemy.name,
        destination=destination,
        data={"enemy_type": enemy.type, "cause": item_id},
    ))
    resolve_enemy_defeat(game_state, enemy)


def _push_from_blast(game_state, enemy, center):
    floor = game_state.floor
    origin = (enemy.column, enemy.row)
    if (
        enemy.is_immobile
        or len(get_enemy_occupied_positions(enemy)) != 1
        or origin == center
    ):
        return
    destination = (2 * origin[0] - center[0], 2 * origin[1] - center[1])
    if (
        destination == (floor.player_column, floor.player_row)
        or _occupied(floor, destination, enemy)
        or not can_player_move_between(floor.map, *origin, *destination, floor.barriers)
    ):
        return
    enemy.column, enemy.row = destination
    game_state.emit(GameEvent(
        type=GameEventType.MOVE, actor=enemy.name, origin=origin, destination=destination,
        data={"kind": "blast_charge", "enemy_type": enemy.type},
    ))


def trigger_spring_trap(game_state, enemy, current_time):
    traps = game_state.floor.act_three_spring_traps
    if enemy.health <= 0:
        return
    triggered = traps.intersection(get_enemy_occupied_positions(enemy))
    if not triggered:
        return
    traps.remove(min(triggered))
    _damage_enemy(game_state, enemy, SPRING_TRAP_DAMAGE, "spring_trap")
    if enemy.health > 0:
        apply_act_three_enemy_stun(game_state, enemy, 1, current_time)


def _use_area_item(game_state, item_id, target, current_time):
    floor = game_state.floor
    if item_id == "spring_trap":
        floor.act_three_spring_traps.add(target)
        return
    if item_id == "flash_bomb":
        cells = set(fire_bomb_zone_cells(floor.map, target))
    else:
        cells = {target}
        for dx, dy in CROSS_OFFSETS[1:]:
            cell = (target[0] + dx, target[1] + dy)
            if can_player_move_between(floor.map, *target, *cell, floor.barriers):
                cells.add(cell)
    for enemy in tuple(floor.enemies):
        if enemy.health <= 0 or cells.isdisjoint(get_enemy_occupied_positions(enemy)):
            continue
        if item_id == "flash_bomb":
            apply_act_three_enemy_stun(game_state, enemy, 1, current_time)
        else:
            _damage_enemy(game_state, enemy, BLAST_CHARGE_DAMAGE, item_id)
            if enemy.health > 0:
                _push_from_blast(game_state, enemy, target)
                trigger_spring_trap(game_state, enemy, current_time)


def use_belt_item(game_state, slot, target, current_time):
    player = game_state.player
    item_id = belt_item(player, slot)
    if item_id not in TRADER_ITEMS:
        return False
    if item_id in TARGETED_ITEMS and not valid_consumable_target(game_state, item_id, target):
        return False
    if item_id == POTION:
        if not try_use_potion(game_state, slot, healing_amount=POTION_HEALING):
            return False
        player.potion_effect_started_at = current_time
        return True
    if item_id in SCROLLS:
        return use_scroll(
            game_state, slot, target, current_time,
            healing_amount=HEALING_SCROLL_HEALING, impulse_damage=ARCANE_IMPULSE_DAMAGE,
        )
    if item_id == FIRE_BOMB:
        return throw_fire_bomb(game_state, slot, target, current_time, impact_damage=FIRE_BOMB_IMPACT)
    if item_id in HEALING_ITEMS:
        if healing_consumables_are_blocked(player):
            add_log_message(
                game_state.combat_log,
                "Blood Hunger prevents you from using healing consumables.",
                category="warning",
            )
            return False
        if item_id == "regeneration_draught":
            if player.health >= player.max_health or player.act_three.regeneration_ticks > 0:
                return False
            player.act_three.regeneration_ticks = REGENERATION_TICKS
            _heal(game_state, item_id, REGENERATION_HEALING)
        else:
            player.act_three.ironblood_guard = True
            _heal(game_state, item_id, IRONBLOOD_HEALING)
        player.potion_effect_started_at = current_time
    else:
        _use_area_item(game_state, item_id, target, current_time)
        add_log_message(game_state.combat_log, f"Used {TRADER_ITEMS[item_id].name}.", category="ability")
    remove_act_two_consumable(player, slot)
    game_state.run_stats.consumables_used += 1
    return True
