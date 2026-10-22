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


def draw_act_one_prisoner(
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
        knife_visible=True,
        knife_pickup_progress=0.0,
        pain_pose=False,
):
    actor = pygame.Surface(
        (30, 42),
        pygame.SRCALPHA,
    )
    center = 15
    walking = movement_progress is not None
    walk_phase = (
        movement_progress * math.tau
        if walking
        else 0.0
    )
    stride = (
        round(math.sin(walk_phase))
        if walking
        else 0
    )
    pickup_progress = max(
        0.0,
        min(1.0, knife_pickup_progress),
    )
    pickup_reach = math.sin(
        math.pi * pickup_progress
    )
    torso_y = (
        11
        + round(pickup_reach * 7)
        + (2 if pain_pose else 0)
    )
    cloth_shadow = tuple(
        max(0, channel - 30)
        for channel in cloth_color
    )
    cloth_deep_shadow = tuple(
        max(0, channel - 43)
        for channel in cloth_color
    )
    cloth_light = tuple(
        min(255, channel + 15)
        for channel in cloth_color
    )
    skin_shadow = tuple(
        max(0, channel - 38)
        for channel in skin_color
    )
    facing_direction = (
        attack_direction
        if attack_direction is not None
        else movement_direction
    )
    facing_up = facing_direction[1] < 0
    facing_side = facing_direction[0] != 0
    attack_reach = (
        round(
            math.sin(math.pi * attack_progress) * 2
        )
        if attack_progress is not None
        else 0
    )

    pygame.draw.ellipse(
        actor,
        (2, 3, 5, 150),
        (6, 27, 18, 4),
    )

    if facing_side:
        left_foot = (
            11 - stride,
            29,
        )
        right_foot = (
            18 + stride,
            28,
        )
    else:
        left_foot = (
            11,
            28 + stride,
        )
        right_foot = (
            19,
            28 - stride,
        )

    if pain_pose:
        left_foot = (
            12,
            29,
        )
        right_foot = (
            18,
            29,
        )

    pygame.draw.line(
        actor,
        (21, 22, 24),
        (12, 20),
        left_foot,
        5,
    )
    pygame.draw.line(
        actor,
        (18, 19, 21),
        (18, 20),
        right_foot,
        5,
    )
    pygame.draw.line(
        actor,
        (55, 55, 55),
        (12, 20),
        left_foot,
        3,
    )
    pygame.draw.line(
        actor,
        (45, 46, 48),
        (18, 20),
        right_foot,
        3,
    )
    pygame.draw.line(
        actor,
        (22, 22, 23),
        (
            left_foot[0] - 2,
            left_foot[1],
        ),
        (
            left_foot[0] + 2,
            left_foot[1],
        ),
        3,
    )
    pygame.draw.line(
        actor,
        (19, 19, 20),
        (
            right_foot[0] - 2,
            right_foot[1],
        ),
        (
            right_foot[0] + 2,
            right_foot[1],
        ),
        3,
    )

    pygame.draw.polygon(
        actor,
        cloth_deep_shadow,
        (
            (10, torso_y),
            (20, torso_y),
            (19, torso_y + 10),
            (17, torso_y + 11),
            (15, torso_y + 10),
            (13, torso_y + 12),
            (10, torso_y + 10),
        ),
    )
    pygame.draw.polygon(
        actor,
        cloth_color,
        (
            (11, torso_y + 1),
            (19, torso_y + 1),
            (18, torso_y + 9),
            (16, torso_y + 10),
            (14, torso_y + 9),
            (12, torso_y + 11),
            (11, torso_y + 9),
        ),
    )
    pygame.draw.line(
        actor,
        cloth_light,
        (12, torso_y + 2),
        (18, torso_y + 2),
    )
    pygame.draw.line(
        actor,
        cloth_shadow,
        (14, torso_y + 2),
        (13, torso_y + 9),
    )
    pygame.draw.line(
        actor,
        edge_color,
        (11, torso_y + 8),
        (19, torso_y + 8),
    )
    pygame.draw.line(
        actor,
        (57, 47, 40),
        (11, torso_y + 9),
        (19, torso_y + 9),
        2,
    )

    if facing_side:
        attack_offset = (attack_reach, 0)
        left_shoulder = (11, torso_y + 3)
        right_shoulder = (19, torso_y + 3)
        left_elbow = (9, torso_y + 7)
        right_elbow = (
            21 + round(attack_offset[0] * 0.5),
            torso_y + 6,
        )
        left_hand = (9, torso_y + 10)
        right_hand = (
            22 + attack_offset[0],
            torso_y + 9,
        )
    elif facing_up:
        attack_offset = (0, -attack_reach)
        left_shoulder = (11, torso_y + 3)
        right_shoulder = (19, torso_y + 3)
        left_elbow = (9, torso_y + 7)
        right_elbow = (
            21,
            torso_y
            + 7
            + round(attack_offset[1] * 0.5),
        )
        left_hand = (9, torso_y + 10)
        right_hand = (
            21,
            torso_y + 10 + attack_offset[1],
        )
    else:
        attack_offset = (0, attack_reach)
        left_shoulder = (11, torso_y + 3)
        right_shoulder = (19, torso_y + 3)
        left_elbow = (9, torso_y + 7)
        right_elbow = (
            21,
            torso_y
            + 7
            + round(attack_offset[1] * 0.5),
        )
        left_hand = (9, torso_y + 10)
        right_hand = (
            21,
            torso_y + 10 + attack_offset[1],
        )

    if pain_pose:
        left_elbow = (
            12,
            torso_y + 4,
        )
        right_elbow = (
            18,
            torso_y + 4,
        )
        left_hand = (
            14,
            torso_y + 6,
        )
        right_hand = (
            16,
            torso_y + 6,
        )

    pickup_arm_bend = round(
        pickup_reach * 2
    )
    right_elbow = (
        right_elbow[0] + pickup_arm_bend,
        right_elbow[1] - round(pickup_reach),
    )

    pygame.draw.line(
        actor,
        cloth_deep_shadow,
        left_shoulder,
        left_elbow,
        3,
    )
    pygame.draw.line(
        actor,
        cloth_deep_shadow,
        right_shoulder,
        right_elbow,
        3,
    )
    pygame.draw.line(
        actor,
        skin_shadow,
        left_elbow,
        left_hand,
        2,
    )
    pygame.draw.line(
        actor,
        skin_color,
        right_elbow,
        right_hand,
        2,
    )
    pygame.draw.circle(
        actor,
        skin_shadow,
        left_hand,
        1,
    )
    pygame.draw.circle(
        actor,
        skin_color,
        right_hand,
        1,
    )

    if facing_up:
        knife_handle_offset = (1, -3)
        knife_tip_offset = (3, -7)
    elif facing_side:
        knife_handle_offset = (3, 1)
        knife_tip_offset = (7, 2)
    else:
        knife_handle_offset = (1, 3)
        knife_tip_offset = (3, 7)

    if 0.5 <= pickup_progress < 1.0:
        pickup_raise = (pickup_progress - 0.5) * 2.0
        knife_handle_offset = (
            round(2 + (knife_handle_offset[0] - 2) * pickup_raise),
            round(knife_handle_offset[1] * pickup_raise),
        )
        knife_tip_offset = (
            round(5 + (knife_tip_offset[0] - 5) * pickup_raise),
            round(1 + (knife_tip_offset[1] - 1) * pickup_raise),
        )

    knife_handle_end = (
        right_hand[0] + knife_handle_offset[0],
        right_hand[1] + knife_handle_offset[1],
    )
    knife_tip = (
        right_hand[0] + knife_tip_offset[0],
        right_hand[1] + knife_tip_offset[1],
    )

    if knife_visible:
        pygame.draw.line(
            actor,
            (23, 20, 19),
            right_hand,
            knife_handle_end,
            3,
        )
        pygame.draw.line(
            actor,
            (101, 76, 51),
            right_hand,
            knife_handle_end,
        )
        pygame.draw.line(
            actor,
            (31, 34, 38),
            (
                knife_handle_end[0] - 1,
                knife_handle_end[1],
            ),
            (
                knife_handle_end[0] + 1,
                knife_handle_end[1],
            ),
            2,
        )
        pygame.draw.line(
            actor,
            (72, 82, 89),
            knife_handle_end,
            knife_tip,
            2,
        )
        pygame.draw.line(
            actor,
            (151, 160, 164),
            knife_handle_end,
            knife_tip,
        )

    pygame.draw.rect(
        actor,
        skin_shadow,
        (
            13,
            torso_y - 3,
            4,
            5,
        ),
    )
    pygame.draw.ellipse(
        actor,
        (22, 21, 22),
        (
            10,
            torso_y - 10,
            10,
            10,
        ),
    )
    pygame.draw.ellipse(
        actor,
        skin_color,
        (
            11,
            torso_y - 9,
            8,
            8,
        ),
    )

    if facing_up:
        pygame.draw.polygon(
            actor,
            (28, 27, 29),
            (
                (10, torso_y - 5),
                (11, torso_y - 10),
                (14, torso_y - 12),
                (18, torso_y - 10),
                (20, torso_y - 6),
                (17, torso_y - 7),
                (15, torso_y - 5),
                (12, torso_y - 7),
            ),
        )
    elif facing_side:
        pygame.draw.polygon(
            actor,
            (30, 27, 27),
            (
                (11, torso_y - 7),
                (12, torso_y - 10),
                (15, torso_y - 12),
                (18, torso_y - 9),
                (19, torso_y - 6),
                (16, torso_y - 7),
                (14, torso_y - 6),
            ),
        )
        pygame.draw.line(
            actor,
            skin_shadow,
            (16, torso_y - 5),
            (19, torso_y - 5),
        )
        pygame.draw.rect(
            actor,
            skin_shadow,
            (
                19,
                torso_y - 7,
                1,
                2,
            ),
        )
        pygame.draw.line(
            actor,
            cloth_light,
            (19, torso_y + 2),
            (18, torso_y + 8),
        )
    else:
        pygame.draw.polygon(
            actor,
            (30, 27, 27),
            (
                (10, torso_y - 7),
                (11, torso_y - 10),
                (14, torso_y - 12),
                (18, torso_y - 10),
                (20, torso_y - 7),
                (18, torso_y - 6),
                (16, torso_y - 8),
                (13, torso_y - 7),
            ),
        )
        pygame.draw.line(
            actor,
            skin_shadow,
            (12, torso_y - 4),
            (18, torso_y - 4),
        )
        pygame.draw.line(
            actor,
            (66, 48, 42),
            (15, torso_y - 6),
            (16, torso_y - 4),
        )

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

    if head_drop > 0:
        head_rectangle = pygame.Rect(
            9,
            0,
            12,
            11,
        )
        head = actor.subsurface(
            head_rectangle,
        ).copy()
        actor.fill(
            (0, 0, 0, 0),
            head_rectangle,
        )
        actor.blit(
            head,
            (
                head_rectangle.x,
                head_rectangle.y + head_drop,
            ),
        )

    if movement_direction[0] < 0:
        actor = pygame.transform.flip(
            actor,
            True,
            False,
        )

    screen.blit(
        actor,
        (
            center_x - center,
            center_y - 18,
        ),
    )

