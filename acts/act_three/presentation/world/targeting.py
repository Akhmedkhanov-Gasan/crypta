from acts.act_three.presentation.berserker import (
    draw_crushing_leap_targeting,
)
from acts.act_three.presentation.mage import (
    draw_act_three_arcane_burst_targeting,
)
from acts.act_three.combat.warlock_aim import valid_warlock_aim_target
from acts.act_three.presentation.paladin.sacred_ground import (
    draw_paladin_sacred_ground_cells,
)
from acts.act_three.presentation.paladin.shield_charge import (
    draw_shield_charge_targeting,
)
from acts.act_three.presentation.primitives import (
    _draw_tile_markers,
)
from acts.act_three.presentation.archer.barrage_zone import (
    draw_barrage_zone_cells,
)
from acts.act_three.presentation.targeting import (
    draw_shadow_step_targeting,
)
from acts.act_three.presentation.view import _view_position
from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.enemies.catalog import LANTERN_WARDEN_TYPE
from acts.act_three.presentation.enemies.lantern_warden.lantern_warden_combat import (
    draw_warden_telegraph,
)
from acts.act_three.presentation.enemies.telegraphs import (
    draw_enemy_attack_markers,
)
from acts.act_three.presentation.warrior.power_cleave import (
    draw_power_cleave_targeting,
)
from acts.act_three.presentation.summoner.summon_effect import (
    draw_summoner_familiar_summon_targeting,
)


def draw_world_targeting(
    context,
    game_state,
    assets,
    current_time,
):
    player = game_state.player
    target = player.warlock_aim_target
    if player.warlock_curse_aiming and valid_warlock_aim_target(game_state, target):
        _draw_tile_markers(
            context.view_surface,
            (target,),
            context.camera_x,
            context.camera_y,
            (206, 97, 245),
        )

    draw_summoner_familiar_summon_targeting(
        context.view_surface,
        game_state,
        context.camera_x,
        context.camera_y,
        current_time,
    )

    draw_paladin_sacred_ground_cells(
        context.view_surface,
        player.paladin_sacred_ground_cells if player.act_three.paladin_sacred_ground_floor in (None, game_state.floor_index) else (),
        player.paladin_sacred_ground_anchor,
        context.camera_x,
        context.camera_y,
        current_time,
        ACT_THREE_TILE_SIZE,
    )

    draw_power_cleave_targeting(
        context.view_surface,
        game_state,
        context.camera_x,
        context.camera_y,
        current_time,
        ACT_THREE_TILE_SIZE,
    )
    draw_barrage_zone_cells(
        context.view_surface,
        player.archer_barrage_zone_cells,
        context.camera_x,
        context.camera_y,
        current_time,
        ACT_THREE_TILE_SIZE,
    )

    if player.archer_barrage_zone_aiming:
        draw_barrage_zone_cells(
            context.view_surface,
            player.archer_barrage_zone_preview_cells,
            context.camera_x,
            context.camera_y,
            current_time,
            ACT_THREE_TILE_SIZE,
            preview=True,
        )

    if player.berserker_crushing_leap_aiming:
        draw_crushing_leap_targeting(
            context.view_surface,
            (
                context.floor.player_column,
                context.floor.player_row,
            ),
            player.berserker_crushing_leap_preview_cells,
            context.camera_x,
            context.camera_y,
            current_time,
            ACT_THREE_TILE_SIZE,
        )

    if player.paladin_shield_charge_aiming:
        draw_shield_charge_targeting(
            context.view_surface,
            (
                context.floor.player_column,
                context.floor.player_row,
            ),
            player.paladin_shield_charge_preview_cells,
            context.camera_x,
            context.camera_y,
            current_time,
            ACT_THREE_TILE_SIZE,
        )

    draw_act_three_arcane_burst_targeting(
        context.view_surface,
        game_state,
        context.camera_x,
        context.camera_y,
        ACT_THREE_TILE_SIZE,
        current_time,
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


def draw_world_attack_markers(context, game_state, current_time):
    draw_enemy_attack_markers(context, current_time)

    for enemy in context.floor.enemies:
        if (
            enemy.health > 0
            and enemy.type == LANTERN_WARDEN_TYPE
            and enemy.attack_targets
        ):
            draw_warden_telegraph(
                context,
                enemy,
                current_time,
                ACT_THREE_TILE_SIZE,
            )
