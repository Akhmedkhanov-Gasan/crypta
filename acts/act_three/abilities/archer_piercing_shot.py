from acts.act_three.abilities.progression import (
    clear_ability_slot_charge,
    is_ability_slot_charged,
)
from acts.act_three.combat.attacks import (
    is_valid_archer_attack_target,
)
from acts.act_three.events import GameEvent, GameEventType
from acts.act_three.combat.stun import (
    apply_act_three_enemy_stun,
)
from game.combat_log import add_log_message
from logic import get_enemy_occupied_positions, has_line_of_sight
from systems.player_combat import attack_enemy, resolve_enemy_defeat


PIERCING_DAMAGE_MIN = 3
PIERCING_DAMAGE_MAX = 5
PIERCING_STUN_TURNS = 2
PIERCING_PATH_CELLS = 6


def piercing_shot_ready(game_state):
    return is_ability_slot_charged(game_state.player, "q")


def piercing_shot_cells(game_state, target):
    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    if dx == 0 and dy == 0:
        return []

    end = (
        origin[0] + dx * PIERCING_PATH_CELLS,
        origin[1] + dy * PIERCING_PATH_CELLS,
    )
    x, y = origin
    distance_x = abs(end[0] - x)
    distance_y = abs(end[1] - y)
    step_x = 1 if end[0] > x else -1
    step_y = 1 if end[1] > y else -1
    error = distance_x - distance_y
    cells = []

    while len(cells) < PIERCING_PATH_CELLS:
        doubled_error = error * 2
        if doubled_error > -distance_y:
            error -= distance_y
            x += step_x
        if doubled_error < distance_x:
            error += distance_x
            y += step_y

        if not (
            0 <= y < len(floor.map)
            and 0 <= x < len(floor.map[y])
        ):
            break

        if not has_line_of_sight(
            floor.map,
            *origin,
            x,
            y,
        ):
            break

        cells.append((x, y))

    return cells


def perform_archer_piercing_shot(
    game_state,
    target,
    current_time,
    oracle_hit_reaction,
):
    player = game_state.player
    floor = game_state.floor

    if (
        not piercing_shot_ready(game_state)
        or not is_valid_archer_attack_target(game_state, target)
    ):
        return False

    cells = piercing_shot_cells(game_state, target)
    if target not in cells:
        return False

    origin = (floor.player_column, floor.player_row)
    hit_enemies = []
    seen = set()

    for cell in cells:
        for enemy in floor.enemies:
            if (
                enemy.health <= 0
                or id(enemy) in seen
                or cell not in get_enemy_occupied_positions(enemy)
            ):
                continue
            seen.add(id(enemy))
            hit_enemies.append(enemy)

    if not hit_enemies:
        return False

    clear_ability_slot_charge(player, "q")
    player.archer_piercing_effect_target = cells[-1]
    player.archer_piercing_effect_started_at = current_time

    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=origin,
            positions=tuple(cells),
            data={"kind": "archer_piercing_shot"},
        )
    )
    shot_from_invisibility = player.invisibility_turns > 0

    for index, enemy in enumerate(hit_enemies):
        defeated = attack_enemy(
            game_state,
            enemy,
            PIERCING_DAMAGE_MIN,
            PIERCING_DAMAGE_MAX,
            player.crit_chance,
            force_critical=shot_from_invisibility,
            attacker_position=origin,
            grant_ability_charge=False,
            suppress_veil_retrigger=shot_from_invisibility,
        )
        if enemy.type == "oracle":
            oracle_hit_reaction(
                enemy,
                floor,
                game_state.combat_log,
            )
        if defeated:
            resolve_enemy_defeat(game_state, enemy)
            continue

        if index == 0:
            apply_act_three_enemy_stun(
                game_state,
                enemy,
                PIERCING_STUN_TURNS,
                current_time,
            )
            add_log_message(
                game_state.combat_log,
                f"{enemy.name} is stunned by Piercing Shot.",
                category="debuff",
            )

    return True
