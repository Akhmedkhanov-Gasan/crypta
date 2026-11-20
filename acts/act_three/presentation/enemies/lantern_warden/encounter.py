import math

import pygame

from acts.act_three.enemies.lantern_warden.encounter import (
    AWAKEN_START_MS, AWAKEN_END_MS, encounter_dialogue,
)
from acts.act_three.presentation.enemies.lantern_warden.lantern_warden_animation import WARDEN_ATTACK_IMPACT_MS
from acts.act_three.presentation.enemies.lantern_warden.lantern_warden_effects import _fog_puff, _firefly_texture
from acts.act_three.presentation.dialogue_panel import draw_dialogue_panel
from acts.act_three.presentation.enemies.lantern_warden.soul_procession import draw_soul_procession
from presentation.layout import ACT_THREE_TILE_SIZE


def camera_shake(floor, current_time):
    strength = 0.0
    phase = 0
    if floor.lantern_encounter is not None and floor.lantern_encounter["phase"] == "awakening":
        elapsed = current_time - floor.lantern_encounter["started_at"] - 2100
        if 0 <= elapsed < 650:
            strength = 4.5 * (1 - elapsed / 650)
            phase = elapsed
    for enemy in floor.enemies:
        if enemy.type != "lantern_warden" or not enemy.attack_effect_positions:
            continue
        elapsed = current_time - enemy.attack_animation_started_at - WARDEN_ATTACK_IMPACT_MS
        if 0 <= elapsed < 360:
            amplitude = 5 if enemy.attack_effect_mode == "cinder_nova" else 3
            strength = max(strength, amplitude * (1 - elapsed / 360) ** 2)
            phase = elapsed
    return round(math.sin(phase * 0.081) * strength), round(math.cos(phase * 0.097) * strength * 0.7)


def draw_sleeping_warden(context, assets, current_time):
    encounter = context.floor.lantern_encounter
    if encounter is None or encounter["phase"] not in ("sleeping", "entry_dialogue", "awakening"):
        return
    x, y = encounter["position"]
    if encounter["phase"] != "awakening" and not any(
        (x + dx, y + dy) in context.floor.visible_cells for dx in range(2) for dy in range(2)
    ):
        return
    elapsed = current_time - encounter["started_at"] if encounter["phase"] == "awakening" else 0
    progress = min(1.0, max(0.0, (elapsed - AWAKEN_START_MS) / (AWAKEN_END_MS - AWAKEN_START_MS)))
    frame = min(7, int(progress * 8))
    position = (round(x * ACT_THREE_TILE_SIZE - context.camera_x), round(y * ACT_THREE_TILE_SIZE - context.camera_y))
    sprite = assets[f"enemy_lantern_warden_awaken_{frame}"]
    if elapsed >= AWAKEN_END_MS:
        idle = assets["enemy_lantern_warden_idle_down_0"]
        blend = min(1.0, (elapsed - AWAKEN_END_MS) / 300)
        sprite = sprite.copy()
        incoming = idle.copy()
        incoming.set_alpha(round(blend * 255))
        sprite.blit(incoming, (0, 0))
    context.view_surface.blit(sprite, position)
    if encounter["phase"] != "awakening":
        return
    intensity = math.sin(math.pi * min(1.0, max(0.0, elapsed / 4400)))
    center = (position[0] + ACT_THREE_TILE_SIZE, position[1] + ACT_THREE_TILE_SIZE * 1.65)
    for index in range(18):
        angle = index * math.tau / 18 + elapsed / 3700
        radius = ACT_THREE_TILE_SIZE * (0.4 + progress * 1.3)
        point = (round(center[0] + math.cos(angle) * radius), round(center[1] + math.sin(angle) * radius * 0.38 - progress * 16))
        mist = _fog_puff(22 + index % 4 * 3, (58, 66, 29)).copy()
        mist.set_alpha(round(150 * intensity))
        context.view_surface.blit(mist, mist.get_rect(center=point))
        glow = _firefly_texture(4).copy()
        weight = round(255 * intensity)
        glow.fill((weight, weight, weight), special_flags=pygame.BLEND_RGB_MULT)
        point = (point[0], point[1] - round((elapsed / 12 + index * 13) % 90))
        context.view_surface.blit(glow, glow.get_rect(center=point), special_flags=pygame.BLEND_RGB_ADD)


def draw_ability_impacts(context, current_time):
    size = ACT_THREE_TILE_SIZE
    for enemy in context.floor.enemies:
        if enemy.type == "lantern_warden":
            draw_soul_procession(context, enemy, current_time)
        if enemy.type != "lantern_warden" or not enemy.attack_effect_positions:
            continue
        elapsed = current_time - enemy.attack_animation_started_at - WARDEN_ATTACK_IMPACT_MS
        if not 0 <= elapsed < 800:
            continue
        progress = elapsed / 800
        color = (185, 204, 83) if enemy.attack_effect_mode in ("soul_lance", "soul_procession") else (214, 138, 57)
        for index, (x, y) in enumerate(enemy.attack_effect_positions):
            if (x, y) not in context.floor.visible_cells:
                continue
            center = (round((x + 0.5) * size - context.camera_x), round((y + 0.65) * size - context.camera_y))
            effect = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            radius = round(size * (0.12 + progress * 0.5))
            alpha = round(210 * (1 - progress) ** 1.4)
            pygame.draw.ellipse(effect, (*color, alpha), (size - radius, size - radius * 0.4, radius * 2, radius * 0.8), 2)
            if enemy.attack_effect_mode == "soul_lance":
                height = round(size * math.sin(math.pi * progress) * 0.9)
                pygame.draw.polygon(effect, (119, 146, 46, alpha), (
                    (size - 12, size + 4), (size - 7, size - height // 2),
                    (size, size - height), (size + 8, size - height // 3),
                    (size + 12, size + 4),
                ))
                pygame.draw.line(effect, (236, 238, 159, alpha), (size, size), (size, size - height), 3)
            for spark in range(7):
                phase = spark * math.tau / 7 + index * 1.7
                distance = size * progress * (0.25 + spark % 3 * 0.12)
                sx = round(size + math.cos(phase) * distance)
                sy = round(size + math.sin(phase) * distance * 0.35 - math.sin(progress * math.pi) * size * 0.65)
                pygame.draw.line(effect, (*color, alpha), (sx, sy), (sx, sy + 3 + spark % 4), 2)
            context.view_surface.blit(effect, (center[0] - size, center[1] - size))
        if enemy.attack_effect_mode == "cinder_nova":
            ring = pygame.Surface(context.view_surface.get_size(), pygame.SRCALPHA)
            center = (round((enemy.column + 1) * size - context.camera_x), round((enemy.row + 1) * size - context.camera_y))
            radius = round(size * (0.6 + progress * 1.6))
            pygame.draw.ellipse(ring, (209, 192, 78, round(190 * (1 - progress))), (center[0] - radius, center[1] - radius * 0.5, radius * 2, radius), 3)
            context.view_surface.blit(ring, (0, 0))


def draw_encounter_dialogue(screen, game_state, fonts):
    if game_state.player.health <= 0:
        return
    line = encounter_dialogue(game_state)
    if line is None:
        return
    speaker_id, message = line
    draw_dialogue_panel(
        screen, fonts, speaker_id, text=message,
        close_label="SPACE / CLICK - CONTINUE",
    )
