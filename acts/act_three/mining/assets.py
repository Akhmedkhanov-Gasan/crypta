import pygame
import resource_store as resources

from acts.act_three.items.inventory import BLACK_ORE_CHUNK, IRON_ORE_CHUNK
from presentation.layout import ACT_THREE_TILE_SIZE, ASSET_ROOT


def _load_player_mining_frames(root, mining_size):
    return {
        direction: tuple(
            pygame.transform.scale(
                resources.load_image(
                    root
                    / "mining"
                    / f"mining_{direction}"
                    / f"mining_{direction}_{index:02d}.png"
                ).convert_alpha(),
                mining_size,
            )
            for index in range(1, 9)
        )
        for direction in ("left", "right")
    }


def load_mining_assets():
    ore_root = ASSET_ROOT / "act_3" / "items" / "ores"
    player_root = ASSET_ROOT / "act_3" / "player"
    size = (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE)
    mining_size = (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE * 2)
    ore_icons = {
        item: resources.load_image(
            ore_root / directory / f"{item}.png"
        ).convert_alpha()
        for item, directory in ((BLACK_ORE_CHUNK, "black_ore"), (IRON_ORE_CHUNK, "iron"))
    }

    return {
        "black_ore_stages": tuple(
            pygame.transform.scale(
                resources.load_image(
                    ore_root / "black_ore" / f"black_ore_{index:02d}.png"
                ).convert_alpha(),
                size,
            )
            for index in range(1, 5)
        ),
        "black_ore_chunk_icon": pygame.transform.scale(
            ore_icons[BLACK_ORE_CHUNK],
            (18, 18),
        ),
        "act_three_inventory_sprites": ore_icons,
        **{
            f"{subclass}_mining_frames": _load_player_mining_frames(
                player_root / subclass,
                size if subclass == "warlock" else mining_size,
            )
            for subclass in (
                "assassin",
                "archer",
                "berserker",
                "paladin",
                "summoner",
                "warlock",
            )
        },
        "summoner_no_familiar_mining_frames": _load_player_mining_frames(
            player_root / "summoner" / "no_familiar",
            mining_size,
        ),
    }
