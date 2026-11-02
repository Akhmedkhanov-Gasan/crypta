from functools import lru_cache

import pygame
import resource_store as resources

from acts.act_three.presentation.dialogue_layout import (
    dialogue_background, load_dialogue_layout,
)
from presentation.figma_ui import figma_rect
from presentation.dialogue_text import draw_dialogue_text as _draw_dialogue_text
from presentation.layout import ASSET_ROOT


SPEAKER_COLORS = {
    "old_man": (173, 166, 151),
    "assassin": (185, 70, 78),
    "archer": (124, 163, 98),
    "berserker": (210, 86, 62),
    "paladin": (190, 165, 111),
    "warlock": (172, 109, 204),
    "summoner": (88, 183, 189),
}


@lru_cache(maxsize=32)
def dialogue_portrait(speaker_id):
    if speaker_id == "old_man":
        paths = (ASSET_ROOT / "ui/act_3/awakening/old_man/portrait_old_man.png",)
    elif speaker_id in SPEAKER_COLORS:
        paths = (ASSET_ROOT / "act_3/player" / speaker_id / "portrait.png",)
    elif speaker_id:
        paths = (
            ASSET_ROOT / "act_3/npcs" / speaker_id / "portrait.png",
            ASSET_ROOT / "act_3/enemies" / speaker_id / "portrait.png",
        )
    else:
        return None
    path = next((path for path in paths if resources.is_file(path)), None)
    if path is None:
        return None
    image = resources.load_image(str(path)).convert_alpha()
    rectangle = figma_rect(load_dialogue_layout()["portrait_section"]["portrait"]["rect"])
    scale = min(rectangle.width / image.get_width(), rectangle.height / image.get_height())
    size = (max(1, round(image.get_width() * scale)), max(1, round(image.get_height() * scale)))
    transform = pygame.transform.scale if max(image.get_size()) <= 256 else pygame.transform.smoothscale
    return transform(image, size)


def draw_dialogue_panel(screen, fonts, speaker_id, speaker_name, text, visible_characters=None, opacity=1.0, close_label=None):
    if opacity <= 0:
        return
    layout = load_dialogue_layout()
    panel = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    background_spec = layout["dialog_background"]
    background = dialogue_background().copy()
    background.set_alpha(round(255 * background_spec.get("opacity", 1)))
    panel.blit(background, figma_rect(background_spec["rect"]))
    portrait_rect = figma_rect(layout["portrait_section"]["portrait"]["rect"])
    portrait = dialogue_portrait(speaker_id)
    if portrait is not None:
        portrait = portrait.copy()
        portrait.set_alpha(round(255 * layout["portrait_section"]["portrait"].get("opacity", 1)))
        panel.blit(portrait, portrait.get_rect(center=portrait_rect.center))
    _draw_dialogue_text(panel, layout["speaker_name"], speaker_name, color=SPEAKER_COLORS.get(speaker_id))
    _draw_dialogue_text(panel, layout["dialogue_text"], text, visible_characters)
    if layout.get("skip_text") is not None:
        _draw_dialogue_text(panel, layout["skip_text"], "SPACE / CLICK - SKIP TEXT", color=(142, 139, 133))
    panel.set_alpha(round(255 * max(0, min(1, opacity))))
    screen.blit(panel, (0, 0))
