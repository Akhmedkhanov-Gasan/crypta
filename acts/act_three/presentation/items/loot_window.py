from functools import lru_cache

import pygame

from acts.act_three.items.inventory import ORE_ITEM_NAMES
from acts.act_three.items.special import SPECIAL_ITEM_NAMES
from acts.act_three.trader_catalog import TRADER_ITEMS, TRADER_SELL_ITEMS
from presentation.figma_ui import get_figma_font
from presentation.text import fit_text_to_width
from presentation.tooltips.highlights import draw_selection_highlight


def _font(family, size, scale):
    return get_figma_font({"font": {"family": family, "style": "Regular", "size": max(1, round(size * scale))}})


def _item_category(item):
    if item.kind in TRADER_ITEMS:
        return "Consumable"
    if item.kind in ORE_ITEM_NAMES:
        return "Ore"
    if item.kind in TRADER_SELL_ITEMS:
        return "Trade goods"
    if item.kind in SPECIAL_ITEM_NAMES:
        return "Special item"
    return "Key" if item.kind == "key" else "Item"


@lru_cache(maxsize=24)
def _background(size, scale):
    panel = pygame.Surface(size, pygame.SRCALPHA)
    width, height = size
    stroke = max(1, round(scale))
    cut = max(2, round(8 * scale))
    corners = (
        (cut, 0), (width - cut - 1, 0), (width - 1, cut),
        (width - 1, height - cut - 1), (width - cut - 1, height - 1),
        (cut, height - 1), (0, height - cut - 1), (0, cut),
    )
    pygame.draw.polygon(panel, (10, 10, 10), corners)
    for y in range(cut, height - cut):
        light = 13 + round(6 * (1 - y / max(1, height - 1)))
        pygame.draw.line(panel, (light, light, light), (stroke, y), (width - stroke - 1, y))
    pygame.draw.polygon(panel, (81, 81, 81), corners, width=stroke)
    inner = panel.get_rect().inflate(-6 * stroke, -6 * stroke)
    pygame.draw.rect(panel, (35, 35, 35), inner, width=stroke, border_radius=cut)
    for y in (stroke, height - stroke - 1):
        pygame.draw.line(panel, (112, 112, 112), (cut, y), (width - cut - 1, y), stroke)
    return panel


def _divider(screen, panel, y, scale):
    inset = round(18 * scale)
    middle = panel.centerx
    radius = max(1, round(3 * scale))
    pygame.draw.line(screen, (56, 56, 56), (panel.left + inset, y), (panel.right - inset, y))
    pygame.draw.polygon(screen, (112, 112, 112), (
        (middle - radius, y), (middle, y - radius),
        (middle + radius, y), (middle, y + radius),
    ))


def draw_loot_window(screen, items, selected, panel, close_button, rows, sprites, *, scale=1.0):
    def px(value):
        return max(1, round(value * scale))

    shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 165))
    screen.blit(shade, (0, 0))
    shadow = pygame.Surface(panel.inflate(px(16), px(16)).size, pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 150), shadow.get_rect(), border_radius=px(10))
    screen.blit(shadow, (panel.x - px(4), panel.y + px(4)))
    screen.blit(_background(panel.size, scale), panel)

    title_font = _font("Asul", 20, scale)
    text_font = _font("Asul", 16, scale)
    small_font = _font("Ubuntu Mono", 12, scale)
    controls_font = _font("Ubuntu Mono", 13, scale)
    screen.blit(title_font.render("GROUND LOOT", True, (217, 217, 217)), (panel.x + px(20), panel.y + px(8)))
    subtitle = f"{len(items)} {'item' if len(items) == 1 else 'items'} in this pile"
    screen.blit(small_font.render(subtitle, True, (128, 128, 128)), (panel.x + px(21), panel.y + px(33)))
    _divider(screen, panel, panel.y + px(49), scale)

    pygame.draw.rect(screen, (24, 24, 24), close_button, border_radius=px(3))
    pygame.draw.rect(screen, (73, 73, 73), close_button, width=px(1), border_radius=px(3))
    cross = close_button.inflate(-px(18), -px(18))
    pygame.draw.line(screen, (177, 177, 177), cross.topleft, cross.bottomright, px(1))
    pygame.draw.line(screen, (177, 177, 177), cross.topright, cross.bottomleft, px(1))

    for index, rectangle in rows:
        active = index == selected
        item = items[index]
        pygame.draw.rect(screen, (24, 24, 24) if active else (17, 17, 17), rectangle, border_radius=px(4))
        pygame.draw.rect(screen, (49, 49, 49) if active else (30, 30, 30), rectangle, width=px(1), border_radius=px(4))
        if active:
            draw_selection_highlight(screen, rectangle, radius=px(4))
            marker = pygame.Rect(rectangle.x + px(2), rectangle.y + px(12), px(2), rectangle.height - px(24))
            pygame.draw.rect(screen, (155, 155, 155), marker)

        icon_box = pygame.Rect(rectangle.x + px(9), rectangle.centery - px(24), px(48), px(48))
        pygame.draw.rect(screen, (9, 9, 9), icon_box, border_radius=px(3))
        pygame.draw.rect(screen, (89, 89, 89) if active else (53, 53, 53), icon_box, width=px(1), border_radius=px(3))
        source = sprites.get(item.sprite_name)
        if source is not None:
            fitted = source.get_rect().fit(icon_box.inflate(-px(6), -px(6)))
            image = source if source.get_size() == fitted.size else pygame.transform.smoothscale(source, fitted.size)
            screen.blit(image, fitted)

        left = rectangle.x + px(72)
        width = max(1, rectangle.right - left - px(14))
        name = fit_text_to_width(text_font, item.name, width)
        screen.blit(text_font.render(name, True, (220, 220, 220) if active else (176, 176, 176)), (left, rectangle.y + px(10)))
        screen.blit(small_font.render(_item_category(item), True, (131, 131, 131) if active else (95, 95, 95)), (left, rectangle.y + px(36)))

    if len(items) > len(rows):
        track = pygame.Rect(panel.right - px(10), rows[0][1].top, px(3), rows[-1][1].bottom - rows[0][1].top)
        pygame.draw.rect(screen, (36, 36, 36), track)
        height = min(track.height, max(px(12), round(track.height * len(rows) / len(items))))
        thumb = pygame.Rect(track.x, track.y + round((track.height - height) * selected / (len(items) - 1)), track.width, height)
        pygame.draw.rect(screen, (116, 116, 116), thumb)

    _divider(screen, panel, panel.bottom - px(57), scale)
    for text, y, color in (
        ("W/S / arrows: select   Space / click: take", panel.bottom - px(46), (175, 175, 175)),
        (f"{selected + 1}/{len(items)}   R: take all   G / Esc: close", panel.bottom - px(25), (127, 127, 127)),
    ):
        label = fit_text_to_width(controls_font, text, panel.width - px(40))
        screen.blit(controls_font.render(label, True, color), (panel.x + px(20), y))


def draw_native_loot_overlay(target, game_state, window, assets, fonts, current_time):
    from acts.act_three.presentation.pickup_feedback import draw_pickup_feedback
    from presentation.ground_items import draw_ground_item_window
    from settings import GAME_HEIGHT, GAME_WIDTH

    scale = min(target.get_width() / GAME_WIDTH, target.get_height() / GAME_HEIGHT)
    draw_ground_item_window(
        target, game_state, window, assets["ground_item_window_sprites"], fonts, current_time,
        scale=scale,
    )
    draw_pickup_feedback(target, game_state, window, current_time, show_prompt=False, scale=scale)
