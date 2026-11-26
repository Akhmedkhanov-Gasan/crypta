import random
from pathlib import Path

import resource_store as resources
from acts.act_three.room_generation import _passage_positions
from acts.act_three.tmx_loader import load_tmx_floor


def _load_variants(config, role):
    project_root = Path(__file__).resolve().parents[2]
    directory = config.get(f"{role}_template_directory")
    if directory:
        paths = resources.glob_resources(project_root / directory, f"room_{role}_*.tmx")
    else:
        key = "map_path" if role == "entry" else "exit_map_path"
        paths = [project_root / config[key]]
    if not paths:
        raise ValueError(f"No Act Three {role} templates found")

    variants = []
    names = ("exit_up", "exit_back") if role == "entry" else ("exit_down", "exit_next_floor")
    for path in paths:
        room = load_tmx_floor(path)
        gates = [connector for connector in room["connectors"] if connector["name"] in names]
        if len(gates) != 1:
            raise ValueError(f"Room needs exactly one {names[0]} connector: {path.name}")
        positions = _passage_positions(gates[0])
        if positions is None:
            raise ValueError(f"Gate needs a direction: {path.name}: {names[0]}")
        x, y = positions[1]
        if not (0 <= y < room["height"] and 0 <= x < room["width"] and room["map"][y][x] == "."):
            raise ValueError(f"Gate approach is blocked: {path.name}: {names[0]} at {(x, y)}")
        if role == "entry" and room["player_start"] is None:
            room["player_start"] = positions[1]
        variants.append(room)
    return variants


def select_floor_templates(config):
    entries = _load_variants(config, "entry")
    exits = _load_variants(config, "exit")
    return random.choice(entries), random.choice(exits)


def floor_template_pairs(config):
    entries = _load_variants(config, "entry")
    exits = _load_variants(config, "exit")
    pairs = [(entry, exit_room) for entry in entries for exit_room in exits]
    random.shuffle(pairs)
    return pairs
