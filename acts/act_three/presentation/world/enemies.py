import pygame

from acts.act_three.enemies import LANTERN_WARDEN_TYPE
from acts.act_three.presentation.enemies.lantern_warden import (
    draw_lantern_warden,
)
from acts.act_three.presentation.stun_effect import (
    draw_act_three_enemy_stun,
)
from logic import get_enemy_occupied_positions
from acts.act_three.presentation.actors import (
    _draw_enemy_movement_effects,
    _enemy_sprite,
    _enemy_world_position,
)
from acts.act_three.presentation.warlock import (
    draw_warlock_curse_status,
)
from acts.act_three.presentation.animation import _stable_text_seed
from acts.act_three.presentation.combat_effects import (
    _draw_enemy_hit_feedback,
    _enemy_hit_feedback_active,
)
from acts.act_three.presentation.lighting import draw_actor_shadow
from acts.act_three.presentation.primitives import _draw_health_bar
from acts.act_three.presentation.status_effects import (
    _draw_healing_aura,
    _draw_warlock_curse_aura,
)
from acts.act_three.presentation.view import _view_position
from acts.act_two.presentation.enemies.sentinel import (
    draw_sentinel_status,
)
from game.state import EnemyBehaviorState
from presentation.ground_items import draw_ground_items
from presentation.layout import ACT_THREE_TILE_SIZE
from settings import DANGER_BORDER_COLOR, HEALTH_BAR_COLOR


def draw_world_enemies(
    context,
    game_state,
    fonts,
    assets,
    current_time,
):
    floor = context.floor
    stun_visuals = game_state.act_three.enemy_stun_visuals
    living_enemy_ids = {
        id(enemy)
        for enemy in floor.enemies
        if enemy.health > 0
    }
    for enemy_id in tuple(stun_visuals):
        if enemy_id not in living_enemy_ids:
            del stun_visuals[enemy_id]
    visible_enemies = [
        enemy
        for enemy in floor.enemies
        if get_enemy_occupied_positions(enemy) & floor.visible_cells
    ]
    living_enemies = [
        enemy
        for enemy in visible_enemies
        if enemy.health > 0
    ]
    rendered_enemies = [
        enemy
        for enemy in visible_enemies
        if (
            enemy.health > 0
            or enemy.type == LANTERN_WARDEN_TYPE
            or (
                enemy.type
                in ("archer", "brute", "priest", "sentinel")
                and enemy.behavior_state
                is EnemyBehaviorState.DEAD
            )
            or _enemy_hit_feedback_active(
                enemy,
                current_time,
            )
        )
    ]
    healing_aura_seeds = {}

    for enemy in living_enemies:
        heal_target = enemy.heal_target

        if (
            enemy.type == "priest"
            and enemy.behavior_state
            is EnemyBehaviorState.PREPARING_HEAL
            and heal_target is not None
            and heal_target.health > 0
        ):
            link_seed = (
                floor.visual_seed
                ^ _stable_text_seed(
                    f"heal:{enemy.name}:{heal_target.name}"
                )
            )
            healing_aura_seeds[id(enemy)] = link_seed
            healing_aura_seeds[id(heal_target)] = (
                link_seed ^ 0x9E3779B9
            )

    draw_ground_items(
        context.view_surface,
        game_state,
        assets["ground_item_sprites"],
        current_time,
        ACT_THREE_TILE_SIZE,
        (-context.camera_x, -context.camera_y),
    )

    for enemy in living_enemies:
        aura_seed = healing_aura_seeds.get(id(enemy))

        if aura_seed is None:
            continue

        aura_position = _view_position(
            enemy.column,
            enemy.row,
            context.camera_x,
            context.camera_y,
        )
        _draw_healing_aura(
            context.view_surface,
            aura_position[0],
            aura_position[1],
            current_time,
            aura_seed,
        )

    for enemy in sorted(
        rendered_enemies,
        key=lambda living_enemy: (
            living_enemy.row
            + living_enemy.footprint_height
            - 1
        ),
    ):
        if enemy.type == LANTERN_WARDEN_TYPE:
            draw_lantern_warden(
                context,
                assets,
                enemy,
                current_time,
            )
            continue

        enemy_world_position = _enemy_world_position(
            enemy,
            current_time,
            ACT_THREE_TILE_SIZE,
        )
        enemy_position = (
            enemy_world_position[0] - context.camera_x,
            enemy_world_position[1] - context.camera_y,
        )

        enemy_sprite = _enemy_sprite(
            assets,
            enemy,
            current_time,
            floor.visual_seed,
        )
        _draw_enemy_movement_effects(
            context.view_surface,
            assets,
            enemy,
            current_time,
            ACT_THREE_TILE_SIZE,
            context.camera_x,
            context.camera_y,
        )

        if enemy.health > 0:
            draw_actor_shadow(
                context.view_surface,
                enemy_sprite,
                enemy_position,
                ACT_THREE_TILE_SIZE,
                floor.torches,
                context.camera_x,
                context.camera_y,
                (
                    "enemy",
                    enemy.type,
                    enemy_sprite.get_size(),
                ),
            )


        _draw_enemy_hit_feedback(
            context.view_surface,
            enemy_sprite,
            enemy_position,
            enemy,
            current_time,
            fonts["sidebar_numbers"],
        )
        stun_started_at = stun_visuals.get(id(enemy))
        if enemy.health > 0 and stun_started_at is not None:
            draw_act_three_enemy_stun(
                context.view_surface,
                enemy_position,
                ACT_THREE_TILE_SIZE,
                current_time,
                stun_started_at,
                fonts["sidebar_numbers"],
            )
        if enemy.health > 0 and enemy.curse_turns > 0:
            draw_warlock_curse_status(
                context.view_surface,
                enemy_position[0],
                enemy_position[1],
                current_time,
                floor.visual_seed
                ^ _stable_text_seed(
                    f"curse:{enemy.name}"
                ),
                enemy.curse_turns,
                fonts["sidebar_numbers"],
            )
        if enemy.health > 0 and enemy.is_aggro:
            pygame.draw.rect(
                context.view_surface,
                DANGER_BORDER_COLOR,
                (
                    enemy_position[0] + 3,
                    enemy_position[1] + 3,
                    ACT_THREE_TILE_SIZE - 6,
                    ACT_THREE_TILE_SIZE - 6,
                ),
                width=2,
                border_radius=5,
            )

        if enemy.health > 0:
            draw_sentinel_status(
                context.view_surface,
                enemy,
                enemy_position,
                current_time,
                ACT_THREE_TILE_SIZE,
            )
            _draw_health_bar(
                context.view_surface,
                enemy_position[0],
                enemy_position[1],
                enemy.health,
                enemy.max_health,
                HEALTH_BAR_COLOR,
            )
