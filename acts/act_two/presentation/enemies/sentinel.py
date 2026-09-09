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
from acts.act_two.presentation.enemies.timing import (
    attack_telegraph_is_visible,
)


def draw_sentinel_status(screen, enemy, position, current_time, tile_size):
    if enemy.type != "sentinel" or enemy.health <= 0:
        return

    state = enemy.sentinel
    blocks = (
        0
        if state.shield_broken
        else enemy.shield_blocks_remaining
        if state.shield_raised
        else enemy.shield_durability
    )
    center_x = position[0] + tile_size / 2
    top = round(position[1] - 9)
    hit_started_at = enemy.hit_animation_started_at
    indicators_visible = (
        hit_started_at >= 0
        and 0 <= current_time - hit_started_at < 1500
    )

    if indicators_visible:
        for index in range(2):
            left = round(center_x - 8 + index * 9)
            rectangle = pygame.Rect(left, top, 7, 4)
            filled = index < blocks
            color = (
                (87, 96, 102)
                if filled and state.recovery_turns == 0
                else (58, 64, 69)
                if filled
                else (28, 29, 32)
            )
            pygame.draw.rect(
                screen,
                (10, 11, 14),
                rectangle.inflate(2, 2),
            )
            pygame.draw.rect(screen, color, rectangle)
            if filled:
                pygame.draw.line(
                    screen,
                    (119, 124, 126),
                    (left + 1, top),
                    (left + 5, top),
                    1,
                )
            else:
                pygame.draw.line(
                    screen,
                    (86, 57, 53),
                    (left + 1, top + 3),
                    (left + 5, top),
                    1,
                )

    if (
        enemy.prepared_attack_mode != "shield_bash"
        or not attack_telegraph_is_visible(enemy, current_time)
    ):
        return

    direction = pygame.Vector2(state.bash_direction)
    if not direction.length_squared():
        return
    direction = direction.normalize()
    side = pygame.Vector2(-direction.y, direction.x)
    center = pygame.Vector2(
        position[0] + tile_size / 2,
        position[1] + tile_size / 2,
    )
    start = center + direction * tile_size * 0.18
    end = center + direction * tile_size * 0.82
    head = tile_size * 0.2
    pulse = 0.5 + 0.5 * math.sin(current_time / 90)
    color = (round(140 + pulse * 80), 230, 255)

    pygame.draw.line(screen, (8, 28, 48), start, end, 8)
    pygame.draw.line(screen, color, start, end, 4)
    pygame.draw.polygon(
        screen,
        (8, 28, 48),
        [
            end + direction * 3,
            end - direction * head + side * head * 0.8,
            end - direction * head - side * head * 0.8,
        ],
    )
    pygame.draw.polygon(
        screen,
        color,
        [
            end,
            end - direction * head + side * head * 0.55,
            end - direction * head - side * head * 0.55,
        ],
    )


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

    if not blocked:
        _draw_act_two_damage_number(
            screen,
            enemy,
            current_time,
            damage_font,
        )
