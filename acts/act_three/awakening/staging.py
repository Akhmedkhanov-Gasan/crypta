import resource_store as resources


def read_awakening_markers(path, floor):
    root = resources.load_xml(path).getroot()
    tile_width = int(root.get("tilewidth", "64"))
    tile_height = int(root.get("tileheight", "64"))
    names = {"awakening_player", "awakening_old_man"}
    markers = {}

    def visit(node, offset_x=0.0, offset_y=0.0):
        offset_x += float(node.get("offsetx", "0"))
        offset_y += float(node.get("offsety", "0"))
        for child in node:
            if child.tag in ("group", "objectgroup"):
                visit(child, offset_x, offset_y)
            elif child.tag == "object":
                name = child.get("name", "").strip().casefold()
                if name not in names:
                    continue
                if name in markers:
                    raise ValueError(f"Duplicate awakening marker: {name}")
                position = (
                    int((float(child.get("x", "0")) + offset_x) // tile_width),
                    int((float(child.get("y", "0")) + offset_y) // tile_height),
                )
                column, row = position
                if not (0 <= row < len(floor.map) and 0 <= column < len(floor.map[row])):
                    raise ValueError(f"Awakening marker outside the map: {name} {position}")
                if name == "awakening_player" and floor.map[row][column] != ".":
                    raise ValueError(f"awakening_player must be on a walkable tile: {position}")
                markers[name] = position

    visit(root)
    if len(markers) == 2 and len(set(markers.values())) != 2:
        raise ValueError("Awakening player and old man markers must occupy different tiles.")
    return markers
