import math

import pygame

from acts.act_two.presentation.enemy_effects import (
    draw_act_two_enemy_death,
)
from acts.act_two.presentation.enemies.archer import (
    _draw_act_two_archer_hit_feedback,
)
from acts.act_two.presentation.enemies.brute import (
    _draw_act_two_brute_hit_feedback,
)
from acts.act_two.presentation.enemies.goblin import (
    _draw_act_two_goblin_hit_feedback,
    draw_goblin_summon_effects,
)
from acts.act_two.presentation.enemies.priest import (
    _draw_act_two_priest_hit_feedback,
)
from acts.act_two.presentation.enemies.sentinel import (
    _draw_act_two_sentinel_hit_feedback,
)
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import (
    ATTACK_WARNING_COLOR,
    DANGER_BORDER_COLOR,
    HEALTH_BAR_BACKGROUND,
    HEALTH_BAR_COLOR,
    TILE_SIZE,
)
from acts.act_two.presentation.enemies.timing import (
    ACT_TWO_ENEMY_KNOCKBACK_MS,
    attack_telegraph_is_visible,
    enemy_movement_duration,
)

ACT_TWO_ENEMY_ATTACK_FRAME_MS = 240
_AFTERSHOCK_HIT_FEEDBACK_MS = 520

_STANDARD_ENEMY_TYPES = (
    "goblin",
    "archer",
    "brute",
    "sentinel",
    "priest",
)
_STANDING_SPRITE_NAMES = {
    "goblin": "goblin",
    "archer": "archer",
    "brute": "brute",
    "sentinel": "sentinel_idle",
    "priest": "priest_idle",
}
_HIT_FEEDBACK_RENDERERS = {
    "goblin": _draw_act_two_goblin_hit_feedback,
    "archer": _draw_act_two_archer_hit_feedback,
    "brute": _draw_act_two_brute_hit_feedback,
    "sentinel": _draw_act_two_sentinel_hit_feedback,
    "priest": _draw_act_two_priest_hit_feedback,
}


def _movement_offset(enemy, current_time):
    origin = enemy.get("movement_origin")
    started_at = enemy.get("movement_animation_started_at", 0)
    movement_kind = enemy.get("movement_animation_kind")
    duration = enemy_movement_duration(enemy)
    elapsed = current_time - started_at

    if origin is None or started_at <= 0:
        return 0, 0

    if elapsed < 0:
        return (
            (origin[0] - enemy.column) * TILE_SIZE,
            (origin[1] - enemy.row) * TILE_SIZE,
        )

    if elapsed >= duration:
        return 0, 0

    progress = elapsed / duration
    if movement_kind in (
        "power_cleave_knockback",
        "arcane_burst_knockback",
    ):
        travel = 1 - (1 - progress) ** 3
        lift = round(math.sin(math.pi * progress) * 7)
    else:
        travel = progress * progress * (3 - 2 * progress)
        lift = round(math.sin(math.pi * progress) * 2)
    remaining = 1 - travel
    return (
        round((origin[0] - enemy["column"]) * TILE_SIZE * remaining),
        round((origin[1] - enemy["row"]) * TILE_SIZE * remaining) - lift,
    )


def _draw_oracle(
    screen,
    enemy,
    sprites,
    current_time,
):
    body_size = TILE_SIZE * 3
    body_left = MAP_OFFSET_X + (enemy["column"] - 1) * TILE_SIZE
    body_top = MAP_OFFSET_Y + (enemy["row"] - 1) * TILE_SIZE
    sprite_name = (
        "oracle_awake"
        if enemy["oracle_awakened"]
        else "oracle_idle"
    )
    screen.blit(sprites[sprite_name], (body_left, body_top))

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
    pygame.draw.rect(
        screen,
        HEALTH_BAR_BACKGROUND,
        (bar_x, bar_y, bar_width, 5),
    )
    pygame.draw.rect(
        screen,
        HEALTH_BAR_COLOR,
        (bar_x, bar_y, int(bar_width * health_ratio), 5),
    )

    if attack_telegraph_is_visible(
        enemy,
        current_time,
    ):
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


def _enemy_sprite_name(enemy, current_time):
    if enemy["type"] == "brute":
        return (
            "brute_attack"
            if attack_telegraph_is_visible(
                enemy,
                current_time,
            )
            else "brute"
        )

    sprite_name = enemy["type"]
    attack_started_at = enemy.get("attack_animation_started_at", 0)
    attack_elapsed = current_time - attack_started_at
    if (
        attack_started_at > 0
        and 0 <= attack_elapsed < ACT_TWO_ENEMY_ATTACK_FRAME_MS
    ):
        return (
            "priest_cast"
            if (
                enemy["type"] == "priest"
                and enemy.get("attack_effect_mode") == "heal"
            )
            else f"{enemy['type']}_attack"
        )

    if enemy["type"] == "sentinel":
        return (
            "sentinel_guard"
            if enemy["shield_turns"] > 0
            else "sentinel_idle"
        )
    if enemy["type"] == "priest":
        return (
            "priest_cast"
            if (
                attack_telegraph_is_visible(
                    enemy,
                    current_time,
                )
                or enemy["heal_target"] is not None
            )
            else "priest_idle"
        )
    return sprite_name


def _draw_sentinel_vulnerable_side(screen, enemy):
    if enemy["type"] != "sentinel" or enemy["shield_turns"] <= 0:
        return

    tile_left = MAP_OFFSET_X + enemy["column"] * TILE_SIZE
    tile_top = MAP_OFFSET_Y + enemy["row"] * TILE_SIZE
    shield_direction = enemy["shield_direction"]
    vulnerable_direction = (-shield_direction[0], -shield_direction[1])
    opening_lines = {
        (0, -1): (
            (tile_left + 5, tile_top + 3),
            (tile_left + TILE_SIZE - 5, tile_top + 3),
        ),
        (0, 1): (
            (tile_left + 5, tile_top + TILE_SIZE - 3),
            (tile_left + TILE_SIZE - 5, tile_top + TILE_SIZE - 3),
        ),
        (-1, 0): (
            (tile_left + 3, tile_top + 5),
            (tile_left + 3, tile_top + TILE_SIZE - 5),
        ),
        (1, 0): (
            (tile_left + TILE_SIZE - 3, tile_top + 5),
            (tile_left + TILE_SIZE - 3, tile_top + TILE_SIZE - 5),
        ),
    }
    opening_line = opening_lines.get(vulnerable_direction)
    if opening_line is not None:
        pygame.draw.line(
            screen,
            (235, 185, 75),
            opening_line[0],
            opening_line[1],
            3,
        )


def _draw_standard_enemy(
    screen,
    enemy,
    sprites,
    current_time,
    damage_font,
):
    sprite = sprites[_enemy_sprite_name(enemy, current_time)]
    movement_offset = _movement_offset(enemy, current_time)
    position = (
        MAP_OFFSET_X
        + enemy["column"] * TILE_SIZE
        + movement_offset[0],
        MAP_OFFSET_Y
        + enemy["row"] * TILE_SIZE
        + movement_offset[1],
    )
    _HIT_FEEDBACK_RENDERERS[enemy["type"]](
        screen,
        enemy,
        sprite,
        position,
        current_time,
        damage_font,
    )
    if enemy.type == "goblin":
        draw_goblin_summon_effects(
            screen,
            enemy,
            position,
            current_time,
        )
    _draw_sentinel_vulnerable_side(screen, enemy)

    if enemy["is_aggro"]:
        pygame.draw.rect(
            screen,
            DANGER_BORDER_COLOR,
            (
                position[0] + 2,
                position[1] + 2,
                TILE_SIZE - 4,
                TILE_SIZE - 4,
            ),
            width=2,
            border_radius=3,
        )


def _draw_fallback_enemy(screen, enemy, current_time):
    padding = TILE_SIZE // 5
    movement_offset = _movement_offset(enemy, current_time)
    x = (
        MAP_OFFSET_X
        + enemy["column"] * TILE_SIZE
        + padding
        + movement_offset[0]
    )
    y = (
        MAP_OFFSET_Y
        + enemy["row"] * TILE_SIZE
        + padding
        + movement_offset[1]
    )
    size = TILE_SIZE - padding * 2
    color = (
        enemy["color"]
        if enemy["is_aggro"]
        else enemy["sleeping_color"]
    )
    pygame.draw.rect(screen, color, (x, y, size, size), border_radius=6)


def _draw_health_bar(screen, enemy, current_time):
    movement_offset = _movement_offset(
        enemy,
        current_time,
    )

    health_ratio = enemy["health"] / enemy["max_health"]
    bar_x = (
        MAP_OFFSET_X
        + enemy["column"] * TILE_SIZE
        + movement_offset[0]
        + 4
    )
    bar_y = (
        MAP_OFFSET_Y
        + (enemy["row"] + 1) * TILE_SIZE
        + movement_offset[1]
        - 5
    )
    bar_width = TILE_SIZE - 8

    pygame.draw.rect(
        screen,
        HEALTH_BAR_BACKGROUND,
        (bar_x, bar_y, bar_width, 4),
    )
    pygame.draw.rect(
        screen,
        HEALTH_BAR_COLOR,
        (bar_x, bar_y, int(bar_width * health_ratio), 4),
    )


def _draw_attack_warning(
    screen,
    enemy,
    current_time,
):
    if not attack_telegraph_is_visible(
        enemy,
        current_time,
    ):
        return
    warning_x = (
        MAP_OFFSET_X
        + enemy["column"] * TILE_SIZE
        + TILE_SIZE // 2
    )
    warning_top = MAP_OFFSET_Y + enemy["row"] * TILE_SIZE + 8
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


def _draw_binding_effect(screen, enemy, sprites, current_time):
    if enemy.binding_turns <= 0:
        return
    half_width = enemy.footprint_width // 2
    half_height = enemy.footprint_height // 2
    left = (
        MAP_OFFSET_X
        + (enemy.column - half_width) * TILE_SIZE
        + 3
    )
    top = (
        MAP_OFFSET_Y
        + (enemy.row - half_height) * TILE_SIZE
        + 3
    )
    width = enemy.footprint_width * TILE_SIZE - 6
    height = enemy.footprint_height * TILE_SIZE - 6
    chains = pygame.transform.scale(
        sprites["binding_chains"],
        (width, height),
    )
    pulse = (current_time // 90) % 6
    chains.set_alpha(205 + min(pulse, 5 - pulse) * 10)
    screen.blit(chains, (left, top))


def _draw_rune_status_effects(screen, enemy, current_time):
    center_x = MAP_OFFSET_X + enemy.column * TILE_SIZE + TILE_SIZE // 2
    top_y = (
        MAP_OFFSET_Y
        + (enemy.row - enemy.footprint_height // 2) * TILE_SIZE
    )
    if enemy.stun_turns > 0:
        rotation = current_time / 190
        for star_index in range(3):
            angle = rotation + star_index * math.tau / 3
            star_center = (
                round(center_x + math.cos(angle) * 13),
                round(top_y + 7 + math.sin(angle) * 4),
            )
            pygame.draw.circle(
                screen,
                (246, 203, 77),
                star_center,
                3,
            )
            pygame.draw.circle(
                screen,
                (255, 244, 176),
                star_center,
                1,
            )

    if enemy.bleed_turns > 0:
        pulse = 0.5 + 0.5 * math.sin(current_time / 125)
        for drop_index, x_offset in enumerate((-8, 0, 8)):
            drop_y = round(top_y + 4 + (drop_index % 2) * 5 + pulse * 3)
            pygame.draw.circle(
                screen,
                (145, 18, 28),
                (center_x + x_offset, drop_y),
                3,
            )
            pygame.draw.line(
                screen,
                (220, 47, 48),
                (center_x + x_offset, drop_y - 4),
                (center_x + x_offset, drop_y),
                2,
            )


def _draw_aftershock_hit_feedback(
    screen,
    enemy,
    current_time,
    damage_font,
):
    started_at = enemy.get("aftershock_hit_started_at", -1)
    elapsed = current_time - started_at
    if started_at < 0 or not 0 <= elapsed < _AFTERSHOCK_HIT_FEEDBACK_MS:
        return

    progress = elapsed / _AFTERSHOCK_HIT_FEEDBACK_MS
    visibility = max(0.0, 1.0 - progress)
    center = (
        MAP_OFFSET_X + enemy["column"] * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + enemy["row"] * TILE_SIZE + TILE_SIZE // 2,
    )
    effect = pygame.Surface(
        (TILE_SIZE * 2, TILE_SIZE * 2),
        pygame.SRCALPHA,
    )
    local_center = (TILE_SIZE, TILE_SIZE)
    radius = round(8 + min(1.0, progress * 2.5) * 19)
    pygame.draw.circle(
        effect,
        (232, 49, 43, round(190 * visibility)),
        local_center,
        radius,
        width=5,
    )
    pygame.draw.circle(
        effect,
        (255, 184, 104, round(235 * visibility)),
        local_center,
        max(3, radius - 4),
        width=2,
    )
    for slash_offset in (-7, 7):
        pygame.draw.line(
            effect,
            (255, 219, 162, round(230 * visibility)),
            (TILE_SIZE - 13 + slash_offset, TILE_SIZE + 11),
            (TILE_SIZE + 8 + slash_offset, TILE_SIZE - 12),
            3,
        )
    screen.blit(
        effect,
        (center[0] - TILE_SIZE, center[1] - TILE_SIZE),
    )

    damage = enemy.get("aftershock_hit_damage", 0)
    if damage_font is None or damage <= 0:
        return
    number = damage_font.render(str(damage), True, (255, 174, 102))
    number.set_alpha(round(255 * min(1.0, visibility * 1.8)))
    rectangle = number.get_rect(
        midbottom=(
            center[0] + 13,
            center[1] - 10 - round(progress * 13),
        )
    )
    screen.blit(number, rectangle)


def draw_act_two_enemy(
    screen,
    enemy,
    sprites,
    current_time=0,
    damage_font=None,
):
    enemy_type = enemy["type"]
    if enemy_type in _STANDARD_ENEMY_TYPES and enemy["health"] <= 0:
        draw_act_two_enemy_death(
            screen,
            enemy,
            sprites[_STANDING_SPRITE_NAMES[enemy_type]],
            sprites[f"{enemy_type}_death"],
            current_time,
            damage_font,
        )
        _draw_aftershock_hit_feedback(
            screen, enemy, current_time, damage_font
        )
        return

    if enemy_type == "oracle":
        _draw_oracle(
            screen,
            enemy,
            sprites,
            current_time,
        )
        _draw_binding_effect(screen, enemy, sprites, current_time)
        _draw_rune_status_effects(screen, enemy, current_time)
        _draw_aftershock_hit_feedback(
            screen, enemy, current_time, damage_font
        )
        return

    if enemy_type in _STANDARD_ENEMY_TYPES:
        _draw_standard_enemy(
            screen,
            enemy,
            sprites,
            current_time,
            damage_font,
        )
    else:
        _draw_fallback_enemy(screen, enemy, current_time)

    _draw_health_bar(
        screen,
        enemy,
        current_time,
    )
    _draw_attack_warning(
        screen,
        enemy,
        current_time,
    )
    _draw_binding_effect(screen, enemy, sprites, current_time)
    _draw_rune_status_effects(screen, enemy, current_time)
    _draw_aftershock_hit_feedback(
        screen, enemy, current_time, damage_font
    )
