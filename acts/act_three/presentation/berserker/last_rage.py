import math

import pygame


LAST_RAGE_FRAME_COUNT = 8


def last_rage_frame(elapsed, duration):
    progress = max(
        0.0,
        min(1.0, elapsed / duration),
    )

    return min(
        LAST_RAGE_FRAME_COUNT - 1,
        int(progress * LAST_RAGE_FRAME_COUNT),
    )


def last_rage_camera_offset(elapsed, duration):
    shake_duration = min(560, duration)

    if not 0 <= elapsed < shake_duration:
        return (0, 0)

    progress = elapsed / shake_duration
    rise = min(1.0, progress / 0.18)
    fall = (1.0 - progress) ** 2
    strength = 2.6 * rise * fall

    return (
        round(math.sin(elapsed * 0.075) * strength),
        round(math.cos(elapsed * 0.095) * strength * 0.55),
    )


def draw_last_rage_activation_effect(surface, position, elapsed, duration, tile_size, palette=None):
    from acts.act_three.presentation.berserker.effect_brushes import (
        BLOOD, crescent, draw_storm, envelope, mist, shock_dust, spark,
    )

    if not 0 <= elapsed < duration:
        return
    palette = palette or BLOOD
    phase = elapsed / duration
    strength = envelope(phase) ** 0.65
    extent = tile_size * 4
    layer = pygame.Surface((extent, extent), pygame.SRCALPHA)
    center = extent / 2, extent * 0.63
    burst = min(1, phase / 0.48)
    shock_dust(layer, center, tile_size, burst, envelope(burst) * 0.9, palette)
    for side in (0, math.pi):
        crescent(layer, center, tile_size * (0.32 + burst * 0.6),
                 side + phase * 1.3, 1.6, tile_size * 0.09,
                 envelope(burst) * 0.65, palette, flatten=0.36)
    draw_storm(layer, center, tile_size, elapsed * 1.4, strength * 1.25, palette)
    for side in (-1, 1):
        for index in range(5):
            flight = (phase * 1.5 - index * 0.055)
            if not 0 < flight < 1:
                continue
            x = center[0] + side * tile_size * (0.22 + flight * 0.43)
            y = center[1] - math.sin(flight * math.pi * 0.8) * tile_size * (0.6 + index * 0.09)
            mist(layer, (x, y + 6), 12 + index, palette[1], envelope(flight) * 0.24)
            spark(layer, (x, y), (side * 0.5, -0.8), palette[2], envelope(flight) * 0.85, 3)
    surface.blit(layer, (round(position[0] + tile_size / 2 - center[0]),
                         round(position[1] + tile_size * 0.83 - center[1])))
