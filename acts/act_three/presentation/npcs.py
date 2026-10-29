import pygame

import resource_store as resources

from acts.act_three.npcs import (
    NPC_FOOTPRINTS,
    NPC_FRAME_COUNT,
    close_npc_dialog,
    get_npc_animation,
    get_npc_cells,
)
from presentation.layout import (
    ACT_THREE_TILE_SIZE,
    ACT_THREE_VIEW_HEIGHT,
    ACT_THREE_VIEW_WIDTH,
    ACT_THREE_VIEW_X,
    ACT_THREE_VIEW_Y,
    ASSET_ROOT,
)


NPC_DIALOG_RECT = pygame.Rect(
    ACT_THREE_VIEW_X + (ACT_THREE_VIEW_WIDTH - 480) // 2,
    ACT_THREE_VIEW_Y + ACT_THREE_VIEW_HEIGHT - 184,
    480,
    172,
)
NPC_DIALOG_CLOSE_RECT = pygame.Rect(
    NPC_DIALOG_RECT.right - 158,
    NPC_DIALOG_RECT.bottom - 48,
    138,
    32,
)


def load_act_three_npc_assets():
    frames = {}
    for npc_type, (width, height) in NPC_FOOTPRINTS.items():
        root = ASSET_ROOT / "act_3" / "npcs" / npc_type
        frames[npc_type] = {}
        for animation in (
            "work_down",
            "talk_start_down",
            "talk_idle_down",
        ):
            frames[npc_type][animation] = tuple(
                pygame.transform.scale(
                    resources.load_image(
                        root
                        / animation
                        / f"{animation}_{index:02d}.png"
                    ).convert_alpha(),
                    (
                        width * ACT_THREE_TILE_SIZE,
                        height * ACT_THREE_TILE_SIZE,
                    ),
                )
                for index in range(1, NPC_FRAME_COUNT + 1)
            )
    return {"act_three_npc_frames": frames}


def draw_world_npcs(context, game_state, assets, current_time):
    for npc in context.floor.act_three_npcs:
        if not get_npc_cells(npc).intersection(
            context.floor.visible_cells
        ):
            continue

        animation, frame = get_npc_animation(
            game_state,
            npc,
            current_time,
        )
        column, row = npc["position"]
        sprite = assets["act_three_npc_frames"][npc["type"]][
            animation
        ][frame]
        context.view_surface.blit(
            sprite,
            (
                column * ACT_THREE_TILE_SIZE - context.camera_x,
                row * ACT_THREE_TILE_SIZE - context.camera_y,
            ),
        )


def draw_npc_dialog(screen, game_state, fonts):
    state = game_state.act_three
    if (
        state.npc_dialog_position is None
        or state.npc_dialog_phase not in ("opening", "talk")
    ):
        return

    pygame.draw.rect(screen, (24, 21, 23), NPC_DIALOG_RECT)
    pygame.draw.rect(
        screen,
        (131, 104, 72),
        NPC_DIALOG_RECT,
        width=2,
    )
    title = fonts["sidebar_heading"].render(
        "Blacksmith",
        True,
        (231, 210, 177),
    )
    screen.blit(
        title,
        (NPC_DIALOG_RECT.x + 20, NPC_DIALOG_RECT.y + 16),
    )
    message = fonts["text"].render(
        "The forge will be available soon.",
        True,
        (208, 204, 197),
    )
    screen.blit(
        message,
        (NPC_DIALOG_RECT.x + 20, NPC_DIALOG_RECT.y + 58),
    )
    pygame.draw.rect(
        screen,
        (67, 52, 43),
        NPC_DIALOG_CLOSE_RECT,
    )
    label = fonts["sidebar_numbers"].render(
        "Close [Esc]",
        True,
        (231, 210, 177),
    )
    screen.blit(
        label,
        label.get_rect(center=NPC_DIALOG_CLOSE_RECT.center),
    )


def handle_npc_dialog_event(event, game_state, mouse_position):
    if game_state.act_three.npc_dialog_position is None:
        return False

    close_requested = (
        event.type == pygame.KEYDOWN
        and event.key == pygame.K_ESCAPE
    )
    if (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button == 1
        and mouse_position is not None
        and NPC_DIALOG_CLOSE_RECT.collidepoint(mouse_position)
    ):
        close_requested = True

    if close_requested:
        close_npc_dialog(game_state, pygame.time.get_ticks())
    return True
