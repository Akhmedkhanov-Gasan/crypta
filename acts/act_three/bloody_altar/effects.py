from math import ceil
import random

from acts.act_three.bloody_altar.catalog import has_pact


def critical_multiplier(player):
    return player.critical_damage_multiplier + (0.75 if has_pact(player, "exposed_heart") else 0)


def outgoing_multiplier(player, target, floor=None, *, basic=False):
    identifier = player.act_three.altar_pact_id
    if target is None and identifier in ("final_word", "lone_prey", "feast_of_many"):
        return 1.0
    if identifier == "black_tribute":
        return 2.0
    if identifier == "splintered_heart":
        return 1.75
    if identifier == "final_word":
        return 1.6 if target.health * 2 <= target.max_health else 0.7
    if identifier == "insatiable_edge" and basic:
        return 1 + player.act_three.altar_attack_chain * 0.15
    if identifier in ("lone_prey", "feast_of_many") and floor is not None:
        from logic import get_enemy_occupied_positions

        target_cells = get_enemy_occupied_positions(target)
        grouped = any(other is not target and other.health > 0 and not other.possessed_by_summoner
                      and any(max(abs(a[0] - b[0]), abs(a[1] - b[1])) <= 5
                              for a in target_cells for b in get_enemy_occupied_positions(other))
                      for other in floor.enemies)
        favored = grouped if identifier == "feast_of_many" else not grouped
        return 1.4 if favored else 0.75
    return 1.0


def begin_basic_attack(player):
    player.act_three.altar_basic_action = True
    if has_pact(player, "insatiable_edge"):
        player.act_three.altar_attack_chain = min(4, player.act_three.altar_attack_chain + 1)


def basic_attack_failed(player):
    player.act_three.altar_attack_chain = 0


def finish_player_action(player):
    if not player.act_three.altar_basic_action:
        player.act_three.altar_attack_chain = 0
    player.act_three.altar_basic_action = False


def adjusted_healing(player, amount, source=None):
    identifier = player.act_three.altar_pact_id
    if identifier == "endless_hunger" and source != "lifesteal":
        return 0
    ratio = 1.0
    if identifier == "insatiable_edge":
        ratio = 0.6
    elif identifier == "crimson_rupture":
        ratio = 0.4
    elif identifier == "deaths_reprieve" and not player.act_three.reprieve_ready:
        ratio = 0.5
    if ratio == 1 or amount <= 0:
        return max(0, amount)
    if player.health >= player.max_health:
        player.act_three.altar_healing_progress = 0.0
        return 0
    total = player.act_three.altar_healing_progress + amount * ratio
    whole = int(total + 1e-9)
    player.act_three.altar_healing_progress = max(0.0, total - whole)
    return whole


def incoming_attack_damage(player, damage):
    if damage <= 0:
        return 0
    multiplier = 1.0
    if has_pact(player, "blood_carapace"):
        multiplier *= 0.65
    elif has_pact(player, "endless_hunger"):
        multiplier *= 1.5
    elif has_pact(player, "exposed_heart") and random.random() < 0.2:
        multiplier *= 2
    return max(1, ceil(damage * multiplier))


def prevent_death(game_state):
    player = game_state.player
    if player.health > 0 or not has_pact(player, "deaths_reprieve") or not player.act_three.reprieve_ready:
        return False
    from acts.act_three.abilities.charges import ability_is_passive, fill_ability_slot
    from acts.act_three.abilities.progression import is_ability_slot_unlocked
    from acts.act_three.combat.stun import apply_act_three_enemy_stun
    from game.combat_log import add_log_message
    from game.events import GameEvent, GameEventType
    from logic import get_enemy_occupied_positions
    import pygame

    player.health = 1
    player.act_three.reprieve_ready = False
    player.act_three.reprieve_kills = 0
    for slot in ("q", "e", "f"):
        if is_ability_slot_unlocked(player, slot) and not ability_is_passive(player, slot):
            fill_ability_slot(player, slot)
    origin = game_state.floor.player_column, game_state.floor.player_row
    for enemy in game_state.floor.enemies:
        if enemy.health > 0 and not enemy.possessed_by_summoner and any(
            max(abs(cell[0] - origin[0]), abs(cell[1] - origin[1])) <= 1
            for cell in get_enemy_occupied_positions(enemy)
        ):
            apply_act_three_enemy_stun(game_state, enemy, 1, pygame.time.get_ticks())
    game_state.emit(GameEvent(type=GameEventType.ABILITY, actor="hero", origin=origin,
                              data={"kind": "deaths_reprieve"}))
    add_log_message(game_state.combat_log, "Death's Reprieve saves you. Slay 15 original foes to restore it.", category="altar")
    return True


def record_original_kill(game_state, enemy):
    player = game_state.player
    if (not has_pact(player, "deaths_reprieve") or player.act_three.reprieve_ready
            or enemy.is_summoned or not enemy.altar_original_enemy):
        return
    player.act_three.reprieve_kills += 1
    if player.act_three.reprieve_kills >= 15:
        from game.combat_log import add_log_message

        player.act_three.reprieve_ready = True
        player.act_three.reprieve_kills = 0
        player.act_three.altar_healing_progress = 0.0
        add_log_message(game_state.combat_log, "Death's Reprieve is ready. Its healing penalty is lifted.", category="altar")


def on_hero_damage(game_state, enemy, damage):
    if damage <= 0:
        return
    player = game_state.player
    if has_pact(player, "crimson_rupture") and enemy.health > 0:
        from systems.bleeding import apply_bleed

        apply_bleed(enemy, max(1, ceil(damage * 0.2)), 3)
    if has_pact(player, "endless_hunger") and player.health < player.max_health:
        from game.healing import heal_player
        from game.events import GameEvent, GameEventType

        total = player.act_three.altar_lifesteal_progress + damage * 0.4
        whole = int(total + 1e-9)
        player.act_three.altar_lifesteal_progress = max(0.0, total - whole)
        healed = heal_player(player, whole, source="lifesteal")
        if healed:
            game_state.emit(GameEvent(type=GameEventType.HEAL, actor="hero", target="hero", amount=healed,
                                      data={"kind": "endless_hunger"}))
        if player.health >= player.max_health:
            player.act_three.altar_lifesteal_progress = 0.0


def pay_seal_cost(game_state):
    player = game_state.player
    if not has_pact(player, "shattered_seal"):
        return True
    from game.events import GameEvent, GameEventType

    cost = max(1, ceil(player.max_health * 0.05))
    player.health = max(0, player.health - cost)
    game_state.emit(GameEvent(type=GameEventType.ABILITY, actor="hero", target="hero", amount=cost,
                              data={"kind": "shattered_seal_cost"}))
    prevent_death(game_state)
    return player.health > 0
