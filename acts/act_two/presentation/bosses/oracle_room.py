from functools import lru_cache

import pygame

from acts.act_two.presentation.bosses.oracle_intro import (
    oracle_gate_sprite,
)

from presentation.layout import (
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    PROJECT_ROOT,
)
from settings import TILE_SIZE


@lru_cache(maxsize=1)
def _load_oracle_room_sprites():
    root = (
        PROJECT_ROOT
        / "assets"
        / "sprites"
        / "act_2"
        / "bosses"
        / "oracle"
    )
    sprites = {}

    for name in (
        "gate_closed",
        "gate_half_open",
        "gate_open",
    ):
        source = pygame.image.load(
            str(root / "gate" / f"{name}.png")
        ).convert_alpha()
        sprites[name] = pygame.transform.scale(
            source,
            (TILE_SIZE * 4, TILE_SIZE * 3),
        )

    for name in (
        "brazier_base",
        "brazier_fire_00",
        "brazier_fire_01",
        "brazier_fire_02",
    ):
        source = pygame.image.load(
            str(root / "brazier" / f"{name}.png")
        ).convert_alpha()
        sprites[name] = pygame.transform.scale(
            source,
            (TILE_SIZE, TILE_SIZE),
        )

    return sprites


def draw_oracle_braziers(screen, floor, current_time):
    if not floor.has_oracle_gate:
        return

    sprites = _load_oracle_room_sprites()

    for row, tiles in enumerate(floor.map):
        for column, tile in enumerate(tiles):
            if tile != "B":
                continue

            position = (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            )
            phase_offset = column * 71 + row * 43
            frame = ((current_time + phase_offset) // 140) % 3

            screen.blit(sprites["brazier_base"], position)
            screen.blit(
                sprites[f"brazier_fire_{frame:02d}"],
                position,
            )


def draw_oracle_gate(screen, floor, current_time):
    if not floor.has_oracle_gate or floor.boss_door is None:
        return

    sprites = _load_oracle_room_sprites()
    living_boss_exists = any(
        enemy.boss_group and enemy.health > 0
        for enemy in floor.enemies
    )

    intro_sprite = oracle_gate_sprite(floor)

    if intro_sprite is not None:
        sprite_name = intro_sprite
    elif floor.boss_fight_started and living_boss_exists:
        sprite_name = "gate_closed"
    elif floor.oracle_gate_opened or not living_boss_exists:
        sprite_name = "gate_open"
    elif (
        floor.oracle_gate_opening_started_at >= 0
        and current_time - floor.oracle_gate_opening_started_at >= 200
    ):
        sprite_name = "gate_half_open"
    else:
        sprite_name = "gate_closed"

    sprite = sprites[sprite_name]
    column, row = floor.boss_door
    rectangle = sprite.get_rect(
        midbottom=(
            MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2,
            MAP_OFFSET_Y + (row + 1) * TILE_SIZE,
        )
    )

    player_rectangle = pygame.Rect(
        MAP_OFFSET_X + floor.player_column * TILE_SIZE,
        MAP_OFFSET_Y + floor.player_row * TILE_SIZE,
        TILE_SIZE,
        TILE_SIZE,
    )
    if (
        floor.player_row < row
        and rectangle.colliderect(player_rectangle)
    ):
        sprite = sprite.copy()
        sprite.set_alpha(110)

    screen.blit(sprite, rectangle)
