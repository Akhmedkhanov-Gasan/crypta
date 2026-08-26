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


def _draw_act_two_priest_hit_feedback(
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
    offset_x = round(offset_x * 0.42)
    offset_y = round(offset_y * 0.42 - reaction * 2)
    center = (
        position[0] + TILE_SIZE // 2 + offset_x,
        position[1] + TILE_SIZE // 2 + offset_y,
    )
    origin = enemy.get("hit_origin")
    rotation_direction = -1
    if origin is not None and origin[0] > enemy["column"]:
        rotation_direction = 1
    reacted_sprite = pygame.transform.rotozoom(
        sprite,
        rotation_direction * reaction * 4,
        1 + reaction * 0.025,
    )
    sprite_position = reacted_sprite.get_rect(center=center)
    if enemy.type != "priest_ghost":
        pygame.draw.ellipse(
            screen,
            (3, 7, 7),
            (
                center[0] - 10,
                position[1] + TILE_SIZE - 6,
                20,
                5,
            ),
        )

    screen.blit(reacted_sprite, sprite_position)

    if elapsed < ACT_TWO_HIT_REACTION_MS:
        visibility = 1 - reaction_progress
        flash = reacted_sprite.copy()
        flash.fill((117, 229, 173, 0), special_flags=pygame.BLEND_RGBA_ADD)
        flash.set_alpha(round(205 * visibility))
        screen.blit(flash, sprite_position)

        aura = pygame.Surface((84, 84), pygame.SRCALPHA)
        aura_center = 42
        aura_color = (75, 208, 143)
        class_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
            enemy.get("hit_attacker_class"),
            (189, 234, 204),
        )
        radius = round(17 + reaction_progress * 13)
        for arc_index in range(5):
            start = (
                arc_index * math.tau / 5
                + enemy["row"] * 0.17
                + reaction_progress * 0.35
            )
            pygame.draw.arc(
                aura,
                (*aura_color, round(205 * visibility)),
                (
                    aura_center - radius,
                    aura_center - radius,
                    radius * 2,
                    radius * 2,
                ),
                start,
                start + 0.55,
                2,
            )
        for mote_index in range(10):
            angle = mote_index * math.tau / 10 + enemy["column"] * 0.31
            distance = 10 + reaction_progress * (13 + mote_index % 3 * 3)
            mote = (
                round(aura_center + math.cos(angle) * distance),
                round(aura_center + math.sin(angle) * distance),
            )
            color = class_color if mote_index % 4 == 0 else aura_color
            pygame.draw.circle(
                aura,
                (*color, round(225 * visibility)),
                mote,
                2 if mote_index % 3 == 0 else 1,
            )
        screen.blit(aura, (center[0] - aura_center, center[1] - aura_center))

    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )
