import math
import random

import pygame

from acts.act_three.presentation.view import _view_position


BARRAGE_SHOT_MS = 1140
_SHOT_STARTS = (80, 360, 640)


def draw_barrage_zone_cells(
    surface,
    positions,
    camera_x,
    camera_y,
    current_time,
    tile_size,
    preview=False,
):
    for index, (column, row) in enumerate(positions):
        marker = pygame.Surface(
            (tile_size, tile_size),
            pygame.SRCALPHA,
        )
        cx = tile_size // 2
        cy = tile_size // 2 + 10
        pulse = (
            math.sin(current_time * 0.005 + index * 1.2) + 1
        ) / 2
        strength = 1.0 if preview else 0.85

        for radius, color in (
            (26, (7, 38, 20, round(110 * strength))),
            (22, (21, 88, 43, round((115 + pulse * 35) * strength))),
            (17, (40, 126, 57, round((100 + pulse * 55) * strength))),
        ):
            points = []
            for point_index in range(14):
                angle = point_index * math.tau / 14
                uneven = (
                    0.84
                    + 0.12 * math.sin(point_index * 2.7 + index)
                    + 0.06 * math.sin(
                        current_time * 0.003 + point_index
                    )
                )
                points.append(
                    (
                        round(cx + math.cos(angle) * radius * uneven),
                        round(
                            cy
                            + math.sin(angle)
                            * radius
                            * 0.48
                            * uneven
                        ),
                    )
                )
            pygame.draw.polygon(marker, color, points)

        pygame.draw.ellipse(
            marker,
            (93, 181, 95, round((65 + pulse * 45) * strength)),
            (cx - 15, cy - 6, 30, 12),
        )

        for tip_index, angle in enumerate(
            (0.35, 2.65, 3.65, 5.7)
        ):
            outward = (
                math.cos(angle),
                math.sin(angle) * 0.52,
            )
            across = (
                -outward[1],
                outward[0],
            )
            base = (
                cx + outward[0] * 25,
                cy + outward[1] * 25,
            )
            point = (
                cx + outward[0] * 13,
                cy + outward[1] * 13,
            )
            pygame.draw.ellipse(
                marker,
                (1, 8, 5, 105),
                (
                    round(base[0] - 6),
                    round(base[1] + 2),
                    12,
                    5,
                ),
            )
            pygame.draw.polygon(
                marker,
                (2, 9, 7, 245),
                (
                    (round(point[0]), round(point[1])),
                    (
                        round(base[0] + across[0] * 5),
                        round(base[1] + across[1] * 5),
                    ),
                    (
                        round(base[0] + outward[0] * 4),
                        round(base[1] + outward[1] * 4),
                    ),
                    (
                        round(base[0] - across[0] * 5),
                        round(base[1] - across[1] * 5),
                    ),
                ),
            )
            pygame.draw.circle(
                marker,
                (96, 150, 91, round(110 * strength)),
                (
                    round(base[0] - outward[0] * 3),
                    round(base[1] - outward[1] * 3),
                ),
                1 + tip_index % 2,
            )

        surface.blit(
            marker,
            _view_position(
                column,
                row,
                camera_x,
                camera_y,
            ),
        )


def _curve_point(start, control, end, progress):
    remaining = 1 - progress
    return (
        round(
            remaining * remaining * start[0]
            + 2 * remaining * progress * control[0]
            + progress * progress * end[0]
        ),
        round(
            remaining * remaining * start[1]
            + 2 * remaining * progress * control[1]
            + progress * progress * end[1]
        ),
    )


def _phantom_sides(direction):
    if direction[0]:
        sides = (
            ((0, -1), "down"),
            ((0, 1), "up"),
        )
        return sides if direction[0] > 0 else sides[::-1]

    sides = (
        ((-1, 0), "right"),
        ((1, 0), "left"),
    )
    return sides if direction[1] > 0 else sides[::-1]


def draw_barrage_shot(
    surface,
    assets,
    target_position,
    elapsed,
    tile_size,
    direction,
    seed,
):
    effect = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    target = (
        target_position[0] + tile_size // 2,
        target_position[1] + tile_size // 2,
    )
    sides = _phantom_sides(direction)
    rng = random.Random(seed)
    first_side = rng.randrange(2)

    for shot_index, start_time in enumerate(_SHOT_STARTS):
        side_index = (first_side + shot_index) % 2
        offset, facing = sides[side_index]
        distance = tile_size + rng.randrange(2, 18)
        sideways = rng.randrange(-17, 18)
        perpendicular = (-offset[1], offset[0])
        ghost_position = (
            target_position[0]
            + offset[0] * distance
            + perpendicular[0] * sideways,
            target_position[1]
            + offset[1] * distance
            + perpendicular[1] * sideways
            - 8,
        )
        local_time = round((elapsed - start_time) * 1.15)

        if not 0 <= local_time < 520:
            continue

        ghost_center = (
            ghost_position[0] + tile_size // 2,
            ghost_position[1] + tile_size // 2,
        )
        facing_vector = {
            "right": (1, 0),
            "left": (-1, 0),
            "up": (0, -1),
            "down": (0, 1),
        }[facing]
        bow = (
            ghost_center[0] + facing_vector[0] * 15,
            ghost_center[1] + facing_vector[1] * 13,
        )

        if local_time < 280:
            visibility = max(
                0.0,
                min(
                    1.0,
                    local_time / 24,
                    (280 - local_time) / 38,
                ),
            )
            frame = min(7, local_time * 8 // 250)
            sprite = assets[
                f"player_archer_attack_{facing}_{frame}"
            ].copy()
            shadow = sprite.copy()
            shadow.fill(
                (28, 62, 41),
                special_flags=pygame.BLEND_RGB_MULT,
            )
            shadow.set_alpha(round(125 * visibility))
            surface.blit(
                shadow,
                (
                    ghost_position[0] + offset[0] * 4,
                    ghost_position[1] + offset[1] * 4,
                ),
            )
            sprite.fill(
                (128, 169, 137),
                special_flags=pygame.BLEND_RGB_MULT,
            )
            sprite.set_alpha(round(215 * visibility))
            surface.blit(sprite, ghost_position)

            if local_time < 90:
                burst = 1 - local_time / 90
                for fragment in range(7):
                    angle = (
                        fragment * math.tau / 7
                        + shot_index * 0.37
                    )
                    radius = 12 + burst * 19
                    point = (
                        round(
                            ghost_center[0]
                            + math.cos(angle) * radius
                        ),
                        round(
                            ghost_center[1]
                            + math.sin(angle) * radius
                        ),
                    )
                    pygame.draw.circle(
                        effect,
                        (
                            26,
                            89,
                            49,
                            round(170 * burst * visibility),
                        ),
                        point,
                        max(1, round(4 * burst)),
                    )

            if 90 <= local_time < 155:
                charge = math.sin(
                    (local_time - 90) * math.pi / 65
                )
                pygame.draw.circle(
                    effect,
                    (
                        105,
                        208,
                        125,
                        round(190 * charge * visibility),
                    ),
                    bow,
                    round(3 + charge * 6),
                )

        flight = local_time - 128
        if 0 <= flight < 200:
            progress = flight / 200
            vx = target[0] - bow[0]
            vy = target[1] - bow[1]
            length = max(1.0, math.hypot(vx, vy))
            bend = 0
            control = (
                round(
                    (bow[0] + target[0]) / 2
                    - vy / length * bend
                ),
                round(
                    (bow[1] + target[1]) / 2
                    + vx / length * bend
                ),
            )
            head = _curve_point(
                bow,
                control,
                target,
                progress,
            )
            dx = vx / length
            dy = vy / length
            px = -dy
            py = dx
            tail = (
                round(head[0] - dx * 17),
                round(head[1] - dy * 17),
            )
            tip = (
                round(head[0] + dx * 13),
                round(head[1] + dy * 13),
            )
            pygame.draw.line(
                effect,
                (5, 27, 16, 245),
                tail,
                tip,
                3,
            )
            pygame.draw.line(
                effect,
                (129, 211, 139, 230),
                tail,
                head,
                1,
            )
            pygame.draw.polygon(
                effect,
                (188, 232, 180, 245),
                (
                    tip,
                    (
                        round(head[0] - dx * 5 + px * 4),
                        round(head[1] - dy * 5 + py * 4),
                    ),
                    (
                        round(head[0] - dx * 2),
                        round(head[1] - dy * 2),
                    ),
                    (
                        round(head[0] - dx * 5 - px * 4),
                        round(head[1] - dy * 5 - py * 4),
                    ),
                ),
            )
            for fragment in range(2):
                point = (
                    round(head[0] - dx * (25 + fragment * 11)),
                    round(head[1] - dy * (25 + fragment * 11)),
                )
                pygame.draw.circle(
                    effect,
                    (73, 150, 86, 125 - fragment * 40),
                    point,
                    2 - fragment,
                )
        impact_age = local_time - 328
        if 0 <= impact_age < 190:
            progress = impact_age / 190
            strength = 1 - progress
            pygame.draw.circle(
                effect,
                (5, 47, 24, round(160 * strength)),
                target,
                round(8 + progress * 22),
            )
            pygame.draw.circle(
                effect,
                (184, 232, 169, round(230 * strength)),
                target,
                max(2, round(7 * strength)),
            )
            for fragment in range(10):
                angle = (
                    fragment * math.tau / 10
                    + shot_index * 0.43
                )
                distance = (
                    7 + progress * (17 + fragment % 3 * 5)
                )
                point = (
                    round(
                        target[0]
                        + math.cos(angle) * distance
                    ),
                    round(
                        target[1]
                        + math.sin(angle) * distance * 0.7
                    ),
                )
                pygame.draw.circle(
                    effect,
                    (
                        77,
                        157 + fragment % 3 * 18,
                        91,
                        round(205 * strength),
                    ),
                    point,
                    max(1, round(4 * strength)),
                )

    surface.blit(effect, (0, 0))
