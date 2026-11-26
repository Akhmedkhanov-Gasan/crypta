import pygame

from presentation.figma_ui import figma_rect


def map_rectangle(layout, full=False):
    return figma_rect(layout["cartography"]["full_map" if full else "minimap"]["frame"])


def map_content_rectangle(layout, full=False):
    panel = map_rectangle(layout, full)
    minimum = round(12 * layout["frame"]["width"] / 1280)
    return panel.inflate(-max(minimum, round(panel.width * 0.07)), -max(minimum, round(panel.height * 0.12)))


def map_viewport(layout, full=False):
    content = map_content_rectangle(layout, full)
    if full:
        spacing = round(36 * layout["frame"]["width"] / 1280)
        content.top += spacing
        content.height -= spacing * 2
    return content


def close_rectangle(layout):
    content = map_content_rectangle(layout, True)
    scale = layout["frame"]["width"] / 1280
    size = max(1, round(22 * scale))
    margin = round(4 * scale)
    return pygame.Rect(content.right - size - margin, content.top + margin, size, size)
