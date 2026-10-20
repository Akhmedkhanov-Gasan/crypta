from functools import lru_cache
import math

import pygame

from acts.act_one.state import ActOneIntroState
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


CAMERA_HOLD_END_MS = 1000
CAMERA_RISE_END_MS = 3000
ELDER_APPEAR_START_MS = 3200
ELDER_APPEAR_END_MS = 4800
HEAD_LIFT_START_MS = 4700
HEAD_LIFT_END_MS = 5500
ELDER_KNIFE_DRAW_START_MS = 16800
ELDER_KNIFE_DRAW_END_MS = 17600
ELDER_KNIFE_PLACE_END_MS = 18900
ELDER_RETURN_END_MS = 20200
CHAIN_BREAK_MS = 20500
ELDER_FADE_START_MS = 20900
ELDER_FADE_END_MS = 21900
KNIFE_PICKUP_START_MS = 22600
KNIFE_PICKUP_GRAB_MS = 23300
KNIFE_PICKUP_END_MS = 24000
INTRO_END_MS = 24800
SKIP_HOLD_MS = 1200
HUD_FADE_IN_MS = 900

DIALOGUE = (
    (
        6000,
        8800,
        "Awaken, prisoner.",
    ),
    (
        9100,
        13100,
        "Your chains have held you long enough.",
    ),
    (
        13400,
        16500,
        "Rise. The dark below is waiting.",
    ),
)


def _progress(elapsed, start, end):
    if elapsed <= start:
        return 0.0
    if elapsed >= end:
        return 1.0

    progress = (elapsed - start) / (end - start)
    return progress * progress * (3.0 - 2.0 * progress)


def act_one_intro_camera_offset(state):
    if state is None or state.finished:
        return None

    rise = _progress(
        state.elapsed,
        CAMERA_HOLD_END_MS,
        CAMERA_RISE_END_MS,
    )

    return 10.0 + 42.0 * (1.0 - rise)


def act_one_intro_head_lift(state):
    if state is None or state.finished:
        return 1.0

    return _progress(
        state.elapsed,
        HEAD_LIFT_START_MS,
        HEAD_LIFT_END_MS,
    )


def act_one_intro_knife_pickup(state):
    if state is None or state.finished:
        return 0.0

    return _progress(
        state.elapsed,
        KNIFE_PICKUP_START_MS,
        KNIFE_PICKUP_END_MS,
    )


def act_one_intro_player_has_knife(state):
    return (
        state is None
        or state.finished
        or state.elapsed >= KNIFE_PICKUP_GRAB_MS
    )


def act_one_intro_active(game_state):
    state = getattr(game_state, "act_one_intro", None)
    return state is not None and not state.finished


def act_one_intro_hud_opacity(state, current_time):
    if state is None:
        return 255

    if not state.finished:
        return 0

    if state.updated_at < 0:
        return 255

    fade_progress = _progress(
        current_time,
        state.updated_at,
        state.updated_at + HUD_FADE_IN_MS,
    )
    return round(255 * fade_progress)


def update_act_one_intro(
    game_state,
    current_time,
    enabled,
):
    state = getattr(game_state, "act_one_intro", None)

    if state is None or state.finished:
        return

    if state.updated_at < 0:
        state.updated_at = current_time

    delta = max(
        0,
        min(50, current_time - state.updated_at),
    )
    state.updated_at = current_time

    if not enabled:
        state.skip_held_ms = 0
        return

    state.elapsed = min(
        INTRO_END_MS,
        state.elapsed + delta,
    )

    holding_space = (
        pygame.key.get_focused()
        and pygame.key.get_pressed()[pygame.K_SPACE]
    )

    if holding_space:
        state.skip_held_ms = min(
            SKIP_HOLD_MS,
            state.skip_held_ms + delta,
        )
    else:
        state.skip_held_ms = 0

    if state.skip_held_ms >= SKIP_HOLD_MS:
        state.elapsed = INTRO_END_MS
        state.finished = True
        state.skip_held_ms = 0
    elif state.elapsed >= INTRO_END_MS:
        state.finished = True


def _draw_chain(
    screen,
    start,
    end,
):
    delta_x = end[0] - start[0]
    delta_y = end[1] - start[1]
    distance = math.hypot(delta_x, delta_y)
    link_count = max(3, round(distance / 5))

    for index in range(link_count + 1):
        progress = index / link_count
        x = round(start[0] + delta_x * progress)
        y = round(
            start[1]
            + delta_y * progress
            + math.sin(math.pi * progress) * 2
        )

        if index % 2 == 0:
            rectangle = pygame.Rect(x - 1, y, 3, 2)
        else:
            rectangle = pygame.Rect(x, y - 1, 2, 3)

        pygame.draw.rect(
            screen,
            (20, 22, 24),
            rectangle,
        )
        pygame.draw.rect(
            screen,
            (76, 81, 84),
            rectangle,
            width=1,
        )


def _draw_wall_anchor(
    screen,
    position,
):
    pygame.draw.circle(
        screen,
        (18, 19, 21),
        position,
        4,
    )
    pygame.draw.circle(
        screen,
        (68, 72, 75),
        position,
        3,
        width=1,
    )
    pygame.draw.circle(
        screen,
        (12, 13, 15),
        position,
        1,
    )


def _draw_broken_chains(
    screen,
    center_x,
    center_y,
):
    pieces = (
        (-15, 17, 3, 2),
        (-12, 19, 2, 3),
        (-8, 21, 3, 2),
        (-4, 22, 2, 3),
        (5, 22, 3, 2),
        (9, 20, 2, 3),
        (13, 18, 3, 2),
        (17, 16, 2, 3),
    )

    for index, piece in enumerate(pieces):
        rectangle = pygame.Rect(
            center_x + piece[0],
            center_y + piece[1],
            piece[2],
            piece[3],
        )
        pygame.draw.rect(
            screen,
            (
                (72, 76, 79)
                if index % 2 == 0
                else (48, 52, 55)
            ),
            rectangle,
            width=1,
        )


def _draw_chain_break(
    screen,
    center_x,
    center_y,
    elapsed,
):
    break_elapsed = elapsed - CHAIN_BREAK_MS

    if not 0 <= break_elapsed < 480:
        return

    progress = break_elapsed / 480
    lift = round(math.sin(math.pi * progress) * 7)

    fragments = (
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    )

    for index, direction in enumerate(fragments):
        distance = round(progress * (5 + index * 2))
        x = center_x + direction[0] * distance
        y = (
            center_y
            + 2
            + direction[1] * distance
            - lift
        )
        rectangle = pygame.Rect(
            x - 1,
            y,
            3 if index % 2 == 0 else 2,
            2 if index % 2 == 0 else 3,
        )
        pygame.draw.rect(
            screen,
            (82, 87, 90),
            rectangle,
            width=1,
        )

def _draw_intro_knife_shape(
    surface,
    handle_start,
    handle_end,
    blade_tip,
):
    pygame.draw.line(
        surface,
        (20, 18, 17),
        handle_start,
        handle_end,
        3,
    )
    pygame.draw.line(
        surface,
        (91, 67, 45),
        handle_start,
        handle_end,
    )
    pygame.draw.line(
        surface,
        (27, 30, 34),
        (
            handle_end[0],
            handle_end[1] - 2,
        ),
        (
            handle_end[0],
            handle_end[1] + 2,
        ),
        2,
    )
    pygame.draw.line(
        surface,
        (59, 68, 74),
        handle_end,
        blade_tip,
        2,
    )
    pygame.draw.line(
        surface,
        (132, 140, 144),
        handle_end,
        blade_tip,
    )


def _draw_intro_knife(
    screen,
    center_x,
    center_y,
    elapsed,
):
    if (
        elapsed < ELDER_KNIFE_PLACE_END_MS
        or elapsed >= KNIFE_PICKUP_GRAB_MS
    ):
        return

    handle_start = (
        center_x + 7,
        center_y + 10,
    )
    handle_end = (
        center_x + 9,
        center_y + 10,
    )
    blade_tip = (
        center_x + 12,
        center_y + 11,
    )

    _draw_intro_knife_shape(
        screen,
        handle_start,
        handle_end,
        blade_tip,
    )


def _elder_offer_pose(elapsed):
    if elapsed < ELDER_KNIFE_DRAW_END_MS:
        return 0.0

    if elapsed < ELDER_KNIFE_PLACE_END_MS:
        return _progress(
            elapsed,
            ELDER_KNIFE_DRAW_END_MS,
            ELDER_KNIFE_PLACE_END_MS,
        )

    if elapsed < ELDER_RETURN_END_MS:
        return 1.0 - _progress(
            elapsed,
            ELDER_KNIFE_PLACE_END_MS,
            ELDER_RETURN_END_MS,
        )

    return 0.0


def _draw_elder_knife_offer(
    screen,
    center_x,
    center_y,
    elapsed,
):
    if (
        elapsed < ELDER_KNIFE_DRAW_START_MS
        or elapsed >= KNIFE_PICKUP_START_MS
    ):
        return

    offer_pose = _elder_offer_pose(elapsed)
    elder_x = center_x - round(offer_pose * 10)
    elder_y = center_y + round(offer_pose * 4)

    shoulder = (
        elder_x - 6,
        elder_y - 3,
    )
    hidden_hand = (
        elder_x - 4,
        elder_y - 1,
    )
    ready_hand = (
        elder_x - 9,
        elder_y + 2,
    )
    floor_hand = (
        center_x - TILE_SIZE + 9,
        center_y + 12,
    )
    resting_hand = (
        elder_x - 8,
        elder_y + 6,
    )

    knife_visible = False

    if elapsed < ELDER_KNIFE_DRAW_END_MS:
        draw_progress = _progress(
            elapsed,
            ELDER_KNIFE_DRAW_START_MS,
            ELDER_KNIFE_DRAW_END_MS,
        )
        hand = (
            round(
                hidden_hand[0]
                + (ready_hand[0] - hidden_hand[0])
                * draw_progress
            ),
            round(
                hidden_hand[1]
                + (ready_hand[1] - hidden_hand[1])
                * draw_progress
            ),
        )
        handle_end = (
            hand[0],
            hand[1] - round(3 * draw_progress),
        )
        blade_tip = (
            hand[0],
            hand[1] - round(9 * draw_progress),
        )
        knife_visible = draw_progress > 0.08
    elif elapsed < ELDER_KNIFE_PLACE_END_MS:
        place_progress = _progress(
            elapsed,
            ELDER_KNIFE_DRAW_END_MS,
            ELDER_KNIFE_PLACE_END_MS,
        )
        hand = (
            round(
                ready_hand[0]
                + (floor_hand[0] - ready_hand[0])
                * place_progress
            ),
            round(
                ready_hand[1]
                + (floor_hand[1] - ready_hand[1])
                * place_progress
            ),
        )
        handle_end = (
            hand[0] + round(2 * place_progress),
            hand[1] - round(3 * (1.0 - place_progress)),
        )
        blade_tip = (
            hand[0] + round(5 * place_progress),
            hand[1] + round(
                -9 * (1.0 - place_progress)
                + place_progress
            ),
        )
        knife_visible = True
    else:
        return_progress = _progress(
            elapsed,
            ELDER_KNIFE_PLACE_END_MS,
            KNIFE_PICKUP_START_MS,
        )
        hand = (
            round(
                floor_hand[0]
                + (resting_hand[0] - floor_hand[0])
                * return_progress
            ),
            round(
                floor_hand[1]
                + (resting_hand[1] - floor_hand[1])
                * return_progress
            ),
        )
        handle_end = hand
        blade_tip = hand

    elbow = (
        round((shoulder[0] + hand[0]) / 2),
        round((shoulder[1] + hand[1]) / 2) + 3,
    )

    pygame.draw.line(
        screen,
        (20, 20, 22),
        shoulder,
        elbow,
        5,
    )
    pygame.draw.line(
        screen,
        (29, 28, 29),
        elbow,
        hand,
        4,
    )
    pygame.draw.line(
        screen,
        (58, 53, 48),
        shoulder,
        elbow,
        2,
    )
    pygame.draw.line(
        screen,
        (67, 58, 50),
        elbow,
        hand,
        2,
    )
    pygame.draw.circle(
        screen,
        (112, 79, 61),
        hand,
        2,
    )

    if knife_visible:
        _draw_intro_knife_shape(
            screen,
            hand,
            handle_end,
            blade_tip,
        )


def _draw_reworked_elder(
        screen,
        center_x,
        center_y,
        elapsed,
        opacity,
):
    offer_pose = _elder_offer_pose(elapsed)
    elder_x = center_x - round(offer_pose * 18)
    elder_y = center_y + round(offer_pose * 3)

    actor = pygame.Surface(
        (30, 36),
        pygame.SRCALPHA,
    )

    pygame.draw.ellipse(
        actor,
        (4, 5, 7, 145),
        (7, 31, 17, 4),
    )

    pygame.draw.line(
        actor,
        (24, 23, 24),
        (13, 26),
        (12, 32),
        4,
    )
    pygame.draw.line(
        actor,
        (19, 19, 20),
        (17, 26),
        (19, 32),
        4,
    )
    pygame.draw.line(
        actor,
        (62, 50, 41),
        (10, 33),
        (14, 33),
        2,
    )
    pygame.draw.line(
        actor,
        (52, 45, 40),
        (18, 33),
        (22, 33),
        2,
    )

    pygame.draw.polygon(
        actor,
        (18, 19, 21),
        (
            (10, 15),
            (12, 13),
            (18, 13),
            (20, 15),
            (20, 27),
            (19, 30),
            (17, 29),
            (15, 31),
            (12, 29),
            (10, 28),
        ),
    )
    pygame.draw.polygon(
        actor,
        (43, 41, 41),
        (
            (11, 15),
            (13, 14),
            (17, 14),
            (19, 16),
            (19, 26),
            (17, 29),
            (15, 28),
            (12, 29),
            (11, 25),
        ),
    )
    pygame.draw.polygon(
        actor,
        (57, 53, 50),
        (
            (11, 16),
            (13, 14),
            (14, 14),
            (14, 28),
            (12, 28),
            (11, 25),
        ),
    )
    pygame.draw.line(
        actor,
        (27, 27, 28),
        (15, 15),
        (15, 29),
    )
    pygame.draw.line(
        actor,
        (55, 52, 50),
        (17, 16),
        (17, 27),
    )
    pygame.draw.line(
        actor,
        (31, 30, 31),
        (18, 18),
        (18, 26),
    )

    pygame.draw.line(
        actor,
        (22, 22, 24),
        (19, 16),
        (21, 24),
        3,
    )
    pygame.draw.line(
        actor,
        (58, 53, 49),
        (19, 16),
        (21, 24),
    )
    pygame.draw.circle(
        actor,
        (102, 73, 58),
        (21, 25),
        1,
    )

    pygame.draw.rect(
        actor,
        (67, 48, 41),
        (13, 11, 4, 4),
    )
    pygame.draw.polygon(
        actor,
        (70, 53, 47),
        (
            (12, 5),
            (14, 4),
            (17, 4),
            (19, 6),
            (19, 9),
            (17, 13),
            (14, 14),
            (12, 12),
            (11, 9),
        ),
    )
    pygame.draw.polygon(
        actor,
        (103, 76, 60),
        (
            (13, 6),
            (15, 5),
            (17, 6),
            (18, 8),
            (17, 11),
            (15, 13),
            (13, 11),
            (12, 8),
        ),
    )
    pygame.draw.polygon(
        actor,
        (48, 41, 40),
        (
            (12, 6),
            (14, 5),
            (14, 9),
            (13, 11),
            (12, 10),
        ),
    )
    pygame.draw.polygon(
        actor,
        (60, 47, 43),
        (
            (17, 6),
            (19, 7),
            (18, 10),
            (17, 12),
            (16, 10),
        ),
    )
    pygame.draw.line(
        actor,
        (126, 89, 69),
        (14, 11),
        (15, 12),
    )
    pygame.draw.line(
        actor,
        (78, 53, 46),
        (15, 12),
        (17, 11),
    )

    pygame.draw.polygon(
        actor,
        (98, 99, 98),
        (
            (11, 6),
            (11, 4),
            (13, 3),
            (17, 3),
            (19, 5),
            (19, 6),
            (17, 5),
            (15, 5),
            (13, 6),
        ),
    )
    pygame.draw.line(
        actor,
        (153, 153, 149),
        (13, 4),
        (16, 4),
    )

    pygame.draw.polygon(
        actor,
        (69, 70, 70),
        (
            (12, 11),
            (14, 12),
            (16, 11),
            (18, 12),
            (17, 16),
            (15, 18),
            (13, 16),
        ),
    )
    pygame.draw.polygon(
        actor,
        (126, 127, 124),
        (
            (14, 13),
            (16, 12),
            (17, 13),
            (16, 16),
            (15, 17),
            (14, 15),
        ),
    )

    shoulder = (10, 16)
    relaxed_hand = (10, 24)
    lapel_hand = (12, 17)
    ready_hand = (9, 19)
    floor_hand = (8, 25)
    hand = relaxed_hand
    knife_visible = False
    handle_end = hand
    blade_tip = hand

    if (
            ELDER_KNIFE_DRAW_START_MS
            <= elapsed
            < ELDER_KNIFE_DRAW_END_MS
    ):
        draw_progress = _progress(
            elapsed,
            ELDER_KNIFE_DRAW_START_MS,
            ELDER_KNIFE_DRAW_END_MS,
        )

        if draw_progress < 0.45:
            hand_progress = draw_progress / 0.45
            hand = (
                round(
                    relaxed_hand[0]
                    + (lapel_hand[0] - relaxed_hand[0])
                    * hand_progress
                ),
                round(
                    relaxed_hand[1]
                    + (lapel_hand[1] - relaxed_hand[1])
                    * hand_progress
                ),
            )
        else:
            knife_progress = (
                                     draw_progress - 0.45
                             ) / 0.55
            hand = (
                round(
                    lapel_hand[0]
                    + (ready_hand[0] - lapel_hand[0])
                    * knife_progress
                ),
                round(
                    lapel_hand[1]
                    + (ready_hand[1] - lapel_hand[1])
                    * knife_progress
                ),
            )
            handle_end = (
                hand[0],
                hand[1] - round(3 * knife_progress),
            )
            blade_tip = (
                hand[0],
                hand[1] - round(7 * knife_progress),
            )
            knife_visible = knife_progress > 0.08
    elif (
                ELDER_KNIFE_DRAW_END_MS
                <= elapsed
                < ELDER_KNIFE_PLACE_END_MS
        ):
        place_progress = _progress(
            elapsed,
            ELDER_KNIFE_DRAW_END_MS,
            ELDER_KNIFE_PLACE_END_MS,
        )
        hand = (
            round(
                ready_hand[0]
                + (floor_hand[0] - ready_hand[0])
                * place_progress
            ),
            round(
                ready_hand[1]
                + (floor_hand[1] - ready_hand[1])
                * place_progress
            ),
        )
        handle_end = (
            hand[0] + round(2 * place_progress),
            hand[1] - round(3 * (1.0 - place_progress)),
        )
        blade_tip = (
            hand[0] + round(5 * place_progress),
            hand[1] + round(
                -7 * (1.0 - place_progress)
                + place_progress
            ),
        )
        knife_visible = True
    elif elapsed < KNIFE_PICKUP_START_MS:
        return_progress = _progress(
            elapsed,
            ELDER_KNIFE_PLACE_END_MS,
            KNIFE_PICKUP_START_MS,
        )
        hand = (
            round(
                floor_hand[0]
                + (relaxed_hand[0] - floor_hand[0])
                * return_progress
            ),
            round(
                floor_hand[1]
                + (relaxed_hand[1] - floor_hand[1])
                * return_progress
            ),
        )

    elbow = (
        round((shoulder[0] + hand[0]) / 2) - 1,
        round((shoulder[1] + hand[1]) / 2),
    )

    pygame.draw.line(
        actor,
        (22, 22, 24),
        shoulder,
        elbow,
        4,
    )
    pygame.draw.line(
        actor,
        (25, 25, 27),
        elbow,
        hand,
        4,
    )
    pygame.draw.line(
        actor,
        (60, 55, 51),
        shoulder,
        elbow,
        2,
    )
    pygame.draw.line(
        actor,
        (65, 57, 50),
        elbow,
        hand,
        2,
    )
    pygame.draw.circle(
        actor,
        (116, 82, 63),
        hand,
        2,
    )

    if knife_visible:
        _draw_intro_knife_shape(
            actor,
            hand,
            handle_end,
            blade_tip,
        )

    actor.set_alpha(round(255 * opacity))

    screen.blit(
        actor,
        (
            elder_x - actor.get_width() // 2,
            elder_y - 18,
        ),
    )


def _draw_final_elder_sleeve(
        actor,
        shoulder,
        elbow,
        hand,
):
    pygame.draw.polygon(
        actor,
        (20, 20, 22),
        (
            (shoulder[0] - 1, shoulder[1]),
            (shoulder[0] + 2, shoulder[1]),
            (elbow[0] + 2, elbow[1]),
            (hand[0] + 1, hand[1]),
            (hand[0] - 1, hand[1] + 1),
            (elbow[0] - 1, elbow[1]),
        ),
    )
    pygame.draw.line(
        actor,
        (51, 48, 47),
        shoulder,
        elbow,
        2,
    )
    pygame.draw.line(
        actor,
        (48, 45, 44),
        elbow,
        hand,
        2,
    )
    pygame.draw.rect(
        actor,
        (98, 70, 56),
        (
            hand[0] - 1,
            hand[1],
            2,
            2,
        ),
    )


def _draw_final_elder(
        screen,
        center_x,
        center_y,
        elapsed,
        opacity,
):
    offer_pose = _elder_offer_pose(elapsed)
    elder_x = center_x - round(offer_pose * 19)
    elder_y = center_y + round(offer_pose * 3)

    actor = pygame.Surface(
        (28, 36),
        pygame.SRCALPHA,
    )

    pygame.draw.ellipse(
        actor,
        (4, 5, 7, 145),
        (5, 31, 18, 4),
    )

    pygame.draw.line(
        actor,
        (22, 22, 23),
        (12, 26),
        (11, 32),
        4,
    )
    pygame.draw.line(
        actor,
        (18, 18, 19),
        (16, 26),
        (18, 32),
        4,
    )
    pygame.draw.line(
        actor,
        (60, 49, 41),
        (9, 33),
        (13, 33),
        2,
    )
    pygame.draw.line(
        actor,
        (51, 44, 40),
        (17, 33),
        (21, 33),
        2,
    )

    pygame.draw.polygon(
        actor,
        (17, 18, 20),
        (
            (8, 15),
            (11, 12),
            (17, 12),
            (20, 15),
            (21, 27),
            (18, 31),
            (15, 29),
            (12, 31),
            (8, 28),
        ),
    )
    pygame.draw.polygon(
        actor,
        (43, 41, 41),
        (
            (10, 15),
            (12, 13),
            (16, 13),
            (19, 15),
            (19, 26),
            (17, 29),
            (14, 28),
            (11, 29),
            (9, 26),
        ),
    )
    pygame.draw.polygon(
        actor,
        (56, 52, 49),
        (
            (10, 16),
            (12, 14),
            (13, 14),
            (13, 28),
            (11, 28),
            (9, 25),
        ),
    )
    pygame.draw.line(
        actor,
        (27, 27, 28),
        (14, 15),
        (14, 29),
    )
    pygame.draw.line(
        actor,
        (52, 49, 47),
        (16, 16),
        (16, 27),
    )
    pygame.draw.line(
        actor,
        (32, 31, 32),
        (18, 18),
        (18, 26),
    )
    pygame.draw.rect(
        actor,
        (74, 53, 45),
        (13, 9, 4, 5),
    )

    pygame.draw.polygon(
        actor,
        (65, 47, 41),
        (
            (11, 4),
            (13, 3),
            (17, 3),
            (19, 5),
            (19, 8),
            (17, 11),
            (12, 11),
            (10, 9),
            (10, 6),
        ),
    )
    pygame.draw.polygon(
        actor,
        (112, 78, 61),
        (
            (12, 4),
            (17, 4),
            (18, 5),
            (18, 8),
            (16, 10),
            (12, 10),
            (11, 8),
            (11, 5),
        ),
    )
    pygame.draw.polygon(
        actor,
        (91, 63, 52),
        (
            (16, 4),
            (18, 5),
            (18, 8),
            (16, 10),
            (15, 9),
            (16, 7),
        ),
    )

    pygame.draw.polygon(
        actor,
        (91, 92, 92),
        (
            (10, 6),
            (10, 4),
            (12, 2),
            (17, 2),
            (19, 4),
            (19, 6),
            (17, 5),
            (15, 4),
            (12, 4),
            (11, 6),
        ),
    )
    pygame.draw.line(
        actor,
        (151, 151, 147),
        (12, 3),
        (17, 3),
    )

    pygame.draw.polygon(
        actor,
        (70, 70, 69),
        (
            (11, 9),
            (13, 10),
            (14, 11),
            (16, 10),
            (18, 10),
            (17, 13),
            (15, 16),
            (13, 15),
            (11, 13),
        ),
    )
    pygame.draw.polygon(
        actor,
        (132, 132, 128),
        (
            (13, 10),
            (14, 11),
            (16, 10),
            (17, 11),
            (16, 13),
            (15, 15),
            (13, 14),
        ),
    )
    relaxed_hand = (9, 24)
    lapel_hand = (12, 17)
    ready_hand = (9, 20)
    floor_hand = (8, 25)
    active_hand = relaxed_hand
    knife_visible = False
    handle_end = active_hand
    blade_tip = active_hand

    if (
        ELDER_KNIFE_DRAW_START_MS
        <= elapsed
        < ELDER_KNIFE_DRAW_END_MS
    ):
        draw_progress = _progress(
            elapsed,
            ELDER_KNIFE_DRAW_START_MS,
            ELDER_KNIFE_DRAW_END_MS,
        )

        if draw_progress < 0.5:
            hand_progress = draw_progress * 2.0
            active_hand = (
                round(
                    relaxed_hand[0]
                    + (lapel_hand[0] - relaxed_hand[0])
                    * hand_progress
                ),
                round(
                    relaxed_hand[1]
                    + (lapel_hand[1] - relaxed_hand[1])
                    * hand_progress
                ),
            )
        else:
            knife_progress = (
                                     draw_progress - 0.5
                             ) * 2.0
            active_hand = (
                round(
                    lapel_hand[0]
                    + (ready_hand[0] - lapel_hand[0])
                    * knife_progress
                ),
                round(
                    lapel_hand[1]
                    + (ready_hand[1] - lapel_hand[1])
                    * knife_progress
                ),
            )
            handle_end = (
                active_hand[0],
                active_hand[1] - round(3 * knife_progress),
            )
            blade_tip = (
                active_hand[0],
                active_hand[1] - round(7 * knife_progress),
            )
            knife_visible = knife_progress > 0.08
    elif (
            ELDER_KNIFE_DRAW_END_MS
            <= elapsed
            < ELDER_KNIFE_PLACE_END_MS
    ):
        place_progress = _progress(
            elapsed,
            ELDER_KNIFE_DRAW_END_MS,
            ELDER_KNIFE_PLACE_END_MS,
        )
        active_hand = (
            round(
                ready_hand[0]
                + (floor_hand[0] - ready_hand[0])
                * place_progress
            ),
            round(
                ready_hand[1]
                + (floor_hand[1] - ready_hand[1])
                * place_progress
            ),
        )
        handle_end = (
            active_hand[0] + round(2 * place_progress),
            active_hand[1] - round(
                3 * (1.0 - place_progress)
            ),
        )
        blade_tip = (
            active_hand[0] + round(5 * place_progress),
            active_hand[1] + round(
                -7 * (1.0 - place_progress)
                + place_progress
            ),
        )
        knife_visible = True
    elif (
                ELDER_KNIFE_PLACE_END_MS
                <= elapsed
                < ELDER_RETURN_END_MS
        ):
        return_progress = _progress(
            elapsed,
            ELDER_KNIFE_PLACE_END_MS,
            ELDER_RETURN_END_MS,
        )
        active_hand = (
            round(
                floor_hand[0]
                + (relaxed_hand[0] - floor_hand[0])
                * return_progress
            ),
            round(
                floor_hand[1]
                + (relaxed_hand[1] - floor_hand[1])
                * return_progress
            ),
        )

    far_shoulder = (18, 15)
    far_elbow = (20, 20)
    far_hand = (20, 24)

    _draw_final_elder_sleeve(
        actor,
        far_shoulder,
        far_elbow,
        far_hand,
    )

    near_shoulder = (10, 15)
    near_elbow = (
        round(
            (
                    near_shoulder[0]
                    + active_hand[0]
            ) / 2
        ),
        round(
            (
                    near_shoulder[1]
                    + active_hand[1]
            ) / 2
        ),
    )

    _draw_final_elder_sleeve(
        actor,
        near_shoulder,
        near_elbow,
        active_hand,
    )

    if knife_visible:
        _draw_intro_knife_shape(
            actor,
            active_hand,
            handle_end,
            blade_tip,
        )

    actor.set_alpha(round(255 * opacity))

    screen.blit(
        actor,
        (
            elder_x - actor.get_width() // 2,
            elder_y - 18,
        ),
    )


def _draw_elder(
        screen,
        center_x,
        center_y,
        elapsed,
):
    appearance = _progress(
        elapsed,
        ELDER_APPEAR_START_MS,
        ELDER_APPEAR_END_MS,
    )
    disappearance = _progress(
        elapsed,
        ELDER_FADE_START_MS,
        ELDER_FADE_END_MS,
    )
    opacity = appearance * (1.0 - disappearance)

    if opacity <= 0:
        return

    _draw_final_elder(
        screen,
        center_x,
        center_y,
        elapsed,
        opacity,
    )
    return

    actor = pygame.Surface(
        (52, 62),
        pygame.SRCALPHA,
    )

    for index in range(8):
        phase = elapsed / 420 + index * 1.7
        radius = 15 + index * 2
        particle_x = round(
            26 + math.cos(phase) * radius
        )
        particle_y = round(
            34
            + math.sin(phase * 0.73) * 23
            - appearance * 5
        )
        particle_alpha = round(
            70
            * opacity
            * (0.45 + 0.55 * abs(math.sin(phase)))
        )
        pygame.draw.rect(
            actor,
            (17, 19, 25, particle_alpha),
            (
                particle_x,
                particle_y,
                2 + index % 2,
                2 + (index + 1) % 2,
            ),
        )

    pygame.draw.ellipse(
        actor,
        (3, 4, 6, 150),
        (7, 51, 39, 7),
    )

    pygame.draw.line(
        actor,
        (28, 27, 28),
        (19, 43),
        (16, 53),
        5,
    )
    pygame.draw.line(
        actor,
        (24, 24, 25),
        (30, 43),
        (33, 53),
        5,
    )
    pygame.draw.line(
        actor,
        (55, 50, 46),
        (14, 53),
        (21, 53),
        3,
    )
    pygame.draw.line(
        actor,
        (48, 44, 41),
        (30, 53),
        (37, 53),
        3,
    )

    pygame.draw.polygon(
        actor,
        (24, 25, 28),
        (
            (14, 21),
            (34, 21),
            (38, 47),
            (31, 51),
            (24, 48),
            (17, 52),
            (9, 47),
        ),
    )
    pygame.draw.polygon(
        actor,
        (51, 49, 48),
        (
            (16, 22),
            (32, 22),
            (34, 45),
            (28, 48),
            (23, 45),
            (17, 49),
            (12, 45),
        ),
    )
    pygame.draw.polygon(
        actor,
        (70, 65, 60),
        (
            (17, 23),
            (24, 20),
            (24, 45),
            (18, 48),
            (14, 44),
        ),
    )
    pygame.draw.line(
        actor,
        (93, 81, 67),
        (15, 28),
        (33, 28),
        2,
    )
    pygame.draw.line(
        actor,
        (38, 34, 31),
        (24, 28),
        (24, 45),
        2,
    )

    pygame.draw.line(
        actor,
        (43, 41, 41),
        (14, 25),
        (8, 37),
        4,
    )
    pygame.draw.line(
        actor,
        (53, 49, 45),
        (34, 25),
        (39, 35),
        4,
    )
    pygame.draw.circle(
        actor,
        (112, 94, 78),
        (8, 38),
        2,
    )
    pygame.draw.circle(
        actor,
        (106, 89, 74),
        (39, 36),
        2,
    )

    pygame.draw.ellipse(
        actor,
        (25, 25, 28),
        (13, 5, 23, 22),
    )
    pygame.draw.ellipse(
        actor,
        (65, 61, 58),
        (16, 8, 17, 17),
    )
    pygame.draw.ellipse(
        actor,
        (19, 19, 21),
        (18, 10, 13, 10),
    )
    pygame.draw.polygon(
        actor,
        (117, 112, 104),
        (
            (18, 17),
            (31, 17),
            (29, 28),
            (24, 32),
            (19, 27),
        ),
    )
    pygame.draw.polygon(
        actor,
        (154, 148, 136),
        (
            (20, 18),
            (29, 18),
            (28, 25),
            (24, 29),
            (20, 25),
        ),
    )
    pygame.draw.line(
        actor,
        (181, 176, 160),
        (20, 20),
        (22, 20),
    )

    actor = pygame.transform.scale(
        actor,
        (30, 36),
    )

    pygame.draw.polygon(
        actor,
        (27, 27, 29),
        (
            (8, 14),
            (12, 12),
            (18, 12),
            (22, 14),
            (21, 20),
            (17, 18),
            (14, 20),
            (9, 18),
        ),
    )
    pygame.draw.line(
        actor,
        (73, 52, 38),
        (19, 16),
        (16, 31),
        3,
    )
    pygame.draw.line(
        actor,
        (112, 75, 45),
        (19, 16),
        (16, 30),
    )
    pygame.draw.line(
        actor,
        (35, 34, 35),
        (10, 26),
        (8, 32),
        2,
    )
    pygame.draw.line(
        actor,
        (35, 34, 35),
        (21, 26),
        (23, 32),
        2,
    )

    pygame.draw.polygon(
        actor,
        (83, 56, 45),
        (
            (10, 7),
            (12, 5),
            (18, 5),
            (21, 7),
            (20, 13),
            (17, 15),
            (13, 14),
            (10, 12),
        ),
    )
    pygame.draw.polygon(
        actor,
        (126, 85, 61),
        (
            (11, 7),
            (13, 6),
            (18, 6),
            (20, 8),
            (19, 12),
            (17, 14),
            (13, 13),
            (11, 11),
        ),
    )
    pygame.draw.line(
        actor,
        (105, 69, 52),
        (12, 8),
        (12, 11),
    )
    pygame.draw.line(
        actor,
        (102, 64, 47),
        (15, 9),
        (15, 12),
    )
    pygame.draw.line(
        actor,
        (150, 97, 65),
        (16, 8),
        (17, 11),
    )
    pygame.draw.line(
        actor,
        (78, 48, 39),
        (14, 13),
        (18, 13),
    )

    pygame.draw.polygon(
        actor,
        (112, 113, 111),
        (
            (10, 7),
            (10, 5),
            (12, 3),
            (14, 4),
            (16, 3),
            (19, 4),
            (21, 6),
            (20, 7),
            (18, 6),
            (16, 6),
            (14, 5),
            (12, 7),
        ),
    )
    pygame.draw.rect(
        actor,
        (88, 89, 88),
        (9, 7, 2, 4),
    )
    pygame.draw.rect(
        actor,
        (96, 97, 95),
        (20, 7, 2, 4),
    )
    pygame.draw.line(
        actor,
        (164, 164, 159),
        (12, 4),
        (14, 4),
    )
    pygame.draw.line(
        actor,
        (145, 145, 141),
        (17, 4),
        (19, 5),
    )

    pygame.draw.polygon(
        actor,
        (80, 80, 78),
        (
            (11, 12),
            (13, 12),
            (15, 13),
            (17, 12),
            (20, 13),
            (19, 16),
            (16, 18),
            (13, 16),
        ),
    )
    pygame.draw.polygon(
        actor,
        (136, 136, 131),
        (
            (13, 13),
            (15, 14),
            (17, 13),
            (19, 14),
            (18, 16),
            (16, 17),
            (14, 16),
        ),
    )

    pygame.draw.rect(
        actor,
        (103, 68, 48),
        (5, 23, 2, 3),
    )
    pygame.draw.rect(
        actor,
        (99, 65, 46),
        (23, 23, 2, 3),
    )

    actor.fill(
        (0, 0, 0, 0),
        pygame.Rect(4, 2, 23, 33),
    )

    pygame.draw.ellipse(
        actor,
        (5, 6, 8, 145),
        (5, 30, 21, 5),
    )
    pygame.draw.line(
        actor,
        (24, 23, 24),
        (12, 26),
        (10, 33),
        5,
    )
    pygame.draw.line(
        actor,
        (20, 20, 21),
        (18, 26),
        (20, 33),
        5,
    )
    pygame.draw.line(
        actor,
        (57, 49, 43),
        (8, 33),
        (13, 33),
        3,
    )
    pygame.draw.line(
        actor,
        (51, 45, 41),
        (18, 33),
        (23, 33),
        3,
    )

    pygame.draw.polygon(
        actor,
        (21, 21, 23),
        (
            (8, 14),
            (12, 12),
            (20, 13),
            (24, 17),
            (22, 29),
            (18, 32),
            (11, 31),
            (7, 27),
        ),
    )
    pygame.draw.polygon(
        actor,
        (47, 44, 43),
        (
            (9, 15),
            (13, 13),
            (19, 14),
            (22, 17),
            (20, 28),
            (16, 30),
            (11, 29),
            (8, 26),
        ),
    )
    pygame.draw.polygon(
        actor,
        (65, 57, 49),
        (
            (10, 15),
            (14, 13),
            (14, 29),
            (10, 28),
            (8, 25),
        ),
    )
    pygame.draw.line(
        actor,
        (105, 72, 45),
        (20, 15),
        (15, 29),
        3,
    )
    pygame.draw.line(
        actor,
        (55, 43, 35),
        (20, 15),
        (15, 29),
    )

    pygame.draw.line(
        actor,
        (26, 25, 26),
        (20, 16),
        (23, 24),
        4,
    )
    pygame.draw.line(
        actor,
        (62, 54, 48),
        (20, 16),
        (23, 24),
        2,
    )
    pygame.draw.circle(
        actor,
        (105, 75, 58),
        (23, 25),
        2,
    )

    pygame.draw.polygon(
        actor,
        (76, 52, 43),
        (
            (9, 7),
            (11, 5),
            (16, 4),
            (20, 7),
            (19, 12),
            (16, 15),
            (11, 14),
            (8, 11),
            (8, 9),
        ),
    )
    pygame.draw.polygon(
        actor,
        (128, 88, 65),
        (
            (10, 7),
            (12, 6),
            (16, 6),
            (18, 8),
            (17, 12),
            (15, 13),
            (11, 12),
            (9, 10),
        ),
    )
    pygame.draw.rect(
        actor,
        (46, 36, 33),
        (10, 9, 1, 1),
    )
    pygame.draw.rect(
        actor,
        (72, 49, 41),
        (14, 8, 1, 1),
    )
    pygame.draw.line(
        actor,
        (154, 103, 75),
        (10, 10),
        (8, 11),
    )
    pygame.draw.line(
        actor,
        (83, 51, 42),
        (11, 13),
        (15, 13),
    )

    pygame.draw.polygon(
        actor,
        (112, 113, 110),
        (
            (9, 7),
            (10, 5),
            (12, 3),
            (15, 3),
            (18, 4),
            (20, 6),
            (18, 7),
            (16, 6),
            (13, 6),
            (11, 8),
        ),
    )
    pygame.draw.line(
        actor,
        (166, 166, 160),
        (12, 4),
        (15, 4),
    )
    pygame.draw.line(
        actor,
        (139, 139, 135),
        (17, 5),
        (19, 6),
    )

    pygame.draw.polygon(
        actor,
        (82, 81, 78),
        (
            (10, 12),
            (12, 12),
            (14, 13),
            (16, 12),
            (18, 13),
            (17, 16),
            (14, 18),
            (11, 16),
        ),
    )
    pygame.draw.polygon(
        actor,
        (135, 134, 129),
        (
            (12, 13),
            (14, 14),
            (16, 13),
            (17, 14),
            (16, 16),
            (14, 17),
            (12, 16),
        ),
    )

    actor.fill((0, 0, 0, 0))

    pygame.draw.ellipse(
        actor,
        (5, 6, 8, 150),
        (4, 31, 23, 4),
    )

    pygame.draw.line(
        actor,
        (25, 24, 25),
        (12, 26),
        (10, 32),
        5,
    )
    pygame.draw.line(
        actor,
        (20, 20, 21),
        (18, 26),
        (20, 32),
        5,
    )
    pygame.draw.line(
        actor,
        (63, 52, 44),
        (8, 33),
        (13, 33),
        3,
    )
    pygame.draw.line(
        actor,
        (53, 46, 42),
        (18, 33),
        (23, 33),
        3,
    )

    pygame.draw.polygon(
        actor,
        (20, 21, 23),
        (
            (8, 14),
            (12, 12),
            (19, 12),
            (23, 15),
            (24, 25),
            (21, 31),
            (16, 30),
            (11, 32),
            (6, 28),
            (6, 19),
        ),
    )
    pygame.draw.polygon(
        actor,
        (48, 45, 44),
        (
            (9, 15),
            (12, 13),
            (18, 13),
            (21, 16),
            (21, 27),
            (17, 29),
            (13, 28),
            (9, 30),
            (8, 25),
        ),
    )
    pygame.draw.polygon(
        actor,
        (64, 58, 53),
        (
            (9, 16),
            (12, 14),
            (14, 14),
            (13, 28),
            (10, 29),
            (8, 25),
        ),
    )
    pygame.draw.line(
        actor,
        (31, 29, 29),
        (15, 14),
        (15, 29),
        2,
    )
    pygame.draw.line(
        actor,
        (79, 68, 56),
        (20, 14),
        (15, 29),
        3,
    )
    pygame.draw.line(
        actor,
        (122, 83, 49),
        (20, 14),
        (15, 28),
    )

    pygame.draw.line(
        actor,
        (25, 25, 27),
        (20, 16),
        (23, 24),
        4,
    )
    pygame.draw.line(
        actor,
        (63, 57, 52),
        (20, 16),
        (23, 24),
        2,
    )
    pygame.draw.circle(
        actor,
        (113, 81, 63),
        (23, 25),
        2,
    )

    pygame.draw.line(
        actor,
        (23, 23, 25),
        (9, 16),
        (7, 24),
        4,
    )
    pygame.draw.line(
        actor,
        (61, 55, 50),
        (9, 16),
        (7, 24),
        2,
    )
    pygame.draw.circle(
        actor,
        (117, 83, 64),
        (7, 25),
        2,
    )

    pygame.draw.rect(
        actor,
        (79, 55, 45),
        (13, 11, 5, 4),
    )

    pygame.draw.polygon(
        actor,
        (82, 56, 46),
        (
            (10, 6),
            (13, 4),
            (18, 5),
            (20, 7),
            (19, 12),
            (16, 14),
            (12, 13),
            (10, 11),
            (8, 10),
            (8, 8),
        ),
    )
    pygame.draw.polygon(
        actor,
        (132, 91, 67),
        (
            (11, 7),
            (13, 5),
            (17, 6),
            (19, 8),
            (18, 11),
            (16, 13),
            (12, 12),
            (10, 10),
        ),
    )

    pygame.draw.rect(
        actor,
        (44, 35, 32),
        (11, 8, 1, 1),
    )
    pygame.draw.rect(
        actor,
        (76, 52, 43),
        (15, 8, 1, 1),
    )
    pygame.draw.line(
        actor,
        (157, 107, 78),
        (10, 9),
        (8, 10),
    )
    pygame.draw.line(
        actor,
        (91, 57, 45),
        (11, 12),
        (16, 12),
    )

    pygame.draw.polygon(
        actor,
        (105, 106, 105),
        (
            (9, 7),
            (10, 5),
            (12, 3),
            (16, 3),
            (19, 4),
            (21, 6),
            (19, 7),
            (17, 6),
            (14, 5),
            (12, 6),
            (10, 8),
        ),
    )
    pygame.draw.line(
        actor,
        (163, 163, 158),
        (12, 4),
        (16, 4),
    )
    pygame.draw.line(
        actor,
        (136, 137, 134),
        (18, 5),
        (20, 6),
    )

    pygame.draw.polygon(
        actor,
        (79, 79, 77),
        (
            (10, 12),
            (12, 12),
            (14, 13),
            (16, 12),
            (18, 13),
            (17, 16),
            (14, 18),
            (11, 16),
        ),
    )
    pygame.draw.polygon(
        actor,
        (137, 137, 132),
        (
            (12, 13),
            (14, 14),
            (16, 13),
            (17, 14),
            (16, 16),
            (14, 17),
            (12, 16),
        ),
    )

    actor.set_alpha(round(255 * opacity))

    offer_pose = _elder_offer_pose(elapsed)
    elder_x = center_x - round(offer_pose * 10)
    elder_y = center_y + round(offer_pose * 4)

    screen.blit(
        actor,
        (
            elder_x - actor.get_width() // 2,
            elder_y - 18,
        ),
    )

    _draw_elder_knife_offer(
        screen,
        center_x,
        center_y,
        elapsed,
    )


def draw_act_one_intro_world(
    screen,
    state,
):
    if state is None:
        return

    center_x = (
        MAP_OFFSET_X
        + state.column * TILE_SIZE
        + TILE_SIZE // 2
    )
    center_y = (
        MAP_OFFSET_Y
        + state.row * TILE_SIZE
        + TILE_SIZE // 2
    )
    chains_broken = (
        state.finished
        or state.elapsed >= CHAIN_BREAK_MS
    )

    if chains_broken:
        _draw_broken_chains(
            screen,
            center_x,
            center_y,
        )
        _draw_chain_break(
            screen,
            center_x,
            center_y,
            state.elapsed,
        )
    else:
        left_anchor = (
            center_x - 14,
            center_y - 27,
        )
        right_anchor = (
            center_x + 14,
            center_y - 27,
        )
        left_wrist = (
            center_x - 7,
            center_y + 1,
        )
        right_wrist = (
            center_x + 7,
            center_y + 1,
        )

        _draw_wall_anchor(
            screen,
            left_anchor,
        )
        _draw_wall_anchor(
            screen,
            right_anchor,
        )
        _draw_chain(
            screen,
            left_anchor,
            left_wrist,
        )
        _draw_chain(
            screen,
            right_anchor,
            right_wrist,
        )

    _draw_intro_knife(
        screen,
        center_x,
        center_y,
        state.elapsed,
    )

    if state.finished:
        return

    _draw_elder(
        screen,
        center_x + TILE_SIZE,
        center_y,
        state.elapsed,
    )


@lru_cache(maxsize=4)
def _cinematic_shade(size):
    width, height = size
    shade = pygame.Surface(
        size,
        pygame.SRCALPHA,
    )
    shade.fill((0, 1, 4, 34))

    pygame.draw.rect(
        shade,
        (0, 0, 2, 220),
        (0, 0, width, 52),
    )
    pygame.draw.rect(
        shade,
        (0, 0, 2, 220),
        (0, height - 52, width, 52),
    )

    for index in range(6):
        alpha = 72 - index * 10
        inset = 52 + index * 10
        pygame.draw.rect(
            shade,
            (0, 1, 4, alpha),
            (
                0,
                inset,
                width,
                height - inset * 2,
            ),
            width=9,
        )

    return shade


def _draw_dialogue(
    screen,
    state,
    title_font,
    text_font,
):
    active_line = next(
        (
            (start, end, line)
            for start, end, line in DIALOGUE
            if start <= state.elapsed < end
        ),
        None,
    )

    if active_line is None:
        return

    start, end, line = active_line
    fade_in = _progress(
        state.elapsed,
        start,
        start + 320,
    )
    fade_out = 1.0 - _progress(
        state.elapsed,
        end - 320,
        end,
    )
    opacity = fade_in * fade_out
    visible_characters = max(
        0,
        (state.elapsed - start) // 72,
    )
    visible_line = line[:visible_characters]

    panel = pygame.Surface(
        (620, 82),
        pygame.SRCALPHA,
    )
    pygame.draw.rect(
        panel,
        (3, 5, 9, round(154 * opacity)),
        panel.get_rect(),
        border_radius=3,
    )
    pygame.draw.line(
        panel,
        (65, 70, 76, round(150 * opacity)),
        (42, 1),
        (panel.get_width() - 42, 1),
    )
    pygame.draw.line(
        panel,
        (29, 33, 39, round(130 * opacity)),
        (72, panel.get_height() - 1),
        (panel.get_width() - 72, panel.get_height() - 1),
    )

    title = title_font.render(
        "THE OLD MAN",
        True,
        (104, 108, 112),
    )
    text = text_font.render(
        visible_line,
        True,
        (187, 191, 194),
    )
    title.set_alpha(round(255 * opacity))
    text.set_alpha(round(255 * opacity))

    panel.blit(
        title,
        title.get_rect(
            midtop=(panel.get_width() // 2, 9),
        ),
    )
    panel.blit(
        text,
        text.get_rect(
            center=(panel.get_width() // 2, 55),
        ),
    )

    screen.blit(
        panel,
        panel.get_rect(
            midbottom=(
                screen.get_width() // 2,
                screen.get_height() - 57,
            ),
        ),
    )


def _draw_skip_hint(
    screen,
    state,
    text_font,
):
    progress = min(
        1.0,
        state.skip_held_ms / SKIP_HOLD_MS,
    )
    panel = pygame.Surface(
        (242, 42),
        pygame.SRCALPHA,
    )

    pygame.draw.rect(
        panel,
        (5, 6, 9, 185),
        panel.get_rect(),
        border_radius=4,
    )
    pygame.draw.rect(
        panel,
        (54, 55, 59, 210),
        (12, 31, 218, 3),
    )

    if progress > 0:
        pygame.draw.rect(
            panel,
            (157, 163, 166, 235),
            (
                12,
                31,
                round(218 * progress),
                3,
            ),
        )

    label = text_font.render(
        "HOLD SPACE TO SKIP",
        True,
        (173, 174, 176),
    )
    panel.blit(
        label,
        label.get_rect(
            center=(121, 17),
        ),
    )

    screen.blit(
        panel,
        panel.get_rect(
            bottomright=(
                screen.get_width() - 20,
                screen.get_height() - 48,
            ),
        ),
    )


def draw_act_one_intro_overlay(
    screen,
    state,
    title_font,
    text_font,
):
    if state is None or state.finished:
        return

    screen.blit(
        _cinematic_shade(screen.get_size()),
        (0, 0),
    )
    _draw_dialogue(
        screen,
        state,
        title_font,
        text_font,
    )
    _draw_skip_hint(
        screen,
        state,
        text_font,
    )


__all__ = [
    "ActOneIntroState",
    "act_one_intro_active",
    "act_one_intro_camera_offset",
    "act_one_intro_head_lift",
    "act_one_intro_hud_opacity",
    "act_one_intro_knife_pickup",
    "act_one_intro_player_has_knife",
    "draw_act_one_intro_overlay",
    "draw_act_one_intro_world",
    "update_act_one_intro",
]