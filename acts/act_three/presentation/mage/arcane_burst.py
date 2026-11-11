import math

import pygame

from acts.mage_targeting import (
    mage_aiming,
    mage_preview_target,
    mage_uses_resonance,
    valid_mage_aim_target,
)

from acts.act_three.settings import (
    MAGE_ARCANE_BURST_EFFECT_MS,
)
from acts.act_three.presentation.mage.burst_effects import (
    draw_burst_charge,
    draw_summoner_burst,
    draw_warlock_burst,
)
from acts.act_three.presentation.view import _view_position
from logic import get_mage_arcane_burst_cells, get_mage_resonance_cells


_SUBCLASS_EFFECT_COLORS = {
    "warlock": {
        None: ((119, 49, 184), (218, 154, 255)),
        "concentration_release": ((155, 61, 219), (243, 197, 255)),
        "fracture": ((97, 46, 158), (199, 138, 244)),
        "resonance": ((136, 54, 202), (229, 175, 255)),
    },
    "summoner": {
        None: ((77, 184, 193), (180, 247, 240)),
        "concentration_release": ((47, 210, 181), (200, 255, 236)),
        "fracture": ((42, 150, 166), (149, 231, 231)),
        "resonance": ((66, 197, 195), (191, 250, 245)),
    },
}


def _effect_colors(subclass, effect_kind):
    palette = _SUBCLASS_EFFECT_COLORS.get(subclass)
    if palette is not None:
        return palette.get(effect_kind, palette[None])

    if effect_kind == "concentration_release":
        return (
            (181, 78, 255),
            (244, 203, 255),
        )
    if effect_kind == "fracture":
        return (
            (46, 188, 255),
            (194, 245, 255),
        )
    if effect_kind == "resonance":
        return (76, 198, 255), (210, 249, 255)
    return (
        (73, 118, 255),
        (205, 229, 255),
    )


def _cell_center(
    position,
    camera_x,
    camera_y,
    tile_size,
):
    left, top = _view_position(
        position[0],
        position[1],
        camera_x,
        camera_y,
    )
    return (
        left + tile_size // 2,
        top + tile_size // 2,
    )


def draw_act_three_arcane_burst_targeting(
    surface,
    game_state,
    camera_x,
    camera_y,
    tile_size,
    current_time,
):
    player = game_state.player
    if not mage_aiming(player):
        return

    target = mage_preview_target(game_state)
    valid = valid_mage_aim_target(game_state, target)
    resonance = mage_uses_resonance(player)
    kind = {
        "rune_of_concentration": "concentration_release",
        "rune_of_fracture": "fracture",
        "rune_of_resonance": "resonance",
    }.get(player.selected_rune_id)
    primary, highlight = _effect_colors(player.subclass, kind)
    cells = (
        get_mage_resonance_cells(game_state)
        if resonance
        else get_mage_arcane_burst_cells(game_state.floor, target, player.selected_rune_id)
        if valid
        else ()
    )
    pulse = 0.5 + 0.5 * math.sin(current_time / 115)
    overlay = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )

    for cell in cells:
        left, top = _view_position(
            cell[0],
            cell[1],
            camera_x,
            camera_y,
        )
        inset = 7 if cell == target else 11
        rectangle = pygame.Rect(
            left + inset,
            top + inset,
            tile_size - inset * 2,
            tile_size - inset * 2,
        )
        pygame.draw.rect(
            overlay,
            (*primary, round(19 + pulse * 21)),
            rectangle,
            border_radius=7,
        )
        pygame.draw.rect(
            overlay,
            (*primary, round(65 + pulse * 65)),
            rectangle,
            width=2,
            border_radius=7,
        )

    target_center = _cell_center(
        target,
        camera_x,
        camera_y,
        tile_size,
    )
    pygame.draw.circle(
        overlay,
        (*(highlight if valid else (230, 111, 123)), round(155 + pulse * 70)),
        target_center,
        round(10 + pulse * 3),
        width=2,
    )
    if valid:
        origin = _cell_center(
            (game_state.floor.player_column, game_state.floor.player_row),
            camera_x,
            camera_y,
            tile_size,
        )
        pygame.draw.line(overlay, (*primary, 110), origin, target_center, width=2)
    surface.blit(overlay, (0, 0))


def draw_act_three_arcane_burst_effect(
    surface,
    game_state,
    player_position,
    camera_x,
    camera_y,
    tile_size,
    current_time,
):
    player = game_state.player
    state = player.act_three.mage_arcane_burst
    started_at = state.ability_effect_started_at
    target = state.ability_effect_target
    if (
        player.player_class != "mage"
        or started_at <= 0
        or target is None
    ):
        return

    elapsed = current_time - started_at
    if not 0 <= elapsed < MAGE_ARCANE_BURST_EFFECT_MS:
        return

    progress = elapsed / MAGE_ARCANE_BURST_EFFECT_MS
    primary, highlight = _effect_colors(
        player.subclass,
        state.ability_effect_kind,
    )
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    resonance = state.ability_effect_kind == "resonance"
    impact_start = 0.04 if resonance else 0.16
    if progress < impact_start:
        draw_burst_charge(
            overlay,
            (
                player_position[0] + tile_size // 2,
                player_position[1] + tile_size // 2 - 8,
            ),
            tile_size,
            progress / impact_start,
            primary,
            highlight,
        )

    draw_cell_burst = (
        draw_warlock_burst if player.subclass == "warlock" else draw_summoner_burst
    )
    affected_cells = dict.fromkeys((target, *state.ability_effect_cells))
    hit_cells = set(state.ability_effect_hit_positions)
    for cell in affected_cells:
        distance = max(abs(cell[0] - target[0]), abs(cell[1] - target[1]))
        start = min(0.42, impact_start + distance * 0.095)
        if progress < start:
            continue

        cell_progress = (progress - start) / (1 - start)
        scale = 0.86 if cell == target or cell in hit_cells else 0.64
        if state.ability_effect_kind == "concentration_release":
            scale = 1.08
        elif resonance:
            scale = 0.72

        draw_cell_burst(
            overlay,
            _cell_center(cell, camera_x, camera_y, tile_size),
            tile_size * scale,
            cell_progress,
            primary,
            highlight,
            cell[0] * 0.73 + cell[1] * 1.29,
        )

    surface.blit(overlay, (0, 0))
