from functools import lru_cache

import pygame

from acts.act_three.awakening.assets import load_layouts
from acts.act_three.awakening.selection_effects import draw_selection_card
from acts.act_two.presentation.awakening import _draw_image
from presentation.dialogue_text import _wrap_dialogue
from presentation.figma_layout import scale_figma_layout
from presentation.figma_ui import (
    _apply_text_case, _letter_spacing_pixels,
    draw_figma_rectangle, draw_figma_text, figma_rect, get_figma_font,
)


_OPTION_SURFACES = {}


@lru_cache(maxsize=12)
def _render_layout(parent, size):
    layout = load_layouts()[parent]
    scale = min(size[0] / layout["frame"]["width"], size[1] / layout["frame"]["height"])
    return scale_figma_layout(layout, scale), scale


def _draw_selection_text(screen, source_spec, offset=(0, 0), wrap=False):
    rectangle = figma_rect(source_spec["rect"]).move(offset)
    spec = {
        **source_spec,
        "rect": {"x": rectangle.x, "y": rectangle.y, "width": rectangle.width, "height": rectangle.height},
    }
    text = _apply_text_case(str(spec.get("text", "")), spec.get("text_case", "ORIGINAL"))
    if wrap:
        lines = _wrap_dialogue(get_figma_font(spec), text, rectangle.width, _letter_spacing_pixels(spec))
        text = "\n".join(lines)
    spec["text_case"] = "ORIGINAL"
    draw_figma_text(screen, spec, text_override=text)


def selection_rectangles(parent="warrior"):
    choices = load_layouts()[parent]["subclass_choices"]
    return {key: figma_rect(choices["options"][key]["card_background"]["rect"]) for key in choices["order"]}


def _option_surfaces(screen_size, assets, parent, key, option):
    identity = (parent, key, id(assets), screen_size)
    if identity not in _OPTION_SURFACES:
        if len(_OPTION_SURFACES) >= 12:
            _OPTION_SURFACES.clear()
        surface = pygame.Surface(screen_size, pygame.SRCALPHA)
        rectangle = figma_rect(option["card_background"]["rect"])
        _draw_image(surface, assets, option["card_background"])
        frame = surface.subsurface(rectangle).copy()
        portrait = option["portrait_section"]
        draw_figma_rectangle(surface, portrait["background"])
        _draw_image(surface, assets, portrait["portrait"])
        for feature in (option["passive"], option["abilities"]["q"], option["abilities"]["f"]):
            _draw_image(surface, assets, feature["background"])
            _draw_image(surface, assets, feature["icon"])
        _OPTION_SURFACES[identity] = (surface.subsurface(rectangle).copy(), frame)
    return _OPTION_SURFACES[identity]


def draw_selection(screen, title_font, heading_font, text_font, assets, mouse_position, selected_subclass, player_class, pressed_subclass=None):
    layout, render_scale = _render_layout(player_class, screen.get_size())
    color = layout["background"]["color"]
    screen.fill((color["r"], color["g"], color["b"]))
    title = layout["screen_title"]
    if title is not None:
        if "asset_key" in title:
            _draw_image(screen, assets, title)
        else:
            _draw_selection_text(screen, title["text"])
    choices = layout["subclass_choices"]
    for key in choices["order"]:
        option = choices["options"][key]
        rectangle = figma_rect(option["card_background"]["rect"])
        card, frame = _option_surfaces(screen.get_size(), assets, player_class, key, option)
        accent = option["class_name"]["color"]
        hovered = mouse_position is not None and rectangle.collidepoint(mouse_position)
        offset = draw_selection_card(
            screen, card, frame, rectangle, (accent["r"], accent["g"], accent["b"]),
            (player_class, key), hovered or selected_subclass == key, pressed_subclass == key,
            render_scale=render_scale,
        )
        _draw_selection_text(screen, option["class_name"], offset)
        _draw_selection_text(screen, option["class_description"], offset, wrap=True)
        for feature in (option["passive"], option["abilities"]["q"], option["abilities"]["f"]):
            _draw_selection_text(screen, feature["name"], offset)
            _draw_selection_text(screen, feature["description"], offset, wrap=True)

