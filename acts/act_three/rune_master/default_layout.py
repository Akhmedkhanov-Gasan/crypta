ART_ROOT = "assets/sprites/ui/act_3/rune_ui_elements"


def rect(x, y, width, height):
    return {"x": x, "y": y, "width": width, "height": height}


def art(name, bounds):
    return {"rect": bounds, "asset_path": f"{ART_ROOT}/{name}.png", "opacity": 1}


def text(bounds, size, color):
    return {
        "rect": bounds, "text": "",
        "font": {"family": "JMH Cthulhumbus Arcade", "style": "Regular", "size": size},
        "line_height": {"unit": "AUTO"},
        "letter_spacing": {"unit": "PIXELS", "value": 0},
        "horizontal_align": "CENTER", "vertical_align": "CENTER",
        "text_case": "ORIGINAL",
        "color": {"r": color, "g": color, "b": color, "a": 255},
    }


def default_layout():
    slots = {}
    for index in range(3):
        x, y = 265 + index * 250, 152
        bounds = rect(x, y, 250, 375)
        description = rect(x + 38, y + 194, 175, 110)
        description_text = text(description, 15, 255)
        description_text["font"]["family"] = "Ubuntu Mono"
        description_text["line_height"] = {"unit": "PIXELS", "value": 17}
        slots[f"slot_{index + 1:02d}"] = {
            "rect": bounds, "hitbox": bounds,
            "background": art("rune_background", bounds),
            "content": {
                "rect": rect(x + 38, y + 55, 175, 249),
                "icon": rect(x + 75, y + 55, 100, 100),
                "name": text(rect(x + 38, y + 156, 174, 32), 20, 167),
                "description_background": {
                    "rect": description,
                    "fill": {"r": 137, "g": 137, "b": 137, "a": 115},
                    "corner_radius": 7,
                },
                "description": description_text,
            },
        }
    layout = {
        "schema_version": 1, "screen": "runes", "act": 3,
        "coordinate_space": "frame",
        "frame": {"name": "act3_runes", "width": 1280, "height": 720},
        "window_background": art("window_background", rect(140, 40, 1000, 640)),
        "close_hitbox": rect(1090, 61, 40, 39),
        "slots_container": rect(265, 152, 750, 375),
        "slots": slots,
    }
    for name, bounds in (
        ("return_button", rect(540, 524, 200, 51)),
        ("confirm_button", rect(505, 579, 270, 63)),
    ):
        layout[name] = {
            "hitbox": bounds,
            "inactive": art(f"{name}_deactive", bounds),
            "active": art(f"{name}_active", bounds),
        }
    return layout
