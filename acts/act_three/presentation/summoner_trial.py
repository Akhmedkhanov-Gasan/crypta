import math
from functools import lru_cache
from pathlib import Path

import pygame
import resource_store as resources

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.summoner_trial import DURATIONS, EATING_LEAD_MS, EATING_FRAME_MS, aboard, boat_position, interaction
from acts.act_three.presentation.trial_door import door_frames
from acts.act_three.presentation.piercing_trial import screen_position


ROOT = Path(__file__).resolve().parents[3] / "assets/maps/act_3/trials/summoner_release_familiar"


@lru_cache(maxsize=32)
def frames(kind):
    specs = {
        "boat": ("summoner_trial_boat_idle_v01", "summoner_trial_boat_idle", 8, 2, 1),
        "familiar": ("summoner_trial_familiar_idle", "idle_left", 8, 1, 1),
        "grub": ("summoner_trial_grave_grub_idle_v01", "summoner_trial_grave_grub_idle", 8, 1, 1),
        "root": ("summoner_trial_moon_root_v01", "summoner_trial_moon_root", 1, 1, 1),
        "eat_familiar": ("summoner_trial_familiar_eat_grub_up_v01", "summoner_trial_familiar_eat_grub_up", 8, 1, 2),
        "eat_grub": ("summoner_trial_grub_eat_root_up_v01", "summoner_trial_grub_eat_root_up", 8, 1, 2),
    }
    if kind.startswith("sail_"):
        _, cargo, direction = kind.split("_")
        prefix = f"summoner_trial_boat_{cargo}_{direction}"
        suffix = "_v01" if direction == "left" and cargo != "familiar" else ""
        spec = prefix + suffix, prefix, 8, 2, 1
    else:
        spec = specs[kind]
    directory, prefix, count, width, height = spec
    size = ACT_THREE_TILE_SIZE
    return tuple(pygame.transform.smoothscale(resources.load_image(str(ROOT / directory / f"{prefix}_{index:02d}.png")).convert_alpha(), (width * size, height * size)) for index in range(1, count + 1))


def draw_sprite(context, kind, cell, now, alpha=255, frame=None):
    sequence = frames(kind)
    image = sequence[(now // 160) % len(sequence) if frame is None else min(len(sequence) - 1, max(0, frame))]
    if alpha != 255:
        image = image.copy()
        image.set_alpha(round(max(0, min(255, alpha))))
    context.view_surface.blit(image, screen_position(context, cell))


def draw_enter_zone(context, trial, now):
    size = ACT_THREE_TILE_SIZE
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    active = trial["active"]
    pulse = .8 + .2 * math.sin(now / 750)
    color = (109, 177, 172, round(195 * pulse)) if active else (79, 111, 115, 125)
    if trial["phase"] == "complete":
        color = (58, 76, 79, 85)
    for index in range(6):
        angle = math.tau * index / 6 - math.pi / 2
        points = []
        for offset, radius in ((-.38, .14), (-.18, .31), (0, .43), (.18, .31), (.38, .14)):
            a = angle + offset
            points.append((round(size * (.5 + math.cos(a) * radius)), round(size * (.53 + math.sin(a) * radius * .56))))
        pygame.draw.polygon(image, (*color[:3], color[3] // 5), points)
        pygame.draw.aalines(image, color, True, points)
        stem = (round(size * (.5 + math.cos(angle) * .09)), round(size * (.53 + math.sin(angle) * .09 * .56)))
        pygame.draw.aaline(image, color, stem, points[2])
    for sign in (-1, 1):
        curve = []
        for index in range(18):
            t = index / 17
            curve.append((round(size * (.5 + sign * (.04 + .1 * math.sin(t * math.pi)))), round(size * (.36 + .31 * t))))
        pygame.draw.aalines(image, color, False, curve)
    x, y = screen_position(context, trial["enter_zone"])
    context.view_surface.blit(image, (x, y))


def draw_ground(context):
    trial = context.floor.summoner_trial
    if trial is None:
        return
    now = pygame.time.get_ticks()
    elapsed = now - trial["started"]
    phase = trial["phase"]
    frame = min(7, elapsed // 80) if phase == "opening" else (0 if phase == "closed" else 7)
    context.view_surface.blit(door_frames()[frame], screen_position(context, trial["door"]))
    if phase not in ("closed", "opening"):
        draw_enter_zone(context, trial, now)
    on_boat = aboard(trial, now)
    eating = (phase == "eating" and elapsed >= EATING_LEAD_MS) or (phase == "reset" and not trial["transferred"] and "eating_pair" in trial)
    suppressed = set(trial["eating_pair"]) if eating else set()
    if trial["active"]:
        for index, kind in enumerate(("familiar", "grub", "root")):
            if index in suppressed or (on_boat and index == trial["passenger"]):
                continue
            cell = trial["positions"][trial["parts"][index]][index]
            draw_sprite(context, kind, cell, now)
    if on_boat:
        target_side = trial["side"] if phase == "landing" else 1 - trial["side"]
        direction = "right" if trial["docks"][target_side][0] > trial["docks"][1 - target_side][0] else "left"
        passenger = trial["passenger"]
        cargo = ("familiar", "grub", "root")[passenger] if passenger is not None else "sail"
        draw_sprite(context, f"sail_{cargo}_{direction}", boat_position(trial, now), now)
    else:
        draw_sprite(context, "boat", trial["docks"][trial["side"]], now)
    if eating:
        pair = trial["eating_pair"]
        anchor = trial["positions"][trial["eating_side"]][pair[1]]
        kind = "eat_familiar" if pair == (0, 1) else "eat_grub"
        frame = 7 if phase == "reset" else min(7, max(0, (elapsed - EATING_LEAD_MS) // EATING_FRAME_MS))
        draw_sprite(context, kind, anchor, now, frame=frame)


@lru_cache(maxsize=1)
def hint_font():
    return pygame.font.SysFont("consolas", 14)


def draw_overlay(context, game_state, now):
    trial = context.floor.summoner_trial
    if trial is None:
        return
    elapsed = now - trial["started"]
    phase = trial["phase"]
    if phase == "active":
        choice = interaction(game_state)
        if choice is not None:
            kind, index = choice
            if kind == "part":
                cell = trial["positions"][trial["side"]][index]
                text = ("T: Familiar", "T: Grave grub", "T: Moon root")[index]
            else:
                cell = trial["starts"][trial["side"]]
                text = "T: Sail empty"
            x, y = screen_position(context, cell)
            label = hint_font().render(text, True, (181, 216, 210))
            rect = label.get_rect(midbottom=(x + ACT_THREE_TILE_SIZE // 2, y + 5))
            shade = pygame.Surface(rect.inflate(12, 6).size, pygame.SRCALPHA)
            shade.fill((7, 14, 18, 210))
            context.view_surface.blit(shade, rect.inflate(12, 6))
            context.view_surface.blit(label, rect)
    if phase == "completion" and elapsed < 3950:
        draw_completion(context, trial, elapsed)
    duration = DURATIONS.get(phase, 1)
    alpha = 0
    if phase in ("entering", "leaving", "reset"):
        alpha = max(0, min(1, elapsed / (duration / 2), (duration - elapsed) / (duration / 2)))
    elif phase == "boarding":
        alpha = max(0, min(1, elapsed / 300, (600 - elapsed) / 300)) * .85
    elif phase == "landing":
        alpha = max(0, min(1, elapsed / 300, (600 - elapsed) / 300)) * .85
    elif phase == "completion" and elapsed >= 3500:
        alpha = max(0, min(1, (elapsed - 3500) / 450, (4400 - elapsed) / 450))
    if alpha:
        shade = pygame.Surface(context.view_surface.get_size(), pygame.SRCALPHA)
        shade.fill((3, 7, 10, round(255 * alpha)))
        context.view_surface.blit(shade, (0, 0))


def draw_completion(context, trial, elapsed):
    from acts.act_three.presentation.ability_unlock_banner import draw_unlock_banner
    from acts.act_three.presentation.trial_apparitions import apparition, ease, ground_veil, texture

    strength = max(0, min(1, elapsed / 600, (3950 - elapsed) / 800))
    size = ACT_THREE_TILE_SIZE
    x, y = screen_position(context, trial["completion_origin"])
    release = ease((elapsed - 2700) / 1100)
    reveal = ease(elapsed / 1050) * (1 - release)
    center = x + size / 2, y - size * (.55 + .22 * ease(elapsed / 1500)) - release * size * .3
    layer = pygame.Surface(context.view_surface.get_size(), pygame.SRCALPHA)
    layer.fill((3, 9, 13, round(90 * strength)))
    ground_veil(layer, "summoner", center[0], y + size * .7, size, strength * (1 - release), elapsed, outward=True)
    halo = texture("summoner", round(size * 4.9), round(size * 4.9), blurred=True).copy()
    halo.fill((58, 117, 125, 255), special_flags=pygame.BLEND_RGBA_MULT)
    halo.set_alpha(round(65 * strength * reveal))
    layer.blit(halo, halo.get_rect(center=center))
    apparition(layer, "summoner", center, (round(size * 4.4), round(size * 4.4)), 205 * strength, reveal, elapsed, drift=3, spread=release * 12)
    context.view_surface.blit(layer, (0, 0))
    draw_unlock_banner(context.view_surface, max(0, elapsed - 500), "RELEASE FAMILIAR", (158, 210, 208), (103, 148, 154), (5, 12, 17))
