from functools import lru_cache
from pathlib import Path

import resource_store as resources


@lru_cache(maxsize=1)
def tileset_catalog():
    directory = Path(__file__).resolve().parents[2] / "assets/maps/act_3"
    paths = [
        *resources.glob_resources(directory, "*.tsx"),
        *resources.glob_resources(directory / "torches", "*.tsx"),
    ]
    catalog = {}
    first_gid = 1
    for path in sorted(paths):
        root = resources.load_xml(path).getroot()
        count = int(root.get("tilecount", 0))
        count = max(count, max((int(tile.get("id", 0)) + 1 for tile in root.findall("tile")), default=0))
        if count <= 0:
            raise ValueError(f"Tileset has no tiles: {path}")
        catalog[path.resolve()] = (first_gid, root)
        first_gid += count
    return catalog


def normalize_tile_layers(layers, map_root, map_path):
    catalog = tileset_catalog()
    ranges = []
    for node in map_root.findall("tileset"):
        source = node.get("source")
        if not source:
            raise ValueError(f"Act Three requires external tilesets: {map_path}")
        path = (map_path.parent / source).resolve()
        if path not in catalog:
            raise ValueError(f"Tileset must be in the Act Three map catalog: {path}")
        ranges.append((int(node.get("firstgid", 1)), catalog[path][0]))
    ranges.sort(reverse=True)
    for layer in layers.values():
        for row in layer:
            for index, gid in enumerate(row):
                if not gid:
                    continue
                flags = gid & 0xF0000000
                tile_id = gid & 0x0FFFFFFF
                for source_first, target_first in ranges:
                    if tile_id >= source_first:
                        row[index] = flags | (target_first + tile_id - source_first)
                        break
                else:
                    raise ValueError(f"Invalid tile ID {tile_id}: {map_path}")
