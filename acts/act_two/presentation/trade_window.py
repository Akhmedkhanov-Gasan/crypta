import pygame

from presentation.figma_ui import (
    draw_figma_text,
    figma_rect,
    get_figma_font,
)
from presentation.hud import (
    fit_text_to_width,
    wrap_text,
)

from acts.act_two.trader_catalog import (
    DEFAULT_TRADER_STOCK,
    TRADER_ITEMS,
)

_scaled_icon_cache = {}


def _get_scaled_icon(sprites, sprite_name, size):
    cache_key = (sprite_name, size)

    if cache_key not in _scaled_icon_cache:
        _scaled_icon_cache[cache_key] = pygame.transform.smoothscale(
            sprites[sprite_name],
            size,
        )

    return _scaled_icon_cache[cache_key]

def _draw_dynamic_text(
    screen,
    text_spec,
    value,
):
    runtime_spec = {
        **text_spec,
        "text": str(value),
    }

    draw_figma_text(
        screen,
        runtime_spec,
    )


def _draw_wrapped_text(
    screen,
    text_spec,
    value,
):
    rectangle = figma_rect(text_spec["rect"])
    font = get_figma_font(text_spec)

    lines = wrap_text(
        font,
        str(value),
        rectangle.width,
    ) or [""]

    line_height = max(
        1,
        font.get_linesize(),
    )

    maximum_lines = max(
        1,
        rectangle.height // line_height,
    )

    visible_lines = lines[:maximum_lines]

    if len(lines) > maximum_lines:
        visible_lines[-1] = fit_text_to_width(
            font,
            visible_lines[-1] + "...",
            rectangle.width,
        )

    _draw_dynamic_text(
        screen,
        text_spec,
        "\n".join(visible_lines),
    )


def draw_act_two_trade_window(
    screen,
    sprites,
    layout,
    fonts,
    mouse_position,
):
    background_rectangle = figma_rect(
        layout["background"]
    )

    background = _get_scaled_icon(
        sprites,
        "act_two_trade_background",
        background_rectangle.size,
    )

    screen.blit(
        background,
        background_rectangle,
    )

    for slot_name, item_id in DEFAULT_TRADER_STOCK.items():
        slot = layout["slots"].get(slot_name)

        if slot is None:
            continue

        item = TRADER_ITEMS[item_id]

        slot_rectangle = figma_rect(
            slot["rect"]
        )
        icon_rectangle = figma_rect(
            slot["icon"]
        )
        buy_rectangle = figma_rect(
            slot["buy_hitbox"]
        )

        hovered = (
            mouse_position is not None
            and buy_rectangle.collidepoint(
                mouse_position
            )
        )

        if hovered:
            highlight = pygame.Surface(
                slot_rectangle.size,
                pygame.SRCALPHA,
            )

            highlight.fill(
                (225, 174, 77, 28)
            )

            screen.blit(
                highlight,
                slot_rectangle,
            )

            pygame.draw.rect(
                screen,
                (225, 174, 77),
                slot_rectangle,
                width=1,
                border_radius=3,
            )

        icon = _get_scaled_icon(
            sprites,
            item.sprite_name,
            icon_rectangle.size,
        )

        screen.blit(
            icon,
            icon_rectangle,
        )

        _draw_dynamic_text(
            screen,
            slot["name"],
            item.name,
        )

        _draw_wrapped_text(
            screen,
            slot["description"],
            item.description,
        )

        _draw_dynamic_text(
            screen,
            slot["price"],
            item.price,
        )


def get_act_two_trade_buy_rectangles(layout):
    return {
        slot_name: figma_rect(
            layout["slots"][slot_name]["buy_hitbox"]
        )
        for slot_name in DEFAULT_TRADER_STOCK
        if slot_name in layout["slots"]
    }

def get_act_two_trade_close_rectangle(layout):
    return figma_rect(layout["close_hitbox"])
