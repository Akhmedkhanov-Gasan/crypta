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


def _draw_act_two_sentinel_hit_feedback(
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

    blocked = enemy.get("hit_blocked", False)
    reaction_progress = min(1, elapsed / ACT_TWO_HIT_REACTION_MS)
    reaction = math.sin(math.pi * reaction_progress)
    offset_x, offset_y = _act_two_hit_offset(enemy, elapsed)
    if blocked:
        offset_x = 0
        offset_y = 0
    else:
        offset_x = round(offset_x * 0.68)
        offset_y = round(offset_y * 0.68)
    center = (
        position[0] + TILE_SIZE // 2 + offset_x,
        position[1] + TILE_SIZE // 2 + offset_y,
    )
    origin = enemy.get("hit_origin")
    rotation_direction = 1
    if origin is not None and origin[0] > enemy["column"]:
        rotation_direction = -1
    angle = 0 if blocked else rotation_direction * reaction * 6
    reacted_sprite = pygame.transform.rotozoom(sprite, angle, 1)
    sprite_position = reacted_sprite.get_rect(center=center)
    pygame.draw.ellipse(
        screen,
        (4, 5, 7),
        (center[0] - 11, position[1] + TILE_SIZE - 7, 22, 6),
    )
    screen.blit(reacted_sprite, sprite_position)

    if elapsed < ACT_TWO_HIT_REACTION_MS:
        flash = reacted_sprite.copy()
        flash_color = (
            (232, 184, 72, 0)
            if blocked
            else (208, 220, 222, 0)
        )
        flash.fill(flash_color, special_flags=pygame.BLEND_RGBA_ADD)
        flash.set_alpha(round(220 * (1 - reaction_progress)))
        screen.blit(flash, sprite_position)

        effect = pygame.Surface((72, 72), pygame.SRCALPHA)
        effect_center = 36
        visibility = 1 - reaction_progress
        effect_color = (
            (239, 190, 73)
            if blocked
            else ACT_TWO_CLASS_EFFECT_COLORS.get(
                enemy.get("hit_attacker_class"),
                (151, 168, 172),
            )
        )
        if blocked:
            shield_radius = round(14 + reaction_progress * 13)
            pygame.draw.arc(
                effect,
                (*effect_color, round(235 * visibility)),
                (
                    effect_center - shield_radius,
                    effect_center - shield_radius,
                    shield_radius * 2,
                    shield_radius * 2,
                ),
                math.radians(-70),
                math.radians(250),
                4,
            )
        spark_count = 11 if blocked else 7
        for spark_index in range(spark_count):
            angle_radians = (
                spark_index * math.tau / spark_count
                + enemy["column"] * 0.23
            )
            inner = 7 + reaction_progress * 8
            outer = inner + 5 + reaction_progress * 9
            start = (
                round(effect_center + math.cos(angle_radians) * inner),
                round(effect_center + math.sin(angle_radians) * inner),
            )
            end = (
                round(effect_center + math.cos(angle_radians) * outer),
                round(effect_center + math.sin(angle_radians) * outer),
            )
            pygame.draw.line(
                effect,
                (*effect_color, round(225 * visibility)),
                start,
                end,
                2 if blocked or spark_index % 3 == 0 else 1,
            )
        screen.blit(
            effect,
            (center[0] - effect_center, center[1] - effect_center),
        )

    if blocked and damage_font is not None:
        progress = elapsed / ACT_TWO_HIT_FEEDBACK_MS
        alpha = round(255 * min(1, (1 - progress) * 2.3))
        block_label = (
            f"BLOCK "
            f"{enemy.shield_blocks_remaining}/"
            f"{enemy.shield_durability}"
        )
        label = damage_font.render(
            block_label,
            True,
            (183, 199, 205),
        )
        label.set_alpha(alpha)
        label_rectangle = label.get_rect(
            midbottom=(
                center[0],
                position[1] - 6 - round(progress * 12),
            )
        )
        shadow = damage_font.render(
            block_label,
            True,
            (11, 13, 16),
        )
        shadow.set_alpha(alpha)
        screen.blit(shadow, label_rectangle.move(1, 2))
        screen.blit(label, label_rectangle)
    else:
        _draw_act_two_damage_number(
            screen,
            enemy,
            current_time,
            damage_font,
        )
