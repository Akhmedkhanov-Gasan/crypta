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


def _draw_act_two_brute_hit_feedback(
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
    offset_y = round(offset_y * 0.42)
    shake = round(
        math.sin(elapsed / 17) * 2 * max(0, 1 - reaction_progress)
    )
    center = (
        position[0] + TILE_SIZE // 2 + offset_x + shake,
        position[1] + TILE_SIZE // 2 + offset_y + round(reaction * 3),
    )
    sprite_width = round(TILE_SIZE * (1 + reaction * 0.2))
    sprite_height = round(TILE_SIZE * (1 - reaction * 0.23))
    reacted_sprite = pygame.transform.scale(
        sprite,
        (sprite_width, max(20, sprite_height)),
    )
    sprite_position = reacted_sprite.get_rect(
        midbottom=(center[0], position[1] + TILE_SIZE + offset_y)
    )
    pygame.draw.ellipse(
        screen,
        (4, 5, 7),
        (
            center[0] - 13,
            position[1] + TILE_SIZE - 7,
            26,
            7,
        ),
    )
    screen.blit(reacted_sprite, sprite_position)

    if elapsed < ACT_TWO_HIT_REACTION_MS:
        flash = reacted_sprite.copy()
        flash.fill(
            (237, 211, 181, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        flash.set_alpha(round(205 * (1 - reaction_progress)))
        screen.blit(flash, sprite_position)

        effect_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
            enemy.get("hit_attacker_class"),
            (174, 91, 54),
        )
        impact = pygame.Surface((72, 40), pygame.SRCALPHA)
        impact_center = 36
        visibility = 1 - reaction_progress
        ring_width = round(10 + reaction_progress * 24)
        pygame.draw.arc(
            impact,
            (*effect_color, round(190 * visibility)),
            (
                impact_center - ring_width,
                20 - round(ring_width * 0.28),
                ring_width * 2,
                max(8, round(ring_width * 0.56)),
            ),
            math.pi,
            math.tau,
            2,
        )
        chunk_count = 8 if enemy.get("hit_critical", False) else 5
        for chunk_index in range(chunk_count):
            spread = (chunk_index / max(1, chunk_count - 1) - 0.5) * 38
            chunk_x = round(impact_center + spread * reaction_progress)
            chunk_y = round(
                22
                - math.sin(math.pi * reaction_progress)
                * (5 + chunk_index % 3 * 3)
            )
            pygame.draw.rect(
                impact,
                (118, 91, 70, round(210 * visibility)),
                (chunk_x, chunk_y, 2, 2),
            )
        screen.blit(
            impact,
            (center[0] - impact_center, position[1] + TILE_SIZE - 20),
        )

    _draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )
