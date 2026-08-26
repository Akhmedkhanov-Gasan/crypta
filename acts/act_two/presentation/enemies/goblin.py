import math

import pygame

from acts.act_two.presentation.enemy_effects import (
    ACT_TWO_CLASS_EFFECT_COLORS,
    ACT_TWO_HIT_FEEDBACK_MS,
    ACT_TWO_HIT_REACTION_MS,
    act_two_hit_offset as _act_two_hit_offset,
    draw_act_two_damage_number as _draw_act_two_damage_number,
)
from settings import TILE_SIZE

GOBLIN_SUMMON_SPAWN_EFFECT_MS = 520

def _draw_act_two_goblin_hit_feedback(
    screen,
    enemy,
    sprite,
    position,
    current_time,
    damage_font,
):
    started_at = enemy.get("hit_animation_started_at", -1)
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < ACT_TWO_HIT_FEEDBACK_MS:
        screen.blit(sprite, position)
        return

    reaction_progress = min(1, elapsed / ACT_TWO_HIT_REACTION_MS)
    reaction = math.sin(math.pi * reaction_progress)
    offset_x, offset_y = _act_two_hit_offset(enemy, elapsed)
    center = (
        position[0] + TILE_SIZE // 2 + offset_x,
        position[1] + TILE_SIZE // 2 + offset_y,
    )
    pygame.draw.ellipse(
        screen,
        (5, 6, 9),
        (center[0] - 10, position[1] + TILE_SIZE - 7, 20, 6),
    )

    sprite_width = round(TILE_SIZE * (1 + reaction * 0.13))
    sprite_height = round(TILE_SIZE * (1 - reaction * 0.16))
    reacted_sprite = pygame.transform.scale(
        sprite,
        (sprite_width, max(20, sprite_height)),
    )
    sprite_position = reacted_sprite.get_rect(center=center)
    screen.blit(reacted_sprite, sprite_position)

    if elapsed < ACT_TWO_HIT_REACTION_MS:
        flash = reacted_sprite.copy()
        flash.fill(
            (230, 218, 198, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        flash.set_alpha(round(215 * (1 - reaction_progress)))
        screen.blit(flash, sprite_position)

        effect_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
            enemy.get("hit_attacker_class"),
            (190, 84, 67),
        )
        particle_count = 9 if enemy.get("hit_critical", False) else 6
        particle_layer = pygame.Surface(
            (TILE_SIZE * 2, TILE_SIZE * 2),
            pygame.SRCALPHA,
        )
        particle_center = TILE_SIZE
        visibility = 1 - reaction_progress
        for particle_index in range(particle_count):
            angle = (
                particle_index * math.tau / particle_count
                + enemy["column"] * 0.47
                + enemy["row"] * 0.31
            )
            distance = 5 + reaction_progress * 18
            particle_position = (
                round(particle_center + math.cos(angle) * distance),
                round(particle_center + math.sin(angle) * distance),
            )
            pygame.draw.circle(
                particle_layer,
                (*effect_color, round(230 * visibility)),
                particle_position,
                2 if particle_index % 3 == 0 else 1,
            )
        screen.blit(
            particle_layer,
            (
                center[0] - particle_center,
                center[1] - particle_center,
            ),
        )

    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )


def draw_goblin_summon_effects(
    screen,
    enemy,
    position,
    current_time,
):
    layer_size = TILE_SIZE * 3
    layer_center = layer_size // 2
    layer_position = (
        round(
            position[0]
            + TILE_SIZE / 2
            - layer_center
        ),
        round(
            position[1]
            + TILE_SIZE / 2
            - layer_center
        ),
    )

    summon_started_at = enemy.get(
        "summon_animation_started_at",
        -1,
    )

    if (
        summon_started_at >= 0
        and enemy.behavior_state.name == "PREPARING_SUMMON"
        and current_time >= summon_started_at
    ):
        elapsed = current_time - summon_started_at
        rotation = elapsed / 700
        pulse = (math.sin(elapsed / 180) + 1) / 2

        ritual_layer = pygame.Surface(
            (layer_size, layer_size),
            pygame.SRCALPHA,
        )
        center = (layer_center, layer_center + 13)
        outer_radius = round(25 + pulse * 2)

        pygame.draw.ellipse(
            ritual_layer,
            (7, 4, 8, 150),
            (
                center[0] - 28,
                center[1] - 11,
                56,
                22,
            ),
        )

        pygame.draw.ellipse(
            ritual_layer,
            (103, 27, 35, 190),
            (
                center[0] - outer_radius,
                center[1] - outer_radius // 2,
                outer_radius * 2,
                outer_radius,
            ),
            width=2,
        )

        rune_points = []

        for rune_index in range(5):
            angle = (
                rotation
                - math.pi / 2
                + rune_index * math.tau / 5
            )
            rune_points.append(
                (
                    round(
                        center[0]
                        + math.cos(angle) * outer_radius
                    ),
                    round(
                        center[1]
                        + math.sin(angle)
                        * outer_radius
                        * 0.5
                    ),
                )
            )

        for rune_index in range(5):
            pygame.draw.line(
                ritual_layer,
                (132, 38, 44, 175),
                rune_points[rune_index],
                rune_points[(rune_index + 2) % 5],
                width=2,
            )

        for smoke_index in range(7):
            smoke_phase = (
                elapsed / 900
                + smoke_index / 7
            ) % 1
            smoke_angle = (
                smoke_index * math.tau / 7
                - rotation * 0.35
            )
            smoke_distance = 8 + smoke_phase * 22
            smoke_radius = round(5 + smoke_phase * 5)

            smoke_position = (
                round(
                    center[0]
                    + math.cos(smoke_angle)
                    * smoke_distance
                ),
                round(
                    center[1]
                    + math.sin(smoke_angle)
                    * smoke_distance
                    * 0.45
                    - smoke_phase * 25
                ),
            )

            pygame.draw.circle(
                ritual_layer,
                (
                    24,
                    13,
                    27,
                    round(150 * (1 - smoke_phase)),
                ),
                smoke_position,
                smoke_radius,
            )

        pygame.draw.circle(
            ritual_layer,
            (173, 50, 48, round(90 + pulse * 90)),
            (center[0], center[1] - 3),
            round(4 + pulse * 2),
        )

        screen.blit(ritual_layer, layer_position)

    spawn_started_at = enemy.get(
        "summon_spawn_animation_started_at",
        -1,
    )
    spawn_elapsed = current_time - spawn_started_at

    if (
        spawn_started_at >= 0
        and 0 <= spawn_elapsed < GOBLIN_SUMMON_SPAWN_EFFECT_MS
    ):
        progress = (
            spawn_elapsed
            / GOBLIN_SUMMON_SPAWN_EFFECT_MS
        )
        visibility = 1 - progress

        spawn_layer = pygame.Surface(
            (layer_size, layer_size),
            pygame.SRCALPHA,
        )
        center = (layer_center, layer_center + 10)

        portal_width = round(42 * (1 - progress * 0.35))
        portal_height = round(17 * (1 - progress * 0.35))

        pygame.draw.ellipse(
            spawn_layer,
            (5, 3, 7, round(220 * visibility)),
            (
                center[0] - portal_width // 2,
                center[1] - portal_height // 2,
                portal_width,
                portal_height,
            ),
        )

        pygame.draw.ellipse(
            spawn_layer,
            (112, 29, 36, round(210 * visibility)),
            (
                center[0] - portal_width // 2,
                center[1] - portal_height // 2,
                portal_width,
                portal_height,
            ),
            width=2,
        )

        for smoke_index in range(10):
            smoke_phase = (
                progress + smoke_index / 10
            ) % 1
            horizontal_offset = math.sin(
                smoke_index * 2.1 + progress * 5
            ) * (8 + smoke_index)

            smoke_position = (
                round(center[0] + horizontal_offset),
                round(
                    center[1]
                    - smoke_phase * 42
                    + 7
                ),
            )
            smoke_radius = round(7 - smoke_phase * 3)

            pygame.draw.circle(
                spawn_layer,
                (
                    20,
                    11,
                    23,
                    round(
                        190
                        * visibility
                        * (1 - smoke_phase * 0.6)
                    ),
                ),
                smoke_position,
                max(2, smoke_radius),
            )

        screen.blit(spawn_layer, layer_position)
