import json
from functools import lru_cache

import pygame
import resource_store as resources

from presentation.figma_ui import figma_rect
from presentation.layout import ASSET_ROOT, PROJECT_ROOT
from settings import GAME_HEIGHT, GAME_WIDTH


@lru_cache(maxsize=1)
def load_dialogue_layout():
    path = PROJECT_ROOT / "assets/ui/layouts/act_3/dialog.json"
    with resources.open_text(path, encoding="utf-8-sig") as source:
        layout = json.load(source)
    if (
        layout.get("schema_version") != 1
        or layout.get("screen") != "dialogue"
        or layout.get("act") != 3
        or layout.get("coordinate_space") != "frame"
        or (layout["frame"]["width"], layout["frame"]["height"]) != (GAME_WIDTH, GAME_HEIGHT)
    ):
        raise ValueError(f"Unsupported Act III dialogue layout: {path}")
    frame = pygame.Rect(0, 0, GAME_WIDTH, GAME_HEIGHT)
    specs = (
        layout["dialog_background"], layout["portrait_section"],
        layout["portrait_section"]["portrait"], layout["speaker_name"], layout["dialogue_text"],
    )
    if layout.get("skip_text") is not None:
        specs += (layout["skip_text"],)
    for spec in specs:
        rect = figma_rect(spec["rect"])
        if rect.width <= 0 or rect.height <= 0 or not frame.contains(rect):
            raise ValueError(f"Invalid Act III dialogue rectangle: {spec['rect']}")
    return layout


@lru_cache(maxsize=1)
def dialogue_background():
    layout = load_dialogue_layout()
    rect = figma_rect(layout["dialog_background"]["rect"])
    source = resources.load_image(ASSET_ROOT / "ui/act_3/dialog_background.png").convert_alpha()
    return pygame.transform.smoothscale(source, rect.size)


def dialogue_close_rect():
    background = figma_rect(load_dialogue_layout()["dialog_background"]["rect"])
    return pygame.Rect(background.right - 174, background.bottom - 32, 126, 24)
