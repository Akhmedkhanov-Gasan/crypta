from acts.act_three.abilities.summoner_runes import summon_cell_is_free
from logic import get_enemy_occupied_positions


SUMMONER_TELEPORT_DISTANCE = 6


def nearby_companion_cell(game_state, host=None, excluded=()):
    floor = game_state.floor
    hero = floor.player_column, floor.player_row
    width = host.footprint_width if host is not None else 1
    height = host.footprint_height if host is not None else 1
    candidates = [(hero[0] + dx, hero[1] + dy) for dy in range(-3, 4) for dx in range(-3, 4)]
    candidates.sort(key=lambda cell: (max(abs(cell[0] - hero[0]), abs(cell[1] - hero[1])), cell[1], cell[0]))
    return next((cell for cell in candidates
                 if all((cell[0] + dx, cell[1] + dy) not in excluded
                        and summon_cell_is_free(game_state, (cell[0] + dx, cell[1] + dy), ignore_enemy=host)
                        for dy in range(height) for dx in range(width))), None)


def maintain_familiar_tether(game_state, now):
    player, floor = game_state.player, game_state.floor
    state = player.act_three
    if not player.summoner_familiar_active or player.summoner_familiar_health <= 0 or player.health <= 0:
        return
    if state.summoner_familiar_mode == "totem":
        return
    hero = floor.player_column, floor.player_row
    from acts.act_three.abilities.summoner_possession import possession_host, sync_host

    host = possession_host(game_state)
    position = player.summoner_familiar_position
    if position is None:
        return
    cells = get_enemy_occupied_positions(host) if host is not None else (position,)
    if min(max(abs(cell[0] - hero[0]), abs(cell[1] - hero[1])) for cell in cells) <= SUMMONER_TELEPORT_DISTANCE:
        return
    destination = nearby_companion_cell(game_state, host)
    if destination is None:
        return
    if host is not None:
        host.column, host.row = destination
        host.movement_origin = None
        host.attack_targets.clear()
        host.prepared_attack_mode = None
        host.attack_windup_turns_remaining = 0
        host.heal_target = None
        sync_host(game_state, host)
    else:
        player.summoner_familiar_position = destination
        player.summoner_familiar_summoned_at = now
    player.summoner_familiar_movement_origin = None
    player.summoner_familiar_attack_target = None
    player.summoner_familiar_attack_started_at = -1
    player.summoner_familiar_skip_turn = True
