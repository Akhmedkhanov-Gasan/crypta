import math
from functools import lru_cache

import pygame
import resource_store as resources

from acts.act_three.rune_master.default_layout import text
from acts.act_three.rune_master.effects import illuminated_art, draw_card_mist, draw_subpixel_card, draw_confirmation_light
from acts.act_three.rune_master.layout import get_layout
from acts.act_three.rune_master.motion import card_hitbox, card_poses
from acts.act_three.rune_master.runtime import visible_cards
from presentation.dialogue_text import draw_dialogue_text
from presentation.figma_ui import draw_figma_rectangle, figma_rect
from presentation.figma_layout import scale_figma_layout
from acts.act_three.rune_master.buttons import draw_rune_button


@lru_cache(maxsize=128)
def _image(path, size):
    if not resources.is_file(path):
        return None
    return pygame.transform.smoothscale(resources.load_image(path).convert_alpha(), size)


def _art(spec):
    bounds = figma_rect(spec["rect"])
    image = _image(spec["asset_path"], bounds.size)
    if image is None:
        raise FileNotFoundError(spec["asset_path"])
    return image


def _draw_art(surface, spec):
    image = _art(spec)
    if spec.get("opacity", 1) != 1:
        image = image.copy()
        image.set_alpha(round(255 * spec["opacity"]))
    surface.blit(image, figma_rect(spec["rect"]))


def _local(data, origin):
    return {**data, "x": data["x"] - origin.x, "y": data["y"] - origin.y}


def _local_spec(spec, origin):
    return {**spec, "rect": _local(spec["rect"], origin)}


def _content(assets, slot_name, spec, card):
    cache = assets.setdefault("act_three_rune_card_content", {})
    key = slot_name, card, figma_rect(spec["rect"]).size
    if key in cache:
        return cache[key]
    spec = scale_figma_layout(spec, 4)
    bounds = figma_rect(spec["rect"])
    surface = pygame.Surface(bounds.size, pygame.SRCALPHA)
    content = spec["content"]
    icon_rect = figma_rect(_local(content["icon"], bounds))
    icon = next((image for path in card.icon_paths
                 if (image := _image(path, icon_rect.size)) is not None), None)
    if icon is not None:
        surface.blit(icon, icon_rect)
    else:
        pygame.draw.circle(surface, (45, 24, 63), icon_rect.center, icon_rect.width // 2 - 3)
        pygame.draw.circle(surface, (155, 99, 194), icon_rect.center, icon_rect.width // 2 - 3, 2)
        draw_dialogue_text(surface, text(_local(content["icon"], bounds), 144, 210), "?")
    draw_figma_rectangle(surface, _local_spec(content["description_background"], bounds))
    for name, value in (("name", card.name), ("description", card.description)):
        source = _local_spec(content[name], bounds)
        draw_dialogue_text(surface, source, value, preserve_glyphs=True)
    cache[key] = surface
    return surface


def _draw_card(screen, assets, spec, pose, card, highlighted, selected, current_time, opened_at):
    cache = assets.setdefault("act_three_rune_card_layers", {})
    sources = []
    for lit in (False, True):
        key = "quiet_selection", pose.index, card, lit, pose.rect.size
        if key in cache:
            sources.append(cache[key])
            continue
        scaled_spec = scale_figma_layout(spec, 4)
        layer = pygame.Surface((pose.rect.width * 4, pose.rect.height * 4), pygame.SRCALPHA)
        background = scaled_spec["background"]
        image = illuminated_art(_art(background), 1) if lit else _art(background)
        layer.blit(image, (0, 0))
        layer.blit(_content(assets, f"slot_{pose.index + 1:02d}", spec, card), (0, 0))
        padded = pygame.Surface((layer.get_width() + 16, layer.get_height() + 16), pygame.SRCALPHA)
        padded.blit(layer, (8, 8))
        cache[key] = padded
        sources.append(padded)
    states = assets.setdefault("act_three_rune_card_hover", {})
    state_key = opened_at, pose.index
    previous_time, amount = states.get(state_key, (current_time, 0.0))
    target = 1.0 if selected else 0.55 if highlighted else 0.0
    amount += (target - amount) * (1 - math.exp(-max(0, current_time - previous_time) / 95))
    states[state_key] = current_time, amount
    draw_subpixel_card(screen, sources[0], pose.position, pose.alpha, sources[1], amount)


def draw_rune_menu(screen, game_state, assets, current_time, mouse_position=None, *, render_scale=1):
    menu = game_state.act_three.rune_menu
    if menu is None:
        return False
    layout = get_layout() if render_scale == 1 else scale_figma_layout(get_layout(), render_scale)
    shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    shade.fill((8, 3, 15, 190))
    screen.blit(shade, (0, 0))
    _draw_art(screen, layout["window_background"])
    cards = visible_cards(menu)
    poses = card_poses(menu, layout, current_time)
    if menu.confirming_choice:
        poses.sort(key=lambda pose: pose.index == menu.selected_choice)
    for pose in poses:
        highlighted = (
            menu.phase == "idle" and menu.pending_button_action is None
            and ((mouse_position is not None and card_hitbox(layout, pose).collidepoint(mouse_position))
                 or (menu.keyboard_focus and menu.focus == pose.index))
        )
        _draw_card(screen, assets, layout["slots"][f"slot_{pose.index + 1:02d}"],
                   pose, cards[pose.index], highlighted,
                   menu.page == "choices" and menu.selected_choice == pose.index,
                   current_time, menu.opened_at)
    mist = max((pose.mist for pose in poses), default=0)
    for index, name in enumerate(("slot_01", "slot_02", "slot_03")):
        draw_card_mist(screen, figma_rect(layout["slots"][name]["rect"]), mist, current_time, index)
    if menu.phase == "confirmed":
        progress = min(1, max(0, (current_time - menu.started_at) / 380))
        for pose in poses:
            if pose.index == menu.selected_choice:
                draw_confirmation_light(screen, pose.rect, progress)
    idle_choices = menu.page == "choices" and menu.phase == "idle"
    for name, enabled in (
        ("return_button", idle_choices),
        ("confirm_button", idle_choices and menu.selected_choice is not None
         and not menu.choices[menu.selected_choice].placeholder),
    ):
        draw_rune_button(screen, assets, menu, name, layout[name], enabled, mouse_position, current_time, _art)
    return True


def draw_native_rune_menu(target, game_state, assets, current_time, mouse_position):
    scale = target.get_width() / 1280
    offset_x, offset_y = target.get_abs_offset()
    mouse_x, mouse_y = pygame.mouse.get_pos()
    native_mouse = mouse_x - offset_x, mouse_y - offset_y
    if not target.get_rect().collidepoint(native_mouse):
        native_mouse = None
    return draw_rune_menu(
        target, game_state, assets, current_time, native_mouse, render_scale=scale,
    )
