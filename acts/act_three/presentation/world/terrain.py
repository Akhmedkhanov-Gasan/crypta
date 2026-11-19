from acts.act_three.presentation.environment_grading import (
    draw_environment_grading,
)
from acts.act_three.presentation.tile_layers import (
    draw_tile_layer_shadows,
    draw_tile_layers,
    layer_names_by_prefix,
)


def draw_world_terrain(context):
    floor = context.floor
    tile_assets = context.tile_assets

    if not floor.tile_layers or not tile_assets.get("tmx_tiles"):
        return

    draw_tile_layers(
        context.view_surface,
        floor,
        tile_assets,
        layer_names_by_prefix(
            floor,
            "Ground",
            "GroundDetails",
        ),
        context.first_column,
        context.first_row,
        context.last_column,
        context.last_row,
        context.camera_x,
        context.camera_y,
    )
    from acts.act_three.presentation.crushing_trial import draw_layer as draw_crushing_layer

    draw_crushing_layer(context, "ground")
    from acts.act_three.presentation.shield_trial import draw_ground as draw_shield_ground

    draw_shield_ground(context)
    from acts.act_three.presentation.curse_trial import draw_ground as draw_curse_ground

    draw_curse_ground(context)
    draw_crushing_layer(context, "back")
    draw_crushing_layer(context, "front")
    draw_tile_layers(
        context.view_surface,
        floor,
        tile_assets,
        layer_names_by_prefix(floor, "WallsBack", "DecorBack"),
        context.first_column,
        context.first_row,
        context.last_column,
        context.last_row,
        context.camera_x,
        context.camera_y,
    )
    draw_environment_grading(
        context.view_surface,
        floor,
        context.camera_x,
        context.camera_y,
        context.first_column,
        context.first_row,
        context.last_column,
        context.last_row,
    )
    draw_tile_layer_shadows(
        context.view_surface,
        floor,
        tile_assets,
        layer_names_by_prefix(
            floor,
            "DecorMiddle",
            "Objects",
            "Gate",
        ),
        context.first_column,
        context.first_row,
        context.last_column,
        context.last_row,
        context.camera_x,
        context.camera_y,
    )
    draw_tile_layers(
        context.view_surface,
        floor,
        tile_assets,
        layer_names_by_prefix(
            floor,
            "DecorMiddle",
            "Objects",
        ),
        context.first_column,
        context.first_row,
        context.last_column,
        context.last_row,
        context.camera_x,
        context.camera_y,
    )
