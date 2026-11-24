import math

import pygame

from acts.act_three.abilities.summoner_runes import nearest_summon_cell, summon_cell_is_free
from game.combat_log import add_log_message
from acts.act_three.settings import SUMMONER_FAMILIAR_CHARGES


def adjacent_direction_target(game_state, target):
    origin = game_state.floor.player_column, game_state.floor.player_row
    dx, dy = target[0] - origin[0], target[1] - origin[1]
    if dx == dy == 0:
        dx, dy = game_state.player.facing_direction
    angle = round(math.atan2(dy, dx) / (math.pi / 4))
    return origin[0] + round(math.cos(angle * math.pi / 4)), origin[1] + round(math.sin(angle * math.pi / 4))


def totem_blocks_cell(player, target):
    spirit = player.act_three.summoner_manifestation
    if spirit is not None and spirit["health"] > 0 and tuple(spirit["position"]) == target:
        return True
    return (player.subclass == "summoner" and player.summoner_familiar_active
            and not player.summoner_true_form_active and player.act_three.summoner_familiar_mode == "totem"
            and player.summoner_familiar_position == target)


def record_familiar_recall(game_state, now=None):
    player = game_state.player
    state = player.act_three
    state.summoner_recall_position = player.summoner_familiar_position
    state.summoner_recall_started_at = pygame.time.get_ticks() if now is None else now
    state.summoner_recall_floor = game_state.floor_index
    state.summoner_recall_totem = state.summoner_familiar_mode == "totem" and not player.summoner_true_form_active


def bind_totem(game_state, now=None):
    player = game_state.player
    state = player.act_three
    now = pygame.time.get_ticks() if now is None else now
    if state.summoner_suspended_familiar is not None:
        saved = state.summoner_suspended_familiar
        saved["mode"] = "totem"
        saved["anchor"] = saved["position"]
        return
    if not player.summoner_familiar_active or player.summoner_true_form_active:
        return
    if state.summoner_possession_host is not None:
        from acts.act_three.abilities.summoner_possession import release_host

        release_host(game_state)
    origin = player.summoner_familiar_position
    position = origin if summon_cell_is_free(game_state, origin) else nearest_summon_cell(game_state, origin)
    if position is None:
        player.summoner_familiar_active = False
        player.summoner_familiar_position = None
        player.summoner_familiar_charge = SUMMONER_FAMILIAR_CHARGES
        return
    state.summoner_familiar_mode = "totem"
    state.summoner_totem_anchor = position
    state.summoner_entity_floor = game_state.floor_index
    player.summoner_familiar_position = position
    player.summoner_familiar_movement_origin = None
    player.summoner_familiar_attack_started_at = 0
    player.summoner_familiar_attack_target = None
    player.summoner_familiar_summoned_at = now
    state.summoner_rune_started_at = now
    add_log_message(game_state.combat_log, "The familiar takes the shape of a Spirit Totem.", category="rune")
