import math

import pygame

from acts.act_three.abilities.summoner import (
    summoner_familiar_summon_targets,
)
from acts.act_three.presentation.summoner.familiar import (
    SUMMONER_FAMILIAR_SUMMON_DURATION_MS,
)
from acts.act_three.presentation.summoner.true_form_effects import (
    _draw_smoke_blob,
)
from acts.act_three.presentation.view import _view_position
from presentation.layout import ACT_THREE_TILE_SIZE


def draw_summoner_familiar_summon_targeting(
    surface,
    game_state,
    camera_x,
    camera_y,
    current_time,
):
    player = game_state.player
    if not player.summoner_familiar_summon_aiming:
        return

    selected_target = (
        player.summoner_familiar_summon_target
    )
    pulse = 0.5 + 0.5 * math.sin(current_time / 190)

    for target in summoner_familiar_summon_targets(
        game_state
    ):
        marker = pygame.Surface(
            (
                ACT_THREE_TILE_SIZE,
                ACT_THREE_TILE_SIZE,
            ),
            pygame.SRCALPHA,
        )
        center = (
            ACT_THREE_TILE_SIZE // 2,
            ACT_THREE_TILE_SIZE // 2,
        )
        selected = target == selected_target
        radius_x = 22 if selected else 17
        radius_y = 13 if selected else 10

        pygame.draw.ellipse(
            marker,
            (
                21,
                123,
                127,
                round(
                    (62 if selected else 30)
                    + pulse * (38 if selected else 18)
                ),
            ),
            (
                center[0] - radius_x,
                center[1] - radius_y,
                radius_x * 2,
                radius_y * 2,
            ),
        )

        phase = current_time / 520
        for arc_index in range(3):
            arc_radius_x = radius_x + arc_index * 3
            arc_radius_y = radius_y + arc_index * 2
            arc_start = (
                phase
                + arc_index * math.tau / 3
            )
            pygame.draw.arc(
                marker,
                (
                    91 + arc_index * 18,
                    226,
                    211,
                    175 if selected else 90,
                ),
                (
                    center[0] - arc_radius_x,
                    center[1] - arc_radius_y,
                    arc_radius_x * 2,
                    arc_radius_y * 2,
                ),
                arc_start,
                arc_start + 1.55,
                2 if selected else 1,
            )

        if selected:
            for mote_index in range(8):
                angle = (
                    phase * 1.7
                    + mote_index * math.tau / 8
                )
                pygame.draw.circle(
                    marker,
                    (
                        135,
                        244,
                        228,
                        round(130 + pulse * 80),
                    ),
                    (
                        center[0]
                        + round(math.cos(angle) * 23),
                        center[1]
                        + round(math.sin(angle) * 13),
                    ),
                    2 if mote_index % 3 == 0 else 1,
                )

        position = _view_position(
            target[0],
            target[1],
            camera_x,
            camera_y,
        )
        surface.blit(marker, position)


def draw_summoner_familiar_summon_effect(
    surface,
    position,
    current_time,
    started_at,
):
    elapsed = current_time - started_at
    if not (
        0
        <= elapsed
        < SUMMONER_FAMILIAR_SUMMON_DURATION_MS
    ):
        return

    progress = (
        elapsed / SUMMONER_FAMILIAR_SUMMON_DURATION_MS
    )
    visibility = math.sin(math.pi * progress) ** 0.55
    margin = 42
    size = ACT_THREE_TILE_SIZE + margin * 2
    effect_surface = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )
    center = (
        margin + ACT_THREE_TILE_SIZE // 2,
        margin + ACT_THREE_TILE_SIZE // 2 + 5,
    )
    phase = current_time / 150

    pygame.draw.ellipse(
        effect_surface,
        (
            24,
            143,
            145,
            round(75 * visibility),
        ),
        (
            center[0] - 27,
            center[1] + 12,
            54,
            18,
        ),
    )

    for ring_index in range(3):
        radius_x = 23 + ring_index * 5
        radius_y = 9 + ring_index * 3
        ring_start = (
            phase * (0.35 + ring_index * 0.12)
            + ring_index * 2.1
        )
        pygame.draw.arc(
            effect_surface,
            (
                67 + ring_index * 23,
                225,
                211,
                round(
                    (150 - ring_index * 25)
                    * visibility
                ),
            ),
            (
                center[0] - radius_x,
                center[1] + 10 - radius_y,
                radius_x * 2,
                radius_y * 2,
            ),
            ring_start,
            ring_start + 2.15,
            2,
        )

    for smoke_index in range(18):
        angle = (
            smoke_index * 2.399
            + phase * 0.18
        )
        distance = (
            7
            + (1 - progress)
            * (20 + smoke_index % 5 * 4)
        )
        smoke_center = (
            center[0]
            + round(math.cos(angle) * distance),
            center[1]
            + round(
                math.sin(angle)
                * distance
                * 0.72
            ),
        )
        color = (
            (31, 184, 179)
            if smoke_index % 3
            else (105, 56, 148)
        )
        _draw_smoke_blob(
            effect_surface,
            smoke_center,
            4 + smoke_index % 5,
            color,
            round(125 * visibility),
            phase + smoke_index,
        )

    surface.blit(
        effect_surface,
        (
            position[0] - margin,
            position[1] - margin,
        ),
    )
