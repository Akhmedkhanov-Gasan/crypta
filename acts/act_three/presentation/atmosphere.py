import math

import pygame


_MAX_DUST_PARTICLES = 28
_HAZE_SURFACES = {}
_ATMOSPHERE_SURFACES = {}


def _get_atmosphere_surface(size):
    atmosphere = _ATMOSPHERE_SURFACES.get(size)

    if atmosphere is None:
        atmosphere = pygame.Surface(
            size,
            pygame.SRCALPHA,
        )
        _ATMOSPHERE_SURFACES[size] = atmosphere

    atmosphere.fill((0, 0, 0, 0))
    return atmosphere


def _get_haze_surface(tile_size):
    haze = _HAZE_SURFACES.get(tile_size)

    if haze is not None:
        return haze

    width = tile_size * 5
    height = tile_size * 3
    small_size = (
        max(1, width // 4),
        max(1, height // 4),
    )

    haze = pygame.Surface(
        small_size,
        pygame.SRCALPHA,
    )

    center_x = small_size[0] // 2
    center_y = small_size[1] // 2

    for ring in range(12, 0, -1):
        scale = ring / 12
        ring_width = max(
            1,
            round(small_size[0] * scale),
        )
        ring_height = max(
            1,
            round(small_size[1] * scale),
        )
        alpha = round(
            12 + (1 - scale) * 28
        )

        pygame.draw.ellipse(
            haze,
            (126, 104, 76, alpha),
            (
                center_x - ring_width // 2,
                center_y - ring_height // 2,
                ring_width,
                ring_height,
            ),
        )

    haze = pygame.transform.smoothscale(
        haze,
        (width, height),
    )

    _HAZE_SURFACES[tile_size] = haze
    return haze


def draw_lit_atmosphere(
    surface,
    torches,
    camera_x,
    camera_y,
    current_time,
    tile_size,
):
    if not torches:
        return

    atmosphere = _get_atmosphere_surface(
        surface.get_size()
    )
    margin = tile_size * 3
    visible_torches = []

    for torch_index, (column, row) in enumerate(torches):
        center_x = (
            column * tile_size
            + tile_size / 2
            - camera_x
        )
        center_y = (
            row * tile_size
            + tile_size / 2
            - camera_y
        )

        if (
            center_x < -margin
            or center_y < -margin
            or center_x > surface.get_width() + margin
            or center_y > surface.get_height() + margin
        ):
            continue

        visible_torches.append(
            (
                torch_index,
                column,
                row,
                center_x,
                center_y,
            )
        )

    if not visible_torches:
        return

    particle_count = min(
        _MAX_DUST_PARTICLES,
        len(visible_torches) * 7,
    )

    for particle_index in range(particle_count):
        (
            torch_index,
            column,
            row,
            center_x,
            center_y,
        ) = visible_torches[
            particle_index % len(visible_torches)
        ]

        local_index = (
            particle_index
            // len(visible_torches)
        )
        seed = (
            column * 73856093
            ^ row * 19349663
            ^ local_index * 83492791
            ^ torch_index * 2654435761
        ) & 0xFFFFFFFF

        duration = 7600 + seed % 4400
        phase = (
            (
                current_time
                + seed % duration
            )
            % duration
        ) / duration

        visibility = math.sin(
            math.pi * phase
        ) ** 2
        angle = (
            (seed >> 8) % 360
        ) * math.pi / 180
        spread = tile_size * (
            0.45
            + ((seed >> 16) % 100) / 100 * 1.45
        )

        particle_x = (
            center_x
            + math.cos(angle) * spread
            + math.sin(
                current_time / 2300
                + seed * 0.0001
            )
            * tile_size
            * 0.12
        )
        particle_y = (
            center_y
            + math.sin(angle) * tile_size * 0.75
            + tile_size * 0.9
            - phase * tile_size * 1.8
        )

        alpha = round(
            (
                    68
                    + seed % 52
            )
            * visibility
        )

        if alpha <= 2:
            continue

        color = (
            (176, 151, 112, alpha)
            if seed % 3 == 0
            else (132, 127, 116, alpha)
        )
        radius = 2 if seed % 4 == 0 else 1

        pygame.draw.line(
            atmosphere,
            color,
            (
                round(particle_x),
                round(particle_y + 1),
            ),
            (
                round(particle_x),
                round(particle_y - 1),
            ),
            radius,
        )

    surface.blit(atmosphere, (0, 0))
