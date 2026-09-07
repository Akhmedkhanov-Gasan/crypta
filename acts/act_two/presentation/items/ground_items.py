import pygame

from acts.ground_items import ground_items_at_player
from acts.act_two.presentation.items.renderer import (
    draw_dropped_consumables,
)
from presentation.camera import camera_render_rectangle
from presentation.ground_items import (
    draw_ground_items as draw_shared_ground_items,
)
from presentation.layout import (
    ACT_TWO_VIEW_HEIGHT,
    ACT_TWO_VIEW_WIDTH,
    ACT_TWO_VIEW_X,
    ACT_TWO_VIEW_Y,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
)
from settings import TILE_SIZE
from systems.ground_items import DROPPED_ITEM_FLIGHT_MS


def draw_ground_items(screen, game_state, sprites, current_time):
    floor = game_state.floor

    draw_shared_ground_items(
        screen,
        game_state,
        sprites,
        current_time,
        TILE_SIZE,
        (MAP_OFFSET_X, MAP_OFFSET_Y),
        separate_sources=("treasury",),
    )

    draw_dropped_consumables(
        screen,
        [
            dropped
            for dropped in floor.dropped_consumables
            if current_time - dropped.thrown_at < DROPPED_ITEM_FLIGHT_MS
        ],
        floor.visible_cells,
        sprites,
        current_time,
    )


def draw_pickup_hint(
    screen,
    game_state,
    window,
    camera,
    font,
    current_time,
    enabled,
):
    if not enabled or window.is_open:
        return

    items = ground_items_at_player(game_state, current_time)
    if not items:
        return

    viewport = pygame.Rect(
        ACT_TWO_VIEW_X,
        ACT_TWO_VIEW_Y,
        ACT_TWO_VIEW_WIDTH,
        ACT_TWO_VIEW_HEIGHT,
    )
    render_rect = camera_render_rectangle(viewport, camera.zoom)
    floor = game_state.floor

    center_x = render_rect.left + round(
        (
            floor.player_column * TILE_SIZE
            + TILE_SIZE / 2
            - round(camera.x)
        )
        * camera.zoom
    )
    top_y = render_rect.top + round(
        (floor.player_row * TILE_SIZE - round(camera.y))
        * camera.zoom
    )

    text = font.render(
        "[G] Open pile" if len(items) > 1 else "[G] Pick up",
        True,
        (255, 240, 204),
    )

    panel = pygame.Surface(
        (text.get_width() + 20, text.get_height() + 12),
        pygame.SRCALPHA,
    )
    panel.fill((15, 13, 18, 230))
    pygame.draw.rect(
        panel,
        (173, 143, 92),
        panel.get_rect(),
        width=1,
        border_radius=4,
    )
    panel.blit(text, (10, 6))

    rect = panel.get_rect(midbottom=(center_x, top_y - 8))
    rect.clamp_ip(viewport.inflate(-12, -12))
    screen.blit(panel, rect)
