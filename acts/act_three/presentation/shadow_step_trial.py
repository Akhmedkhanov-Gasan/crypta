from functools import lru_cache
from pathlib import Path

import pygame

import resource_store as resources

from acts.act_three.shadow_step_trial import (
    DETECTION_PAUSE_MS,
    DOOR_DURATION_MS,
    LIGHT_RANGE,
    eye_frame,
    eye_light_polygon,
)
from presentation.layout import ACT_THREE_TILE_SIZE


_ASSET_ROOT = (
    Path(__file__).resolve().parents[3]
    / "assets"
    / "maps"
    / "act_3"
    / "assassin_shadow_step"
)


@lru_cache(maxsize=4)
def trial_assets(tile_size):
    def load(directory, filename, height=1):
        path = _ASSET_ROOT / directory / filename
        image = resources.load_image(str(path)).convert_alpha()
        return pygame.transform.scale(
            image,
            (tile_size, tile_size * height),
        )

    result = {
        "door": [
            load(
                "assassin_shadow_step_door",
                f"shadow_step_door_open_{index:02d}.png",
            )
            for index in range(1, 9)
        ],
        "eye": [
            load(
                "assassin_shadow_step_rotating_column",
                f"shadow_step_column_rotate_{index:02d}.png",
                2,
            )
            for index in range(1, 9)
        ],
        "seals": {},
    }

    for variant in ("01", "02", "03", "final"):
        directory = f"assassin_shadow_step_seal_{variant}"
        prefix = f"shadow_step_seal_{variant}"
        frame_count = 7 if variant == "final" else 8
        inactive_state = "extinguished" if variant == "final" else "pressed"
        result["seals"][variant] = {
            "active": [
                load(directory, f"{prefix}_shimmer_{index:02d}.png")
                for index in range(1, frame_count + 1)
            ],
            "inactive": load(directory, f"{prefix}_{inactive_state}.png"),
        }
    return result

@lru_cache(maxsize=4)
def _cone_gradient(radius):
    size = radius * 2 + 4
    center = (radius + 2, radius + 2)
    surface = pygame.Surface((size, size), pygame.SRCALPHA)

    for current_radius in range(radius, 0, -1):
        progress = 1.0 - current_radius / radius
        alpha = round(32 + 38 * progress ** 0.8)
        pygame.draw.circle(
            surface,
            (244, 181, 98, alpha),
            center,
            current_radius,
        )

    return surface


@lru_cache(maxsize=16)
def _beam_surface(radius, points, caught):
    gradient = _cone_gradient(radius)
    mask = pygame.Surface(gradient.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), points)
    reduced_size = (
        max(1, mask.get_width() // 4),
        max(1, mask.get_height() // 4),
    )
    soft_mask = pygame.transform.smoothscale(
        pygame.transform.smoothscale(mask, reduced_size),
        mask.get_size(),
    )
    soft_mask.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    beam = gradient.copy()
    if caught:
        beam.fill((255, 176, 83, 125))
    beam.blit(soft_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return beam


@lru_cache(maxsize=2)
def _detection_vignette(size):
    texture = pygame.Surface((64, 36), pygame.SRCALPHA)
    for y in range(36):
        for x in range(64):
            edge = max(abs((x + 0.5) / 32 - 1), abs((y + 0.5) / 18 - 1))
            texture.set_at((x, y), (12, 7, 9, round(25 + 155 * edge ** 2)))
    return pygame.transform.smoothscale(texture, size)


@lru_cache(maxsize=4)
def _caught_lamp_glow(tile_size):
    texture = pygame.Surface((32, 32), pygame.SRCALPHA)
    for y in range(32):
        for x in range(32):
            distance = (((x - 15.5) / 15.5) ** 2 + ((y - 15.5) / 15.5) ** 2)
            alpha = round(230 * max(0.0, 1.0 - distance) ** 3)
            texture.set_at((x, y), (255, 203, 121, alpha))
    return pygame.transform.smoothscale(texture, (tile_size, tile_size))


def draw_trial_detection(context):
    trial = context.floor.shadow_step_trial
    if trial is None:
        return
    if trial.get("action_stage") == "caught":
        progress = min(1.0, trial["action_ms"] / DETECTION_PAUSE_MS)
        weight = min(1.0, progress / 0.22)
    elif trial["cooldown_ms"] > 0:
        weight = min(1.0, trial["cooldown_ms"] / 600)
    else:
        return
    weight = weight * weight * (3.0 - 2.0 * weight)
    veil = _detection_vignette(context.view_surface.get_size())
    veil.set_alpha(round(255 * weight))
    context.view_surface.blit(veil, (0, 0))
    if trial.get("action_stage") == "caught":
        draw_trial_lighting(context, detection_overlay=True)


def draw_trial_lighting(context, detection_overlay=False):
    floor = context.floor
    trial = floor.shadow_step_trial

    if trial is None or trial["phase"] != "active":
        return

    tile_size = ACT_THREE_TILE_SIZE
    radius = round((LIGHT_RANGE + 52 / 64) * tile_size)

    for eye in trial["eyes"]:
        caught = (
            trial.get("action_stage") == "caught"
            and eye["id"] in trial.get("detected_by", ())
        )
        if caught != detection_overlay:
            continue
        polygon = eye_light_polygon(floor, trial, eye)

        if len(polygon) < 3:
            continue

        lamp_height = tile_size * (52 / 64)
        source_x = (eye["position"][0] + 0.5) * tile_size
        source_y = (
            (eye["position"][1] + 0.5) * tile_size
            - lamp_height
        )
        left = source_x - radius - 2
        top = source_y - radius - 2
        destination = (round(left - context.camera_x), round(top - context.camera_y))
        if not pygame.Rect(
            destination, (radius * 2 + 4, radius * 2 + 4),
        ).colliderect(context.view_surface.get_rect()):
            continue
        points = tuple(
            (
                round(x * tile_size - left),
                round(y * tile_size - (lamp_height if index == 0 else 0) - top),
            )
            for index, (x, y) in enumerate(polygon)
        )
        beam = _beam_surface(radius, points, caught)
        if caught:
            progress = min(1.0, trial["action_ms"] / DETECTION_PAUSE_MS)
            beam.set_alpha(round(225 + 30 * (1.0 - progress) ** 2))
        else:
            beam.set_alpha(255)
        context.view_surface.blit(beam, destination)
        if caught:
            glow = _caught_lamp_glow(tile_size)
            context.view_surface.blit(
                glow,
                (
                    round(source_x - tile_size / 2 - context.camera_x),
                    round(source_y - tile_size / 2 - context.camera_y),
                ),
            )


def draw_trial_layer(context, layer):
    floor = context.floor
    trial = floor.shadow_step_trial

    if trial is None:
        return

    tile_size = ACT_THREE_TILE_SIZE
    assets = trial_assets(tile_size)
    surface = context.view_surface

    def position(cell, height=1):
        return (
            round(cell[0] * tile_size - context.camera_x),
            round((cell[1] - height + 1) * tile_size - context.camera_y),
        )

    if layer == "ground":
        door_index = (
            min(7, trial["opening_ms"] * 8 // DOOR_DURATION_MS)
            if trial["phase"] in ("closed", "opening")
            else 7
        )
        surface.blit(
            assets["door"][door_index],
            position(trial["door"]),
        )

    if trial["phase"] in ("closed", "opening"):
        return

    if layer == "ground":
        animation_tick = trial["animation_ms"] // 120

        for seal in trial["seals"]:
            images = assets["seals"][f"{seal['id']:02d}"]
            active = (
                trial["phase"] == "active"
                and seal["id"] not in trial["activated"]
            )
            image = (
                images["active"][animation_tick % len(images["active"])]
                if active
                else images["inactive"]
            )
            surface.blit(image, position(seal["position"]))

        images = assets["seals"]["final"]
        ready = (
            trial["phase"] == "active"
            and len(trial["activated"]) == 3
        )
        image = (
            images["active"][animation_tick % len(images["active"])]
            if ready
            else images["inactive"]
        )
        surface.blit(image, position(trial["final"]))
        return

    columns = [
        (
            eye["position"],
            assets["eye"][eye_frame(trial, eye)],
        )
        for eye in trial["eyes"]
    ]

    for cell, image in sorted(
        columns,
        key=lambda item: (item[0][1], item[0][0]),
    ):
        in_front = cell[1] >= floor.player_row

        if (layer == "front") == in_front:
            surface.blit(image, position(cell, 2))
