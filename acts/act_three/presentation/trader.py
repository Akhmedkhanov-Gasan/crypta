import json
from functools import lru_cache

import pygame
import resource_store as resources

from acts.act_three.npcs import close_npc_dialog
from acts.act_three.presentation.trader_effects import (
    draw_trader_slot_effect,
    trader_press_offset,
)
from acts.act_three.trader import buy_trader_item
from acts.act_three.trader_catalog import TRADER_ITEMS, TRADER_SELL_ITEMS, TRADER_STOCK
from application.directional_input import CHORD_MOVEMENT_KEYS, movement_direction_for_key
from presentation.dialogue_text import draw_dialogue_text
from presentation.figma_ui import draw_figma_rectangle, figma_rect
from presentation.layout import PROJECT_ROOT


_FOCUS_COLOR = (195, 151, 88)


@lru_cache(maxsize=1)
def load_trader_layout():
    path = PROJECT_ROOT / "assets" / "ui" / "layouts" / "act_3" / "trader.json"
    with resources.open_text(path) as source:
        layout = json.load(source)
    if (
        layout.get("screen") != "trader"
        or layout.get("act") != 3
        or layout.get("schema_version") != 1
        or layout.get("coordinate_space") != "frame"
        or layout.get("frame", {}).get("width") != 1280
        or layout.get("frame", {}).get("height") != 720
    ):
        raise ValueError(f"Invalid Act III trader layout: {path}")
    return layout


@lru_cache(maxsize=64)
def _load_art(path, size, opacity):
    if not resources.is_file(path):
        return None
    sprite = pygame.transform.smoothscale(resources.load_image(path).convert_alpha(), size)
    if opacity != 1:
        sprite.set_alpha(round(255 * opacity))
    return sprite


def _draw_art(screen, spec):
    rectangle = figma_rect(spec["rect"])
    sprite = _load_art(spec["asset_path"], rectangle.size, spec.get("opacity", 1))
    if sprite is None:
        return False
    screen.blit(sprite, rectangle)
    return True


def _stock_rows(layout, tab):
    return zip(sorted(layout["trade_slots"].items()), TRADER_STOCK[tab])


def _slot_image(assets, slot_name, row, item_id, sell):
    cache = assets.setdefault("act_three_trader_slot_images", {})
    cache_key = slot_name, item_id, sell
    if cache_key in cache:
        return cache[cache_key]

    bounds = figma_rect(row["background"]["rect"])
    surface = pygame.Surface(bounds.size, pygame.SRCALPHA)

    def local_rect(rect):
        return {**rect, "x": rect["x"] - bounds.x, "y": rect["y"] - bounds.y}

    def local(spec):
        return {**spec, "rect": local_rect(spec["rect"])}

    if not _draw_art(surface, local(row["background"])):
        rectangle = surface.get_rect()
        pygame.draw.rect(surface, (29, 24, 24), rectangle, border_radius=8)
        pygame.draw.rect(surface, (107, 82, 63), rectangle, width=2, border_radius=8)
    draw_figma_rectangle(surface, local(row["icon_background"]))

    if item_id is not None:
        icon_key = "act_three_sell_item_sprites" if sell else "act_three_consumable_belt_sprites"
        icon = assets.get(icon_key, {}).get(item_id)
        if icon is not None:
            fitted = icon.get_rect().fit(figma_rect(local_rect(row["icon"])))
            surface.blit(pygame.transform.smoothscale(icon, fitted.size), fitted)
        if sell:
            draw_dialogue_text(surface, local(row["text"]), TRADER_SELL_ITEMS[item_id])
        else:
            item = TRADER_ITEMS[item_id]
            draw_dialogue_text(surface, local(row["text"]), f"{item.name} — {item.description}")
            _draw_art(surface, local(row["gold_coin"]))
            draw_dialogue_text(surface, local(row["price"]), str(item.price))

    cache[cache_key] = surface
    return surface


def _select_tab(state, tab):
    state.trader_tab = tab
    state.trader_slot_presses.clear()


def _buy_slot(game_state, slot_name, item_id):
    purchased = buy_trader_item(game_state, item_id)
    game_state.act_three.trader_slot_presses[slot_name] = pygame.time.get_ticks(), purchased


def _handle_trader_key(event, game_state, layout):
    if getattr(event, "automatic_movement", False):
        return

    state = game_state.act_three
    tab_specs = layout["trade_selection"]
    tabs = sorted(tab_specs, key=lambda name: tab_specs[name]["hitbox"]["x"])
    slots = sorted(layout["trade_slots"])
    focus = state.trader_focus or state.trader_tab
    if event.key in CHORD_MOVEMENT_KEYS:
        dx, dy = movement_direction_for_key(event.key)
        if focus in tabs:
            if dx:
                index = max(0, min(len(tabs) - 1, tabs.index(focus) + dx))
                focus = tabs[index]
            elif dy > 0:
                focus = slots[0]
        elif dy:
            index = slots.index(focus) + dy
            focus = state.trader_tab if index < 0 else slots[min(index, len(slots) - 1)]
        state.trader_focus = focus
    elif event.key == pygame.K_SPACE and not getattr(event, "repeat", False):
        state.trader_focus = focus
        if focus in tabs:
            _select_tab(state, focus)
        else:
            for (slot_name, _), item_id in _stock_rows(layout, state.trader_tab):
                if slot_name == focus:
                    _buy_slot(game_state, slot_name, item_id)
                    break


def handle_trader_event(event, game_state, mouse_position):
    state = game_state.act_three
    if state.trader_tab is None:
        return False
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            close_npc_dialog(game_state, pygame.time.get_ticks())
        elif event.key in CHORD_MOVEMENT_KEYS or event.key == pygame.K_SPACE:
            _handle_trader_key(event, game_state, load_trader_layout())
        return True
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1 or mouse_position is None:
        return True
    layout = load_trader_layout()
    state.trader_focus = None
    if figma_rect(layout["close_hitbox"]).collidepoint(mouse_position):
        close_npc_dialog(game_state, pygame.time.get_ticks())
        return True
    for tab, spec in layout["trade_selection"].items():
        if figma_rect(spec["hitbox"]).collidepoint(mouse_position):
            _select_tab(state, tab)
            return True
    for (slot_name, row), item_id in _stock_rows(layout, state.trader_tab):
        if figma_rect(row["background"]["rect"]).collidepoint(mouse_position):
            _buy_slot(game_state, slot_name, item_id)
            break
    return True


def draw_trader(screen, game_state, assets, current_time, mouse_position=None):
    state = game_state.act_three
    tab = state.trader_tab
    if tab is None:
        return False
    layout = load_trader_layout()
    _draw_art(screen, layout["trader_background"])
    for frames in layout["candles"].values():
        if frames:
            _draw_art(screen, frames[current_time // 110 % len(frames)])
    for name, spec in layout["trade_selection"].items():
        _draw_art(screen, spec["active" if name == tab else "inactive"])
        draw_dialogue_text(screen, spec["title"], spec["title"]["text"])
        if state.trader_focus == name:
            rect = figma_rect(spec["hitbox"]).inflate(-4, -4)
            pygame.draw.rect(screen, _FOCUS_COLOR, rect, width=2, border_radius=4)
    sell = tab == "sell"
    items = tuple(TRADER_SELL_ITEMS) if sell else TRADER_STOCK[tab]
    for index, (slot_name, row) in enumerate(sorted(layout["trade_slots"].items())):
        item_id = items[index] if index < len(items) else None
        rect = figma_rect(row["background"]["rect"])
        focused = state.trader_focus == slot_name
        hovered = focused or (
            state.trader_focus is None and mouse_position is not None and rect.collidepoint(mouse_position)
        )
        pressed = state.trader_slot_presses.get(slot_name)
        elapsed = max(0, current_time - pressed[0]) if pressed is not None else None
        purchased = pressed is not None and pressed[1]
        rect = rect.move(trader_press_offset(elapsed, purchased))
        screen.blit(_slot_image(assets, slot_name, row, item_id, sell), rect)
        draw_trader_slot_effect(screen, rect, hovered, elapsed, purchased, current_time)
        if focused:
            pygame.draw.rect(screen, _FOCUS_COLOR, rect.inflate(-6, -6), width=1, border_radius=8)
    return True
