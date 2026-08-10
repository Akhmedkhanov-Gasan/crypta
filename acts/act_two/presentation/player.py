import math

import pygame

from acts.act_two.presentation.movement import (
    PlayerMovementPose,
    draw_mage_movement_grounding,
    draw_rogue_movement_grounding,
    draw_warrior_movement_grounding,
    sample_mage_movement,
    sample_rogue_movement,
    sample_warrior_movement,
)
from presentation.hud import wrap_text
from presentation.layout import (
    MAP_HEIGHT,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    MAP_WIDTH,
)
from settings import TILE_SIZE


ACT_TWO_PLAYER_HIT_FEEDBACK_MS = 650
ACT_TWO_PLAYER_HIT_REACTION_MS = 230
ACT_TWO_PLAYER_HEAL_EFFECT_MS = 950
ACT_TWO_PLAYER_DEATH_HOLD_MS = 480
ACT_TWO_PLAYER_DEATH_COLLAPSE_MS = 2400
ACT_TWO_WARRIOR_DEATH_FALL_MS = 1700
ACT_TWO_ROGUE_DEATH_START_MS = 280
ACT_TWO_ROGUE_DEATH_FALL_MS = 1500
ACT_TWO_MAGE_DEATH_START_MS = 180
ACT_TWO_MAGE_DEATH_FALL_MS = 1800
ACT_TWO_OLD_MAN_APPEAR_MS = 2500
ACT_TWO_OLD_MAN_KNEEL_MS = 3700
ACT_TWO_OLD_MAN_DIALOGUE_MS = 4800
ACT_TWO_DEFEAT_MESSAGE_MS = 6900
ACT_TWO_DEFEAT_FADE_MS = 520

_CLASS_COLORS = {
    "warrior": (224, 83, 58),
    "rogue": (180, 82, 218),
    "mage": (67, 157, 224),
}
_OLD_MAN_LINES = {
    "warrior": "Strength is loud. What waits below is patient.",
    "rogue": "You can hide from beasts. Not from the road below.",
    "mage": "You touch the dark, child. You do not yet see it.",
}
_DEFEAT_TITLES = {
    "warrior": "THE BLADE FALLS",
    "rogue": "THE SHADOW BREAKS",
    "mage": "THE SPARK FADES",
}


def _smoothstep(progress):
    progress = max(0, min(1, progress))
    return progress * progress * (3 - 2 * progress)


def _player_center(column, row):
    return (
        MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2,
    )


def _hit_offset(column, row, hit_origin, elapsed):
    if elapsed >= ACT_TWO_PLAYER_HIT_REACTION_MS:
        return (0, 0)
    direction_x = 0
    direction_y = -1
    if hit_origin is not None:
        direction_x = column - hit_origin[0]
        direction_y = row - hit_origin[1]
        direction_length = max(1, math.hypot(direction_x, direction_y))
        direction_x /= direction_length
        direction_y /= direction_length
    reaction = math.sin(
        math.pi * elapsed / ACT_TWO_PLAYER_HIT_REACTION_MS
    )
    return (
        round(direction_x * 6 * reaction),
        round(direction_y * 6 * reaction),
    )


def _draw_hit_particles(surface, player_class, center, progress):
    visibility = 1 - progress
    color = _CLASS_COLORS[player_class]
    particle_count = {
        "warrior": 12,
        "rogue": 8,
        "mage": 14,
    }[player_class]
    for particle_index in range(particle_count):
        angle = (
            particle_index * math.tau / particle_count
            + {"warrior": 0.2, "rogue": 1.1, "mage": 2.0}[player_class]
        )
        distance = 8 + progress * (12 + particle_index % 4 * 3)
        position = (
            round(center[0] + math.cos(angle) * distance),
            round(center[1] + math.sin(angle) * distance),
        )
        alpha = round(220 * visibility)
        if player_class == "warrior":
            end = (
                round(position[0] + math.cos(angle) * 5),
                round(position[1] + math.sin(angle) * 5),
            )
            pygame.draw.line(surface, (*color, alpha), position, end, 2)
        elif player_class == "rogue":
            pygame.draw.circle(surface, (*color, alpha), position, 2)
        else:
            pygame.draw.polygon(
                surface,
                (*color, alpha),
                (
                    (position[0], position[1] - 3),
                    (position[0] + 2, position[1] + 2),
                    (position[0] - 2, position[1] + 1),
                ),
            )


def _draw_healing_effect(
    screen,
    center,
    player_class,
    current_time,
    effect_started_at,
):
    elapsed = current_time - effect_started_at
    if (
        effect_started_at <= 0
        or not 0 <= elapsed < ACT_TWO_PLAYER_HEAL_EFFECT_MS
    ):
        return False

    progress = elapsed / ACT_TWO_PLAYER_HEAL_EFFECT_MS
    visibility = 1 - progress
    effect = pygame.Surface((76, 80), pygame.SRCALPHA)
    effect_center = (38, 42)
    healing_color = (74, 221, 137)
    light_color = (151, 247, 185)
    class_color = _CLASS_COLORS[player_class]

    ring_progress = min(1, progress * 1.35)
    ring_width = round(22 + ring_progress * 30)
    ring_height = round(7 + ring_progress * 7)
    pygame.draw.ellipse(
        effect,
        (*healing_color, round(205 * visibility)),
        (
            effect_center[0] - ring_width // 2,
            effect_center[1] + 9 - ring_height // 2,
            ring_width,
            ring_height,
        ),
        width=2,
    )

    inner_pulse = math.sin(math.pi * min(1, progress * 1.7))
    if inner_pulse > 0:
        pygame.draw.circle(
            effect,
            (*healing_color, round(80 * inner_pulse * visibility)),
            effect_center,
            round(10 + inner_pulse * 9),
        )

    for particle_index in range(12):
        delay = particle_index * 33
        particle_elapsed = elapsed - delay
        if particle_elapsed < 0:
            continue
        particle_progress = min(1, particle_elapsed / 620)
        if particle_progress >= 1:
            continue
        phase = particle_index * 1.83
        particle_x = round(
            effect_center[0]
            + math.sin(phase + particle_progress * 1.4)
            * (8 + particle_index % 4 * 3)
        )
        particle_y = round(
            effect_center[1]
            + 15
            - particle_progress * (42 + particle_index % 3 * 5)
        )
        particle_visibility = math.sin(math.pi * particle_progress)
        color = class_color if particle_index % 5 == 0 else healing_color
        pygame.draw.rect(
            effect,
            (*color, round(235 * particle_visibility * visibility)),
            (
                particle_x,
                particle_y,
                2 if particle_index % 3 else 3,
                3,
            ),
        )

    symbol_progress = min(1, elapsed / 180)
    symbol_visibility = max(0, 1 - progress * 1.55) * symbol_progress
    symbol_y = effect_center[1] - 20 - round(progress * 7)
    symbol_alpha = round(245 * symbol_visibility)
    pygame.draw.line(
        effect,
        (*light_color, symbol_alpha),
        (effect_center[0] - 5, symbol_y),
        (effect_center[0] + 5, symbol_y),
        3,
    )
    pygame.draw.line(
        effect,
        (*light_color, symbol_alpha),
        (effect_center[0], symbol_y - 5),
        (effect_center[0], symbol_y + 5),
        3,
    )

    screen.blit(
        effect,
        (center[0] - effect_center[0], center[1] - effect_center[1]),
    )
    return True


def _draw_player_hit(
    screen,
    sprite,
    position,
    player_class,
    current_time,
    hit_started_at,
    hit_origin,
    facing_direction=(0, 1),
):
    elapsed = current_time - hit_started_at
    if hit_started_at < 0 or not 0 <= elapsed < ACT_TWO_PLAYER_HIT_FEEDBACK_MS:
        screen.blit(sprite, position)
        return False

    reaction_progress = min(1, elapsed / ACT_TWO_PLAYER_HIT_REACTION_MS)
    reaction = math.sin(math.pi * reaction_progress)
    offset_x, offset_y = _hit_offset(
        (position[0] - MAP_OFFSET_X) // TILE_SIZE,
        (position[1] - MAP_OFFSET_Y) // TILE_SIZE,
        hit_origin,
        elapsed,
    )
    center = (
        position[0] + TILE_SIZE // 2 + offset_x,
        position[1] + TILE_SIZE // 2 + offset_y,
    )
    directional_warrior_hit = (
        player_class == "warrior"
        and facing_direction != (0, 1)
    )
    if directional_warrior_hit:
        shake_direction = (
            1 if (elapsed // 38) % 2 == 0 else -1
        )
        shake = round((1 - reaction_progress) * 2) * shake_direction
        if facing_direction[0] != 0:
            center = (center[0], center[1] + shake)
        else:
            center = (center[0] + shake, center[1])
        reacted_sprite = sprite
    else:
        angle = {
            "warrior": -7,
            "rogue": 10,
            "mage": -4,
        }[player_class] * reaction
        reacted_sprite = pygame.transform.rotozoom(
            sprite,
            angle,
            1 + (0.035 if player_class == "warrior" else 0.015) * reaction,
        )
    reacted_position = reacted_sprite.get_rect(center=center)

    if player_class == "rogue" and reaction_progress < 1:
        echo = reacted_sprite.copy()
        echo.fill((89, 32, 112, 0), special_flags=pygame.BLEND_RGBA_ADD)
        echo.set_alpha(round(90 * (1 - reaction_progress)))
        screen.blit(echo, reacted_position.move(-offset_x * 2, -offset_y * 2))

    screen.blit(reacted_sprite, reacted_position)
    if elapsed < ACT_TWO_PLAYER_HIT_REACTION_MS:
        flash = reacted_sprite.copy()
        flash.fill((232, 225, 218, 0), special_flags=pygame.BLEND_RGBA_ADD)
        flash.set_alpha(round(210 * (1 - reaction_progress)))
        screen.blit(flash, reacted_position)
        effect = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        _draw_hit_particles(effect, player_class, center, reaction_progress)
        if player_class == "mage":
            radius = round(12 + reaction_progress * 12)
            pygame.draw.circle(
                effect,
                (83, 176, 233, round(185 * (1 - reaction_progress))),
                center,
                radius,
                width=2,
            )
        screen.blit(effect, (0, 0))
    return True


def _draw_death_particles(
    screen,
    player_class,
    center,
    elapsed,
):
    effect = pygame.Surface((88, 88), pygame.SRCALPHA)
    local_center = (44, 48)
    color = _CLASS_COLORS[player_class]
    for particle_index in range(18):
        delay = (particle_index % 6) * 28
        particle_elapsed = elapsed - ACT_TWO_PLAYER_DEATH_HOLD_MS - delay
        if particle_elapsed < 0:
            continue
        progress = min(1, particle_elapsed / 1150)
        angle = math.radians((particle_index * 137 + 29) % 360)
        horizontal = math.cos(angle) * (5 + particle_index % 5 * 3) * progress
        if player_class == "warrior":
            vertical = 18 * progress * progress - 12 * progress
        elif player_class == "rogue":
            horizontal *= 1.7
            vertical = -8 * progress + math.sin(angle) * 5
        else:
            vertical = -(16 + particle_index % 4 * 5) * progress
        position = (
            round(local_center[0] + horizontal),
            round(local_center[1] + vertical),
        )
        alpha = round(205 * (1 - progress) ** 1.25)
        radius = 3 if particle_index % 6 == 0 else 2
        pygame.draw.circle(effect, (*color, alpha), position, radius)
    screen.blit(effect, (center[0] - 44, center[1] - 44))


def _draw_player_death(
    screen,
    sprite,
    position,
    player_class,
    current_time,
    death_started_at,
    death_sprites=None,
):
    elapsed = max(0, current_time - death_started_at)
    center = (
        position[0] + TILE_SIZE // 2,
        position[1] + TILE_SIZE // 2,
    )
    collapse = _smoothstep(
        (elapsed - ACT_TWO_PLAYER_DEATH_HOLD_MS)
        / (ACT_TWO_PLAYER_DEATH_COLLAPSE_MS - ACT_TWO_PLAYER_DEATH_HOLD_MS)
    )
    if (
        player_class in ("warrior", "rogue", "mage")
        and death_sprites is not None
    ):
        if player_class == "warrior":
            if elapsed < ACT_TWO_PLAYER_DEATH_HOLD_MS:
                body = death_sprites["hurt"]
            elif elapsed < ACT_TWO_WARRIOR_DEATH_FALL_MS:
                body = death_sprites["death_0"]
            else:
                body = death_sprites["death_1"]
        else:
            death_start = (
                ACT_TWO_ROGUE_DEATH_START_MS
                if player_class == "rogue"
                else ACT_TWO_MAGE_DEATH_START_MS
            )
            death_fall = (
                ACT_TWO_ROGUE_DEATH_FALL_MS
                if player_class == "rogue"
                else ACT_TWO_MAGE_DEATH_FALL_MS
            )
            if elapsed < death_start:
                body = sprite
            elif elapsed < death_fall:
                body = death_sprites["death_0"]
            else:
                body = death_sprites["death_1"]
        body_position = body.get_rect(topleft=position)
        if elapsed < 130:
            body = body.copy()
            flash = body.copy()
            flash.fill(
                (235, 219, 211, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            flash.set_alpha(round(220 * (1 - elapsed / 130)))
            body.blit(flash, (0, 0))
        screen.blit(body, body_position)
        _draw_death_particles(screen, player_class, center, elapsed)
        return

    body = sprite.copy()
    if elapsed < 130:
        flash = body.copy()
        flash.fill((235, 219, 211, 0), special_flags=pygame.BLEND_RGBA_ADD)
        flash.set_alpha(round(220 * (1 - elapsed / 130)))
        body.blit(flash, (0, 0))

    if player_class == "warrior":
        body = pygame.transform.rotozoom(body, -72 * collapse, 1)
        body.set_alpha(round(255 * (1 - collapse * 0.28)))
        body_position = body.get_rect(
            center=(center[0] - round(collapse * 5), center[1] + round(collapse * 8))
        )
    elif player_class == "rogue":
        body = pygame.transform.rotozoom(body, 25 * collapse, 1)
        body = pygame.transform.smoothscale(
            body,
            (
                max(8, round(body.get_width() * (1 + collapse * 0.22))),
                max(7, round(body.get_height() * (1 - collapse * 0.58))),
            ),
        )
        body.set_alpha(round(255 * (1 - collapse * 0.62)))
        body_position = body.get_rect(
            midbottom=(center[0] + round(collapse * 4), center[1] + 14)
        )
    else:
        body = pygame.transform.smoothscale(
            body,
            (
                max(8, round(body.get_width() * (1 - collapse * 0.18))),
                max(8, round(body.get_height() * (1 + collapse * 0.12))),
            ),
        )
        body.set_alpha(round(255 * max(0.16, 1 - collapse * 0.88)))
        body_position = body.get_rect(
            center=(center[0], center[1] - round(collapse * 10))
        )
    screen.blit(body, body_position)
    _draw_death_particles(screen, player_class, center, elapsed)


def draw_act_two_player_actor(
    screen,
    sprites,
    column,
    row,
    health,
    max_health,
    player_class,
    invisibility_turns,
    current_time,
    movement_started_at,
    movement_origin,
    potion_effect_started_at,
    hit_started_at,
    hit_origin,
    death_started_at,
    hit_damage,
    damage_font,
    facing_direction=(0, 1),
):
    sprite = sprites[f"player_{player_class}"]
    destination_position = (
        MAP_OFFSET_X + column * TILE_SIZE,
        MAP_OFFSET_Y + row * TILE_SIZE,
    )
    if invisibility_turns > 0:
        sprite = sprite.copy()
        sprite.set_alpha(90)

    if health <= 0 and death_started_at >= 0:
        death_sprites = None
        if player_class == "warrior":
            death_sprites = {
                "hurt": sprites["player_warrior_hurt"],
                "death_0": sprites["player_warrior_death_0"],
                "death_1": sprites["player_warrior_death_1"],
            }
        elif player_class == "rogue":
            death_sprites = {
                "death_0": sprites["player_rogue_death_0"],
                "death_1": sprites["player_rogue_death_1"],
            }
        elif player_class == "mage":
            death_sprites = {
                "death_0": sprites["player_mage_death_0"],
                "death_1": sprites["player_mage_death_1"],
            }
        _draw_player_death(
            screen,
            sprite,
            destination_position,
            player_class,
            current_time,
            death_started_at,
            death_sprites,
        )
        return

    movement_pose = PlayerMovementPose(
        position=destination_position,
        ground_position=destination_position,
        direction=(0, 0),
        progress=1.0,
        landing_progress=1.0,
        active=False,
    )
    if player_class == "warrior":
        movement_pose = sample_warrior_movement(
            column,
            row,
            movement_origin,
            current_time,
            movement_started_at,
        )
        if movement_pose.active:
            movement_frame = min(
                2,
                int(movement_pose.progress * 3),
            )
            if movement_pose.landing_progress > 0:
                movement_frame = 1
            if (column + row) % 2:
                movement_frame = 2 - movement_frame
            if movement_pose.direction[0] != 0:
                side = (
                    "right"
                    if movement_pose.direction[0] > 0
                    else "left"
                )
                sprite = sprites[
                    f"player_warrior_walk_side_{side}_{movement_frame}"
                ]
            elif movement_pose.direction[1] < 0:
                sprite = sprites[
                    f"player_warrior_walk_up_{movement_frame}"
                ]
            else:
                sprite = sprites[f"player_warrior_walk_{movement_frame}"]
            if invisibility_turns > 0:
                sprite = sprite.copy()
                sprite.set_alpha(90)
        elif facing_direction[0] != 0:
            side = "right" if facing_direction[0] > 0 else "left"
            sprite = sprites[f"player_warrior_walk_side_{side}_1"]
            if invisibility_turns > 0:
                sprite = sprite.copy()
                sprite.set_alpha(90)
        elif facing_direction[1] < 0:
            sprite = sprites["player_warrior_walk_up_1"]
            if invisibility_turns > 0:
                sprite = sprite.copy()
                sprite.set_alpha(90)
        draw_warrior_movement_grounding(screen, movement_pose)
    elif player_class == "rogue":
        movement_pose = sample_rogue_movement(
            column,
            row,
            movement_origin,
            current_time,
            movement_started_at,
        )
        if movement_pose.active:
            movement_frame = min(
                2,
                int(movement_pose.progress * 3),
            )
            if movement_pose.landing_progress > 0:
                movement_frame = 1
            if (column + row) % 2:
                movement_frame = 2 - movement_frame
            if movement_pose.direction[0] != 0:
                side = (
                    "right"
                    if movement_pose.direction[0] > 0
                    else "left"
                )
                sprite = sprites[
                    f"player_rogue_walk_side_{side}_{movement_frame}"
                ]
            else:
                sprite = sprites[f"player_rogue_walk_{movement_frame}"]
            if invisibility_turns > 0:
                sprite = sprite.copy()
                sprite.set_alpha(90)
        elif facing_direction[0] != 0:
            side = "right" if facing_direction[0] > 0 else "left"
            sprite = sprites[f"player_rogue_walk_side_{side}_1"]
            if invisibility_turns > 0:
                sprite = sprite.copy()
                sprite.set_alpha(90)
        draw_rogue_movement_grounding(screen, sprite, movement_pose)
    elif player_class == "mage":
        movement_pose = sample_mage_movement(
            column,
            row,
            movement_origin,
            current_time,
            movement_started_at,
        )
        if movement_pose.active:
            movement_frame = min(
                2,
                int(movement_pose.progress * 3),
            )
            if movement_pose.landing_progress > 0:
                movement_frame = 1
            if (column + row) % 2:
                movement_frame = 2 - movement_frame
            sprite = sprites[f"player_mage_walk_{movement_frame}"]
            if invisibility_turns > 0:
                sprite = sprite.copy()
                sprite.set_alpha(90)
        draw_mage_movement_grounding(screen, movement_pose)
    position = movement_pose.position
    visual_facing_direction = (
        movement_pose.direction
        if movement_pose.active
        else facing_direction
    )

    hit_elapsed = current_time - hit_started_at
    if (
        player_class == "warrior"
        and visual_facing_direction == (0, 1)
        and hit_started_at >= 0
        and 0 <= hit_elapsed < ACT_TWO_PLAYER_HIT_REACTION_MS
    ):
        sprite = sprites["player_warrior_hurt"]
    hit_active = _draw_player_hit(
        screen,
        sprite,
        position,
        player_class,
        current_time,
        hit_started_at,
        hit_origin,
        visual_facing_direction,
    )
    _draw_healing_effect(
        screen,
        (
            position[0] + TILE_SIZE // 2,
            position[1] + TILE_SIZE // 2,
        ),
        player_class,
        current_time,
        potion_effect_started_at,
    )
    elapsed = current_time - hit_started_at
    if (
        hit_active
        and damage_font is not None
        and 0 <= elapsed < ACT_TWO_PLAYER_HIT_FEEDBACK_MS
    ):
        progress = elapsed / ACT_TWO_PLAYER_HIT_FEEDBACK_MS
        alpha = round(255 * min(1, (1 - progress) * 2.4))
        number = damage_font.render(str(hit_damage), True, (244, 224, 215))
        number.set_alpha(alpha)
        number_position = number.get_rect(
            midbottom=(
                position[0] + TILE_SIZE // 2,
                position[1] - 6 - round(progress * 14),
            )
        )
        shadow = damage_font.render(str(hit_damage), True, (18, 5, 7))
        shadow.set_alpha(alpha)
        screen.blit(shadow, number_position.move(1, 2))
        screen.blit(number, number_position)

def _draw_old_man(screen, game_state, fonts, sprites, elapsed):
    old_man_cell = game_state.player.old_man_position
    if elapsed < ACT_TWO_OLD_MAN_APPEAR_MS or old_man_cell is None:
        return
    appearance_elapsed = elapsed - ACT_TWO_OLD_MAN_APPEAR_MS
    fade = _smoothstep(appearance_elapsed / 720)
    sprite_name = (
        "old_man_standing"
        if elapsed < ACT_TWO_OLD_MAN_KNEEL_MS
        else "old_man_kneeling"
    )
    sprite = sprites[sprite_name].copy()
    if old_man_cell[0] < game_state.floor.player_column:
        sprite = pygame.transform.flip(sprite, True, False)
    sprite.set_alpha(round(255 * fade))
    position = (
        MAP_OFFSET_X
        + old_man_cell[0] * TILE_SIZE
        - (sprite.get_width() - TILE_SIZE) // 2,
        MAP_OFFSET_Y
        + old_man_cell[1] * TILE_SIZE
        - (sprite.get_height() - TILE_SIZE),
    )
    for echo_index in range(2, 0, -1):
        echo = sprite.copy()
        echo.set_alpha(round(42 * fade / echo_index))
        screen.blit(echo, (position[0], position[1] - echo_index * 3))
    screen.blit(sprite, position)

    if elapsed < ACT_TWO_OLD_MAN_DIALOGUE_MS:
        return
    dialogue_progress = _smoothstep(
        (elapsed - ACT_TWO_OLD_MAN_DIALOGUE_MS) / 420
    )
    line_y = MAP_OFFSET_Y + MAP_HEIGHT - 46
    for line in wrap_text(
        fonts["text"],
        _OLD_MAN_LINES[game_state.player.player_class],
        MAP_WIDTH - 100,
    ):
        line_surface = fonts["text"].render(line, True, (218, 211, 197))
        line_surface.set_alpha(round(255 * dialogue_progress))
        rectangle = line_surface.get_rect(
            center=(MAP_OFFSET_X + MAP_WIDTH // 2, line_y)
        )
        shadow = fonts["text"].render(line, True, (4, 5, 7))
        shadow.set_alpha(round(255 * dialogue_progress))
        screen.blit(shadow, rectangle.move(2, 2))
        screen.blit(line_surface, rectangle)
        line_y += 23


def draw_act_two_player_feedback_overlay(
    screen,
    game_state,
    fonts,
    sprites,
    current_time,
):
    player = game_state.player
    if player.player_class not in _CLASS_COLORS:
        return
    hit_elapsed = current_time - player.hit_animation_started_at
    if (
        player.health > 0
        and player.hit_animation_started_at >= 0
        and 0 <= hit_elapsed < 330
    ):
        visibility = math.sin(math.pi * hit_elapsed / 330)
        vignette = pygame.Surface((MAP_WIDTH, MAP_HEIGHT), pygame.SRCALPHA)
        for inset, strength in ((0, 1), (7, 0.6), (15, 0.28)):
            pygame.draw.rect(
                vignette,
                (118, 13, 20, round(105 * strength * visibility)),
                (
                    inset,
                    inset,
                    MAP_WIDTH - inset * 2,
                    MAP_HEIGHT - inset * 2,
                ),
                width=9,
            )
        screen.blit(vignette, (MAP_OFFSET_X, MAP_OFFSET_Y))

    if player.health > 0 or player.death_animation_started_at < 0:
        return
    elapsed = max(0, current_time - player.death_animation_started_at)
    fade = _smoothstep((elapsed - 600) / 1900)
    view_rectangle = pygame.Rect(
        MAP_OFFSET_X,
        MAP_OFFSET_Y,
        MAP_WIDTH,
        MAP_HEIGHT,
    )
    if fade > 0:
        view_copy = screen.subsurface(view_rectangle).copy()
        grayscale = pygame.transform.grayscale(view_copy)
        grayscale.set_alpha(round(185 * fade))
        screen.blit(grayscale, view_rectangle)
        darkness = pygame.Surface((MAP_WIDTH, MAP_HEIGHT), pygame.SRCALPHA)
        darkness.fill((3, 5, 7, round(58 * fade)))
        screen.blit(darkness, (MAP_OFFSET_X, MAP_OFFSET_Y))

    _draw_old_man(screen, game_state, fonts, sprites, elapsed)

    message_progress = _smoothstep(
        (elapsed - ACT_TWO_DEFEAT_MESSAGE_MS) / ACT_TWO_DEFEAT_FADE_MS
    )
    if message_progress <= 0:
        return
    alpha = round(255 * message_progress)
    center_x = MAP_OFFSET_X + MAP_WIDTH // 2
    title = fonts["title"].render(
        _DEFEAT_TITLES[player.player_class],
        True,
        _CLASS_COLORS[player.player_class],
    )
    title.set_alpha(alpha)
    title_rectangle = title.get_rect(
        center=(center_x, MAP_OFFSET_Y + 76)
    )
    title_shadow = fonts["title"].render(
        _DEFEAT_TITLES[player.player_class],
        True,
        (8, 5, 7),
    )
    title_shadow.set_alpha(alpha)
    screen.blit(title_shadow, title_rectangle.move(2, 3))
    screen.blit(title, title_rectangle)

    restart = fonts["controls"].render(
        "PRESS R TO RESTART",
        True,
        (170, 174, 176),
    )
    restart.set_alpha(alpha)
    screen.blit(
        restart,
        restart.get_rect(center=(center_x, MAP_OFFSET_Y + 116)),
    )
