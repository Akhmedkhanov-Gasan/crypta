import math
from dataclasses import dataclass
from functools import lru_cache

import pygame

from enemies import ENEMY_TYPES
from levels import FLOOR_CONFIGS
from presentation.layout import FONT_ROOT


DEATH_EFFECT_MS = 2200
DIALOGUE_START_MS = 2400
DIALOGUE_FADE_OUT_MS = 11400
SCORE_START_MS = 11600
MENU_READY_MS = 11800

SCORE_ENEMY_TYPES = ("goblin", "brute", "archer")

OLD_MAN_LINES = (
    "The dark has taken your breath, not your chance.",
    "Remember what struck you down.",
)


@dataclass
class ActOneDeathScene:
    started_at: int
    background: pygame.Surface | None = None
    last_advance_at: int = -1000


@lru_cache(maxsize=1)
def _fonts():
    return {
        "title": pygame.font.Font(
            str(FONT_ROOT / "PixelOperator-Bold.ttf"), 48
        ),
        "heading": pygame.font.Font(
            str(FONT_ROOT / "PixelOperator-Bold.ttf"), 28
        ),
        "text": pygame.font.Font(
            str(FONT_ROOT / "PixelOperator.ttf"), 24
        ),
    }


def _fade(elapsed, start, duration):
    progress = max(0.0, min(1.0, (elapsed - start) / duration))
    return progress * progress * (3.0 - 2.0 * progress)


def _center_text(surface, font, text, position, color):
    label = font.render(text, False, color)
    surface.blit(label, label.get_rect(midtop=position))


def _panel_rect(size):
    panel = pygame.Rect(0, 0, 800, 520)
    panel.center = (size[0] // 2, size[1] // 2)
    return panel


def _menu_button(size):
    panel = _panel_rect(size)
    return pygame.Rect(panel.centerx - 130, panel.bottom - 76, 260, 46)


def begin_act_one_death(game_state, current_time):
    if (
        game_state.floor.presentation_act != 1
        or game_state.player.health > 0
        or game_state.act_one_death_scene is not None
    ):
        return

    game_state.act_one_death_scene = ActOneDeathScene(current_time)
    game_state.player.death_animation_started_at = current_time


def draw_act_one_player_death(
    screen,
    center_x,
    center_y,
    current_time,
    started_at,
):
    if started_at < 0:
        return

    elapsed = max(0, current_time - started_at)
    if elapsed >= DEATH_EFFECT_MS:
        return

    fall = _fade(elapsed, 0, 1200)
    vanish = _fade(elapsed, 1000, 1200)

    body = pygame.Surface((32, 32), pygame.SRCALPHA)

    pygame.draw.polygon(
        body,
        (18, 20, 26),
        ((16, 4), (25, 13), (27, 26), (5, 26), (7, 13)),
    )
    pygame.draw.polygon(
        body,
        (58, 65, 76),
        ((16, 6), (23, 14), (24, 24), (8, 24), (9, 14)),
    )
    pygame.draw.circle(body, (116, 132, 145), (16, 11), 7)
    pygame.draw.circle(body, (25, 29, 37), (16, 12), 5)
    pygame.draw.line(body, (82, 94, 107), (16, 17), (16, 23))
    pygame.draw.rect(body, (174, 165, 151), (13, 11, 2, 1))
    pygame.draw.rect(body, (174, 165, 151), (18, 11, 2, 1))

    fallen_body = pygame.transform.rotate(body, -80 * fall)
    fallen_body.set_alpha(round(255 * (1.0 - vanish)))

    screen.blit(
        fallen_body,
        fallen_body.get_rect(
            center=(
                round(center_x + 7 * fall),
                round(center_y + 7 * fall),
            )
        ),
    )

    if elapsed < 800:
        return

    dust = pygame.Surface((80, 80), pygame.SRCALPHA)
    dust_progress = min(1.0, (elapsed - 800) / 1400)
    alpha = round(190 * math.sin(math.pi * dust_progress))

    for index in range(14):
        angle = index * 2.39996
        distance = (5 + index % 5 * 3) * dust_progress
        x = round(40 + 7 * fall + math.cos(angle) * distance)
        y = round(
            40 + 6
            + math.sin(angle) * distance * 0.5
            - dust_progress * (8 + index % 4 * 3)
        )
        shade = 115 + index % 4 * 22
        pygame.draw.rect(
            dust,
            (shade, shade, shade, alpha),
            (x, y, 2, 2),
        )

    screen.blit(dust, (center_x - 40, center_y - 40))


def handle_act_one_death_event(
    event,
    game_state,
    mouse_position,
    current_time,
    screen_size,
):
    scene = game_state.act_one_death_scene
    if scene is None:
        return None

    key_pressed = (
        event.type == pygame.KEYDOWN
        and not getattr(event, "repeat", False)
    )
    mouse_clicked = (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button in (1, 2, 3)
    )

    if not (key_pressed or mouse_clicked):
        return None

    if current_time - scene.last_advance_at < 180:
        return None

    scene.last_advance_at = current_time
    elapsed = max(0, current_time - scene.started_at)

    if elapsed < DIALOGUE_START_MS:
        target_elapsed = DIALOGUE_START_MS + 800
    elif elapsed < MENU_READY_MS:
        target_elapsed = MENU_READY_MS
    else:
        return "menu"

    skipped_time = target_elapsed - elapsed
    scene.started_at -= skipped_time
    game_state.player.death_animation_started_at -= skipped_time

    return None


def _draw_score(surface, game_state, mouse_position, ready):
    fonts = _fonts()
    panel = _panel_rect(surface.get_size())

    pygame.draw.rect(surface, (15, 15, 18, 244), panel, border_radius=4)
    pygame.draw.rect(
        surface, (104, 104, 110), panel, 1, border_radius=4
    )
    pygame.draw.rect(
        surface, (43, 43, 49), panel.inflate(-10, -10), 1
    )

    _center_text(
        surface,
        fonts["title"],
        "THE DESCENT ENDS",
        (panel.centerx, panel.top + 28),
        (224, 224, 228),
    )
    _center_text(
        surface,
        fonts["text"],
        "ACT I - THE UPPER CRYPTS",
        (panel.centerx, panel.top + 87),
        (139, 139, 148),
    )

    left_x = panel.left + 34
    right_x = panel.centerx + 38

    surface.blit(
        fonts["heading"].render("YOUR DESCENT", False, (192, 192, 199)),
        (left_x, panel.top + 140),
    )
    surface.blit(
        fonts["heading"].render("ENEMIES SLAIN", False, (192, 192, 199)),
        (right_x, panel.top + 140),
    )

    pygame.draw.line(
        surface,
        (61, 61, 68),
        (left_x, panel.top + 178),
        (panel.right - 34, panel.top + 178),
    )
    pygame.draw.line(
        surface,
        (44, 44, 51),
        (panel.centerx, panel.top + 196),
        (panel.centerx, panel.top + 402),
    )

    stats = game_state.run_stats
    completed = sum(
        1
        for index in stats.completed_floors
        if 0 <= index < len(FLOOR_CONFIGS)
        and FLOOR_CONFIGS[index]["act"] == 1
    )
    floor_number = FLOOR_CONFIGS[game_state.floor_index]["act_floor"]

    rows = (
        ("Floor reached", str(floor_number)),
        ("Floors cleared", str(completed)),
        (
            "Enemies slain",
            str(sum(
                stats.kills_by_type.get(enemy_type, 0)
                for enemy_type in SCORE_ENEMY_TYPES
            )),
        ),
        ("Crates broken", str(stats.crates_broken)),
        ("Turns taken", str(stats.turns_taken)),
        ("Potions used", str(stats.consumables_used)),
    )

    for index, (label, value) in enumerate(rows):
        y = panel.top + 196 + index * 36
        surface.blit(
            fonts["text"].render(label, False, (159, 159, 169)),
            (left_x, y),
        )
        value_surface = fonts["text"].render(
            value, False, (226, 226, 232)
        )
        surface.blit(
            value_surface,
            value_surface.get_rect(topright=(panel.centerx - 34, y)),
        )

    for index, enemy_type in enumerate(SCORE_ENEMY_TYPES):
        y = panel.top + 196 + index * 36
        name = ENEMY_TYPES[enemy_type]["display_name"]
        count = stats.kills_by_type.get(enemy_type, 0)

        surface.blit(
            fonts["text"].render(name, False, (159, 159, 169)),
            (right_x, y),
        )
        value_surface = fonts["text"].render(
            str(count), False, (226, 226, 232)
        )
        surface.blit(
            value_surface,
            value_surface.get_rect(topright=(panel.right - 34, y)),
        )

    button = _menu_button(surface.get_size())
    hovered = ready and button.collidepoint(mouse_position)

    pygame.draw.rect(
        surface,
        (53, 53, 61) if hovered else (29, 29, 35),
        button,
        border_radius=3,
    )
    pygame.draw.rect(
        surface,
        (196, 196, 204) if hovered else (104, 104, 115),
        button,
        1,
        border_radius=3,
    )

    label = fonts["text"].render(
        "RETURN TO MENU", False, (226, 226, 232)
    )
    surface.blit(label, label.get_rect(center=button.center))

    _center_text(
        surface,
        fonts["text"],
        "ANY KEY / CLICK",
        (panel.centerx, panel.bottom - 26),
        (117, 117, 128),
    )


def draw_act_one_death_overlay(
    screen,
    game_state,
    current_time,
    mouse_position,
):
    scene = game_state.act_one_death_scene
    if scene is None:
        return

    elapsed = max(0, current_time - scene.started_at)

    if scene.background is None:
        gray = pygame.transform.grayscale(screen)

        if elapsed >= DEATH_EFFECT_MS:
            scene.background = gray
            screen.blit(gray, (0, 0))
        else:
            gray.set_alpha(round(255 * _fade(elapsed, 300, 1900)))
            screen.blit(gray, (0, 0))
    else:
        screen.blit(scene.background, (0, 0))

    shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, round(155 * _fade(elapsed, 1300, 1800))))
    screen.blit(shade, (0, 0))

    if elapsed < DIALOGUE_START_MS:
        return

    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    fonts = _fonts()

    if elapsed < SCORE_START_MS:
        center_x = screen.get_width() // 2
        center_y = screen.get_height() // 2

        _center_text(
            overlay,
            fonts["title"],
            "YOU HAVE FALLEN",
            (center_x, center_y - 100),
            (220, 220, 227),
        )

        for index, line in enumerate(OLD_MAN_LINES):
            _center_text(
                overlay,
                fonts["text"],
                line,
                (center_x, center_y + index * 32),
                (178, 178, 190),
            )

        opacity = (
            _fade(elapsed, DIALOGUE_START_MS, 800)
            * (1.0 - _fade(elapsed, DIALOGUE_FADE_OUT_MS, 200))
        )
    else:
        _draw_score(
            overlay,
            game_state,
            mouse_position,
            elapsed >= MENU_READY_MS,
        )
        opacity = _fade(elapsed, SCORE_START_MS, 200)

    overlay.set_alpha(round(255 * opacity))
    screen.blit(overlay, (0, 0))
