from acts.act_three.abilities.progression import (
    clear_ability_slot_charge,
    is_ability_slot_charged,
)
from acts.act_three.combat.archer_aim import (
    archer_shot_direction,
    cancel_archer_aim,
)
from acts.act_three.events import GameEvent, GameEventType
from game.combat_log import add_log_message
from game.state import ArcherBarrageShotState
from logic import can_move_to, get_enemy_occupied_positions
from systems.player_combat import attack_enemy, resolve_enemy_defeat


BARRAGE_DAMAGE_MIN = 3
BARRAGE_DAMAGE_MAX = 5


class ArcherBarrageTurnInterrupt(Exception):
    pass

def get_archer_barrage_zone_cells(game_state, anchor):
    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    if anchor is None or anchor == origin:
        return []

    direction = archer_shot_direction(origin, anchor)
    dx, dy = direction
    center_x = origin[0] + dx
    center_y = origin[1] + dy

    if dx:
        cells = [
            (center_x, center_y - 1),
            (center_x, center_y),
            (center_x, center_y + 1),
        ]
    else:
        cells = [
            (center_x - 1, center_y),
            (center_x, center_y),
            (center_x + 1, center_y),
        ]

    return [
        (column, row)
        for column, row in cells
        if 0 <= row < len(floor.map)
        and 0 <= column < len(floor.map[row])
        and can_move_to(floor.map, column, row)
    ]


def is_valid_archer_barrage_zone_anchor(game_state, anchor):
    player = game_state.player
    if player.subclass != "archer" or not player.archer_barrage_zone_aiming:
        return False

    cells = get_archer_barrage_zone_cells(game_state, anchor)
    return bool(cells) and tuple(cells) not in player.archer_barrage_zones


def request_archer_barrage_zone(game_state):
    player = game_state.player
    if player.subclass != "archer" or player.health <= 0:
        return False

    if player.archer_barrage_zone_aiming:
        cancel_archer_barrage_zone(game_state)
        return True

    if not is_ability_slot_charged(player, "f"):
        add_log_message(
            game_state.combat_log,
            "Barrage Zone is not charged.",
        )
        return True

    cancel_archer_aim(game_state)
    player.archer_empowered_shot_aiming = False
    player.archer_empowered_shot_target = None
    player.archer_leap_aiming = False
    player.archer_leap_target = None
    player.archer_barrage_zone_aiming = True
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Choose a direction for Barrage Zone.",
    )
    return True


def cancel_archer_barrage_zone(game_state):
    player = game_state.player
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Barrage Zone aiming cancelled.",
    )


def update_archer_barrage_zone_preview(game_state, anchor):
    player = game_state.player
    if not is_valid_archer_barrage_zone_anchor(game_state, anchor):
        player.archer_barrage_zone_anchor = None
        player.archer_barrage_zone_preview_cells.clear()
        return False

    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    dx, dy = archer_shot_direction(origin, anchor)
    player.archer_barrage_zone_anchor = (
        origin[0] + dx,
        origin[1] + dy,
    )
    player.archer_barrage_zone_preview_cells = (
        get_archer_barrage_zone_cells(
            game_state,
            player.archer_barrage_zone_anchor,
        )
    )
    return True


def select_archer_barrage_zone_direction(game_state, direction):
    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    if direction == (0, 0):
        return False

    dx, dy = archer_shot_direction(
        (0, 0),
        direction,
    )
    return update_archer_barrage_zone_preview(
        game_state,
        (origin[0] + dx, origin[1] + dy),
    )


def _fire_archer_barrage_zone(game_state, cells, turn_id):
    player = game_state.player
    floor = game_state.floor
    zone = set(cells)
    targets = [
        enemy
        for enemy in tuple(floor.enemies)
        if enemy.health > 0
        and zone & set(get_enemy_occupied_positions(enemy))
        and player.archer_barrage_hit_turns.get(id(enemy)) != turn_id
    ]
    if not targets:
        return False

    direction = player.archer_barrage_directions.pop(
        cells,
        (1, 0),
    )
    player.archer_barrage_zones.remove(cells)
    player.archer_barrage_zone_cells = list(
        dict.fromkeys(
            cell
            for active_zone in player.archer_barrage_zones
            for cell in active_zone
        )
    )

    for enemy in targets:
        player.archer_barrage_hit_turns[id(enemy)] = turn_id
        target = (enemy.column, enemy.row)
        origin = min(
            cells,
            key=lambda cell: (
                abs(cell[0] - target[0])
                + abs(cell[1] - target[1])
            ),
        )
        player.archer_barrage_shots.append(
            ArcherBarrageShotState(
                origin=origin,
                target=target,
                direction=direction,
            )
        )
        player.archer_barrage_pending_hits.append(
            (id(enemy), origin, target)
        )

    add_log_message(
        game_state.combat_log,
        "Phantom archers unleash a barrage.",
        category="ability",
    )
    return True


def resolve_archer_barrage_hits(game_state):
    player = game_state.player
    floor = game_state.floor
    pending_hits = tuple(player.archer_barrage_pending_hits)
    player.archer_barrage_pending_hits.clear()

    for enemy_id, origin, target in pending_hits:
        enemy = next(
            (
                candidate
                for candidate in floor.enemies
                if id(candidate) == enemy_id
                and candidate.health > 0
            ),
            None,
        )
        if enemy is None:
            continue

        game_state.emit(
            GameEvent(
                type=GameEventType.ATTACK,
                actor="hero",
                target=enemy.name,
                origin=origin,
                positions=(target,),
                data={"kind": "archer_barrage_zone"},
            )
        )
        defeated = attack_enemy(
            game_state,
            enemy,
            BARRAGE_DAMAGE_MIN,
            BARRAGE_DAMAGE_MAX,
            player.crit_chance,
            attacker_position=origin,
            grant_ability_charge=False,
        )
        if enemy.type == "oracle":
            from acts.act_two.enemies.oracle.behavior import resolve_oracle_hit_reaction

            resolve_oracle_hit_reaction(
                enemy,
                floor,
                game_state.combat_log,
            )
        if defeated:
            resolve_enemy_defeat(game_state, enemy)


def place_archer_barrage_zone(game_state):
    player = game_state.player
    if (
        not player.archer_barrage_zone_aiming
        or player.archer_barrage_zone_anchor is None
        or not player.archer_barrage_zone_preview_cells
        or not is_ability_slot_charged(player, "f")
    ):
        return False

    cells = tuple(player.archer_barrage_zone_preview_cells)
    if cells in player.archer_barrage_zones:
        return False

    direction = archer_shot_direction(
        (
            game_state.floor.player_column,
            game_state.floor.player_row,
        ),
        player.archer_barrage_zone_anchor,
    )
    clear_ability_slot_charge(player, "f")
    player.archer_barrage_zones.append(cells)
    player.archer_barrage_directions[cells] = direction
    player.archer_barrage_zone_cells = list(
        dict.fromkeys(
            (
                *player.archer_barrage_zone_cells,
                *cells,
            )
        )
    )
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()

    game_state.emit(
        GameEvent(
            type=GameEventType.ABILITY,
            actor="hero",
            positions=cells,
            data={"ability": "barrage_zone"},
        )
    )
    add_log_message(
        game_state.combat_log,
        "Barrage Zone is deployed.",
        category="ability",
    )
    _fire_archer_barrage_zone(
        game_state,
        cells,
        game_state.run_stats.turns_taken + 1,
    )
    return True


def resolve_archer_barrage_zone_entry(
    game_state,
    enemy,
    previous_position,
):
    player = game_state.player
    if (
        player.subclass != "archer"
        or enemy.health <= 0
        or not player.archer_barrage_zones
    ):
        return False

    current_cells = set(get_enemy_occupied_positions(enemy))
    dx = enemy.column - previous_position[0]
    dy = enemy.row - previous_position[1]
    previous_cells = {
        (column - dx, row - dy)
        for column, row in current_cells
    }

    fired = False
    for cells in tuple(player.archer_barrage_zones):
        zone = set(cells)
        if current_cells & zone and not previous_cells & zone:
            fired = (
                _fire_archer_barrage_zone(
                    game_state,
                    cells,
                    game_state.run_stats.turns_taken,
                )
                or fired
            )
    if fired:
        raise ArcherBarrageTurnInterrupt
    return False
