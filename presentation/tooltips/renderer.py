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


def _wrapped_lines(font, lines):
    wrapped = []

    for line in lines:
        wrapped.extend(
            _wrap_text(
                font,
                line,
                _TOOLTIP_MAX_TEXT_WIDTH,
            )
        )

    return wrapped


def _tooltip_rectangle(
    screen,
    anchor,
    width,
    height,
):
    screen_rectangle = screen.get_rect()
    left = anchor[0] + _TOOLTIP_OFFSET
    top = anchor[1] + _TOOLTIP_OFFSET

    if left + width > screen_rectangle.right - 8:
        left = anchor[0] - width - _TOOLTIP_OFFSET

    if top + height > screen_rectangle.bottom - 8:
        top = anchor[1] - height - _TOOLTIP_OFFSET

    rectangle = pygame.Rect(
        left,
        top,
        width,
        height,
    )
    rectangle.clamp_ip(
        screen_rectangle.inflate(-16, -16)
    )
    return rectangle


def draw_tooltip(
    screen,
    content,
    anchor,
):
    if anchor is None:
        return

    title_font = get_figma_font(_TITLE_FONT_SPEC)
    body_font = get_figma_font(_BODY_FONT_SPEC)

    body_lines = _wrapped_lines(
        body_font,
        content.lines,
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
        + max(0, len(body_surfaces) - 1) * _TOOLTIP_LINE_GAP
    )

    width = content_width + _TOOLTIP_PADDING * 2
    height = (
        _TOOLTIP_PADDING
        + title_surface.get_height()
        + _TOOLTIP_TITLE_GAP
        + body_height
        + _TOOLTIP_PADDING
    )

    rectangle = _tooltip_rectangle(
        screen,
        anchor,
        width,
        height,
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
            _TOOLTIP_PADDING,
            _TOOLTIP_PADDING,
        ),
    )

    line_y = (
        _TOOLTIP_PADDING
        + title_surface.get_height()
        + _TOOLTIP_TITLE_GAP
    )

    for surface in body_surfaces:
        panel.blit(
            surface,
            (_TOOLTIP_PADDING, line_y),
        )
        line_y += (
            body_font.get_linesize()
            + _TOOLTIP_LINE_GAP
        )

    screen.blit(panel, rectangle)
