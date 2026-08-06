import math

import pygame

from presentation.layout import (
    MAP_HEIGHT,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    MAP_WIDTH,
)
from settings import (
    ATTACK_WARNING_COLOR,
    DANGER_BORDER_COLOR,
    DANGER_TILE_COLOR,
    GRID_COLOR,
    HEALTH_BAR_BACKGROUND,
    HEALTH_BAR_COLOR,
    PLAYER_ATTACK_BORDER_COLOR,
    PLAYER_ATTACK_TILE_COLOR,
    PLAYER_HEALTH_BAR_COLOR,
    TILE_SIZE,
)


ACT_ONE_FLOOR_COLOR = (24, 25, 31)
ACT_ONE_FLOOR_ALT_COLOR = (27, 28, 35)
ACT_ONE_WALL_COLOR = (49, 48, 56)
ACT_ONE_WALL_ALT_COLOR = (54, 52, 61)
ACT_ONE_GRID_COLOR = (15, 16, 21)
ACT_ONE_STONE_LIGHT = (67, 64, 73)
ACT_ONE_STONE_SHADOW = (18, 18, 24)
ACT_ONE_IRON = (42, 43, 51)
ACT_ONE_IRON_LIGHT = (78, 76, 85)
ACT_ONE_GOLD = (164, 124, 50)
ACT_ONE_GOLD_LIGHT = (226, 184, 82)
ACT_ONE_BLOOD = (112, 38, 45)
ACT_ONE_PLAYER_CLOAK = (58, 65, 76)
ACT_ONE_PLAYER_EDGE = (116, 132, 145)
ACT_ONE_PLAYER_FACE = (174, 165, 151)


def _act_one_enemy_color(color, is_aggro):
    factor = 0.78 if is_aggro else 0.56
    return tuple(max(28, round(channel * factor)) for channel in color)


def _draw_act_one_glow(screen, center, color, radius=18):
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for current_radius in range(radius, 2, -3):
        progress = 1 - current_radius / radius
        alpha = round(5 + 21 * progress * progress)
        pygame.draw.circle(
            glow,
            (*color, alpha),
            (radius, radius),
            current_radius,
        )
    screen.blit(glow, (center[0] - radius, center[1] - radius))


def _draw_act_one_shadow(screen, center_x, center_y, width=22):
    shadow = pygame.Surface((width + 8, 10), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (4, 4, 7, 145), shadow.get_rect())
    screen.blit(shadow, (center_x - shadow.get_width() // 2, center_y + 7))


def _draw_act_one_healing_effect(
    screen,
    center_x,
    center_y,
    current_time,
    effect_started_at,
):
    duration = 720
    elapsed = current_time - effect_started_at
    if effect_started_at <= 0 or not 0 <= elapsed < duration:
        return False

    progress = elapsed / duration
    visibility = 1 - progress
    effect_size = 64
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    effect_center = effect_size // 2

    ring_radius = round(10 + progress * 18)
    pygame.draw.circle(
        effect_surface,
        (67, 207, 126, round(190 * visibility)),
        (effect_center, effect_center + 2),
        ring_radius,
        width=2,
    )
    pygame.draw.ellipse(
        effect_surface,
        (91, 230, 145, round(145 * visibility)),
        (
            effect_center - 14 - round(progress * 7),
            effect_center + 12,
            28 + round(progress * 14),
            7,
        ),
        width=2,
    )

    particle_offsets = (-12, -7, -2, 4, 9, 13)
    for particle_index, offset_x in enumerate(particle_offsets):
        particle_delay = particle_index * 38
        particle_elapsed = max(0, elapsed - particle_delay)
        particle_progress = min(1, particle_elapsed / 470)
        if particle_elapsed <= 0 or particle_progress >= 1:
            continue
        particle_visibility = 1 - particle_progress
        drift = -1 if particle_index % 2 else 1
        particle_x = (
            effect_center
            + offset_x
            + round(drift * particle_progress * 4)
        )
        particle_y = effect_center + 12 - round(particle_progress * 34)
        pygame.draw.rect(
            effect_surface,
            (95, 235, 151, round(220 * particle_visibility)),
            (particle_x, particle_y, 2, 3),
        )

    symbol_alpha = round(235 * max(0, 1 - progress * 1.35))
    symbol_y = effect_center - 16 - round(progress * 7)
    pygame.draw.line(
        effect_surface,
        (141, 244, 174, symbol_alpha),
        (effect_center - 4, symbol_y),
        (effect_center + 4, symbol_y),
        2,
    )
    pygame.draw.line(
        effect_surface,
        (141, 244, 174, symbol_alpha),
        (effect_center, symbol_y - 4),
        (effect_center, symbol_y + 4),
        2,
    )

    screen.blit(
        effect_surface,
        (center_x - effect_center, center_y - effect_center),
    )
    return True


def _act_one_hit_reaction(
    column,
    row,
    current_time,
    hit_started_at,
    hit_origin,
):
    duration = 380
    elapsed = current_time - hit_started_at
    if hit_started_at < 0 or not 0 <= elapsed < duration:
        return False, 0, 0, False

    offset_x = 0
    offset_y = 0
    recoil_duration = 210
    if elapsed < recoil_duration:
        recoil_progress = elapsed / recoil_duration
        recoil = math.sin(math.pi * recoil_progress)
        direction_x = 0
        direction_y = 1
        if hit_origin is not None:
            difference_x = column - hit_origin[0]
            difference_y = row - hit_origin[1]
            if abs(difference_x) >= abs(difference_y):
                direction_x = 1 if difference_x >= 0 else -1
                direction_y = 0
            else:
                direction_x = 0
                direction_y = 1 if difference_y >= 0 else -1
        offset_x = round(direction_x * 4 * recoil)
        offset_y = round(direction_y * 4 * recoil)

    return True, offset_x, offset_y, elapsed < 170


def _draw_act_one_hit_effect(
    screen,
    center_x,
    center_y,
    current_time,
    hit_started_at,
):
    elapsed = current_time - hit_started_at
    duration = 380
    if hit_started_at < 0 or not 0 <= elapsed < duration:
        return

    progress = elapsed / duration
    visibility = 1 - progress
    effect_size = 58
    effect_center = effect_size // 2
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    ring_radius = round(9 + progress * 16)
    pygame.draw.circle(
        effect_surface,
        (205, 61, 67, round(175 * visibility)),
        (effect_center, effect_center),
        ring_radius,
        width=2,
    )

    ray_length = round(7 + progress * 8)
    ray_start = round(8 + progress * 5)
    ray_alpha = round(210 * visibility)
    for direction_x, direction_y in (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (1, 1),
    ):
        start = (
            effect_center + direction_x * ray_start,
            effect_center + direction_y * ray_start,
        )
        end = (
            effect_center + direction_x * ray_length,
            effect_center + direction_y * ray_length,
        )
        pygame.draw.line(
            effect_surface,
            (235, 112, 107, ray_alpha),
            start,
            end,
            2,
        )

    screen.blit(
        effect_surface,
        (center_x - effect_center, center_y - effect_center),
    )


def _act_one_attack_lunge(
    column,
    row,
    target,
    current_time,
    attack_started_at,
):
    duration = 260
    elapsed = current_time - attack_started_at
    if (
        target is None
        or attack_started_at <= 0
        or not 0 <= elapsed < duration
    ):
        return 0, 0

    direction_x = target[0] - column
    direction_y = target[1] - row
    if direction_x:
        direction_x = 1 if direction_x > 0 else -1
    if direction_y:
        direction_y = 1 if direction_y > 0 else -1

    lunge = math.sin(math.pi * elapsed / duration)
    return (
        round(direction_x * 5 * lunge),
        round(direction_y * 5 * lunge),
    )


def draw_act_one_player_attack_effect(
    screen,
    act_number,
    column,
    row,
    target,
    current_time,
    attack_started_at,
):
    duration = 280
    elapsed = current_time - attack_started_at
    if (
        act_number >= 2
        or target is None
        or attack_started_at <= 0
        or not 0 <= elapsed < duration
    ):
        return

    progress = elapsed / duration
    visibility = max(0.0, 1 - progress)
    direction_x = target[0] - column
    direction_y = target[1] - row
    length = math.hypot(direction_x, direction_y)
    if length == 0:
        return
    direction_x /= length
    direction_y /= length
    perpendicular_x = -direction_y
    perpendicular_y = direction_x

    player_center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    player_center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
    target_center_x = MAP_OFFSET_X + target[0] * TILE_SIZE + TILE_SIZE // 2
    target_center_y = MAP_OFFSET_Y + target[1] * TILE_SIZE + TILE_SIZE // 2
    lunge = math.sin(math.pi * min(1.0, elapsed / 260))
    hand_x = player_center_x + direction_x * (8 + 5 * lunge)
    hand_y = player_center_y + direction_y * (8 + 5 * lunge)

    effect_left = round(min(player_center_x, target_center_x) - 24)
    effect_top = round(min(player_center_y, target_center_y) - 24)
    effect_right = round(max(player_center_x, target_center_x) + 24)
    effect_bottom = round(max(player_center_y, target_center_y) + 24)
    effect_surface = pygame.Surface(
        (effect_right - effect_left, effect_bottom - effect_top),
        pygame.SRCALPHA,
    )
    hand_x -= effect_left
    hand_y -= effect_top
    target_center_x -= effect_left
    target_center_y -= effect_top
    blade_alpha = round(220 * visibility)
    pygame.draw.line(
        effect_surface,
        (91, 98, 108, round(165 * visibility)),
        (round(hand_x), round(hand_y)),
        (
            round(hand_x + direction_x * 13),
            round(hand_y + direction_y * 13),
        ),
        3,
    )
    pygame.draw.line(
        effect_surface,
        (226, 217, 194, blade_alpha),
        (
            round(target_center_x - perpendicular_x * 11 - direction_x * 4),
            round(target_center_y - perpendicular_y * 11 - direction_y * 4),
        ),
        (
            round(target_center_x + perpendicular_x * 11 + direction_x * 3),
            round(target_center_y + perpendicular_y * 11 + direction_y * 3),
        ),
        3,
    )
    pygame.draw.line(
        effect_surface,
        (164, 124, 50, round(145 * visibility)),
        (
            round(target_center_x - perpendicular_x * 9 - direction_x * 8),
            round(target_center_y - perpendicular_y * 9 - direction_y * 8),
        ),
        (
            round(target_center_x + perpendicular_x * 9 - direction_x * 1),
            round(target_center_y + perpendicular_y * 9 - direction_y * 1),
        ),
        2,
    )

    spark_alpha = round(235 * max(0.0, 1 - progress * 1.7))
    spark_center = (
        round(target_center_x - direction_x * 5),
        round(target_center_y - direction_y * 5),
    )
    spark_length = round(4 + progress * 7)
    for spark_x, spark_y in (
        (perpendicular_x, perpendicular_y),
        (-perpendicular_x, -perpendicular_y),
        (direction_x, direction_y),
    ):
        pygame.draw.line(
            effect_surface,
            (239, 197, 102, spark_alpha),
            spark_center,
            (
                round(spark_center[0] + spark_x * spark_length),
                round(spark_center[1] + spark_y * spark_length),
            ),
            2,
        )

    screen.blit(effect_surface, (effect_left, effect_top))


def _lighter(color, amount):
    return tuple(min(255, channel + amount) for channel in color)


def _draw_act_one_goblin(screen, x, y, size, color, is_aggro):
    center_x = x + size // 2
    eye_color = (229, 79, 64) if is_aggro else (116, 92, 61)
    pygame.draw.ellipse(
        screen,
        (17, 19, 22),
        (x + 3, y + 9, size - 6, size - 7),
    )
    pygame.draw.polygon(
        screen,
        color,
        [
            (x + 1, y + 5),
            (x + 7, y + 8),
            (x + 6, y + 2),
            (center_x, y + 5),
            (x + size - 6, y + 2),
            (x + size - 7, y + 8),
            (x + size - 1, y + 5),
            (x + size - 5, y + 13),
            (x + 5, y + 13),
        ],
    )
    pygame.draw.ellipse(
        screen,
        _lighter(color, 18),
        (x + 5, y + 5, size - 10, 10),
    )
    pygame.draw.rect(screen, eye_color, (center_x - 4, y + 9, 2, 1))
    pygame.draw.rect(screen, eye_color, (center_x + 3, y + 9, 2, 1))
    pygame.draw.line(
        screen,
        (105, 104, 103),
        (x + size - 3, y + 11),
        (x + size + 2, y + 6),
        2,
    )
    pygame.draw.line(
        screen,
        (72, 51, 35),
        (x + size - 4, y + 13),
        (x + size - 1, y + 10),
        2,
    )


def _draw_act_one_brute(screen, x, y, size, color, is_aggro):
    center_x = x + size // 2
    eye_color = (233, 75, 55) if is_aggro else (104, 73, 52)
    pygame.draw.rect(screen, (16, 16, 20), (x + 4, y + 8, size - 8, 12))
    pygame.draw.circle(screen, color, (x + 4, y + 11), 5)
    pygame.draw.circle(screen, color, (x + size - 4, y + 11), 5)
    pygame.draw.polygon(
        screen,
        color,
        [
            (x + 5, y + 7),
            (x + 8, y + 3),
            (x + size - 8, y + 3),
            (x + size - 5, y + 7),
            (x + size - 6, y + size),
            (x + 6, y + size),
        ],
    )
    pygame.draw.rect(
        screen,
        _lighter(color, 20),
        (center_x - 5, y + 2, 10, 7),
        border_radius=3,
    )
    pygame.draw.rect(screen, eye_color, (center_x - 3, y + 5, 2, 1))
    pygame.draw.rect(screen, eye_color, (center_x + 2, y + 5, 2, 1))
    pygame.draw.line(
        screen,
        (59, 39, 31),
        (x + 5, y + 15),
        (x + size - 5, y + 15),
        2,
    )
    pygame.draw.rect(screen, (38, 32, 31), (x + 1, y + 15, 6, 5))
    pygame.draw.rect(screen, (38, 32, 31), (x + size - 7, y + 15, 6, 5))
    pygame.draw.line(
        screen,
        (92, 67, 43),
        (x + size - 2, y + 10),
        (x + size + 3, y + 19),
        2,
    )
    pygame.draw.polygon(
        screen,
        (76, 78, 82),
        [
            (x + size - 3, y + 5),
            (x + size + 4, y + 7),
            (x + size + 2, y + 13),
            (x + size - 3, y + 10),
        ],
    )
    pygame.draw.line(
        screen,
        (130, 126, 123),
        (x + size - 2, y + 6),
        (x + size + 2, y + 8),
    )


def _draw_act_one_archer(screen, x, y, size, color, is_aggro):
    center_x = x + size // 2
    eye_color = (218, 94, 65) if is_aggro else (88, 110, 83)
    pygame.draw.polygon(
        screen,
        (17, 20, 22),
        [
            (center_x, y),
            (x + size - 4, y + 8),
            (x + size - 3, y + size),
            (x + 3, y + size),
            (x + 4, y + 8),
        ],
    )
    pygame.draw.polygon(
        screen,
        color,
        [
            (center_x, y + 1),
            (x + size - 6, y + 8),
            (x + size - 5, y + size - 1),
            (x + 5, y + size - 1),
            (x + 6, y + 8),
        ],
    )
    pygame.draw.circle(
        screen,
        _lighter(color, 20),
        (center_x, y + 7),
        6,
    )
    pygame.draw.circle(screen, (18, 23, 24), (center_x, y + 8), 4)
    pygame.draw.rect(screen, eye_color, (center_x - 2, y + 7, 1, 1))
    pygame.draw.rect(screen, eye_color, (center_x + 2, y + 7, 1, 1))
    bow_rectangle = pygame.Rect(x - 3, y + 3, 10, 18)
    pygame.draw.arc(
        screen,
        (128, 93, 52),
        bow_rectangle,
        -1.45,
        1.45,
        2,
    )
    pygame.draw.line(
        screen,
        (91, 77, 58),
        (x + 2, y + 4),
        (x + 2, y + 20),
    )
    pygame.draw.line(
        screen,
        (151, 143, 119),
        (x + 1, y + 12),
        (x + size - 1, y + 12),
    )
    pygame.draw.polygon(
        screen,
        (151, 143, 119),
        [
            (x + size - 1, y + 12),
            (x + size - 5, y + 10),
            (x + size - 5, y + 14),
        ],
    )


def _draw_act_one_warden(screen, x, y, size, color, is_aggro):
    center_x = x + size // 2
    rune_color = (213, 91, 112) if is_aggro else (123, 82, 129)
    pygame.draw.polygon(
        screen,
        (16, 15, 21),
        [
            (center_x, y - 2),
            (x + size - 2, y + 8),
            (x + size - 4, y + size + 1),
            (x + 4, y + size + 1),
            (x + 2, y + 8),
        ],
    )
    pygame.draw.polygon(
        screen,
        color,
        [
            (center_x, y + 1),
            (x + size - 4, y + 8),
            (x + size - 6, y + size),
            (x + 6, y + size),
            (x + 4, y + 8),
        ],
    )
    pygame.draw.polygon(
        screen,
        _lighter(color, 24),
        [
            (center_x, y - 3),
            (center_x + 3, y + 3),
            (x + size - 3, y),
            (x + size - 6, y + 7),
            (x + 6, y + 7),
            (x + 3, y),
            (center_x - 3, y + 3),
        ],
    )
    pygame.draw.rect(screen, (19, 16, 25), (center_x - 5, y + 6, 10, 5))
    pygame.draw.rect(screen, rune_color, (center_x - 3, y + 8, 2, 1))
    pygame.draw.rect(screen, rune_color, (center_x + 2, y + 8, 2, 1))
    pygame.draw.line(
        screen,
        rune_color,
        (center_x, y + 13),
        (center_x, y + 18),
        2,
    )
    pygame.draw.line(screen, rune_color, (center_x - 3, y + 15), (center_x, y + 18))
    pygame.draw.line(screen, rune_color, (center_x + 3, y + 15), (center_x, y + 18))
    pygame.draw.line(
        screen,
        (88, 81, 98),
        (x + size + 1, y + 3),
        (x + size + 1, y + size),
        2,
    )
    pygame.draw.circle(screen, rune_color, (x + size + 1, y + 3), 3, width=1)


def _draw_act_one_enemy(screen, enemy, x, y, size, color):
    _draw_act_one_shadow(
        screen,
        x + size // 2,
        y + size // 2,
        size,
    )
    drawers = {
        "goblin": _draw_act_one_goblin,
        "brute": _draw_act_one_brute,
        "archer": _draw_act_one_archer,
        "warden": _draw_act_one_warden,
    }
    drawer = drawers.get(enemy["type"], _draw_act_one_goblin)
    drawer(screen, x, y, size, color, enemy["is_aggro"])


def draw_act_one_atmosphere(
    screen,
    act_number,
    player_column,
    player_row,
):
    if act_number >= 2:
        return

    overlay = pygame.Surface((MAP_WIDTH, MAP_HEIGHT), pygame.SRCALPHA)
    for inset, alpha, width in (
        (0, 74, 24),
        (22, 43, 20),
        (42, 22, 18),
    ):
        pygame.draw.rect(
            overlay,
            (2, 3, 7, alpha),
            (
                inset,
                inset,
                MAP_WIDTH - inset * 2,
                MAP_HEIGHT - inset * 2,
            ),
            width=width,
        )
    screen.blit(overlay, (MAP_OFFSET_X, MAP_OFFSET_Y))

    player_center = (
        MAP_OFFSET_X + player_column * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + player_row * TILE_SIZE + TILE_SIZE // 2,
    )
    _draw_act_one_glow(screen, player_center, (72, 94, 116), 52)


def draw_dungeon(screen, dungeon_map, act_number, sprites):
    for row_index, row in enumerate(dungeon_map):
        for column_index, tile in enumerate(row):
            x = MAP_OFFSET_X + column_index * TILE_SIZE
            y = MAP_OFFSET_Y + row_index * TILE_SIZE
            tile_rectangle = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            if act_number >= 2:
                texture_name = "wall" if tile == "#" else "floor"
                screen.blit(sprites[texture_name], tile_rectangle)

                if tile == "C":
                    screen.blit(
                        sprites["pillar"],
                        tile_rectangle,
                    )
            else:
                variation = (column_index * 7 + row_index * 11) % 5
                if tile == "#":
                    color = (
                        ACT_ONE_WALL_ALT_COLOR
                        if variation in (0, 3)
                        else ACT_ONE_WALL_COLOR
                    )
                    pygame.draw.rect(screen, color, tile_rectangle)
                    pygame.draw.line(
                        screen,
                        ACT_ONE_STONE_LIGHT,
                        (x + 2, y + 2),
                        (x + TILE_SIZE - 3, y + 2),
                    )
                    pygame.draw.line(
                        screen,
                        ACT_ONE_STONE_SHADOW,
                        (x + 2, y + TILE_SIZE - 2),
                        (x + TILE_SIZE - 2, y + TILE_SIZE - 2),
                        2,
                    )
                    seam_x = x + (11 if row_index % 2 else 20)
                    pygame.draw.line(
                        screen,
                        (35, 34, 41),
                        (seam_x, y + 4),
                        (seam_x, y + 13),
                    )
                else:
                    color = (
                        ACT_ONE_FLOOR_ALT_COLOR
                        if variation == 0
                        else ACT_ONE_FLOOR_COLOR
                    )
                    pygame.draw.rect(screen, color, tile_rectangle)
                    pygame.draw.line(
                        screen,
                        (34, 35, 42),
                        (x + 3, y + 3),
                        (x + TILE_SIZE - 4, y + 3),
                    )
                    if variation == 0:
                        pygame.draw.line(
                            screen,
                            (39, 39, 47),
                            (x + 9, y + 19),
                            (x + 16, y + 16),
                        )
                        pygame.draw.line(
                            screen,
                            (17, 18, 23),
                            (x + 16, y + 16),
                            (x + 22, y + 21),
                        )

            grid_color = (
                ACT_ONE_GRID_COLOR
                if act_number < 2
                else GRID_COLOR
            )
            pygame.draw.rect(screen, grid_color, tile_rectangle, 1)


def draw_map_frame(screen, act_number):
    if act_number < 2:
        outer_rectangle = pygame.Rect(
            MAP_OFFSET_X - 5,
            MAP_OFFSET_Y - 5,
            MAP_WIDTH + 10,
            MAP_HEIGHT + 10,
        )
        pygame.draw.rect(screen, (10, 10, 14), outer_rectangle, width=5)
        pygame.draw.rect(screen, ACT_ONE_IRON, outer_rectangle, width=2)
        pygame.draw.line(
            screen,
            ACT_ONE_IRON_LIGHT,
            outer_rectangle.topleft,
            outer_rectangle.topright,
        )
        for corner in (
            outer_rectangle.topleft,
            outer_rectangle.topright,
            outer_rectangle.bottomleft,
            outer_rectangle.bottomright,
        ):
            pygame.draw.circle(screen, (20, 20, 25), corner, 4)
            pygame.draw.circle(screen, (89, 84, 81), corner, 2)
        return

    outer_rectangle = pygame.Rect(
        MAP_OFFSET_X - 4,
        MAP_OFFSET_Y - 4,
        MAP_WIDTH + 8,
        MAP_HEIGHT + 8,
    )
    pygame.draw.rect(
        screen,
        (72, 68, 78),
        outer_rectangle,
        width=3,
    )
    pygame.draw.rect(
        screen,
        (30, 27, 34),
        outer_rectangle.inflate(-6, -6),
        width=1,
    )


def _draw_act_one_warden_telegraph(
    screen,
    column,
    row,
    mode,
    current_time,
    sweep_is_horizontal=False,
):
    left = MAP_OFFSET_X + column * TILE_SIZE
    top = MAP_OFFSET_Y + row * TILE_SIZE
    center = (left + TILE_SIZE // 2, top + TILE_SIZE // 2)
    pulse = (math.sin(current_time / 125) + 1) / 2
    tile_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

    if mode == "cross":
        tile_overlay.fill((92, 17, 27, round(54 + pulse * 28)))
        line_color = (218, 54, 66, round(150 + pulse * 80))
        pygame.draw.line(
            tile_overlay,
            line_color,
            (3, TILE_SIZE // 2),
            (TILE_SIZE - 3, TILE_SIZE // 2),
            2,
        )
        pygame.draw.line(
            tile_overlay,
            line_color,
            (TILE_SIZE // 2, 3),
            (TILE_SIZE // 2, TILE_SIZE - 3),
            2,
        )
        pygame.draw.circle(
            tile_overlay,
            (245, 104, 105, round(175 + pulse * 70)),
            (TILE_SIZE // 2, TILE_SIZE // 2),
            4,
            width=1,
        )
    elif mode == "sweep":
        tile_overlay.fill((91, 39, 12, round(48 + pulse * 25)))
        sweep_color = (232, 119, 49, round(155 + pulse * 85))
        offset = round(pulse * 5) - 2
        if sweep_is_horizontal:
            pygame.draw.line(
                tile_overlay,
                sweep_color,
                (2, TILE_SIZE // 2 + offset),
                (TILE_SIZE - 2, TILE_SIZE // 2 + offset),
                3,
            )
            pygame.draw.line(
                tile_overlay,
                (255, 190, 89, 150),
                (8, TILE_SIZE // 2 - 5 + offset),
                (TILE_SIZE - 8, TILE_SIZE // 2 - 5 + offset),
            )
        else:
            pygame.draw.line(
                tile_overlay,
                sweep_color,
                (TILE_SIZE // 2 + offset, 2),
                (TILE_SIZE // 2 + offset, TILE_SIZE - 2),
                3,
            )
            pygame.draw.line(
                tile_overlay,
                (255, 190, 89, 150),
                (TILE_SIZE // 2 - 5 + offset, 8),
                (TILE_SIZE // 2 - 5 + offset, TILE_SIZE - 8),
            )
    else:
        tile_overlay.fill((52, 19, 70, round(50 + pulse * 28)))
        rune_color = (179, 82, 205, round(160 + pulse * 85))
        radius = round(8 + pulse * 3)
        pygame.draw.circle(
            tile_overlay,
            rune_color,
            (TILE_SIZE // 2, TILE_SIZE // 2),
            radius,
            width=2,
        )
        pygame.draw.polygon(
            tile_overlay,
            rune_color,
            [
                (TILE_SIZE // 2, 5),
                (TILE_SIZE - 5, TILE_SIZE // 2),
                (TILE_SIZE // 2, TILE_SIZE - 5),
                (5, TILE_SIZE // 2),
            ],
            width=1,
        )
        pygame.draw.circle(
            tile_overlay,
            (230, 139, 244, round(180 + pulse * 70)),
            (TILE_SIZE // 2, TILE_SIZE // 2),
            2,
        )

    screen.blit(tile_overlay, (left, top))
    pygame.draw.rect(
        screen,
        (122, 47, 59) if mode == "cross" else (
            (145, 77, 37) if mode == "sweep" else (100, 53, 122)
        ),
        (left, top, TILE_SIZE, TILE_SIZE),
        width=1,
    )


def draw_attack_markers(
    screen,
    enemies,
    act_number=2,
    current_time=0,
):
    for enemy in enemies:
        if enemy["health"] <= 0:
            continue

        attack_mode = enemy.get("prepared_attack_mode")
        uses_warden_telegraph = (
            act_number < 2
            and enemy["type"] == "warden"
            and attack_mode in ("cross", "sweep", "runes")
        )
        attack_targets = enemy["attack_targets"]
        target_rows = {row for _, row in attack_targets}
        sweep_is_horizontal = len(target_rows) == 1

        for column, row in attack_targets:
            if uses_warden_telegraph:
                _draw_act_one_warden_telegraph(
                    screen,
                    column,
                    row,
                    attack_mode,
                    current_time,
                    sweep_is_horizontal,
                )
                continue

            target_rectangle = pygame.Rect(
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
            )
            pygame.draw.rect(screen, DANGER_TILE_COLOR, target_rectangle)
            pygame.draw.rect(
                screen,
                DANGER_BORDER_COLOR,
                target_rectangle,
                width=3,
            )


def _draw_act_one_warden_attack_impact(
    screen,
    column,
    row,
    mode,
    progress,
    sweep_is_horizontal,
):
    left = MAP_OFFSET_X + column * TILE_SIZE
    top = MAP_OFFSET_Y + row * TILE_SIZE
    effect = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    visibility = max(0, 1 - progress)
    center = TILE_SIZE // 2

    if mode == "cross":
        color = (255, 95, 96, round(235 * visibility))
        width = 4 if progress < 0.35 else 2
        pygame.draw.line(effect, color, (1, center), (TILE_SIZE - 1, center), width)
        pygame.draw.line(effect, color, (center, 1), (center, TILE_SIZE - 1), width)
        pygame.draw.circle(
            effect,
            (255, 207, 177, round(210 * visibility)),
            (center, center),
            round(4 + progress * 10),
            width=2,
        )
    elif mode == "sweep":
        color = (255, 152, 59, round(240 * visibility))
        travel = round(progress * TILE_SIZE)
        if sweep_is_horizontal:
            pygame.draw.line(effect, color, (0, center), (travel, center), 5)
            pygame.draw.line(
                effect,
                (255, 224, 156, round(190 * visibility)),
                (0, center - 4),
                (travel, center - 4),
                2,
            )
        else:
            pygame.draw.line(effect, color, (center, 0), (center, travel), 5)
            pygame.draw.line(
                effect,
                (255, 224, 156, round(190 * visibility)),
                (center - 4, 0),
                (center - 4, travel),
                2,
            )
    else:
        color = (218, 101, 240, round(230 * visibility))
        radius = round(3 + progress * 14)
        pygame.draw.circle(effect, color, (center, center), radius, width=3)
        pygame.draw.polygon(
            effect,
            (247, 178, 255, round(205 * visibility)),
            [(center, 2), (TILE_SIZE - 2, center), (center, TILE_SIZE - 2), (2, center)],
            width=2,
        )

    screen.blit(effect, (left, top))


def _draw_act_one_warden_phase_transition(
    screen,
    warden,
    current_time,
    font,
):
    elapsed = current_time - warden.phase_transition_started_at
    duration = 1150
    if warden.phase_transition_started_at < 0 or not 0 <= elapsed < duration:
        return

    progress = elapsed / duration
    pulse = math.sin(math.pi * progress)
    arena_overlay = pygame.Surface((MAP_WIDTH, MAP_HEIGHT), pygame.SRCALPHA)
    arena_overlay.fill((37, 6, 47, round(72 * pulse)))
    screen.blit(arena_overlay, (MAP_OFFSET_X, MAP_OFFSET_Y))

    center_x = MAP_OFFSET_X + warden.column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + warden.row * TILE_SIZE + TILE_SIZE // 2
    aura = pygame.Surface((112, 112), pygame.SRCALPHA)
    aura_center = 56
    for ring_index in range(3):
        radius = round(16 + progress * 30 + ring_index * 8)
        pygame.draw.circle(
            aura,
            (190, 67, 202, round((165 - ring_index * 35) * pulse)),
            (aura_center, aura_center),
            radius,
            width=2,
        )
    screen.blit(aura, (center_x - aura_center, center_y - aura_center))

    if font is not None:
        title_alpha = round(255 * min(1, progress * 5) * min(1, (1 - progress) * 4))
        title = font.render(
            "THE WARDEN UNBOUND",
            True,
            (226, 151, 220),
        )
        title.set_alpha(title_alpha)
        screen.blit(
            title,
            title.get_rect(
                center=(
                    MAP_OFFSET_X + MAP_WIDTH // 2,
                    MAP_OFFSET_Y + 55,
                )
            ),
        )


def draw_act_one_boss_effects(
    screen,
    enemies,
    act_number,
    current_time,
    font=None,
):
    if act_number >= 2:
        return

    warden = next(
        (enemy for enemy in enemies if enemy.type == "warden"),
        None,
    )
    if warden is None:
        return

    _draw_act_one_warden_phase_transition(
        screen,
        warden,
        current_time,
        font,
    )

    elapsed = current_time - warden.attack_animation_started_at
    duration = 460
    if (
        warden.attack_animation_started_at <= 0
        or not 0 <= elapsed < duration
        or warden.attack_effect_mode not in ("cross", "sweep", "runes")
        or not warden.attack_effect_positions
    ):
        return

    progress = elapsed / duration
    target_rows = {row for _, row in warden.attack_effect_positions}
    sweep_is_horizontal = len(target_rows) == 1
    if warden.attack_effect_mode == "sweep":
        columns = [column for column, _ in warden.attack_effect_positions]
        rows = [row for _, row in warden.attack_effect_positions]
        visibility = max(0, 1 - progress)
        travel_progress = min(1, progress * 1.65)
        glow_color = (177, 69, 24)
        core_color = (
            255,
            180,
            77,
        )
        if sweep_is_horizontal:
            start_x = MAP_OFFSET_X + min(columns) * TILE_SIZE
            end_x = MAP_OFFSET_X + (max(columns) + 1) * TILE_SIZE
            sweep_y = MAP_OFFSET_Y + rows[0] * TILE_SIZE + TILE_SIZE // 2
            current_end_x = round(
                start_x + (end_x - start_x) * travel_progress
            )
            pygame.draw.line(
                screen,
                glow_color,
                (start_x, sweep_y),
                (current_end_x, sweep_y),
                max(2, round(8 * visibility)),
            )
            pygame.draw.line(
                screen,
                core_color,
                (start_x, sweep_y),
                (current_end_x, sweep_y),
                max(1, round(3 * visibility)),
            )
        else:
            sweep_x = MAP_OFFSET_X + columns[0] * TILE_SIZE + TILE_SIZE // 2
            start_y = MAP_OFFSET_Y + min(rows) * TILE_SIZE
            end_y = MAP_OFFSET_Y + (max(rows) + 1) * TILE_SIZE
            current_end_y = round(
                start_y + (end_y - start_y) * travel_progress
            )
            pygame.draw.line(
                screen,
                glow_color,
                (sweep_x, start_y),
                (sweep_x, current_end_y),
                max(2, round(8 * visibility)),
            )
            pygame.draw.line(
                screen,
                core_color,
                (sweep_x, start_y),
                (sweep_x, current_end_y),
                max(1, round(3 * visibility)),
            )
        return

    for column, row in warden.attack_effect_positions:
        _draw_act_one_warden_attack_impact(
            screen,
            column,
            row,
            warden.attack_effect_mode,
            progress,
            sweep_is_horizontal,
        )


def draw_player_attack_markers(screen, attack_targets):
    for column, row in attack_targets:
        target_rectangle = pygame.Rect(
            MAP_OFFSET_X + column * TILE_SIZE,
            MAP_OFFSET_Y + row * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(
            screen,
            PLAYER_ATTACK_TILE_COLOR,
            target_rectangle,
        )
        pygame.draw.rect(
            screen,
            PLAYER_ATTACK_BORDER_COLOR,
            target_rectangle,
            width=3,
        )


def draw_oracle_projectiles(
    screen,
    projectiles,
    sprites,
):
    for projectile in projectiles:
        sprite_name = (
            "oracle_projectile_homing"
            if projectile["kind"] == "homing"
            else "oracle_projectile"
        )
        projectile_left = (
            MAP_OFFSET_X + projectile["column"] * TILE_SIZE
        )
        projectile_top = (
            MAP_OFFSET_Y + projectile["row"] * TILE_SIZE
        )
        screen.blit(
            sprites[sprite_name],
            (projectile_left, projectile_top),
        )


def draw_oracle_emitters(
    screen,
    emitters,
    is_active,
    sprites,
):
    if not is_active:
        return

    for column, row in emitters:
        left = MAP_OFFSET_X + column * TILE_SIZE
        top = MAP_OFFSET_Y + row * TILE_SIZE
        screen.blit(
            sprites["charged_pillar"],
            (left, top),
        )


def draw_player(
    screen,
    column,
    row,
    health,
    max_health,
    player_class,
    act_number,
    sprites,
    invisibility_turns,
    current_time=0,
    potion_effect_started_at=0,
    hit_animation_started_at=-1,
    hit_origin=None,
    attack_animation_started_at=0,
    attack_target=None,
):
    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
    healing_effect_active = False
    hit_effect_active = False
    hit_flash_active = False
    if act_number < 2:
        attack_offset_x, attack_offset_y = _act_one_attack_lunge(
            column,
            row,
            attack_target,
            current_time,
            attack_animation_started_at,
        )
        center_x += attack_offset_x
        center_y += attack_offset_y
        (
            hit_effect_active,
            recoil_x,
            recoil_y,
            hit_flash_active,
        ) = _act_one_hit_reaction(
            column,
            row,
            current_time,
            hit_animation_started_at,
            hit_origin,
        )
        center_x += recoil_x
        center_y += recoil_y
    if act_number >= 2 and player_class is not None:
        player_sprite = sprites[f"player_{player_class}"]

        if invisibility_turns > 0:
            player_sprite = player_sprite.copy()
            player_sprite.set_alpha(90)

        screen.blit(
            player_sprite,
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
    else:
        cloak_color = ACT_ONE_PLAYER_CLOAK
        edge_color = ACT_ONE_PLAYER_EDGE
        face_color = ACT_ONE_PLAYER_FACE
        if hit_flash_active:
            flash_is_bright = (
                (current_time - hit_animation_started_at) // 45
            ) % 2 == 0
            if flash_is_bright:
                cloak_color = (211, 204, 199)
                edge_color = (244, 231, 216)
                face_color = (255, 242, 224)
            else:
                cloak_color = (126, 47, 55)
                edge_color = (211, 81, 82)
                face_color = (231, 166, 149)

        _draw_act_one_shadow(screen, center_x, center_y)
        pygame.draw.polygon(
            screen,
            (18, 20, 26),
            [
                (center_x, center_y - 12),
                (center_x + 9, center_y - 3),
                (center_x + 11, center_y + 10),
                (center_x - 11, center_y + 10),
                (center_x - 9, center_y - 3),
            ],
        )
        pygame.draw.polygon(
            screen,
            cloak_color,
            [
                (center_x, center_y - 10),
                (center_x + 7, center_y - 2),
                (center_x + 8, center_y + 8),
                (center_x - 8, center_y + 8),
                (center_x - 7, center_y - 2),
            ],
        )
        pygame.draw.circle(
            screen,
            edge_color,
            (center_x, center_y - 5),
            7,
        )
        pygame.draw.circle(
            screen,
            (25, 29, 37),
            (center_x, center_y - 4),
            5,
        )
        pygame.draw.line(
            screen,
            edge_color,
            (center_x - 7, center_y + 1),
            (center_x - 8, center_y + 7),
            2,
        )
        pygame.draw.line(
            screen,
            (82, 94, 107),
            (center_x, center_y + 1),
            (center_x, center_y + 7),
        )
        pygame.draw.circle(
            screen,
            ACT_ONE_GOLD,
            (center_x, center_y + 1),
            1,
        )
        pygame.draw.rect(
            screen,
            face_color,
            (center_x - 3, center_y - 5, 2, 1),
        )
        pygame.draw.rect(
            screen,
            face_color,
            (center_x + 2, center_y - 5, 2, 1),
        )

        if act_number < 2:
            healing_effect_active = _draw_act_one_healing_effect(
                screen,
                center_x,
                center_y,
                current_time,
                potion_effect_started_at,
            )
            if hit_effect_active:
                _draw_act_one_hit_effect(
                    screen,
                    center_x,
                    center_y,
                    current_time,
                    hit_animation_started_at,
                )

    health_ratio = health / max_health
    bar_x = MAP_OFFSET_X + column * TILE_SIZE + 4
    bar_y = MAP_OFFSET_Y + (row + 1) * TILE_SIZE - 5
    bar_width = TILE_SIZE - 8
    bar_height = 4

    pygame.draw.rect(
        screen,
        HEALTH_BAR_BACKGROUND,
        (bar_x, bar_y, bar_width, bar_height),
    )
    pygame.draw.rect(
        screen,
        (
            (230, 69, 74)
            if hit_effect_active
            else (
                (91, 220, 139)
                if healing_effect_active
                else PLAYER_HEALTH_BAR_COLOR
            )
        ),
        (bar_x, bar_y, int(bar_width * health_ratio), bar_height),
    )


def draw_enemy(
    screen,
    enemy,
    act_number,
    sprites,
    current_time=0,
):
    padding = TILE_SIZE // 5
    column = enemy["column"]
    row = enemy["row"]
    x = MAP_OFFSET_X + column * TILE_SIZE + padding
    y = MAP_OFFSET_Y + row * TILE_SIZE + padding
    size = TILE_SIZE - padding * 2
    color = (
        enemy["color"]
        if enemy["is_aggro"]
        else enemy["sleeping_color"]
    )
    hit_effect_active = False
    hit_flash_active = False
    if act_number < 2:
        color = _act_one_enemy_color(color, enemy["is_aggro"])
        hit_animation_started_at = enemy.get(
            "hit_animation_started_at",
            -1,
        )
        (
            hit_effect_active,
            recoil_x,
            recoil_y,
            hit_flash_active,
        ) = _act_one_hit_reaction(
            column,
            row,
            current_time,
            hit_animation_started_at,
            enemy.get("hit_origin"),
        )
        x += recoil_x
        y += recoil_y
        if hit_flash_active:
            flash_is_bright = (
                (current_time - hit_animation_started_at) // 45
            ) % 2 == 0
            color = (
                (224, 216, 207)
                if flash_is_bright
                else (171, 54, 61)
            )

    if act_number >= 2 and enemy["type"] == "oracle":
        body_size = TILE_SIZE * 3
        body_left = MAP_OFFSET_X + (column - 1) * TILE_SIZE
        body_top = MAP_OFFSET_Y + (row - 1) * TILE_SIZE
        sprite_name = (
            "oracle_awake"
            if enemy["oracle_awakened"]
            else "oracle_idle"
        )
        screen.blit(
            sprites[sprite_name],
            (body_left, body_top),
        )

        if enemy["is_active"]:
            pygame.draw.rect(
                screen,
                DANGER_BORDER_COLOR,
                (
                    body_left + 2,
                    body_top + 2,
                    body_size - 4,
                    body_size - 4,
                ),
                width=2,
                border_radius=5,
            )

        health_ratio = enemy["health"] / enemy["max_health"]
        bar_x = body_left + 8
        bar_y = body_top + body_size - 7
        bar_width = body_size - 16
        bar_height = 5
        pygame.draw.rect(
            screen,
            HEALTH_BAR_BACKGROUND,
            (bar_x, bar_y, bar_width, bar_height),
        )
        pygame.draw.rect(
            screen,
            HEALTH_BAR_COLOR,
            (
                bar_x,
                bar_y,
                int(bar_width * health_ratio),
                bar_height,
            ),
        )

        if enemy["attack_targets"]:
            warning_x = body_left + body_size // 2
            warning_top = body_top + 8
            pygame.draw.line(
                screen,
                ATTACK_WARNING_COLOR,
                (warning_x, warning_top),
                (warning_x, warning_top + 12),
                4,
            )
            pygame.draw.circle(
                screen,
                ATTACK_WARNING_COLOR,
                (warning_x, warning_top + 19),
                3,
            )

        return

    if act_number < 2:
        if (
            enemy["type"] == "warden"
            and enemy.get("second_phase_announced", False)
        ):
            aura = pygame.Surface((48, 48), pygame.SRCALPHA)
            aura_pulse = (math.sin(current_time / 120) + 1) / 2
            pygame.draw.circle(
                aura,
                (165, 49, 177, round(55 + aura_pulse * 45)),
                (24, 24),
                round(14 + aura_pulse * 3),
                width=3,
            )
            pygame.draw.circle(
                aura,
                (218, 73, 111, round(35 + aura_pulse * 35)),
                (24, 24),
                round(19 + aura_pulse * 2),
                width=2,
            )
            screen.blit(
                aura,
                (x + size // 2 - 24, y + size // 2 - 24),
            )
        _draw_act_one_enemy(screen, enemy, x, y, size, color)
        if hit_effect_active:
            _draw_act_one_hit_effect(
                screen,
                x + size // 2,
                y + size // 2,
                current_time,
                enemy["hit_animation_started_at"],
            )
    elif (
        act_number >= 2
        and enemy["type"] in (
            "goblin",
            "brute",
            "archer",
            "sentinel",
            "priest",
        )
    ):
        sprite_name = enemy["type"]

        if enemy["type"] == "sentinel":
            sprite_name = (
                "sentinel_guard"
                if enemy["shield_turns"] > 0
                else "sentinel_idle"
            )
        elif enemy["type"] == "priest":
            sprite_name = (
                "priest_cast"
                if (
                    enemy["attack_targets"]
                    or enemy["heal_target"] is not None
                )
                else "priest_idle"
            )
        enemy_sprite = sprites[sprite_name]

        screen.blit(
            enemy_sprite,
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )

        if (
            enemy["type"] == "sentinel"
            and enemy["shield_turns"] > 0
        ):
            opening_color = (235, 185, 75)
            tile_left = MAP_OFFSET_X + column * TILE_SIZE
            tile_top = MAP_OFFSET_Y + row * TILE_SIZE
            shield_direction = enemy["shield_direction"]
            vulnerable_direction = (
                -shield_direction[0],
                -shield_direction[1],
            )
            opening_lines = {
                (0, -1): (
                    (tile_left + 5, tile_top + 3),
                    (tile_left + TILE_SIZE - 5, tile_top + 3),
                ),
                (0, 1): (
                    (tile_left + 5, tile_top + TILE_SIZE - 3),
                    (
                        tile_left + TILE_SIZE - 5,
                        tile_top + TILE_SIZE - 3,
                    ),
                ),
                (-1, 0): (
                    (tile_left + 3, tile_top + 5),
                    (tile_left + 3, tile_top + TILE_SIZE - 5),
                ),
                (1, 0): (
                    (tile_left + TILE_SIZE - 3, tile_top + 5),
                    (
                        tile_left + TILE_SIZE - 3,
                        tile_top + TILE_SIZE - 5,
                    ),
                ),
            }
            opening_line = opening_lines.get(
                vulnerable_direction
            )

            if opening_line is not None:
                pygame.draw.line(
                    screen,
                    opening_color,
                    opening_line[0],
                    opening_line[1],
                    3,
                )

        if (
            enemy["type"] == "priest"
            and enemy["heal_target"] is not None
            and enemy["heal_target"]["health"] > 0
        ):
            heal_target = enemy["heal_target"]
            pygame.draw.rect(
                screen,
                (80, 220, 130),
                (
                    MAP_OFFSET_X
                    + heal_target["column"] * TILE_SIZE
                    + 3,
                    MAP_OFFSET_Y
                    + heal_target["row"] * TILE_SIZE
                    + 3,
                    TILE_SIZE - 6,
                    TILE_SIZE - 6,
                ),
                width=2,
                border_radius=4,
            )

        if enemy["is_aggro"]:
            pygame.draw.rect(
                screen,
                DANGER_BORDER_COLOR,
                (
                    MAP_OFFSET_X + column * TILE_SIZE + 2,
                    MAP_OFFSET_Y + row * TILE_SIZE + 2,
                    TILE_SIZE - 4,
                    TILE_SIZE - 4,
                ),
                width=2,
                border_radius=3,
            )
    elif enemy["type"] == "brute":
        corner = 4
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + corner, y),
                (x + size - corner, y),
                (x + size, y + corner),
                (x + size, y + size - corner),
                (x + size - corner, y + size),
                (x + corner, y + size),
                (x, y + size - corner),
                (x, y + corner),
            ],
        )
    elif enemy["type"] == "archer":
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + size // 2, y),
                (x + size, y + size),
                (x, y + size),
            ],
        )
        pygame.draw.line(
            screen,
            tuple(min(255, channel + 38) for channel in color),
            (x + size // 2, y + 4),
            (x + size - 4, y + size - 4),
            2,
        )
    elif enemy["type"] == "warden":
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + size // 2, y),
                (x + size, y + size // 2),
                (x + size // 2, y + size),
                (x, y + size // 2),
            ],
        )
        crown_y = y + size // 4
        pygame.draw.line(
            screen,
            ATTACK_WARNING_COLOR,
            (x + size // 4, crown_y),
            (x + size * 3 // 4, crown_y),
            2,
        )
        pygame.draw.circle(
            screen,
            ATTACK_WARNING_COLOR,
            (x + size // 2, y + size // 2),
            3,
        )
    else:
        pygame.draw.rect(
            screen,
            color,
            (x, y, size, size),
            border_radius=6,
        )
        if act_number < 2:
            pygame.draw.line(
                screen,
                tuple(min(255, channel + 30) for channel in color),
                (x + 4, y + 4),
                (x + size - 5, y + 4),
            )

    health_ratio = enemy["health"] / enemy["max_health"]
    bar_x = MAP_OFFSET_X + column * TILE_SIZE + 4
    bar_y = MAP_OFFSET_Y + (row + 1) * TILE_SIZE - 5
    bar_width = TILE_SIZE - 8
    bar_height = 4

    pygame.draw.rect(
        screen,
        HEALTH_BAR_BACKGROUND,
        (bar_x, bar_y, bar_width, bar_height),
    )
    pygame.draw.rect(
        screen,
        (
            (236, 75, 78)
            if hit_effect_active
            else HEALTH_BAR_COLOR
        ),
        (bar_x, bar_y, int(bar_width * health_ratio), bar_height),
    )

    if enemy["attack_targets"]:
        warning_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
        warning_top = MAP_OFFSET_Y + row * TILE_SIZE + 8
        pygame.draw.line(
            screen,
            ATTACK_WARNING_COLOR,
            (warning_x, warning_top),
            (warning_x, warning_top + 9),
            3,
        )
        pygame.draw.circle(
            screen,
            ATTACK_WARNING_COLOR,
            (warning_x, warning_top + 14),
            2,
        )


def draw_key(screen, column, row, act_number, sprites):
    if act_number >= 2:
        screen.blit(
            sprites["key"],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
        return

    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2

    _draw_act_one_glow(screen, (center_x, center_y), (132, 91, 28), 17)
    pygame.draw.circle(
        screen,
        (16, 14, 13),
        (center_x - 7, center_y + 1),
        7,
        width=3,
    )
    pygame.draw.circle(
        screen,
        ACT_ONE_GOLD,
        (center_x - 7, center_y),
        6,
        width=2,
    )
    pygame.draw.circle(
        screen,
        ACT_ONE_GOLD_LIGHT,
        (center_x - 7, center_y),
        3,
        width=1,
    )
    pygame.draw.line(
        screen,
        ACT_ONE_GOLD,
        (center_x - 1, center_y),
        (center_x + 12, center_y),
        3,
    )
    pygame.draw.line(
        screen,
        ACT_ONE_GOLD_LIGHT,
        (center_x, center_y - 1),
        (center_x + 10, center_y - 1),
    )
    pygame.draw.line(
        screen,
        ACT_ONE_GOLD,
        (center_x + 7, center_y),
        (center_x + 7, center_y + 5),
        2,
    )
    pygame.draw.line(
        screen,
        ACT_ONE_GOLD,
        (center_x + 11, center_y),
        (center_x + 11, center_y + 4),
        2,
    )


def draw_boss_door(screen, column, row, is_open):
    cell_x = MAP_OFFSET_X + column * TILE_SIZE
    cell_y = MAP_OFFSET_Y + row * TILE_SIZE
    frame_color = (115, 75, 130)

    pygame.draw.rect(
        screen,
        frame_color,
        (cell_x + 3, cell_y + 2, TILE_SIZE - 6, TILE_SIZE - 4),
        width=3,
        border_radius=3,
    )

    if is_open:
        return

    pygame.draw.rect(
        screen,
        (55, 35, 62),
        (cell_x + 7, cell_y + 5, TILE_SIZE - 14, TILE_SIZE - 7),
        border_radius=2,
    )
    pygame.draw.line(
        screen,
        frame_color,
        (cell_x + TILE_SIZE // 2, cell_y + 7),
        (cell_x + TILE_SIZE // 2, cell_y + TILE_SIZE - 5),
        2,
    )
    pygame.draw.circle(
        screen,
        ATTACK_WARNING_COLOR,
        (cell_x + TILE_SIZE // 2, cell_y + TILE_SIZE // 2),
        3,
    )


def draw_potion(screen, column, row, act_number, sprites):
    if act_number >= 2:
        screen.blit(
            sprites["potion"],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
        return

    cell_x = MAP_OFFSET_X + column * TILE_SIZE
    cell_y = MAP_OFFSET_Y + row * TILE_SIZE
    bottle_rectangle = pygame.Rect(
        cell_x + TILE_SIZE // 2 - 6,
        cell_y + 11,
        12,
        17,
    )

    _draw_act_one_glow(
        screen,
        (cell_x + TILE_SIZE // 2, cell_y + 19),
        (35, 123, 86),
        16,
    )
    pygame.draw.rect(
        screen,
        (12, 18, 20),
        bottle_rectangle.inflate(4, 3).move(1, 2),
        border_radius=5,
    )
    pygame.draw.rect(
        screen,
        (30, 87, 69),
        bottle_rectangle,
        border_radius=4,
    )
    pygame.draw.rect(
        screen,
        (76, 184, 126),
        (bottle_rectangle.x + 3, bottle_rectangle.y + 8, 3, 6),
        border_radius=1,
    )
    pygame.draw.rect(
        screen,
        ACT_ONE_IRON_LIGHT,
        (cell_x + TILE_SIZE // 2 - 4, cell_y + 7, 8, 5),
        border_radius=1,
    )
    pygame.draw.line(
        screen,
        (137, 134, 129),
        (cell_x + TILE_SIZE // 2 - 2, cell_y + 8),
        (cell_x + TILE_SIZE // 2 + 2, cell_y + 8),
    )


def draw_coin(screen, column, row, act_number, sprites):
    if act_number >= 2:
        screen.blit(
            sprites["coin"],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
        return

    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2

    _draw_act_one_glow(screen, (center_x, center_y), (133, 88, 24), 15)
    pygame.draw.ellipse(
        screen,
        (12, 11, 12),
        (center_x - 8, center_y - 5, 17, 13),
    )
    pygame.draw.circle(
        screen,
        ACT_ONE_GOLD,
        (center_x, center_y),
        7,
    )
    pygame.draw.circle(
        screen,
        ACT_ONE_GOLD_LIGHT,
        (center_x, center_y),
        5,
        width=1,
    )
    pygame.draw.line(
        screen,
        (90, 60, 25),
        (center_x, center_y - 3),
        (center_x, center_y + 3),
        2,
    )


def draw_chest(screen, chest, act_number, sprites):
    cell_x = MAP_OFFSET_X + chest["column"] * TILE_SIZE
    cell_y = MAP_OFFSET_Y + chest["row"] * TILE_SIZE

    if act_number >= 2:
        sprite_name = (
            "chest_open"
            if chest["is_open"]
            else "chest_closed"
        )
        screen.blit(sprites[sprite_name], (cell_x, cell_y))
        return

    if chest["is_open"]:
        _draw_act_one_shadow(
            screen,
            cell_x + TILE_SIZE // 2,
            cell_y + TILE_SIZE // 2,
            25,
        )
        pygame.draw.rect(
            screen,
            (45, 31, 28),
            (cell_x + 4, cell_y + 17, TILE_SIZE - 8, 10),
            border_radius=2,
        )
        pygame.draw.rect(
            screen,
            (66, 43, 34),
            (cell_x + 5, cell_y + 7, TILE_SIZE - 10, 7),
            border_radius=2,
        )
        pygame.draw.line(
            screen,
            ACT_ONE_IRON_LIGHT,
            (cell_x + 5, cell_y + 16),
            (cell_x + TILE_SIZE - 5, cell_y + 16),
            2,
        )
        return

    _draw_act_one_shadow(
        screen,
        cell_x + TILE_SIZE // 2,
        cell_y + TILE_SIZE // 2,
        26,
    )
    pygame.draw.rect(
        screen,
        (31, 28, 30),
        (cell_x + 3, cell_y + 8, TILE_SIZE - 6, 20),
        border_radius=3,
    )
    pygame.draw.rect(
        screen,
        (73, 46, 35),
        (cell_x + 5, cell_y + 10, TILE_SIZE - 10, 16),
        border_radius=2,
    )
    pygame.draw.line(
        screen,
        (117, 75, 48),
        (cell_x + 6, cell_y + 11),
        (cell_x + TILE_SIZE - 7, cell_y + 11),
    )
    pygame.draw.rect(
        screen,
        ACT_ONE_IRON,
        (cell_x + TILE_SIZE // 2 - 3, cell_y + 8, 6, 20),
    )
    pygame.draw.rect(
        screen,
        ACT_ONE_GOLD,
        (cell_x + TILE_SIZE // 2 - 2, cell_y + 16, 4, 6),
        border_radius=1,
    )


def draw_stairs(
    screen,
    column,
    row,
    is_open,
    act_number,
    sprites,
):
    if act_number >= 2:
        sprite_name = (
            "stairs_open" if is_open else "stairs_locked"
        )
        screen.blit(
            sprites[sprite_name],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
        return

    cell_x = MAP_OFFSET_X + column * TILE_SIZE
    cell_y = MAP_OFFSET_Y + row * TILE_SIZE
    center = (cell_x + TILE_SIZE // 2, cell_y + TILE_SIZE // 2)
    if is_open:
        _draw_act_one_glow(screen, center, (89, 100, 132), 20)
    frame_color = (103, 104, 115) if is_open else (60, 59, 67)
    pygame.draw.arc(
        screen,
        frame_color,
        (cell_x + 6, cell_y + 4, TILE_SIZE - 12, 23),
        0,
        3.14159,
        3,
    )
    pygame.draw.line(
        screen,
        frame_color,
        (cell_x + 6, cell_y + 15),
        (cell_x + 6, cell_y + 28),
        3,
    )
    pygame.draw.line(
        screen,
        frame_color,
        (cell_x + TILE_SIZE - 6, cell_y + 15),
        (cell_x + TILE_SIZE - 6, cell_y + 28),
        3,
    )
    pygame.draw.rect(
        screen,
        (11, 12, 17),
        (cell_x + 9, cell_y + 14, TILE_SIZE - 18, 14),
    )
    for step_number in range(3):
        step_y = cell_y + 20 + step_number * 4
        inset = step_number * 2
        pygame.draw.line(
            screen,
            frame_color,
            (cell_x + 9 - inset, step_y),
            (cell_x + TILE_SIZE - 9 + inset, step_y),
            2,
        )
