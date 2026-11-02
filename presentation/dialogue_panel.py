from functools import lru_cache

import pygame
import resource_store as resources

from presentation.layout import FONT_ROOT
from presentation.text import wrap_text


@lru_cache(maxsize=2)
def _readable_font(act):
    path = FONT_ROOT / "Pixelify_Sans/PixelifySans-Regular.ttf" if act == 2 else FONT_ROOT / "AtkinsonHyperlegible-Regular.ttf"
    return resources.load_font(str(path), 24)


@lru_cache(maxsize=1)
def _act_one_title_font():
    return resources.load_font(str(FONT_ROOT / "AtkinsonHyperlegible-Bold.ttf"), 24)


@lru_cache(maxsize=2)
def _hint_font(act):
    path = FONT_ROOT / "Pixelify_Sans/PixelifySans-Regular.ttf" if act == 2 else FONT_ROOT / "AtkinsonHyperlegible-Regular.ttf"
    return resources.load_font(str(path), 17)


def draw_fixed_dialogue(screen, title_font, text_font, speaker, text, opacity=1.0, act=2, visible_characters=None):
    if act == 2:
        from acts.act_two.presentation.dialogue_panel import draw_act_two_dialogue

        if draw_act_two_dialogue(screen, speaker, text, opacity, visible_characters):
            return
    if act == 1:
        title_font = _act_one_title_font()
        text_font = _readable_font(1)
    elif text_font.get_height() < 24:
        text_font = _readable_font(act)
    width = min(1000, screen.get_width() - 80)
    height = 166
    panel = pygame.Surface((width, height), pygame.SRCALPHA)
    accent = (154, 123, 80) if act == 2 else (139, 146, 158)
    pygame.draw.rect(panel, (5, 7, 11, 242), panel.get_rect(), border_radius=6)
    pygame.draw.rect(panel, (*accent, 210), panel.get_rect(), 2, border_radius=6)
    pygame.draw.line(panel, (*accent, 150), (28, 44), (width - 28, 44))
    name = title_font.render(speaker, True, accent)
    if act != 1 and name.get_height() > 24:
        name = pygame.transform.smoothscale(name, (round(name.get_width() * 24 / name.get_height()), 24))
    panel.blit(name, name.get_rect(center=(width // 2, 24)))
    lines = wrap_text(text_font, text, width - 72)
    line_height = text_font.get_linesize()
    y = 56
    remaining = len(text) if visible_characters is None else max(0, visible_characters)
    for line in lines:
        rendered = text_font.render(line[:remaining], True, (224, 218, 205))
        panel.blit(rendered, (round((width - text_font.size(line)[0]) / 2), y))
        remaining = max(0, remaining - len(line) - 1)
        y += line_height
    hint = _hint_font(act).render("SPACE / CLICK - SKIP TEXT", True, (164, 160, 153))
    panel.blit(hint, hint.get_rect(midbottom=(width // 2, height - 12)))
    panel.set_alpha(round(255 * max(0, min(1, opacity))))
    screen.blit(panel, panel.get_rect(midbottom=(screen.get_width() // 2, screen.get_height() - 22)))
