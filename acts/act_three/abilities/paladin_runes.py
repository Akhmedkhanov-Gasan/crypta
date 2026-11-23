from acts.act_three.rune_master.definitions import (
    FERVENT_CRUSADE_DAMAGE_MULTIPLIER, FERVENT_CRUSADE_HITS, TOWER_SHIELD_DAMAGE_MULTIPLIER,
    has_ability_rune,
)
from acts.act_three.settings import PALADIN_SACRED_GROUND_HITS
from game.combat_log import add_log_message


def crusade_active(player):
    return player.subclass == "paladin" and player.act_three.paladin_crusade_hits > 0


def tower_shield_active(player):
    return (player.subclass == "paladin" and has_ability_rune(player, "rune_of_tower_shield"))


def effective_dodge_chance(player):
    return 0.0 if crusade_active(player) else player.dodge_chance


def paladin_attack_multiplier(player):
    if player.subclass != "paladin":
        return 1.0
    multiplier = TOWER_SHIELD_DAMAGE_MULTIPLIER if tower_shield_active(player) else 1.0
    return multiplier * (FERVENT_CRUSADE_DAMAGE_MULTIPLIER if crusade_active(player) else 1.0)


def round_tower_damage(player, damage):
    scaled = damage + player.act_three.paladin_tower_damage_remainder
    amount = int(scaled + 1e-9)
    player.act_three.paladin_tower_damage_remainder = max(0.0, scaled - amount)
    return max(1, amount)


def consume_crusade_hit(game_state, damage):
    player = game_state.player
    if damage <= 0 or not crusade_active(player):
        return
    player.act_three.paladin_crusade_hits -= 1
    if player.act_three.paladin_crusade_hits == 0:
        add_log_message(game_state.combat_log, "Fervent Crusade fades. Guard and evasion return.", category="ability")


def paladin_ultimate_active(player):
    return player.paladin_sacred_ground_hits > 0 or player.act_three.paladin_crusade_hits > 0


def migrate_paladin_ultimate(player, floor_index=None):
    if player.paladin_sacred_ground_turns > 0 and not paladin_ultimate_active(player):
        player.paladin_sacred_ground_hits = PALADIN_SACRED_GROUND_HITS
    player.paladin_sacred_ground_turns = 0
    player.paladin_sacred_ground_hits = min(PALADIN_SACRED_GROUND_HITS, player.paladin_sacred_ground_hits)
    player.act_three.paladin_crusade_hits = min(FERVENT_CRUSADE_HITS, player.act_three.paladin_crusade_hits)
    if player.paladin_sacred_ground_hits > 0 and player.act_three.paladin_sacred_ground_floor is None:
        player.act_three.paladin_sacred_ground_floor = floor_index
