import json
from functools import lru_cache

import pygame
import resource_store as resources

from acts.act_three.equipment import MAX_EQUIPMENT_RANK, equipment_rank_bonus
from acts.act_three.blacksmith.recipes import IMPLEMENTED_FORGE_RANK
from acts.act_three.forge import (
    FORGE_UPGRADES,
    can_forge_upgrade,
    forge_ore_count,
    forge_rank,
    forge_recipe,
    forge_work,
    forge_progress_fraction,
    try_forge_upgrade,
)
from acts.act_three.npcs import close_npc_dialog, get_npc_at
from acts.act_three.presentation.forge_effects import (
    animated_forge_progress,
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
        or not state.blacksmith_forge_open
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


def _control_rectangles(layout):
    return {
        **{
            upgrade: figma_rect(layout["selection_buttons"][upgrade]["hitbox"])
            for upgrade in FORGE_UPGRADES
        },
        "confirm": figma_rect(layout["confirm_button"]["hitbox"]),
        "close": figma_rect(layout["close_hitbox"]),
    }


def handle_blacksmith_event(event, game_state, mouse_position):
    if not _blacksmith_is_open(game_state):
        return False

    floor = game_state.floor
    control = None
    if event.type == pygame.KEYDOWN:
        if getattr(event, "automatic_movement", False):
            return True
        if event.key in (pygame.K_a, pygame.K_d):
            if tempering_elapsed(floor, pygame.time.get_ticks()) is None:
                game_state.act_three.npc_dialog_line_index = (
                    0 if event.key == pygame.K_a else 1
                )
            return True

        if getattr(event, "repeat", False):
            return True
        if event.key == pygame.K_ESCAPE:
            control = "close"
        elif event.key == pygame.K_SPACE:
            control = "confirm"
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            control = "confirm"
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and mouse_position is not None:
        control = next(
            (
                name for name, rect in _control_rectangles(get_blacksmith_layout()).items()
                if rect.collidepoint(mouse_position)
            ),
            None,
        )

    if control is None:
        return True

    current_time = pygame.time.get_ticks()
    if control == "close":
        if tempering_elapsed(floor, current_time) is not None:
            return True
        stop_tempering(floor)
        close_npc_dialog(game_state, current_time)
    elif tempering_elapsed(floor, current_time) is not None:
        return True
    elif control == "confirm":
        selected = _selected_upgrade(game_state)
        before = forge_progress_fraction(game_state.player, selected)
        previous_rank = forge_rank(game_state.player, selected)
        if try_forge_upgrade(game_state, selected):
            target = 1.0 if forge_rank(game_state.player, selected) > previous_rank else forge_progress_fraction(game_state.player, selected)
            start_tempering(floor, current_time, before, target)
    elif control in FORGE_UPGRADES:
        game_state.act_three.npc_dialog_line_index = FORGE_UPGRADES.index(control)

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
    recipe = forge_recipe(player, selected)
    work = forge_work(player, selected)
    worked = sum(min(work.get(item, 0), required) for item, required in recipe.items())
    description = f"{selected.title()} rank {rank}/{MAX_EQUIPMENT_RANK}\n"
    if rank >= MAX_EQUIPMENT_RANK:
        description += f"{bonus_label}: {bonus}%\nMaximum rank reached."
    elif rank >= IMPLEMENTED_FORGE_RANK:
        description += f"{bonus_label}: {bonus}%\nFurther ranks are not available yet."
    else:
        description += (
            f"{bonus_label}: {bonus}% to {next_bonus}%\n"
            f"Work on next rank: {worked}/{sum(recipe.values())} materials\n"
            "Finish this rank to receive the bonus."
        )
    if elapsed is not None:
        description = f"Tempering {selected}...\n{bonus_label}: {bonus}%"
    draw_figma_text(screen, improvement["improvement_description"], text_override=description, wrap=True)

    for index, (item, required) in enumerate(recipe.items(), start=1):
        ore = layout["resources_icons"].get(f"resource_{index:02d}")
        if ore is None:
            continue
        ore_rectangle = figma_rect(ore["rect"])
        sprite = assets.get("act_three_inventory_sprites", {}).get(item)
        if sprite is not None:
            fitted = sprite.get_rect().fit(ore_rectangle)
            screen.blit(pygame.transform.smoothscale(sprite, fitted.size), fitted)
        else:
            label = fonts["sidebar_numbers"].render("?", True, (122, 114, 128))
            screen.blit(label, label.get_rect(center=ore_rectangle.center))
        owned = forge_ore_count(player, item)
        done = min(work.get(item, 0), required)
        color = (143, 188, 128) if done == required else (224, 205, 163) if owned else (217, 115, 107)
        amount = fonts["sidebar_numbers"].render(f"{done}/{required}", True, color)
        amount_rectangle = amount.get_rect(bottomright=ore_rectangle.bottomright)
        pygame.draw.rect(screen, (14, 10, 13), amount_rectangle.inflate(6, 2), border_radius=3)
        screen.blit(amount, amount_rectangle)

    scale = layout["scale"]
    fill = scale["fill"]
    fill_rect = figma_rect(fill["rect"])
    progress = animated_forge_progress(forge_progress_fraction(player, selected), elapsed, game_state.floor)
    fill_width = round(fill_rect.width * max(0.0, min(1.0, progress)))
    if fill_width > 0:
        screen.blit(
            images[_art_key(fill)], fill_rect,
            pygame.Rect(0, 0, fill_width, fill_rect.height),
        )
        draw_forge_fill_glow(screen, fill_rect, fill_width, elapsed)
    draw_art(scale["frame"])
    draw_art(layout["confirm_button"]["active" if can_upgrade else "inactive"])
    return True
