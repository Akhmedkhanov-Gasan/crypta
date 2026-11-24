from math import ceil

from acts.act_three.settings import SUMMONER_TRUE_FORM_DAMAGE_BONUS, SUMMONER_TRUE_FORM_HEALTH_BONUS
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType


SOUL_DAMAGE_STEP = 0.25
SOUL_KILL_HEAL_RATIO = 0.9
MANIFESTATION_SUMMON_MS = 880
MANIFESTATION_DEATH_MS = 960
MANIFESTATION_MOVE_MS = 360
MANIFESTATION_ATTACK_MS = 480
MANIFESTATION_HURT_MS = 320
MANIFESTATION_IDLE_FRAME_MS = 300


def manifestation_alive(player):
    spirit = player.act_three.summoner_manifestation
    return spirit is not None and spirit["health"] > 0


def manifestation_attack_cost(spirit):
    return 1 + spirit["attacks"] if spirit["devourer"] else 1


def manifestation_animation_busy(spirit, now):
    return any(started >= 0 and 0 <= now - started < duration for started, duration in (
        (spirit["summoned_at"], MANIFESTATION_SUMMON_MS),
        (spirit["move_at"], MANIFESTATION_MOVE_MS),
        (spirit["attack_at"], MANIFESTATION_ATTACK_MS),
    ))


def summon_manifestation(game_state, now, devourer, position):
    player, floor = game_state.player, game_state.floor
    from acts.act_three.abilities.manifestation_targeting import manifestation_targets

    if position not in manifestation_targets(game_state):
        add_log_message(game_state.combat_log, "There is no free cell for Greater Manifestation.", category="warning")
        return False
    maximum = max(1, player.max_health // 2) + SUMMONER_TRUE_FORM_HEALTH_BONUS
    player.act_three.summoner_manifestation = {
        "position": position, "health": maximum, "max_health": maximum,
        "floor": game_state.floor_index, "summoned_at": now,
        "attack_at": -1, "hurt_at": -1, "death_at": -1,
        "move_at": -1, "origin": None, "target": None,
        "direction": "down", "souls": 0, "attacks": 0, "devourer": devourer,
        "soul_at": -1, "skip_turn": True, "move_pause": 0, "focus_enemy": None, "retaliation_enemy": None,
    }
    game_state.emit(GameEvent(type=GameEventType.SUMMON, actor="greater_manifestation", destination=position))
    add_log_message(game_state.combat_log, "Greater Manifestation answers the call.", category="ability")
    return True


def damage_manifestation(game_state, damage, now, *, feedback=True, attacker=None):
    spirit = game_state.player.act_three.summoner_manifestation
    if spirit is None or spirit["health"] <= 0:
        return 0
    dealt = min(spirit["health"], max(0, damage))
    spirit["health"] -= dealt
    if dealt and attacker is not None:
        spirit["retaliation_enemy"] = attacker
        spirit["move_pause"] = 0
    if dealt and feedback:
        spirit["hurt_at"] = max(now, spirit["summoned_at"] + MANIFESTATION_SUMMON_MS,
                                 spirit["attack_at"] + MANIFESTATION_ATTACK_MS,
                                 spirit["move_at"] + MANIFESTATION_MOVE_MS)
    if spirit["health"] <= 0:
        spirit["death_at"] = now
        game_state.player.summoner_true_form_charge = 0
        game_state.emit(GameEvent(type=GameEventType.DEATH, actor="greater_manifestation", destination=spirit["position"]))
        add_log_message(game_state.combat_log, "Greater Manifestation fades.", category="ability")
    return dealt


def maintain_manifestation(game_state, now):
    player, floor = game_state.player, game_state.floor
    spirit = player.act_three.summoner_manifestation
    if spirit is None:
        return
    if player.health <= 0:
        if spirit["health"] > 0:
            damage_manifestation(game_state, spirit["health"], now)
        return
    from acts.act_three.abilities.summoner_tether import SUMMONER_TELEPORT_DISTANCE, nearby_companion_cell

    hero = floor.player_column, floor.player_row
    too_far = max(abs(spirit["position"][0] - hero[0]), abs(spirit["position"][1] - hero[1])) > SUMMONER_TELEPORT_DISTANCE
    if spirit["floor"] != game_state.floor_index or (spirit["health"] > 0 and too_far):
        if spirit["health"] <= 0:
            player.act_three.summoner_manifestation = None
            return
        excluded = (player.summoner_familiar_position,) if player.summoner_familiar_active else ()
        position = nearby_companion_cell(game_state, excluded=excluded)
        if position is not None:
            spirit.update(position=position, floor=game_state.floor_index, origin=None, target=None,
                          summoned_at=now, attack_at=-1, move_at=-1, skip_turn=True)


def take_manifestation_turn(game_state):
    from systems.player_combat import attack_enemy, resolve_enemy_defeat

    player, floor = game_state.player, game_state.floor
    spirit = player.act_three.summoner_manifestation
    if not manifestation_alive(player) or player.health <= 0 or spirit["floor"] != game_state.floor_index:
        return
    if spirit["skip_turn"]:
        spirit["skip_turn"] = False
        return
    now = player.familiar_turn_started_at
    if manifestation_animation_busy(spirit, now):
        return
    origin = tuple(spirit["position"])
    from acts.act_three.abilities.summoner_follow import plan_companion_turn

    target, cells, step = plan_companion_turn(game_state, origin, spirit=True)
    destination = cells[0] if target is not None else step
    dx, dy = destination[0] - origin[0], destination[1] - origin[1]
    if dx or dy:
        spirit["direction"] = ("right" if dx > 0 else "left") if abs(dx) >= abs(dy) else ("down" if dy > 0 else "up")
    if target is not None:
        spirit["attack_at"] = now
        spirit["target"] = destination
        cost = manifestation_attack_cost(spirit)
        spirit["attacks"] += 1
        multiplier = 1 + spirit["souls"] * SOUL_DAMAGE_STEP
        defeated = attack_enemy(game_state, target,
                                ceil((player.damage_min + SUMMONER_TRUE_FORM_DAMAGE_BONUS) * multiplier),
                                ceil((player.damage_max + SUMMONER_TRUE_FORM_DAMAGE_BONUS) * multiplier),
                                0.0, attacker_position=origin, grant_ability_charge=False,
                                attacker_name="greater_manifestation")
        damage_manifestation(game_state, cost, now, feedback=False)
        if defeated:
            resolve_enemy_defeat(game_state, target)
            if spirit["devourer"]:
                spirit["souls"] += 1
                spirit["soul_at"] = now
                spirit["soul_origin"] = (target.column, target.row)
                healed = 0
                if spirit["health"] > 0:
                    healed = min(spirit["max_health"] - spirit["health"], ceil(spirit["max_health"] * SOUL_KILL_HEAL_RATIO))
                    spirit["health"] += healed
                    if healed:
                        game_state.emit(GameEvent(type=GameEventType.HEAL, actor="greater_manifestation", target="greater_manifestation",
                                                  destination=spirit["position"], amount=healed, data={"kind": "soul_devourer"}))
                add_log_message(game_state.combat_log, f"Soul Devourer: {spirit['souls']} souls; restored {healed} HP; next attack costs {manifestation_attack_cost(spirit)} HP.", category="rune")
        return
    if step != origin:
        from acts.act_three.abilities.summoner_follow import cell_distance

        hero = floor.player_column, floor.player_row
        if cell_distance(origin, hero) <= 1 and spirit.get("retaliation_enemy") is None and spirit.get("move_pause", 0) > 0:
            spirit["move_pause"] -= 1
            return
        spirit.update(origin=origin, position=step, move_at=now, target=None)
        spirit["move_pause"] = 1
