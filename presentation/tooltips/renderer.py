import pygame

from presentation.figma_ui import get_figma_font
from presentation.tooltips.model import TooltipContent


_TOOLTIP_MAX_TEXT_WIDTH = 310
_TOOLTIP_PADDING = 14
_TOOLTIP_OFFSET = 16
_TOOLTIP_TITLE_GAP = 8
_TOOLTIP_LINE_GAP = 4

_TITLE_FONT_SPEC = {
    "font": {
        "family": "Ubuntu Mono",
        "style": "Medium",
        "size": 15,
    },
}

_BODY_FONT_SPEC = {
    "font": {
        "family": "Ubuntu Mono",
        "style": "Regular",
        "size": 13,
    },
}


def _wrap_text(font, text, maximum_width):
    words = text.split()

    if not words:
        return [""]

    lines = []
    current_line = words[0]

    for word in words[1:]:
        candidate = f"{current_line} {word}"

        if font.size(candidate)[0] <= maximum_width:
            current_line = candidate
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def _wrapped_lines(font, lines, maximum_width=_TOOLTIP_MAX_TEXT_WIDTH):
    wrapped = []

    for line in lines:
        wrapped.extend(
            _wrap_text(
                font,
                line,
                maximum_width,
            )
        )

    return wrapped


def _tooltip_rectangle(
    screen,
    anchor,
    width,
    height,
    scale=1.0,
):
    screen_rectangle = screen.get_rect()
    offset = round(_TOOLTIP_OFFSET * scale)
    margin = max(1, round(8 * scale))
    left = anchor[0] + offset
    top = anchor[1] + offset

    if left + width > screen_rectangle.right - margin:
        left = anchor[0] - width - offset

    if top + height > screen_rectangle.bottom - margin:
        top = anchor[1] - height - offset

    rectangle = pygame.Rect(
        left,
        top,
        width,
        height,
    )
    rectangle.clamp_ip(
        screen_rectangle.inflate(-margin * 2, -margin * 2)
    )
    return rectangle


def draw_tooltip(
    screen,
    content,
    anchor,
    *,
    scale=1.0,
):
    if anchor is None:
        return

    padding = round(_TOOLTIP_PADDING * scale)
    title_gap = round(_TOOLTIP_TITLE_GAP * scale)
    line_gap = round(_TOOLTIP_LINE_GAP * scale)
    title_font = get_figma_font({
        "font": {**_TITLE_FONT_SPEC["font"], "size": max(1, round(15 * scale))},
    })
    body_font = get_figma_font({
        "font": {**_BODY_FONT_SPEC["font"], "size": max(1, round(13 * scale))},
    })

    body_lines = _wrapped_lines(
        body_font,
        content.lines,
        max(1, round(_TOOLTIP_MAX_TEXT_WIDTH * scale)),
    )

    title_surface = title_font.render(
        content.title,
        True,
        content.accent,
    )
    body_surfaces = [
        body_font.render(
            line,
            True,
            (220, 213, 202),
        )
        for line in body_lines
    ]

    content_width = max(
        [title_surface.get_width()]
        + [surface.get_width() for surface in body_surfaces]
    )
    body_height = (
        len(body_surfaces) * body_font.get_linesize()
        + max(0, len(body_surfaces) - 1) * line_gap
    )

    width = content_width + padding * 2
    height = (
        padding
        + title_surface.get_height()
        + title_gap
        + body_height
        + padding
    )

    rectangle = _tooltip_rectangle(
        screen,
        anchor,
        width,
        height,
        scale,
    )

    shadow = pygame.Surface(
        (width + 8, height + 8),
        pygame.SRCALPHA,
    )
    pygame.draw.rect(
        shadow,
        (0, 0, 0, 145),
        pygame.Rect(8, 8, width, height),
        border_radius=7,
    )
    screen.blit(
        shadow,
        (rectangle.x - 4, rectangle.y - 4),
    )

    panel = pygame.Surface(
        rectangle.size,
        pygame.SRCALPHA,
    )
    pygame.draw.rect(
        panel,
        (13, 12, 16, 246),
        panel.get_rect(),
        border_radius=7,
    )
    pygame.draw.rect(
        panel,
        (*content.accent, 220),
        panel.get_rect(),
        width=2,
        border_radius=7,
    )

    panel.blit(
        title_surface,
        (
            padding,
            padding,
        ),
    )

    line_y = (
        padding
        + title_surface.get_height()
        + title_gap
    )

    for surface in body_surfaces:
        panel.blit(
            surface,
            (padding, line_y),
        )
        line_y += (
            body_font.get_linesize()
            + line_gap
        )

    screen.blit(panel, rectangle)
