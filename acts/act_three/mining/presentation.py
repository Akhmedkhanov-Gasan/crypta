import math

import pygame

from acts.act_three.mining.runtime import (
    MINING_EFFECT_MS,
    MINING_REWARD_MS,
    mining_frame,
)
from presentation.layout import ACT_THREE_TILE_SIZE


def mining_sprite(player, assets, current_time):
    frame = mining_frame(player, current_time)
    if frame is None:
        return None

    direction, index = frame
    return assets["assassin_mining_frames"][direction][index]


def draw_world_ores(context, assets):
    for ore in context.floor.act_three_ores:
        if ore["position"] not in context.floor.explored_cells:
            continue

        column, row = ore["position"]
        context.view_surface.blit(
            assets["black_ore_stages"][ore["stage"]],
            (
                column * ACT_THREE_TILE_SIZE - context.camera_x,
                row * ACT_THREE_TILE_SIZE - context.camera_y,
            ),
        )


def draw_mining_feedback(context, game_state, assets, font, current_time):
    surface = context.view_surface
    particles = None

    for effect in game_state.act_three.mining_effects:
        elapsed = current_time - effect["started_at"]
        if (
            effect["floor_index"] != game_state.floor_index
            or not 0 <= elapsed < MINING_EFFECT_MS
        ):
            continue

        if particles is None:
            particles = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        progress = elapsed / MINING_EFFECT_MS
        column, row = effect["position"]
        center_x = (
            column * ACT_THREE_TILE_SIZE
            - context.camera_x
            + ACT_THREE_TILE_SIZE // 2
        )
        center_y = (
            row * ACT_THREE_TILE_SIZE
            - context.camera_y
            + ACT_THREE_TILE_SIZE // 2
        )
        alpha = round(220 * (1 - progress))

        for index in range(9):
            angle = index * 2.399 + effect["seed"] * 0.71
            distance = progress * (13 + index % 4 * 6)
            x = center_x + math.cos(angle) * distance
            y = (
                center_y
                + math.sin(angle) * distance * 0.65
                - math.sin(progress * math.pi) * 10
                + progress * progress * 15
            )
            color = (
                (205, 171, 235, alpha)
                if index % 3 == 0
                else (89, 70, 111, alpha)
            )
            pygame.draw.circle(
                particles,
                color,
                (round(x), round(y)),
                1 + index % 2,
            )

        if progress < 0.3:
            pygame.draw.circle(
                particles,
                (224, 205, 244, round(alpha * 0.6)),
                (round(center_x), round(center_y)),
                round(3 + progress * 18),
                width=1,
            )

    if particles is not None:
        surface.blit(particles, (0, 0))

    reward = game_state.act_three.mining_reward
    if reward is None or reward["floor_index"] != game_state.floor_index:
        return

    elapsed = current_time - reward["started_at"]
    if not 0 <= elapsed < MINING_REWARD_MS:
        return

    progress = elapsed / MINING_REWARD_MS
    alpha = round(255 * min(1, (1 - progress) * 3))
    column, row = reward["position"]
    label = font.render("+1 Black ore", True, (212, 184, 235))
    label.set_alpha(alpha)
    rectangle = label.get_rect(
        center=(
            round(
                column * ACT_THREE_TILE_SIZE
                - context.camera_x
                + ACT_THREE_TILE_SIZE // 2
            ),
            round(row * ACT_THREE_TILE_SIZE - context.camera_y - 8 - progress * 18),
        )
    )
    shadow = font.render("+1 Black ore", True, (12, 8, 18))
    shadow.set_alpha(alpha)
    surface.blit(shadow, rectangle.move(1, 2))
    surface.blit(label, rectangle)
    icon = assets["black_ore_chunk_icon"].copy()
    icon.set_alpha(alpha)
    surface.blit(icon, (rectangle.left - 23, rectangle.centery - 9))
