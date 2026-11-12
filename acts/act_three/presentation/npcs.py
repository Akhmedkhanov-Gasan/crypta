import pygame

import resource_store as resources

from acts.act_three.npcs import (
    NPC_FOOTPRINTS,
    NPC_ANIMATIONS,
    NPC_FRAME_COUNT,
    close_npc_dialog,
    continue_npc_dialog,
    get_npc_animation,
    get_npc_at,
    get_npc_cells,
)
from acts.act_three.npc_dialogue import get_npc_dialogue
from presentation.layout import (
    ACT_THREE_TILE_SIZE,
    ASSET_ROOT,
)
from acts.act_three.presentation.dialogue_panel import draw_dialogue_panel


def load_act_three_npc_assets():
    frames = {}
    for npc_type, (width, height) in NPC_FOOTPRINTS.items():
        root = ASSET_ROOT / "act_3" / "npcs" / npc_type
        frames[npc_type] = {}
        for animation in NPC_ANIMATIONS[npc_type]:
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

    npc = get_npc_at(game_state.floor, state.npc_dialog_position)
    if npc is None:
        return
    lines = get_npc_dialogue(game_state, npc)
    speaker_id, message = lines[state.npc_dialog_line_index]
    close_label = (
        "SPACE / CLICK - CONTINUE"
        if state.npc_dialog_line_index + 1 < len(lines)
        else "SPACE / CLICK - TRADE" if npc["type"] == "trader"
        else "SPACE / CLICK - CLOSE"
    )
    draw_dialogue_panel(
        screen, fonts, speaker_id, speaker_id.replace("_", " ").upper(),
        message, close_label=close_label,
    )


def handle_npc_dialog_event(event, game_state, mouse_position):
    if game_state.act_three.npc_dialog_position is None:
        return False

    if (
        event.type == pygame.KEYDOWN
        and event.key == pygame.K_ESCAPE
        and not getattr(event, "repeat", False)
    ):
        close_npc_dialog(game_state, pygame.time.get_ticks())
        return True

    continue_requested = (
        event.type == pygame.KEYDOWN
        and event.key == pygame.K_SPACE
        and not getattr(event, "repeat", False)
    )
    if (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button == 1
    ):
        continue_requested = True

    if continue_requested:
        continue_npc_dialog(game_state, pygame.time.get_ticks())
    return True
