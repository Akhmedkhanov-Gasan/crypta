from acts.act_three.rune_master.definitions import (
    ABSORPTION_DAMAGE_MULTIPLIER, FAMILIAR_DEATH_CHARGES, has_ability_rune,
)
from acts.act_three.settings import SUMMONER_FAMILIAR_CHARGES
from logic import can_move_to, get_enemy_occupied_positions, has_line_of_sight


def absorption_active(player):
    return (player.subclass == "summoner" and (player.act_three.summoner_absorption_attacks > 0
            or player.act_three.summoner_absorption_attack_active))


def familiar_is_away(player):
    return player.summoner_familiar_active or absorption_active(player)


def familiar_recharge_requirement(player):
    return player.act_three.summoner_recall_requirement or SUMMONER_FAMILIAR_CHARGES


def familiar_rune_mode(player):
    if has_ability_rune(player, "rune_of_spirit_totem"):
        return "totem"
    if has_ability_rune(player, "rune_of_possession"):
        return "possession"
    return "familiar"


def summon_cell_is_free(game_state, cell):
    from acts.act_three.npcs import get_npc_at

    floor = game_state.floor
    if (cell == (floor.player_column, floor.player_row) or not can_move_to(floor.map, *cell)
            or cell == (floor.stairs_column, floor.stairs_row)):
        return False
    if any(enemy.health > 0 and cell in get_enemy_occupied_positions(enemy) for enemy in floor.enemies):
        return False
    if any(not chest.is_open and cell == (chest.column, chest.row) for chest in floor.chests):
        return False
    if any(not crate.is_broken and cell == (crate.column, crate.row) for crate in floor.breakable_crates):
        return False
    if any(ore.get("stage", 0) < 3 and cell == ore["position"] for ore in getattr(floor, "act_three_ores", [])):
        return False
    return get_npc_at(floor, cell) is None


def nearest_summon_cell(game_state, origin):
    floor = game_state.floor
    candidates = [(origin[0] + dx, origin[1] + dy) for dy in range(-3, 4) for dx in range(-3, 4)]
    candidates.sort(key=lambda cell: (max(abs(cell[0] - origin[0]), abs(cell[1] - origin[1])), cell[1], cell[0]))
    return next((cell for cell in candidates if summon_cell_is_free(game_state, cell)
                 and has_line_of_sight(floor.map, *origin, *cell, floor.barriers)), None)


def familiar_lost(player, penalty_multiplier=1):
    player.act_three.summoner_recall_requirement = FAMILIAR_DEATH_CHARGES * penalty_multiplier
    player.act_three.summoner_possession_host = None
    player.act_three.summoner_possession_turns = 0
    player.act_three.summoner_suspended_familiar = None
    player.summoner_familiar_charge = 0


def begin_summoner_attack(game_state):
    player = game_state.player
    if player.subclass != "summoner":
        return
    player.act_three.summoner_absorption_attack_active = player.act_three.summoner_absorption_attacks > 0
    if player.act_three.summoner_absorption_attack_active:
        player.act_three.summoner_absorption_attacks -= 1


def finish_summoner_attack(game_state):
    player = game_state.player
    if player.subclass != "summoner" or not player.act_three.summoner_absorption_attack_active:
        return
    player.act_three.summoner_absorption_attack_active = False
    if player.act_three.summoner_absorption_attacks == 0:
        from acts.act_three.abilities.summoner_ultimate import restore_familiar

        restore_familiar(game_state)


def absorption_damage_multiplier(player):
    return ABSORPTION_DAMAGE_MULTIPLIER if absorption_active(player) else 1.0
