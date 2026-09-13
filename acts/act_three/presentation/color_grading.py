import math

import pygame


_GRADE_MASK_ALPHA = 28
_LIGHT_PRESERVE_SURFACES = {}
_GRADE_MASK_SURFACES = {}
_VIGNETTE_SURFACES = {}


def _get_grade_mask(size):
    mask = _GRADE_MASK_SURFACES.get(size)

    if mask is None:
        mask = pygame.Surface(
            size,
            pygame.SRCALPHA,
        )
        _GRADE_MASK_SURFACES[size] = mask

    mask.fill(
        (
            255,
            255,
            255,
            _GRADE_MASK_ALPHA,
        )
    )
    return mask


def _get_light_preserve_surface(
    tile_size,
    scale,
):
    radius = max(
        1,
        round(tile_size * 2.45 * scale),
    )
    cached = _LIGHT_PRESERVE_SURFACES.get(radius)

    if cached is not None:
        return cached

    preserve = pygame.Surface(
        (radius * 2, radius * 2),
        pygame.SRCALPHA,
    )

    for current_radius in range(radius, 0, -1):
        proximity = (
            1 - current_radius / radius
        )
        alpha = round(
            _GRADE_MASK_ALPHA
            * proximity**1.35
        )

        pygame.draw.circle(
            preserve,
            (0, 0, 0, alpha),
            (radius, radius),
            current_radius,
        )

    preserve = pygame.transform.gaussian_blur(
        preserve,
        3,
    )

    _LIGHT_PRESERVE_SURFACES[radius] = preserve
    return preserve


def _get_vignette_surface(size):
    vignette = _VIGNETTE_SURFACES.get(size)

    if vignette is not None:
        return vignette

    small_size = (
        max(1, size[0] // 8),
        max(1, size[1] // 8),
    )
    small_vignette = pygame.Surface(
        small_size,
        pygame.SRCALPHA,
    )

    center_x = (small_size[0] - 1) / 2
    center_y = (small_size[1] - 1) / 2
    horizontal_radius = max(1, center_x)
    vertical_radius = max(1, center_y)

    for y in range(small_size[1]):
        normalized_y = (
            y - center_y
        ) / vertical_radius

        for x in range(small_size[0]):
            normalized_x = (
                x - center_x
            ) / horizontal_radius
            distance = math.sqrt(
                normalized_x * normalized_x
                + normalized_y * normalized_y
            )
            edge = max(
                0,
                min(
                    1,
                    (distance - 0.62) / 0.48,
                ),
            )
            smooth_edge = (
                edge
                * edge
                * (3 - 2 * edge)
            )
            alpha = round(
                42 * smooth_edge
            )

            small_vignette.set_at(
                (x, y),
                (0, 1, 4, alpha),
            )

    vignette = pygame.transform.smoothscale(
        small_vignette,
        size,
    )
    _VIGNETTE_SURFACES[size] = vignette
    return vignette


def draw_act_three_color_grading(
    surface,
    torches,
    camera_x,
    camera_y,
    tile_size,
):
    surface_width = surface.get_width()
    surface_height = surface.get_height()
    work_size = (
        max(1, surface_width // 4),
        max(1, surface_height // 4),
    )
    scale_x = work_size[0] / surface_width
    scale_y = work_size[1] / surface_height
    scale = min(scale_x, scale_y)

    reduced = pygame.transform.smoothscale(
        surface,
        work_size,
    )
    grading = pygame.transform.grayscale(
        reduced
    ).convert_alpha()
    grading.fill(
        (0, 3, 8, 0),
        special_flags=pygame.BLEND_RGBA_ADD,
    )

    grade_mask = _get_grade_mask(work_size)
    light_preserve = _get_light_preserve_surface(
        tile_size,
        scale,
    )

    for column, row in torches:
        center_x = (
            column * tile_size
            + tile_size / 2
            - camera_x
        ) * scale_x
        center_y = (
            row * tile_size
            + tile_size * 0.85
            - camera_y
        ) * scale_y

        preserve_rectangle = (
            light_preserve.get_rect(
                center=(
                    round(center_x),
                    round(center_y),
                )
            )
        )
        grade_mask.blit(
            light_preserve,
            preserve_rectangle,
            special_flags=pygame.BLEND_RGBA_SUB,
        )

    grading.blit(
        grade_mask,
        (0, 0),
        special_flags=pygame.BLEND_RGBA_MULT,
    )
    grading = pygame.transform.smoothscale(
        grading,
        surface.get_size(),
    )

    surface.blit(grading, (0, 0))
    surface.blit(
        _get_vignette_surface(
            surface.get_size()
        ),
        (0, 0),
    )
