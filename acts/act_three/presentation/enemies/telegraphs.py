import math

import pygame

from acts.act_three.presentation.enemies.telegraph_art import (
    attacker_badge,
    direction_marker,
    ground_marker,
    shield_bash_sweep,
    sigil_marker,
    threat_band,
)
from acts.act_three.presentation.enemies.telegraph_layout import TelegraphLayout
from acts.act_three.presentation.view import _view_position
from presentation.layout import ACT_THREE_TILE_SIZE


_LAYOUT = TelegraphLayout()


def _animation_frame(current_time):
    return int(current_time // 80) % 32


def _center(context, cell):
    position = _view_position(*cell, context.camera_x, context.camera_y)
    half = ACT_THREE_TILE_SIZE / 2
    return pygame.Vector2(position[0] + half, position[1] + half)


def draw_attack_direction(
    surface, source, destination, tile_size, current_time, enemy_type, lane=0, emphasis=False,
):
    direction = pygame.Vector2(destination) - pygame.Vector2(source)
    if direction.length_squared() == 0:
        return
    direction = direction.normalize()
    side = pygame.Vector2(-direction.y, direction.x)
    offset = (0, -0.18, 0.18, -0.32, 0.32)[min(lane, 4)] * tile_size
    center = pygame.Vector2(destination) + side * offset
    marker = direction_marker(tile_size, enemy_type, _animation_frame(current_time), emphasis)
    angle = math.degrees(math.atan2(direction.x, direction.y))
    marker = pygame.transform.rotozoom(marker, angle, 1)
    surface.blit(marker, marker.get_rect(center=(round(center.x), round(center.y))))


def _draw_bash_sweep(context, threat, frame):
    enemy = threat.enemy
    source = _center(context, (enemy.column, enemy.row))
    destination = _center(context, threat.target)
    delta = destination - source
    if not delta.length_squared():
        return
    marker = shield_bash_sweep(ACT_THREE_TILE_SIZE, frame)
    if abs(delta.length() - ACT_THREE_TILE_SIZE) > 1:
        marker = pygame.transform.smoothscale(
            marker, (marker.get_width(), round(marker.get_height() * delta.length() / ACT_THREE_TILE_SIZE)),
        )
    marker = pygame.transform.rotozoom(marker, math.degrees(math.atan2(delta.x, delta.y)), 1)
    marker.set_alpha(threat.opacity)
    middle = (source + destination) / 2
    context.view_surface.blit(marker, marker.get_rect(center=(round(middle.x), round(middle.y))))


def draw_enemy_attack_markers(context, current_time):
    by_cell = _LAYOUT.sample(context.floor, current_time)
    frame = _animation_frame(current_time)
    size = ACT_THREE_TILE_SIZE
    for cell, threats in by_cell.items():
        position = _view_position(*cell, context.camera_x, context.camera_y)
        if not context.view_surface.get_rect().colliderect((*position, size, size)):
            continue
        context.view_surface.blit(ground_marker(size, min(4, len(threats))), position)
        for threat in threats:
            enemy = threat.enemy
            if enemy.type == "sentinel" and enemy.prepared_attack_mode == "shield_bash":
                _draw_bash_sweep(context, threat, frame)
            angle_step = round(threat.source_angle * 96 / math.tau) % 96
            band = threat_band(size, enemy.type, frame, round(threat.radius * 500), angle_step).copy()
            band.set_alpha(threat.opacity)
            context.view_surface.blit(band, position)
        if len(threats) == 1:
            enemy = threats[0].enemy
            glyph = sigil_marker(size, enemy.type, enemy.prepared_attack_mode, frame, 0).copy()
            glyph.set_alpha(threats[0].opacity)
            context.view_surface.blit(glyph, position)


def _draw_badge(surface, center, threat, frame, size):
    enemy = threat.enemy
    badge = attacker_badge(size, enemy.type, enemy.prepared_attack_mode, frame).copy()
    badge.set_alpha(threat.opacity)
    surface.blit(badge, badge.get_rect(center=(round(center.x), round(center.y))))


def draw_enemy_attack_directions(context, current_time):
    by_cell = _LAYOUT.sample(context.floor, current_time)
    frame = _animation_frame(current_time)
    size = ACT_THREE_TILE_SIZE
    player_cell = (context.floor.player_column, context.floor.player_row)
    for cell, threats in by_cell.items():
        destination = _center(context, cell)
        for index, threat in enumerate(threats):
            enemy = threat.enemy
            source_cell = (enemy.column, enemy.row)
            source = _center(context, source_cell)
            if cell == player_cell and len(threats) > 1:
                radial = pygame.Vector2(math.cos(threat.badge_angle), math.sin(threat.badge_angle))
                _draw_badge(context.view_surface, destination + radial * size * threat.radius,
                            threat, frame, round(size * 0.3))
            bash = enemy.type == "sentinel" and enemy.prepared_attack_mode == "shield_bash"
            if enemy.prepared_attack_mode in ("ranged", "magic") or bash:
                draw_attack_direction(
                    context.view_surface, source, destination, size, current_time,
                    enemy.type, index, emphasis=bash,
                )
