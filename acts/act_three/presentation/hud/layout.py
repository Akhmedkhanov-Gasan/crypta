import json
from functools import lru_cache

import pygame

import resource_store as resources
from presentation.layout import PROJECT_ROOT


_LAYOUT_PATH = (
    PROJECT_ROOT
    / "assets"
    / "ui"
    / "layouts"
    / "act_3"
    / "HUD_act3.json"
)


@lru_cache(maxsize=1)
def get_act_three_hud_layout():
    with resources.open_text(
        _LAYOUT_PATH,
        encoding="utf-8",
    ) as file:
        layout = json.load(file)

    if (
        layout.get("schema_version") != 3
        or layout.get("screen") != "hud"
        or layout.get("act") != 3
        or layout.get("coordinate_space") != "frame"
    ):
        raise ValueError(
            f"Invalid Act III HUD layout: {_LAYOUT_PATH}"
        )

    frame = layout.get("frame", {})

    if (
        frame.get("width") != 1280
        or frame.get("height") != 720
    ):
        raise ValueError(
            "Act III HUD layout must be 1280x720."
        )

    return layout


def get_layout_value(layout, *path):
    value = layout

    for key in path:
        value = value[key]

    return value


def get_layout_rect(layout, *path):
    value = get_layout_value(layout, *path)

    if "rect" in value:
        value = value["rect"]

    return pygame.Rect(
        value["x"],
        value["y"],
        value["width"],
        value["height"],
    )
