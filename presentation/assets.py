import pygame
import xml.etree.ElementTree as ET

import json

from acts.act_two.rune_catalog import RUNE_DEFINITIONS
from levels import FLOOR_CONFIGS
from presentation.layout import (
    ACT_THREE_TILE_SIZE,
    ASSET_ROOT,
    FONT_ROOT,
    PROJECT_ROOT,
)
from settings import GAME_HEIGHT, GAME_WIDTH, TILE_SIZE


def load_act_one_fonts():
    regular_path = FONT_ROOT / "AtkinsonHyperlegible-Regular.ttf"
    bold_path = FONT_ROOT / "AtkinsonHyperlegible-Bold.ttf"
    pixel_path = FONT_ROOT / "PixelOperator.ttf"
    pixel_bold_path = FONT_ROOT / "PixelOperator-Bold.ttf"

    return {
        "title": pygame.font.Font(str(bold_path), 42),
        "heading": pygame.font.Font(str(bold_path), 27),
        "status": pygame.font.Font(str(bold_path), 21),
        "text": pygame.font.Font(str(regular_path), 19),
        "controls": pygame.font.Font(str(bold_path), 17),
        "interface": pygame.font.Font(str(regular_path), 19),
        "hud": pygame.font.Font(str(pixel_bold_path), 19),
        "hud_small": pygame.font.Font(str(pixel_path), 16),
    }


def load_act_one_gameplay_assets():
    ui_directory = ASSET_ROOT / "ui" / "act_1"

    return {
        "act_one_hud_frame": _load_scaled_image(
            ui_directory / "hud_frame_act1.png",
            (466, 121),
        ),
        "act_one_health_fill": _load_scaled_image(
            ui_directory / "hp_bar_act1.png",
            (389, 34),
        ),
        "act_one_bottom_bar": _load_scaled_image(
            ui_directory / "skill+belt_bar_act1.png",
            (736, 245),
        ),
        "act_one_upgrade": _load_scaled_image(
            ui_directory / "upgrade.png",
            (1080, 608),
        ),
        "act_one_potion": _create_act_one_health_potion(),
    }


def _create_act_one_health_potion():
    potion = pygame.Surface((26, 30), pygame.SRCALPHA)

    pygame.draw.polygon(
        potion,
        (8, 7, 11),
        ((8, 8), (18, 8), (22, 13), (22, 25), (19, 28),
         (7, 28), (4, 25), (4, 13)),
    )
    pygame.draw.polygon(
        potion,
        (129, 20, 31),
        ((9, 9), (17, 9), (20, 14), (20, 24), (18, 26),
         (8, 26), (6, 24), (6, 14)),
    )
    pygame.draw.rect(potion, (213, 42, 52), (8, 14, 10, 10))
    pygame.draw.rect(potion, (255, 112, 105), (9, 14, 3, 8))
    pygame.draw.rect(potion, (32, 25, 29), (8, 3, 10, 6))
    pygame.draw.rect(potion, (91, 79, 71), (9, 1, 8, 4))
    pygame.draw.rect(potion, (241, 226, 211), (11, 16, 4, 8))
    pygame.draw.rect(potion, (241, 226, 211), (9, 18, 8, 4))
    return pygame.transform.scale(potion, (22, 25))


def load_menu_assets():
    menu_directory = ASSET_ROOT / "ui" / "menu"

    act_one_directory = menu_directory / "act_1"
    act_two_directory = menu_directory / "act_2"
    act_three_directory = menu_directory / "act_3"

    return {
        "act_two_background": pygame.image.load(
            str(act_two_directory / "act_2_background.png")
        ).convert(),

        "act_three_background": pygame.image.load(
            str(act_three_directory / "act_3_background.png")
        ).convert(),

        "act_three_menu_frame": pygame.image.load(
            str(act_three_directory / "menu_frame.png")
        ).convert_alpha(),

        "act_three_menu_title": pygame.image.load(
            str(act_three_directory / "menu_title.png")
        ).convert_alpha(),

        "act_two_menu_frame": pygame.image.load(
            str(act_two_directory / "menu_frame.png")
        ).convert_alpha(),

        "act_two_menu_title": pygame.image.load(
            str(act_two_directory / "menu_title.png")
        ).convert_alpha(),

        "act_one_menu_frame": pygame.image.load(
            str(act_one_directory / "menu_frame.png")
        ).convert_alpha(),

        "act_one_menu_title": pygame.image.load(
            str(act_one_directory / "menu_title.png")
        ).convert_alpha(),
    }


def load_menu_layouts(act):
    layout_directory = (
        PROJECT_ROOT
        / "assets"
        / "ui"
        / "layouts"
        / f"act_{act}"
    )

    layouts = {}

    for page in ("main", "settings", "confirm"):
        layout_path = layout_directory / f"{page}.json"

        with layout_path.open(encoding="utf-8") as file:
            layouts[page] = json.load(file)

    return layouts

def load_act_two_fonts():
    pixelify_directory = FONT_ROOT / "Pixelify_Sans"
    pixel_operator_bold_path = FONT_ROOT / "PixelOperator-Bold.ttf"
    regular_path = pixelify_directory / "PixelifySans-Regular.ttf"
    medium_path = pixelify_directory / "PixelifySans-Medium.ttf"
    semibold_path = pixelify_directory / "PixelifySans-SemiBold.ttf"
    bold_path = pixelify_directory / "PixelifySans-Bold.ttf"
    alagard_path = FONT_ROOT / "alagard" / "alagard.ttf"

    return {
        "title": pygame.font.Font(str(alagard_path), 42),
        "heading": pygame.font.Font(str(alagard_path), 20),
        "status": pygame.font.Font(str(alagard_path), 22),
        "text": pygame.font.Font(str(alagard_path), 18),
        "log": pygame.font.Font(str(alagard_path), 15),
        "ability_text": pygame.font.Font(str(alagard_path), 12),
        "controls": pygame.font.Font(str(alagard_path), 17),
        "sidebar_heading": pygame.font.Font(str(alagard_path), 15), # lvl
        "sidebar_text": pygame.font.Font(str(alagard_path), 15),
        "sidebar_controls": pygame.font.Font(str(alagard_path), 12), # HP and XP
        "trade_name": pygame.font.Font(str(alagard_path), 12),
        "trade_description": pygame.font.Font(str(alagard_path), 10),
        "trade_price": pygame.font.Font(str(alagard_path), 12),
    }


def load_act_two_trade_layout():
    layout_path = (
        PROJECT_ROOT
        / "assets"
        / "ui"
        / "layouts"
        / "act_2"
        / "trade.json"
    )

    with layout_path.open(encoding="utf-8") as file:
        return json.load(file)


def load_act_three_fonts():
    display_path = FONT_ROOT / "Sandey Molse DEMO.ttf"
    hud_path = FONT_ROOT / "Almendra-Regular.ttf"
    hud_bold_path = FONT_ROOT / "Almendra-Bold.ttf"
    interface_path = FONT_ROOT / "AtkinsonHyperlegible-Regular.ttf"
    interface_bold_path = FONT_ROOT / "AtkinsonHyperlegible-Bold.ttf"

    hud_value_font = pygame.font.Font(str(hud_path), 17)
    hud_value_font.set_bold(True)
    hud_value_font.set_italic(True)

    return {
        "title": pygame.font.Font(str(display_path), 46),
        "heading": pygame.font.Font(str(display_path), 28),
        "narrative": pygame.font.Font(str(display_path), 27),
        "text": pygame.font.Font(str(interface_path), 20),
        "sidebar_display": pygame.font.Font(
            str(display_path),
            23,
        ),
        "sidebar_heading": pygame.font.Font(
            str(interface_bold_path),
            22,
        ),
        "sidebar_text": pygame.font.Font(
            str(interface_path),
            19,
        ),
        "sidebar_log": pygame.font.Font(
            str(interface_path),
            16,
        ),
        "sidebar_hud": pygame.font.Font(
            str(interface_path),
            13,
        ),
        "hud_value": hud_value_font,
        "hud_level": pygame.font.Font(str(hud_bold_path), 18),
        "sidebar_class": pygame.font.Font(
            str(display_path),
            19,
        ),
        "sidebar_numbers": pygame.font.Font(
            str(interface_bold_path),
            18,
        ),
    }


def load_act_two_sprites():
    asset_directory = ASSET_ROOT / "act_2"
    ui_directory = ASSET_ROOT / "ui" / "act_2"
    sprite_paths = {
        "player_level_up_0": "player/lvl_up_1111.png",
        "player_level_up_1": "player/lvl_up_211.png",
        "player_warrior": "player/warrior/idle/idle_00.png",
        "player_warrior_hurt": "player/warrior/hurt/hurt_00.png",
        "player_warrior_walk_0": "player/warrior/walk/down/walk_00.png",
        "player_warrior_walk_1": "player/warrior/walk/down/walk_01.png",
        "player_warrior_walk_2": "player/warrior/walk/down/walk_02.png",
        "player_warrior_walk_side_right_0": (
            "player/warrior/walk/side/walk_00.png"
        ),
        "player_warrior_walk_side_right_1": (
            "player/warrior/walk/side/walk_01.png"
        ),
        "player_warrior_walk_side_right_2": (
            "player/warrior/walk/side/walk_02.png"
        ),
        "player_warrior_walk_up_0": "player/warrior/walk/up/walk_00.png",
        "player_warrior_walk_up_1": "player/warrior/walk/up/walk_01.png",
        "player_warrior_walk_up_2": "player/warrior/walk/up/walk_02.png",
        "player_warrior_attack_side_right_0": (
            "player/warrior/attack/side/attack_00.png"
        ),
        "player_warrior_attack_side_right_1": (
            "player/warrior/attack/side/attack_01.png"
        ),
        "player_warrior_attack_side_right_2": (
            "player/warrior/attack/side/attack_02.png"
        ),
        "player_warrior_attack_up_0": (
            "player/warrior/attack/up/attack_00.png"
        ),
        "player_warrior_attack_up_1": (
            "player/warrior/attack/up/attack_01.png"
        ),
        "player_warrior_attack_up_2": (
            "player/warrior/attack/up/attack_02.png"
        ),
        "player_warrior_attack_down_0": (
            "player/warrior/attack/down/attack_00.png"
        ),
        "player_warrior_attack_down_1": (
            "player/warrior/attack/down/attack_01.png"
        ),
        "player_warrior_attack_down_2": (
            "player/warrior/attack/down/attack_02.png"
        ),
        "player_warrior_death_0": "player/warrior/death/death_00.png",
        "player_warrior_death_1": "player/warrior/death/death_01.png",
        "player_rogue": "player/rogue/idle/idle_00.png",
        "player_rogue_walk_0": "player/rogue/walk/down/walk_00.png",
        "player_rogue_walk_1": "player/rogue/walk/down/walk_01.png",
        "player_rogue_walk_2": "player/rogue/walk/down/walk_02.png",
        "player_rogue_walk_side_right_0": (
            "player/rogue/walk/side/walk_00.png"
        ),
        "player_rogue_walk_side_right_1": (
            "player/rogue/walk/side/walk_01.png"
        ),
        "player_rogue_walk_side_right_2": (
            "player/rogue/walk/side/walk_02.png"
        ),
        "player_rogue_walk_up_0": "player/rogue/walk/up/walk_00.png",
        "player_rogue_walk_up_1": "player/rogue/walk/up/walk_01.png",
        "player_rogue_walk_up_2": "player/rogue/walk/up/walk_02.png",
        "player_rogue_attack_side_right": (
            "player/rogue/attack/side/attack_00.png"
        ),
        "player_rogue_attack_side_left": (
            "player/rogue/attack/side/attack_left_00.png"
        ),
        "player_rogue_attack_down": (
            "player/rogue/attack/down/attack_00.png"
        ),
        "player_rogue_attack_up": (
            "player/rogue/attack/up/attack_00.png"
        ),
        "player_rogue_death_0": "player/rogue/death/death_00.png",
        "player_rogue_death_1": "player/rogue/death/death_01.png",
        "player_mage": "player/mage/idle/idle_00.png",
        "player_mage_walk_0": "player/mage/walk/down/walk_00.png",
        "player_mage_walk_1": "player/mage/walk/down/walk_01.png",
        "player_mage_walk_2": "player/mage/walk/down/walk_02.png",
        "player_mage_walk_side_right_0": (
            "player/mage/walk/side/walk_00.png"
        ),
        "player_mage_walk_side_right_1": (
            "player/mage/walk/side/walk_01.png"
        ),
        "player_mage_walk_side_right_2": (
            "player/mage/walk/side/walk_02.png"
        ),
        "player_mage_walk_up_0": "player/mage/walk/up/walk_00.png",
        "player_mage_walk_up_1": "player/mage/walk/up/walk_01.png",
        "player_mage_walk_up_2": "player/mage/walk/up/walk_02.png",
        "player_mage_attack_side_right": (
            "player/mage/attack/side/attack_00.png"
        ),
        "player_mage_attack_side_left": (
            "player/mage/attack/side/attack_left_00.png"
        ),
        "player_mage_death_0": "player/mage/death/death_00.png",
        "player_mage_death_1": "player/mage/death/death_01.png",
        "old_man_standing": "npcs/old_man/standing/standing_00.png",
        "old_man_kneeling": "npcs/old_man/kneeling/kneeling_00.png",
        "trader_idle_0": "npcs/trader/trader_1.png",
        "trader_idle_1": "npcs/trader/trader_2.png",
        "trader_idle_2": "npcs/trader/trader_3.png",
        "trader_idle_3": "npcs/trader/trader_4.png",
        "goblin": "enemies/goblin/idle/idle_00.png",
        "goblin_attack": "enemies/goblin/attack/attack_00.png",
        "goblin_death": "enemies/goblin/death/death_00.png",
        "brute": "enemies/brute/idle/idle_00.png",
        "brute_attack": "enemies/brute/attack/attack_00.png",
        "brute_death": "enemies/brute/death/death_00.png",
        "archer": "enemies/archer/idle/idle_00.png",
        "archer_attack": "enemies/archer/attack/attack_00.png",
        "archer_death": "enemies/archer/death/death_00.png",
        "sentinel_idle": "enemies/sentinel/idle/idle_00.png",
        "sentinel_attack": "enemies/sentinel/attack/attack_00.png",
        "sentinel_guard": "enemies/sentinel/guard/guard_00.png",
        "sentinel_death": "enemies/sentinel/death/death_00.png",
        "priest_idle": "enemies/priest/idle/idle_00.png",
        "priest_attack": "enemies/priest/attack/attack_00.png",
        "priest_cast": "enemies/priest/cast/cast_00.png",
        "priest_death": "enemies/priest/death/death_00.png",
        "oracle_idle": "bosses/oracle/idle/idle_00.png",
        "oracle_awake": "bosses/oracle/awake/awake_00.png",
        "oracle_projectile": "bosses/oracle/projectiles/projectile.png",
        "oracle_projectile_homing": (
            "bosses/oracle/projectiles/projectile_homing.png"
        ),
        "pillar": "bosses/oracle/arena/pillar.png",
        "charged_pillar": "bosses/oracle/arena/charged_pillar.png",
        "floor": "environment/tiles/floor.png",
        "floor_layout_b": (
            "environment/tiles/floor_variants/floor_layout_b.png"
        ),
        "floor_fissure": (
            "environment/tiles/floor_variants/floor_fissure.png"
        ),
        "floor_fissure_cross": (
            "environment/tiles/floor_variants/floor_fissure_cross.png"
        ),
        "floor_puddle": (
            "environment/tiles/floor_variants/floor_puddle.png"
        ),
        "floor_rubble_heavy": (
            "environment/tiles/floor_variants/floor_rubble_heavy.png"
        ),
        "floor_drain": (
            "environment/tiles/floor_variants/floor_drain.png"
        ),
        "floor_burial_seal": (
            "environment/tiles/floor_variants/floor_burial_seal.png"
        ),
        "spike_trap_hole": "environment/traps/spike_trap_hole.png",
        "spike_trap_warning": "environment/traps/spike_trap_warning.png",
        "spike_trap_active": "environment/traps/spike_trap_active.png",
        "wall": "environment/tiles/wall.png",
        "wall_torch": (
            "environment/tiles/wall_variants/wall_torch.png"
        ),
        "wall_chains": (
            "environment/tiles/wall_variants/wall_chains.png"
        ),
        "wall_broken": (
            "environment/tiles/wall_variants/wall_broken.png"
        ),
        "wall_iron_shackle": (
            "environment/tiles/wall_variants/wall_iron_shackle.png"
        ),
        "wall_secret": (
            "environment/tiles/wall_variants/wall_secret.png"
        ),
        "wall_secret_2": (
            "environment/tiles/wall_variants/wall_secret_2.png"
        ),
        "wall_damp": (
            "environment/tiles/wall_variants/wall_damp.png"
        ),
        "wall_skull_niche": (
            "environment/tiles/wall_variants/wall_skull_niche.png"
        ),
        "decor_floor_broken_barrel": (
            "environment/decor/floor/broken_barrel.png"
        ),
        "decor_floor_skeleton_sprawled": (
            "environment/decor/floor/skeleton_sprawled.png"
        ),
        "decor_floor_skeleton_curled": (
            "environment/decor/floor/skeleton_curled.png"
        ),
        "decor_floor_bone_pile": (
            "environment/decor/floor/bone_pile.png"
        ),
        "decor_floor_broken_crate": (
            "environment/decor/floor/broken_crate.png"
        ),
        "decor_floor_urn_shards": (
            "environment/decor/floor/urn_shards.png"
        ),
        "decor_floor_boss_brazier": (
            "environment/decor/floor/boss_brazier.png"
        ),
        "decor_wall_cobweb": "environment/decor/wall/cobweb.png",
        "decor_wall_torn_banner": (
            "environment/decor/wall/torn_banner.png"
        ),
        "decor_wall_guardian_statue": (
            "environment/decor/wall/guardian_statue.png"
        ),
        "decor_wall_mourner_statue": (
            "environment/decor/wall/mourner_statue.png"
        ),
        "stairs_locked": "environment/stairs/locked.png",
        "stairs_open": "environment/stairs/open.png",
        "potion": "items/consumables/potion.png",
        "potion_belt": "items/consumables/potion_belt.png",
        "fire_bomb": "items/consumables/fire_bomb.png",
        "fire_bomb_belt": "items/consumables/fire_bomb_belt.png",
        "scroll_of_stoneflesh": (
            "items/consumables/scroll_of_stoneflesh.png"
        ),
        "scroll_of_binding": (
            "items/consumables/scroll_of_binding.png"
        ),
        "healing_scroll": "items/consumables/healing_scroll.png",
        "scroll_of_arcane_impulse": (
            "items/consumables/scroll_of_impulse.png"
        ),
        "binding_chains": "items/consumables/effects/chains.png",
        "fire_0": "environment/effects/fire/fire_00.png",
        "fire_1": "environment/effects/fire/fire_01.png",
        "fire_2": "environment/effects/fire/fire_02.png",
        "fire_3": "environment/effects/fire/fire_03.png",
        "key": "items/loot/key.png",
        "key_belt": "items/loot/key_belt.png",
        "coin": "items/loot/coin.png",
        "chest_closed": "items/chests/closed.png",
        "chest_open": "items/chests/open.png",
        "stash_closed": "items/chests/closed_stash.png",
        "stash_open": "items/chests/open_stash.png",
        "treasury_chest": "items/chests/treasury_closed.png",
        "breakable_crate_1": (
            "environment/objects/breakable_crates/crate_01.png"
        ),
        "breakable_crate_1_broken": (
            "environment/objects/breakable_crates/crate_01_broken.png"
        ),
        "breakable_crate_2": (
            "environment/objects/breakable_crates/crate_02.png"
        ),
        "breakable_crate_2_broken": (
            "environment/objects/breakable_crates/crate_02_broken.png"
        ),
        "breakable_crate_3": (
            "environment/objects/breakable_crates/crate_03.png"
        ),
        "breakable_crate_3_broken": (
            "environment/objects/breakable_crates/crate_03_broken.png"
        ),
        "treasury_guardian_knight": (
            "environment/objects/treasury_guardian_knight.png"
        ),
        "treasury_guardian_knight_red": (
            "environment/objects/treasury_guardian_knight_red.png"
        ),
        "treasury_guardian_hooded": (
            "environment/objects/treasury_guardian_hooded.png"
        ),
        "treasury_guardian_hooded_red": (
            "environment/objects/treasury_guardian_hooded_red.png"
        ),
        "treasury_gate_horizontal": (
            "environment/tiles/doorways/treasury_gate.png"
        ),
        "rune_pedestal": "environment/objects/rune_pedestal.png",
        "rune_pedestal_reward": (
            "environment/objects/rune_pedestal_reward.png"
        ),
        "rune_trident": "environment/runes/rune_trident.png",
        "rune_eye": "environment/runes/rune_eye.png",
        "rune_spiral": "environment/runes/rune_spiral.png",
    }

    sprites = {}
    oversized_sprite_names = {"oracle_idle", "oracle_awake"}
    for name, relative_path in sprite_paths.items():
        source_path = asset_directory / relative_path
        source = pygame.image.load(str(source_path)).convert_alpha()
        if name in oversized_sprite_names:
            sprites[name] = pygame.transform.scale(
                source,
                (TILE_SIZE * 3, TILE_SIZE * 3),
            )
            continue
        if name == "binding_chains":
            sprites[name] = pygame.transform.scale(
                source,
                (TILE_SIZE, TILE_SIZE),
            )
            continue
        if source.get_size() != (TILE_SIZE, TILE_SIZE):
            raise ValueError(
                "Act Two gameplay asset must be "
                f"{TILE_SIZE}x{TILE_SIZE}, got "
                f"{source.get_width()}x{source.get_height()}: "
                f"{source_path}"
            )
        sprites[name] = source
    sprites["treasury_gate_vertical"] = pygame.transform.rotate(
        sprites["treasury_gate_horizontal"],
        90,
    )

    trade_item_directory = asset_directory / "items" / "consumables"

    sprites.update(
        {
            "trader_potion": pygame.image.load(
                str(trade_item_directory / "potion_original.png")
            ).convert_alpha(),

            "trader_scroll_of_binding": pygame.image.load(
                str(
                    trade_item_directory
                    / "scroll_of_binding_original.png"
                )
            ).convert_alpha(),

            "trader_scroll_of_arcane_impulse": pygame.image.load(
                str(
                    trade_item_directory
                    / "scroll_of_impulse_original.png"
                )
            ).convert_alpha(),

            "trader_healing_scroll": pygame.image.load(
                str(
                    trade_item_directory
                    / "healing_scroll_original.png"
                )
            ).convert_alpha(),

            "trader_scroll_of_stoneflesh": pygame.image.load(
                str(
                    trade_item_directory
                    / "scroll_of_stoneflesh_original.png"
                )
            ).convert_alpha(),
        }
    )

    for frame_index in range(3):
        sprites[f"player_warrior_walk_side_left_{frame_index}"] = (
            pygame.transform.flip(
                sprites[
                    f"player_warrior_walk_side_right_{frame_index}"
                ],
                True,
                False,
            )
        )
        sprites[f"player_warrior_attack_side_left_{frame_index}"] = (
            pygame.transform.flip(
                sprites[
                    f"player_warrior_attack_side_right_{frame_index}"
                ],
                True,
                False,
            )
        )
        sprites[f"player_rogue_walk_side_left_{frame_index}"] = (
            pygame.transform.flip(
                sprites[
                    f"player_rogue_walk_side_right_{frame_index}"
                ],
                True,
                False,
            )
        )
        sprites[f"player_mage_walk_side_left_{frame_index}"] = (
            pygame.transform.flip(
                sprites[
                    f"player_mage_walk_side_right_{frame_index}"
                ],
                True,
                False,
            )
        )
    for floor_sprite_name in (
        "floor",
        "floor_layout_b",
        "floor_fissure",
        "floor_fissure_cross",
        "floor_puddle",
        "floor_rubble_heavy",
        "floor_drain",
        "floor_burial_seal",
    ):
        sprites[floor_sprite_name].fill(
            (150, 145, 160),
            special_flags=pygame.BLEND_RGB_MULT,
        )
    for wall_sprite_name in (
        "wall",
        "wall_torch",
        "wall_chains",
        "wall_broken",
        "wall_iron_shackle",
        "wall_damp",
        "wall_skull_niche",
    ):
        sprites[wall_sprite_name].fill(
            (10, 12, 16),
            special_flags=pygame.BLEND_RGB_ADD,
        )
    awakening_source = pygame.image.load(
        str(ui_directory / "awakening.png")
    ).convert()
    source_width, source_height = awakening_source.get_size()
    target_ratio = GAME_WIDTH / GAME_HEIGHT
    source_ratio = source_width / source_height

    if source_ratio > target_ratio:
        crop_width = int(source_height * target_ratio)
        crop_rectangle = pygame.Rect(
            (source_width - crop_width) // 2,
            0,
            crop_width,
            source_height,
        )
    else:
        crop_height = int(source_width / target_ratio)
        crop_rectangle = pygame.Rect(
            0,
            (source_height - crop_height) // 2,
            source_width,
            crop_height,
        )

    awakening_small = pygame.transform.smoothscale(
        awakening_source.subsurface(crop_rectangle),
        (320, 180),
    )

    if hasattr(pygame.transform, "grayscale"):
        awakening_gray = pygame.transform.grayscale(
            awakening_small
        )
        awakening_gray.set_alpha(75)
        awakening_small.blit(awakening_gray, (0, 0))

    awakening_small.fill(
        (145, 140, 160),
        special_flags=pygame.BLEND_RGB_MULT,
    )
    sprites["awakening"] = pygame.transform.scale(
        awakening_small,
        (GAME_WIDTH, GAME_HEIGHT),
    )

    transition_directory = ui_directory / "awakening_v2"

    def load_transition_background(filename):
        source = pygame.image.load(
            str(transition_directory / filename)
        ).convert()
        source_width, source_height = source.get_size()
        target_ratio = GAME_WIDTH / GAME_HEIGHT
        source_ratio = source_width / source_height
        if source_ratio > target_ratio:
            crop_width = round(source_height * target_ratio)
            crop = pygame.Rect(
                (source_width - crop_width) // 2,
                0,
                crop_width,
                source_height,
            )
        else:
            crop_height = round(source_width / target_ratio)
            crop = pygame.Rect(
                0,
                (source_height - crop_height) // 2,
                source_width,
                crop_height,
            )
        return pygame.transform.scale(
            source.subsurface(crop),
            (GAME_WIDTH, GAME_HEIGHT),
        )

    sprites["awakening_act_one"] = load_transition_background(
        "act_one_corridor_source.png"
    )
    sprites["awakening_act_two"] = load_transition_background(
        "act_two_corridor_source.png"
    )
    old_man = pygame.image.load(
        str(transition_directory / "old_man_silhouette.png")
    ).convert_alpha()
    old_man_bounds = old_man.get_bounding_rect(min_alpha=8)
    sprites["awakening_old_man"] = old_man.subsurface(
        old_man_bounds
    ).copy()

    for class_name in ("warrior", "rogue", "mage"):
        sprites[f"{class_name}_portrait"] = pygame.image.load(
            str(
                ui_directory
                / f"{class_name}_portrait.png"
            )
        ).convert_alpha()

    ability_directory = ui_directory / "abilities"
    for asset_name, file_name in (
        ("warrior_power_cleave_icon", "power_cleave.png"),
        ("rogue_invisibility_icon", "invisibility.png"),
        ("mage_arcane_burst_icon", "blast.png"),
    ):
        sprites[asset_name] = pygame.image.load(
            str(ability_directory / file_name)
        ).convert_alpha()
    rune_directory = ability_directory / "runes"
    for rune in RUNE_DEFINITIONS:
        sprites[f"{rune.id}_icon"] = pygame.image.load(
            str(rune_directory / rune.icon_filename)
        ).convert_alpha()
        rune_original = pygame.image.load(
            str(rune_directory / rune.original_filename)
        ).convert_alpha()
        sprites[f"{rune.id}_original"] = (
            pygame.transform.smoothscale(
                rune_original,
                (151, 151),
            )
        )
    sprites["upgrade_window"] = pygame.image.load(
        str(ui_directory / "upgrade" / "upgrade_window.png")
    ).convert_alpha()

    act_two_hud_directory = ui_directory / "ui_v.0.2"
    sprites.update(
        {
            "act_two_trade_background": pygame.image.load(
                str(act_two_hud_directory / "trade_background.png")
            ).convert_alpha(),
            "act_two_hud_frame": _load_scaled_image(
                act_two_hud_directory / "hud_frame_act2(32).png",
                (315, 89),
            ),
            "act_two_hud_hp": _load_scaled_image(
                act_two_hud_directory / "hp_bar_act2.png",
                (258, 17),
            ),
            "act_two_hud_xp": _load_scaled_image(
                act_two_hud_directory / "xp_bar_act2.png",
                (246, 16),
            ),
            "act_two_bottom_bar": _load_scaled_image(
                act_two_hud_directory
                / "skill+belt_bar_act2_v2.png",
                (367, 122),
            ),
            "act_two_stats_panel": _load_scaled_image(
                act_two_hud_directory / "character_list.png",
                (236, 354),
            ),
            "act_two_side_buttons": _load_scaled_image(
                act_two_hud_directory / "sidebar_act2(32).png",
                (67, 175),
            ),
            "act_two_level_up_indicator": _load_scaled_image(
                act_two_hud_directory / "lvl_up.png",
                (68, 65),
            ),
            "act_two_confirm_button": _load_scaled_image(
                act_two_hud_directory / "confirm_button.png",
                (121, 40),
            ),
            "act_two_rune_confirm_button": _load_scaled_image(
                act_two_hud_directory / "confirm_button.png",
                (132, 44),
            ),
            "act_two_gold_counter": _load_scaled_image(
                act_two_hud_directory / "gold.png",
                (76, 76),
            ),
            "act_two_abilities_panel": _load_scaled_image(
                act_two_hud_directory / "abilities.png",
                (264, 198),
            ),
            "act_two_rune_window": _load_scaled_image(
                act_two_hud_directory / "runes.png",
                (756, 426),
            ),
        }
    )
    chat_log_backing = pygame.Surface((276, 82), pygame.SRCALPHA)
    pygame.draw.rect(
        chat_log_backing,
        (42, 39, 39, 191),
        pygame.Rect(4, 4, 268, 74),
        border_radius=11,
    )
    sprites["act_two_chat_log_backing"] = (
        pygame.transform.gaussian_blur(chat_log_backing, 2)
    )
    ability_text_backing = pygame.Surface((146, 66), pygame.SRCALPHA)
    pygame.draw.rect(
        ability_text_backing,
        (42, 39, 39, 191),
        pygame.Rect(4, 4, 138, 58),
        border_radius=11,
    )
    sprites["act_two_ability_text_backing"] = (
        pygame.transform.gaussian_blur(ability_text_backing, 2)
    )
    ability_name_backing = pygame.Surface((86, 23), pygame.SRCALPHA)
    pygame.draw.rect(
        ability_name_backing,
        (10, 8, 9, 220),
        pygame.Rect(4, 4, 78, 15),
        border_radius=4,
    )
    sprites["act_two_ability_name_backing"] = (
        pygame.transform.gaussian_blur(ability_name_backing, 1)
    )

    return sprites


def _scale_to_width(source, target_width):
    source_width, source_height = source.get_size()
    target_height = round(
        source_height * target_width / source_width
    )
    return pygame.transform.smoothscale(
        source,
        (target_width, target_height),
    )


def load_act_three_transition_assets():
    ui_directory = ASSET_ROOT / "ui" / "act_3"
    player_directory = ASSET_ROOT / "act_3" / "player"
    berserker_path = (
        player_directory
        / "berserker"
        / "idle"
        / "idle_00_original.png"
    )
    paladin_path = (
        player_directory
        / "paladin"
        / "idle"
        / "idle_00_original.png"
    )
    assassin_path = (
        player_directory
        / "assassin"
        / "idle"
        / "idle_00_original.png"
    )
    archer_path = (
        player_directory
        / "archer"
        / "idle"
        / "idle_00_original.png"
    )
    warlock_path = (
        player_directory
        / "warlock"
        / "idle"
        / "idle_00_original.png"
    )
    summoner_path = (
        player_directory
        / "summoner"
        / "idle"
        / "idle_00_original.png"
    )
    background_source = pygame.image.load(
        str(ui_directory / "awakening_background_v2.png")
    ).convert()
    background_width = round(GAME_WIDTH * 1.12)
    hands_width = GAME_WIDTH

    assets = {
        "background": _scale_to_width(
            background_source,
            background_width,
        ),
        "berserker_portrait": pygame.transform.smoothscale(
            pygame.image.load(
                str(berserker_path)
            ).convert_alpha(),
            (230, 230),
        ),
        "paladin_portrait": pygame.transform.smoothscale(
            pygame.image.load(
                str(paladin_path)
            ).convert_alpha(),
            (230, 230),
        ),
        "assassin_portrait": pygame.transform.smoothscale(
            pygame.image.load(
                str(assassin_path)
            ).convert_alpha(),
            (230, 230),
        ),
        "archer_portrait": pygame.transform.smoothscale(
            pygame.image.load(
                str(archer_path)
            ).convert_alpha(),
            (230, 230),
        ),
        "warlock_portrait": pygame.transform.smoothscale(
            pygame.image.load(
                str(warlock_path)
            ).convert_alpha(),
            (230, 230),
        ),
        "summoner_portrait": pygame.transform.smoothscale(
            pygame.image.load(
                str(summoner_path)
            ).convert_alpha(),
            (230, 230),
        ),
    }

    for player_class in ("warrior", "rogue", "mage"):
        for pose in ("open", "clenched"):
            hands = _scale_to_width(
                pygame.image.load(
                    str(
                        ui_directory
                        / f"{player_class}_hands_{pose}.png"
                    )
                ).convert_alpha(),
                hands_width,
            )
            hands.fill(
                (185, 190, 200, 255),
                special_flags=pygame.BLEND_RGBA_MULT,
            )
            assets[f"{player_class}_hands_{pose}"] = hands

    return assets


def _load_scaled_image(path, size, use_alpha=True):
    source = pygame.image.load(str(path))
    source = (
        source.convert_alpha()
        if use_alpha
        else source.convert()
    )
    return pygame.transform.smoothscale(source, size)


def _load_pixel_scaled_image(path, size):
    source = pygame.image.load(str(path)).convert_alpha()
    return pygame.transform.scale(source, size)


def _load_cropped_ui_image(path, size):
    source = pygame.image.load(str(path)).convert_alpha()
    content_rectangle = source.get_bounding_rect(min_alpha=1)
    cropped_source = source.subsurface(
        content_rectangle
    ).copy()
    return pygame.transform.smoothscale(cropped_source, size)


def _load_pixel_cropped_ui_image(path, size):
    source = pygame.image.load(str(path)).convert_alpha()
    content_rectangle = source.get_bounding_rect(min_alpha=1)
    cropped_source = source.subsurface(content_rectangle).copy()
    return pygame.transform.scale(cropped_source, size)


def load_act_three_gameplay_assets():
    act_directory = ASSET_ROOT / "act_3"
    act_three_config = next(
        config for config in FLOOR_CONFIGS if config["act"] == 3
    )
    project_root = ASSET_ROOT.parent.parent
    map_path = project_root / act_three_config["map_path"]
    environment_directory = map_path.parent
    ui_directory = ASSET_ROOT / "ui" / "act_3"
    hud_directory = ui_directory / "ui_v.0.2"
    tile_size = ACT_THREE_TILE_SIZE
    assets = {
        "character_hud_frame": _load_scaled_image(
            hud_directory / "hud_frame.png",
            (423, 160),
        ),
        "character_hud_hp": _load_scaled_image(
            hud_directory / "character_hud_hp.png",
            (261, 19),
        ),
        "character_hud_xp": _load_scaled_image(
            hud_directory / "character_hud_xp.png",
            (256, 19),
        ),
        "character_portrait_placeholder": _load_scaled_image(
            hud_directory / "character_portrait_placeholder.png",
            (96, 87),
        ),
        "floor_base": _load_scaled_image(
            environment_directory / "floor" / "floor_base.png",
            (tile_size, tile_size),
            use_alpha=False,
        ),
        "floor_cracked": _load_scaled_image(
            environment_directory
            / "floor"
            / "floor_cracked.png",
            (tile_size, tile_size),
            use_alpha=False,
        ),
        "floor_damp": _load_scaled_image(
            environment_directory / "floor" / "floor_damp.png",
            (tile_size, tile_size),
            use_alpha=False,
        ),
        "wall_top": _load_scaled_image(
            environment_directory
            / "walls"
            / "original"
            / "wall_top_original.png",
            (tile_size, tile_size),
            use_alpha=False,
        ),
        "wall_top_variant": _load_scaled_image(
            environment_directory
            / "walls"
            / "wall_top_variant_01.png",
            (tile_size, tile_size),
            use_alpha=False,
        ),
        "wall_top_turn_left": _load_scaled_image(
            environment_directory
            / "walls"
            / "wall_top_turn_left.png",
            (tile_size, tile_size),
        ),
        "wall_top_turn_right": _load_scaled_image(
            environment_directory
            / "walls"
            / "wall_top_turn_right.png",
            (tile_size, tile_size),
        ),
        "wall_bottom": _load_scaled_image(
            environment_directory
            / "walls"
            / "wall_bottom.png",
            (tile_size, tile_size),
        ),
        "wall_left": _load_scaled_image(
            environment_directory / "walls" / "wall_left.png",
            (tile_size, tile_size),
        ),
        "wall_right": _load_scaled_image(
            environment_directory / "walls" / "wall_right.png",
            (tile_size, tile_size),
        ),
        "wall_corner_bottom_left": _load_scaled_image(
            environment_directory
            / "walls"
            / "wall_corner_bottom_left.png",
            (tile_size, tile_size),
        ),
        "wall_corner_bottom_right": _load_scaled_image(
            environment_directory
            / "walls"
            / "wall_corner_bottom_right.png",
            (tile_size, tile_size),
        ),
        "wall_corner_top_left": _load_scaled_image(
            environment_directory
            / "walls"
            / "wall_corner_top_left.png",
            (tile_size, tile_size),
        ),
        "wall_corner_top_right": _load_scaled_image(
            environment_directory
            / "walls"
            / "wall_corner_top_right.png",
            (tile_size, tile_size),
        ),
        "chest_closed": _load_scaled_image(
            environment_directory
            / "chests"
            / "chest_closed.png",
            (tile_size, tile_size),
        ),
        "chest_open": _load_scaled_image(
            environment_directory
            / "chests"
            / "chest_open.png",
            (tile_size, tile_size),
        ),
        "coin": _load_scaled_image(
            environment_directory / "items" / "coin.png",
            (tile_size, tile_size),
        ),
        "key": _load_scaled_image(
            environment_directory / "items" / "key.png",
            (tile_size, tile_size),
        ),
        "potion": _load_scaled_image(
            environment_directory
            / "items"
            / "potion_health.png",
            (tile_size, tile_size),
        ),
        "stairs_locked": _load_scaled_image(
            environment_directory
            / "stairs"
            / "stairs_locked_original.png",
            (tile_size, tile_size),
        ),
        "stairs_open": _load_scaled_image(
            environment_directory
            / "stairs"
            / "stairs_open_original.png",
            (tile_size, tile_size),
        ),
        "torch_base": _load_scaled_image(
            environment_directory
            / "torches"
            / "torch_base_v2.png",
            (tile_size, tile_size),
        ),
        "upgrade_altar_0": _load_pixel_scaled_image(
            environment_directory
            / "upgrade_altar"
            / "upgrade_altar_00.png",
            (tile_size * 2, tile_size * 2),
        ),
        "upgrade_altar_1": _load_pixel_scaled_image(
            environment_directory
            / "upgrade_altar"
            / "upgrade_altar_01.png",
            (tile_size * 2, tile_size * 2),
        ),
        "upgrade_altar_2": _load_pixel_scaled_image(
            environment_directory
            / "upgrade_altar"
            / "upgrade_altar_02.png",
            (tile_size * 2, tile_size * 2),
        ),
        "altar_menu_panel": _load_scaled_image(
            ui_directory / "altar_menu" / "panel.png",
            (1000, 590),
        ),
        "altar_menu_card": _load_scaled_image(
            ui_directory / "altar_menu" / "attribute_card.png",
            (410, 205),
        ),
        "altar_menu_tab": _load_scaled_image(
            ui_directory / "altar_menu" / "tab.png",
            (280, 58),
        ),
        "altar_menu_button": _load_scaled_image(
            ui_directory / "altar_menu" / "upgrade_button.png",
            (330, 42),
        ),
        "altar_menu_xp_bar": _load_scaled_image(
            ui_directory / "altar_menu" / "xp_bar_frame.png",
            (320, 34),
        ),
        "altar_menu_vitality": _load_scaled_image(
            ui_directory / "altar_menu" / "vitality.png",
            (72, 72),
        ),
        "altar_menu_power": _load_scaled_image(
            ui_directory / "altar_menu" / "power.png",
            (72, 72),
        ),
        "altar_menu_precision": _load_scaled_image(
            ui_directory / "altar_menu" / "precision.png",
            (72, 72),
        ),
        "altar_menu_evasion": _load_scaled_image(
            ui_directory / "altar_menu" / "evasion.png",
            (72, 72),
        ),
        "altar_menu_attribute_point": _load_scaled_image(
            ui_directory / "altar_menu" / "attribute_point.png",
            (24, 24),
        ),
        "altar_menu_skill_point": _load_scaled_image(
            ui_directory / "altar_menu" / "skill_point.png",
            (24, 24),
        ),
        "altar_menu_rank_filled": _load_scaled_image(
            ui_directory / "altar_menu" / "rank_filled.png",
            (14, 14),
        ),
        "altar_menu_rank_empty": _load_scaled_image(
            ui_directory / "altar_menu" / "rank_empty.png",
            (14, 14),
        ),
        "assassin_invisibility": _load_scaled_image(
            act_directory
            / "player"
            / "assassin"
            / "assassin_invisibility"
            / "assassin_invisibility.png",
            (46, 52),
        ),
        "assassin_teleport": _load_scaled_image(
            act_directory
            / "player"
            / "assassin"
            / "assassin_teleport"
            / "assassin_teleport.png",
            (46, 52),
        ),
        "assassin_killing_spree": _load_scaled_image(
            act_directory
            / "player"
            / "assassin"
            / "assassin_killing_spree"
            / "assassin_killing_spree.png",
            (46, 52),
        ),
        "archer_empowered_shot": _load_scaled_image(
            act_directory
            / "player"
            / "archer"
            / "archer_empowered_shot"
            / "archer_empowered_shot.png",
            (46, 52),
        ),
        "archer_leap": _load_scaled_image(
            act_directory
            / "player"
            / "archer"
            / "archer_leap"
            / "archer_leap.png",
            (46, 52),
        ),
        "archer_barrage_zone": _load_scaled_image(
            act_directory
            / "player"
            / "archer"
            / "archer_barrage_zone"
            / "archer_barrage_zone.png",
            (46, 52),
        ),
        "berserker_rage": _load_scaled_image(
            act_directory
            / "player"
            / "berserker"
            / "berserker_rage"
            / "berserker_rage.png",
            (46, 52),
        ),
        "berserker_crushing_leap": _load_scaled_image(
            act_directory
            / "player"
            / "berserker"
            / "berserker_crushing_leap"
            / "berserker_crushing_leap.png",
            (46, 52),
        ),
        "berserker_last_rage": _load_scaled_image(
            act_directory
            / "player"
            / "berserker"
            / "berserker_last_rage"
            / "berserker_last_rage.png",
            (46, 52),
        ),
        "paladin_holy_hand": _load_scaled_image(
            act_directory
            / "player"
            / "paladin"
            / "paladin_holy_hand"
            / "paladin_holy_hand.png",
            (46, 52),
        ),
        "paladin_shield_charge": _load_scaled_image(
            act_directory
            / "player"
            / "paladin"
            / "paladin_shield_charge"
            / "paladin_shield_charge.png",
            (46, 52),
        ),
        "paladin_holy_shield": _load_scaled_image(
            act_directory
            / "player"
            / "paladin"
            / "paladin_holy_shield"
            / "paladin_holy_shield.png",
            (46, 52),
        ),
        "warlock_curse": _load_scaled_image(
            act_directory
            / "player"
            / "warlock"
            / "warlock_curse"
            / "warlock_curse.png",
            (46, 52),
        ),
        "warlock_soul_exchange": _load_scaled_image(
            act_directory
            / "player"
            / "warlock"
            / "warlock_soul_exchange"
            / "warlock_soul_exchange.png",
            (46, 52),
        ),
        "warlock_demon_form": _load_scaled_image(
            act_directory
            / "player"
            / "warlock"
            / "warlock_demon_form"
            / "warlock_demon_form.png",
            (46, 52),
        ),
        "warlock_demon_edge_left": _load_scaled_image(
            act_directory
            / "player"
            / "warlock"
            / "warlock_demon_form"
            / "demon_form_edge_left_original.png",
            (273, 512),
        ),
        "warlock_demon_edge_right": _load_scaled_image(
            act_directory
            / "player"
            / "warlock"
            / "warlock_demon_form"
            / "demon_form_edge_right_original.png",
            (273, 512),
        ),
        "summoner_familiar": _load_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "summoner_familiar"
            / "summoner_familiar_original.png",
            (46, 52),
        ),
        "summoner_bond": _load_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "summoner_bond"
            / "summoner_bond_original.png",
            (46, 52),
        ),
        "summoner_true_form": _load_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "summoner_true_form"
            / "summoner_true_form_original.png",
            (46, 52),
        ),
        "summoner_familiar_idle_0": _load_pixel_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "summoner_familiar"
            / "idle_00.png",
            (tile_size, tile_size),
        ),
        "summoner_familiar_idle_1": _load_pixel_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "summoner_familiar"
            / "idle_01.png",
            (tile_size, tile_size),
        ),
        "summoner_familiar_idle_2": _load_pixel_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "summoner_familiar"
            / "idle_02.png",
            (tile_size, tile_size),
        ),
        "summoner_familiar_attack": _load_pixel_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "summoner_familiar"
            / "attack"
            / "attack_00.png",
            (tile_size, tile_size),
        ),
        "summoner_true_form_idle_0": _load_pixel_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "summoner_true_form"
            / "idle_00.png",
            (tile_size, tile_size),
        ),
        "summoner_true_form_idle_1": _load_pixel_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "summoner_true_form"
            / "idle_01.png",
            (tile_size, tile_size),
        ),
        "summoner_true_form_idle_2": _load_pixel_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "summoner_true_form"
            / "idle_02.png",
            (tile_size, tile_size),
        ),
        "summoner_true_form_attack": _load_pixel_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "summoner_true_form"
            / "attack"
            / "attack_00.png",
            (tile_size, tile_size),
        ),
        "sidebar_potion": _load_scaled_image(
            environment_directory / "items" / "potion_health.png",
            (34, 34),
        ),
        "sidebar_coin": _load_scaled_image(
            environment_directory / "items" / "coin.png",
            (34, 34),
        ),
        "sidebar_key": _load_scaled_image(
            environment_directory / "items" / "key.png",
            (34, 34),
        ),
    }
    map_root = ET.parse(map_path).getroot()
    tileset_reference = map_root.find("tileset")
    if tileset_reference is None or not tileset_reference.get("source"):
        raise ValueError(f"TMX map has no external tileset: {map_path}")
    tileset_path = map_path.parent / tileset_reference.get("source")
    tmx_tiles = {}
    if tileset_path.exists():
        tileset_root = ET.parse(tileset_path).getroot()
        for tile in tileset_root.findall("tile"):
            image = tile.find("image")
            if image is None or not image.get("source"):
                continue
            image_path = tileset_path.parent / image.get("source")
            if not image_path.exists():
                raise FileNotFoundError(
                    f"Missing TMX tile image: {image_path}"
                )
            tmx_tiles[int(tile.get("id", 0)) + 1] = _load_scaled_image(
                image_path,
                (tile_size, tile_size),
            )
    assets["tmx_tiles"] = tmx_tiles

    for frame_index in range(3):
        assets[f"torch_flame_{frame_index}"] = (
            _load_scaled_image(
                environment_directory
                / "torches"
                / f"torch_flame_0{frame_index}_v2.png",
                (tile_size, tile_size),
            )
        )

    idle_filenames = (
        "idle_00.png",
        "idle_01.png",
        "idle_02.png",
    )

    for subclass in (
        "berserker",
        "paladin",
        "assassin",
        "archer",
        "warlock",
        "summoner",
    ):
        idle_directory = (
            act_directory / "player" / subclass / "idle"
        )

        for frame_index, filename in enumerate(
            idle_filenames
        ):
            assets[
                f"player_{subclass}_idle_{frame_index}"
            ] = (
                _load_scaled_image(
                    idle_directory / filename,
                    (tile_size, tile_size),
                )
            )

    summoner_no_familiar_idle_directory = (
        act_directory
        / "player"
        / "summoner"
        / "idle_no_familiar"
    )
    for frame_index in range(3):
        assets[
            f"player_summoner_no_familiar_idle_{frame_index}"
        ] = _load_pixel_scaled_image(
            summoner_no_familiar_idle_directory
            / f"idle_{frame_index:02d}.png",
            (tile_size, tile_size),
        )

    demon_idle_directory = (
        act_directory
        / "player"
        / "warlock"
        / "warlock_demon_form"
    )
    for frame_index in range(3):
        assets[f"player_warlock_demon_idle_{frame_index}"] = (
            _load_pixel_scaled_image(
                demon_idle_directory
                / f"idle_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )
    for frame_index in range(2):
        assets[f"player_warlock_demon_walk_{frame_index}"] = (
            _load_pixel_scaled_image(
                demon_idle_directory
                / f"walk_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )
    assets["player_warlock_demon_attack"] = (
        _load_pixel_scaled_image(
            demon_idle_directory / "attack_00.png",
            (tile_size, tile_size),
        )
    )

    walk_directory = (
        act_directory / "player" / "assassin" / "walk"
    )
    for frame_index in range(2):
        assets[f"player_assassin_walk_{frame_index}"] = (
            _load_pixel_scaled_image(
                walk_directory / f"walk_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )

    archer_walk_directory = (
        act_directory / "player" / "archer" / "walk"
    )
    for frame_index in range(2):
        assets[f"player_archer_walk_{frame_index}"] = (
            _load_pixel_scaled_image(
                archer_walk_directory
                / f"walk_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )

    berserker_walk_directory = (
        act_directory / "player" / "berserker" / "walk"
    )
    for frame_index in range(2):
        assets[f"player_berserker_walk_{frame_index}"] = (
            _load_pixel_scaled_image(
                berserker_walk_directory
                / f"walk_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )

    assets["player_berserker_hurt"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "berserker"
            / "hurt"
            / "hurt_00.png",
            (tile_size, tile_size),
        )
    )

    berserker_death_directory = (
        act_directory / "player" / "berserker" / "death"
    )
    for frame_index in range(2):
        assets[f"player_berserker_death_{frame_index}"] = (
            _load_pixel_scaled_image(
                berserker_death_directory
                / f"death_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )

    assets["player_paladin_hurt"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "paladin"
            / "hurt"
            / "hurt_00.png",
            (tile_size, tile_size),
        )
    )

    paladin_death_directory = (
        act_directory / "player" / "paladin" / "death"
    )
    for frame_index in range(2):
        assets[f"player_paladin_death_{frame_index}"] = (
            _load_pixel_scaled_image(
                paladin_death_directory
                / f"death_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )

    old_man_appearance_directory = (
        act_directory / "npcs" / "old_man" / "appearance"
    )
    for frame_index in range(6):
        assets[f"old_man_appearance_{frame_index}"] = (
            _load_pixel_scaled_image(
                old_man_appearance_directory
                / f"appearance_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )

    assets["player_assassin_hurt"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "assassin"
            / "hurt"
            / "hurt_00.png",
            (tile_size, tile_size),
        )
    )

    assassin_death_directory = (
        act_directory / "player" / "assassin" / "death"
    )
    for frame_index in range(2):
        assets[f"player_assassin_death_{frame_index}"] = (
            _load_pixel_scaled_image(
                assassin_death_directory
                / f"death_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )

    assets["player_archer_hurt"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "archer"
            / "hurt"
            / "hurt_00.png",
            (tile_size, tile_size),
        )
    )

    archer_death_directory = (
        act_directory / "player" / "archer" / "death"
    )
    for frame_index in range(2):
        assets[f"player_archer_death_{frame_index}"] = (
            _load_pixel_scaled_image(
                archer_death_directory
                / f"death_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )

    assets["player_warlock_hurt"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "warlock"
            / "hurt"
            / "hurt_00.png",
            (tile_size, tile_size),
        )
    )

    warlock_death_directory = (
        act_directory / "player" / "warlock" / "death"
    )
    for frame_index in range(2):
        assets[f"player_warlock_death_{frame_index}"] = (
            _load_pixel_scaled_image(
                warlock_death_directory
                / f"death_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )

    assets["player_warlock_demon_hurt"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "warlock"
            / "warlock_demon_form"
            / "hurt"
            / "hurt_00.png",
            (tile_size, tile_size),
        )
    )

    assets["player_summoner_hurt"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "hurt"
            / "hurt_00.png",
            (tile_size, tile_size),
        )
    )

    assets["player_summoner_no_familiar_hurt"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "hurt_no_familiar"
            / "hurt_00.png",
            (tile_size, tile_size),
        )
    )

    summoner_death_directory = (
        act_directory / "player" / "summoner" / "death"
    )
    for frame_index in range(2):
        assets[f"player_summoner_death_{frame_index}"] = (
            _load_pixel_scaled_image(
                summoner_death_directory
                / f"death_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )

    paladin_walk_directory = (
        act_directory / "player" / "paladin" / "walk"
    )
    for frame_index in range(2):
        assets[f"player_paladin_walk_{frame_index}"] = (
            _load_pixel_scaled_image(
                paladin_walk_directory
                / f"walk_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )

    warlock_walk_directory = (
        act_directory / "player" / "warlock" / "walk"
    )
    for frame_index in range(2):
        assets[f"player_warlock_walk_{frame_index}"] = (
            _load_pixel_scaled_image(
                warlock_walk_directory
                / f"walk_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )

    summoner_walk_directory = (
        act_directory / "player" / "summoner" / "walk"
    )
    for frame_index in range(2):
        assets[f"player_summoner_walk_{frame_index}"] = (
            _load_pixel_scaled_image(
                summoner_walk_directory
                / f"walk_{frame_index:02d}.png",
                (tile_size, tile_size),
            )
        )

    summoner_no_familiar_walk_directory = (
        act_directory
        / "player"
        / "summoner"
        / "walk_no_familiar"
    )
    for frame_index in range(2):
        assets[
            f"player_summoner_no_familiar_walk_{frame_index}"
        ] = _load_pixel_scaled_image(
            summoner_no_familiar_walk_directory
            / f"walk_{frame_index:02d}.png",
            (tile_size, tile_size),
        )

    assets["player_assassin_attack"] = _load_pixel_scaled_image(
        act_directory
        / "player"
        / "assassin"
        / "attack"
        / "attack_00.png",
        (tile_size, tile_size),
    )
    ultimate_directory = (
        act_directory / "player" / "assassin" / "ultimate"
    )
    for variant_index, filename in enumerate(
        (
            "chain_slash_01.png",
            "chain_slash_02.png",
            "chain_slash_03.png",
        )
    ):
        slash_path = ultimate_directory / filename
        assets[f"assassin_ultimate_slash_{variant_index}"] = (
            _load_pixel_scaled_image(slash_path, (96, 96))
        )
    assets["player_archer_attack"] = _load_pixel_scaled_image(
        act_directory
        / "player"
        / "archer"
        / "attack"
        / "attack_00.png",
        (tile_size, tile_size),
    )
    assets["archer_empowered_shot_arrow"] = _load_scaled_image(
        act_directory
        / "player"
        / "archer"
        / "empowered_shot"
        / "empowered_shot_arrow.png",
        (64, 64),
    )
    assets["player_archer_leap"] = _load_pixel_scaled_image(
        act_directory
        / "player"
        / "archer"
        / "leap"
        / "leap_00.png",
        (tile_size, tile_size),
    )
    assets["archer_barrage_zone_cell"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "archer"
            / "barrage_zone"
            / "barrage_zone_cell.png",
            (tile_size, tile_size),
        )
    )
    assets["player_berserker_attack"] = _load_pixel_scaled_image(
        act_directory
        / "player"
        / "berserker"
        / "attack"
        / "attack_00.png",
        (tile_size, tile_size),
    )
    assets["player_berserker_crushing_leap"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "berserker"
            / "crushing_leap"
            / "leap_00_original.png",
            (tile_size, tile_size),
        )
    )
    assets["player_berserker_crushing_leap_impact"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "berserker"
            / "crushing_leap"
            / "leap_impact_00_original.png",
            (tile_size, tile_size),
        )
    )
    assets["berserker_crushing_leap_area"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "berserker"
            / "crushing_leap"
            / "crushing_leap_area_original.png",
            (tile_size, tile_size),
        )
    )
    assets["player_paladin_attack"] = _load_pixel_scaled_image(
        act_directory
        / "player"
        / "paladin"
        / "attack"
        / "attack_00.png",
        (tile_size, tile_size),
    )
    assets["player_paladin_shield_charge"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "paladin"
            / "shield_charge"
            / "shield_charge_00.png",
            (tile_size, tile_size),
        )
    )
    assets["player_warlock_attack"] = _load_pixel_scaled_image(
        act_directory
        / "player"
        / "warlock"
        / "attack"
        / "attack_00.png",
        (tile_size, tile_size),
    )
    assets["player_summoner_attack"] = _load_pixel_scaled_image(
        act_directory
        / "player"
        / "summoner"
        / "attack"
        / "attack_00.png",
        (tile_size, tile_size),
    )
    assets["player_summoner_no_familiar_attack"] = (
        _load_pixel_scaled_image(
            act_directory
            / "player"
            / "summoner"
            / "attack_no_familiar"
            / "attack_00.png",
            (tile_size, tile_size),
        )
    )

    for enemy_type in (
        "archer",
        "brute",
        "sentinel",
        "priest",
    ):
        enemy_idle_directory = (
            act_directory
            / "enemies"
            / enemy_type
            / "idle"
        )

        for frame_index in range(3):
            assets[
                f"enemy_{enemy_type}_idle_{frame_index}"
            ] = _load_pixel_scaled_image(
                enemy_idle_directory
                / f"idle_{frame_index:02d}.png",
                (tile_size, tile_size),
            )

    for enemy_type in (
        "archer",
        "brute",
        "priest",
        "sentinel",
    ):
        enemy_death_directory = (
            act_directory
            / "enemies"
            / enemy_type
            / "death"
        )
        for frame_index in range(2):
            assets[
                f"enemy_{enemy_type}_death_{frame_index}"
            ] = _load_pixel_scaled_image(
                enemy_death_directory
                / f"death_{frame_index:02d}.png",
                (tile_size, tile_size),
            )

    for enemy_type in (
        "archer",
        "brute",
        "priest",
        "sentinel",
    ):
        enemy_walk_directory = (
            act_directory
            / "enemies"
            / enemy_type
            / "walk"
        )
        for frame_index in range(2):
            assets[
                f"enemy_{enemy_type}_walk_{frame_index}"
            ] = _load_pixel_scaled_image(
                enemy_walk_directory
                / f"walk_{frame_index:02d}.png",
                (tile_size, tile_size),
            )

    for enemy_type in (
        "archer",
        "brute",
        "sentinel",
    ):
        assets[
            f"enemy_{enemy_type}_attack"
        ] = _load_pixel_scaled_image(
            act_directory
            / "enemies"
            / enemy_type
            / "attack"
            / "attack_00.png",
            (tile_size, tile_size),
        )

    assets["sentinel_guard"] = (
        _load_pixel_scaled_image(
            act_directory
            / "enemies"
            / "sentinel"
            / "guard.png",
            (tile_size, tile_size),
        )
    )
    assets["priest_heal_cast"] = (
        _load_pixel_scaled_image(
            act_directory
            / "enemies"
            / "priest"
            / "heal_cast.png",
            (tile_size, tile_size),
        )
    )

    return assets
