import math
from functools import lru_cache

import pygame

from acts.act_three.presentation.shadow_step_trial import trial_assets
from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.shadow_step_rite import draw_completion


@lru_cache(maxsize=8)
def _glow(size, color):
    image = pygame.Surface((24, 24), pygame.SRCALPHA)
    for y in range(24):
        for x in range(24):
            distance = ((x - 11.5) ** 2 + (y - 11.5) ** 2) / 132.25
            alpha = round(210 * max(0.0, 1.0 - distance) ** 3)
            image.set_at((x, y), (*color, alpha))
    return pygame.transform.smoothscale(image, (size, size))


@lru_cache(maxsize=2)
def _effect_canvas(size):
    return pygame.Surface(size, pygame.SRCALPHA)


def _soft_light(surface, center, size, color, opacity):
    image = _glow(size, color)
    image.set_alpha(round(255 * max(0.0, min(1.0, opacity))))
    surface.blit(image, (round(center[0] - size / 2), round(center[1] - size / 2)))


def draw_trial_seal_effects(context):
    floor = context.floor
    trial = floor.shadow_step_trial
    if trial is None or trial["phase"] in ("closed", "opening"):
        return
    now = trial["animation_ms"]
    started = trial.get("completion_fx_ms")
    if trial["phase"] == "complete" and started is not None:
        draw_completion(context, trial, now - started)
        return
    pickups = [
        effect for effect in trial.get("seal_fx", ())
        if 0 <= now - effect["started_ms"] < 800
        and tuple(effect["position"]) in floor.visible_cells
    ]
    if not pickups:
        return
    tile = ACT_THREE_TILE_SIZE
    surface = context.view_surface
    ink = _effect_canvas(surface.get_size())
    ink.fill((0, 0, 0, 0))

    def point(cell):
        return (
            (cell[0] + 0.5) * tile - context.camera_x,
            (cell[1] + 0.5) * tile - context.camera_y,
        )

    for effect in pickups:
        progress = (now - effect["started_ms"]) / 800
        center = point(effect["position"])
        strength = math.sin(math.pi * progress) ** 0.7
        _soft_light(surface, center, tile, (129, 102, 177), strength * 0.85)
        rune = trial_assets(tile)["seals"][f"{effect['id']:02d}"]["active"][0]
        flash = rune.copy()
        flash.set_alpha(round(210 * (1.0 - progress) ** 2))
        surface.blit(flash, (round(center[0] - tile / 2), round(center[1] - tile / 2)))
        for index in range(10):
            angle = index * math.tau / 10 + effect["id"]
            radius = tile * 0.36 * (1.0 - progress)
            x = center[0] + math.cos(angle) * radius
            y = center[1] + math.sin(angle) * radius * 0.45 - tile * progress * 0.6
            _soft_light(surface, (x, y), 12, (153, 180, 178), strength * 0.75)
            pygame.draw.line(
                ink, (158, 182, 183, round(150 * strength)),
                (round(x), round(y)), (round(x + math.cos(angle) * 3), round(y + 4)), 1,
            )

    surface.blit(ink, (0, 0))
