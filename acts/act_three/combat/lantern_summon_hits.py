from acts.act_three.abilities.greater_manifestation import damage_manifestation
from acts.act_three.abilities.summoner import damage_summoner_familiar
from acts.act_three.abilities.summoner_possession import possession_host, sync_host
from acts.act_three.combat.creature_attacks import damage_enemy_from_creature
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from logic import get_enemy_occupied_positions, roll_enemy_damage


def resolve_lantern_summon_hits(game_state, enemy, cells, mode):
    player = game_state.player
    if player.subclass != "summoner":
        return
    cells = set(cells)
    now = player.familiar_turn_started_at
    host = possession_host(game_state)
    if host is not None:
        if get_enemy_occupied_positions(host).intersection(cells):
            damage = damage_enemy_from_creature(game_state, enemy, host, roll_enemy_damage(enemy, mode), mode)
            if host.health > 0:
                sync_host(game_state, host)
            add_log_message(game_state.combat_log, f"{enemy.name} hits {host.name} for {damage}.", category="enemy_attack")
    elif player.summoner_familiar_active and player.summoner_familiar_position in cells:
        position = player.summoner_familiar_position
        damage = damage_summoner_familiar(game_state, roll_enemy_damage(enemy, mode))
        game_state.emit(GameEvent(type=GameEventType.HIT, actor=enemy.name, target="familiar",
                                  origin=(enemy.column, enemy.row), destination=position, amount=damage,
                                  data={"mode": mode}))
    spirit = player.act_three.summoner_manifestation
    if spirit is not None and spirit["health"] > 0 and spirit["floor"] == game_state.floor_index and tuple(spirit["position"]) in cells:
        damage = damage_manifestation(game_state, roll_enemy_damage(enemy, mode), now, attacker=enemy.name)
        game_state.emit(GameEvent(type=GameEventType.HIT, actor=enemy.name, target="greater_manifestation",
                                  origin=(enemy.column, enemy.row), destination=spirit["position"], amount=damage,
                                  data={"mode": mode}))
