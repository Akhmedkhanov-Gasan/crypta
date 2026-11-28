from functools import lru_cache
import json
import math

import pygame
import resource_store as resources

from acts.act_three.bloody_altar.catalog import PACTS, PACTS_BY_ID
from acts.act_three.bloody_altar.runtime import menu_altar
from acts.act_three.bloody_altar.world_animation import draw_world_altar, world_frames
from presentation.figma_ui import _load_figma_font, draw_figma_rectangle, draw_figma_text, figma_rect
from presentation.text import wrap_text
from presentation.figma_layout import scale_figma_layout
from acts.act_three.bloody_altar.motion import poses, hitbox
from acts.act_three.rune_master.effects import illuminated_art, draw_subpixel_card, draw_card_mist, draw_confirmation_light
from acts.act_three.rune_master.buttons import draw_rune_button


@lru_cache(maxsize=1)
def get_layout():
    with resources.open_text("assets/ui/layouts/act_3/bloody_altar.json", encoding="utf-8") as source:
        layout = json.load(source)
    if (layout.get("screen") != "bloody_altar" or layout.get("act") != 3
            or layout.get("schema_version") != 2 or layout.get("coordinate_space") != "frame"
            or layout.get("frame", {}).get("width") != 1280 or layout.get("frame", {}).get("height") != 720):
        raise ValueError("Invalid Act III bloody altar layout.")
    return layout


@lru_cache(maxsize=1)
def get_assets():
    layout = get_layout()
    specs = [layout["bloody_altar_background"], layout["close_icon"]]
    specs.extend(layout["confirm_button"][state] for state in ("active", "inactive"))
    specs.extend(card["background"] for card in layout["pacts"].values())
    images = {}
    for spec in specs:
        path = spec["asset_path"]
        size = figma_rect(spec["rect"]).size
        key = path, size
        if key not in images:
            images[key] = pygame.transform.smoothscale(resources.load_image(path).convert_alpha(), size)
    for pact in PACTS:
        path = f"assets/sprites/ui/act_3/bloody_altar/120/{pact.icon or pact.id}.png"
        images[pact.id] = resources.load_image(path).convert_alpha()
    return images


def _description_spec(spec, text):
    for size in range(round(spec["font"]["size"]), 10, -1):
        candidate = {**spec, "font": {**spec["font"], "size": size},
                     "line_height": {"unit": "PIXELS", "value": size + 1}}
        font = _load_figma_font(candidate)
        lines = [line for paragraph in text.split("\n")
                 for line in (wrap_text(font, paragraph, spec["rect"]["width"]) or [""])]
        if len(lines) * (size + 1) <= spec["rect"]["height"]:
            return candidate
    return candidate


@lru_cache(maxsize=64)
def _image(path, size):
    return pygame.transform.smoothscale(resources.load_image(path).convert_alpha(), size)


def _art_image(spec):
    return _image(spec["asset_path"], figma_rect(spec["rect"]).size)


def _local(spec, origin):
    return {**spec, "rect": {**spec["rect"], "x": spec["rect"]["x"] - origin.x,
                            "y": spec["rect"]["y"] - origin.y}}


@lru_cache(maxsize=36)
def _card_layers(identifier, render_scale, index):
    template = get_layout()["pacts"][f"pact_{index + 1:02d}"]
    spec = scale_figma_layout(template, render_scale * 4)
    card_bounds = figma_rect(spec["rect"])
    rarity_rect = figma_rect(spec["rarity"])
    bounds = card_bounds.union(rarity_rect)
    pact = PACTS_BY_ID[identifier]
    content = pygame.Surface(bounds.size, pygame.SRCALPHA)
    icon_rect = figma_rect(spec["icon"]).move(-bounds.x, -bounds.y)
    icon_path = f"assets/sprites/ui/act_3/bloody_altar/120/{pact.icon or pact.id}.png"
    content.blit(_image(icon_path, icon_rect.size), icon_rect)
    draw_figma_text(content, _local(spec["name"], bounds), text_override=pact.name, wrap=True)
    draw_figma_rectangle(content, _local(spec["description"]["background"], bounds))
    description = _description_spec(template["description"]["text"], pact.description)
    description = scale_figma_layout(description, render_scale * 4)
    draw_figma_text(content, _local(description, bounds), text_override=pact.description, wrap=True)
    rarity = get_layout()["rarities"][pact.rarity]
    badge = _image(rarity["asset_path"], rarity_rect.size)
    if rarity.get("opacity", 1) < 1:
        badge = badge.copy()
        badge.set_alpha(round(255 * rarity["opacity"]))
    content.blit(badge, rarity_rect.move(-bounds.x, -bounds.y))
    sources = []
    background = spec["background"]
    for lit in (False, True):
        layer = pygame.Surface((bounds.width + 16, bounds.height + 16), pygame.SRCALPHA)
        art = _art_image(background)
        if lit:
            art = illuminated_art(art, 1)
        layer.blit(art, (figma_rect(background["rect"]).x - bounds.x + 8,
                         figma_rect(background["rect"]).y - bounds.y + 8))
        layer.blit(content, (8, 8))
        sources.append(layer)
    offset = (bounds.x - card_bounds.x) / 4, (bounds.y - card_bounds.y) / 4
    return tuple(sources), offset


def draw_altar_menu(screen, game_state, current_time=None, mouse_position=None, *, render_scale=1):
    state = game_state.act_three
    if not state.altar_menu_open:
        return False
    menu = state.altar_motion
    if menu is None:
        return False
    current_time = pygame.time.get_ticks() if current_time is None else current_time
    layout = get_layout() if render_scale == 1 else scale_figma_layout(get_layout(), render_scale)
    images = get_assets()
    if images.get("menu") is not menu:
        images["menu"] = menu
        images["hover"] = {}
        images["act_three_rune_button_visuals"] = {}
    veil = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    veil.fill((0, 0, 0, 160))
    screen.blit(veil, (0, 0))
    screen.blit(_art_image(layout["bloody_altar_background"]), figma_rect(layout["bloody_altar_background"]["rect"]))
    screen.blit(_art_image(layout["close_icon"]), figma_rect(layout["close_icon"]["rect"]))
    offers = menu_altar(game_state)["offers"]
    card_poses = poses(menu, layout, current_time)
    card_poses.sort(key=lambda pose: pose.index == menu.selected_choice)
    for pose in card_poses:
        highlighted = (menu.phase == "idle" and menu.pending_button_action is None
                       and ((mouse_position is not None and hitbox(layout, pose).collidepoint(mouse_position))
                            or (menu.keyboard_focus and menu.focus == pose.index)))
        selected = menu.selected_choice == pose.index
        previous_time, amount = images["hover"].get(pose.index, (current_time, 0.0))
        target = 1.0 if selected else 0.55 if highlighted else 0.0
        amount += (target - amount) * (1 - math.exp(-max(0, current_time - previous_time) / 95))
        images["hover"][pose.index] = current_time, amount
        sources, offset = _card_layers(offers[pose.index], render_scale, pose.index)
        position = pose.position[0] + offset[0], pose.position[1] + offset[1]
        draw_subpixel_card(screen, sources[0], position, pose.alpha, sources[1], amount)
        if menu.phase == "confirmed" and selected:
            draw_confirmation_light(screen, pose.rect, min(1, max(0, (current_time - menu.started_at) / 380)))
    mist = max((pose.mist for pose in card_poses), default=0)
    for index, card in enumerate(layout["pacts"].values()):
        draw_card_mist(screen, figma_rect(card["rect"]), mist, current_time, index, color=(172, 50, 57))
    idle = menu.phase == "idle"
    draw_rune_button(screen, images, menu, "confirm_button", layout["confirm_button"],
                     idle and menu.selected_choice is not None, mouse_position, current_time, _art_image)
    draw_figma_text(screen, layout["specification"], wrap=True)
    return True


def draw_native_altar_menu(target, game_state, current_time):
    offset_x, offset_y = target.get_abs_offset()
    mouse_x, mouse_y = pygame.mouse.get_pos()
    mouse = mouse_x - offset_x, mouse_y - offset_y
    if not target.get_rect().collidepoint(mouse):
        mouse = None
    return draw_altar_menu(target, game_state, current_time, mouse,
                           render_scale=target.get_width() / 1280)
