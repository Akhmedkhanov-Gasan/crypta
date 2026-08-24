import json
from pathlib import Path

import pygame

from acts.act_two.bloody_altar import (
    bloody_pact_is_available,
    cancel_bloody_altar,
    confirm_bloody_pact,
    select_bloody_pact,
)
from acts.act_two.bloody_altar_catalog import (
    BLOODY_PACTS,
    BLOODY_PACTS_BY_ID,
)
from presentation.hud import wrap_text
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import GAME_HEIGHT, GAME_WIDTH, TILE_SIZE


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ALTAR_FRAME_DURATION_MS = 180
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
    with path.open(encoding="utf-8") as file:
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
                BLOODY_PACTS[event.key - pygame.K_1].id,
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

    frame_index = (
        0
        if altar.claimed
        else (current_time // _ALTAR_FRAME_DURATION_MS) % 4
    )
    sprite = sprites[f"bloody_altar_{frame_index}"]
    if altar.claimed:
        sprite = sprite.copy()
        sprite.set_alpha(145)
    screen.blit(
        sprite,
        (
            MAP_OFFSET_X + altar.column * TILE_SIZE,
            MAP_OFFSET_Y + altar.row * TILE_SIZE,
        ),
    )


def _scaled_icon(sprites, pact_id, size):
    key = (pact_id, size)
    if key not in _scaled_icon_cache:
        _scaled_icon_cache[key] = pygame.transform.smoothscale(
            sprites[f"bloody_pact_{pact_id}"],
            size,
        )
    return _scaled_icon_cache[key]


def _draw_wrapped_text(
    screen,
    font,
    text,
    color,
    rectangle,
    line_height=None,
):
    lines = wrap_text(font, text, rectangle.width)
    line_height = line_height or font.get_linesize()
    block_height = len(lines) * line_height
    start_y = rectangle.centery - block_height // 2
    previous_clip = screen.get_clip()
    screen.set_clip(rectangle)
    for index, line in enumerate(lines):
        line_surface = font.render(line, True, color)
        screen.blit(
            line_surface,
            line_surface.get_rect(
                midtop=(
                    rectangle.centerx,
                    start_y + index * line_height,
                )
            ),
        )
    screen.set_clip(previous_clip)


def _draw_card_text(
    screen,
    fonts,
    pact,
    card_rect,
    name_color,
    reward_color,
    sacrifice_color,
    sacrifice_text=None,
):
    inset = 7
    name_font = fonts["bloody_altar_name"]
    body_font = fonts["bloody_altar_body"]
    name_height = name_font.get_linesize()
    name_rect = pygame.Rect(
        card_rect.x + inset,
        card_rect.y + 4,
        card_rect.width - inset * 2,
        name_height,
    )
    _draw_wrapped_text(
        screen,
        name_font,
        pact.name,
        name_color,
        name_rect,
    )

    body_rect = pygame.Rect(
        card_rect.x + inset,
        name_rect.bottom + 2,
        card_rect.width - inset * 2,
        card_rect.bottom - name_rect.bottom - 6,
    )
    reward_lines = wrap_text(body_font, pact.reward, body_rect.width)
    sacrifice_lines = wrap_text(
        body_font,
        sacrifice_text or pact.sacrifice,
        body_rect.width,
    )
    line_height = body_font.get_height() + 1
    gap = 3
    reward_height = len(reward_lines) * line_height
    sacrifice_height = len(sacrifice_lines) * line_height
    content_height = reward_height + gap + sacrifice_height
    content_y = body_rect.y + max(
        0,
        (body_rect.height - content_height) // 2,
    )
    reward_rect = pygame.Rect(
        body_rect.x,
        content_y,
        body_rect.width,
        reward_height,
    )
    sacrifice_rect = pygame.Rect(
        body_rect.x,
        reward_rect.bottom + gap,
        body_rect.width,
        sacrifice_height,
    )
    _draw_wrapped_text(
        screen,
        body_font,
        pact.reward,
        reward_color,
        reward_rect,
        line_height,
    )
    _draw_wrapped_text(
        screen,
        body_font,
        sacrifice_text or pact.sacrifice,
        sacrifice_color,
        sacrifice_rect,
        line_height,
    )


def draw_bloody_altar_window(
    screen,
    game_state,
    sprites,
    fonts,
    layout,
    mouse_position,
):
    veil = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
    veil.fill((3, 0, 2, 215))
    screen.blit(veil, (0, 0))

    window_rect = _rect(layout["window"])
    screen.blit(sprites["bloody_altar_window"], window_rect)
    _draw_wrapped_text(
        screen,
        fonts["heading"],
        "Choose wisely",
        (224, 207, 193),
        _rect(layout["title"]),
    )

    pending_id = game_state.bloody_altar_pending_id
    for pact_id, option in layout["options"].items():
        pact = BLOODY_PACTS_BY_ID[pact_id]
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

        name_color = (
            (225, 174, 77)
            if selected
            else (207, 197, 188)
            if available
            else (105, 97, 97)
        )
        _draw_card_text(
            screen,
            fonts,
            pact,
            card_rect,
            name_color,
            (196, 188, 180) if available else (92, 86, 86),
            (178, 48, 49) if available else (105, 62, 62),
            None if available else "Requires a bound rune.",
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
]
