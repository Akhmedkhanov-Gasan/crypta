import pygame

from acts.act_three.items.inventory import (
    BLACK_ORE_CHUNK,
    inventory_has_space,
    store_inventory_item,
)
from acts.act_three.mining.world import clear_ore_collision, get_ore_at
from game.combat_log import add_log_message
from systems.grid_geometry import can_reach_adjacent_cell


MINING_FRAME_MS = 160
MINING_FRAME_SEQUENCE = (0, 1, 2, 3, 4, 5, 6, 7, 1, 0)
MINING_IMPACT_MS = MINING_FRAME_MS * 7
MINING_DURATION_MS = MINING_FRAME_MS * len(MINING_FRAME_SEQUENCE)
MINING_RETURN_MS = MINING_FRAME_MS * 2
MINING_EFFECT_MS = 600
MINING_REWARD_MS = 1400


def start_mining(game_state, target, current_time):
    player = game_state.player
    floor = game_state.floor
    ore = get_ore_at(floor, target)
    origin = (floor.player_column, floor.player_row)

    if (
        floor.presentation_act != 3
        or player.subclass not in ("assassin", "archer", "berserker")
        or player.health <= 0
        or player.stun_turns > 0
        or game_state.game_won
        or player.act_three.mining is not None
        or game_state.act_three.npc_dialog_position is not None
        or ore is None
        or ore["stage"] >= 3
        or target not in floor.visible_cells
    ):
        return False

    if not can_reach_adjacent_cell(
        floor.map,
        origin,
        target,
        floor.barriers,
        target_must_be_walkable=False,
    ):
        return False

    if ore["stage"] == 2 and not inventory_has_space(player):
        add_log_message(
            game_state.combat_log,
            "The inventory is full. Make room for Black ore.",
            category="warning",
        )
        return False

    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    direction = (
        "right"
        if dx > 0 or (dx == 0 and dy > 0)
        else "left"
    )
    player.act_three.mining = {
        "floor_index": game_state.floor_index,
        "origin": origin,
        "target": target,
        "direction": direction,
        "started_at": current_time,
        "ending_at": None,
        "initial_stage": ore["stage"],
        "hits": 0,
    }
    player.facing_direction = (
        (1, 0) if direction == "right" else (-1, 0)
    )
    player.movement_origin = None
    player.movement_animation_started_at = 0
    player.attack_animation_started_at = 0
    return True


def handle_mining_event(event, game_state):
    mining = game_state.player.act_three.mining
    if mining is None:
        return False

    if (
        event.type == pygame.KEYDOWN
        and event.key == pygame.K_ESCAPE
        and mining["ending_at"] is None
    ):
        mining["ending_at"] = pygame.time.get_ticks()

    return True


def advance_mining(game_state, current_time):
    session = game_state.act_three
    player = game_state.player
    for ore in game_state.floor.act_three_ores:
        if ore["stage"] == 3:
            clear_ore_collision(game_state.floor, ore["position"])
    session.mining_effects[:] = [
        effect
        for effect in session.mining_effects
        if (
            effect["floor_index"] == game_state.floor_index
            and 0 <= current_time - effect["started_at"]
            < MINING_EFFECT_MS
        )
    ]

    reward = session.mining_reward
    if reward is not None and (
        reward["floor_index"] != game_state.floor_index
        or current_time - reward["started_at"] >= MINING_REWARD_MS
    ):
        session.mining_reward = None

    mining = player.act_three.mining
    if mining is None:
        return

    if (
        mining["floor_index"] != game_state.floor_index
        or mining["origin"]
        != (game_state.floor.player_column, game_state.floor.player_row)
        or player.health <= 0
        or game_state.game_won
    ):
        player.act_three.mining = None
        return

    if mining["ending_at"] is not None:
        if current_time - mining["ending_at"] >= MINING_RETURN_MS:
            player.act_three.mining = None
        return

    ore = get_ore_at(game_state.floor, mining["target"])
    if (
        ore is None
        or ore["stage"] != mining["initial_stage"] + mining["hits"]
    ):
        player.act_three.mining = None
        return

    elapsed = max(0, current_time - mining["started_at"])

    if mining["hits"] == 0 and elapsed >= MINING_IMPACT_MS:
        if ore["stage"] == 2 and not store_inventory_item(player, BLACK_ORE_CHUNK):
            add_log_message(
                game_state.combat_log,
                "The inventory is full. Make room for Black ore.",
                category="warning",
            )
            mining["ending_at"] = current_time
            return

        mining["hits"] = 1
        ore["stage"] += 1
        session.mining_effects.append(
            {
                "floor_index": game_state.floor_index,
                "position": mining["target"],
                "started_at": mining["started_at"] + MINING_IMPACT_MS,
                "seed": ore["stage"],
            }
        )

        if ore["stage"] == 3:
            clear_ore_collision(game_state.floor, ore["position"])
            session.mining_reward = {
                "floor_index": game_state.floor_index,
                "position": mining["origin"],
                "started_at": current_time,
            }
            add_log_message(
                game_state.combat_log,
                "Mined 1 Black ore.",
                category="loot",
            )

    if elapsed >= MINING_DURATION_MS:
        player.act_three.mining = None


def mining_frame(player, current_time):
    mining = player.act_three.mining
    if mining is None:
        return None

    elapsed = max(0, current_time - mining["started_at"])
    if mining["ending_at"] is not None:
        return_elapsed = max(0, current_time - mining["ending_at"])
        index = 8 + min(1, return_elapsed // MINING_FRAME_MS)
    else:
        index = min(
            len(MINING_FRAME_SEQUENCE) - 1,
            elapsed // MINING_FRAME_MS,
        )

    return mining["direction"], MINING_FRAME_SEQUENCE[index]
