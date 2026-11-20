import math

import pygame

from acts.act_three.presentation.view import _view_position


SUMMON_EFFECT_MS = 850


def _ground_echo(layer, center, progress, strength, seed, scale):
    radius = scale * (0.22 + progress * 0.28)
    for index in range(4):
        glow = pygame.Rect(0, 0, round(radius * 2), round(radius * 0.65))
        glow.center = center
        pygame.draw.ellipse(layer, (47, 91, 84, round(strength * (30 - index * 5))), glow)
        radius *= 0.78
    for fragment in range(9):
        angle = fragment * math.tau / 9 + seed * 0.37
        points = []
        for step in range(7):
            theta = angle + step * 0.036
            edge = scale * (0.28 + progress * 0.18) * (1 + math.sin(theta * 7 + seed) * 0.08)
            points.append((round(center[0] + math.cos(theta) * edge), round(center[1] + math.sin(theta) * edge * 0.33)))
        pygame.draw.lines(layer, (147, 186, 173, round(145 * strength)), False, points, 1)


def draw_retinue_summon(surface, game_state, camera_x, camera_y, current_time, tile_size):
    state = game_state.player.act_three
    cast = state.archer_phantom_cast
    if cast is None:
        return
    elapsed = current_time - cast["started_at"]
    if cast["floor_index"] != game_state.floor_index or elapsed >= SUMMON_EFFECT_MS:
        state.archer_phantom_cast = None
        return
    if elapsed < 0:
        return
    progress = elapsed / SUMMON_EFFECT_MS
    strength = math.sin(math.pi * progress) ** 0.7
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    x, y = _view_position(*cast["origin"], camera_x, camera_y)
    center = (round(x + tile_size * 0.5), round(y + tile_size * 0.86))
    _ground_echo(layer, center, progress, strength, 1, tile_size * 1.2)
    for index in range(18):
        phase = (progress * 1.4 + index * 0.057) % 1
        angle = index * 2.399 + progress * 2.1
        radius = tile_size * (0.13 + phase * 0.3)
        px = center[0] + math.cos(angle) * radius
        py = center[1] + math.sin(angle) * radius * 0.35 - phase * tile_size * 0.8
        alpha = round(175 * strength * math.sin(phase * math.pi))
        points = [
            (round(px + math.sin(angle + step * 0.3) * 2), round(py + step * 1.8))
            for step in range(5)
        ]
        pygame.draw.lines(layer, (116, 170, 155, alpha), False, points, 1)
        pygame.draw.circle(layer, (206, 222, 209, alpha), points[0], 1)
    for index, position in enumerate(cast["positions"]):
        local_progress = max(0.0, min(1.0, (elapsed - 70 - index * 70) / 650))
        local_strength = math.sin(local_progress * math.pi) ** 0.7
        if local_strength <= 0:
            continue
        gx, gy = _view_position(*position, camera_x, camera_y)
        feet = (round(gx + tile_size * 0.5), round(gy + tile_size * 0.86))
        _ground_echo(layer, feet, local_progress, local_strength, index + 3, tile_size)
        for wisp in range(8):
            angle = wisp * 2.399 + index
            distance = tile_size * (0.1 + (1 - local_progress) * 0.25)
            rise = local_progress * tile_size * (0.35 + wisp % 3 * 0.12)
            point = (
                round(feet[0] + math.cos(angle) * distance),
                round(feet[1] + math.sin(angle) * distance * 0.4 - rise),
            )
            pygame.draw.circle(layer, (150, 197, 185, round(130 * local_strength)), point, 1 + wisp % 2)
    surface.blit(layer, (0, 0))
