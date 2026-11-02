import json
from functools import lru_cache

import pygame
import resource_store as resources

from presentation.dialogue_text import draw_dialogue_text
from presentation.figma_ui import figma_rect
from presentation.layout import ASSET_ROOT, PROJECT_ROOT
from settings import GAME_HEIGHT, GAME_WIDTH


@lru_cache(maxsize=1)
def _layout():
    path = PROJECT_ROOT / "assets/ui/layouts/act_2/dialog.json"
    with resources.open_text(path, encoding="utf-8-sig") as source:
        layout = json.load(source)
    if (
        layout.get("schema_version") != 1
        or layout.get("screen") != "dialogue"
        or layout.get("act") != 2
        or layout.get("coordinate_space") != "frame"
        or (layout["frame"]["width"], layout["frame"]["height"]) != (GAME_WIDTH, GAME_HEIGHT)
    ):
        raise ValueError(f"Unsupported Act II dialogue layout: {path}")
    frame = pygame.Rect(0, 0, GAME_WIDTH, GAME_HEIGHT)
    for key in ("dialog_background", "speaker_name", "dialogue_text", "skip_text"):
        if layout.get(key) is None:
            continue
        rect = figma_rect(layout[key]["rect"])
        if rect.width <= 0 or rect.height <= 0 or not frame.contains(rect):
            raise ValueError(f"Invalid Act II dialogue rectangle: {key}")
    return layout


@lru_cache(maxsize=1)
def _background():
    rect = figma_rect(_layout()["dialog_background"]["rect"])
    image = resources.load_image(ASSET_ROOT / "ui/act_2/ui_v.0.2/dialog_background.png").convert_alpha()
    return pygame.transform.smoothscale(image, rect.size)


def draw_act_two_dialogue(screen, speaker, text, opacity=1.0, visible_characters=None):
    if not (
        resources.is_file(PROJECT_ROOT / "assets/ui/layouts/act_2/dialog.json")
        and resources.is_file(ASSET_ROOT / "ui/act_2/ui_v.0.2/dialog_background.png")
    ):
        return False
    layout = _layout()
    panel = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    background = _background().copy()
    background.set_alpha(round(255 * layout["dialog_background"].get("opacity", 1)))
    panel.blit(background, figma_rect(layout["dialog_background"]["rect"]))
    draw_dialogue_text(panel, layout["speaker_name"], speaker)
    draw_dialogue_text(panel, layout["dialogue_text"], text, visible_characters)
    if layout.get("skip_text") is not None:
        draw_dialogue_text(panel, layout["skip_text"], "SPACE / CLICK - SKIP TEXT")
    panel.set_alpha(round(255 * max(0, min(1, opacity))))
    screen.blit(panel, (0, 0))
    return True
