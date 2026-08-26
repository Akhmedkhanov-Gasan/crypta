import math

import pygame

from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


ACT_TWO_HIT_FEEDBACK_MS = 650
ACT_TWO_HIT_REACTION_MS = 230
ACT_TWO_DEATH_IMPACT_MS = 150
ACT_TWO_DEATH_SETTLE_MS = 430
ACT_TWO_DEATH_BURST_MS = 360
ACT_TWO_CLASS_EFFECT_COLORS = {
    "warrior": (218, 76, 54),
    "rogue": (161, 73, 202),
    "mage": (61, 146, 216),
}

def draw_act_two_dodge_feedback(
    screen,
    enemy,
    sprite,
    position,
    current_time,
    damage_font,
) -> bool:
    started_at = enemy.get("hit_animation_started_at", -1)
    elapsed = current_time - started_at

    if (
        not enemy.get("hit_dodged", False)
        or started_at < 0
        or not 0 <= elapsed < ACT_TWO_HIT_FEEDBACK_MS
    ):
        return False

    screen.blit(sprite, position)

    if damage_font is None:
        return True

    progress = elapsed / ACT_TWO_HIT_FEEDBACK_MS
    alpha = round(255 * min(1, (1 - progress) * 2.4))
    color = (102, 226, 237)

    label = damage_font.render("DODGE", True, color)
    label.set_alpha(alpha)
    shadow = damage_font.render("DODGE", True, (6, 16, 20))
    shadow.set_alpha(alpha)

    rectangle = label.get_rect(
        midbottom=(
            position[0] + TILE_SIZE // 2,
            position[1] - 6 - round(progress * 14),
        )
    )
    screen.blit(shadow, rectangle.move(1, 2))
    screen.blit(label, rectangle)
    return True


def act_two_hit_offset(enemy, elapsed):
    if elapsed >= ACT_TWO_HIT_REACTION_MS:
        return (0, 0)
    origin = enemy.get("hit_origin")
    direction_x = 0
    direction_y = -1
    if origin is not None:
        direction_x = enemy["column"] - origin[0]
        direction_y = enemy["row"] - origin[1]
        direction_length = max(1, math.hypot(direction_x, direction_y))
        direction_x /= direction_length
        direction_y /= direction_length
    progress = elapsed / ACT_TWO_HIT_REACTION_MS
    recoil = math.sin(math.pi * progress)
    distance = 8 if enemy.get("hit_critical", False) else 5
    return (
        round(direction_x * distance * recoil),
        round(direction_y * distance * recoil),
    )


def draw_act_two_damage_number(
    screen,
    enemy,
    current_time,
    damage_font,
):
    started_at = enemy.get("hit_animation_started_at", -1)
    elapsed = current_time - started_at
    if (
        damage_font is None
        or started_at < 0
        or enemy.get("hit_blocked", False)
        or not 0 <= elapsed < ACT_TWO_HIT_FEEDBACK_MS
    ):
        return
    progress = elapsed / ACT_TWO_HIT_FEEDBACK_MS
    alpha = round(255 * min(1, (1 - progress) * 2.4))
    critical = enemy.get("hit_critical", False)
    text = (
        f"{enemy.get('hit_damage', 0)}!"
        if critical
        else str(enemy.get("hit_damage", 0))
    )
    color = (255, 213, 91) if critical else (241, 233, 218)
    number = damage_font.render(text, True, color)
    number.set_alpha(alpha)
    shadow = damage_font.render(text, True, (13, 8, 11))
    shadow.set_alpha(alpha)
    center_x = (
        MAP_OFFSET_X
        + enemy["column"] * TILE_SIZE
        + TILE_SIZE // 2
    )
    top = (
        MAP_OFFSET_Y
        + enemy["row"] * TILE_SIZE
        - 7
        - round(progress * 14)
    )
    rectangle = number.get_rect(midbottom=(center_x, top))
    screen.blit(shadow, rectangle.move(1, 2))
    screen.blit(number, rectangle)


def draw_act_two_enemy_death(
    screen,
    enemy,
    standing_sprite,
    corpse_sprite,
    current_time,
    damage_font,
):
    started_at = enemy.get("death_animation_started_at", -1)
    elapsed = (
        max(0, current_time - started_at)
        if started_at >= 0
        else ACT_TWO_DEATH_SETTLE_MS
    )
    tile_position = (
        MAP_OFFSET_X + enemy["column"] * TILE_SIZE,
        MAP_OFFSET_Y + enemy["row"] * TILE_SIZE,
    )
    center = (
        tile_position[0] + TILE_SIZE // 2,
        tile_position[1] + TILE_SIZE // 2,
    )

    if elapsed < ACT_TWO_DEATH_IMPACT_MS:
        progress = elapsed / ACT_TWO_DEATH_IMPACT_MS
        recoil_x, recoil_y = act_two_hit_offset(enemy, elapsed)
        body_height = max(
            22,
            round(TILE_SIZE * (1 - progress * 0.18)),
        )
        body = pygame.transform.scale(
            standing_sprite,
            (TILE_SIZE, body_height),
        )
        body_position = body.get_rect(
            midbottom=(
                center[0] + recoil_x,
                tile_position[1] + TILE_SIZE - 2 + recoil_y,
            )
        )
        screen.blit(body, body_position)
        flash = body.copy()
        flash.fill(
            (235, 224, 207, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        flash.set_alpha(round(205 * (1 - progress)))
        screen.blit(flash, body_position)
    else:
        settle_progress = min(
            1,
            (elapsed - ACT_TWO_DEATH_IMPACT_MS)
            / (ACT_TWO_DEATH_SETTLE_MS - ACT_TWO_DEATH_IMPACT_MS),
        )
        lift = round((1 - settle_progress) * 5)
        if enemy.type != "priest_ghost":
            shadow = pygame.Surface((28, 7), pygame.SRCALPHA)
            pygame.draw.ellipse(
                shadow,
                (5, 6, 8, round(105 + settle_progress * 45)),
                shadow.get_rect(),
            )
            screen.blit(
                shadow,
                (
                    center[0] - 14,
                    tile_position[1] + TILE_SIZE - 8,
                ),
            )

        screen.blit(
            corpse_sprite,
            (tile_position[0], tile_position[1] - lift),
        )

    if elapsed < ACT_TWO_DEATH_BURST_MS:
        burst_progress = elapsed / ACT_TWO_DEATH_BURST_MS
        visibility = 1 - burst_progress
        effect_color = ACT_TWO_CLASS_EFFECT_COLORS.get(
            enemy.get("hit_attacker_class"),
            (157, 74, 61),
        )
        burst = pygame.Surface(
            (TILE_SIZE * 2, TILE_SIZE * 2),
            pygame.SRCALPHA,
        )
        burst_center = TILE_SIZE
        pygame.draw.circle(
            burst,
            (*effect_color, round(135 * visibility)),
            (burst_center, burst_center + 5),
            round(5 + burst_progress * 14),
            width=2,
        )
        for particle_index in range(6):
            angle = (
                particle_index * math.tau / 6
                + enemy["column"] * 0.31
                + enemy["row"] * 0.19
            )
            distance = 5 + burst_progress * 17
            particle_position = (
                round(burst_center + math.cos(angle) * distance),
                round(
                    burst_center
                    + 5
                    + math.sin(angle) * distance * 0.5
                ),
            )
            pygame.draw.circle(
                burst,
                (*effect_color, round(210 * visibility)),
                particle_position,
                2 if particle_index % 2 == 0 else 1,
            )
        screen.blit(
            burst,
            (center[0] - burst_center, center[1] - burst_center),
        )

    draw_act_two_damage_number(
        screen,
        enemy,
        current_time,
        damage_font,
    )
