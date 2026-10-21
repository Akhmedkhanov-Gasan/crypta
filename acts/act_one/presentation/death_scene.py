from dataclasses import dataclass
from functools import lru_cache

import pygame
import resource_store as resources

from acts.act_one.presentation.player import (
    draw_act_one_prisoner,
)
from enemies import ENEMY_TYPES
from levels import FLOOR_CONFIGS
from presentation.layout import FONT_ROOT


KNEEL_FRAME_MS = 1100
FALL_TRANSITION_MS = 700
DEATH_EFFECT_MS = 2200
DIALOGUE_START_MS = 2400
DIALOGUE_FADE_OUT_MS = 8100
SCORE_START_MS = 8400
MENU_READY_MS = 8700

SCORE_ENEMY_TYPES = (
    "goblin",
    "brute",
    "archer",
    "warden",
)

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
        "title": resources.load_font(
            str(FONT_ROOT / "PixelOperator-Bold.ttf"), 48
        ),
        "heading": resources.load_font(
            str(FONT_ROOT / "PixelOperator-Bold.ttf"), 28
        ),
        "text": resources.load_font(
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


def _darker(color, amount):
    return tuple(
        max(0, channel - amount)
        for channel in color
    )


def _lighter(color, amount):
    return tuple(
        min(255, channel + amount)
        for channel in color
    )


def _draw_kneeling_prisoner(
    screen,
    center_x,
    floor_y,
    cloth_color,
    edge_color,
    skin_color,
):
    actor = pygame.Surface(
        (40, 42),
        pygame.SRCALPHA,
    )
    cloth_shadow = _darker(
        cloth_color,
        31,
    )
    cloth_deep = _darker(
        cloth_color,
        47,
    )
    cloth_light = _lighter(
        cloth_color,
        13,
    )
    skin_shadow = _darker(
        skin_color,
        39,
    )

    pygame.draw.ellipse(
        actor,
        (2, 3, 5, 165),
        (6, 32, 28, 6),
    )

    pygame.draw.line(
        actor,
        (44, 44, 45),
        (17, 24),
        (12, 29),
        5,
    )
    pygame.draw.line(
        actor,
        (48, 48, 49),
        (12, 29),
        (8, 34),
        4,
    )
    pygame.draw.line(
        actor,
        (37, 38, 40),
        (21, 24),
        (25, 30),
        5,
    )
    pygame.draw.line(
        actor,
        (41, 42, 44),
        (25, 30),
        (31, 33),
        4,
    )

    pygame.draw.line(
        actor,
        (18, 18, 20),
        (5, 35),
        (11, 34),
        3,
    )
    pygame.draw.line(
        actor,
        (18, 18, 20),
        (28, 34),
        (34, 34),
        3,
    )

    pygame.draw.polygon(
        actor,
        cloth_deep,
        (
            (12, 12),
            (20, 10),
            (27, 15),
            (28, 24),
            (24, 27),
            (20, 25),
            (17, 28),
            (12, 25),
            (9, 18),
        ),
    )
    pygame.draw.polygon(
        actor,
        cloth_color,
        (
            (13, 13),
            (20, 12),
            (25, 16),
            (26, 23),
            (22, 25),
            (19, 23),
            (16, 26),
            (12, 23),
            (11, 17),
        ),
    )
    pygame.draw.line(
        actor,
        cloth_light,
        (14, 14),
        (22, 14),
    )
    pygame.draw.line(
        actor,
        cloth_shadow,
        (17, 14),
        (15, 23),
    )
    pygame.draw.line(
        actor,
        edge_color,
        (12, 22),
        (25, 22),
    )

    pygame.draw.line(
        actor,
        cloth_deep,
        (13, 15),
        (8, 21),
        4,
    )
    pygame.draw.line(
        actor,
        skin_shadow,
        (8, 21),
        (9, 27),
        2,
    )
    pygame.draw.line(
        actor,
        cloth_deep,
        (24, 16),
        (29, 22),
        4,
    )
    pygame.draw.line(
        actor,
        skin_color,
        (29, 22),
        (28, 28),
        2,
    )

    pygame.draw.circle(
        actor,
        skin_shadow,
        (9, 27),
        1,
    )
    pygame.draw.circle(
        actor,
        skin_color,
        (28, 28),
        1,
    )

    pygame.draw.rect(
        actor,
        skin_shadow,
        (15, 9, 5, 5),
    )
    pygame.draw.ellipse(
        actor,
        skin_color,
        (11, 4, 10, 9),
    )
    pygame.draw.polygon(
        actor,
        (28, 26, 27),
        (
            (10, 8),
            (11, 4),
            (15, 1),
            (20, 3),
            (23, 8),
            (20, 10),
            (17, 8),
            (14, 10),
        ),
    )
    pygame.draw.line(
        actor,
        skin_shadow,
        (13, 10),
        (19, 11),
    )

    screen.blit(
        actor,
        (
            center_x - 20,
            floor_y - 37,
        ),
    )


def _draw_fallen_prisoner(
    screen,
    center_x,
    floor_y,
    cloth_color,
    edge_color,
    skin_color,
):
    actor = pygame.Surface(
        (56, 28),
        pygame.SRCALPHA,
    )
    cloth_shadow = _darker(
        cloth_color,
        31,
    )
    cloth_deep = _darker(
        cloth_color,
        47,
    )
    cloth_light = _lighter(
        cloth_color,
        12,
    )
    skin_shadow = _darker(
        skin_color,
        41,
    )

    pygame.draw.ellipse(
        actor,
        (2, 3, 5, 175),
        (4, 18, 48, 7),
    )

    pygame.draw.line(
        actor,
        (40, 41, 43),
        (18, 15),
        (8, 20),
        5,
    )
    pygame.draw.line(
        actor,
        (33, 34, 36),
        (20, 17),
        (11, 23),
        5,
    )
    pygame.draw.line(
        actor,
        (18, 18, 20),
        (5, 22),
        (11, 20),
        3,
    )
    pygame.draw.line(
        actor,
        (17, 17, 19),
        (8, 24),
        (14, 22),
        3,
    )

    pygame.draw.polygon(
        actor,
        cloth_deep,
        (
            (16, 8),
            (31, 6),
            (40, 10),
            (42, 17),
            (36, 21),
            (27, 19),
            (20, 22),
            (14, 17),
        ),
    )
    pygame.draw.polygon(
        actor,
        cloth_color,
        (
            (18, 9),
            (31, 8),
            (38, 11),
            (39, 16),
            (34, 19),
            (27, 17),
            (21, 20),
            (16, 16),
        ),
    )
    pygame.draw.line(
        actor,
        cloth_light,
        (19, 10),
        (33, 9),
    )
    pygame.draw.line(
        actor,
        cloth_shadow,
        (24, 9),
        (22, 18),
    )
    pygame.draw.line(
        actor,
        edge_color,
        (18, 16),
        (38, 16),
    )

    pygame.draw.line(
        actor,
        cloth_deep,
        (25, 11),
        (29, 21),
        4,
    )
    pygame.draw.line(
        actor,
        skin_shadow,
        (29, 21),
        (35, 23),
        2,
    )
    pygame.draw.line(
        actor,
        cloth_deep,
        (35, 11),
        (42, 17),
        4,
    )
    pygame.draw.line(
        actor,
        skin_color,
        (42, 17),
        (46, 19),
        2,
    )

    pygame.draw.rect(
        actor,
        skin_shadow,
        (39, 10, 5, 5),
    )
    pygame.draw.ellipse(
        actor,
        skin_color,
        (41, 7, 9, 9),
    )
    pygame.draw.polygon(
        actor,
        (27, 25, 27),
        (
            (39, 11),
            (40, 7),
            (44, 4),
            (49, 6),
            (52, 11),
            (49, 14),
            (46, 11),
            (43, 14),
        ),
    )
    pygame.draw.line(
        actor,
        skin_shadow,
        (43, 13),
        (49, 13),
    )

    screen.blit(
        actor,
        (
            center_x - 28,
            floor_y - 22,
        ),
    )


def _draw_dropped_knife(
    screen,
    handle,
    guard,
    tip,
):
    pygame.draw.line(
        screen,
        (18, 16, 16),
        handle,
        guard,
        3,
    )
    pygame.draw.line(
        screen,
        (94, 68, 47),
        handle,
        guard,
    )
    pygame.draw.line(
        screen,
        (31, 34, 37),
        (
            guard[0] - 1,
            guard[1] - 2,
        ),
        (
            guard[0] + 1,
            guard[1] + 2,
        ),
        2,
    )
    pygame.draw.line(
        screen,
        (67, 76, 82),
        guard,
        tip,
        2,
    )
    pygame.draw.line(
        screen,
        (136, 144, 148),
        guard,
        tip,
    )


def _draw_death_impact(
    screen,
    center_x,
    floor_y,
    elapsed,
):
    impact_elapsed = (
        elapsed
        - KNEEL_FRAME_MS
        - FALL_TRANSITION_MS
    )

    if not 0 <= impact_elapsed < 760:
        return

    progress = impact_elapsed / 760
    visibility = 1.0 - progress
    effect = pygame.Surface(
        (74, 38),
        pygame.SRCALPHA,
    )

    ring_width = round(
        18 + progress * 40
    )
    pygame.draw.ellipse(
        effect,
        (
            94,
            89,
            84,
            round(105 * visibility),
        ),
        (
            37 - ring_width // 2,
            25 - round(progress * 3),
            ring_width,
            5 + round(progress * 4),
        ),
        width=1,
    )

    fragments = (
        (-15, -3),
        (-11, -7),
        (-6, -10),
        (7, -9),
        (12, -6),
        (17, -2),
    )

    for index, offset in enumerate(fragments):
        x = round(
            37 + offset[0] * progress
        )
        lift = round(
            8
            * progress
            * (1.0 - progress)
        )
        y = round(
            25
            + offset[1] * progress
            - lift
        )
        shade = 91 + index * 8

        pygame.draw.rect(
            effect,
            (
                shade,
                shade - 4,
                shade - 8,
                round(150 * visibility),
            ),
            (
                x,
                y,
                2 if index % 2 == 0 else 1,
                2,
            ),
        )

    screen.blit(
        effect,
        (
            center_x - 37,
            floor_y - 25,
        ),
    )


def draw_act_one_player_death(
    screen,
    center_x,
    center_y,
    current_time,
    started_at,
    cloth_color,
    edge_color,
    skin_color,
):
    if started_at < 0:
        return

    elapsed = max(
        0,
        current_time - started_at,
    )
    floor_y = center_y + 14

    base_actor = pygame.Surface(
        (48, 56),
        pygame.SRCALPHA,
    )
    draw_act_one_prisoner(
        base_actor,
        24,
        31,
        cloth_color,
        edge_color,
        skin_color,
        current_time=current_time,
        movement_direction=(0, 1),
        head_lift_progress=0.0,
        knife_visible=False,
        pain_pose=False,
    )

    agony_actor = pygame.Surface(
        (48, 56),
        pygame.SRCALPHA,
    )
    draw_act_one_prisoner(
        agony_actor,
        24,
        31,
        cloth_color,
        edge_color,
        skin_color,
        current_time=current_time,
        movement_direction=(0, 1),
        head_lift_progress=0.0,
        knife_visible=False,
        pain_pose=True,
    )

    standing_position = (
        center_x - 24,
        center_y - 31,
    )
    knife_handle = (
        center_x + 7,
        floor_y - 2,
    )
    knife_guard = (
        center_x + 10,
        floor_y,
    )
    knife_tip = (
        center_x + 15,
        floor_y + 1,
    )

    if elapsed < KNEEL_FRAME_MS:
        agony_progress = _fade(
            elapsed,
            120,
            520,
        )

        if agony_progress < 1.0:
            base_pose = base_actor.copy()
            base_pose.set_alpha(
                round(
                    255
                    * (
                        1.0
                        - agony_progress
                    )
                )
            )
            screen.blit(
                base_pose,
                standing_position,
            )

        agony_pose = agony_actor.copy()
        agony_pose.set_alpha(
            round(
                255 * agony_progress
            )
        )
        screen.blit(
            agony_pose,
            standing_position,
        )

        _draw_dropped_knife(
            screen,
            knife_handle,
            knife_guard,
            knife_tip,
        )
        return

    transition_progress = min(
        1.0,
        (
            elapsed - KNEEL_FRAME_MS
        )
        / FALL_TRANSITION_MS,
    )

    agony_bounds = agony_actor.get_bounding_rect(
        min_alpha=1
    )
    agony_sprite = agony_actor.subsurface(
        agony_bounds
    ).copy()

    stain_progress = _fade(
        elapsed,
        KNEEL_FRAME_MS
        + FALL_TRANSITION_MS
        - 100,
        1000,
    )
    stain = pygame.Surface(
        (38, 12),
        pygame.SRCALPHA,
    )
    pygame.draw.ellipse(
        stain,
        (
            68,
            24,
            29,
            round(68 * stain_progress),
        ),
        (
            19 - round(15 * stain_progress),
            5,
            max(
                1,
                round(30 * stain_progress),
            ),
            5,
        ),
    )
    screen.blit(
        stain,
        (
            center_x - 19,
            floor_y - 7,
        ),
    )

    if transition_progress < 1.0:
        standing = agony_actor.copy()
        standing.set_alpha(
            round(
                255
                * (
                    1.0
                    - transition_progress
                )
            )
        )
        screen.blit(
            standing,
            standing_position,
        )

        afterimages = (
            (-18, 0.24),
            (-42, 0.50),
            (-70, 0.76),
        )

        for angle, position in afterimages:
            distance = abs(
                transition_progress
                - position
            )
            visibility = max(
                0.0,
                1.0 - distance / 0.34,
            )

            if visibility <= 0.0:
                continue

            afterimage = pygame.transform.rotate(
                agony_sprite,
                angle,
            )
            afterimage.set_alpha(
                round(
                    82 * visibility
                )
            )
            screen.blit(
                afterimage,
                afterimage.get_rect(
                    midbottom=(
                        center_x,
                        floor_y
                        - round(
                            (
                                1.0
                                - position
                            )
                            * 6
                        ),
                    ),
                ),
            )

    fallen_visibility = _fade(
        transition_progress,
        0.35,
        0.65,
    )
    fallen = pygame.transform.rotate(
        agony_sprite,
        -90,
    )
    fallen.set_alpha(
        round(
            255 * fallen_visibility
        )
    )
    screen.blit(
        fallen,
        fallen.get_rect(
            midbottom=(
                center_x,
                floor_y + 1,
            ),
        ),
    )

    _draw_dropped_knife(
        screen,
        knife_handle,
        knife_guard,
        knife_tip,
    )
    _draw_death_impact(
        screen,
        center_x,
        floor_y,
        elapsed,
    )


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
            gray.set_alpha(
                round(
                    255
                    * _fade(
                        elapsed,
                        0,
                        1400,
                    )
                )
            )
            screen.blit(gray, (0, 0))
    else:
        screen.blit(scene.background, (0, 0))

    shade = pygame.Surface(
        screen.get_size(),
        pygame.SRCALPHA,
    )
    shade.fill(
        (
            0,
            0,
            0,
            round(
                155
                * _fade(
                    elapsed,
                    550,
                    1300,
                )
            ),
        )
    )
    screen.blit(
        shade,
        (0, 0),
    )

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
