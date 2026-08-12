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


ACT_TWO_ENEMY_ATTACK_FRAME_MS = 240

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


def _draw_oracle(screen, enemy, sprites):
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


def _enemy_sprite_name(enemy, current_time):
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
            if enemy["attack_targets"] or enemy["heal_target"] is not None
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


def _draw_priest_heal_target(screen, enemy):
    if (
        enemy["type"] != "priest"
        or enemy["heal_target"] is None
        or enemy["heal_target"]["health"] <= 0
    ):
        return

    heal_target = enemy["heal_target"]
    pygame.draw.rect(
        screen,
        (80, 220, 130),
        (
            MAP_OFFSET_X + heal_target["column"] * TILE_SIZE + 3,
            MAP_OFFSET_Y + heal_target["row"] * TILE_SIZE + 3,
            TILE_SIZE - 6,
            TILE_SIZE - 6,
        ),
        width=2,
        border_radius=4,
    )


def _draw_standard_enemy(
    screen,
    enemy,
    sprites,
    current_time,
    damage_font,
):
    sprite = sprites[_enemy_sprite_name(enemy, current_time)]
    position = (
        MAP_OFFSET_X + enemy["column"] * TILE_SIZE,
        MAP_OFFSET_Y + enemy["row"] * TILE_SIZE,
    )
    _HIT_FEEDBACK_RENDERERS[enemy["type"]](
        screen,
        enemy,
        sprite,
        position,
        current_time,
        damage_font,
    )
    _draw_sentinel_vulnerable_side(screen, enemy)
    _draw_priest_heal_target(screen, enemy)

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


def _draw_fallback_enemy(screen, enemy):
    padding = TILE_SIZE // 5
    x = MAP_OFFSET_X + enemy["column"] * TILE_SIZE + padding
    y = MAP_OFFSET_Y + enemy["row"] * TILE_SIZE + padding
    size = TILE_SIZE - padding * 2
    color = (
        enemy["color"]
        if enemy["is_aggro"]
        else enemy["sleeping_color"]
    )
    pygame.draw.rect(screen, color, (x, y, size, size), border_radius=6)


def _draw_health_bar(screen, enemy):
    health_ratio = enemy["health"] / enemy["max_health"]
    bar_x = MAP_OFFSET_X + enemy["column"] * TILE_SIZE + 4
    bar_y = MAP_OFFSET_Y + (enemy["row"] + 1) * TILE_SIZE - 5
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


def _draw_attack_warning(screen, enemy):
    if not enemy["attack_targets"]:
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
        return

    if enemy_type == "oracle":
        _draw_oracle(screen, enemy, sprites)
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
        _draw_fallback_enemy(screen, enemy)

    _draw_health_bar(screen, enemy)
    _draw_attack_warning(screen, enemy)
