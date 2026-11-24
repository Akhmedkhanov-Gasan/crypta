from acts.act_three.abilities.summoner_runes import summon_cell_is_free
from acts.act_three.abilities.summoner_targeting import adjacent_direction_target
from game.combat_log import add_log_message
from logic import can_player_move_between


def manifestation_targets(game_state):
    player, floor = game_state.player, game_state.floor
    origin = floor.player_column, floor.player_row
    familiar = tuple(player.summoner_familiar_position) if player.summoner_familiar_active and player.summoner_familiar_position is not None else None
    return tuple((origin[0] + dx, origin[1] + dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                 if (dx or dy) and (origin[0] + dx, origin[1] + dy) != familiar
                 and summon_cell_is_free(game_state, (origin[0] + dx, origin[1] + dy))
                 and can_player_move_between(floor.map, *origin, origin[0] + dx, origin[1] + dy, floor.barriers))


def select_manifestation_target(game_state, target):
    state = game_state.player.act_three
    if not state.summoner_manifestation_aiming or target is None:
        return False
    state.summoner_manifestation_target = adjacent_direction_target(game_state, target)
    return state.summoner_manifestation_target in manifestation_targets(game_state)


def cancel_manifestation_targeting(player):
    player.act_three.summoner_manifestation_aiming = False
    player.act_three.summoner_manifestation_target = None


def begin_manifestation_targeting(game_state):
    player, floor = game_state.player, game_state.floor
    targets = manifestation_targets(game_state)
    if not targets:
        add_log_message(game_state.combat_log, "There is no free neighboring cell for Greater Manifestation.", category="warning")
        return False
    player.summoner_familiar_summon_aiming = False
    player.summoner_familiar_summon_target = None
    player.summoner_aiming = False
    player.summoner_aim_target = None
    player.act_three.summoner_manifestation_aiming = True
    facing = floor.player_column + player.facing_direction[0], floor.player_row + player.facing_direction[1]
    player.act_three.summoner_manifestation_target = facing if facing in targets else targets[0]
    add_log_message(game_state.combat_log, "Choose a neighboring cell. F or a click summons the greater spirit; Escape cancels.", category="ability")
    return True
