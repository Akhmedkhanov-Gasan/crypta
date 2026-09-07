import pygame

from acts.ground_items import (
    ground_items,
    ground_items_at_player,
)


def ground_item_window_layout(size, count, selected):
    width = min(480, size[0] - 32)
    available_rows = max(1, (size[1] - 160) // 42)
    row_count = min(8, available_rows, max(1, count))
    height = 116 + row_count * 42

    panel = pygame.Rect(0, 0, width, height)
    panel.center = (size[0] // 2, size[1] // 2)

    close_button = pygame.Rect(
        panel.right - 42,
        panel.top + 12,
        28,
        28,
    )

    selected = max(0, min(selected, max(0, count - 1)))
    first = selected // row_count * row_count

    rows = tuple(
        (
            index,
            pygame.Rect(
                panel.left + 16,
                panel.top + 54 + row * 42,
                panel.width - 32,
                38,
            ),
        )
        for row, index in enumerate(
            range(first, min(first + row_count, count))
        )
    )

    return panel, close_button, rows


def draw_ground_items(
    screen,
    game_state,
    sprites,
    current_time,
    tile_size,
    offset,
    separate_sources=(),
):
    floor = game_state.floor
    grouped = {}

    for item in ground_items(game_state, current_time):
        if item.position not in floor.visible_cells:
            continue
        grouped.setdefault(item.position, []).append(item)

    for position, items in grouped.items():
        if (
            len(items) == 1
            and items[0].source in separate_sources
        ):
            continue

        sprite_name = (
            "item_pile"
            if len(items) > 1
            else items[0].sprite_name
        )
        sprite = sprites[sprite_name]
        if sprite.get_size() != (tile_size, tile_size):
            sprite = pygame.transform.scale(
                sprite,
                (tile_size, tile_size),
            )

        screen.blit(
            sprite,
            (
                offset[0] + position[0] * tile_size,
                offset[1] + position[1] * tile_size,
            ),
        )


def draw_ground_item_window(
    screen,
    game_state,
    window,
    sprites,
    fonts,
    current_time,
):
    if not window.is_open:
        return

    items = ground_items_at_player(game_state, current_time)
    if not items:
        return

    selected = min(window.selected, len(items) - 1)
    panel, close_button, rows = ground_item_window_layout(
        screen.get_size(),
        len(items),
        selected,
    )

    shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 130))
    screen.blit(shade, (0, 0))

    pygame.draw.rect(
        screen,
        (24, 21, 27),
        panel,
        border_radius=8,
    )
    pygame.draw.rect(
        screen,
        (153, 126, 83),
        panel,
        width=2,
        border_radius=8,
    )

    title = fonts["heading"].render(
        f"Items on the ground ({len(items)})",
        True,
        (239, 222, 183),
    )
    screen.blit(title, (panel.left + 16, panel.top + 18))

    pygame.draw.rect(
        screen,
        (63, 43, 45),
        close_button,
        border_radius=4,
    )
    close_text = fonts["text"].render(
        "X",
        True,
        (239, 222, 183),
    )
    screen.blit(
        close_text,
        close_text.get_rect(center=close_button.center),
    )

    for index, rect in rows:
        item = items[index]
        pygame.draw.rect(
            screen,
            (83, 65, 43) if index == selected else (39, 34, 41),
            rect,
            border_radius=4,
        )

        icon = pygame.transform.scale(
            sprites[item.sprite_name],
            (28, 28),
        )
        screen.blit(icon, (rect.left + 6, rect.top + 5))

        name = fonts["text"].render(
            item.name,
            True,
            (243, 230, 203),
        )
        screen.blit(
            name,
            (
                rect.left + 44,
                rect.centery - name.get_height() // 2,
            ),
        )

    controls = fonts["log"].render(
        "WASD / arrows: select   G / Enter / click: take",
        True,
        (198, 187, 168),
    )
    screen.blit(
        controls,
        (panel.left + 16, panel.bottom - 48),
    )

    footer = fonts["log"].render(
        f"{selected + 1}/{len(items)}   Wheel: select   Esc: close",
        True,
        (198, 187, 168),
    )
    screen.blit(
        footer,
        (panel.left + 16, panel.bottom - 27),
    )
    