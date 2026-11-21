import math

import pygame

from acts.act_three.rune_master.effects import blend_art, illuminated_art
from presentation.figma_ui import figma_rect


def draw_rune_button(screen, assets, menu, name, spec, enabled, mouse_position, current_time, load_art):
    control = "back" if name == "return_button" else "confirm"
    bounds = figma_rect(spec["hitbox"])
    hovered = enabled and mouse_position is not None and bounds.collidepoint(mouse_position)
    held = hovered and menu.pressed == control
    visuals = assets.setdefault("act_three_rune_button_visuals", {})
    previous_time, hover, depth = visuals.get(name, (current_time, 0.0, 0.0))
    elapsed = max(0, current_time - previous_time)
    blend = 1 - math.exp(-elapsed / 65)
    hover += (float(hovered) - hover) * blend
    activating = (
        menu.pending_button_action == control
        and current_time - menu.pending_button_started_at < 55
    )
    press_target = float(held or activating)
    press_blend = 1 - math.exp(-elapsed / (30 if press_target else 65))
    depth += (press_target - depth) * press_blend
    visuals[name] = current_time, hover, depth
    amount = depth
    available = enabled or menu.pending_button_action == control
    art_spec = spec["active" if available else "inactive"]
    image = load_art(art_spec).copy()
    active_amount = max(hover, depth)
    if active_amount > 0 and available:
        active = illuminated_art(load_art(spec["active"]), 0.35 * hover)
        image = blend_art(image, active, active_amount)
    if amount > 0:
        shade = round(255 - 65 * amount)
        image.fill((shade, shade, shade, 255), special_flags=pygame.BLEND_RGBA_MULT)
    if art_spec.get("opacity", 1) != 1:
        image.set_alpha(round(255 * art_spec["opacity"]))
    scale = max(1, bounds.height / 47)
    position = figma_rect(art_spec["rect"]).move(0, round(5 * scale * amount))
    screen.blit(image, position)
