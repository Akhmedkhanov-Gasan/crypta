import pygame

from presentation.layout import (
    AWAKENING_FADE_END_MS,
    AWAKENING_HOLD_END_MS,
    AWAKENING_OPEN_END_MS,
    AWAKENING_OPEN_START_MS,
    ASSET_ROOT,
    CLASS_SELECTION_READY_MS,
    FONT_ROOT,
    MAP_HEIGHT,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    MAP_WIDTH,
    SIDEBAR_HEIGHT,
    SIDEBAR_WIDTH,
    SIDEBAR_X,
    SIDEBAR_Y,
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
