import math

import pygame

from acts.act_three.abilities.greater_manifestation import (
    MANIFESTATION_DEATH_MS, MANIFESTATION_SUMMON_MS, MANIFESTATION_MOVE_MS,
    MANIFESTATION_ATTACK_MS, MANIFESTATION_HURT_MS, MANIFESTATION_IDLE_FRAME_MS,
)
from acts.act_three.presentation.summoner.true_form_effects import draw_summoner_true_form_attack_effect
from acts.act_three.presentation.summoner.soul_devourer_effects import draw_soul_devourer_aura, draw_soul_feast
from presentation.layout import ACT_THREE_TILE_SIZE


def _spirit_aura(surface, position, spirit, now):
    margin = 42
    size = ACT_THREE_TILE_SIZE + margin * 2
    glow = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    souls = spirit["souls"]
    intensity = 1 - math.exp(-souls / 4)
    pulse = 0.5 + 0.5 * math.sin(now / 720)
    radius = 25 + round(intensity * 13)
    color = (87 + round(intensity * 85), 212, 216 + round(intensity * 35))
    count = 3 + min(7, souls)
    for index in range(count):
        phase = now / (4100 - intensity * 1200) + index * math.tau / count
        x = cx + round(math.cos(phase) * radius)
        y = cy + round(math.sin(phase) * radius * 0.65)
        alpha = round(75 + intensity * 70 + pulse * 25)
        pygame.draw.circle(glow, (*color, alpha // 6), (x, y), 7)
        pygame.draw.arc(glow, (*color, alpha), (x - 3, y - 4, 7, 9), 0.4, 5.2, 1)
        pygame.draw.circle(glow, (205, 255, 249, alpha), (x, y), 1)
    for index in range(2 + round(intensity * 3)):
        rect = pygame.Rect(cx - radius - index * 3, cy + 19 - index, (radius + index * 3) * 2, 18 + index * 2)
        angle = now / 2100 + index * 1.7
        pygame.draw.arc(glow, (*color, round(65 + intensity * 70)), rect, angle, angle + 1.8, 1)
    surge = now - spirit["soul_at"]
    summon = now - spirit["summoned_at"]
    elapsed = surge if 0 <= surge < 900 else summon
    if 0 <= elapsed < 900:
        progress = elapsed / 900
        ring = 12 + round(progress * 42)
        pygame.draw.ellipse(glow, (*color, round(180 * math.sin(progress * math.pi))),
                            (cx - ring, cy + 22 - ring // 3, ring * 2, max(2, ring * 2 // 3)), 2)
    surface.blit(glow, (position[0] - margin, position[1] - margin))


def draw_manifestation(surface, assets, game_state, camera_x, camera_y, now):
    spirit = game_state.player.act_three.summoner_manifestation
    if spirit is None or spirit["floor"] != game_state.floor_index:
        return
    dead = spirit["health"] <= 0
    if dead and not 0 <= now - spirit["death_at"] < MANIFESTATION_DEATH_MS:
        return
    tile = ACT_THREE_TILE_SIZE
    position = (round(spirit["position"][0] * tile - camera_x), round(spirit["position"][1] * tile - camera_y))
    moving = spirit["origin"] is not None and 0 <= now - spirit["move_at"] < MANIFESTATION_MOVE_MS
    if moving and not dead:
        progress = (now - spirit["move_at"]) / MANIFESTATION_MOVE_MS
        progress = progress * progress * (3 - 2 * progress)
        position = tuple(round((spirit["origin"][axis] + (spirit["position"][axis] - spirit["origin"][axis]) * progress) * tile
                               - (camera_x if axis == 0 else camera_y)) for axis in range(2))
    animation, frame = "idle", (now // MANIFESTATION_IDLE_FRAME_MS) % 8
    if dead:
        animation, frame = "death", min(7, (now - spirit["death_at"]) * 8 // MANIFESTATION_DEATH_MS)
    elif 0 <= now - spirit["summoned_at"] < MANIFESTATION_SUMMON_MS:
        animation, frame = "summon", min(7, (now - spirit["summoned_at"]) * 8 // MANIFESTATION_SUMMON_MS)
    elif 0 <= now - spirit["attack_at"] < MANIFESTATION_ATTACK_MS:
        animation, frame = "attack", min(7, (now - spirit["attack_at"]) * 8 // MANIFESTATION_ATTACK_MS)
    elif 0 <= now - spirit["hurt_at"] < MANIFESTATION_HURT_MS:
        animation, frame = "hurt", min(7, (now - spirit["hurt_at"]) * 8 // MANIFESTATION_HURT_MS)
    elif moving:
        animation, frame = "walk", min(7, (now - spirit["move_at"]) * 8 // MANIFESTATION_MOVE_MS)
    if not dead:
        _spirit_aura(surface, position, spirit, now)
        draw_soul_devourer_aura(surface, position, spirit, now)
    key = f"summoner_true_form_transform_{frame}" if animation == "summon" else f"summoner_true_form_{animation}_{spirit['direction']}_{frame}"
    surface.blit(assets[key], position)
    if dead:
        return
    draw_soul_feast(surface, position, spirit, camera_x, camera_y, now)
    width = 34
    bar = pygame.Rect(position[0] + (tile - width) // 2, position[1] - 5, width, 3)
    pygame.draw.rect(surface, (23, 30, 35), bar)
    pygame.draw.rect(surface, (87, 220, 209), (bar.x, bar.y, round(width * spirit["health"] / spirit["max_health"]), bar.height))
    if spirit["target"] is not None and 0 <= now - spirit["attack_at"] < MANIFESTATION_ATTACK_MS:
        target = (round(spirit["target"][0] * tile - camera_x), round(spirit["target"][1] * tile - camera_y))
        draw_summoner_true_form_attack_effect(surface, position, target, now, spirit["attack_at"])
