from acts.act_three.presentation.berserker import (
    draw_crushing_leap_targeting,
)
from acts.act_three.presentation.primitives import (
    _draw_archer_barrage_zone_cells,
    _draw_tile_markers,
)
from acts.act_three.presentation.targeting import (
    draw_shadow_step_targeting,
)
from acts.act_three.presentation.view import _view_position
from presentation.layout import ACT_THREE_TILE_SIZE


def draw_world_targeting(
    context,
    game_state,
    assets,
    current_time,
):
    player = game_state.player

    _draw_archer_barrage_zone_cells(
        context.view_surface,
        assets["archer_barrage_zone_cell"],
        player.archer_barrage_zone_cells,
        context.camera_x,
        context.camera_y,
        current_time,
    )

    if player.archer_barrage_zone_aiming:
        _draw_archer_barrage_zone_cells(
            context.view_surface,
            assets["archer_barrage_zone_cell"],
            player.archer_barrage_zone_preview_cells,
            context.camera_x,
            context.camera_y,
            current_time,
            preview=True,
        )

    if player.berserker_crushing_leap_aiming:
        draw_crushing_leap_targeting(
            context.view_surface,
            (
                context.floor.player_column,
                context.floor.player_row,
            ),
            player.berserker_crushing_leap_target,
            player.berserker_crushing_leap_preview_cells,
            context.camera_x,
            context.camera_y,
            current_time,
            ACT_THREE_TILE_SIZE,
        )

    if player.paladin_shield_charge_aiming:
        _draw_tile_markers(
            context.view_surface,
            player.paladin_shield_charge_preview_cells,
            context.camera_x,
            context.camera_y,
            (241, 192, 70),
        )

    if (
        player.teleport_aiming
        and player.teleport_preview_target is not None
    ):
        teleport_preview_target = player.teleport_preview_target
        draw_shadow_step_targeting(
            context.view_surface,
            _view_position(
                context.floor.player_column,
                context.floor.player_row,
                context.camera_x,
                context.camera_y,
            ),
            _view_position(
                teleport_preview_target[0],
                teleport_preview_target[1],
                context.camera_x,
                context.camera_y,
            ),
            current_time,
            ACT_THREE_TILE_SIZE,
        )


def draw_world_attack_markers(context, game_state):
    attack_positions = [
        position
        for enemy in context.floor.enemies
        if (
            enemy.health > 0
            and not (
                enemy.type == "sentinel"
                and enemy.prepared_attack_mode == "shield_bash"
            )
        )
        for position in enemy.attack_targets
    ]
    _draw_tile_markers(
        context.view_surface,
        attack_positions,
        context.camera_x,
        context.camera_y,
        (190, 48, 45),
    )
    _draw_tile_markers(
        context.view_surface,
        game_state.player_attack_targets,
        context.camera_x,
        context.camera_y,
        (210, 152, 42),
    )
