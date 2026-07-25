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
from settings import (
    ATTACK_WARNING_COLOR,
    CHEST_BAND_COLOR,
    CHEST_COLOR,
    DANGER_BORDER_COLOR,
    DANGER_TILE_COLOR,
    ENEMY_COLOR,
    FLOOR_COLOR,
    GAME_HEIGHT,
    GAME_WIDTH,
    GOLD_COLOR,
    GRID_COLOR,
    HEALTH_BAR_BACKGROUND,
    HEALTH_BAR_COLOR,
    KEY_COLOR,
    LOCKED_COLOR,
    MAP_COLUMNS,
    MAP_ROWS,
    OPEN_CHEST_COLOR,
    PANEL_BORDER_COLOR,
    PANEL_COLOR,
    PLAYER_ATTACK_BORDER_COLOR,
    PLAYER_ATTACK_TILE_COLOR,
    PLAYER_COLOR,
    PLAYER_HEALTH_BAR_COLOR,
    POTION_COLOR,
    STAIRS_COLOR,
    TEXT_COLOR,
    TILE_SIZE,
    WALL_COLOR,
)


def draw_dungeon(screen, dungeon_map, act_number, sprites):
    for row_index, row in enumerate(dungeon_map):
        for column_index, tile in enumerate(row):
            x = MAP_OFFSET_X + column_index * TILE_SIZE
            y = MAP_OFFSET_Y + row_index * TILE_SIZE
            tile_rectangle = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            if act_number >= 2:
                texture_name = "wall" if tile == "#" else "floor"
                screen.blit(sprites[texture_name], tile_rectangle)

                if tile == "C":
                    screen.blit(
                        sprites["pillar"],
                        tile_rectangle,
                    )
            else:
                color = WALL_COLOR if tile == "#" else FLOOR_COLOR
                pygame.draw.rect(screen, color, tile_rectangle)

            pygame.draw.rect(screen, GRID_COLOR, tile_rectangle, 1)


def draw_map_frame(screen, act_number):
    if act_number < 2:
        return

    outer_rectangle = pygame.Rect(
        MAP_OFFSET_X - 4,
        MAP_OFFSET_Y - 4,
        MAP_WIDTH + 8,
        MAP_HEIGHT + 8,
    )
    pygame.draw.rect(
        screen,
        (72, 68, 78),
        outer_rectangle,
        width=3,
    )
    pygame.draw.rect(
        screen,
        (30, 27, 34),
        outer_rectangle.inflate(-6, -6),
        width=1,
    )


def draw_attack_markers(screen, enemies):
    for enemy in enemies:
        if enemy["health"] <= 0:
            continue

        for column, row in enemy["attack_targets"]:
            target_rectangle = pygame.Rect(
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
            )
            pygame.draw.rect(screen, DANGER_TILE_COLOR, target_rectangle)
            pygame.draw.rect(
                screen,
                DANGER_BORDER_COLOR,
                target_rectangle,
                width=3,
            )


def draw_player_attack_markers(screen, attack_targets):
    for column, row in attack_targets:
        target_rectangle = pygame.Rect(
            MAP_OFFSET_X + column * TILE_SIZE,
            MAP_OFFSET_Y + row * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(
            screen,
            PLAYER_ATTACK_TILE_COLOR,
            target_rectangle,
        )
        pygame.draw.rect(
            screen,
            PLAYER_ATTACK_BORDER_COLOR,
            target_rectangle,
            width=3,
        )


def draw_oracle_projectiles(
    screen,
    projectiles,
    sprites,
):
    for projectile in projectiles:
        sprite_name = (
            "oracle_projectile_homing"
            if projectile["kind"] == "homing"
            else "oracle_projectile"
        )
        projectile_left = (
            MAP_OFFSET_X + projectile["column"] * TILE_SIZE
        )
        projectile_top = (
            MAP_OFFSET_Y + projectile["row"] * TILE_SIZE
        )
        screen.blit(
            sprites[sprite_name],
            (projectile_left, projectile_top),
        )


def draw_oracle_emitters(
    screen,
    emitters,
    is_active,
    sprites,
):
    if not is_active:
        return

    for column, row in emitters:
        left = MAP_OFFSET_X + column * TILE_SIZE
        top = MAP_OFFSET_Y + row * TILE_SIZE
        screen.blit(
            sprites["charged_pillar"],
            (left, top),
        )


def draw_player(
    screen,
    column,
    row,
    health,
    max_health,
    player_class,
    act_number,
    sprites,
    invisibility_turns,
):
    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2
    if act_number >= 2 and player_class is not None:
        player_sprite = sprites[f"player_{player_class}"]

        if invisibility_turns > 0:
            player_sprite = player_sprite.copy()
            player_sprite.set_alpha(90)

        screen.blit(
            player_sprite,
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
    else:
        pygame.draw.circle(
            screen,
            PLAYER_COLOR,
            (center_x, center_y),
            TILE_SIZE // 3,
        )

    health_ratio = health / max_health
    bar_x = MAP_OFFSET_X + column * TILE_SIZE + 4
    bar_y = MAP_OFFSET_Y + (row + 1) * TILE_SIZE - 5
    bar_width = TILE_SIZE - 8
    bar_height = 4

    pygame.draw.rect(
        screen,
        HEALTH_BAR_BACKGROUND,
        (bar_x, bar_y, bar_width, bar_height),
    )
    pygame.draw.rect(
        screen,
        PLAYER_HEALTH_BAR_COLOR,
        (bar_x, bar_y, int(bar_width * health_ratio), bar_height),
    )


def draw_enemy(screen, enemy, act_number, sprites):
    padding = TILE_SIZE // 5
    column = enemy["column"]
    row = enemy["row"]
    x = MAP_OFFSET_X + column * TILE_SIZE + padding
    y = MAP_OFFSET_Y + row * TILE_SIZE + padding
    size = TILE_SIZE - padding * 2
    color = (
        enemy["color"]
        if enemy["is_aggro"]
        else enemy["sleeping_color"]
    )

    if act_number >= 2 and enemy["type"] == "oracle":
        body_size = TILE_SIZE * 3
        body_left = MAP_OFFSET_X + (column - 1) * TILE_SIZE
        body_top = MAP_OFFSET_Y + (row - 1) * TILE_SIZE
        sprite_name = (
            "oracle_awake"
            if enemy["oracle_awakened"]
            else "oracle_idle"
        )
        screen.blit(
            sprites[sprite_name],
            (body_left, body_top),
        )

        if enemy["is_active"]:
            pygame.draw.rect(
                screen,
                DANGER_BORDER_COLOR,
                (
                    body_left + 2,
                    body_top + 2,
                    body_size - 4,
                    body_size - 4,
                ),
                width=2,
                border_radius=5,
            )

        health_ratio = enemy["health"] / enemy["max_health"]
        bar_x = body_left + 8
        bar_y = body_top + body_size - 7
        bar_width = body_size - 16
        bar_height = 5
        pygame.draw.rect(
            screen,
            HEALTH_BAR_BACKGROUND,
            (bar_x, bar_y, bar_width, bar_height),
        )
        pygame.draw.rect(
            screen,
            HEALTH_BAR_COLOR,
            (
                bar_x,
                bar_y,
                int(bar_width * health_ratio),
                bar_height,
            ),
        )

        if enemy["attack_targets"]:
            warning_x = body_left + body_size // 2
            warning_top = body_top + 8
            pygame.draw.line(
                screen,
                ATTACK_WARNING_COLOR,
                (warning_x, warning_top),
                (warning_x, warning_top + 12),
                4,
            )
            pygame.draw.circle(
                screen,
                ATTACK_WARNING_COLOR,
                (warning_x, warning_top + 19),
                3,
            )

        return

    if (
        act_number >= 2
        and enemy["type"] in (
            "goblin",
            "brute",
            "archer",
            "sentinel",
            "priest",
        )
    ):
        sprite_name = enemy["type"]

        if enemy["type"] == "sentinel":
            sprite_name = (
                "sentinel_guard"
                if enemy["shield_turns"] > 0
                else "sentinel_idle"
            )
        elif enemy["type"] == "priest":
            sprite_name = (
                "priest_cast"
                if (
                    enemy["attack_targets"]
                    or enemy["heal_target"] is not None
                )
                else "priest_idle"
            )
        enemy_sprite = sprites[sprite_name]

        screen.blit(
            enemy_sprite,
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )

        if (
            enemy["type"] == "sentinel"
            and enemy["shield_turns"] > 0
        ):
            opening_color = (235, 185, 75)
            tile_left = MAP_OFFSET_X + column * TILE_SIZE
            tile_top = MAP_OFFSET_Y + row * TILE_SIZE
            shield_direction = enemy["shield_direction"]
            vulnerable_direction = (
                -shield_direction[0],
                -shield_direction[1],
            )
            opening_lines = {
                (0, -1): (
                    (tile_left + 5, tile_top + 3),
                    (tile_left + TILE_SIZE - 5, tile_top + 3),
                ),
                (0, 1): (
                    (tile_left + 5, tile_top + TILE_SIZE - 3),
                    (
                        tile_left + TILE_SIZE - 5,
                        tile_top + TILE_SIZE - 3,
                    ),
                ),
                (-1, 0): (
                    (tile_left + 3, tile_top + 5),
                    (tile_left + 3, tile_top + TILE_SIZE - 5),
                ),
                (1, 0): (
                    (tile_left + TILE_SIZE - 3, tile_top + 5),
                    (
                        tile_left + TILE_SIZE - 3,
                        tile_top + TILE_SIZE - 5,
                    ),
                ),
            }
            opening_line = opening_lines.get(
                vulnerable_direction
            )

            if opening_line is not None:
                pygame.draw.line(
                    screen,
                    opening_color,
                    opening_line[0],
                    opening_line[1],
                    3,
                )

        if (
            enemy["type"] == "priest"
            and enemy["heal_target"] is not None
            and enemy["heal_target"]["health"] > 0
        ):
            heal_target = enemy["heal_target"]
            pygame.draw.rect(
                screen,
                (80, 220, 130),
                (
                    MAP_OFFSET_X
                    + heal_target["column"] * TILE_SIZE
                    + 3,
                    MAP_OFFSET_Y
                    + heal_target["row"] * TILE_SIZE
                    + 3,
                    TILE_SIZE - 6,
                    TILE_SIZE - 6,
                ),
                width=2,
                border_radius=4,
            )

        if enemy["is_aggro"]:
            pygame.draw.rect(
                screen,
                DANGER_BORDER_COLOR,
                (
                    MAP_OFFSET_X + column * TILE_SIZE + 2,
                    MAP_OFFSET_Y + row * TILE_SIZE + 2,
                    TILE_SIZE - 4,
                    TILE_SIZE - 4,
                ),
                width=2,
                border_radius=3,
            )
    elif enemy["type"] == "brute":
        corner = 4
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + corner, y),
                (x + size - corner, y),
                (x + size, y + corner),
                (x + size, y + size - corner),
                (x + size - corner, y + size),
                (x + corner, y + size),
                (x, y + size - corner),
                (x, y + corner),
            ],
        )
    elif enemy["type"] == "archer":
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + size // 2, y),
                (x + size, y + size),
                (x, y + size),
            ],
        )
    elif enemy["type"] == "warden":
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + size // 2, y),
                (x + size, y + size // 2),
                (x + size // 2, y + size),
                (x, y + size // 2),
            ],
        )
        crown_y = y + size // 4
        pygame.draw.line(
            screen,
            ATTACK_WARNING_COLOR,
            (x + size // 4, crown_y),
            (x + size * 3 // 4, crown_y),
            2,
        )
        pygame.draw.circle(
            screen,
            ATTACK_WARNING_COLOR,
            (x + size // 2, y + size // 2),
            3,
        )
    else:
        pygame.draw.rect(
            screen,
            color,
            (x, y, size, size),
            border_radius=6,
        )

    health_ratio = enemy["health"] / enemy["max_health"]
    bar_x = MAP_OFFSET_X + column * TILE_SIZE + 4
    bar_y = MAP_OFFSET_Y + (row + 1) * TILE_SIZE - 5
    bar_width = TILE_SIZE - 8
    bar_height = 4

    pygame.draw.rect(
        screen,
        HEALTH_BAR_BACKGROUND,
        (bar_x, bar_y, bar_width, bar_height),
    )
    pygame.draw.rect(
        screen,
        HEALTH_BAR_COLOR,
        (bar_x, bar_y, int(bar_width * health_ratio), bar_height),
    )

    if enemy["attack_targets"]:
        warning_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
        warning_top = MAP_OFFSET_Y + row * TILE_SIZE + 8
        pygame.draw.line(
            screen,
            ATTACK_WARNING_COLOR,
            (warning_x, warning_top),
            (warning_x, warning_top + 9),
            3,
        )
        pygame.draw.circle(
            screen,
            ATTACK_WARNING_COLOR,
            (warning_x, warning_top + 14),
            2,
        )


def draw_key(screen, column, row, act_number, sprites):
    if act_number >= 2:
        screen.blit(
            sprites["key"],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
        return

    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2

    pygame.draw.circle(
        screen,
        KEY_COLOR,
        (center_x - 8, center_y),
        6,
        width=3,
    )
    pygame.draw.line(
        screen,
        KEY_COLOR,
        (center_x - 2, center_y),
        (center_x + 13, center_y),
        4,
    )
    pygame.draw.line(
        screen,
        KEY_COLOR,
        (center_x + 7, center_y),
        (center_x + 7, center_y + 6),
        3,
    )
    pygame.draw.line(
        screen,
        KEY_COLOR,
        (center_x + 12, center_y),
        (center_x + 12, center_y + 5),
        3,
    )


def draw_boss_door(screen, column, row, is_open):
    cell_x = MAP_OFFSET_X + column * TILE_SIZE
    cell_y = MAP_OFFSET_Y + row * TILE_SIZE
    frame_color = (115, 75, 130)

    pygame.draw.rect(
        screen,
        frame_color,
        (cell_x + 3, cell_y + 2, TILE_SIZE - 6, TILE_SIZE - 4),
        width=3,
        border_radius=3,
    )

    if is_open:
        return

    pygame.draw.rect(
        screen,
        (55, 35, 62),
        (cell_x + 7, cell_y + 5, TILE_SIZE - 14, TILE_SIZE - 7),
        border_radius=2,
    )
    pygame.draw.line(
        screen,
        frame_color,
        (cell_x + TILE_SIZE // 2, cell_y + 7),
        (cell_x + TILE_SIZE // 2, cell_y + TILE_SIZE - 5),
        2,
    )
    pygame.draw.circle(
        screen,
        ATTACK_WARNING_COLOR,
        (cell_x + TILE_SIZE // 2, cell_y + TILE_SIZE // 2),
        3,
    )


def draw_potion(screen, column, row, act_number, sprites):
    if act_number >= 2:
        screen.blit(
            sprites["potion"],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
        return

    cell_x = MAP_OFFSET_X + column * TILE_SIZE
    cell_y = MAP_OFFSET_Y + row * TILE_SIZE
    bottle_rectangle = pygame.Rect(
        cell_x + TILE_SIZE // 2 - 6,
        cell_y + 12,
        12,
        15,
    )

    pygame.draw.rect(
        screen,
        POTION_COLOR,
        bottle_rectangle,
        border_radius=4,
    )
    pygame.draw.rect(
        screen,
        TEXT_COLOR,
        (cell_x + TILE_SIZE // 2 - 3, cell_y + 8, 6, 6),
        border_radius=2,
    )


def draw_coin(screen, column, row, act_number, sprites):
    if act_number >= 2:
        screen.blit(
            sprites["coin"],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
        return

    center_x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2

    pygame.draw.circle(
        screen,
        GOLD_COLOR,
        (center_x, center_y),
        7,
    )
    pygame.draw.circle(
        screen,
        KEY_COLOR,
        (center_x, center_y),
        7,
        width=2,
    )
    pygame.draw.line(
        screen,
        KEY_COLOR,
        (center_x, center_y - 3),
        (center_x, center_y + 3),
        2,
    )


def draw_chest(screen, chest, act_number, sprites):
    cell_x = MAP_OFFSET_X + chest["column"] * TILE_SIZE
    cell_y = MAP_OFFSET_Y + chest["row"] * TILE_SIZE

    if act_number >= 2:
        sprite_name = (
            "chest_open"
            if chest["is_open"]
            else "chest_closed"
        )
        screen.blit(sprites[sprite_name], (cell_x, cell_y))
        return

    if chest["is_open"]:
        pygame.draw.rect(
            screen,
            OPEN_CHEST_COLOR,
            (cell_x + 4, cell_y + 17, TILE_SIZE - 8, 11),
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            CHEST_COLOR,
            (cell_x + 4, cell_y + 6, TILE_SIZE - 8, 7),
            border_radius=3,
        )
        return

    pygame.draw.rect(
        screen,
        CHEST_COLOR,
        (cell_x + 4, cell_y + 9, TILE_SIZE - 8, 19),
        border_radius=4,
    )
    pygame.draw.rect(
        screen,
        CHEST_BAND_COLOR,
        (cell_x + TILE_SIZE // 2 - 3, cell_y + 9, 6, 19),
    )
    pygame.draw.rect(
        screen,
        KEY_COLOR,
        (cell_x + TILE_SIZE // 2 - 2, cell_y + 17, 4, 7),
        border_radius=2,
    )


def draw_stairs(
    screen,
    column,
    row,
    is_open,
    act_number,
    sprites,
):
    if act_number >= 2:
        sprite_name = (
            "stairs_open" if is_open else "stairs_locked"
        )
        screen.blit(
            sprites[sprite_name],
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )
        return

    color = STAIRS_COLOR if is_open else LOCKED_COLOR
    left = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 4
    top = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 5
    right = left + TILE_SIZE // 2
    bottom = top + TILE_SIZE * 3 // 5

    pygame.draw.line(screen, color, (left, top), (left, bottom), 4)
    pygame.draw.line(screen, color, (right, top), (right, bottom), 4)

    for step_number in range(4):
        step_y = top + step_number * (bottom - top) // 3
        pygame.draw.line(screen, color, (left, step_y), (right, step_y), 3)
