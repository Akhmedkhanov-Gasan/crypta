import pygame

from acts.act_three.awakening.assets import load_layouts
from acts.act_two.presentation.awakening import _draw_image, _draw_text
from presentation.figma_ui import draw_figma_rectangle, figma_rect


def selection_rectangles(parent="warrior"):
    choices = load_layouts()[parent]["subclass_choices"]
    return {key: figma_rect(choices["options"][key]["hitbox"]) for key in choices["order"]}


def draw_selection(screen, title_font, heading_font, text_font, assets, mouse_position, selected_subclass, player_class):
    layout = load_layouts()[player_class]
    color = layout["background"]["color"]
    screen.fill((color["r"], color["g"], color["b"]))
    if layout["screen_title"] is not None:
        _draw_text(screen, layout["screen_title"]["text"])
    choices = layout["subclass_choices"]
    for key in choices["order"]:
        option = choices["options"][key]
        _draw_image(screen, assets, option["card_background"])
        portrait = option["portrait_section"]
        draw_figma_rectangle(screen, portrait["background"])
        _draw_image(screen, assets, portrait["portrait"])
        _draw_text(screen, option["class_name"])
        _draw_text(screen, option["class_description"], wrap=True)
        for feature in (option["passive"], option["abilities"]["q"], option["abilities"]["f"]):
            _draw_image(screen, assets, feature["background"])
            _draw_image(screen, assets, feature["icon"])
            _draw_text(screen, feature["name"])
            _draw_text(screen, feature["description"], wrap=True)
        if mouse_position is not None and figma_rect(option["hitbox"]).collidepoint(mouse_position):
            rectangle = figma_rect(option["card_background"]["rect"])
            accent = option["class_name"]["color"]
            pygame.draw.rect(screen, (accent["r"], accent["g"], accent["b"]), rectangle.inflate(-10, -10), 2, border_radius=5)

