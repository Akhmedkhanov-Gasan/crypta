from copy import deepcopy

from presentation.figma_ui import (
    _apply_text_case, _letter_spacing_pixels, _line_height_pixels,
    draw_figma_text, figma_rect, get_figma_font,
)


def _text_width(font, text, spacing):
    return font.size(text)[0] + max(0, len(text) - 1) * spacing


def _wrap_dialogue(font, text, width, spacing):
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}" if line else word
            if line and _text_width(font, candidate, spacing) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines


def draw_dialogue_text(surface, source_spec, text, visible_characters=None, color=None):
    spec = deepcopy(source_spec)
    rectangle = figma_rect(spec["rect"])
    text = _apply_text_case(text, spec.get("text_case", "ORIGINAL"))
    spec["text_case"] = "ORIGINAL"
    original_size = max(1, round(spec["font"]["size"]))
    for size in range(original_size, min(8, original_size) - 1, -1):
        spec["font"]["size"] = size
        font = get_figma_font(spec)
        spacing = _letter_spacing_pixels(spec)
        lines = _wrap_dialogue(font, text, rectangle.width, spacing)
        line_height = _line_height_pixels(spec, font)
        if (
            len(lines) * line_height <= rectangle.height
            and font.get_height() <= rectangle.height
            and all(_text_width(font, line, spacing) <= rectangle.width for line in lines)
        ):
            break
    else:
        raise ValueError(f"Dialogue does not fit its Figma rectangle: {text!r}")
    total_height = len(lines) * line_height
    vertical = spec.get("vertical_align", "TOP")
    y = rectangle.top
    if vertical == "CENTER":
        y = rectangle.centery - total_height // 2
    elif vertical == "BOTTOM":
        y = rectangle.bottom - total_height
    remaining = len(text) if visible_characters is None else max(0, visible_characters)
    for line in lines:
        width = max(1, _text_width(font, line, spacing))
        x = rectangle.left
        if spec.get("horizontal_align") == "CENTER":
            x = rectangle.centerx - width // 2
        elif spec.get("horizontal_align") == "RIGHT":
            x = rectangle.right - width
        line_spec = {
            **spec,
            "rect": {"x": x, "y": y, "width": width, "height": line_height},
            "horizontal_align": "LEFT",
            "vertical_align": "TOP",
        }
        draw_figma_text(surface, line_spec, text_override=line[:remaining], color_override=color)
        remaining = max(0, remaining - len(line) - 1)
        y += line_height
