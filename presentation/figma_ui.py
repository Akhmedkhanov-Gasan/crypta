from __future__ import annotations

from typing import Any

import pygame

from presentation.layout import FONT_ROOT


_FONT_PATHS = {
    ("alagard", "regular"): FONT_ROOT / "alagard" / "alagard.ttf",
    ("alagard", "medium"): FONT_ROOT / "alagard" / "alagard.ttf",

    ("pixelify sans", "regular"):
        FONT_ROOT / "Pixelify_Sans" / "static" / "PixelifySans-Regular.ttf",
    ("pixelify sans", "medium"):
        FONT_ROOT / "Pixelify_Sans" / "static" / "PixelifySans-Medium.ttf",
    ("pixelify sans", "semibold"):
        FONT_ROOT / "Pixelify_Sans" / "static" / "PixelifySans-SemiBold.ttf",
    ("pixelify sans", "bold"):
        FONT_ROOT / "Pixelify_Sans" / "static" / "PixelifySans-Bold.ttf",
}


_FONT_CACHE: dict[tuple[str, str, int], pygame.font.Font] = {}


def figma_rect(data: dict[str, Any]) -> pygame.Rect:
    return pygame.Rect(
        round(data["x"]),
        round(data["y"]),
        round(data["width"]),
        round(data["height"]),
    )

def _figma_color(
    color_data: dict[str, Any] | None,
) -> tuple[int, int, int, int] | None:
    if color_data is None:
        return None

    return (
        round(color_data.get("r", 255)),
        round(color_data.get("g", 255)),
        round(color_data.get("b", 255)),
        round(color_data.get("a", 255)),
    )


def draw_figma_rectangle(
    screen: pygame.Surface,
    rectangle_spec: dict[str, Any] | None,
) -> None:
    if rectangle_spec is None:
        return

    rect = figma_rect(rectangle_spec["rect"])
    fill_color = _figma_color(rectangle_spec.get("fill"))
    stroke_color = _figma_color(rectangle_spec.get("stroke"))

    stroke_width = max(
        0,
        round(rectangle_spec.get("stroke_weight", 0)),
    )
    corner_radius = max(
        0,
        round(rectangle_spec.get("corner_radius", 0)),
    )
    blur_radius = max(
        0,
        round(rectangle_spec.get("blur_radius", 0)),
    )

    padding = blur_radius * 2
    layer = pygame.Surface(
        (
            max(1, rect.width + padding * 2),
            max(1, rect.height + padding * 2),
        ),
        pygame.SRCALPHA,
    )

    local_rect = pygame.Rect(
        padding,
        padding,
        rect.width,
        rect.height,
    )

    if fill_color is not None:
        pygame.draw.rect(
            layer,
            fill_color,
            local_rect,
            border_radius=corner_radius,
        )

    if stroke_color is not None and stroke_width > 0:
        pygame.draw.rect(
            layer,
            stroke_color,
            local_rect,
            width=stroke_width,
            border_radius=corner_radius,
        )

    if blur_radius > 0:
        layer = pygame.transform.gaussian_blur(
            layer,
            blur_radius,
        )

    screen.blit(
        layer,
        (rect.x - padding, rect.y - padding),
    )


def _load_figma_font(text_spec: dict[str, Any]) -> pygame.font.Font:
    font_spec = text_spec["font"]

    family = str(font_spec["family"]).strip().lower()
    style = str(font_spec["style"]).strip().lower()
    size = max(1, round(font_spec["size"]))

    cache_key = (family, style, size)

    cached_font = _FONT_CACHE.get(cache_key)
    if cached_font is not None:
        return cached_font

    font_path = _FONT_PATHS.get((family, style))

    if font_path is None:
        raise ValueError(
            f"Unsupported Figma font: "
            f"{font_spec['family']} {font_spec['style']}"
        )

    font = pygame.font.Font(str(font_path), size)
    _FONT_CACHE[cache_key] = font
    return font


def get_figma_font(
    text_spec: dict[str, Any],
) -> pygame.font.Font:
    return _load_figma_font(text_spec)


def _apply_text_case(text: str, text_case: str) -> str:
    text_case = text_case.upper()

    if text_case == "UPPER":
        return text.upper()

    if text_case == "LOWER":
        return text.lower()

    if text_case == "TITLE":
        return text.title()

    return text


def _line_height_pixels(
    text_spec: dict[str, Any],
    font: pygame.font.Font,
) -> int:
    line_height = text_spec.get("line_height", {})
    unit = str(line_height.get("unit", "AUTO")).upper()
    value = line_height.get("value")

    if unit == "PIXELS" and value is not None:
        return max(1, round(value))

    if unit == "PERCENT" and value is not None:
        font_size = text_spec["font"]["size"]
        return max(1, round(font_size * value / 100))

    return font.get_linesize()


def _letter_spacing_pixels(text_spec: dict[str, Any]) -> int:
    letter_spacing = text_spec.get("letter_spacing", {})
    unit = str(letter_spacing.get("unit", "PIXELS")).upper()
    value = letter_spacing.get("value", 0) or 0

    if unit == "PERCENT":
        font_size = text_spec["font"]["size"]
        return round(font_size * value / 100)

    return round(value)


def _render_line(
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int, int],
    letter_spacing: int,
) -> pygame.Surface:
    red, green, blue, alpha = color

    if not text:
        return pygame.Surface(
            (1, max(1, font.get_height())),
            pygame.SRCALPHA,
        )

    # Важный случай: сохраняем штатный kerning шрифта.
    if letter_spacing == 0:
        rendered = font.render(text, True, (red, green, blue))
        rendered.set_alpha(alpha)
        return rendered

    glyphs: list[pygame.Surface] = []

    for character in text:
        glyph = font.render(character, True, (red, green, blue))
        glyph.set_alpha(alpha)
        glyphs.append(glyph)

    width = sum(glyph.get_width() for glyph in glyphs)
    width += letter_spacing * max(0, len(glyphs) - 1)

    height = max(glyph.get_height() for glyph in glyphs)

    rendered = pygame.Surface(
        (max(1, width), max(1, height)),
        pygame.SRCALPHA,
    )

    x = 0

    for glyph in glyphs:
        rendered.blit(glyph, (x, 0))
        x += glyph.get_width() + letter_spacing

    return rendered


def draw_figma_text(
    screen: pygame.Surface,
    text_spec: dict[str, Any] | None,
    *,
    opacity_multiplier: float = 1.0,
) -> None:
    if text_spec is None:
        return

    rect = figma_rect(text_spec["rect"])
    font = _load_figma_font(text_spec)

    text = _apply_text_case(
        str(text_spec.get("text", "")),
        str(text_spec.get("text_case", "ORIGINAL")),
    )

    # Только переносы, реально существующие в Figma/JSON.
    # Автоматического wrap_text здесь намеренно нет.
    lines = text.split("\n")

    color_data = text_spec.get("color", {})
    alpha = round(
        color_data.get("a", 255) * max(0.0, min(1.0, opacity_multiplier))
    )

    color = (
        color_data.get("r", 255),
        color_data.get("g", 255),
        color_data.get("b", 255),
        alpha,
    )

    line_height = _line_height_pixels(text_spec, font)
    letter_spacing = _letter_spacing_pixels(text_spec)

    horizontal_alignment = str(
        text_spec.get("horizontal_align", "LEFT")
    ).upper()

    vertical_alignment = str(
        text_spec.get("vertical_align", "TOP")
    ).upper()

    total_height = line_height * len(lines)

    if vertical_alignment == "CENTER":
        start_y = rect.centery - total_height // 2
    elif vertical_alignment == "BOTTOM":
        start_y = rect.bottom - total_height
    else:
        start_y = rect.top

    previous_clip = screen.get_clip()
    screen.set_clip(previous_clip.clip(rect))

    try:
        for line_index, line in enumerate(lines):
            rendered = _render_line(
                font,
                line,
                color,
                letter_spacing,
            )

            if horizontal_alignment == "CENTER":
                x = rect.centerx - rendered.get_width() // 2
            elif horizontal_alignment == "RIGHT":
                x = rect.right - rendered.get_width()
            else:
                x = rect.left

            line_y = start_y + line_index * line_height
            y = line_y + (line_height - rendered.get_height()) // 2

            screen.blit(rendered, (x, y))
    finally:
        screen.set_clip(previous_clip)