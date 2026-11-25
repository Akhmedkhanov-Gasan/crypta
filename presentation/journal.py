from presentation.figma_ui import figma_rect, get_figma_font
from presentation.text import wrap_text


def scroll_journal(layout, messages, ratio, direction, *, inset=False):
    viewport = figma_rect(layout["viewport"])
    template = layout["row_template"]
    text = template["text"]
    text_rect = figma_rect(text["rect"])
    separator = figma_rect(template["separator"]["rect"])
    font = get_figma_font(text)
    line_height = max(1, font.get_linesize())
    width = text_rect.width
    if inset:
        width = min(width, viewport.width - max(0, text_rect.x - viewport.x))
    gap = max(0, separator.top - text_rect.bottom)
    height = sum(
        max(1, len(wrap_text(font, str(message), max(1, width)))) * line_height + gap + separator.height
        for message in messages
    )
    maximum = max(0, height - viewport.height)
    if maximum == 0:
        return 1.0
    return max(0.0, min(1.0, ratio + direction * line_height / maximum))
