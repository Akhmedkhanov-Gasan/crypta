from acts.act_three.presentation.tile_layers import _tile_for_gid
from acts.act_three.tile_catalog import TILED_GID_MASK
from presentation.layout import ACT_THREE_TILE_SIZE


def draw_breakable_environment_objects(context, current_time):
    tiles = context.tile_assets.get("tmx_tiles", {})
    animations = context.tile_assets.get("tmx_animations", {})

    for crate in context.floor.breakable_crates:
        if not (
            context.first_column <= crate.column < context.last_column
            and context.first_row <= crate.row < context.last_row
        ):
            continue

        gid = crate.variant
        if crate.is_broken:
            base_gid = gid & TILED_GID_MASK
            frames = animations.get(base_gid, ())
            if frames:
                frame_gid = frames[-1][1]
                if crate.destruction_started_at is not None:
                    elapsed = max(0, current_time - crate.destruction_started_at)
                    if frames[0][1] == base_gid:
                        elapsed += frames[0][0]
                    frame_gid = next(
                        (tile_gid for end, tile_gid in frames if elapsed < end),
                        frame_gid,
                    )
                gid = (gid & ~TILED_GID_MASK) | frame_gid

        sprite = _tile_for_gid(tiles, gid)
        if sprite is not None:
            context.view_surface.blit(
                sprite,
                (
                    crate.column * ACT_THREE_TILE_SIZE - context.camera_x,
                    crate.row * ACT_THREE_TILE_SIZE - context.camera_y,
                ),
            )
