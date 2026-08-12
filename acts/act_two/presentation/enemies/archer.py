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


def _draw_act_two_archer_hit_feedback(
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
    offset_x = round(offset_x * 1.45)
    offset_y = round(offset_y * 1.45)
    center = (
        position[0] + TILE_SIZE // 2 + offset_x,
        position[1] + TILE_SIZE // 2 + offset_y,
    )
    origin = enemy.get("hit_origin")
    rotation_direction = 1
    if origin is not None and origin[0] > enemy["column"]:
        rotation_direction = -1
    angle = rotation_direction * reaction * (
        17 if enemy.get("hit_critical", False) else 11
    )
    reacted_sprite = pygame.transform.rotozoom(sprite, angle, 1)
    sprite_position = reacted_sprite.get_rect(center=center)
    pygame.draw.ellipse(
        screen,
        (5, 6, 9),
        (center[0] - 10, position[1] + TILE_SIZE - 7, 20, 6),
    )
    screen.blit(reacted_sprite, sprite_position)

    if elapsed < ACT_TWO_HIT_REACTION_MS:
        flash = reacted_sprite.copy()
        flash.fill(
            (229, 220, 196, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        flash.set_alpha(round(210 * (1 - reaction_progress)))
        screen.blit(flash, sprite_position)

        effect_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
            enemy.get("hit_attacker_class"),
            (176, 118, 58),
        )
        debris = pygame.Surface((64, 64), pygame.SRCALPHA)
        debris_center = 32
        visibility = 1 - reaction_progress
        debris_count = 8 if enemy.get("hit_critical", False) else 5
        for debris_index in range(debris_count):
            angle_radians = (
                debris_index * math.tau / debris_count
                + enemy["row"] * 0.37
            )
            distance = 5 + reaction_progress * 20
            debris_start = (
                round(debris_center + math.cos(angle_radians) * distance),
                round(debris_center + math.sin(angle_radians) * distance),
            )
            debris_end = (
                round(debris_start[0] + math.cos(angle_radians) * 5),
                round(debris_start[1] + math.sin(angle_radians) * 5),
            )
            color = (
                (*effect_color, round(225 * visibility))
                if debris_index % 2 == 0
                else (171, 126, 67, round(210 * visibility))
            )
            pygame.draw.line(
                debris,
                color,
                debris_start,
                debris_end,
                2 if debris_index % 3 == 0 else 1,
            )
        screen.blit(
            debris,
            (center[0] - debris_center, center[1] - debris_center),
        )

    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )
