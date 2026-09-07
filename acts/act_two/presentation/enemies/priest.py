import math

import pygame

from acts.act_two.presentation.enemy_effects import (
    ACT_TWO_CLASS_EFFECT_COLORS,
    ACT_TWO_HIT_FEEDBACK_MS,
    ACT_TWO_HIT_REACTION_MS,
    act_two_hit_offset as _act_two_hit_offset,
    draw_act_two_damage_number as _draw_act_two_damage_number,
)
from game.events import GameEventType
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

PRIEST_REBIRTH_DURATION_MS = 1100
PRIEST_REBIRTH_SOUND_FILES = (
    "priest_rebirth_01.mp3",
    "priest_rebirth_02.mp3",
)
PRIEST_REBIRTH_SOUND_VOLUME = 0.88

def _is_priest_rebirth_event(event):
    return (
            event.type is GameEventType.ENVIRONMENT
            and event.data.get("kind") == "enemy_death_spawn"
            and event.data.get("source_enemy_type") == "priest"
            and event.data.get("enemy_type") == "priest_ghost"
    )

def priest_rebirth_sound_key(event):
    if _is_priest_rebirth_event(event):
        return "priest_rebirth"
    return None

def record_priest_rebirth_feedback(game_state, started_at):
    enemies_by_name = {
        enemy.name: enemy
        for enemy in game_state.floor.enemies
    }
    for event in game_state.events:
        if not _is_priest_rebirth_event(event):
            continue

        priest = enemies_by_name.get(event.target)
        if priest is not None:
            priest.act_two_presentation.corpse_consumed = True

        ghost = enemies_by_name.get(event.actor)
        if ghost is None:
            continue

        presentation = ghost.act_two_presentation
        if presentation.priest_rebirth_started_at < 0:
            presentation.priest_rebirth_started_at = started_at

def draw_priest_rebirth_effect(
        screen,
        enemy,
        sprites,
        position,
        current_time,
):
    started_at = (
        enemy.act_two_presentation.priest_rebirth_started_at
    )
    elapsed = current_time - started_at
    if (
            started_at < 0
            or not 0 <= elapsed < PRIEST_REBIRTH_DURATION_MS
    ):
        return

    progress = elapsed / PRIEST_REBIRTH_DURATION_MS
    visibility = min(1.0, (1.0 - progress) * 2.8)
    eruption = min(1.0, progress / 0.3)
    center = (
        round(position[0] + TILE_SIZE / 2),
        round(position[1] + TILE_SIZE / 2),
    )
    size = TILE_SIZE * 4
    local_center = size // 2
    effect = pygame.Surface((size, size), pygame.SRCALPHA)

    radius = round(TILE_SIZE * (0.34 + eruption * 0.76))
    pygame.draw.circle(
        effect,
        (3, 13, 8, round(175 * visibility)),
        (local_center, local_center),
        radius,
    )
    pygame.draw.circle(
        effect,
        (24, 91, 40, round(150 * visibility)),
        (local_center, local_center),
        max(1, radius - 5),
        width=5,
    )
    pygame.draw.circle(
        effect,
        (111, 242, 99, round(220 * visibility)),
        (local_center, local_center),
        radius,
        width=2,
    )

    seal_radius = TILE_SIZE * (0.42 + eruption * 0.18)
    rotation = -math.pi / 2 + progress * 1.8
    vertices = [
        (
            round(
                local_center
                + math.cos(rotation + index * math.tau / 5)
                * seal_radius
            ),
            round(
                local_center
                + math.sin(rotation + index * math.tau / 5)
                * seal_radius
            ),
        )
        for index in range(5)
    ]
    pygame.draw.lines(
        effect,
        (81, 208, 74, round(185 * visibility)),
        True,
        [vertices[index] for index in (0, 2, 4, 1, 3)],
        2,
    )

    for index in range(12):
        angle = (
                index * math.tau / 12
                + progress * 3.4
                + enemy.column * 0.17
        )
        distance = TILE_SIZE * (
                0.2 + eruption * 0.42 + (index % 3) * 0.08
        )
        lift = progress * TILE_SIZE * (
                0.7 + (index % 4) * 0.16
        )
        x = local_center + math.cos(angle) * distance
        y = (
                local_center
                + math.sin(angle) * distance * 0.5
                - lift
        )
        points = [
            (
                round(
                    x
                    + math.sin(angle + segment * 0.7)
                    * (2 + segment)
                ),
                round(y + segment * TILE_SIZE * 0.075),
            )
            for segment in range(5)
        ]
        pygame.draw.lines(
            effect,
            (8, 39, 19, round(205 * visibility)),
            False,
            points,
            7,
        )
        pygame.draw.lines(
            effect,
            (58, 174, 67, round(200 * visibility)),
            False,
            points,
            3,
        )
        pygame.draw.circle(
            effect,
            (172, 255, 128, round(235 * visibility)),
            points[0],
            2,
        )

    screen.blit(
        effect,
        (
            center[0] - local_center,
            center[1] - local_center,
        ),
    )

    body_fade = max(0.0, 1.0 - elapsed / 240)
    if body_fade > 0:
        old_body = sprites["priest_idle"].copy()
        old_body.fill(
            (31, 101, 39, 255),
            special_flags=pygame.BLEND_RGBA_MULT,
        )
        old_body.set_alpha(round(230 * body_fade))
        screen.blit(old_body, position)

    flash_strength = max(0.0, 1.0 - progress / 0.52)
    ghost_sprite = sprites["priest_ghost_idle"]
    if flash_strength > 0:
        flash = ghost_sprite.copy()
        flash.fill(
            (98, 226, 75, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        flash.set_alpha(round(235 * flash_strength))
        screen.blit(flash, position)

    for direction in (-1, 1):
        echo = ghost_sprite.copy()
        echo.fill(
            (59, 185, 82, 255),
            special_flags=pygame.BLEND_RGBA_MULT,
        )
        echo.set_alpha(round(75 * visibility * (1.0 - progress)))
        screen.blit(
            echo,
            (
                round(
                    position[0]
                    + direction * TILE_SIZE * progress * 0.48
                ),
                round(position[1] - TILE_SIZE * progress * 0.3),
            ),
        )
