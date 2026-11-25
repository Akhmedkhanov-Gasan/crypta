from acts.act_three.ability_scaling import familiar_damage_range
from acts.act_three.abilities.summoner_runes import summon_cell_is_free
from acts.act_three.rune_master.definitions import SPIRIT_TOTEM_PLACEMENT_RANGE, SPIRIT_TOTEM_RANGE
from game.events import GameEvent, GameEventType
from logic import get_enemy_occupied_positions, has_line_of_sight
from logic import can_player_move_between


def totem_targets(game_state):
    floor = game_state.floor
    origin = floor.player_column, floor.player_row
    radius = SPIRIT_TOTEM_PLACEMENT_RANGE
    return tuple((origin[0] + dx, origin[1] + dy)
                 for dy in range(-radius, radius + 1) for dx in range(-radius, radius + 1)
                 if summon_cell_is_free(game_state, (origin[0] + dx, origin[1] + dy))
                 and (origin[0] + dx, origin[1] + dy) in floor.visible_cells
                 and can_player_move_between(floor.map, *origin, origin[0] + dx, origin[1] + dy, floor.barriers))


def take_totem_turn(game_state):
    from systems.player_combat import attack_enemy, resolve_enemy_defeat

    player, floor = game_state.player, game_state.floor
    origin = player.summoner_familiar_position
    candidates = [(max(abs(cell[0] - origin[0]), abs(cell[1] - origin[1])), enemy.name, enemy, cell)
                  for enemy in floor.enemies if enemy.health > 0 and not enemy.possessed_by_summoner
                  for cell in get_enemy_occupied_positions(enemy)
                  if max(abs(cell[0] - origin[0]), abs(cell[1] - origin[1])) <= SPIRIT_TOTEM_RANGE
                  and has_line_of_sight(floor.map, *origin, *cell, floor.barriers)]
    if not candidates:
        return
    _, _, enemy, cell = min(candidates, key=lambda item: item[:2])
    player.summoner_familiar_attack_started_at = player.familiar_turn_started_at
    player.summoner_familiar_attack_target = cell
    game_state.emit(GameEvent(type=GameEventType.ATTACK, actor="familiar", origin=origin,
                              destination=cell, positions=(cell,), data={"kind": "summoner_spirit_totem"}))
    damage_minimum, damage_maximum = familiar_damage_range(player)
    defeated = attack_enemy(game_state, enemy, damage_minimum, damage_maximum, 0,
                            attacker_name="familiar", attacker_position=origin, grant_ability_charge=False)
    if enemy.type == "oracle":
        from acts.act_two.enemies.oracle.behavior import resolve_oracle_hit_reaction

        resolve_oracle_hit_reaction(enemy, floor, game_state.combat_log)
    if defeated:
        resolve_enemy_defeat(game_state, enemy)
