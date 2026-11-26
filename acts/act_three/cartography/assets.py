import resource_store as resources

from presentation.layout import ASSET_ROOT


def load_map_assets(layout):
    directory = ASSET_ROOT / "ui" / "act_3" / "map"
    files = {
        "minimap_frame": layout["cartography"]["minimap"]["asset"],
        "full_map_frame": layout["cartography"]["full_map"]["asset"],
        "backing": "map_backing.png",
        "floor": "explored_floor_texture.png",
        "trader": "marker_trader.png",
        "blacksmith": "marker_blacksmith.png",
        "rune_master": "marker_rune_master.png",
    }
    images = {}
    for name, filename in files.items():
        image = resources.load_image(str(directory / filename)).convert_alpha()
        if name in ("trader", "blacksmith", "rune_master"):
            image = image.subsurface(image.get_bounding_rect(min_alpha=32)).copy()
        images[name] = image
    return images
