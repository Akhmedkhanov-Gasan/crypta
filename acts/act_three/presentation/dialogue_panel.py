from functools import lru_cache

import pygame
import resource_store as resources

from presentation.layout import ASSET_ROOT
from presentation.text import wrap_text
from settings import GAME_HEIGHT, GAME_WIDTH


SPEAKER_COLORS = {
    "old_man": (173, 166, 151),
    "assassin": (185, 70, 78),
    "archer": (124, 163, 98),
    "berserker": (210, 86, 62),
    "paladin": (190, 165, 111),
    "warlock": (172, 109, 204),
    "summoner": (88, 183, 189),
}

PANEL_WIDTH = 1080
PANEL_HEIGHT = 186
PORTRAIT_SIZE = 142
PANEL_FILL = (17, 16, 20)
TEXT_COLOR = (223, 215, 199)


@lru_cache(maxsize=7)
def dialogue_portrait(speaker_id):
    if speaker_id == "old_man":
        path = ASSET_ROOT / "ui/act_3/awakening/old_man/portrait_old_man.png"
    else:
        path = ASSET_ROOT / "act_3/player" / speaker_id / "portrait.png"
    image = resources.load_image(str(path)).convert_alpha()
    scale = min(PORTRAIT_SIZE / image.get_width(), PORTRAIT_SIZE / image.get_height())
    size = (max(1, round(image.get_width() * scale)), max(1, round(image.get_height() * scale)))
    transform = pygame.transform.scale if max(image.get_size()) <= 256 else pygame.transform.smoothscale
    return transform(image, size)


def draw_dialogue_panel(screen, fonts, speaker_id, speaker_name, text, visible_characters, opacity):
    if opacity <= 0:
        return
    accent = SPEAKER_COLORS[speaker_id]
    panel = pygame.Surface((PANEL_WIDTH, PANEL_HEIGHT), pygame.SRCALPHA)
    shape = (
        (12, 0), (PANEL_WIDTH - 12, 0), (PANEL_WIDTH, 12),
        (PANEL_WIDTH, PANEL_HEIGHT - 12), (PANEL_WIDTH - 12, PANEL_HEIGHT),
        (12, PANEL_HEIGHT), (0, PANEL_HEIGHT - 12), (0, 12),
    )
    pygame.draw.polygon(panel, PANEL_FILL, shape)
    pygame.draw.polygon(panel, (106, 101, 96), shape, 2)
    pygame.draw.rect(panel, (44, 41, 45), (8, 8, PANEL_WIDTH - 16, PANEL_HEIGHT - 16), 1)
    portrait_rect = pygame.Rect(22, 22, PORTRAIT_SIZE, PORTRAIT_SIZE)
    pygame.draw.rect(panel, (9, 9, 12), portrait_rect)
    pygame.draw.rect(panel, accent, portrait_rect, 1)
    portrait = dialogue_portrait(speaker_id)
    panel.blit(portrait, portrait.get_rect(center=portrait_rect.center))
    left = portrait_rect.right + 26
    width = PANEL_WIDTH - left - 32
    name = fonts["sidebar_heading"].render(speaker_name, True, accent)
    panel.blit(name, (left, 22))
    pygame.draw.line(panel, (66, 61, 66), (left, 55), (PANEL_WIDTH - 30, 55))
    pygame.draw.line(panel, accent, (left, 55), (left + 90, 55), 2)
    font = fonts["text"]
    lines = wrap_text(font, text, width)
    line_height = font.get_linesize() + 5
    if len(lines) * line_height > PANEL_HEIGHT - 82:
        raise ValueError(f"Act III dialogue exceeds its fixed panel: {text!r}")
    remaining = visible_characters
    for index, line in enumerate(lines):
        visible = line[:max(0, remaining)]
        if visible:
            rendered = font.render(visible, True, TEXT_COLOR)
            panel.blit(rendered, (left, 72 + index * line_height))
        remaining -= len(line) + 1
    panel.set_alpha(round(255 * max(0, min(1, opacity))))
    screen.blit(panel, ((GAME_WIDTH - PANEL_WIDTH) // 2, GAME_HEIGHT - PANEL_HEIGHT - 18))
