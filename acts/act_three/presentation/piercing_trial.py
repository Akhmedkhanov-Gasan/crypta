import math
from functools import lru_cache
from pathlib import Path

import pygame
import resource_store as resources

from acts.act_three.piercing_trial import PUSH_MS, RESET_MS, SHOT_MS, TURN_MS
from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.piercing_trial_effects import draw_target_effects, draw_completion


ROOT = Path(__file__).resolve().parents[3] / "assets/maps/act_3/trials"


@lru_cache(maxsize=4)
def assets(size):
    def load(path):
        return pygame.transform.scale(resources.load_image(str(ROOT / path)).convert_alpha(), (size, size))

    def frames(directory, prefix, count=8):
        return [load(f"{directory}/{prefix}_{index:02d}.png") for index in range(1, count + 1)]

    archer = "archer_piercing_trial"
    return {
        "door": frames("trial_door", "shadow_step_door_open"),
        "launcher": frames(f"{archer}/piercing_trial_column", "piercing_trial_column_rotate"),
        "fragile": frames(f"{archer}/piercing_trial_fragile_column", "piercing_trial_fragile_column_break"),
        "intact": load(f"{archer}/piercing_trial_fragile_column/piercing_trial_fragile_column_idle.png"),
        "movable": load(f"{archer}/piercing_trial_movable_column.png"),
        "rotary": frames("piercing_trial_rotary_lever", "piercing_trial_rotary_lever_turn"),
        "fire": frames("piercing_trial_fire_lever", "piercing_trial_fire_lever_pull"),
        "seals": {
            index: (
                frames(f"{archer}/piercing_trial_seal_{index:02d}_v01", f"piercing_trial_seal_{index:02d}_shimmer"),
                load(f"{archer}/piercing_trial_seal_{index:02d}_v01/piercing_trial_seal_{index:02d}_hit.png"),
            ) for index in range(1, 4)
        },
    }


def screen_position(context, cell):
    size = ACT_THREE_TILE_SIZE
    return round(cell[0] * size - context.camera_x), round(cell[1] * size - context.camera_y)


def moving_column_position(trial, elapsed):
    progress = max(0, min(1, (elapsed - 90) / (PUSH_MS - 150)))
    eased = progress * progress * (3 - 2 * progress)
    origin = trial["push_origin"]
    target = trial["push_target"]
    dx, dy = target[0] - origin[0], target[1] - origin[1]
    tremor = math.sin(progress * math.pi * 14) * math.sin(progress * math.pi) * .009
    return origin[0] + dx * eased - dy * tremor, origin[1] + dy * eased + dx * tremor


def draw_column_dust(context, trial, elapsed):
    size = ACT_THREE_TILE_SIZE
    progress = max(0, min(1, elapsed / PUSH_MS))
    cell = moving_column_position(trial, elapsed)
    x, y = screen_position(context, cell)
    origin, target = trial["push_origin"], trial["push_target"]
    dx, dy = target[0] - origin[0], target[1] - origin[1]
    dust = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    strength = math.sin(progress * math.pi)
    for index in range(9):
        offset = (index - 4) * size * .045
        drift = ((progress * 1.7 + index * .19) % 1) * size * .16
        cx = size - dy * offset - dx * (size * .19 + drift)
        cy = size - size * .1 + dx * offset - dy * (size * .13 + drift)
        radius = max(1, round(size * (.025 + .012 * (index % 3))))
        pygame.draw.circle(dust, (90, 81, 68, round(42 * strength)), (round(cx), round(cy)), radius)
    context.view_surface.blit(dust, (x - size // 2, y))


def draw_layer(context, layer):
    floor = context.floor
    trial = floor.piercing_trial
    if trial is None:
        return
    now = pygame.time.get_ticks()
    elapsed = now - trial["started"]
    sprites = assets(ACT_THREE_TILE_SIZE)
    surface = context.view_surface
    if layer == "ground":
        index = min(7, elapsed * 8 // 640) if trial["phase"] == "opening" else (0 if trial["phase"] == "closed" else 7)
        surface.blit(sprites["door"][index], screen_position(context, trial["door"]))
    if trial["phase"] in ("closed", "opening"):
        return
    if layer == "ground":
        if trial["stage"] == "push":
            draw_column_dust(context, trial, elapsed)
        for target in trial["targets"]:
            if target["id"] in trial.get("destroyed_targets", set()):
                continue
            shimmer, hit = sprites["seals"][target["id"]]
            sprite = hit if target["id"] in trial["activated"] else shimmer[(now // 120) % 8]
            surface.blit(sprite, screen_position(context, target["position"]))
        return
    objects = []
    for launcher in trial["launchers"]:
        direction = launcher["direction"]
        if trial["stage"] == "lever" and trial["lever"] != "fire":
            changes = {"a": (-1, 1, 0), "b": (1, 0, -1)}[trial["lever"]]
            direction += changes[launcher["id"] - 1] * min(1, elapsed / TURN_MS)
        frame = round((direction + 2) * 2) % 8
        objects.append((launcher["position"], sprites["launcher"][frame]))
    for cell in trial["fragile"]:
        sprite = sprites["intact"]
        if cell in trial["broken"]:
            broken_at = trial.get("broken_at", {}).get(cell)
            frame = 7 if broken_at is None else min(7, max(0, now - broken_at) // 70)
            sprite = sprites["fragile"][frame]
        objects.append((cell, sprite))
    for cell in trial["movable"]:
        position = cell
        if trial["stage"] == "push" and cell == trial["push_target"]:
            position = moving_column_position(trial, elapsed)
        objects.append((position, sprites["movable"]))
    for key, cell in trial["levers"].items():
        index = 0
        if trial.get("lever") == key:
            if trial["stage"] == "lever":
                index = min(7, elapsed * 8 // TURN_MS)
            elif trial["stage"] in ("shot", "reset", "restore_targets"):
                index = 7
            elif trial["stage"] == "return":
                index = max(0, 7 - elapsed * 8 // 220)
        objects.append((cell, sprites["fire" if key == "fire" else "rotary"][index]))
    for cell, sprite in sorted(objects, key=lambda item: (item[0][1], item[0][0])):
        if (layer == "front") == (cell[1] >= floor.player_row):
            surface.blit(sprite, screen_position(context, cell))


@lru_cache(maxsize=1)
def hint_font():
    return pygame.font.SysFont("consolas", 14)


def draw_arrow(surface, tip, direction, size, rejected=False):
    length = max(18, round(size * .46))
    head = max(6, round(size * .12))
    width = max(3, round(size * .055))
    dx, dy = direction
    nx, ny = -dy, dx

    def point(back, side=0):
        return round(tip[0] - dx * back + nx * side), round(tip[1] - dy * back + ny * side)

    pygame.draw.line(surface, (30, 25, 22), point(head - 1), point(length), 4)
    pygame.draw.line(surface, (151, 116, 72), point(head - 1), point(length), 2)
    metal = (184, 86, 68) if rejected else (193, 197, 188)
    pygame.draw.polygon(surface, (43, 46, 43), [point(-1), point(head + 1, width + 1), point(head + 1, -width - 1)])
    pygame.draw.polygon(surface, metal, [point(0), point(head, width), point(head - 2), point(head, -width)])
    for side in (-1, 1):
        pygame.draw.polygon(surface, (151, 153, 137), [
            point(length - 9), point(length - 4, side * width),
            point(length + 1, side * width), point(length - 3),
        ])


def draw_overlay(context):
    floor = context.floor
    trial = floor.piercing_trial
    if trial is None:
        return
    surface = context.view_surface
    size = ACT_THREE_TILE_SIZE
    now = pygame.time.get_ticks()
    elapsed = now - trial["started"]

    def center(cell):
        x, y = screen_position(context, cell)
        return x + size // 2, y + size // 2

    if trial["stage"] in ("shot", "reset"):
        for path in trial["paths"]:
            cells = path["cells"]
            if len(cells) < 2:
                continue
            wrong = any(hit != path["id"] for hit in path["hits"])
            progress = min(1, elapsed / SHOT_MS) if trial["stage"] == "shot" else 1
            start, end = center(cells[0]), center(cells[-1])
            tip = (round(start[0] + (end[0] - start[0]) * progress), round(start[1] + (end[1] - start[1]) * progress))
            distance = math.hypot(end[0] - start[0], end[1] - start[1])
            direction = ((end[0] - start[0]) / distance, (end[1] - start[1]) / distance)
            if trial["stage"] == "shot" or wrong:
                draw_arrow(surface, tip, direction, size, rejected=trial["stage"] == "reset")
    draw_target_effects(context, trial, now)
    if trial["stage"] in ("reset", "recover"):
        veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        alpha = (
            round(205 * max(0, 1 - elapsed / 350))
            if trial["stage"] == "recover"
            else round(205 * math.sin(min(1, elapsed / RESET_MS) * math.pi / 2))
        )
        veil.fill((24, 5, 8, alpha))
        surface.blit(veil, (0, 0))
    draw_completion(context, trial, now)
    if trial["phase"] in ("closed", "opening"):
        return
    for launcher in trial["launchers"]:
        if launcher["position"] in floor.visible_cells:
            label = hint_font().render(str(launcher["id"]), True, (195, 202, 154))
            x, y = screen_position(context, launcher["position"])
            surface.blit(label, label.get_rect(midbottom=(x + size // 2, y + 8)))
