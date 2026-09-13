import math

import pygame

_AMBIENT_COLOR = (3, 6, 12, 82)
_TORCH_LIGHT_RADIUS = 148
_TORCH_WALL_GLOW_RADIUS = 152
_TORCH_LIGHT_LEVELS = 12
_AMBIENT_SURFACES = {}
_LIGHT_MAP_SURFACES = {}

_TORCH_LIGHT_SURFACES = {}
_TORCH_WALL_GLOW_SURFACES = {}
_OCCLUDED_TORCH_LIGHT_SURFACES = {}
_ACTOR_SHADOW_SURFACES = {}
_DIRECTIONAL_ACTOR_SHADOWS = {}
_DIRECTIONAL_SHADOW_COUNT = 24
_TORCH_FLAME_SEQUENCE = (0, 1, 2, 3, 3, 2, 1, 0)
_TORCH_FLAME_FRAME_DURATION_MS = 420

_IDLE_FRAME_SEQUENCE = (0, 1, 2, 1)
_IDLE_TIMELINE_CYCLE_COUNT = 4
_MOVE_FRAME_COUNT = 2
_MOVE_FRAME_DURATION_MS = 90
_ATTACK_FRAME_DURATION_MS = 240
_FAMILIAR_MOVE_DURATION_MS = 180
_TELEPORT_CAMERA_DURATION_MS = 480
_TELEPORT_EFFECT_DURATION_MS = 600
_ARCHER_BARRAGE_SHOT_EFFECT_MS = 360
_TOP_VOID_CORNER_Y_OFFSET = 47
_TOP_VOID_CORNER_X_OFFSETS = {
    "wall_corner_top_left": -18,
    "wall_corner_top_right": 18,
}
_TOP_VOID_DOUBLE_CORNER_CROP_WIDTH = 24



def _get_ambient_surface(size):
    ambient = _AMBIENT_SURFACES.get(size)

    if ambient is None:
        ambient = pygame.Surface(size, pygame.SRCALPHA)
        ambient.fill(_AMBIENT_COLOR)
        _AMBIENT_SURFACES[size] = ambient

    return ambient


def _get_light_map_surface(size):
    light_map = _LIGHT_MAP_SURFACES.get(size)

    if light_map is None:
        light_map = pygame.Surface(size)
        _LIGHT_MAP_SURFACES[size] = light_map

    light_map.fill((0, 0, 0))
    return light_map


def _build_torch_glow(radius, level):
    strength = 0.94 + (
        level / (_TORCH_LIGHT_LEVELS - 1)
    ) * 0.06

    glow = pygame.Surface(
        (radius * 2, radius * 2)
    )
    glow.fill((0, 0, 0))

    for current_radius in range(radius, 0, -1):
        outer_proximity = (
            1 - current_radius / radius
        )
        outer_intensity = (
            outer_proximity**1.55
        )

        core_proximity = max(
            0,
            1 - current_radius / 52,
        )
        core_intensity = (
            core_proximity**1.8
        )

        color = (
            round(
                (
                    12 * outer_intensity
                    + 4 * core_intensity
                )
                * strength
            ),
            round(
                (
                    9 * outer_intensity
                    + 3 * core_intensity
                )
                * strength
            ),
            round(
                (
                    6 * outer_intensity
                    + core_intensity
                )
                * strength
            ),
        )

        pygame.draw.circle(
            glow,
            color,
            (radius, radius),
            current_radius,
        )

    return pygame.transform.gaussian_blur(
        glow,
        10,
    )


def _get_torch_light_surface(level):
    light_surface = _TORCH_LIGHT_SURFACES.get(level)

    if light_surface is None:
        light_surface = _build_torch_glow(
            _TORCH_LIGHT_RADIUS,
            level,
        )
        _TORCH_LIGHT_SURFACES[level] = light_surface

    return light_surface


def _get_torch_wall_glow_surface(level):
    glow = _TORCH_WALL_GLOW_SURFACES.get(level)

    if glow is None:
        glow = _build_torch_glow(
            _TORCH_WALL_GLOW_RADIUS,
            level,
        )
        _TORCH_WALL_GLOW_SURFACES[level] = glow

    return glow


def _barrier_segment(barrier, tile_size):
    first, second = barrier
    first_column, first_row = first
    second_column, second_row = second

    if (
        first_row == second_row
        and abs(first_column - second_column) == 1
    ):
        boundary_x = max(
            first_column,
            second_column,
        ) * tile_size
        top = first_row * tile_size

        return (
            (boundary_x, top),
            (boundary_x, top + tile_size),
        )

    if (
        first_column == second_column
        and abs(first_row - second_row) == 1
    ):
        boundary_y = max(
            first_row,
            second_row,
        ) * tile_size
        left = first_column * tile_size

        return (
            (left, boundary_y),
            (left + tile_size, boundary_y),
        )

    return None


def _distance_to_segment(point, start, end):
    segment_x = end[0] - start[0]
    segment_y = end[1] - start[1]
    segment_length_squared = (
        segment_x * segment_x
        + segment_y * segment_y
    )

    if segment_length_squared == 0:
        return math.hypot(
            point[0] - start[0],
            point[1] - start[1],
        )

    projection = (
        (point[0] - start[0]) * segment_x
        + (point[1] - start[1]) * segment_y
    ) / segment_length_squared
    projection = max(0, min(1, projection))

    nearest = (
        start[0] + segment_x * projection,
        start[1] + segment_y * projection,
    )

    return math.hypot(
        point[0] - nearest[0],
        point[1] - nearest[1],
    )


def _nearest_point_on_segment(point, start, end):
    segment_x = end[0] - start[0]
    segment_y = end[1] - start[1]
    segment_length_squared = (
        segment_x * segment_x
        + segment_y * segment_y
    )

    if segment_length_squared == 0:
        return start

    projection = (
        (point[0] - start[0]) * segment_x
        + (point[1] - start[1]) * segment_y
    ) / segment_length_squared
    projection = max(0, min(1, projection))

    return (
        start[0] + segment_x * projection,
        start[1] + segment_y * projection,
    )


def _torch_light_source(
    column,
    row,
    barrier_key,
    tile_size,
):
    marker_position = (
        column * tile_size + tile_size / 2,
        row * tile_size + tile_size / 2,
    )
    nearest_point = None
    nearest_distance = float("inf")

    for barrier in barrier_key:
        segment = _barrier_segment(
            barrier,
            tile_size,
        )

        if segment is None:
            continue

        candidate = _nearest_point_on_segment(
            marker_position,
            segment[0],
            segment[1],
        )
        distance = math.hypot(
            candidate[0] - marker_position[0],
            candidate[1] - marker_position[1],
        )

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_point = candidate

    if (
        nearest_point is None
        or nearest_distance > tile_size * 0.8
    ):
        return marker_position

    direction_x = (
        nearest_point[0] - marker_position[0]
    )
    direction_y = (
        nearest_point[1] - marker_position[1]
    )
    direction_length = math.hypot(
        direction_x,
        direction_y,
    )

    if direction_length < 1:
        return marker_position

    crossing_distance = tile_size * 0.34
    total_distance = (
        direction_length + crossing_distance
    )

    return (
        marker_position[0]
        + direction_x / direction_length
        * total_distance,
        marker_position[1]
        + direction_y / direction_length
        * total_distance,
    )

def _project_away(source, point, distance):
    direction_x = point[0] - source[0]
    direction_y = point[1] - source[1]
    length = math.hypot(direction_x, direction_y)

    if length == 0:
        return point

    return (
        point[0] + direction_x / length * distance,
        point[1] + direction_y / length * distance,
    )


def _get_occluded_torch_light_surface(
    column,
    row,
    level,
    barrier_key,
    tile_size,
):
    key = (
        column,
        row,
        level,
        barrier_key,
        tile_size,
    )
    cached = _OCCLUDED_TORCH_LIGHT_SURFACES.get(key)

    if cached is not None:
        return cached

    radius = _TORCH_LIGHT_RADIUS
    source = _torch_light_source(
        column,
        row,
        barrier_key,
        tile_size,
    )
    light_left = source[0] - radius
    light_top = source[1] - radius
    projection_distance = radius * 3

    light = _get_torch_light_surface(level).copy()

    for barrier in barrier_key:
        segment = _barrier_segment(
            barrier,
            tile_size,
        )

        if segment is None:
            continue

        start, end = segment

        if (
            _distance_to_segment(source, start, end)
            > radius + tile_size
        ):
            continue

        projected_start = _project_away(
            source,
            start,
            projection_distance,
        )
        projected_end = _project_away(
            source,
            end,
            projection_distance,
        )

        polygon = (
            (
                round(start[0] - light_left),
                round(start[1] - light_top),
            ),
            (
                round(end[0] - light_left),
                round(end[1] - light_top),
            ),
            (
                round(projected_end[0] - light_left),
                round(projected_end[1] - light_top),
            ),
            (
                round(projected_start[0] - light_left),
                round(projected_start[1] - light_top),
            ),
        )

        pygame.draw.polygon(
            light,
            (0, 0, 0),
            polygon,
        )

    reduced_size = (
        max(1, light.get_width() // 2),
        max(1, light.get_height() // 2),
    )
    light = pygame.transform.smoothscale(
        light,
        reduced_size,
    )
    light = pygame.transform.smoothscale(
        light,
        (
            radius * 2,
            radius * 2,
        ),
    )

    if len(_OCCLUDED_TORCH_LIGHT_SURFACES) >= 256:
        _OCCLUDED_TORCH_LIGHT_SURFACES.clear()

    _OCCLUDED_TORCH_LIGHT_SURFACES[key] = light
    return light


def _torch_light_level(current_time, torch_index):
    time_seconds = current_time / 1000
    phase = torch_index * 1.73

    slow_wave = math.sin(
        time_seconds * 1.15 + phase
    )
    secondary_wave = math.sin(
        time_seconds * 2.05 + phase * 0.71
    )

    flicker = (
        slow_wave * 0.68
        + secondary_wave * 0.32
        + 1
    ) / 2

    return max(
        0,
        min(
            _TORCH_LIGHT_LEVELS - 1,
            round(flicker * (_TORCH_LIGHT_LEVELS - 1)),
        ),
    )


def draw_act_three_lighting(
    surface,
    torches,
    barriers,
    camera_x,
    camera_y,
    current_time,
    tile_size,
):
    surface.blit(
        _get_ambient_surface(surface.get_size()),
        (0, 0),
    )

    light_map = _get_light_map_surface(
        surface.get_size()
    )
    barrier_key = tuple(sorted(barriers))
    for torch_index, (column, row) in enumerate(torches):
        light_level = _torch_light_level(
            current_time,
            torch_index,
        )

        wall_glow = _get_torch_wall_glow_surface(
            light_level
        )
        marker_center_x = (
                column * tile_size
                - camera_x
                + tile_size // 2
        )
        marker_center_y = (
                row * tile_size
                - camera_y
                + tile_size // 2
        )
        wall_glow_left = (
                marker_center_x
                - wall_glow.get_width() // 2
        )
        wall_glow_top = (
                marker_center_y
                - wall_glow.get_height() // 2
        )

        light_map.blit(
            wall_glow,
            (
                wall_glow_left,
                wall_glow_top,
            ),
            special_flags=pygame.BLEND_RGB_MAX,
        )

        light = _get_occluded_torch_light_surface(
            column,
            row,
            light_level,
            barrier_key,
            tile_size,
        )

        light_source_x, light_source_y = (
            _torch_light_source(
                column,
                row,
                barrier_key,
                tile_size,
            )
        )
        center_x = round(light_source_x - camera_x)
        center_y = round(light_source_y - camera_y)
        left = center_x - light.get_width() // 2
        top = center_y - light.get_height() // 2

        if (
                left >= surface.get_width()
                or top >= surface.get_height()
                or left + light.get_width() <= 0
                or top + light.get_height() <= 0
        ):
            continue

        light_map.blit(
            light,
            (left, top),
            special_flags=pygame.BLEND_RGB_MAX,
        )

    surface.blit(
        light_map,
        (0, 0),
        special_flags=pygame.BLEND_RGB_ADD,
    )


def _get_actor_shadow_surface(tile_size):
    shadow = _ACTOR_SHADOW_SURFACES.get(tile_size)

    if shadow is not None:
        return shadow

    width = round(tile_size * 0.66)
    height = max(12, round(tile_size * 0.22))

    shadow = pygame.Surface(
        (width, height),
        pygame.SRCALPHA,
    )

    pygame.draw.ellipse(
        shadow,
        (0, 0, 0, 52),
        (0, 0, width, height),
    )
    pygame.draw.ellipse(
        shadow,
        (0, 0, 0, 105),
        (
            round(width * 0.12),
            round(height * 0.2),
            round(width * 0.76),
            round(height * 0.6),
        ),
    )
    pygame.draw.ellipse(
        shadow,
        (0, 0, 0, 145),
        (
            round(width * 0.28),
            round(height * 0.34),
            round(width * 0.44),
            round(height * 0.32),
        ),
    )

    _ACTOR_SHADOW_SURFACES[tile_size] = shadow
    return shadow


def _get_directional_actor_shadow(
    sprite,
    tile_size,
    direction_index,
    shadow_key,
):
    key = (
        shadow_key,
        tile_size,
        direction_index,
    )
    cached = _DIRECTIONAL_ACTOR_SHADOWS.get(key)

    if cached is not None:
        return cached

    bounds = sprite.get_bounding_rect(min_alpha=24)

    if bounds.width <= 0 or bounds.height <= 0:
        bounds = sprite.get_rect()

    silhouette = pygame.Surface(
        bounds.size,
        pygame.SRCALPHA,
    )
    silhouette.blit(
        sprite,
        (0, 0),
        bounds,
    )
    silhouette.fill(
        (0, 0, 0, 112),
        special_flags=pygame.BLEND_RGBA_MULT,
    )

    projected_width = max(
        round(tile_size * 0.52),
        round(bounds.width * 1.08),
    )
    projected_width = min(
        projected_width,
        round(tile_size * 1.35),
    )
    projected_length = max(
        round(tile_size * 0.68),
        round(bounds.height * 0.82),
    )
    projected_length = min(
        projected_length,
        round(tile_size * 1.15),
    )

    silhouette = pygame.transform.smoothscale(
        silhouette,
        (
            projected_width,
            projected_length,
        ),
    )

    reduced_size = (
        max(1, projected_width // 2),
        max(1, projected_length // 2),
    )
    silhouette = pygame.transform.smoothscale(
        silhouette,
        reduced_size,
    )
    silhouette = pygame.transform.smoothscale(
        silhouette,
        (
            projected_width,
            projected_length,
        ),
    )

    angle = (
        math.tau
        * direction_index
        / _DIRECTIONAL_SHADOW_COUNT
    )
    rotation = -math.degrees(
        angle + math.pi / 2
    )
    silhouette = pygame.transform.rotate(
        silhouette,
        rotation,
    )

    result = (
        silhouette,
        projected_length,
    )
    _DIRECTIONAL_ACTOR_SHADOWS[key] = result
    return result


def _nearest_torch_direction(
    position,
    tile_size,
    torches,
    camera_x,
    camera_y,
):
    feet = (
        position[0] + tile_size / 2,
        position[1] + tile_size * 0.84,
    )
    nearest_distance = float("inf")
    nearest_torch = None

    for column, row in torches:
        torch_position = (
            column * tile_size
            - camera_x
            + tile_size / 2,
            row * tile_size
            - camera_y
            + tile_size / 2,
        )
        distance = math.hypot(
            feet[0] - torch_position[0],
            feet[1] - torch_position[1],
        )

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_torch = torch_position

    if (
        nearest_torch is None
        or nearest_distance > tile_size * 5
        or nearest_distance < 1
    ):
        return None

    angle = math.atan2(
        feet[1] - nearest_torch[1],
        feet[0] - nearest_torch[0],
    )
    direction_index = round(
        angle
        / math.tau
        * _DIRECTIONAL_SHADOW_COUNT
    ) % _DIRECTIONAL_SHADOW_COUNT
    quantized_angle = (
        math.tau
        * direction_index
        / _DIRECTIONAL_SHADOW_COUNT
    )

    return (
        feet,
        direction_index,
        quantized_angle,
        nearest_distance,
    )


def draw_actor_shadow(
    surface,
    sprite,
    position,
    tile_size,
    torches,
    camera_x,
    camera_y,
    shadow_key,
):
    torch_direction = _nearest_torch_direction(
        position,
        tile_size,
        torches,
        camera_x,
        camera_y,
    )

    if torch_direction is not None:
        (
            feet,
            direction_index,
            angle,
            distance,
        ) = torch_direction

        directional, projected_length = (
            _get_directional_actor_shadow(
                sprite,
                tile_size,
                direction_index,
                shadow_key,
            )
        )
        directional = directional.copy()
        strength = max(
            0.35,
            min(
                1,
                1 - distance / (tile_size * 6),
            ),
        )
        directional.set_alpha(
            round(255 * strength)
        )

        shadow_center = (
            feet[0]
            + math.cos(angle) * projected_length * 0.42,
            feet[1]
            + math.sin(angle) * projected_length * 0.42,
        )
        shadow_rectangle = directional.get_rect(
            center=(
                round(shadow_center[0]),
                round(shadow_center[1]),
            )
        )

        surface.blit(
            directional,
            shadow_rectangle,
        )

    contact_shadow = _get_actor_shadow_surface(
        tile_size
    )

    surface.blit(
        contact_shadow,
        (
            round(
                position[0]
                + (
                    tile_size
                    - contact_shadow.get_width()
                )
                / 2
            ),
            round(position[1] + tile_size * 0.73),
        ),
    )


def draw_torch_flame(
    surface,
    assets,
    position,
    current_time,
    torch_index,
):
    timeline = (
        current_time + torch_index * 193
    ) / _TORCH_FLAME_FRAME_DURATION_MS

    current_step = int(timeline)
    blend = timeline - current_step
    blend = blend * blend * (3 - 2 * blend)

    sequence_length = len(_TORCH_FLAME_SEQUENCE)
    current_sequence_index = current_step % sequence_length
    next_sequence_index = (
                                  current_sequence_index + 1
                          ) % sequence_length

    current_frame_index = _TORCH_FLAME_SEQUENCE[
        current_sequence_index
    ]
    next_frame_index = _TORCH_FLAME_SEQUENCE[
        next_sequence_index
    ]

    current_frame = assets[
        f"torch_flame_{current_frame_index}"
    ].copy()
    next_frame = assets[
        f"torch_flame_{next_frame_index}"
    ].copy()

    current_frame.set_alpha(
        round(255 * (1 - blend) ** 0.5)
    )
    next_frame.set_alpha(
        round(255 * blend**0.5)
    )

    surface.blit(current_frame, position)
    surface.blit(next_frame, position)
