import pygame

from presentation.hud import wrap_text

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


def draw_act_two_trade_window(
    screen,
    sprites,
    layout,
    fonts,
    mouse_position,
):
    background = layout["background"]

    screen.blit(
        sprites["act_two_trade_background"],
        (background["x"], background["y"]),
    )

    for slot_name, item_id in DEFAULT_TRADER_STOCK.items():
        slot = layout["slots"].get(slot_name)

        if slot is None or slot["icon"] is None:
            continue

        item = TRADER_ITEMS[item_id]
        icon_layout = slot["icon"]

        icon_rectangle = pygame.Rect(
            icon_layout["x"],
            icon_layout["y"],
            icon_layout["width"],
            icon_layout["height"],
        )

        icon = _get_scaled_icon(
            sprites,
            item.sprite_name,
            icon_rectangle.size,
        )

        screen.blit(icon, icon_rectangle)
        name_rectangle = _layout_rectangle(slot["name"])
        price_rectangle = _layout_rectangle(slot["price"])

        name_surface = fonts["trade_name"].render(
            item.name,
            True,
            (218, 211, 197),
        )
        screen.blit(
            name_surface,
            name_surface.get_rect(center=name_rectangle.center),
        )

        price_surface = fonts["trade_price"].render(
            str(item.price),
            True,
            (218, 211, 197),
        )
        description_rectangle = _layout_rectangle(
            slot["description"]
        )
        buy_rectangle = _layout_rectangle(slot["buy_hitbox"])
        slot_rectangle = _layout_rectangle(slot["rect"])

        hovered = (
                mouse_position is not None
                and buy_rectangle.collidepoint(mouse_position)
        )

        if hovered:
            highlight = pygame.Surface(
                slot_rectangle.size,
                pygame.SRCALPHA,
            )
            highlight.fill((225, 174, 77, 28))

            screen.blit(
                highlight,
                slot_rectangle.topleft,
            )

            pygame.draw.rect(
                screen,
                (225, 174, 77),
                slot_rectangle,
                width=1,
                border_radius=3,
            )
        description_font = fonts["trade_description"]

        description_lines = wrap_text(
            description_font,
            item.description,
            description_rectangle.width,
        )

        line_height = description_font.get_linesize()
        maximum_lines = max(
            1,
            description_rectangle.height // line_height,
        )
        description_lines = description_lines[:maximum_lines]

        total_height = len(description_lines) * line_height
        line_y = description_rectangle.centery - total_height // 2

        for line in description_lines:
            line_surface = description_font.render(
                line,
                True,
                (166, 157, 157),
            )
            screen.blit(
                line_surface,
                line_surface.get_rect(
                    midtop=(description_rectangle.centerx, line_y)
                ),
            )
            line_y += line_height
        screen.blit(
            price_surface,
            price_surface.get_rect(center=price_rectangle.center),
        )


def _layout_rectangle(data):
    return pygame.Rect(
        data["x"],
        data["y"],
        data["width"],
        data["height"],
    )


def get_act_two_trade_buy_rectangles(layout):
    rectangles = {}

    for slot_name in DEFAULT_TRADER_STOCK:
        slot = layout["slots"].get(slot_name)

        if slot is None or slot["buy_hitbox"] is None:
            continue

        rectangles[slot_name] = _layout_rectangle(
            slot["buy_hitbox"]
        )

    return rectangles
