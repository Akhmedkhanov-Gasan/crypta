import json
from functools import lru_cache

import pygame
import resource_store as resources

from acts.act_three.abilities.catalog import SUBCLASS_DEFINITIONS
from presentation.layout import ACT_THREE_TILE_SIZE, ASSET_ROOT, PROJECT_ROOT
from settings import TILE_SIZE


@lru_cache(maxsize=1)
def load_layouts():
    path = PROJECT_ROOT / "assets/ui/layouts/act_3/awakening.json"
    with resources.open_text(path, encoding="utf-8-sig") as source:
        bundle = json.load(source)
    if bundle.get("screen") != "subclass_selection_bundle" or bundle.get("schema_version") != 1:
        raise ValueError(f"Unsupported Act III awakening layout: {path}")
    screens = bundle["screens"]
    for parent in ("rogue", "warrior", "mage"):
        layout = screens[parent]
        expected = {key for key, value in SUBCLASS_DEFINITIONS.items() if value.parent_class == parent}
        choices = layout["subclass_choices"]
        if (
            layout["frame"]["width"] != 1280 or layout["frame"]["height"] != 720
            or layout["player_class"] != parent
            or set(choices["order"]) != expected
            or len(choices["order"]) != 2
            or set(choices["options"]) != expected
        ):
            raise ValueError(f"Invalid Act III subclass choices: {parent}")
    return screens


def load_selection_assets():
    root = ASSET_ROOT / "ui/act_3/awakening"
    paths = {
        "act_three_subclass_card": root / "portrait_background.png",
        "act_three_skill_panel": root / "passive_background.png",
    }
    for subclass, definition in SUBCLASS_DEFINITIONS.items():
        folder = root / subclass
        paths[f"{subclass}_portrait"] = folder / f"portrait_{subclass}.png"
        paths[definition.passive.icon_asset] = folder / "passive_icon.png"
        paths[definition.abilities["q"].icon_asset] = folder / "ability_icon_01.png"
        paths[definition.abilities["f"].icon_asset] = folder / "ability_icon_02.png"
    return {key: resources.load_image(str(path)).convert_alpha() for key, path in paths.items()}


@lru_cache(maxsize=18)
def scene_frames(parent, animation):
    folder = ASSET_ROOT / "ui/act_3/awakening/classes" / parent / animation
    paths = resources.glob_resources(folder, "*.png")
    if len(paths) != 8:
        raise ValueError(f"Expected eight awakening frames: {folder}")
    return tuple(
        pygame.transform.scale(
            resources.load_image(str(path)).convert_alpha(),
            (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        )
        for path in paths
    )


@lru_cache(maxsize=2)
def old_man_sprite(act):
    path = (
        ASSET_ROOT / "act_2/npcs/old_man/standing/standing_00.png"
        if act == 2 else
        ASSET_ROOT / "act_3/npcs/old_man/appearance/appearance_05.png"
    )
    image = resources.load_image(str(path)).convert_alpha()
    if act == 2:
        return pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
    bounds = image.get_bounding_rect(min_alpha=8)
    if bounds.width and bounds.height:
        image = image.subsurface(bounds).copy()
    height = 78
    return pygame.transform.scale(image, (max(1, round(image.get_width() * height / image.get_height())), height))


@lru_cache(maxsize=3)
def old_man_frames(animation):
    folder = ASSET_ROOT / "ui/act_3/awakening/old_man" / animation
    paths = resources.glob_resources(folder, "*.png")
    if len(paths) != 8:
        raise ValueError(f"Expected eight old man frames: {folder}")
    return tuple(
        pygame.transform.scale(
            resources.load_image(str(path)).convert_alpha(),
            (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        )
        for path in paths
    )

