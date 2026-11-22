import math

import pygame

from acts.act_three.abilities.catalog import get_ability_definition
from acts.act_three.abilities.charges import ability_is_passive, get_act_three_ability_charge_state
from acts.act_three.abilities.progression import is_ability_slot_unlocked
from acts.act_three.presentation.hud.ability_tooltips import ability_tooltip_content, hovered_ability_slot
from acts.act_three.presentation.ability_assets import ability_icon_key
from presentation.figma_ui import draw_figma_rectangle, figma_rect


def draw_belt_image(screen, assets, node):
    if node is None:
        return
    rectangle = figma_rect(node["rect"])
    if rectangle.width <= 0 or rectangle.height <= 0:
        return
    name = node["asset"]
    cache = assets["hud_belt_image_cache"]
    cached = cache.get(name)
    if cached is None or cached.get_size() != rectangle.size:
        source = assets["hud_belt_images"][name]
        cached = source if source.get_size() == rectangle.size else pygame.transform.smoothscale(source, rectangle.size)
        cache[name] = cached
    screen.blit(cached, rectangle)


def draw_belt_frame(screen, player, assets, layout):
    art = layout["down_bar"]["belt_art"]
    draw_belt_image(screen, assets, art["background"])
    rectangle = figma_rect(art["background"]["rect"])
    feedback = assets["hud_belt_feedback"]
    signature = id(player)
    unlocked = frozenset(
        slot for slot in ("q", "e", "f")
        if player.debug_unlimited_abilities or is_ability_slot_unlocked(player, slot)
    )
    now = pygame.time.get_ticks()
    if feedback.get("signature") != signature or feedback.get("unlocked") != unlocked:
        previous = feedback.get("unlocked", unlocked)
        feedback["started"] = now if signature == feedback.get("signature") and unlocked - previous else -10000
        feedback["signature"] = signature
        feedback["unlocked"] = unlocked
    progress = (now - feedback["started"]) / 900
    if 0 <= progress < 1:
        glow = pygame.Surface(rectangle.size, pygame.SRCALPHA)
        width = max(8, rectangle.width // 5)
        center = round((rectangle.width + width) * progress - width / 2)
        for offset in range(-width, width):
            alpha = round(75 * (1 - abs(offset) / width) * math.sin(math.pi * progress))
            pygame.draw.line(glow, (239, 205, 137, alpha), (center + offset, 0), (center + offset, rectangle.height))
        glow.blit(assets["hud_belt_image_cache"][art["background"]["asset"]], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(glow, rectangle)


def _draw_charge_mask(screen, mask, ratio):
    rectangle = figma_rect(mask["rect"])
    height = round(rectangle.height * (1 - ratio))
    if rectangle.width <= 0 or height <= 0:
        return
    layer = pygame.Surface(rectangle.size, pygame.SRCALPHA)
    draw_figma_rectangle(layer, {
        **mask,
        "rect": {"x": 0, "y": 0, "width": rectangle.width, "height": rectangle.height},
    })
    screen.blit(layer, rectangle.topleft, pygame.Rect(0, 0, rectangle.width, height))


def draw_belt_abilities(screen, player, assets, layout, mouse_position):
    slots = layout["down_bar"]["abilities"]["slots"]
    hovered = hovered_ability_slot(slots, mouse_position)
    scale = assets.get("hud_render_scale", 1.0)
    now = pygame.time.get_ticks()
    for name, slot in slots.items():
        key = name.removeprefix("ability_")
        if slot.get("frame") is not None:
            draw_belt_image(screen, assets, slot["frame"])
        if not is_ability_slot_unlocked(player, key) and not player.debug_unlimited_abilities:
            draw_belt_image(screen, assets, slot.get("letter"))
            if slot["plug"] is not None:
                draw_belt_image(screen, assets, slot["plug"])
            continue
        ability = get_ability_definition(player.subclass, key)
        if ability is None:
            continue
        rectangle = figma_rect(slot["icon"])
        image = assets.get(ability_icon_key(player, ability))
        current, required = get_act_three_ability_charge_state(player, key)
        ratio = max(0.0, min(1.0, current / max(1, required)))
        passive = ability_is_passive(player, key)
        ready = ratio >= 1
        if ready and not passive:
            padding = max(3, round(5 * scale))
            glow = pygame.Surface((rectangle.width + padding * 2, rectangle.height + padding * 2), pygame.SRCALPHA)
            alpha = round(30 + 12 * math.sin(now * 0.003))
            pygame.draw.rect(glow, (211, 176, 112, alpha), glow.get_rect().inflate(-padding, -padding), border_radius=max(2, padding))
            glow = pygame.transform.gaussian_blur(glow, padding)
            screen.blit(glow, rectangle.move(-padding, -padding))
        if image is not None:
            displayed = image if image.get_size() == rectangle.size else pygame.transform.smoothscale(image, rectangle.size)
            screen.blit(displayed, rectangle)
        if not ready:
            _draw_charge_mask(screen, slot["charge_level"], ratio)
        if key == hovered:
            shine = pygame.Surface(rectangle.size, pygame.SRCALPHA)
            shine.fill((225, 210, 178, 26))
            screen.blit(shine, rectangle)
        draw_belt_image(screen, assets, slot.get("letter"))
    for ornament in layout["down_bar"]["abilities"].get("ornaments", {}).values():
        draw_belt_image(screen, assets, ornament)
    return ability_tooltip_content(player, hovered)
