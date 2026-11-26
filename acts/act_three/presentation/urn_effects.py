import math
import random
from array import array
from functools import lru_cache

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE


@lru_cache(maxsize=8)
def _urn_sound(stage, mixer_format):
    frequency, sample_format, channels = mixer_format
    if sample_format != -16:
        return None
    rng = random.Random(83 + stage)
    duration = 0.8 + stage * 0.18
    samples = array("h")
    for index in range(round(frequency * duration)):
        time = index / frequency
        envelope = math.sin(math.pi * time / duration) ** 2
        rattle = rng.uniform(-1, 1) * (0.05 + 0.09 * math.sin(time * 47) ** 8)
        hum = math.sin(math.tau * (59 + stage * 7) * time) * 0.13
        value = round(32767 * envelope * (rattle + hum))
        samples.extend([value] * channels)
    return pygame.mixer.Sound(buffer=samples.tobytes())


def play_urn_sound(stage):
    mixer_format = pygame.mixer.get_init()
    if mixer_format is None:
        return
    sound = _urn_sound(stage, mixer_format)
    if sound is not None:
        sound.set_volume(0.26)
        sound.play()


def urn_camera_shake(floor, current_time):
    effect = floor.trader_urn_effect
    if effect is None or effect["kind"] != "altar":
        return 0, 0
    elapsed = current_time - effect["started_at"]
    if not 0 <= elapsed < 4200:
        return 0, 0
    seconds = elapsed / 1000
    strength = min(1, seconds * 2) * (1 - elapsed / 4200) * 3
    return round(math.sin(seconds * 53) * strength), round(math.sin(seconds * 71) * strength * 0.7)


def _draw_altar_effect(context, assets, effect, elapsed):
    progress = elapsed / 4200
    time = elapsed / 1000
    tile = ACT_THREE_TILE_SIZE
    size = tile * 7
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    fade = min(1.0, time * 2) * min(1.0, (1 - progress) * 4)
    pulse = 0.85 + math.sin(time * 8) * 0.15
    radius = tile * (1.15 + math.sin(math.pi * progress) * 0.4)
    for index in range(20, 0, -1):
        spread = radius * index / 12
        bounds = pygame.Rect(round(cx - spread), round(cy - spread * 0.5), round(spread * 2), round(spread))
        pygame.draw.ellipse(layer, (9, 6, 15, round(fade * (6 + (20 - index) * 1.2))), bounds)
    for index in range(3):
        ring_radius = radius + index * 9
        bounds = pygame.Rect(round(cx - ring_radius), round(cy - ring_radius * 0.42), round(ring_radius * 2), round(ring_radius * 0.84))
        pygame.draw.ellipse(layer, (117, 91, 130, round(fade * pulse * (165 - index * 40))), bounds, 1)
    for index in range(12):
        angle = math.tau * index / 12 + time * 0.08
        x = cx + math.cos(angle) * (radius + 18)
        y = cy + math.sin(angle) * (radius + 18) * 0.42
        color = (153, 125, 146, round(190 * fade * pulse))
        points = [(round(x - 4), round(y + 5)), (round(x), round(y - 7)), (round(x + 4), round(y + 4))]
        pygame.draw.lines(layer, color, False, points, 1)
        pygame.draw.line(layer, color, (round(x - 5), round(y - 1)), (round(x + 5), round(y - 1)), 1)
        if index % 2 == 0:
            pygame.draw.line(layer, color, (round(x), round(y - 7)), (round(x + 5), round(y - 10)), 1)
    for index in range(45):
        phase = (progress * 1.2 + index * 0.137) % 1
        angle = index * 2.399 + phase * 1.8
        distance = tile * (0.25 + (1 - phase) * 2.1)
        x = cx + math.cos(angle) * distance
        y = cy + math.sin(angle) * distance * 0.42 - phase * tile * 0.6
        alpha = round(fade * math.sin(math.pi * phase) * 105)
        pygame.draw.circle(layer, (34, 21, 43, alpha), (round(x), round(y)), 7 + index % 11)
        if index % 3 == 0:
            pygame.draw.circle(layer, (145, 113, 136, alpha), (round(x), round(y)), 1)
    for index in range(7):
        points = []
        for segment in range(24):
            height = segment / 23
            twist = index * math.tau / 7 + time * 0.9 + height * 4
            spread = tile * (0.15 + height * 0.9) * math.sin(math.pi * progress) ** 0.6
            points.append((round(cx + math.sin(twist) * spread), round(cy - height * tile * 2.2 + math.cos(twist) * spread * 0.2)))
        pygame.draw.lines(layer, (91, 60, 103, round(fade * 100)), False, points, 2)
    shock = min(1, progress * 1.6)
    shock_radius = tile * (0.5 + shock * 2.1)
    pygame.draw.ellipse(
        layer, (143, 121, 131, round(130 * fade * (1 - shock))),
        pygame.Rect(round(cx - shock_radius), round(cy - shock_radius * 0.4), round(shock_radius * 2), round(shock_radius * 0.8)), 2,
    )
    image = assets.get("act_three_consumable_original_sprites", {}).get("sealed_urn")
    if image is not None and progress < 0.82:
        dissolve = min(1.0, max(0.0, (progress - 0.42) / 0.4))
        scale = 1 - dissolve * 0.35
        bounds = image.get_rect().fit(pygame.Rect(0, 0, round(tile * 0.7 * scale), round(tile * 0.9 * scale)))
        sprite = pygame.transform.smoothscale(image, bounds.size)
        sprite.set_alpha(round(255 * min(1, time * 4) * (1 - dissolve)))
        lift = math.sin(min(1, progress / 0.65) * math.pi) * tile * 0.5
        layer.blit(sprite, sprite.get_rect(midbottom=(cx, round(cy - 5 - lift))))
    x, y = effect["position"]
    center = x * tile + tile // 2 - context.camera_x, y * tile + tile // 2 - context.camera_y
    context.view_surface.blit(layer, (round(center[0] - cx), round(center[1] - cy)))


def draw_urn_effect(context, game_state, assets, current_time):
    effect = context.floor.trader_urn_effect
    if effect is None:
        return
    elapsed = current_time - effect["started_at"]
    duration = 4200 if effect["kind"] == "altar" else 1600
    if elapsed < 0 or elapsed >= duration:
        context.floor.trader_urn_effect = None
        return
    if effect["kind"] == "altar":
        _draw_altar_effect(context, assets, effect, elapsed)
        return
    progress = elapsed / 1600
    tile = ACT_THREE_TILE_SIZE
    x, y = effect["position"]
    center = (x * tile + tile // 2 - context.camera_x, y * tile + tile // 2 - context.camera_y)
    layer = pygame.Surface((tile * 5, tile * 5), pygame.SRCALPHA)
    origin = tile * 2.5, tile * 2.5
    color = (125, 67, 150) if effect["kind"] == "burst" else (100, 139, 127)
    for index in range(22):
        angle = index * 2.4 + progress * 3
        radius = (15 + index % 5 * 9) * (1 + progress * 2)
        point = (
            round(origin[0] + math.cos(angle) * radius),
            round(origin[1] + math.sin(angle) * radius * 0.5 - progress * 55),
        )
        pygame.draw.circle(layer, (*color, round(110 * (1 - progress))), point, 3 + index % 4)
    pygame.draw.ellipse(
        layer, (*color, round(180 * (1 - progress))),
        pygame.Rect(round(origin[0] - 45 - progress * 35), round(origin[1] - 18), round(90 + progress * 70), 36),
        width=2,
    )
    context.view_surface.blit(layer, (round(center[0] - origin[0]), round(center[1] - origin[1])))
