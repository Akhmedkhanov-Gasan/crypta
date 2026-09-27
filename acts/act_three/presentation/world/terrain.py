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
            "WallsBack",
            "DecorBack",
        ),
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
