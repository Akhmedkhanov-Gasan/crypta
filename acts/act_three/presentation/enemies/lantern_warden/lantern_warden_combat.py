import math

import pygame

from .lantern_warden_animation import (
    WARDEN_ATTACK_DURATION_MS,
    WARDEN_ATTACK_IMPACT_MS,
    WARDEN_HURT_DURATION_MS,
    WARDEN_DEATH_IMPACT_MS,
    WARDEN_DEATH_EFFECT_DURATION_MS,
)
from .lantern_warden_effects import (
    WARDEN_FIREFLY_COLOR,
    WARDEN_FIREFLY_CORE_COLOR,
    _draw_fireflies,
    _firefly_texture,
    _fog_puff,
    _unit,
)


WARDEN_COMBAT_SHADOW = (9, 12, 6)
WARDEN_COMBAT_SMOKE = (66, 76, 37)
WARDEN_COMBAT_GROUND = (24, 31, 11)
WARDEN_COMBAT_MOSS = (82, 101, 31)


def _target_angle(enemy, target):
    center_column = (
        enemy.column
        + (enemy.footprint_width - 1) / 2
    )
    center_row = (
        enemy.row
        + (enemy.footprint_height - 1) / 2
    )
    return math.atan2(
        target[1] - center_row,
        target[0] - center_column,
    )


def _draw_combat_smoke(surface, center, radius, opacity):
    radius = max(3, round(radius))
    opacity = max(0, min(255, round(opacity)))

    if opacity == 0:
        return

    edge = _fog_puff(
        radius,
        WARDEN_COMBAT_SMOKE,
    ).copy()
    edge.set_alpha(opacity)

    surface.blit(
        edge,
        edge.get_rect(
            center=(
                round(center[0]),
                round(center[1]),
            )
        ),
    )

    core = _fog_puff(
        max(2, round(radius * 0.83)),
        WARDEN_COMBAT_SHADOW,
    ).copy()
    core.set_alpha(opacity)

    surface.blit(
        core,
        core.get_rect(
            center=(
                round(center[0] + radius * 0.13),
                round(center[1] + radius * 0.10),
            )
        ),
    )


def _ragged_ground(size, seed, current_time, strength=1.0):
    size = max(8, round(size))
    strength = max(0.0, min(1.0, strength))
    marker = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )
    perimeter = []

    for side in range(4):
        for index in range(9):
            along = 3 + (size - 7) * index / 8
            inset = 2 + _unit(seed, side * 17 + index) * 4

            if side == 0:
                point = (along, inset)
            elif side == 1:
                point = (size - 1 - inset, along)
            elif side == 2:
                point = (size - 1 - along, size - 1 - inset)
            else:
                point = (inset, size - 1 - along)

            perimeter.append(tuple(round(value) for value in point))

    pygame.draw.polygon(
        marker,
        (29, 7, 16, round(145 * strength)),
        perimeter,
    )

    phase = current_time / 1500

    for index in range(9):
        x = size * (0.14 + _unit(seed, index + 101) * 0.72)
        y = size * (0.14 + _unit(seed, index + 121) * 0.72)
        x += math.sin(phase * 0.73 + index * 1.9) * size * 0.045
        y += math.cos(phase * 0.61 + index * 2.3) * size * 0.045
        radius = size * (
            0.17 + _unit(seed, index + 141) * 0.13
        )
        opacity = (
            165
            + 30 * math.sin(phase + index * 1.7)
        ) * strength

        _draw_combat_smoke(
            marker,
            (x, y),
            radius,
            opacity,
        )

    for index in range(3):
        points = []

        for step in range(6):
            points.append(
                (
                    round(size * (0.12 + step * 0.15)),
                    round(
                        size * (
                            0.24
                            + index * 0.24
                            + (
                                _unit(seed, 201 + index * 13 + step)
                                - 0.5
                            ) * 0.18
                        )
                    ),
                )
            )

        pygame.draw.lines(
            marker,
            (11, 4, 10, round(225 * strength)),
            False,
            points,
            5,
        )
        pygame.draw.lines(
            marker,
            (132, 39, 53, round(175 * strength)),
            False,
            points,
            2,
        )

    pygame.draw.lines(
        marker,
        (157, 48, 61, round(230 * strength)),
        True,
        perimeter,
        2,
    )

    return marker


def _draw_torn_sweep(
    effect,
    center,
    sprite_size,
    angle,
    sweep,
    seed,
):
    strength = math.sin(math.pi * sweep) ** 0.45
    head = angle - 0.95 + sweep * 1.90
    span = 1.25 * strength
    tail = head - span

    def point(point_angle, radius):
        return (
            round(center + math.cos(point_angle) * radius),
            round(center + math.sin(point_angle) * radius),
        )

    for index in range(13):
        along = index / 12
        smoke_angle = tail + span * along
        radius = sprite_size * (
            0.67 + _unit(seed, index + 501) * 0.10
        )
        drift = (
            sprite_size
            * 0.08
            * sweep
            * (1 - along)
        )

        _draw_combat_smoke(
            effect,
            point(smoke_angle, radius + drift),
            sprite_size * (
                0.04 + _unit(seed, index + 521) * 0.045
            ),
            165 * strength,
        )

    for index in range(9):
        slot_start = index / 9
        slot_end = (index + 1) / 9
        gap = 0.012 + _unit(seed, index + 541) * 0.022
        start = tail + span * (slot_start + gap)
        end = tail + span * (slot_end - gap)
        outer = []
        inner = []

        width_factor = (
            0.65 + _unit(seed, index + 561) * 0.65
        )

        for step in range(7):
            along = step / 6
            point_angle = start + (end - start) * along
            tooth = _unit(seed, 601 + index * 11 + step)
            taper = math.sin(math.pi * along) ** 0.6
            radius = sprite_size * (
                0.69 + tooth * 0.045
            )

            if step == 4:
                radius += sprite_size * (
                    0.04 + _unit(seed, index + 701) * 0.045
                ) * strength

            thickness = (
                sprite_size
                * 0.14
                * width_factor
                * taper
                * strength
            )
            outer.append(point(point_angle, radius))
            inner.append(
                point(
                    point_angle,
                    radius - thickness,
                )
            )

        polygon = outer + list(reversed(inner))

        pygame.draw.polygon(
            effect,
            (*WARDEN_COMBAT_SHADOW, round(235 * strength)),
            polygon,
        )
        pygame.draw.polygon(
            effect,
            (*WARDEN_COMBAT_MOSS, round(155 * strength)),
            polygon,
        )
        pygame.draw.lines(
            effect,
            (*WARDEN_COMBAT_SHADOW, round(245 * strength)),
            False,
            inner,
            3,
        )
        pygame.draw.lines(
            effect,
            (*WARDEN_FIREFLY_COLOR, round(215 * strength)),
            False,
            outer[2:6],
            2,
        )

        if index % 3 == 1:
            pygame.draw.line(
                effect,
                (
                    *WARDEN_FIREFLY_CORE_COLOR,
                    round(225 * strength),
                ),
                outer[3],
                outer[4],
                1,
            )

        fragment_angle = end + span * 0.015
        fragment_radius = sprite_size * (
            0.76
            + sweep * 0.035
            + _unit(seed, index + 741) * 0.035
        )
        fragment = [
            point(fragment_angle, fragment_radius),
            point(
                fragment_angle - 0.025,
                fragment_radius - sprite_size * 0.055,
            ),
            point(
                fragment_angle + 0.012,
                fragment_radius - sprite_size * 0.025,
            ),
        ]
        pygame.draw.polygon(
            effect,
            (*WARDEN_COMBAT_MOSS, round(185 * strength)),
            fragment,
        )


def _draw_attack_arc(
    surface,
    position,
    sprite_size,
    enemy,
    elapsed,
):
    targets = enemy.attack_effect_positions
    target_center = (
        sum(cell[0] for cell in targets) / len(targets),
        sum(cell[1] for cell in targets) / len(targets),
    )
    angle = _target_angle(enemy, target_center)
    tile_size = sprite_size / 2
    canvas_size = round(sprite_size * 3)
    effect = pygame.Surface(
        (canvas_size, canvas_size),
        pygame.SRCALPHA,
    )
    center = canvas_size / 2
    offset = center - sprite_size / 2
    sweep_start = WARDEN_ATTACK_IMPACT_MS * 0.35
    sweep_duration = WARDEN_ATTACK_IMPACT_MS * 1.25
    sweep = (elapsed - sweep_start) / max(1, sweep_duration)

    if 0 < sweep < 1:
        _draw_torn_sweep(
            effect,
            center,
            sprite_size,
            angle,
            sweep,
            int(enemy.attack_animation_started_at),
        )

    impact_duration = max(
        1,
        WARDEN_ATTACK_DURATION_MS - WARDEN_ATTACK_IMPACT_MS,
    )
    impact = (
        elapsed - WARDEN_ATTACK_IMPACT_MS
    ) / impact_duration

    if 0 <= impact < 1:
        fade = (1 - impact) ** 1.5

        for cell_index, (column, row) in enumerate(targets):
            left = offset + (column - enemy.column) * tile_size
            top = offset + (row - enemy.row) * tile_size
            ground_seed = column * 73856093 ^ row * 19349663
            ground = _ragged_ground(
                tile_size,
                ground_seed,
                enemy.attack_animation_started_at + elapsed,
                fade,
            )
            effect.blit(
                ground,
                (round(left), round(top)),
            )

            for smoke_index in range(5):
                smoke_angle = (
                    _unit(ground_seed, smoke_index + 401)
                    * math.tau
                )
                distance = tile_size * (
                    0.08 + impact * 0.28
                )
                smoke_center = (
                    left
                    + tile_size / 2
                    + math.cos(smoke_angle) * distance,
                    top
                    + tile_size / 2
                    + math.sin(smoke_angle) * distance
                    - impact * tile_size * 0.10,
                )

                _draw_combat_smoke(
                    effect,
                    smoke_center,
                    tile_size * (0.12 + impact * 0.10),
                    200 * fade,
                )

            seed = (
                int(enemy.attack_animation_started_at)
                + cell_index * 7919
            )
            center_x = left + tile_size / 2
            center_y = top + tile_size / 2

            for index in range(6):
                direction = _unit(seed, index + 1) * math.tau
                length = tile_size * (
                    0.20 + _unit(seed, index + 11) * 0.22
                )
                endpoint = (
                    center_x + math.cos(direction) * length,
                    center_y + math.sin(direction) * length,
                )
                midpoint = (
                    center_x
                    + math.cos(direction + 0.22) * length * 0.53,
                    center_y
                    + math.sin(direction + 0.22) * length * 0.53,
                )
                points = [
                    (round(center_x), round(center_y)),
                    (round(midpoint[0]), round(midpoint[1])),
                    (round(endpoint[0]), round(endpoint[1])),
                ]
                pygame.draw.lines(
                    effect,
                    (12, 7, 14, round(240 * fade)),
                    False,
                    points,
                    5,
                )
                pygame.draw.lines(
                    effect,
                    (127, 48, 49, round(190 * fade)),
                    False,
                    points,
                    2,
                )

                travel = length * (0.35 + impact * 0.65)
                shard_x = center_x + math.cos(direction) * travel
                shard_y = (
                    center_y
                    + math.sin(direction) * travel
                    - math.sin(math.pi * impact) * tile_size * 0.12
                )
                radius = max(1, round(3 * (1 - impact)))
                pygame.draw.polygon(
                    effect,
                    (95, 87, 74, round(220 * fade)),
                    [
                        (round(shard_x), round(shard_y - radius * 2)),
                        (round(shard_x + radius), round(shard_y)),
                        (round(shard_x), round(shard_y + radius)),
                        (round(shard_x - radius), round(shard_y)),
                    ],
                )

    surface.blit(
        effect,
        (
            round(position[0] - offset),
            round(position[1] - offset),
        ),
    )


def _draw_dark_hit(
    surface,
    position,
    sprite_size,
    sprite,
    enemy,
    elapsed,
):
    progress = elapsed / WARDEN_HURT_DURATION_MS
    envelope = math.sin(math.pi * progress)

    dark_sprite = sprite.copy()
    dark_sprite.fill(
        (38, 28, 43, 255),
        special_flags=pygame.BLEND_RGBA_MULT,
    )
    dark_sprite.set_alpha(round(135 * envelope))
    surface.blit(dark_sprite, position)

    source_angle = (
        _target_angle(enemy, enemy.hit_origin)
        if enemy.hit_origin is not None
        else -math.pi / 2
    )
    impact = (
        position[0]
        + sprite_size * 0.5
        + math.cos(source_angle) * sprite_size * 0.20,
        position[1]
        + sprite_size * 0.48
        + math.sin(source_angle) * sprite_size * 0.20,
    )
    seed = int(enemy.hit_animation_started_at)

    for index in range(7):
        angle = (
            source_angle
            + (_unit(seed, index + 1) - 0.5) * 2.6
        )
        distance = sprite_size * (
            0.025
            + progress * (
                0.13 + _unit(seed, index + 21) * 0.12
            )
        )
        center = (
            impact[0] + math.cos(angle) * distance,
            impact[1]
            + math.sin(angle) * distance
            - progress * sprite_size * 0.09,
        )
        radius = max(
            3,
            round(sprite_size * (0.045 + progress * 0.045)),
        )
        color = (
            (59, 18, 32)
            if index % 3 == 0
            else (13, 11, 20)
        )
        smoke = _fog_puff(radius, color).copy()
        smoke.set_alpha(round(215 * envelope))

        surface.blit(
            smoke,
            smoke.get_rect(
                center=(
                    round(center[0]),
                    round(center[1]),
                )
            ),
        )


def draw_warden_combat_effects(
    surface,
    position,
    sprite_size,
    sprite,
    enemy,
    current_time,
    action,
):
    attack_elapsed = current_time - enemy.attack_animation_started_at

    if (
        action == "attack"
        and enemy.attack_effect_positions
        and 0 <= attack_elapsed < WARDEN_ATTACK_DURATION_MS
    ):
        _draw_attack_arc(
            surface,
            position,
            sprite_size,
            enemy,
            attack_elapsed,
        )

    hurt_elapsed = current_time - enemy.hit_animation_started_at

    if (
        enemy.hit_damage > 0
        and not enemy.hit_dodged
        and enemy.hit_animation_started_at >= 0
        and 0 <= hurt_elapsed < WARDEN_HURT_DURATION_MS
    ):
        _draw_dark_hit(
            surface,
            position,
            sprite_size,
            sprite,
            enemy,
            hurt_elapsed,
        )


def draw_warden_telegraph(context, enemy, current_time, tile_size):
    for column, row in enemy.attack_targets:
        if (column, row) not in context.floor.visible_cells:
            continue

        seed = column * 73856093 ^ row * 19349663
        marker = _ragged_ground(
            tile_size,
            seed,
            current_time,
        )

        context.view_surface.blit(
            marker,
            (
                column * tile_size - context.camera_x,
                row * tile_size - context.camera_y,
            ),
        )


def draw_warden_death_effects(
    surface,
    position,
    sprite_size,
    enemy,
    current_time,
    identity_seed,
    *,
    foreground=False,
):
    started_at = enemy.death_animation_started_at

    if started_at < 0:
        return

    elapsed = current_time - started_at

    if not 0 <= elapsed < WARDEN_DEATH_EFFECT_DURATION_MS:
        return

    presence_strength = max(
        0.0,
        1.0 - elapsed / 1300,
    ) ** 1.5

    if presence_strength > 0:
        _draw_fireflies(
            surface,
            position,
            sprite_size,
            started_at,
            identity_seed,
            foreground,
            strength=presence_strength,
        )

    impact_elapsed = elapsed - WARDEN_DEATH_IMPACT_MS

    if impact_elapsed < 0:
        return

    duration = (
        WARDEN_DEATH_EFFECT_DURATION_MS
        - WARDEN_DEATH_IMPACT_MS
    )
    progress = min(1.0, impact_elapsed / duration)
    emergence = min(1.0, impact_elapsed / 100)
    fade = emergence * (1 - progress) ** 1.6
    spread = 1 - (1 - progress) ** 3
    seed = identity_seed ^ int(started_at)

    center_x = position[0] + sprite_size * 0.5
    ground_y = position[1] + sprite_size * 0.82

    for index in range(10):
        angle = index * math.tau / 10
        is_front = math.sin(angle) >= 0

        if is_front != foreground:
            continue

        irregularity = 0.85 + _unit(seed, index + 801) * 0.30
        center = (
            center_x
            + math.cos(angle)
            * sprite_size
            * (0.12 + spread * 0.38)
            * irregularity,
            ground_y
            + math.sin(angle)
            * sprite_size
            * (0.025 + spread * 0.10)
            - progress * sprite_size * 0.045,
        )
        radius = sprite_size * (
            0.08
            + progress * 0.065
            + _unit(seed, index + 821) * 0.025
        )

        _draw_combat_smoke(
            surface,
            center,
            radius,
            220 * fade * (0.72 if foreground else 1.0),
        )

    if not foreground:
        return

    for index in range(8):
        delay = _unit(seed, index + 841) * 260
        age = impact_elapsed - delay
        lifetime = 850 + _unit(seed, index + 861) * 650

        if not 0 <= age < lifetime:
            continue

        particle_progress = age / lifetime
        brightness = (
            min(1.0, age / 100)
            * (1 - particle_progress) ** 1.8
        )
        side = _unit(seed, index + 881) * 2 - 1
        particle_position = (
            center_x
            + side * sprite_size * (
                0.10 + particle_progress * 0.25
            ),
            ground_y
            - sprite_size * 0.13
            - particle_progress * sprite_size * (
                0.20 + _unit(seed, index + 901) * 0.18
            ),
        )

        glow = _firefly_texture(3 + index % 2).copy()
        weight = max(0, min(255, round(190 * brightness)))
        glow.fill(
            (weight, weight, weight),
            special_flags=pygame.BLEND_RGB_MULT,
        )
        surface.blit(
            glow,
            glow.get_rect(
                center=(
                    round(particle_position[0]),
                    round(particle_position[1]),
                )
            ),
            special_flags=pygame.BLEND_RGB_ADD,
        )
