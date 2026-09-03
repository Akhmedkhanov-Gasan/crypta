import json
from pathlib import Path

import pygame
import resource_store as resources

from acts.act_two.bloody_altar import (
    BLOODY_PACT_ORDER,
    bloody_pact_is_available,
    cancel_bloody_altar,
    confirm_bloody_pact,
    select_bloody_pact,
)
from presentation.figma_ui import draw_figma_text
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import GAME_HEIGHT, GAME_WIDTH, TILE_SIZE


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ALTAR_BLOOD_FRAME_DURATION_MS = 200
_scaled_icon_cache = {}


def load_bloody_altar_layout():
    path = (
        _PROJECT_ROOT
        / "assets"
        / "ui"
        / "layouts"
        / "act_2"
        / "bloody_altar.json"
    )
    with resources.open_text(path, encoding="utf-8") as file:
        return json.load(file)


def _rect(data):
    return pygame.Rect(
        data["x"],
        data["y"],
        data["width"],
        data["height"],
    )


def get_bloody_altar_option_rectangles(layout):
    return {
        pact_id: _rect(option["hitbox"])
        for pact_id, option in layout["options"].items()
    }


def get_bloody_altar_confirm_rectangle(layout):
    return _rect(layout["confirm"]["hitbox"])


def get_bloody_altar_close_rectangle(layout):
    return _rect(layout["close_hitbox"])

def handle_bloody_altar_event(
    event,
    game_state,
    layout,
    mouse_position,
):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            cancel_bloody_altar(game_state)
        elif event.key in (
            pygame.K_1,
            pygame.K_2,
            pygame.K_3,
            pygame.K_4,
        ):
            select_bloody_pact(
                game_state,
                BLOODY_PACT_ORDER[event.key - pygame.K_1],
            )
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            confirm_bloody_pact(game_state)
        return

    if event.type != pygame.MOUSEBUTTONDOWN:
        return
    if event.button == 3:
        cancel_bloody_altar(game_state)
        return
    if event.button != 1 or mouse_position is None:
        return

    if get_bloody_altar_close_rectangle(layout).collidepoint(
            mouse_position
    ):
        cancel_bloody_altar(game_state)
        return

    clicked_pact_id = next(
        (
            pact_id
            for pact_id, rectangle in (
                get_bloody_altar_option_rectangles(layout).items()
            )
            if rectangle.collidepoint(mouse_position)
        ),
        None,
    )
    if clicked_pact_id is not None:
        select_bloody_pact(game_state, clicked_pact_id)
    elif get_bloody_altar_confirm_rectangle(layout).collidepoint(
        mouse_position
    ):
        confirm_bloody_pact(game_state)


def draw_bloody_altar_object(
    screen,
    altar,
    sprites,
    visible_cells,
    current_time,
):
    if altar is None or (altar.column, altar.row) not in visible_cells:
        return

    position = (
        MAP_OFFSET_X + altar.column * TILE_SIZE,
        MAP_OFFSET_Y + altar.row * TILE_SIZE,
    )
    altar_sprite = sprites["bloody_altar_base"]
    if altar.claimed:
        altar_sprite = altar_sprite.copy()
        altar_sprite.set_alpha(145)
    screen.blit(altar_sprite, position)

    if not altar.claimed:
        blood_frame_index = (
            current_time // _ALTAR_BLOOD_FRAME_DURATION_MS
        ) % 4
        screen.blit(
            sprites[f"bloody_altar_blood_{blood_frame_index}"],
            position,
        )


def _scaled_icon(sprites, pact_id, size):
    key = (pact_id, size)
    if key not in _scaled_icon_cache:
        _scaled_icon_cache[key] = pygame.transform.smoothscale(
            sprites[f"bloody_pact_{pact_id}"],
            size,
        )
    return _scaled_icon_cache[key]


def draw_bloody_altar_window(
    screen,
    game_state,
    sprites,
    layout,
    mouse_position,
):
    veil = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
    veil.fill((3, 0, 2, 215))
    screen.blit(veil, (0, 0))

    window_rect = _rect(layout["background"])
    screen.blit(sprites["bloody_altar_window"], window_rect)

    draw_figma_text(
        screen,
        layout["title"],
    )

    pending_id = game_state.bloody_altar_pending_id
    for pact_id, option in layout["options"].items():
        card_rect = _rect(option["card"])
        hitbox = _rect(option["hitbox"])
        available = bloody_pact_is_available(game_state.player, pact_id)
        hovered = bool(
            available
            and mouse_position is not None
            and hitbox.collidepoint(mouse_position)
        )
        selected = pending_id == pact_id

        card = pygame.Surface(card_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            card,
            (45, 43, 44, 225 if available else 150),
            card.get_rect(),
            border_radius=12,
        )
        pygame.draw.rect(
            card,
            (
                (195, 42, 45)
                if selected
                else (138, 48, 48)
                if hovered
                else (75, 69, 70)
            ),
            card.get_rect(),
            3 if selected else 1,
            border_radius=12,
        )
        screen.blit(card, card_rect)

        icon_rect = _rect(option["icon"])
        icon = _scaled_icon(sprites, pact_id, icon_rect.size)
        if not available:
            icon = icon.copy()
            icon.set_alpha(80)
        screen.blit(icon, icon_rect)

        text_opacity = 1.0 if available else 0.45

        draw_figma_text(
            screen,
            option["name"],
            opacity_multiplier=text_opacity,
        )

        draw_figma_text(
            screen,
            option["reward"],
            opacity_multiplier=text_opacity,
        )

        if available:
            sacrifice_spec = option["sacrifice"]
        else:
            sacrifice_spec = (
                    option.get("sacrifice_disabled")
                    or option["sacrifice"]
            )

        draw_figma_text(
            screen,
            sacrifice_spec,
        )

    button_rect = _rect(layout["confirm"]["button"])
    button = sprites["bloody_altar_confirm_button"].copy()
    confirm_hitbox = get_bloody_altar_confirm_rectangle(layout)
    confirm_hovered = bool(
        pending_id is not None
        and mouse_position is not None
        and confirm_hitbox.collidepoint(mouse_position)
    )
    if pending_id is None:
        button.set_alpha(95)
    elif confirm_hovered:
        button.fill((34, 12, 8, 0), special_flags=pygame.BLEND_RGBA_ADD)
    screen.blit(button, button_rect)


__all__ = [
    "draw_bloody_altar_object",
    "draw_bloody_altar_window",
    "get_bloody_altar_confirm_rectangle",
    "get_bloody_altar_option_rectangles",
    "handle_bloody_altar_event",
    "load_bloody_altar_layout",
    "get_bloody_altar_close_rectangle",
]
