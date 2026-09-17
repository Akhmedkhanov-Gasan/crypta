from __future__ import annotations

import random

from enemies import ENEMY_TYPES

from acts.act_three.settings import (
    ACT_THREE_ENCOUNTER_SETTINGS,
)


def _position_inside_zone(position, zone):
    column, row = position

    return (
        zone["left"] <= column < zone["right"]
        and zone["top"] <= row < zone["bottom"]
    )


def _reserved_positions(floor):
    positions = {
        floor["player_start"],
        floor["stairs"],
    }

    positions.update(
        enemy["position"]
        for enemy in floor["enemies"]
    )
    positions.update(
        chest["position"]
        for chest in floor["chests"]
    )
    positions.update(floor["potions"])

    for passage in floor.get("passages", []):
        positions.add(passage["wall_position"])
        positions.add(passage["trigger_position"])

    return {
        position
        for position in positions
        if position is not None
    }


def _zone_limit(zone, name, fallback):
    value = zone.get(name)

    if value is None:
        return fallback

    return value


def _enemy_pool(zone, settings):
    zone_types = zone.get("enemy_types", ())
    configured_weights = settings["enemy_weights"]
    enemy_types = (
        zone_types
        if zone_types
        else tuple(configured_weights)
    )
    enemy_types = tuple(
        enemy_type
        for enemy_type in enemy_types
        if enemy_type in ENEMY_TYPES
    )
    weights = tuple(
        configured_weights.get(enemy_type, 1)
        for enemy_type in enemy_types
    )

    return enemy_types, weights


def _candidate_positions(
    floor,
    zone,
    occupied_positions,
    enemy_positions,
    minimum_spacing,
    minimum_player_distance,
):
    candidates = []
    dungeon_map = floor["map"]
    map_height = len(dungeon_map)
    map_width = len(dungeon_map[0])
    player_column, player_row = floor["player_start"]

    for row in range(
        max(0, zone["top"]),
        min(map_height, zone["bottom"]),
    ):
        for column in range(
            max(0, zone["left"]),
            min(map_width, zone["right"]),
        ):
            position = (column, row)

            if dungeon_map[row][column] != ".":
                continue

            if position in occupied_positions:
                continue

            if (
                abs(column - player_column)
                + abs(row - player_row)
                < minimum_player_distance
            ):
                continue

            if any(
                abs(column - enemy_column)
                + abs(row - enemy_row)
                < minimum_spacing
                for enemy_column, enemy_row in enemy_positions
            ):
                continue

            candidates.append(position)

    random.shuffle(candidates)
    return candidates


def populate_act_three_enemies(
    floor,
    act_floor,
):
    settings = ACT_THREE_ENCOUNTER_SETTINGS.get(
        act_floor
    )

    if not settings or not settings["enabled"]:
        return floor

    occupied_positions = _reserved_positions(floor)
    enemy_positions = {
        enemy["position"]
        for enemy in floor["enemies"]
    }

    for zone in floor.get("encounter_zones", []):
        enemy_types, weights = _enemy_pool(
            zone,
            settings,
        )

        if not enemy_types:
            continue

        minimum = max(
            0,
            _zone_limit(
                zone,
                "min_enemies",
                settings["min_enemies"],
            ),
        )
        maximum = max(
            minimum,
            _zone_limit(
                zone,
                "max_enemies",
                settings["max_enemies"],
            ),
        )
        target_count = random.randint(
            minimum,
            maximum,
        )
        existing_count = sum(
            _position_inside_zone(
                enemy["position"],
                zone,
            )
            for enemy in floor["enemies"]
        )
        required_count = max(
            0,
            target_count - existing_count,
        )

        for _ in range(required_count):
            candidates = _candidate_positions(
                floor,
                zone,
                occupied_positions,
                enemy_positions,
                settings["minimum_spacing"],
                settings["minimum_player_distance"],
            )

            if not candidates:
                break

            position = candidates[0]
            enemy_type = random.choices(
                enemy_types,
                weights=weights,
                k=1,
            )[0]

            floor["enemies"].append(
                {
                    "position": position,
                    "type": enemy_type,
                    "boss_group": False,
                }
            )
            occupied_positions.add(position)
            enemy_positions.add(position)

    return floor
