import pygame
import resource_store as resources

from acts.act_three.items.inventory import BLACK_ORE_CHUNK
from presentation.layout import ACT_THREE_TILE_SIZE, ASSET_ROOT


def load_mining_assets():
    ore_root = (
        ASSET_ROOT / "act_3" / "npcs" / "blacksmith" / "ores" / "black_ore"
    )
    player_root = ASSET_ROOT / "act_3" / "player" / "assassin" / "mining"
    size = (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE)
    mining_size = (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE * 2)
    chunk = resources.load_image(ore_root / "black_ore_chunk.png").convert_alpha()

    return {
        "black_ore_stages": tuple(
            pygame.transform.scale(
                resources.load_image(
                    ore_root / f"black_ore_{index:02d}.png"
                ).convert_alpha(),
                size,
            )
            for index in range(1, 5)
        ),
        "black_ore_chunk_icon": pygame.transform.scale(
            chunk,
            (18, 18),
        ),
        "act_three_inventory_sprites": {
            BLACK_ORE_CHUNK: chunk,
        },
        "assassin_mining_frames": {
            direction: tuple(
                pygame.transform.scale(
                    resources.load_image(
                        player_root
                        / f"mining_{direction}"
                        / f"mining_{direction}_{index:02d}.png"
                    ).convert_alpha(),
                    mining_size,
                )
                for index in range(1, 9)
            )
            for direction in ("left", "right")
        },
    }
