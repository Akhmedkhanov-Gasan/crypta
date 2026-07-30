import pygame

from presentation.layout import (
    ASSET_ROOT,
    FONT_ROOT,
)
from settings import GAME_HEIGHT, GAME_WIDTH, TILE_SIZE


def load_act_one_fonts():
    regular_path = FONT_ROOT / "PixelOperator.ttf"
    bold_path = FONT_ROOT / "PixelOperator-Bold.ttf"

    return {
        "title": pygame.font.Font(str(bold_path), 44),
        "heading": pygame.font.Font(str(bold_path), 28),
        "status": pygame.font.Font(str(bold_path), 24),
        "text": pygame.font.Font(str(regular_path), 20),
        "controls": pygame.font.Font(str(bold_path), 19),
    }


def load_act_two_fonts():
    regular_path = FONT_ROOT / "Almendra-Regular.ttf"
    bold_path = FONT_ROOT / "Almendra-Bold.ttf"

    return {
        "title": pygame.font.Font(str(bold_path), 42),
        "heading": pygame.font.Font(str(bold_path), 25),
        "status": pygame.font.Font(str(bold_path), 24),
        "text": pygame.font.Font(str(regular_path), 18),
        "controls": pygame.font.Font(str(bold_path), 18),
    }


def load_act_three_fonts():
    display_path = FONT_ROOT / "Sandey Molse DEMO.ttf"
    interface_path = FONT_ROOT / "PixelOperator.ttf"
    interface_bold_path = FONT_ROOT / "PixelOperator-Bold.ttf"

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
        "sidebar_numbers": pygame.font.Font(
            str(interface_bold_path),
            18,
        ),
    }


def load_act_two_sprites():
    asset_directory = ASSET_ROOT / "act_2"
    ui_directory = ASSET_ROOT / "ui" / "act_2"
    sprite_names = (
        "player_warrior",
        "player_rogue",
        "player_mage",
        "goblin",
        "brute",
        "archer",
        "potion",
        "key",
        "coin",
        "chest_closed",
        "chest_open",
        "stairs_locked",
        "stairs_open",
        "floor",
        "wall",
        "sentinel_idle",
        "sentinel_guard",
        "priest_idle",
        "priest_cast",
        "oracle_idle",
        "oracle_awake",
        "oracle_projectile",
        "oracle_projectile_homing",
        "pillar",
        "charged_pillar",
    )

    sprites = {
        name: pygame.transform.scale(
            pygame.image.load(
                str(asset_directory / f"{name}.png")
            ).convert_alpha(),
            (TILE_SIZE, TILE_SIZE),
        )
        for name in sprite_names
    }
    for oracle_sprite_name in ("oracle_idle", "oracle_awake"):
        sprites[oracle_sprite_name] = pygame.transform.scale(
            pygame.image.load(
                str(
                    asset_directory
                    / f"{oracle_sprite_name}.png"
                )
            ).convert_alpha(),
            (TILE_SIZE * 3, TILE_SIZE * 3),
        )
    sprites["floor"].fill(
        (150, 145, 160),
        special_flags=pygame.BLEND_RGB_MULT,
    )
    sprites["wall"].fill(
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

    for class_name in ("warrior", "rogue", "mage"):
        sprites[f"{class_name}_portrait"] = pygame.image.load(
            str(
                ui_directory
                / f"{class_name}_portrait.png"
            )
        ).convert_alpha()

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


def load_act_three_gameplay_assets():
    act_directory = ASSET_ROOT / "act_3"
    environment_directory = act_directory / "environment"
    act_two_directory = ASSET_ROOT / "act_2"
    ui_directory = ASSET_ROOT / "ui" / "act_3"
    tile_size = 64
    assets = {
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
            / "wall_top_original.png",
            (tile_size, tile_size),
            use_alpha=False,
        ),
        "wall_top_variant": _load_scaled_image(
            environment_directory
            / "walls"
            / "wall_top_variant_01_original.png",
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
        "gameplay_frame": _load_cropped_ui_image(
            ui_directory / "gameplay_frame_source.png",
            (928, 656),
        ),
        "sidebar_panel": _load_cropped_ui_image(
            ui_directory / "sidebar_panel_source.png",
            (304, 640),
        ),
        "assassin_hp_bar": _load_scaled_image(
            ui_directory / "assassin_hp_bar.png",
            (258, 42),
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

    fallback_enemy_sprites = {
        "goblin": "goblin",
        "brute": "brute",
        "sentinel": "sentinel_idle",
    }

    for enemy_type, sprite_name in fallback_enemy_sprites.items():
        assets[f"enemy_{enemy_type}"] = (
            _load_pixel_scaled_image(
                act_two_directory / f"{sprite_name}.png",
                (tile_size, tile_size),
            )
        )

    return assets
