from functools import lru_cache

import pygame

from acts.act_one.tutorial import (
    TUTORIAL_FLOOR_LABELS,
    WARDEN_FLOOR_LABELS,
)
from levels import FLOOR_CONFIGS
from presentation.layout import FONT_ROOT, MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE

TUTORIAL_FONT_PATH = FONT_ROOT / "PixelOperator.ttf"
TUTORIAL_FONT_SIZE = 16
TUTORIAL_LINE_GAP = 5
TUTORIAL_ANTIALIAS = False

@lru_cache(maxsize=16)
def _render_floor_label(lines):
    font = pygame.font.Font(
        str(TUTORIAL_FONT_PATH),
        TUTORIAL_FONT_SIZE,
    )
    line_spacing = font.get_linesize() + TUTORIAL_LINE_GAP
    rendered_lines = [
        font.render(line, TUTORIAL_ANTIALIAS, (197, 188, 163))
        for line in lines
    ]

    width = max(surface.get_width() for surface in rendered_lines)
    height = (
        (len(rendered_lines) - 1) * line_spacing
        + font.get_height()
    )

    label = pygame.Surface(
        (width + 4, height + 4),
        pygame.SRCALPHA,
    )

    for index, surface in enumerate(rendered_lines):
        x = (label.get_width() - surface.get_width()) // 2
        y = index * line_spacing

        shadow = font.render(
            lines[index],
            TUTORIAL_ANTIALIAS,
            (12, 12, 15),
        )
        label.blit(shadow, (x + 1, y + 2))
        label.blit(surface, (x, y))

    label.set_alpha(205)
    return label


def draw_tutorial_floor_labels(screen, game_state):
    if game_state.floor.presentation_act != 1:
        return

    floor_config = FLOOR_CONFIGS[game_state.floor_index]

    if floor_config.get("tutorial", False):
        labels = TUTORIAL_FLOOR_LABELS
    elif floor_config.get("boss_room_layout") == "warden_arena":
        labels = WARDEN_FLOOR_LABELS
    else:
        return

    for position, lines in labels:
        label = _render_floor_label(lines)
        center_x = MAP_OFFSET_X + round(position[0] * TILE_SIZE)
        top_y = MAP_OFFSET_Y + round(position[1] * TILE_SIZE)

        screen.blit(
            label,
            label.get_rect(midtop=(center_x, top_y)),
        )
