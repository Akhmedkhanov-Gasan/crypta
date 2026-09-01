import json
from pathlib import Path

import pygame

from presentation.figma_ui import figma_rect


_PROJECT_ROOT = Path(__file__).resolve().parents[4]


def load_oracle_ui():
    layout_path = (
        _PROJECT_ROOT
        / "assets/ui/layouts/act_2/oracle.json"
    )

    with layout_path.open(encoding="utf-8") as file:
        layout = json.load(file)

    if (
        layout["screen"] != "oracle"
        or layout["act"] != 2
        or layout["frame"]["width"] != 1280
        or layout["frame"]["height"] != 720
    ):
        raise ValueError(
            "Expected an Oracle_Act2 layout at 1280x720."
        )

    elements = {
        "frame": layout["boss_hp"]["frame"],
        "fill": layout["boss_hp"]["hp_bar"],
        "introduce": layout["oracle_introduce"],
    }

    assets = {}

    for name, element in elements.items():
        rectangle = figma_rect(element["rect"])
        path = _PROJECT_ROOT / element["asset"]

        source = pygame.image.load(str(path)).convert_alpha()
        assets[name] = pygame.transform.scale(
            source,
            rectangle.size,
        )
        assets[f"{name}_rect"] = rectangle

    empty_fill = pygame.Surface(assets["fill"].get_size())
    empty_fill.fill((16, 5, 8))

    darkened_fill = assets["fill"].copy()
    darkened_fill.fill(
        (55, 45, 50, 255),
        special_flags=pygame.BLEND_RGBA_MULT,
    )
    empty_fill.blit(darkened_fill, (0, 0))
    assets["empty_fill"] = empty_fill

    return layout, assets


def draw_oracle_ui(
    screen,
    floor,
    layout,
    assets,
    *,
    introduce_elapsed_ms=None,
    introduce_hold_ms=1800,
):
    oracle = next(
        (
            enemy
            for enemy in floor.enemies
            if (
                enemy["type"] == "oracle"
                and enemy["health"] > 0
                and enemy["is_active"]
            )
        ),
        None,
    )

    if oracle is not None:
        frame_rect = assets["frame_rect"]
        fill_rect = assets["fill_rect"]

        screen.blit(assets["empty_fill"], fill_rect)

        phase_two = floor.oracle_phase_two
        defeated_pending = (
            phase_two is not None
            and phase_two.defeated_pending
        )

        health_ratio = (
            0.0
            if defeated_pending
            else max(
                0.0,
                min(
                    1.0,
                    oracle["health"]
                    / max(1, oracle["max_health"]),
                ),
            )
        )
        visible_width = round(fill_rect.width * health_ratio)

        if visible_width > 0:
            screen.blit(
                assets["fill"],
                fill_rect.topleft,
                pygame.Rect(
                    0,
                    0,
                    visible_width,
                    fill_rect.height,
                ),
            )

        screen.blit(assets["frame"], frame_rect)

    if introduce_elapsed_ms is None:
        return

    elapsed = introduce_elapsed_ms
    if elapsed < 0:
        return

    introduction = layout["oracle_introduce"]
    fade_in = max(1, int(introduction["fade_in_ms"]))
    fade_out = max(1, int(introduction["fade_out_ms"]))
    hold = max(0, int(introduce_hold_ms))

    fade_out_start = fade_in + hold
    total_duration = fade_out_start + fade_out

    if elapsed >= total_duration:
        return

    if elapsed < fade_in:
        opacity = elapsed / fade_in
    elif elapsed < fade_out_start:
        opacity = 1.0
    else:
        opacity = 1.0 - (elapsed - fade_out_start) / fade_out


    opacity = max(0.0, min(1.0, opacity))
    opacity = opacity * opacity * (3.0 - 2.0 * opacity)

    introduce_surface = assets["introduce"].copy()
    introduce_surface.set_alpha(round(255 * opacity))
    screen.blit(
        introduce_surface,
        assets["introduce_rect"],
    )
