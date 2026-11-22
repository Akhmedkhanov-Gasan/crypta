import math

import pygame

from acts.act_three.combat.archer_aim import archer_shot_direction
from acts.act_three.presentation.view import _view_position
from acts.act_three.abilities.phantom_motion import PHANTOM_MOVE_MS, phantom_position
from acts.act_three.presentation.archer.arrows import draw_arrow_flight, draw_arrow_impact
from acts.act_three.presentation.archer.summon_effect import draw_retinue_summon


def _facing(origin, target):
    return {(1, 0): "right", (-1, 0): "left", (0, 1): "down", (0, -1): "up"}[archer_shot_direction(origin, target)]


def _draw_arrow(effect, start, end, age):
    if 260 <= age < 520:
        draw_arrow_flight(effect, start, end, (age - 260) / 260, phantom=True)
    elif 520 <= age < 620:
        draw_arrow_impact(effect, end, (age - 520) / 100, phantom=True)


def draw_phantom_retinue(surface, assets, game_state, camera_x, camera_y, current_time, tile_size):
    player = game_state.player
    from acts.act_three.presentation.archer.rune_projectiles import draw_rune_projectiles

    draw_rune_projectiles(surface, game_state, camera_x, camera_y, current_time, tile_size)
    if player.subclass != "archer" or player.health <= 0 or not player.act_three.archer_phantoms:
        return
    draw_retinue_summon(surface, game_state, camera_x, camera_y, current_time, tile_size)
    effect = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for phantom in sorted(player.act_three.archer_phantoms, key=lambda ghost: ghost.position[1]):
        fade = 1.0
        if phantom.expired_at >= 0:
            fade = max(0, min(1, 1 - (current_time - phantom.expired_at) / 450))
        if fade <= 0:
            continue
        movement = max(0, min(1, (current_time - phantom.moved_at) / PHANTOM_MOVE_MS))
        if phantom.origin == phantom.position:
            fade *= movement
        position = phantom_position(phantom, current_time)
        if phantom.teleporting:
            visibility = abs(2 * movement - 1) ** 2
        else:
            visibility = 0.9 + 0.1 * abs(2 * movement - 1)
        shot = next((
            shot for shot in phantom.attack_animations
            if shot["started_at"] <= current_time < shot["started_at"] + shot["duration"]
        ), None)
        attacking = shot is not None
        age = (current_time - shot["started_at"]) * 620 / shot["duration"] if attacking else -1
        if attacking:
            position = shot["origin"]
            visibility = 1.0
        travel_started = player.act_three.archer_phantom_travel_started_at
        if travel_started >= 0 and not attacking:
            travel_age = current_time - travel_started
            blend = max(0.0, min(1.0, (travel_age - 220) / 180))
            phase = ((travel_age + phantom.seed % 120) % 500) / 500
            glimpse = max(0.0, 1 - abs(phase - 0.5) / 0.13) ** 2
            visibility *= 1 - blend + blend * (0.025 + glimpse * 0.23)
        elif not attacking:
            travel_ended = player.act_three.archer_phantom_travel_ended_at
            if travel_ended >= 0:
                recovery = max(0.0, min(1.0, (current_time - travel_ended) / 180))
                visibility *= 0.15 + recovery * 0.85
        moving = movement < 1 and phantom.origin != phantom.position
        target = shot["target"] if attacking else (
            phantom.position if moving else (game_state.floor.player_column, game_state.floor.player_row)
        )
        facing = _facing(shot["origin"] if attacking else phantom.origin if moving else phantom.position, target)
        animation = "attack" if attacking else "walk" if moving else "idle"
        frame = min(7, int(max(0, age) * 8 // 460)) if attacking else (current_time // 85 + phantom.seed) % 8
        sprite = assets[f"player_archer_{animation}_{facing}_{frame}"].copy()
        sprite.fill((122, 183, 153), special_flags=pygame.BLEND_RGB_MULT)
        if phantom.mirror:
            sprite = assets[f"player_archer_{animation}_{facing}_{frame}"].copy()
            sprite.fill((185, 207, 221), special_flags=pygame.BLEND_RGB_MULT)
            if phantom.invisibility_turns > 0 and not attacking:
                visibility *= 0.25
        alpha = round((170 + 20 * math.sin(current_time * 0.006 + phantom.seed)) * visibility * fade)
        sprite.set_alpha(alpha)
        x, y = _view_position(*position, camera_x, camera_y)
        for offset in (7, 3):
            echo = sprite.copy()
            echo.set_alpha(alpha // (3 if offset == 3 else 5))
            surface.blit(echo, (round(x - offset), round(y + offset * 0.3)))
        surface.blit(sprite, (round(x), round(y)))
        if attacking:
            sx, sy = _view_position(*shot["origin"], camera_x, camera_y)
            tx, ty = _view_position(*shot["target"], camera_x, camera_y)
            if shot.get("kind") == "piercing" and 220 <= age < 560:
                draw_arrow_flight(effect, (sx + tile_size / 2, sy + tile_size / 2),
                                  (tx + tile_size / 2, ty + tile_size / 2),
                                  (age - 220) / 340, phantom=True, power=2)
            else:
                _draw_arrow(effect, (sx + tile_size / 2, sy + tile_size / 2), (tx + tile_size / 2, ty + tile_size / 2), age)
    surface.blit(effect, (0, 0))
