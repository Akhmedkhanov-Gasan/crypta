from math import ceil

from acts.act_three.rune_master.definitions import (
    BLOOD_WHEEL_RATIO, BLOOD_WHEEL_TURNS, DEATH_WISH_EXTRA_HITS,
    DEVASTATION_ANIMATION_MS, DEVASTATION_RATIO, SECOND_WIND_CAP, SECOND_WIND_RATIO,
    equipped_rune, has_ability_rune,
)
from acts.act_three.settings import BERSERKER_RENDING_SPIN_ANIMATION_MS
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from logic import get_enemy_occupied_positions
from systems.bleeding import apply_bleed
from systems.grid_geometry import can_reach_adjacent_cell


def rage_rune_active(player, identifier):
    return (player.subclass == "berserker" and player.berserker_last_rage_hits > 0
            and player.act_three.berserker_rage_rune == identifier)


def rage_blocks_healing(player):
    return (player.subclass == "berserker" and player.berserker_last_rage_hits > 0
            and player.act_three.berserker_rage_rune in ("rune_of_death_wish", "rune_of_second_wind"))


def begin_rage_rune(player):
    rune = equipped_rune(player, "f")
    player.act_three.berserker_rage_rune = rune.id if rune else None
    player.act_three.berserker_deferred_healing = 0.0
    player.act_three.berserker_rage_extensions = 0
    player.act_three.berserker_rage_released_at = -1
    if rune and rune.id == "rune_of_death_wish":
        player.health = 1


def record_rage_damage(player, damage):
    if damage > 0 and rage_rune_active(player, "rune_of_second_wind"):
        player.act_three.berserker_deferred_healing = min(
            player.max_health * SECOND_WIND_CAP,
            player.act_three.berserker_deferred_healing + damage * SECOND_WIND_RATIO,
        )


def record_rage_kill(game_state):
    player = game_state.player
    if (rage_rune_active(player, "rune_of_death_wish")
            and player.act_three.berserker_rage_extensions < DEATH_WISH_EXTRA_HITS):
        player.act_three.berserker_rage_extensions += 1
        player.berserker_last_rage_hits += 1
        add_log_message(game_state.combat_log, "Death Wish restores one Last Rage hit.", category="rune")


def finish_rage_rune(game_state, current_time):
    from game.healing import heal_player

    player = game_state.player
    rune = player.act_three.berserker_rage_rune
    if rune == "rune_of_death_wish" and player.health > 0:
        player.health = 1
    elif rune == "rune_of_second_wind":
        healed = heal_player(player, int(player.act_three.berserker_deferred_healing + 1e-9))
        if healed:
            game_state.emit(GameEvent(type=GameEventType.HEAL, actor="hero", target="hero",
                                      amount=healed, data={"kind": "rune_of_second_wind"}))
            add_log_message(game_state.combat_log, f"Second Wind restores {healed} HP.", category="healing")
    player.act_three.berserker_deferred_healing = 0.0
    if rune:
        player.act_three.berserker_rage_released_at = current_time


def apply_blood_wheel(player, enemy, damage, current_time):
    if damage <= 0 or not has_ability_rune(player, "rune_of_blood_wheel"):
        return
    player.act_three.berserker_blood_cuts.append((enemy.column, enemy.row, current_time))
    if enemy.health > 0:
        apply_bleed(enemy, max(1, ceil(damage * BLOOD_WHEEL_RATIO)), BLOOD_WHEEL_TURNS)


def spin_duration(player):
    return BERSERKER_RENDING_SPIN_ANIMATION_MS + (
        DEVASTATION_ANIMATION_MS if player.act_three.berserker_devastation_active else 0
    )


def devastation_cells(floor):
    origin = floor.player_column, floor.player_row
    return tuple((origin[0] + dx, origin[1] + dy)
                 for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                 if (dx or dy) and can_reach_adjacent_cell(
                     floor.map, origin, (origin[0] + dx, origin[1] + dy), floor.barriers))


def perform_devastation(game_state, oracle_hit_reaction):
    from systems.player_combat import attack_enemy, resolve_enemy_defeat

    player, floor = game_state.player, game_state.floor
    cells = devastation_cells(floor)
    origin = floor.player_column, floor.player_row
    for enemy in floor.enemies:
        if enemy.health <= 0 or not set(get_enemy_occupied_positions(enemy)).intersection(cells):
            continue
        defeated = attack_enemy(game_state, enemy, player.damage_min, player.damage_max,
                                player.crit_chance, attacker_position=origin,
                                damage_multiplier=DEVASTATION_RATIO, grant_ability_charge=False)
        if enemy.type == "oracle":
            oracle_hit_reaction(enemy, floor, game_state.combat_log)
        if defeated:
            resolve_enemy_defeat(game_state, enemy)
    game_state.emit(GameEvent(type=GameEventType.ATTACK, actor="hero", origin=origin,
                              positions=cells, data={"kind": "rune_of_devastation"}))
