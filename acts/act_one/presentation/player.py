import math

import pygame

from settings import TILE_SIZE


ACT_ONE_PLAYER_MOVE_MS = 170
ACT_ONE_WAIT_EFFECT_DURATION_MS = 900


def act_one_player_movement_offset(
    column,
    row,
    movement_origin,
    current_time,
    movement_started_at,
):
    elapsed = current_time - movement_started_at

    if (
        movement_origin is None
        or movement_started_at <= 0
        or not 0 <= elapsed < ACT_ONE_PLAYER_MOVE_MS
    ):
        return 0, 0

    progress = elapsed / ACT_ONE_PLAYER_MOVE_MS
    eased_progress = 1 - (1 - progress) ** 3
    remaining = 1 - eased_progress
    offset_x = round(
        (movement_origin[0] - column)
        * TILE_SIZE
        * remaining
    )
    offset_y = round(
        (movement_origin[1] - row)
        * TILE_SIZE
        * remaining
    )
    step_lift = round(
        math.sin(math.pi * progress) * 2
    )

    return offset_x, offset_y - step_lift


def draw_act_one_wait_indicator(
        screen,
        center_x,
        center_y,
        current_time,
        started_at,
):
    elapsed = current_time - started_at

    if (
            elapsed < 0
            or elapsed >= ACT_ONE_WAIT_EFFECT_DURATION_MS
    ):
        return

    fade_in = min(
        1.0,
        elapsed / 100,
    )
    fade_out = min(
        1.0,
        (
                ACT_ONE_WAIT_EFFECT_DURATION_MS
                - elapsed
        )
        / 220,
    )
    effect = pygame.Surface(
        (28, 14),
        pygame.SRCALPHA,
    )

    for dot_index in range(3):
        reveal = max(
            0.0,
            min(
                1.0,
                (
                        elapsed
                        - dot_index * 70
                )
                / 100,
            ),
        )
        alpha = round(
            230
            * fade_in
            * fade_out
            * reveal
        )
        dot_center = (
            6 + dot_index * 8,
            7,
        )

        pygame.draw.circle(
            effect,
            (
                12,
                13,
                16,
                round(alpha * 0.7),
            ),
            (
                dot_center[0] + 1,
                dot_center[1] + 1,
            ),
            3,
        )
        pygame.draw.circle(
            effect,
            (
                181,
                176,
                163,
                alpha,
            ),
            dot_center,
            2,
        )

    screen.blit(
        effect,
        (
            center_x - effect.get_width() // 2,
            center_y - 37,
        ),
    )


def draw_act_one_player(
    screen,
    center_x,
    center_y,
    cloth_color,
    edge_color,
    skin_color,
    drag_x=0,
    drag_y=0,
    current_time=0,
    movement_progress=None,
    movement_direction=(0, 1),
    attack_progress=None,
    attack_direction=None,
    head_lift_progress=1.0,
    pain_pose=False,
):
    actor = pygame.Surface(
        (32, 34),
        pygame.SRCALPHA,
    )
    actor_center_x = 16
    actor_center_y = 17 + (2 if pain_pose else 0)
    head_drop = round(
        3
        * (
            1.0
            - max(
                0.0,
                min(1.0, head_lift_progress),
            )
        )
    )

    drag_x = max(
        -3,
        min(3, drag_x),
    )
    drag_y = max(
        -3,
        min(3, drag_y),
    )

    pygame.draw.ellipse(
        actor,
        (2, 3, 5, 140),
        (
            actor_center_x - 11,
            actor_center_y + 7,
            22,
            5,
        ),
    )

    pygame.draw.polygon(
        actor,
        (18, 20, 26),
        (
            (
                actor_center_x,
                actor_center_y - 12,
            ),
            (
                actor_center_x + 9,
                actor_center_y - 3,
            ),
            (
                actor_center_x + 11 + drag_x,
                actor_center_y + 10 + drag_y,
            ),
            (
                actor_center_x - 11 + drag_x,
                actor_center_y + 10 + drag_y,
            ),
            (
                actor_center_x - 9,
                actor_center_y - 3,
            ),
        ),
    )
    pygame.draw.polygon(
        actor,
        cloth_color,
        (
            (
                actor_center_x,
                actor_center_y - 10,
            ),
            (
                actor_center_x + 7,
                actor_center_y - 2,
            ),
            (
                actor_center_x + 8 + drag_x,
                actor_center_y + 8 + drag_y,
            ),
            (
                actor_center_x - 8 + drag_x,
                actor_center_y + 8 + drag_y,
            ),
            (
                actor_center_x - 7,
                actor_center_y - 2,
            ),
        ),
    )

    head_center = (
        actor_center_x,
        actor_center_y - 5 + head_drop,
    )

    pygame.draw.circle(
        actor,
        edge_color,
        head_center,
        7,
    )
    pygame.draw.circle(
        actor,
        (25, 29, 37),
        (
            head_center[0],
            head_center[1] + 1,
        ),
        5,
    )

    pygame.draw.line(
        actor,
        edge_color,
        (
            actor_center_x - 7,
            actor_center_y + 1,
        ),
        (
            actor_center_x - 8 + drag_x,
            actor_center_y + 7 + drag_y,
        ),
        2,
    )
    pygame.draw.line(
        actor,
        (82, 94, 107),
        (
            actor_center_x,
            actor_center_y + 1,
        ),
        (
            actor_center_x + drag_x,
            actor_center_y + 7 + drag_y,
        ),
    )
    pygame.draw.circle(
        actor,
        (164, 124, 50),
        (
            actor_center_x,
            actor_center_y + 1,
        ),
        1,
    )

    pygame.draw.rect(
        actor,
        skin_color,
        (
            head_center[0] - 3,
            head_center[1],
            2,
            1,
        ),
    )
    pygame.draw.rect(
        actor,
        skin_color,
        (
            head_center[0] + 2,
            head_center[1],
            2,
            1,
        ),
    )

    screen.blit(
        actor,
        (
            center_x - actor_center_x,
            center_y - 17,
        ),
    )
