import json
from functools import lru_cache
from pathlib import Path

import pygame

from presentation.figma_ui import draw_figma_text, figma_rect
from settings import GAME_HEIGHT, GAME_WIDTH


_PROJECT_ROOT = Path(__file__).resolve().parents[3]

_LAYOUT_FILENAMES = {
    "warrior": "RuneSelection_Warrior.json",
    "rogue": "RuneSelection_Rogue.json",
    "mage": "RuneSelection_Mage.json",
}


@lru_cache(maxsize=1)
def load_rune_selection_layouts():
    layout_directory = (
        _PROJECT_ROOT
        / "assets"
        / "ui"
        / "layouts"
        / "act_2"
        / "rune"
    )

    layouts = {}

    for player_class, filename in _LAYOUT_FILENAMES.items():
        path = layout_directory / filename

        with path.open(encoding="utf-8") as file:
            layout = json.load(file)

        if layout.get("player_class") != player_class:
            raise ValueError(
                f"Rune layout {filename} has wrong player_class."
            )

        layouts[player_class] = layout

    return layouts


def _layout_for_class(player_class):
    layout = load_rune_selection_layouts().get(player_class)

    if layout is None:
        raise ValueError(
            f"No rune selection layout for class: {player_class}"
        )

    return layout


def get_rune_selection_card_rectangles(player_class):
    layout = _layout_for_class(player_class)

    return {
        rune_id: figma_rect(option["hitbox"])
        for rune_id, option in layout["options"].items()
    }


def get_rune_selection_confirm_rectangle(player_class):
    layout = _layout_for_class(player_class)
    return figma_rect(layout["confirm"]["hitbox"])


def _option_accent_color(option):
    color = option["name"]["color"]

    return (
        color["r"],
        color["g"],
        color["b"],
    )


def draw_rune_selection(
    screen,
    game_state,
    fonts,
    sprites,
    mouse_position,
):
    del fonts

    player_class = game_state.player.player_class
    layout = _layout_for_class(player_class)

    veil = pygame.Surface(
        (GAME_WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA,
    )
    veil.fill((4, 3, 5, 215))
    screen.blit(veil, (0, 0))

    background_rect = figma_rect(layout["background"])
    screen.blit(
        sprites["rune_selection_background"],
        background_rect,
    )

    pending_id = game_state.rune_selection_pending_id

    for rune_id, option in layout["options"].items():
        card_rect = figma_rect(option["card"])
        hitbox = figma_rect(option["hitbox"])

        hovered = (
            mouse_position is not None
            and hitbox.collidepoint(mouse_position)
        )
        selected = pending_id == rune_id
        accent_color = _option_accent_color(option)

        card = pygame.Surface(
            card_rect.size,
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            card,
            (45, 43, 44, 225),
            card.get_rect(),
            border_radius=12,
        )
        screen.blit(card, card_rect)

        if hovered or selected:
            highlight = pygame.Surface(
                hitbox.size,
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                highlight,
                (
                    *accent_color,
                    225 if selected else 145,
                ),
                highlight.get_rect(),
                width=3 if selected else 2,
                border_radius=12,
            )
            screen.blit(highlight, hitbox)

        icon_rect = figma_rect(option["icon"])
        icon = sprites[f"{rune_id}_selection"]

        if icon.get_size() != icon_rect.size:
            raise ValueError(
                f"{rune_id} selection icon must be "
                f"{icon_rect.width}x{icon_rect.height}, "
                f"got {icon.get_width()}x{icon.get_height()}."
            )

        screen.blit(icon, icon_rect)

        draw_figma_text(
            screen,
            option["name"],
        )
        draw_figma_text(
            screen,
            option["description"],
        )

    button_rect = figma_rect(layout["confirm"]["button"])
    confirm_hitbox = get_rune_selection_confirm_rectangle(
        player_class
    )
    button = sprites["rune_selection_confirm_button"].copy()

    confirm_hovered = (
        pending_id is not None
        and mouse_position is not None
        and confirm_hitbox.collidepoint(mouse_position)
    )

    if pending_id is None:
        button.set_alpha(95)
    elif confirm_hovered:
        button.fill(
            (34, 12, 8, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )

    screen.blit(button, button_rect)


__all__ = [
    "draw_rune_selection",
    "get_rune_selection_card_rectangles",
    "get_rune_selection_confirm_rectangle",
    "load_rune_selection_layouts",
]