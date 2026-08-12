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
