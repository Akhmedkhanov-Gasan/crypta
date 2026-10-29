import math
from functools import lru_cache

import pygame

from acts.act_three.presentation.shadow_step_trial import trial_assets
from acts.act_three.shadow_step_trial import AWAKENING_DURATION_MS
from presentation.layout import ACT_THREE_TILE_SIZE


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
    pickups = [
        effect for effect in trial.get("seal_fx", ())
        if 0 <= now - effect["started_ms"] < 800
        and tuple(effect["position"]) in floor.visible_cells
    ]
    started = trial.get("completion_fx_ms")
    final_age = now - started if started is not None else -1
    finishing = 0 <= final_age < AWAKENING_DURATION_MS
    if not pickups and not finishing:
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

    if finishing:
        progress = final_age / AWAKENING_DURATION_MS
        center = point(trial["final"])
        strength = math.sin(math.pi * progress) ** 0.65
        _soft_light(surface, center, tile * 3, (29, 19, 43), strength)
        _soft_light(surface, center, tile * 2, (109, 84, 150), strength * 0.65)

        for seal in trial["seals"]:
            if seal["position"] not in floor.visible_cells:
                continue
            source = point(seal["position"])
            for index in range(7):
                travel = (progress * 1.65 - index * 0.055)
                if not 0.0 < travel < 1.0:
                    continue
                eased = travel * travel * (3.0 - 2.0 * travel)
                x = source[0] + (center[0] - source[0]) * eased
                y = source[1] + (center[1] - source[1]) * eased
                y -= math.sin(math.pi * travel) * tile * 0.4
                _soft_light(surface, (x, y), 18, (144, 162, 180), math.sin(math.pi * travel))

        for index in range(24):
            angle = index * 2.39996 + progress * 2.6
            radius = tile * (0.85 - progress * 0.65) * (0.6 + (index % 5) * 0.1)
            x = center[0] + math.cos(angle) * radius
            y = center[1] + math.sin(angle) * radius * 0.45 - tile * progress * 0.9
            _soft_light(surface, (x, y), 18, (43, 27, 61), strength)
            if index % 3 == 0:
                _soft_light(surface, (x, y), 12, (153, 133, 183), strength * 0.8)
            pygame.draw.line(
                ink, (82, 65, 109, round(180 * strength)),
                (round(x), round(y)),
                (round(x + math.cos(angle - 0.5) * 6), round(y + 8)), 2,
            )

    surface.blit(ink, (0, 0))
