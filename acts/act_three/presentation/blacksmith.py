import json
from functools import lru_cache

import pygame
import resource_store as resources

from acts.act_three.equipment import MAX_EQUIPMENT_RANK, equipment_rank_bonus
from acts.act_three.forge import (
    FORGE_UPGRADES,
    can_forge_upgrade,
    forge_ore_count,
    forge_rank,
    try_forge_upgrade,
)
from acts.act_three.npcs import close_npc_dialog, get_npc_at
from acts.act_three.presentation.forge_effects import (
    animated_forge_rank,
    draw_forge_fill_glow,
    draw_tempering,
    start_tempering,
    stop_tempering,
    tempering_elapsed,
)
from presentation.figma_ui import draw_figma_rectangle, draw_figma_text, figma_rect
from presentation.layout import PROJECT_ROOT


@lru_cache(maxsize=1)
def get_blacksmith_layout():
    path = PROJECT_ROOT / "assets" / "ui" / "layouts" / "act_3" / "blacksmith.json"
    with resources.open_text(path) as source:
        layout = json.load(source)

    if (
        layout.get("screen") != "blacksmith"
        or layout.get("act") != 3
        or layout.get("schema_version") != 1
        or layout.get("coordinate_space") != "frame"
        or layout.get("frame", {}).get("width") != 1280
        or layout.get("frame", {}).get("height") != 720
    ):
        raise ValueError(f"Invalid Act III blacksmith layout: {path}")
    return layout


def _art_key(spec):
    rectangle = figma_rect(spec["rect"])
    return spec["asset_path"], rectangle.size, spec.get("opacity", 1)


def load_blacksmith_assets():
    layout = get_blacksmith_layout()
    confirm = layout["confirm_button"]
    scale = layout["scale"]
    selection = layout["selection_buttons"]
    type_selection = layout["improvement_section"]["type_selection"]
    art = [
        layout["forge_background"],
        confirm["inactive"],
        confirm["active"],
        scale["fill"],
        scale["frame"],
        layout["resources_icons"]["resource_01"]["icon"],
    ]
    for upgrade in FORGE_UPGRADES:
        art.extend(
            (selection[upgrade]["inactive"], selection[upgrade]["active"], type_selection[upgrade])
        )

    images = {}
    for key in dict.fromkeys(_art_key(spec) for spec in art):
        path, size, opacity = key
        sprite = pygame.transform.smoothscale(
            resources.load_image(path).convert_alpha(), size,
        )
        if opacity != 1:
            sprite.set_alpha(round(opacity * 255))
        images[key] = sprite
    return {"blacksmith_images": images}


def _blacksmith_is_open(game_state):
    state = game_state.act_three
    if (
        state.npc_dialog_position is None
        or state.npc_dialog_floor_index != game_state.floor_index
        or state.npc_dialog_phase not in ("opening", "talk")
        or game_state.player.health <= 0
        or game_state.game_won
    ):
        return False
    npc = get_npc_at(game_state.floor, state.npc_dialog_position)
    return npc is not None and npc["type"] == "blacksmith"


def _selected_upgrade(game_state):
    return "armor" if game_state.act_three.npc_dialog_line_index == 1 else "weapon"


def handle_blacksmith_event(event, game_state, mouse_position):
    if not _blacksmith_is_open(game_state):
        return False

    current_time = pygame.time.get_ticks()
    is_tempering = tempering_elapsed(game_state.floor, current_time) is not None
    confirm_requested = False

    if event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
        if event.key == pygame.K_ESCAPE:
            stop_tempering(game_state.floor)
            close_npc_dialog(game_state, current_time)
            return True
        confirm_requested = event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and mouse_position is not None:
        layout = get_blacksmith_layout()
        if figma_rect(layout["close_hitbox"]).collidepoint(mouse_position):
            stop_tempering(game_state.floor)
            close_npc_dialog(game_state, current_time)
            return True
        confirm_requested = figma_rect(layout["confirm_button"]["hitbox"]).collidepoint(
            mouse_position
        )
        if not confirm_requested and not is_tempering:
            for index, upgrade in enumerate(FORGE_UPGRADES):
                hitbox = layout["selection_buttons"][upgrade]["hitbox"]
                if figma_rect(hitbox).collidepoint(mouse_position):
                    game_state.act_three.npc_dialog_line_index = index
                    break

    if confirm_requested and not is_tempering:
        if try_forge_upgrade(game_state, _selected_upgrade(game_state)):
            start_tempering(game_state.floor, current_time)

    return True


def draw_blacksmith(screen, game_state, fonts, assets, current_time):
    if not _blacksmith_is_open(game_state):
        return False

    layout = get_blacksmith_layout()
    images = assets["blacksmith_images"]
    player = game_state.player
    selected = _selected_upgrade(game_state)
    rank = forge_rank(player, selected)
    elapsed = tempering_elapsed(game_state.floor, current_time)
    can_upgrade = elapsed is None and can_forge_upgrade(player, selected)

    def draw_art(spec):
        screen.blit(images[_art_key(spec)], figma_rect(spec["rect"]))

    draw_art(layout["forge_background"])
    for upgrade in FORGE_UPGRADES:
        button = layout["selection_buttons"][upgrade]
        draw_art(button["active" if upgrade == selected else "inactive"])
        draw_figma_text(screen, button["title"])

    improvement = layout["improvement_section"]
    equipment = improvement["type_selection"][selected]
    draw_art(equipment)
    if elapsed is not None:
        draw_tempering(
            screen, images[_art_key(equipment)], figma_rect(equipment["rect"]), elapsed,
        )
    draw_figma_rectangle(screen, improvement["text_background"])
    bonus_label = "Weapon damage" if selected == "weapon" else "Physical damage reduction"
    bonus = equipment_rank_bonus(rank)
    next_bonus = equipment_rank_bonus(rank + 1)
    description = (
        f"{selected.title()} rank {rank}/{MAX_EQUIPMENT_RANK}\n"
        + (
            f"{bonus_label}: {bonus}%\nMaximum rank reached."
            if rank >= MAX_EQUIPMENT_RANK
            else f"{bonus_label}: {bonus}% to {next_bonus}%"
        )
    )
    if elapsed is not None:
        description = f"Tempering {selected}...\n{bonus_label}: {bonus}%"
    draw_figma_text(screen, improvement["improvement_description"], text_override=description)

    ore = layout["resources_icons"]["resource_01"]
    draw_art(ore["icon"])
    owned = forge_ore_count(player)
    amount = fonts["sidebar_numbers"].render(
        f"{owned}/1", True, (224, 205, 163) if owned else (217, 115, 107),
    )
    ore_rectangle = figma_rect(ore["rect"])
    amount_rectangle = amount.get_rect(bottomright=ore_rectangle.bottomright)
    pygame.draw.rect(screen, (14, 10, 13), amount_rectangle.inflate(6, 2), border_radius=3)
    screen.blit(amount, amount_rectangle)

    scale = layout["scale"]
    fill = scale["fill"]
    fill_rect = figma_rect(fill["rect"])
    display_rank = animated_forge_rank(rank, elapsed)
    fill_width = round(fill_rect.width * display_rank / MAX_EQUIPMENT_RANK)
    if fill_width > 0:
        screen.blit(
            images[_art_key(fill)], fill_rect,
            pygame.Rect(0, 0, fill_width, fill_rect.height),
        )
        draw_forge_fill_glow(screen, fill_rect, fill_width, elapsed)
    draw_art(scale["frame"])
    draw_art(layout["confirm_button"]["active" if can_upgrade else "inactive"])
    return True
