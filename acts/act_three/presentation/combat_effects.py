import math

import pygame


from presentation.layout import ACT_THREE_TILE_SIZE


_TORCH_LIGHT_SURFACE = None
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

def _draw_attack_impact_flash(
    surface,
    position,
    current_time,
    started_at,
    flash_color,
):
    elapsed = current_time - started_at
    if not 0 <= elapsed < _ATTACK_FRAME_DURATION_MS:
        return

    progress = elapsed / _ATTACK_FRAME_DURATION_MS
    visibility = math.sin(math.pi * progress)
    center = (
        position[0] + ACT_THREE_TILE_SIZE // 2,
        position[1] + ACT_THREE_TILE_SIZE // 2,
    )
    radius = round(7 + visibility * 9)
    alpha = round(190 * visibility)
    flash_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    local_center = (
        center[0] - position[0],
        center[1] - position[1],
    )
    pygame.draw.circle(
        flash_surface,
        (*flash_color, alpha),
        local_center,
        radius,
        width=2,
    )
    pygame.draw.line(
        flash_surface,
        (235, 255, 235, alpha),
        (local_center[0] - radius, local_center[1] + radius // 2),
        (local_center[0] + radius, local_center[1] - radius // 2),
        width=2,
    )
    surface.blit(flash_surface, position)


def _draw_archer_projectile(
    surface,
    arrow_sprite,
    origin,
    destination,
    progress,
    empowered=False,
    current_time=0,
):
    direction = math.atan2(
        destination[1] - origin[1],
        destination[0] - origin[0],
    )
    rotation = -math.degrees(direction) - 45
    arrow_position = (
        round(origin[0] + (destination[0] - origin[0]) * progress),
        round(origin[1] + (destination[1] - origin[1]) * progress),
    )

    for trail_progress, trail_alpha in (
        (progress - 0.18, 38),
        (progress - 0.10, 78),
    ):
        if trail_progress <= 0:
            continue
        trail_position = (
            round(origin[0] + (destination[0] - origin[0]) * trail_progress),
            round(origin[1] + (destination[1] - origin[1]) * trail_progress),
        )
        trail = pygame.transform.rotate(arrow_sprite, rotation).copy()
        trail.set_alpha(trail_alpha)
        surface.blit(trail, trail.get_rect(center=trail_position))

    if empowered:
        effect_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        travel_dx = destination[0] - origin[0]
        travel_dy = destination[1] - origin[1]
        travel_length = max(1, math.hypot(travel_dx, travel_dy))
        direction_x = travel_dx / travel_length
        direction_y = travel_dy / travel_length
        normal_x = -travel_dy / travel_length
        normal_y = travel_dx / travel_length

        trail_start_progress = max(0, progress - 0.34)
        trail_start = (
            round(origin[0] + travel_dx * trail_start_progress),
            round(origin[1] + travel_dy * trail_start_progress),
        )
        for width, color in (
            (12, (20, 135, 85, 24)),
            (7, (40, 220, 125, 48)),
            (3, (125, 255, 180, 145)),
            (1, (235, 255, 240, 225)),
        ):
            pygame.draw.line(
                effect_surface,
                color,
                trail_start,
                arrow_position,
                width=width,
            )

        for wave_index, (wave_color, wave_alpha) in enumerate(
            (
                ((75, 235, 135), 115),
                ((145, 255, 190), 70),
            )
        ):
            points = []
            for point_index in range(15):
                wave_progress = max(
                    0,
                    progress - 0.31 + point_index * 0.021,
                )
                wave_x = origin[0] + travel_dx * wave_progress
                wave_y = origin[1] + travel_dy * wave_progress
                wave = math.sin(
                    current_time * 0.014
                    + point_index * 0.82
                    + wave_index * math.pi
                ) * (3.5 + wave_index * 2)
                points.append(
                    (
                        round(wave_x + normal_x * wave),
                        round(wave_y + normal_y * wave),
                    )
                )
            if len(points) > 1:
                pygame.draw.lines(
                    effect_surface,
                    (*wave_color, wave_alpha),
                    False,
                    points,
                    width=1 if wave_index else 2,
                )

        for particle_index in range(9):
            particle_progress = progress - 0.035 - particle_index * 0.032
            if particle_progress <= 0:
                continue
            particle_wave = math.sin(
                current_time * 0.021 + particle_index * 2.15
            ) * (2 + particle_index * 0.45)
            particle_position = (
                round(
                    origin[0]
                    + travel_dx * particle_progress
                    + normal_x * particle_wave
                ),
                round(
                    origin[1]
                    + travel_dy * particle_progress
                    + normal_y * particle_wave
                ),
            )
            particle_alpha = max(30, 185 - particle_index * 17)
            particle_radius = 2 if particle_index < 3 else 1
            pygame.draw.circle(
                effect_surface,
                (155, 255, 195, particle_alpha),
                particle_position,
                particle_radius,
            )

        pulse = (math.sin(current_time * 0.025) + 1) / 2
        for radius, alpha in (
            (13, round(18 + pulse * 10)),
            (8, round(30 + pulse * 14)),
            (4, round(65 + pulse * 25)),
        ):
            pygame.draw.circle(
                effect_surface,
                (75, 245, 145, alpha),
                arrow_position,
                radius,
            )

        ring_angle = current_time * 0.012
        for angle_offset in (-0.9, 0.9):
            ring_length = 9
            ring_center = (
                round(
                    arrow_position[0]
                    - direction_x * 4
                    + normal_x * math.sin(ring_angle + angle_offset) * 5
                ),
                round(
                    arrow_position[1]
                    - direction_y * 4
                    + normal_y * math.sin(ring_angle + angle_offset) * 5
                ),
            )
            ring_end = (
                round(ring_center[0] + normal_x * ring_length),
                round(ring_center[1] + normal_y * ring_length),
            )
            pygame.draw.line(
                effect_surface,
                (205, 255, 220, 155),
                ring_center,
                ring_end,
                width=1,
            )

        if progress > 0.82:
            impact_progress = min(1, (progress - 0.82) / 0.18)
            impact_visibility = math.sin(math.pi * impact_progress)
            impact_radius = round(5 + impact_progress * 12)
            pygame.draw.circle(
                effect_surface,
                (
                    95,
                    255,
                    160,
                    round(150 * impact_visibility),
                ),
                destination,
                impact_radius,
                width=2,
            )
            for ray_index in range(6):
                ray_angle = ray_index * math.tau / 6 + direction
                ray_start = (
                    round(
                        destination[0]
                        + math.cos(ray_angle) * 4
                    ),
                    round(
                        destination[1]
                        + math.sin(ray_angle) * 4
                    ),
                )
                ray_end = (
                    round(
                        destination[0]
                        + math.cos(ray_angle) * impact_radius
                    ),
                    round(
                        destination[1]
                        + math.sin(ray_angle) * impact_radius
                    ),
                )
                pygame.draw.line(
                    effect_surface,
                    (
                        220,
                        255,
                        225,
                        round(175 * impact_visibility),
                    ),
                    ray_start,
                    ray_end,
                    width=1,
                )

        surface.blit(effect_surface, (0, 0))

    arrow = pygame.transform.rotate(arrow_sprite, rotation)
    surface.blit(arrow, arrow.get_rect(center=arrow_position))


def _draw_warlock_orb(
    surface,
    origin,
    destination,
    progress,
    current_time,
):
    orb_position = (
        round(
            origin[0]
            + (destination[0] - origin[0]) * progress
        ),
        round(
            origin[1]
            + (destination[1] - origin[1]) * progress
        ),
    )
    effect_surface = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    trail_start_progress = max(0, progress - 0.34)
    trail_start = (
        round(
            origin[0]
            + (destination[0] - origin[0])
            * trail_start_progress
        ),
        round(
            origin[1]
            + (destination[1] - origin[1])
            * trail_start_progress
        ),
    )
    for width, color in (
        (10, (72, 18, 112, 32)),
        (6, (126, 35, 188, 68)),
        (2, (211, 105, 255, 175)),
    ):
        pygame.draw.line(
            effect_surface,
            color,
            trail_start,
            orb_position,
            width=width,
        )

    pulse = (math.sin(current_time * 0.028) + 1) / 2
    for radius, color in (
        (10, (86, 20, 142, round(38 + pulse * 20))),
        (7, (144, 42, 222, round(95 + pulse * 35))),
        (4, (210, 105, 255, 235)),
        (2, (246, 220, 255, 255)),
    ):
        pygame.draw.circle(
            effect_surface,
            color,
            orb_position,
            radius,
        )

    for particle_index in range(5):
        angle = (
            current_time * 0.012
            + particle_index * math.tau / 5
        )
        particle_position = (
            round(orb_position[0] + math.cos(angle) * 9),
            round(orb_position[1] + math.sin(angle) * 7),
        )
        pygame.draw.circle(
            effect_surface,
            (225, 125, 255, 170),
            particle_position,
            1,
        )

    if progress > 0.78:
        impact_progress = min(
            1,
            (progress - 0.78) / 0.22,
        )
        impact_visibility = math.sin(
            math.pi * impact_progress
        )
        pygame.draw.circle(
            effect_surface,
            (
                205,
                75,
                255,
                round(190 * impact_visibility),
            ),
            destination,
            round(7 + impact_progress * 13),
            width=2,
        )

    surface.blit(effect_surface, (0, 0))


def _draw_assassin_slash_particles(
    surface,
    position,
    progress,
    identity_seed,
    strike_index,
):
    particle_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    center = ACT_THREE_TILE_SIZE // 2
    visibility = math.sin(math.pi * progress)
    alpha = round(245 * visibility)
    slash_patterns = (
        ((-1.10, 25, -5), (-0.28, 19, 4), (0.62, 22, 0)),
        ((-0.55, 22, -7), (0.38, 28, 4), (1.18, 18, 1)),
        ((-1.38, 18, 3), (-0.72, 27, -4), (0.20, 24, 5)),
        ((-0.92, 29, 5), (0.02, 18, -5), (0.82, 26, 2)),
        ((-0.35, 20, -4), (0.56, 25, 5), (1.36, 19, -1)),
    )
    slash_pattern = slash_patterns[strike_index % len(slash_patterns)]
    for slash_index, (base_angle, length, offset) in enumerate(
        slash_pattern
    ):
        angle = (
            base_angle
            + math.sin(progress * math.tau + slash_index) * 0.16
            + (identity_seed % 11) * 0.01
        )
        bend = 5 + slash_index * 2
        start = (
            round(center + math.cos(angle) * offset - math.cos(angle) * length / 2),
            round(center + math.sin(angle) * offset - math.sin(angle) * length / 2),
        )
        end = (
            round(center + math.cos(angle) * offset + math.cos(angle) * length / 2),
            round(center + math.sin(angle) * offset + math.sin(angle) * length / 2),
        )
        middle = (
            round((start[0] + end[0]) / 2 - math.sin(angle) * bend),
            round((start[1] + end[1]) / 2 + math.cos(angle) * bend),
        )
        pygame.draw.line(
            particle_surface,
            (65, 145, 255, alpha // 3),
            start,
            middle,
            width=8,
        )
        pygame.draw.line(
            particle_surface,
            (65, 145, 255, alpha // 3),
            middle,
            end,
            width=8,
        )
        pygame.draw.line(
            particle_surface,
            (185, 230, 255, alpha),
            start,
            middle,
            width=2,
        )
        pygame.draw.line(
            particle_surface,
            (220, 245, 255, alpha),
            middle,
            end,
            width=2,
        )
        for shard_index, shard_side in enumerate((-1, 1)):
            shard_origin = (
                end[0] + round(math.cos(angle + math.pi / 2) * shard_side * 4),
                end[1] + round(math.sin(angle + math.pi / 2) * shard_side * 4),
            )
            shard_end = (
                shard_origin[0] + round(math.cos(angle + shard_side) * (5 + shard_index * 2)),
                shard_origin[1] + round(math.sin(angle + shard_side) * (5 + shard_index * 2)),
            )
            pygame.draw.line(
                particle_surface,
                (125, 205, 255, alpha),
                shard_origin,
                shard_end,
                width=2,
            )
    surface.blit(particle_surface, position)
