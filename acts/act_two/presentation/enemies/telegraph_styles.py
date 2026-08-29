from dataclasses import dataclass
import math

import pygame

from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


@dataclass(frozen=True)
class TelegraphStyle:
    color: tuple[int, int, int]
    shadow: tuple[int, int, int]
    pattern: str


TELEGRAPH_STYLES = {
    "goblin": TelegraphStyle(
        color=(239, 93, 55),
        shadow=(67, 16, 12),
        pattern="jagged",
    ),
    "mimic": TelegraphStyle(
        color=(229, 151, 58),
        shadow=(65, 35, 9),
        pattern="teeth",
    ),
    "brute": TelegraphStyle(
        color=(225, 32, 45),
        shadow=(69, 3, 10),
        pattern="heavy",
    ),
    "archer": TelegraphStyle(
        color=(112, 224, 83),
        shadow=(19, 61, 21),
        pattern="chevrons",
    ),
    "sentinel": TelegraphStyle(
        color=(76, 156, 241),
        shadow=(13, 34, 68),
        pattern="shield",
    ),
    "priest": TelegraphStyle(
        color=(245, 196, 76),
        shadow=(69, 44, 7),
        pattern="runes",
    ),
    "priest_ghost": TelegraphStyle(
        color=(103, 226, 220),
        shadow=(11, 55, 62),
        pattern="spectral",
    ),
    "warden": TelegraphStyle(
        color=(192, 92, 218),
        shadow=(49, 13, 64),
        pattern="warden",
    ),
    "oracle": TelegraphStyle(
        color=(105, 190, 255),
        shadow=(14, 40, 72),
        pattern="oracle",
    ),
}

DEFAULT_TELEGRAPH_STYLE = TelegraphStyle(
    color=(238, 78, 70),
    shadow=(59, 8, 12),
    pattern="corners",
)


def _draw_corner_frame(
    surface,
    rectangle,
    color,
    width,
    arm_length,
):
    left = rectangle.left
    top = rectangle.top
    right = rectangle.right - 1
    bottom = rectangle.bottom - 1

    segments = (
        ((left, top + arm_length), (left, top), (left + arm_length, top)),
        ((right - arm_length, top), (right, top), (right, top + arm_length)),
        ((left, bottom - arm_length), (left, bottom), (left + arm_length, bottom)),
        (
            (right - arm_length, bottom),
            (right, bottom),
            (right, bottom - arm_length),
        ),
    )

    for points in segments:
        pygame.draw.lines(
            surface,
            color,
            False,
            points,
            width,
        )


def draw_attack_tile_base(
    screen,
    column,
    row,
    threat_count,
    current_time,
):
    left = MAP_OFFSET_X + column * TILE_SIZE
    top = MAP_OFFSET_Y + row * TILE_SIZE

    phase = (
        current_time / 175
        + column * 0.47
        + row * 0.31
    )
    pulse = (math.sin(phase) + 1) / 2

    marker = pygame.Surface(
        (TILE_SIZE, TILE_SIZE),
        pygame.SRCALPHA,
    )

    threat_strength = min(threat_count, 4)

    pygame.draw.rect(
        marker,
        (
            53,
            5,
            11,
            round(
                20
                + threat_strength * 8
                + pulse * 9
            ),
        ),
        (1, 1, TILE_SIZE - 2, TILE_SIZE - 2),
        border_radius=3,
    )

    pygame.draw.rect(
        marker,
        (
            132,
            23,
            34,
            round(38 + threat_strength * 9),
        ),
        (2, 2, TILE_SIZE - 4, TILE_SIZE - 4),
        width=1,
        border_radius=3,
    )

    sweep_position = round(
        (
            current_time / 22
            + column * 7
            + row * 5
        )
        % (TILE_SIZE * 2)
    ) - TILE_SIZE

    pygame.draw.polygon(
        marker,
        (
            221,
            46,
            54,
            round(10 + pulse * 13),
        ),
        (
            (sweep_position - 5, TILE_SIZE),
            (sweep_position, TILE_SIZE),
            (sweep_position + TILE_SIZE, 0),
            (sweep_position + TILE_SIZE - 5, 0),
        ),
    )

    screen.blit(marker, (left, top))


def draw_attack_lane(
    screen,
    column,
    row,
    current_time,
    lane,
    enemy_type,
    attack_mode,
    is_player_cell,
):
    style = TELEGRAPH_STYLES.get(
        enemy_type,
        DEFAULT_TELEGRAPH_STYLE,
    )

    left = MAP_OFFSET_X + column * TILE_SIZE
    top = MAP_OFFSET_Y + row * TILE_SIZE

    marker = pygame.Surface(
        (TILE_SIZE, TILE_SIZE),
        pygame.SRCALPHA,
    )

    phase = (
        current_time / 125
        + column * 0.53
        + row * 0.37
    )
    pulse = (math.sin(phase) + 1) / 2

    inset = min(
        2 + lane * 3,
        TILE_SIZE // 2 - 4,
    )
    rectangle = pygame.Rect(
        inset,
        inset,
        TILE_SIZE - inset * 2,
        TILE_SIZE - inset * 2,
    )

    color = (
        *style.color,
        round(205 + pulse * 50),
    )
    soft_glow = (
        *style.color,
        round(45 + pulse * 45),
    )
    medium_glow = (
        *style.color,
        round(95 + pulse * 65),
    )
    shadow = (
        *style.shadow,
        230,
    )

    arm_length = max(
        2,
        min(7, rectangle.width // 3),
    )

    if style.pattern == "heavy":
        contraction = round(pulse * 2)
        heavy_rectangle = rectangle.inflate(
            -contraction * 2,
            -contraction * 2,
        )

        _draw_corner_frame(
            marker,
            heavy_rectangle,
            soft_glow,
            7,
            arm_length,
        )
        _draw_corner_frame(
            marker,
            heavy_rectangle,
            shadow,
            5,
            arm_length,
        )
        _draw_corner_frame(
            marker,
            heavy_rectangle,
            color,
            3,
            arm_length,
        )

        center_x = TILE_SIZE // 2
        center_y = TILE_SIZE // 2
        tooth_depth = round(3 + pulse * 3)

        impact_teeth = (
            (
                (center_x - 3, heavy_rectangle.top),
                (center_x + 3, heavy_rectangle.top),
                (center_x, heavy_rectangle.top + tooth_depth),
            ),
            (
                (center_x - 3, heavy_rectangle.bottom - 1),
                (center_x + 3, heavy_rectangle.bottom - 1),
                (center_x, heavy_rectangle.bottom - 1 - tooth_depth),
            ),
            (
                (heavy_rectangle.left, center_y - 3),
                (heavy_rectangle.left, center_y + 3),
                (heavy_rectangle.left + tooth_depth, center_y),
            ),
            (
                (heavy_rectangle.right - 1, center_y - 3),
                (heavy_rectangle.right - 1, center_y + 3),
                (
                    heavy_rectangle.right - 1 - tooth_depth,
                    center_y,
                ),
            ),
        )

        for tooth in impact_teeth:
            pygame.draw.polygon(
                marker,
                medium_glow,
                tooth,
            )
            pygame.draw.polygon(
                marker,
                color,
                tooth,
                width=1,
            )

    elif style.pattern == "chevrons":
        rotation = current_time / 420

        pygame.draw.ellipse(
            marker,
            soft_glow,
            rectangle,
            width=5,
        )
        pygame.draw.ellipse(
            marker,
            shadow,
            rectangle,
            width=3,
        )

        for arc_index in range(4):
            start_angle = (
                rotation
                + arc_index * math.tau / 4
            )
            pygame.draw.arc(
                marker,
                color,
                rectangle,
                start_angle,
                start_angle + 0.62,
                2,
            )

        center_x = TILE_SIZE // 2
        center_y = TILE_SIZE // 2
        notch_length = max(2, rectangle.width // 5)

        pygame.draw.line(
            marker,
            color,
            (center_x, rectangle.top),
            (
                center_x,
                rectangle.top + notch_length,
            ),
            2,
        )
        pygame.draw.line(
            marker,
            color,
            (center_x, rectangle.bottom - 1),
            (
                center_x,
                rectangle.bottom - 1 - notch_length,
            ),
            2,
        )
        pygame.draw.line(
            marker,
            color,
            (rectangle.left, center_y),
            (
                rectangle.left + notch_length,
                center_y,
            ),
            2,
        )
        pygame.draw.line(
            marker,
            color,
            (rectangle.right - 1, center_y),
            (
                rectangle.right - 1 - notch_length,
                center_y,
            ),
            2,
        )

        pygame.draw.circle(
            marker,
            medium_glow,
            (center_x, center_y),
            round(2 + pulse * 2),
        )
        pygame.draw.circle(
            marker,
            color,
            (center_x, center_y),
            1,
        )

    elif style.pattern == "jagged":
        _draw_corner_frame(
            marker,
            rectangle,
            soft_glow,
            6,
            arm_length,
        )
        _draw_corner_frame(
            marker,
            rectangle,
            shadow,
            4,
            arm_length,
        )
        _draw_corner_frame(
            marker,
            rectangle,
            color,
            2,
            arm_length,
        )

        slash_progress = (
            current_time / 360
            + column * 0.13
            + row * 0.09
        ) % 1

        previous_clip = marker.get_clip()
        marker.set_clip(rectangle)

        slash_center = round(
            rectangle.left
            - 8
            + slash_progress
            * (rectangle.width + 16)
        )

        for slash_index in range(3):
            slash_offset = (slash_index - 1) * 5
            slash_start = (
                slash_center + slash_offset - 7,
                rectangle.bottom + 3,
            )
            slash_end = (
                slash_center + slash_offset + 5,
                rectangle.top - 3,
            )

            pygame.draw.line(
                marker,
                (
                    *style.shadow,
                    round(145 + pulse * 50),
                ),
                slash_start,
                slash_end,
                4,
            )
            pygame.draw.line(
                marker,
                (
                    *style.color,
                    round(145 + pulse * 100),
                ),
                slash_start,
                slash_end,
                1,
            )

        marker.set_clip(previous_clip)

    elif style.pattern == "teeth":
        jaw_movement = round(
            (1 - pulse) * min(3, rectangle.height // 5)
        )
        top_y = rectangle.top + jaw_movement
        bottom_y = rectangle.bottom - 1 - jaw_movement

        pygame.draw.line(
            marker,
            soft_glow,
            (rectangle.left, top_y),
            (rectangle.right - 1, top_y),
            6,
        )
        pygame.draw.line(
            marker,
            soft_glow,
            (rectangle.left, bottom_y),
            (rectangle.right - 1, bottom_y),
            6,
        )
        pygame.draw.line(
            marker,
            shadow,
            (rectangle.left, top_y),
            (rectangle.right - 1, top_y),
            4,
        )
        pygame.draw.line(
            marker,
            shadow,
            (rectangle.left, bottom_y),
            (rectangle.right - 1, bottom_y),
            4,
        )
        pygame.draw.line(
            marker,
            color,
            (rectangle.left, top_y),
            (rectangle.right - 1, top_y),
            2,
        )
        pygame.draw.line(
            marker,
            color,
            (rectangle.left, bottom_y),
            (rectangle.right - 1, bottom_y),
            2,
        )

        if rectangle.width >= 12:
            tooth_count = 3
            spacing = rectangle.width / (tooth_count + 1)

            for tooth_index in range(1, tooth_count + 1):
                tooth_x = round(
                    rectangle.left
                    + tooth_index * spacing
                )
                tooth_height = max(
                    3,
                    min(6, rectangle.height // 3),
                )

                pygame.draw.polygon(
                    marker,
                    color,
                    (
                        (tooth_x - 2, top_y),
                        (tooth_x + 2, top_y),
                        (tooth_x, top_y + tooth_height),
                    ),
                )
                pygame.draw.polygon(
                    marker,
                    color,
                    (
                        (tooth_x - 2, bottom_y),
                        (tooth_x + 2, bottom_y),
                        (
                            tooth_x,
                            bottom_y - tooth_height,
                        ),
                    ),
                )

    elif style.pattern == "shield":
        pygame.draw.rect(
            marker,
            soft_glow,
            rectangle,
            width=7,
            border_radius=2,
        )
        pygame.draw.rect(
            marker,
            shadow,
            rectangle,
            width=4,
            border_radius=2,
        )
        pygame.draw.rect(
            marker,
            color,
            rectangle,
            width=2,
            border_radius=2,
        )

        scan_progress = (
            current_time / 720
            + column * 0.07
            + row * 0.05
        ) % 1
        scan_y = round(
            rectangle.top
            + scan_progress
            * max(1, rectangle.height - 1)
        )

        pygame.draw.line(
            marker,
            (
                *style.color,
                round(45 + pulse * 55),
            ),
            (rectangle.left + 2, scan_y),
            (rectangle.right - 3, scan_y),
            2,
        )

        if attack_mode == "shield_counter":
            counter_progress = (
                current_time / 620
            ) % 1
            counter_rectangle = rectangle.inflate(
                round(-counter_progress * rectangle.width * 0.45),
                round(-counter_progress * rectangle.height * 0.45),
            )

            if (
                counter_rectangle.width > 2
                and counter_rectangle.height > 2
            ):
                pygame.draw.rect(
                    marker,
                    (
                        *style.color,
                        round(145 * (1 - counter_progress)),
                    ),
                    counter_rectangle,
                    width=2,
                    border_radius=2,
                )

            center_x = TILE_SIZE // 2
            center_y = TILE_SIZE // 2
            arrow_depth = round(3 + pulse * 3)

            arrowheads = (
                (
                    (center_x, rectangle.top),
                    (center_x - 3, rectangle.top + arrow_depth),
                    (center_x + 3, rectangle.top + arrow_depth),
                ),
                (
                    (center_x, rectangle.bottom - 1),
                    (
                        center_x - 3,
                        rectangle.bottom - 1 - arrow_depth,
                    ),
                    (
                        center_x + 3,
                        rectangle.bottom - 1 - arrow_depth,
                    ),
                ),
                (
                    (rectangle.left, center_y),
                    (rectangle.left + arrow_depth, center_y - 3),
                    (rectangle.left + arrow_depth, center_y + 3),
                ),
                (
                    (rectangle.right - 1, center_y),
                    (
                        rectangle.right - 1 - arrow_depth,
                        center_y - 3,
                    ),
                    (
                        rectangle.right - 1 - arrow_depth,
                        center_y + 3,
                    ),
                ),
            )

            for arrowhead in arrowheads:
                pygame.draw.polygon(
                    marker,
                    color,
                    arrowhead,
                )

    elif style.pattern == "runes":
        rotation = current_time / 520
        reverse_rotation = -current_time / 760

        pygame.draw.ellipse(
            marker,
            soft_glow,
            rectangle,
            width=6,
        )

        for arc_index in range(4):
            start_angle = (
                rotation
                + arc_index * math.tau / 4
            )
            pygame.draw.arc(
                marker,
                color,
                rectangle,
                start_angle,
                start_angle + 0.68,
                2,
            )

        inner_rectangle = rectangle.inflate(-6, -6)

        if (
            inner_rectangle.width > 2
            and inner_rectangle.height > 2
        ):
            for arc_index in range(3):
                start_angle = (
                    reverse_rotation
                    + arc_index * math.tau / 3
                )
                pygame.draw.arc(
                    marker,
                    medium_glow,
                    inner_rectangle,
                    start_angle,
                    start_angle + 0.75,
                    1,
                )

        center_x = TILE_SIZE // 2
        center_y = TILE_SIZE // 2
        rune_radius = max(2, rectangle.width // 2 - 2)

        rune_points = []

        for rune_index in range(4):
            angle = (
                rotation
                + rune_index * math.tau / 4
            )
            rune_points.append(
                (
                    round(
                        center_x
                        + math.cos(angle) * rune_radius
                    ),
                    round(
                        center_y
                        + math.sin(angle) * rune_radius
                    ),
                )
            )

        pygame.draw.polygon(
            marker,
            medium_glow,
            rune_points,
            width=1,
        )

        pygame.draw.circle(
            marker,
            color,
            (center_x, center_y),
            round(1 + pulse * 2),
        )

    elif style.pattern == "spectral":
        rotation = current_time / 580

        for arc_index in range(7):
            arc_phase = (
                current_time / 410
                + arc_index / 7
            ) % 1
            start_angle = (
                rotation
                + arc_index * math.tau / 7
            )

            pygame.draw.arc(
                marker,
                (
                    *style.color,
                    round(80 + 170 * (1 - arc_phase)),
                ),
                rectangle,
                start_angle,
                start_angle + 0.45,
                2,
            )

        center_x = TILE_SIZE // 2
        center_y = TILE_SIZE // 2

        for wisp_index in range(3):
            wisp_phase = (
                current_time / 850
                + wisp_index / 3
            ) % 1
            angle = (
                rotation
                + wisp_index * math.tau / 3
            )
            distance = (
                rectangle.width * 0.18
                + wisp_phase * rectangle.width * 0.22
            )
            wisp_position = (
                round(
                    center_x
                    + math.cos(angle) * distance
                ),
                round(
                    center_y
                    + math.sin(angle) * distance
                    - wisp_phase * 3
                ),
            )

            pygame.draw.circle(
                marker,
                (
                    *style.color,
                    round(190 * (1 - wisp_phase)),
                ),
                wisp_position,
                2,
            )

    elif style.pattern == "oracle":
        # Оставляем текущий внешний вид босса без изменений.
        center_x = TILE_SIZE // 2
        center_y = TILE_SIZE // 2

        diamond = (
            (center_x, rectangle.top),
            (rectangle.right - 1, center_y),
            (center_x, rectangle.bottom - 1),
            (rectangle.left, center_y),
        )

        pygame.draw.polygon(
            marker,
            shadow,
            diamond,
            width=4,
        )
        pygame.draw.polygon(
            marker,
            color,
            diamond,
            width=2,
        )
        pygame.draw.line(
            marker,
            color,
            (rectangle.left + 2, center_y),
            (rectangle.right - 3, center_y),
            1,
        )

    else:
        _draw_corner_frame(
            marker,
            rectangle,
            soft_glow,
            6,
            arm_length,
        )
        _draw_corner_frame(
            marker,
            rectangle,
            shadow,
            4,
            arm_length,
        )
        _draw_corner_frame(
            marker,
            rectangle,
            color,
            2,
            arm_length,
        )

    if is_player_cell:
        marker_center_x = min(
            TILE_SIZE - 5,
            5 + lane * 5,
        )
        marker_center_y = 4

        pygame.draw.polygon(
            marker,
            shadow,
            (
                (marker_center_x, marker_center_y - 3),
                (marker_center_x + 3, marker_center_y),
                (marker_center_x, marker_center_y + 3),
                (marker_center_x - 3, marker_center_y),
            ),
        )
        pygame.draw.polygon(
            marker,
            color,
            (
                (marker_center_x, marker_center_y - 2),
                (marker_center_x + 2, marker_center_y),
                (marker_center_x, marker_center_y + 2),
                (marker_center_x - 2, marker_center_y),
            ),
        )

    screen.blit(marker, (left, top))


__all__ = [
    "draw_attack_lane",
    "draw_attack_tile_base",
]
