import json
from functools import lru_cache

import resource_store as resources
from acts.act_three.rune_master.default_layout import default_layout
from presentation.layout import PROJECT_ROOT


LAYOUT_PATH = PROJECT_ROOT / "assets/ui/layouts/act_3/runes.json"


@lru_cache(maxsize=1)
def get_layout():
    if resources.is_file(LAYOUT_PATH):
        with resources.open_text(LAYOUT_PATH) as source:
            layout = json.load(source)
    else:
        layout = default_layout()
    if (
        layout.get("schema_version") != 1
        or layout.get("screen") != "runes"
        or layout.get("act") != 3
        or layout.get("coordinate_space") != "frame"
        or layout.get("frame", {}).get("width") != 1280
        or layout.get("frame", {}).get("height") != 720
    ):
        raise ValueError(f"Invalid Act III rune layout: {LAYOUT_PATH}")
    for name in ("slot_01", "slot_02", "slot_03"):
        spec = layout["slots"][name]
        if "background" not in spec:
            spec["background"] = {
                **spec["frames"][0],
                "asset_path": "assets/sprites/ui/act_3/rune_ui_elements/rune_background.png",
            }
        bounds = spec["rect"]
        if bounds["width"] <= 0 or bounds["height"] <= 0:
            raise ValueError(f"Invalid rune slot bounds: {name}")
        if spec["background"]["rect"] != bounds:
            raise ValueError(f"Rune background must match slot bounds: {name}")
        first = layout["slots"]["slot_01"]["rect"]
        if (bounds["width"], bounds["height"]) != (first["width"], first["height"]):
            raise ValueError("Rune slots must have equal dimensions")
    return layout
