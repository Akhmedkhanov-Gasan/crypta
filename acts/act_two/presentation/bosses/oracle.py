"""Oracle-specific presentation for Act Two."""

from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


def draw_oracle_projectiles(screen, projectiles, sprites):
    for projectile in projectiles:
        sprite_name = (
            "oracle_projectile_homing"
            if projectile["kind"] == "homing"
            else "oracle_projectile"
        )
        projectile_left = (
            MAP_OFFSET_X + projectile["column"] * TILE_SIZE
        )
        projectile_top = MAP_OFFSET_Y + projectile["row"] * TILE_SIZE
        screen.blit(
            sprites[sprite_name],
            (projectile_left, projectile_top),
        )
