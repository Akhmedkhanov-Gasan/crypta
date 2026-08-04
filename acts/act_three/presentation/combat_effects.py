import math

import pygame

from game.events import GameEventType
from presentation.layout import ACT_THREE_TILE_SIZE


_TORCH_LIGHT_SURFACE = None
_IDLE_FRAME_SEQUENCE = (0, 1, 2, 1)
_IDLE_TIMELINE_CYCLE_COUNT = 4
_MOVE_FRAME_COUNT = 2
_MOVE_FRAME_DURATION_MS = 90
_ATTACK_FRAME_DURATION_MS = 240
_FAMILIAR_MOVE_DURATION_MS = 180
_TELEPORT_CAMERA_DURATION_MS = 480
_TELEPORT_EFFECT_DURATION_MS = 600
_ARCHER_BARRAGE_SHOT_EFFECT_MS = 360
_TOP_VOID_CORNER_Y_OFFSET = 47
_TOP_VOID_CORNER_X_OFFSETS = {
    "wall_corner_top_left": -18,
    "wall_corner_top_right": 18,
}
_TOP_VOID_DOUBLE_CORNER_CROP_WIDTH = 24

_ENEMY_HIT_REACTION_DURATION_MS = 190
_ENEMY_HIT_FEEDBACK_DURATION_MS = 680
_PLAYER_HIT_REACTION_DURATION_MS = 210
_PLAYER_HIT_SPRITE_DURATION_MS = 270
_PLAYER_HIT_FEEDBACK_DURATION_MS = 680
_PLAYER_HIT_VIGNETTE_DURATION_MS = 340
_PLAYER_HIT_CAMERA_SHAKE_DURATION_MS = 190
_FAMILIAR_HIT_REACTION_DURATION_MS = 190
_FAMILIAR_HIT_FEEDBACK_DURATION_MS = 680
_PLAYER_DEATH_HURT_HOLD_MS = 220
_PLAYER_DEATH_COLLAPSE_END_MS = 720
_PLAYER_DEATH_MESSAGE_START_MS = 1250
_PLAYER_DEATH_MESSAGE_FADE_MS = 350


def record_enemy_hit_feedback(game_state, started_at):
    hit_events_by_target = {}

    for event in game_state.events:
        if (
            event.type is not GameEventType.HIT
            or event.target in (None, "hero", "familiar")
            or not event.amount
        ):
            continue

        hit_events_by_target.setdefault(event.target, []).append(event)

    for enemy in game_state.floor.enemies:
        hit_events = hit_events_by_target.get(enemy.name)
        if not hit_events:
            continue

        enemy.hit_animation_started_at = started_at
        enemy.hit_damage = sum(event.amount for event in hit_events)
        enemy.hit_critical = any(
            event.data.get("critical", False)
            for event in hit_events
        )
        enemy.hit_origin = next(
            (
                event.origin
                for event in reversed(hit_events)
                if event.origin is not None
            ),
            None,
        )


def record_enemy_death_feedback(game_state, started_at):
    defeated_enemy_names = {
        event.actor
        for event in game_state.events
        if event.type is GameEventType.DEATH
    }

    for enemy in game_state.floor.enemies:
        if (
            enemy.name in defeated_enemy_names
            and enemy.death_animation_started_at < 0
        ):
            enemy.death_animation_started_at = started_at


def record_player_hit_feedback(game_state, started_at):
    hit_events = [
        event
        for event in game_state.events
        if (
            event.type is GameEventType.HIT
            and event.target == "hero"
            and event.amount
        )
    ]
    if not hit_events:
        return

    player = game_state.player
    player.hit_animation_started_at = started_at
    player.hit_damage = sum(event.amount for event in hit_events)
    player.hit_origin = next(
        (
            event.origin
            for event in reversed(hit_events)
            if event.origin is not None
        ),
        None,
    )


def record_player_death_feedback(game_state, started_at):
    player = game_state.player
    if (
        player.health > 0
        or player.death_animation_started_at >= 0
    ):
        return

    player.death_animation_started_at = started_at


def _player_death_elapsed(player, current_time):
    if player.death_animation_started_at < 0:
        return None
    return max(0, current_time - player.death_animation_started_at)


def _player_death_frame(player, current_time):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None or elapsed < _PLAYER_DEATH_HURT_HOLD_MS:
        return None
    if elapsed < _PLAYER_DEATH_COLLAPSE_END_MS:
        return 0
    return 1


def record_familiar_hit_feedback(game_state, started_at):
    hit_events = [
        event
        for event in game_state.events
        if (
            event.type is GameEventType.HIT
            and event.target == "familiar"
            and event.amount
        )
    ]
    if not hit_events:
        return

    player = game_state.player
    player.summoner_familiar_hit_animation_started_at = started_at
    player.summoner_familiar_hit_damage = sum(
        event.amount for event in hit_events
    )
    player.summoner_familiar_hit_origin = next(
        (
            event.origin
            for event in reversed(hit_events)
            if event.origin is not None
        ),
        None,
    )
    player.summoner_familiar_hit_position = next(
        (
            event.destination
            for event in reversed(hit_events)
            if event.destination is not None
        ),
        None,
    )


def _familiar_hit_feedback_active(player, current_time):
    elapsed = (
        current_time
        - player.summoner_familiar_hit_animation_started_at
    )
    return (
        player.summoner_familiar_hit_animation_started_at >= 0
        and 0 <= elapsed < _FAMILIAR_HIT_FEEDBACK_DURATION_MS
    )


def _familiar_hit_is_heavy(player):
    return player.summoner_familiar_hit_damage >= max(
        2,
        player.summoner_familiar_max_health * 0.25,
    )


def _familiar_hit_direction(player, familiar_column, familiar_row):
    origin = player.summoner_familiar_hit_origin
    if origin is None:
        return (0.0, 1.0)

    direction_x = familiar_column - origin[0]
    direction_y = familiar_row - origin[1]
    direction_length = max(
        1,
        math.hypot(direction_x, direction_y),
    )
    return (
        direction_x / direction_length,
        direction_y / direction_length,
    )


def _draw_familiar_hit_feedback(
    surface,
    sprite,
    position,
    player,
    familiar_column,
    familiar_row,
    current_time,
    damage_font,
):
    if not _familiar_hit_feedback_active(player, current_time):
        if sprite is not None:
            surface.blit(sprite, position)
        return

    elapsed = (
        current_time
        - player.summoner_familiar_hit_animation_started_at
    )
    direction_x, direction_y = _familiar_hit_direction(
        player,
        familiar_column,
        familiar_row,
    )
    recoil_progress = min(
        1,
        elapsed / _FAMILIAR_HIT_REACTION_DURATION_MS,
    )
    recoil = math.sin(math.pi * recoil_progress)
    recoil_distance = 6 if _familiar_hit_is_heavy(player) else 4
    sprite_position = (
        position[0] + round(direction_x * recoil_distance * recoil),
        position[1] + round(direction_y * recoil_distance * recoil),
    )

    if sprite is not None:
        surface.blit(sprite, sprite_position)
        if elapsed < _FAMILIAR_HIT_REACTION_DURATION_MS:
            flash = sprite.copy()
            flash.fill(
                (164, 226, 255, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            flash.set_alpha(round(225 * (1 - recoil_progress)))
            surface.blit(flash, sprite_position)

    center_x = position[0] + ACT_THREE_TILE_SIZE // 2
    center_y = position[1] + ACT_THREE_TILE_SIZE // 2
    particle_visibility = max(0, 1 - recoil_progress)
    particle_count = 9 if _familiar_hit_is_heavy(player) else 6
    particle_distance = 8 + recoil_progress * 18
    base_angle = math.atan2(direction_y, direction_x) + math.pi
    for particle_index in range(particle_count):
        spread = (
            particle_index - (particle_count - 1) / 2
        ) * 0.28
        angle = base_angle + spread
        particle_radius = 2 if particle_index % 3 == 0 else 1
        particle_surface = pygame.Surface(
            (particle_radius * 2 + 2, particle_radius * 2 + 2),
            pygame.SRCALPHA,
        )
        pygame.draw.circle(
            particle_surface,
            (91, 211, 255, round(245 * particle_visibility)),
            (particle_radius + 1, particle_radius + 1),
            particle_radius,
        )
        particle_position = (
            round(center_x + math.cos(angle) * particle_distance),
            round(center_y + math.sin(angle) * particle_distance),
        )
        surface.blit(
            particle_surface,
            (
                particle_position[0] - particle_radius - 1,
                particle_position[1] - particle_radius - 1,
            ),
        )

    number_progress = min(
        1,
        elapsed / _FAMILIAR_HIT_FEEDBACK_DURATION_MS,
    )
    number_alpha = round(
        255 * min(1, (1 - number_progress) * 2.6)
    )
    number_text = f"-{player.summoner_familiar_hit_damage}"
    number_color = (
        (195, 242, 255)
        if _familiar_hit_is_heavy(player)
        else (103, 218, 255)
    )
    number_surface = damage_font.render(
        number_text,
        True,
        number_color,
    )
    number_surface.set_alpha(number_alpha)
    number_position = number_surface.get_rect(
        center=(
            center_x,
            position[1] - 7 - round(number_progress * 13),
        )
    )
    shadow = damage_font.render(number_text, True, (5, 18, 27))
    shadow.set_alpha(number_alpha)
    surface.blit(shadow, number_position.move(1, 2))
    surface.blit(number_surface, number_position)


def _player_hit_feedback_active(player, current_time):
    elapsed = current_time - player.hit_animation_started_at
    return (
        player.hit_animation_started_at >= 0
        and 0 <= elapsed < _PLAYER_HIT_FEEDBACK_DURATION_MS
    )


def _player_hurt_sprite_active(player, current_time):
    elapsed = current_time - player.hit_animation_started_at
    return (
        player.hit_animation_started_at >= 0
        and 0 <= elapsed < _PLAYER_HIT_SPRITE_DURATION_MS
    )


def _player_hit_is_heavy(player):
    return (
        player.health <= 0
        or player.hit_damage >= max(2, player.max_health * 0.25)
    )


def _player_hit_direction(player, player_column, player_row):
    origin = player.hit_origin
    if origin is None:
        return (0.0, 1.0)

    direction_x = player_column - origin[0]
    direction_y = player_row - origin[1]
    direction_length = max(
        1,
        math.hypot(direction_x, direction_y),
    )
    return (
        direction_x / direction_length,
        direction_y / direction_length,
    )


def _player_hit_offset(
    player,
    player_column,
    player_row,
    current_time,
):
    elapsed = current_time - player.hit_animation_started_at
    if not 0 <= elapsed < _PLAYER_HIT_REACTION_DURATION_MS:
        return (0, 0)

    direction_x, direction_y = _player_hit_direction(
        player,
        player_column,
        player_row,
    )
    progress = elapsed / _PLAYER_HIT_REACTION_DURATION_MS
    recoil = math.sin(math.pi * progress)
    distance = 6 if _player_hit_is_heavy(player) else 4
    return (
        round(direction_x * distance * recoil),
        round(direction_y * distance * recoil),
    )


def _player_hit_camera_offset(player, current_time):
    elapsed = current_time - player.hit_animation_started_at
    if not 0 <= elapsed < _PLAYER_HIT_CAMERA_SHAKE_DURATION_MS:
        return (0, 0)

    progress = elapsed / _PLAYER_HIT_CAMERA_SHAKE_DURATION_MS
    strength = 4 if _player_hit_is_heavy(player) else 2
    decay = 1 - progress
    return (
        round(math.sin(elapsed * 0.19) * strength * decay),
        round(math.cos(elapsed * 0.27) * strength * 0.7 * decay),
    )


def _draw_player_hit_feedback(
    surface,
    sprite,
    position,
    player,
    player_column,
    player_row,
    current_time,
    damage_font,
):
    if not _player_hit_feedback_active(player, current_time):
        surface.blit(sprite, position)
        return

    elapsed = current_time - player.hit_animation_started_at
    offset_x, offset_y = _player_hit_offset(
        player,
        player_column,
        player_row,
        current_time,
    )
    sprite_position = (
        position[0] + offset_x,
        position[1] + offset_y,
    )
    surface.blit(sprite, sprite_position)

    if elapsed < _PLAYER_HIT_REACTION_DURATION_MS:
        reaction_progress = (
            elapsed / _PLAYER_HIT_REACTION_DURATION_MS
        )
        flash = sprite.copy()
        flash.fill(
            (255, 205, 185, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        flash.set_alpha(round(225 * (1 - reaction_progress)))
        surface.blit(flash, sprite_position)

        center_x = position[0] + ACT_THREE_TILE_SIZE // 2
        center_y = position[1] + ACT_THREE_TILE_SIZE // 2
        direction_x, direction_y = _player_hit_direction(
            player,
            player_column,
            player_row,
        )
        base_angle = math.atan2(direction_y, direction_x) + math.pi
        particle_count = 9 if _player_hit_is_heavy(player) else 6
        particle_distance = 8 + reaction_progress * 18
        particle_alpha = round(245 * (1 - reaction_progress))
        for particle_index in range(particle_count):
            spread = (
                particle_index - (particle_count - 1) / 2
            ) * 0.24
            angle = base_angle + spread
            particle_position = (
                round(center_x + math.cos(angle) * particle_distance),
                round(center_y + math.sin(angle) * particle_distance),
            )
            particle_radius = 2 if particle_index % 3 == 0 else 1
            particle_surface = pygame.Surface(
                (particle_radius * 2 + 2, particle_radius * 2 + 2),
                pygame.SRCALPHA,
            )
            pygame.draw.circle(
                particle_surface,
                (255, 112, 82, particle_alpha),
                (particle_radius + 1, particle_radius + 1),
                particle_radius,
            )
            surface.blit(
                particle_surface,
                (
                    particle_position[0] - particle_radius - 1,
                    particle_position[1] - particle_radius - 1,
                ),
            )

    number_progress = min(
        1,
        elapsed / _PLAYER_HIT_FEEDBACK_DURATION_MS,
    )
    number_alpha = round(
        255 * min(1, (1 - number_progress) * 2.6)
    )
    number_text = f"-{player.hit_damage}"
    number_color = (
        (255, 72, 52)
        if _player_hit_is_heavy(player)
        else (255, 126, 105)
    )
    number_surface = damage_font.render(
        number_text,
        True,
        number_color,
    )
    number_surface.set_alpha(number_alpha)
    number_position = number_surface.get_rect(
        center=(
            position[0] + ACT_THREE_TILE_SIZE // 2,
            position[1] - 7 - round(number_progress * 13),
        )
    )
    shadow = damage_font.render(number_text, True, (18, 7, 8))
    shadow.set_alpha(number_alpha)
    surface.blit(shadow, number_position.move(1, 2))
    surface.blit(number_surface, number_position)


def _draw_player_hit_vignette(surface, player, current_time):
    elapsed = current_time - player.hit_animation_started_at
    if not 0 <= elapsed < _PLAYER_HIT_VIGNETTE_DURATION_MS:
        return

    progress = elapsed / _PLAYER_HIT_VIGNETTE_DURATION_MS
    visibility = (1 - progress) ** 2
    base_alpha = round(
        (105 if _player_hit_is_heavy(player) else 72)
        * visibility
    )
    width, height = surface.get_size()
    vignette = pygame.Surface((width, height), pygame.SRCALPHA)
    for inset, alpha_scale in (
        (0, 1.0),
        (7, 0.72),
        (15, 0.42),
        (25, 0.18),
    ):
        pygame.draw.rect(
            vignette,
            (116, 8, 12, round(base_alpha * alpha_scale)),
            (inset, inset, width - inset * 2, height - inset * 2),
            width=8,
        )
    surface.blit(vignette, (0, 0))


def _enemy_hit_feedback_active(enemy, current_time):
    elapsed = current_time - enemy.hit_animation_started_at
    return (
        enemy.hit_animation_started_at >= 0
        and 0 <= elapsed < _ENEMY_HIT_FEEDBACK_DURATION_MS
    )


def _enemy_hit_offset(enemy, elapsed):
    if elapsed >= _ENEMY_HIT_REACTION_DURATION_MS:
        return (0, 0)

    origin = enemy.hit_origin
    direction_x = 0
    direction_y = -1
    if origin is not None:
        direction_x = enemy.column - origin[0]
        direction_y = enemy.row - origin[1]
        direction_length = max(
            1,
            math.hypot(direction_x, direction_y),
        )
        direction_x /= direction_length
        direction_y /= direction_length

    progress = elapsed / _ENEMY_HIT_REACTION_DURATION_MS
    recoil = math.sin(math.pi * progress)
    distance = 7 if enemy.hit_critical else 4
    return (
        round(direction_x * distance * recoil),
        round(direction_y * distance * recoil),
    )


def _draw_enemy_hit_feedback(
    surface,
    sprite,
    position,
    enemy,
    current_time,
    damage_font,
):
    if not _enemy_hit_feedback_active(enemy, current_time):
        surface.blit(sprite, position)
        return

    elapsed = current_time - enemy.hit_animation_started_at
    offset_x, offset_y = _enemy_hit_offset(enemy, elapsed)
    sprite_position = (
        position[0] + offset_x,
        position[1] + offset_y,
    )
    surface.blit(sprite, sprite_position)

    if elapsed < _ENEMY_HIT_REACTION_DURATION_MS:
        flash_progress = (
            elapsed / _ENEMY_HIT_REACTION_DURATION_MS
        )
        flash_alpha = round(220 * (1 - flash_progress))
        flash = sprite.copy()
        flash.fill(
            (255, 238, 205, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        flash.set_alpha(flash_alpha)
        surface.blit(flash, sprite_position)

    center_x = position[0] + ACT_THREE_TILE_SIZE // 2
    center_y = position[1] + ACT_THREE_TILE_SIZE // 2
    particle_progress = min(
        1,
        elapsed / _ENEMY_HIT_REACTION_DURATION_MS,
    )
    particle_visibility = max(0, 1 - particle_progress)
    particle_color = (
        (255, 194, 72)
        if enemy.hit_critical
        else (238, 224, 205)
    )
    particle_count = 8 if enemy.hit_critical else 6
    particle_distance = 10 + particle_progress * (
        20 if enemy.hit_critical else 14
    )

    for particle_index in range(particle_count):
        angle = (
            particle_index * math.tau / particle_count
            + (enemy.column * 0.71 + enemy.row * 1.13)
        )
        particle_position = (
            round(center_x + math.cos(angle) * particle_distance),
            round(center_y + math.sin(angle) * particle_distance),
        )
        particle_radius = 2 if particle_index % 3 == 0 else 1
        particle_surface = pygame.Surface(
            (particle_radius * 2 + 2, particle_radius * 2 + 2),
            pygame.SRCALPHA,
        )
        pygame.draw.circle(
            particle_surface,
            (*particle_color, round(255 * particle_visibility)),
            (particle_radius + 1, particle_radius + 1),
            particle_radius,
        )
        surface.blit(
            particle_surface,
            (
                particle_position[0] - particle_radius - 1,
                particle_position[1] - particle_radius - 1,
            ),
        )

    number_progress = min(
        1,
        elapsed / _ENEMY_HIT_FEEDBACK_DURATION_MS,
    )
    number_alpha = round(
        255 * min(1, (1 - number_progress) * 2.6)
    )
    number_color = (
        (255, 196, 64)
        if enemy.hit_critical
        else (245, 235, 220)
    )
    number_text = (
        f"{enemy.hit_damage}!"
        if enemy.hit_critical
        else str(enemy.hit_damage)
    )
    number_surface = damage_font.render(
        number_text,
        True,
        number_color,
    )
    number_surface.set_alpha(number_alpha)
    number_position = number_surface.get_rect(
        center=(
            center_x,
            position[1] - 7 - round(number_progress * 13),
        )
    )
    shadow = damage_font.render(number_text, True, (18, 10, 12))
    shadow.set_alpha(number_alpha)
    surface.blit(shadow, number_position.move(1, 2))
    surface.blit(number_surface, number_position)

def _draw_attack_impact_flash(
    surface,
    position,
    current_time,
    started_at,
    flash_color,
):
    elapsed = current_time - started_at
    if not 0 <= elapsed < _ATTACK_FRAME_DURATION_MS:
        return

    progress = elapsed / _ATTACK_FRAME_DURATION_MS
    visibility = math.sin(math.pi * progress)
    center = (
        position[0] + ACT_THREE_TILE_SIZE // 2,
        position[1] + ACT_THREE_TILE_SIZE // 2,
    )
    radius = round(7 + visibility * 9)
    alpha = round(190 * visibility)
    flash_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    local_center = (
        center[0] - position[0],
        center[1] - position[1],
    )
    pygame.draw.circle(
        flash_surface,
        (*flash_color, alpha),
        local_center,
        radius,
        width=2,
    )
    pygame.draw.line(
        flash_surface,
        (235, 255, 235, alpha),
        (local_center[0] - radius, local_center[1] + radius // 2),
        (local_center[0] + radius, local_center[1] - radius // 2),
        width=2,
    )
    surface.blit(flash_surface, position)


def _draw_archer_projectile(
    surface,
    arrow_sprite,
    origin,
    destination,
    progress,
    empowered=False,
    current_time=0,
):
    direction = math.atan2(
        destination[1] - origin[1],
        destination[0] - origin[0],
    )
    rotation = -math.degrees(direction) - 45
    arrow_position = (
        round(origin[0] + (destination[0] - origin[0]) * progress),
        round(origin[1] + (destination[1] - origin[1]) * progress),
    )

    for trail_progress, trail_alpha in (
        (progress - 0.18, 38),
        (progress - 0.10, 78),
    ):
        if trail_progress <= 0:
            continue
        trail_position = (
            round(origin[0] + (destination[0] - origin[0]) * trail_progress),
            round(origin[1] + (destination[1] - origin[1]) * trail_progress),
        )
        trail = pygame.transform.rotate(arrow_sprite, rotation).copy()
        trail.set_alpha(trail_alpha)
        surface.blit(trail, trail.get_rect(center=trail_position))

    if empowered:
        effect_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        travel_dx = destination[0] - origin[0]
        travel_dy = destination[1] - origin[1]
        travel_length = max(1, math.hypot(travel_dx, travel_dy))
        direction_x = travel_dx / travel_length
        direction_y = travel_dy / travel_length
        normal_x = -travel_dy / travel_length
        normal_y = travel_dx / travel_length

        trail_start_progress = max(0, progress - 0.34)
        trail_start = (
            round(origin[0] + travel_dx * trail_start_progress),
            round(origin[1] + travel_dy * trail_start_progress),
        )
        for width, color in (
            (12, (20, 135, 85, 24)),
            (7, (40, 220, 125, 48)),
            (3, (125, 255, 180, 145)),
            (1, (235, 255, 240, 225)),
        ):
            pygame.draw.line(
                effect_surface,
                color,
                trail_start,
                arrow_position,
                width=width,
            )

        for wave_index, (wave_color, wave_alpha) in enumerate(
            (
                ((75, 235, 135), 115),
                ((145, 255, 190), 70),
            )
        ):
            points = []
            for point_index in range(15):
                wave_progress = max(
                    0,
                    progress - 0.31 + point_index * 0.021,
                )
                wave_x = origin[0] + travel_dx * wave_progress
                wave_y = origin[1] + travel_dy * wave_progress
                wave = math.sin(
                    current_time * 0.014
                    + point_index * 0.82
                    + wave_index * math.pi
                ) * (3.5 + wave_index * 2)
                points.append(
                    (
                        round(wave_x + normal_x * wave),
                        round(wave_y + normal_y * wave),
                    )
                )
            if len(points) > 1:
                pygame.draw.lines(
                    effect_surface,
                    (*wave_color, wave_alpha),
                    False,
                    points,
                    width=1 if wave_index else 2,
                )

        for particle_index in range(9):
            particle_progress = progress - 0.035 - particle_index * 0.032
            if particle_progress <= 0:
                continue
            particle_wave = math.sin(
                current_time * 0.021 + particle_index * 2.15
            ) * (2 + particle_index * 0.45)
            particle_position = (
                round(
                    origin[0]
                    + travel_dx * particle_progress
                    + normal_x * particle_wave
                ),
                round(
                    origin[1]
                    + travel_dy * particle_progress
                    + normal_y * particle_wave
                ),
            )
            particle_alpha = max(30, 185 - particle_index * 17)
            particle_radius = 2 if particle_index < 3 else 1
            pygame.draw.circle(
                effect_surface,
                (155, 255, 195, particle_alpha),
                particle_position,
                particle_radius,
            )

        pulse = (math.sin(current_time * 0.025) + 1) / 2
        for radius, alpha in (
            (13, round(18 + pulse * 10)),
            (8, round(30 + pulse * 14)),
            (4, round(65 + pulse * 25)),
        ):
            pygame.draw.circle(
                effect_surface,
                (75, 245, 145, alpha),
                arrow_position,
                radius,
            )

        ring_angle = current_time * 0.012
        for angle_offset in (-0.9, 0.9):
            ring_length = 9
            ring_center = (
                round(
                    arrow_position[0]
                    - direction_x * 4
                    + normal_x * math.sin(ring_angle + angle_offset) * 5
                ),
                round(
                    arrow_position[1]
                    - direction_y * 4
                    + normal_y * math.sin(ring_angle + angle_offset) * 5
                ),
            )
            ring_end = (
                round(ring_center[0] + normal_x * ring_length),
                round(ring_center[1] + normal_y * ring_length),
            )
            pygame.draw.line(
                effect_surface,
                (205, 255, 220, 155),
                ring_center,
                ring_end,
                width=1,
            )

        if progress > 0.82:
            impact_progress = min(1, (progress - 0.82) / 0.18)
            impact_visibility = math.sin(math.pi * impact_progress)
            impact_radius = round(5 + impact_progress * 12)
            pygame.draw.circle(
                effect_surface,
                (
                    95,
                    255,
                    160,
                    round(150 * impact_visibility),
                ),
                destination,
                impact_radius,
                width=2,
            )
            for ray_index in range(6):
                ray_angle = ray_index * math.tau / 6 + direction
                ray_start = (
                    round(
                        destination[0]
                        + math.cos(ray_angle) * 4
                    ),
                    round(
                        destination[1]
                        + math.sin(ray_angle) * 4
                    ),
                )
                ray_end = (
                    round(
                        destination[0]
                        + math.cos(ray_angle) * impact_radius
                    ),
                    round(
                        destination[1]
                        + math.sin(ray_angle) * impact_radius
                    ),
                )
                pygame.draw.line(
                    effect_surface,
                    (
                        220,
                        255,
                        225,
                        round(175 * impact_visibility),
                    ),
                    ray_start,
                    ray_end,
                    width=1,
                )

        surface.blit(effect_surface, (0, 0))

    arrow = pygame.transform.rotate(arrow_sprite, rotation)
    surface.blit(arrow, arrow.get_rect(center=arrow_position))


def _draw_warlock_orb(
    surface,
    origin,
    destination,
    progress,
    current_time,
):
    orb_position = (
        round(
            origin[0]
            + (destination[0] - origin[0]) * progress
        ),
        round(
            origin[1]
            + (destination[1] - origin[1]) * progress
        ),
    )
    effect_surface = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    trail_start_progress = max(0, progress - 0.34)
    trail_start = (
        round(
            origin[0]
            + (destination[0] - origin[0])
            * trail_start_progress
        ),
        round(
            origin[1]
            + (destination[1] - origin[1])
            * trail_start_progress
        ),
    )
    for width, color in (
        (10, (72, 18, 112, 32)),
        (6, (126, 35, 188, 68)),
        (2, (211, 105, 255, 175)),
    ):
        pygame.draw.line(
            effect_surface,
            color,
            trail_start,
            orb_position,
            width=width,
        )

    pulse = (math.sin(current_time * 0.028) + 1) / 2
    for radius, color in (
        (10, (86, 20, 142, round(38 + pulse * 20))),
        (7, (144, 42, 222, round(95 + pulse * 35))),
        (4, (210, 105, 255, 235)),
        (2, (246, 220, 255, 255)),
    ):
        pygame.draw.circle(
            effect_surface,
            color,
            orb_position,
            radius,
        )

    for particle_index in range(5):
        angle = (
            current_time * 0.012
            + particle_index * math.tau / 5
        )
        particle_position = (
            round(orb_position[0] + math.cos(angle) * 9),
            round(orb_position[1] + math.sin(angle) * 7),
        )
        pygame.draw.circle(
            effect_surface,
            (225, 125, 255, 170),
            particle_position,
            1,
        )

    if progress > 0.78:
        impact_progress = min(
            1,
            (progress - 0.78) / 0.22,
        )
        impact_visibility = math.sin(
            math.pi * impact_progress
        )
        pygame.draw.circle(
            effect_surface,
            (
                205,
                75,
                255,
                round(190 * impact_visibility),
            ),
            destination,
            round(7 + impact_progress * 13),
            width=2,
        )

    surface.blit(effect_surface, (0, 0))


def _draw_assassin_slash_particles(
    surface,
    position,
    progress,
    identity_seed,
    strike_index,
):
    particle_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    center = ACT_THREE_TILE_SIZE // 2
    visibility = math.sin(math.pi * progress)
    alpha = round(245 * visibility)
    slash_patterns = (
        ((-1.10, 25, -5), (-0.28, 19, 4), (0.62, 22, 0)),
        ((-0.55, 22, -7), (0.38, 28, 4), (1.18, 18, 1)),
        ((-1.38, 18, 3), (-0.72, 27, -4), (0.20, 24, 5)),
        ((-0.92, 29, 5), (0.02, 18, -5), (0.82, 26, 2)),
        ((-0.35, 20, -4), (0.56, 25, 5), (1.36, 19, -1)),
    )
    slash_pattern = slash_patterns[strike_index % len(slash_patterns)]
    for slash_index, (base_angle, length, offset) in enumerate(
        slash_pattern
    ):
        angle = (
            base_angle
            + math.sin(progress * math.tau + slash_index) * 0.16
            + (identity_seed % 11) * 0.01
        )
        bend = 5 + slash_index * 2
        start = (
            round(center + math.cos(angle) * offset - math.cos(angle) * length / 2),
            round(center + math.sin(angle) * offset - math.sin(angle) * length / 2),
        )
        end = (
            round(center + math.cos(angle) * offset + math.cos(angle) * length / 2),
            round(center + math.sin(angle) * offset + math.sin(angle) * length / 2),
        )
        middle = (
            round((start[0] + end[0]) / 2 - math.sin(angle) * bend),
            round((start[1] + end[1]) / 2 + math.cos(angle) * bend),
        )
        pygame.draw.line(
            particle_surface,
            (65, 145, 255, alpha // 3),
            start,
            middle,
            width=8,
        )
        pygame.draw.line(
            particle_surface,
            (65, 145, 255, alpha // 3),
            middle,
            end,
            width=8,
        )
        pygame.draw.line(
            particle_surface,
            (185, 230, 255, alpha),
            start,
            middle,
            width=2,
        )
        pygame.draw.line(
            particle_surface,
            (220, 245, 255, alpha),
            middle,
            end,
            width=2,
        )
        for shard_index, shard_side in enumerate((-1, 1)):
            shard_origin = (
                end[0] + round(math.cos(angle + math.pi / 2) * shard_side * 4),
                end[1] + round(math.sin(angle + math.pi / 2) * shard_side * 4),
            )
            shard_end = (
                shard_origin[0] + round(math.cos(angle + shard_side) * (5 + shard_index * 2)),
                shard_origin[1] + round(math.sin(angle + shard_side) * (5 + shard_index * 2)),
            )
            pygame.draw.line(
                particle_surface,
                (125, 205, 255, alpha),
                shard_origin,
                shard_end,
                width=2,
            )
    surface.blit(particle_surface, position)
