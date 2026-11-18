from functools import lru_cache
from pathlib import Path

import pygame
import resource_store as resources

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.crushing_trial import PUSH_MS, HOLD_MS
from acts.act_three.presentation.piercing_trial import screen_position
from acts.act_three.presentation.crushing_trial_effects import draw_completion


@lru_cache(maxsize=1)
def assets():
    root = Path(__file__).resolve().parents[3] / "assets/maps/act_3/trials/berserker_crushing_leap"
    def load(path):
        return pygame.transform.scale(resources.load_image(str(root / path)).convert_alpha(), (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE))
    return {
        "rocks": {i: load(f"crushing_trial_boulders/crushing_trial_boulder_{i:02d}.png") for i in range(1, 7)},
        "plates": [load(f"crushing_trial_pressure_plate/crushing_trial_pressure_plate_press_{i:02d}.png") for i in range(1, 5)],
    }


def draw_layer(context, layer):
    trial = context.floor.crushing_trial
    if trial is None:
        return
    sprites = assets()
    if layer == "ground":
        for cell, level in trial["plate_levels"].items():
            context.view_surface.blit(sprites["plates"][round(level * 3)], screen_position(context, cell))
        return
    for rock in sorted(trial["rocks"], key=lambda item: item["cell"][1]):
        cell = rock["cell"]
        if (layer == "front") != (cell[1] >= context.floor.player_row):
            continue
        if trial["stage"] == "push" and cell == trial["push_target"]:
            progress = max(0, min(1, (pygame.time.get_ticks() - trial["started"]) / PUSH_MS))
            progress = progress * progress * (3 - 2 * progress)
            origin = trial["push_origin"]
            cell = origin[0] + (cell[0] - origin[0]) * progress, origin[1] + (cell[1] - origin[1]) * progress
        context.view_surface.blit(sprites["rocks"][rock["variant"]], screen_position(context, cell))


def draw_overlay(context):
    trial = context.floor.crushing_trial
    if trial is None:
        return
    surface = context.view_surface
    now = pygame.time.get_ticks()
    if trial["stage"] == "transition":
        elapsed = now - trial["started"]
        alpha = round(255 * max(0, min(1, elapsed / 220, (650 - elapsed) / 220)))
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((8, 5, 5, alpha))
        surface.blit(shade, (0, 0))
    if trial["stage"] == "reset":
        elapsed = now - trial["started"]
        alpha = round(255 * max(0, min(1, elapsed / 350, (1100 - elapsed) / 350)))
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((8, 5, 5, alpha))
        surface.blit(shade, (0, 0))
    if trial.get("completed") is not None:
        draw_completion(context, trial, now)


def draw_reset_hint(surface, trial, font, center_x, top, now):
    if trial is None or not trial["active"] or trial["complete"]:
        return
    text = font.render("Hold T to reset", True, (195, 180, 163))
    rect = text.get_rect(midtop=(center_x, top))
    pygame.draw.rect(surface, (24, 20, 19), rect.inflate(16, 6))
    surface.blit(text, rect)
    if trial["hold"] is not None:
        width = round(rect.width * min(1, (now - trial["hold"]) / HOLD_MS))
        pygame.draw.rect(surface, (157, 87, 66), (rect.x, rect.bottom + 3, width, 2))
