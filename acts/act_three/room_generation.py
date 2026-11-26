"""Compose small Act III floors from hand-authored TMX templates."""

from __future__ import annotations

import random
from pathlib import Path

import resource_store as resources

from acts.act_three.tmx_loader import load_tmx_floor


OPPOSITE_DIRECTION = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
}

DIRECTION_STEP = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
}


def _template_paths(directory, spawn_path):
    directory = Path(directory).resolve()
    paths = resources.glob_resources(directory, "*.tmx", recursive=True)
    return sorted(
        path for path in paths
        if path != Path(spawn_path).resolve()
        and path.name.startswith(("room_", "corridor_", "test_room_"))
        and not {"key_rooms", "room_entry", "room_exit"}.intersection(path.relative_to(directory).parts)
        and not path.name.startswith(("room_entry_", "room_exit_"))
        and path.name != "room_rune_trial.tmx"
    )


def _translated(position, offset):
    return position[0] + offset[0], position[1] + offset[1]


def _placement_offset(open_connector, template_connector):
    step = DIRECTION_STEP[open_connector["direction"]]
    target_position = (
        open_connector["position"][0] + step[0],
        open_connector["position"][1] + step[1],
    )
    return (
        target_position[0] - template_connector["position"][0],
        target_position[1] - template_connector["position"][1],
    )


def _bounds(template, offset):
    return (
        offset[0],
        offset[1],
        offset[0] + template["width"],
        offset[1] + template["height"],
    )


def _bounds_overlap(first, second):
    return (
        first[0] < second[2]
        and first[2] > second[0]
        and first[1] < second[3]
        and first[3] > second[1]
    )


def _shift_edge(edge, offset):
    return tuple(sorted((_translated(edge[0], offset), _translated(edge[1], offset))))


def _shift_entities(items, offset):
    shifted = []
    for item in items:
        shifted_item = dict(item)
        shifted_item["position"] = _translated(item["position"], offset)
        shifted.append(shifted_item)
    return shifted


def _shift_encounter_zones(zones, offset):
    return [
        {
            **zone,
            "left": zone["left"] + offset[0],
            "right": zone["right"] + offset[0],
            "top": zone["top"] + offset[1],
            "bottom": zone["bottom"] + offset[1],
        }
        for zone in zones
    ]


def _compose(placements, connections):
    min_column = min(offset[0] for _, offset in placements)
    min_row = min(offset[1] for _, offset in placements)
    max_column = max(
        offset[0] + template["width"]
        for template, offset in placements
    )
    max_row = max(
        offset[1] + template["height"]
        for template, offset in placements
    )
    normalization = (-min_column, -min_row)
    width = max_column - min_column
    height = max_row - min_row

    dungeon_map = [["#" for _ in range(width)] for _ in range(height)]
    layer_names = tuple(
        dict.fromkeys(
            name
            for template, _ in placements
            for name in template["tile_layers"]
        )
    )
    layers = {
        name: [[0 for _ in range(width)] for _ in range(height)]
        for name in layer_names
    }
    barriers = set()
    torches = []
    enemies = []
    npcs = []
    ores = []
    encounter_zones = []
    spawn_regions = []
    chests = []
    breakable_crates = []
    potions = []
    upgrade_altar = None
    shadow_step_trial = None
    piercing_trial = None
    crushing_trial = None
    shield_trial = None
    curse_trial = None
    summoner_trial = None
    lantern_encounter = None
    rune_trial = None
    trader_altar = None
    trial_entrance = None
    trial_safe_cells = set()
    open_connectors = []

    for template, original_offset in placements:
        offset = (
            original_offset[0] + normalization[0],
            original_offset[1] + normalization[1],
        )
        if template.get("trader_altar") is not None:
            if trader_altar is not None:
                raise ValueError("Only one trader altar is supported per floor")
            trader_altar = _translated(template["trader_altar"], offset)
        if template.get("rune_trial") is not None:
            from acts.act_three.rune_master.trial_map import shift_trial

            if rune_trial is not None:
                raise ValueError("Only one rune trial is supported per floor")
            rune_trial = shift_trial(template["rune_trial"], offset)
        spawn_regions.append({
            "left": offset[0],
            "top": offset[1],
            "right": offset[0] + template["width"],
            "bottom": offset[1] + template["height"],
            "enabled": template.get("enemy_spawn_mode", False),
            "ore_spawn_mode": template.get("ore_spawn_mode", template.get("enemy_spawn_mode", False)),
            "ore_types": template.get("ore_types", ()),
            "ore_count": template.get("ore_count"),
            "source_path": template["source_path"],
        })

        if template.get("trial_entrance") is not None:
            trial_entrance = _translated(template["trial_entrance"], offset)
        if template.get("lantern_encounter") is not None:
            from acts.act_three.enemies.lantern_warden.encounter import shift_encounter

            lantern_encounter = shift_encounter(template["lantern_encounter"], offset)
        trial_safe_cells.update(_translated(cell, offset) for cell in template.get("trial_safe_cells", ()))

        if template.get("piercing_trial") is not None:
            from acts.act_three.trials.archer import shift_trial as shift_piercing_trial

            if piercing_trial is not None:
                raise ValueError("Only one Piercing Shot trial is supported per floor")
            piercing_trial = shift_piercing_trial(template["piercing_trial"], offset)

        if template.get("shield_trial") is not None:
            from acts.act_three.trials.paladin import shift_trial as shift_shield_trial

            shield_trial = shift_shield_trial(template["shield_trial"], offset)

        if template.get("curse_trial") is not None:
            from acts.act_three.trials.warlock import shift_trial as shift_curse_trial

            curse_trial = shift_curse_trial(template["curse_trial"], offset)

        if template.get("summoner_trial") is not None:
            from acts.act_three.trials.summoner import shift_trial as shift_summoner_trial

            summoner_trial = shift_summoner_trial(template["summoner_trial"], offset)

        if template.get("crushing_trial") is not None:
            from acts.act_three.trials.berserker import shift_trial as shift_crushing_trial

            crushing_trial = shift_crushing_trial(template["crushing_trial"], offset)

        if template.get("shadow_step_trial") is not None:
            from acts.act_three.trials.assassin import shift_trial

            if shadow_step_trial is not None:
                raise ValueError(
                    "Only one Shadow Step trial is supported per floor"
                )

            shadow_step_trial = shift_trial(
                template["shadow_step_trial"],
                offset,
            )

        for row, map_row in enumerate(template["map"]):
            for column, value in enumerate(map_row):
                dungeon_map[row + offset[1]][column + offset[0]] = value

        for layer_name, layer in template["tile_layers"].items():
            for row, layer_row in enumerate(layer):
                for column, gid in enumerate(layer_row):
                    if gid:
                        layers[layer_name][row + offset[1]][column + offset[0]] = gid

        barriers.update(
            _shift_edge(edge, offset)
            for edge in template["barriers"]
        )
        torches.extend(
            _translated(position, offset)
            for position in template["torches"]
        )
        enemies.extend(_shift_entities(template["enemies"], offset))
        room_npcs = _shift_entities(template.get("npcs", []), offset)
        entrance = next(iter(_structural_connectors(template)), None)
        if entrance is not None:
            dx, dy = DIRECTION_STEP[entrance["direction"]]
            x, y = entrance["position"]
            for npc in room_npcs:
                npc["room_entrance"] = _translated((x - dx, y - dy), offset)
        npcs.extend(room_npcs)
        ores.extend(_shift_entities(template.get("ores", []), offset))
        encounter_zones.extend(
            _shift_encounter_zones(
                template.get("encounter_zones", []),
                offset,
            )
        )
        chests.extend(_shift_entities(template["chests"], offset))
        breakable_crates.extend(_shift_entities(template["breakable_crates"], offset))
        potions.extend(
            _translated(position, offset)
            for position in template["potions"]
        )
        if (
            upgrade_altar is None
            and template.get("upgrade_altar") is not None
        ):
            upgrade_altar = _translated(
                template["upgrade_altar"],
                offset,
            )
        open_connectors.extend(
            {
                **connector,
                "position": _translated(connector["position"], offset),
            }
            for connector in template["connectors"]
        )

    shifted_connections = {
        tuple(
            sorted(
                (
                    _translated(first, normalization),
                    _translated(second, normalization),
                )
            )
        )
        for first, second in connections
    }
    barriers.difference_update(shifted_connections)
    connected_positions = {
        position
        for edge in shifted_connections
        for position in edge
    }
    open_connectors = [
        connector
        for connector in open_connectors
        if connector["position"] not in connected_positions
    ]

    spawn_template, spawn_offset = placements[0]

    if spawn_template["player_start"] is None:
        raise ValueError(
            "The first TMX template must contain a Spawn entity"
        )

    player_start = _translated(
        spawn_template["player_start"],
        (
            spawn_offset[0] + normalization[0],
            spawn_offset[1] + normalization[1],
        ),
    )
    fallback_stairs = next(
        (
            (column, row)
            for row in range(height - 1, -1, -1)
            for column in range(width - 1, -1, -1)
            if dungeon_map[row][column] == "."
        ),
        player_start,
    )

    return {
        "map": ["".join(row) for row in dungeon_map],
        "player_start": player_start,
        "enemies": enemies,
        "npcs": npcs,
        "ores": ores,
        "shadow_step_trial": shadow_step_trial,
        "piercing_trial": piercing_trial,
        "crushing_trial": crushing_trial,
        "shield_trial": shield_trial,
        "curse_trial": curse_trial,
        "summoner_trial": summoner_trial,
        "trial_entrance": trial_entrance,
        "trial_safe_cells": trial_safe_cells,
        "encounter_zones": encounter_zones,
        "lantern_encounter": lantern_encounter,
        "rune_trial": rune_trial,
        "trader_altar": trader_altar,
        "spawn_regions": spawn_regions,
        "room_connections": shifted_connections,
        "chests": chests,
        "breakable_crates": breakable_crates,
        "potions": potions,
        "torches": torches,
        "upgrade_altar": upgrade_altar,
        "tile_layers": layers,
        "barriers": barriers,
        "connectors": open_connectors,
        "stairs": fallback_stairs,
        "boss_door": None,
        "boss_room": None,
        "boss_columns": [],
        "boss_emitters": [],
        "seal_boss_door_during_fight": False,
        "visual_seed": random.randrange(1_000_000),
        "generated_pieces": [
            Path(template["source_path"]).name
            for template, _ in placements
        ],
    }


def generate_tmx_room_floor(spawn_path, template_directory, piece_count=2):
    project_root = Path(__file__).resolve().parents[2]
    spawn_path = Path(spawn_path)
    template_directory = Path(template_directory)

    if not spawn_path.is_absolute():
        spawn_path = project_root / spawn_path
    if not template_directory.is_absolute():
        template_directory = project_root / template_directory

    spawn = load_tmx_floor(spawn_path)
    templates = [
        load_tmx_floor(path)
        for path in _template_paths(template_directory, spawn_path)
    ]
    placements = [(spawn, (0, 0))]
    open_connectors = [dict(connector) for connector in spawn["connectors"]]
    connections = []

    while len(placements) < piece_count and open_connectors and templates:
        options = []
        for open_index, open_connector in enumerate(open_connectors):
            direction = open_connector.get("direction", "")
            expected_direction = OPPOSITE_DIRECTION.get(direction)
            if expected_direction is None:
                continue
            for template_index, template in enumerate(templates):
                for connector_index, connector in enumerate(template["connectors"]):
                    if (
                        connector.get("direction") != expected_direction
                        or connector.get("width", 1)
                        != open_connector.get("width", 1)
                    ):
                        continue
                    offset = _placement_offset(open_connector, connector)
                    candidate_bounds = _bounds(template, offset)
                    if any(
                        _bounds_overlap(candidate_bounds, _bounds(placed, placed_offset))
                        for placed, placed_offset in placements
                    ):
                        continue
                    options.append(
                        (
                            open_index,
                            template_index,
                            connector_index,
                            offset,
                        )
                    )

        if not options:
            break

        open_index, template_index, connector_index, offset = random.choice(options)
        open_connector = open_connectors.pop(open_index)
        template = templates[template_index]
        used_connector = template["connectors"][connector_index]
        used_world_position = _translated(used_connector["position"], offset)
        connections.append((open_connector["position"], used_world_position))
        placements.append((template, offset))
        open_connectors.extend(
            {
                **connector,
                "position": _translated(connector["position"], offset),
            }
            for index, connector in enumerate(template["connectors"])
            if index != connector_index
        )

    return _compose(placements, connections)


def _structural_connectors(template):
    structural_names = {
        "exit_north",
        "exit_south",
        "exit_east",
        "exit_west",
    }
    return [
        connector
        for connector in template["connectors"]
        if any(
            connector.get("name", "") == name
            or connector.get("name", "").startswith(f"{name}_")
            for name in structural_names
        )
    ]


def generate_tmx_sequence_floor(template_paths):
    project_root = Path(__file__).resolve().parents[2]
    resolved_paths = []

    for template_path in template_paths:
        resolved_path = Path(template_path)
        if not resolved_path.is_absolute():
            resolved_path = project_root / resolved_path
        resolved_paths.append(resolved_path)

    templates = [
        load_tmx_floor(path)
        for path in resolved_paths
    ]

    if not templates:
        raise ValueError("TMX room sequence cannot be empty")

    placements = [(templates[0], (0, 0))]
    connections = []
    first_connectors = _structural_connectors(templates[0])

    if not first_connectors and len(templates) > 1:
        raise ValueError(
            f"No structural connector in {resolved_paths[0].name}"
        )

    open_connector = (
        random.choice(first_connectors)
        if first_connectors
        else None
    )

    for sequence_index, template in enumerate(
        templates[1:],
        start=1,
    ):
        expected_direction = OPPOSITE_DIRECTION.get(
            open_connector.get("direction", "")
        )
        options = []

        for connector in _structural_connectors(template):
            if (
                connector.get("direction") != expected_direction
                or connector.get("width", 1)
                != open_connector.get("width", 1)
            ):
                continue

            offset = _placement_offset(
                open_connector,
                connector,
            )
            candidate_bounds = _bounds(template, offset)

            if any(
                _bounds_overlap(
                    candidate_bounds,
                    _bounds(placed_template, placed_offset),
                )
                for placed_template, placed_offset in placements
            ):
                continue

            options.append((connector, offset))

        if not options:
            raise ValueError(
                "Cannot connect "
                f"{resolved_paths[sequence_index - 1].name} "
                f"to {resolved_paths[sequence_index].name}"
            )

        used_connector, offset = random.choice(options)
        used_world_position = _translated(
            used_connector["position"],
            offset,
        )

        connections.append(
            (
                open_connector["position"],
                used_world_position,
            )
        )
        placements.append((template, offset))

        if sequence_index >= len(templates) - 1:
            continue

        outgoing_connectors = [
            {
                **connector,
                "position": _translated(
                    connector["position"],
                    offset,
                ),
            }
            for connector in _structural_connectors(template)
            if connector is not used_connector
        ]

        if not outgoing_connectors:
            raise ValueError(
                f"No outgoing connector in "
                f"{resolved_paths[sequence_index].name}"
            )

        open_connector = random.choice(outgoing_connectors)

    return _compose(placements, connections)


def _passage_positions(connector):
    name = connector.get("name", "")
    direction = connector.get("direction", "")

    if not direction and name in ("exit_up", "exit_down", "exit_back", "exit_next_floor"):
        direction = "north"

    step = DIRECTION_STEP.get(direction)
    if step is None:
        return None

    wall_position = connector["position"]
    trigger_position = (
        wall_position[0] - step[0],
        wall_position[1] - step[1],
    )
    return wall_position, trigger_position


def attach_act_three_passages(
    floor,
    floor_index,
    floor_count,
):
    passages = []

    for connector in floor.get("connectors", []):
        name = connector.get("name", "")

        if name in ("exit_down", "exit_next_floor"):
            passage_id = "exit_down"
            target_floor_index = (
                floor_index + 1
                if floor_index + 1 < floor_count
                else None
            )
        elif name in ("exit_up", "exit_back"):
            passage_id = "exit_up"
            target_floor_index = None
        else:
            continue

        positions = _passage_positions(connector)
        if positions is None:
            continue

        wall_position, trigger_position = positions

        passages.append(
            {
                "passage_id": passage_id,
                "wall_position": wall_position,
                "trigger_position": trigger_position,
                "target_floor_index": target_floor_index,
                "target_passage_id": "exit_up" if target_floor_index is not None else None,
                "requires_clear": False,
            }
        )

    floor["passages"] = passages
    return floor
