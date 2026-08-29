from dataclasses import dataclass
import math

import pygame

from settings import GAME_HEIGHT, GAME_WIDTH
from presentation.figma_ui import (
    draw_figma_rectangle,
    draw_figma_text,
)

MENU_ACT_TWO_TOP = 270
MENU_ACT_THREE_TOP = 500

_BACKGROUND = (0, 0, 0)
_STONE_DARK = (14, 13, 16)
_TEXT = (181, 174, 161)
_TEXT_DIM = (72, 68, 67)
_ACCENT = (94, 38, 39)
_INTERACTIVE = (132, 127, 119)

_TITLE_SHADE_ALPHA = 10
_CONTENT_SHADE_ALPHA = 10
_THEME_SHADE_ALPHA = 10

def _pygame_rect(data):
    return pygame.Rect(
        data["x"],
        data["y"],
        data["width"],
        data["height"],
    )


def _render_text_fitted(
    font,
    text,
    color,
    rectangle,
    padding=4,
):
    text_surface = font.render(text, True, color)

    available_width = max(
        1,
        rectangle.width - padding * 2,
    )
    available_height = max(
        1,
        rectangle.height - padding * 2,
    )

    if (
        text_surface.get_width() <= available_width
        and text_surface.get_height() <= available_height
    ):
        return text_surface

    scale = min(
        available_width / text_surface.get_width(),
        available_height / text_surface.get_height(),
    )

    fitted_size = (
        max(1, round(text_surface.get_width() * scale)),
        max(1, round(text_surface.get_height() * scale)),
    )

    return pygame.transform.smoothscale(
        text_surface,
        fitted_size,
    )


def _blit_layout_image(surface, image, rectangle_data):
    rectangle = _pygame_rect(rectangle_data)

    if image.get_size() != rectangle.size:
        image = pygame.transform.smoothscale(
            image,
            rectangle.size,
        )

    surface.blit(image, rectangle)


def _draw_layout_shade(
    surface,
    rectangle_data,
    alpha,
    border_radius=0,
):
    rectangle = _pygame_rect(rectangle_data)

    shade = pygame.Surface(
        rectangle.size,
        pygame.SRCALPHA,
    )

    pygame.draw.rect(
        shade,
        (0, 0, 0, alpha),
        shade.get_rect(),
        border_radius=border_radius,
    )

    surface.blit(shade, rectangle)


def _layout_entry_name(action):
    if action == "main_menu":
        return "quit"

    return action


@dataclass
class MenuState:
    page: str = "main"
    selected_index: int = 0
    music_volume: float = 0.55
    effects_volume: float = 0.65
    menu_theme: int = 1

    transition_from_theme: int | None = None
    transition_started_at: int = 0
    transition_duration_ms: int = 950


def _main_entries(game_started):
    if game_started:
        return (
            ("resume", "RETURN"),
            ("settings", "SETTINGS"),
            ("main_menu", "MAIN MENU"),
        )

    return (
        ("resume", "DESCEND"),
        ("settings", "SETTINGS"),
        ("quit", "LEAVE"),
    )


def _settings_entries(menu_state, fullscreen):
    fullscreen_label = "ON" if fullscreen else "OFF"
    return (
        ("toggle_fullscreen", f"FULLSCREEN  {fullscreen_label}"),
        ("music_volume", "MUSIC"),
        ("effects_volume", "EFFECTS"),
        ("back", "BACK"),
    )


def _entries(menu_state, game_started, fullscreen):
    if menu_state.page == "settings":
        return _settings_entries(menu_state, fullscreen)
    if menu_state.page == "confirm_abandon":
        return (
            ("back", "NO"),
            ("abandon_run", "YES"),
        )
    return _main_entries(game_started)


def _rectangles_for_page(
    menu_state,
    entries,
    menu_layout,
):
    if menu_state.page == "main":
        rectangles_by_action = {
            action: menu_layout["entries"][
                _layout_entry_name(action)
            ]["rect"]
            for action, _ in entries
        }

    elif menu_state.page == "settings":
        rectangles_by_action = {
            "toggle_fullscreen": (
                menu_layout["fullscreen"]["rect"]
            ),
            "music_volume": (
                menu_layout["sliders"]["music"]["rect"]
            ),
            "effects_volume": (
                menu_layout["sliders"]["effects"]["rect"]
            ),
            "back": menu_layout["back"]["rect"],
        }

    else:
        rectangles_by_action = {
            "back": menu_layout["entries"]["no"]["rect"],
            "abandon_run": (
                menu_layout["entries"]["yes"]["rect"]
            ),
        }

    return tuple(
        _pygame_rect(rectangles_by_action[action])
        for action, _ in entries
    )


def _slider_rectangle(menu_layout, action):
    slider_name = (
        "music"
        if action == "music_volume"
        else "effects"
    )

    return _pygame_rect(
        menu_layout["sliders"][slider_name]["track"]["rect"]
    )

def _visible_menu_themes(highest_unlocked_theme):
    highest_unlocked_theme = max(
        1,
        min(3, highest_unlocked_theme),
    )

    if highest_unlocked_theme <= 1:
        return ()

    return tuple(
        range(1, highest_unlocked_theme + 1)
    )


def get_menu_theme_rectangles(
    menu_layout,
    highest_unlocked_theme,
):
    return tuple(
        _pygame_rect(
            menu_layout["themes"][str(theme)]["rect"]
        )
        for theme in _visible_menu_themes(
            highest_unlocked_theme
        )
    )


def _set_slider_from_mouse(
    menu_state,
    action,
    menu_layout,
    mouse_x,
):
    slider = _slider_rectangle(
        menu_layout,
        action,
    )

    volume = max(
        0.0,
        min(
            1.0,
            (mouse_x - slider.x) / slider.width,
        ),
    )

    if action == "music_volume":
        menu_state.music_volume = volume
    else:
        menu_state.effects_volume = volume


def _adjust_selected_slider(menu_state, action, amount):
    attribute = (
        "music_volume"
        if action == "music_volume"
        else "effects_volume"
    )
    value = getattr(menu_state, attribute)
    setattr(menu_state, attribute, max(0.0, min(1.0, value + amount)))


def _activate_entry(menu_state, action):
    if action == "settings":
        menu_state.page = "settings"
        menu_state.selected_index = 0
        return None
    if action == "main_menu":
        menu_state.page = "confirm_abandon"
        menu_state.selected_index = 0
        return None
    if action == "back":
        menu_state.page = "main"
        menu_state.selected_index = 0
        return None
    return action


def handle_menu_event(
    event,
    menu_state,
    mouse_position,
    game_started,
    fullscreen,
    highest_unlocked_theme=1,
    menu_layout=None,
):
    if menu_state.transition_from_theme is not None:
        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_F11
        ):
            return "toggle_fullscreen"

        return None
    entries = _entries(menu_state, game_started, fullscreen)
    rectangles = _rectangles_for_page(
        menu_state,
        entries,
        menu_layout,
)

    if event.type == pygame.MOUSEMOTION and mouse_position is not None:
        for index, rectangle in enumerate(rectangles):
            if rectangle.collidepoint(mouse_position):
                menu_state.selected_index = index
                break
        if (
            getattr(event, "buttons", (False, False, False))[0]
            and menu_state.page == "settings"
        ):
            index = menu_state.selected_index
            action = entries[index][0]
            if action in ("music_volume", "effects_volume"):
                _set_slider_from_mouse(
                    menu_state,
                    action,
                    menu_layout,
                    mouse_position[0],
                )
                return "act_one_volume_changed"

    if (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button == 1
        and mouse_position is not None
    ):
        if not game_started and menu_state.page == "main":
            for theme, rectangle in enumerate(
                get_menu_theme_rectangles(
                    menu_layout,
                    highest_unlocked_theme,
                ),
                start=1,
            ):
                if rectangle.collidepoint(mouse_position):
                    if theme > highest_unlocked_theme:
                        return None

                    if theme == menu_state.menu_theme:
                        return None

                    menu_state.transition_from_theme = (
                        menu_state.menu_theme
                    )
                    menu_state.menu_theme = theme
                    menu_state.transition_started_at = (
                        pygame.time.get_ticks()
                    )

                    return "menu_theme_changed"
        for index, rectangle in enumerate(rectangles):
            if rectangle.collidepoint(mouse_position):
                menu_state.selected_index = index
                action = entries[index][0]
                if action in ("music_volume", "effects_volume"):
                    _set_slider_from_mouse(
                        menu_state,
                        action,
                        menu_layout,
                        mouse_position[0],
                    )
                    return "act_one_volume_changed"
                return _activate_entry(menu_state, action)

    if event.type != pygame.KEYDOWN:
        return None

    if event.key == pygame.K_F11:
        return "toggle_fullscreen"
    if event.key in (pygame.K_UP, pygame.K_w):
        menu_state.selected_index = (
            menu_state.selected_index - 1
        ) % len(entries)
    elif event.key in (pygame.K_DOWN, pygame.K_s):
        menu_state.selected_index = (
            menu_state.selected_index + 1
        ) % len(entries)
    elif event.key in (pygame.K_LEFT, pygame.K_a):
        action = entries[menu_state.selected_index][0]
        if action in ("music_volume", "effects_volume"):
            _adjust_selected_slider(menu_state, action, -0.05)
            return "act_one_volume_changed"
    elif event.key in (pygame.K_RIGHT, pygame.K_d):
        action = entries[menu_state.selected_index][0]
        if action in ("music_volume", "effects_volume"):
            _adjust_selected_slider(menu_state, action, 0.05)
            return "act_one_volume_changed"
    elif event.key in (
        pygame.K_RETURN,
        pygame.K_KP_ENTER,
        pygame.K_SPACE,
    ):
        return _activate_entry(
            menu_state,
            entries[menu_state.selected_index][0],
        )
    elif event.key == pygame.K_ESCAPE:
        if menu_state.page in ("settings", "confirm_abandon"):
            menu_state.page = "main"
            menu_state.selected_index = 0
        elif game_started:
            return "resume"

    return None


def _draw_menu_background(surface, menu_assets, visual_stage):
    surface.fill(_BACKGROUND)

    if visual_stage >= 3:
        surface.blit(menu_assets["act_three_background"], (0, 0))
    elif visual_stage >= 2:
        surface.blit(menu_assets["act_two_background"], (0, 0))

def _draw_theme_selector(
    surface,
    selected_theme,
    highest_unlocked_theme,
    menu_layout,
):
    visible_themes = _visible_menu_themes(
        highest_unlocked_theme
    )

    for theme in visible_themes:
        theme_layout = menu_layout["themes"][str(theme)]
        rectangle = _pygame_rect(theme_layout["rect"])
        selected = theme == selected_theme

        draw_figma_rectangle(
            surface,
            theme_layout["frame"],
        )

        if selected:
            corner_radius = round(
                theme_layout["frame"].get(
                    "corner_radius",
                    0,
                )
            )

            pygame.draw.rect(
                surface,
                _INTERACTIVE,
                rectangle,
                width=2,
                border_radius=corner_radius,
            )

        draw_figma_text(
            surface,
            theme_layout["label"],
            color_override=(
                _TEXT
                if selected
                else None
            ),
        )


def _draw_entries(
    surface,
    entries,
    selected_index,
    menu_state,
    menu_layout,
):
    rectangles = _rectangles_for_page(
        menu_state,
        entries,
        menu_layout,
    )

    for index, ((action, label), rectangle) in enumerate(
        zip(entries, rectangles)
    ):
        selected = index == selected_index
        selected_color = _TEXT if selected else None

        if menu_state.page == "main":
            layout_name = _layout_entry_name(action)
            label_spec = menu_layout["entries"][
                layout_name
            ]["label"]
            visible_label = label.title()

        elif menu_state.page == "settings":
            if action == "toggle_fullscreen":
                label_spec = menu_layout[
                    "fullscreen"
                ]["label"]
                visible_label = "Fullscreen"

                value_spec = menu_layout[
                    "fullscreen"
                ]["value"]

                draw_figma_rectangle(
                    surface,
                    value_spec,
                )

                enabled = label.strip().endswith("ON")

                if enabled:
                    value_rectangle = _pygame_rect(
                        value_spec["rect"]
                    )

                    pygame.draw.rect(
                        surface,
                        _INTERACTIVE,
                        value_rectangle,
                        border_radius=round(
                            value_spec.get(
                                "corner_radius",
                                0,
                            )
                        ),
                    )

            elif action in (
                "music_volume",
                "effects_volume",
            ):
                slider_name = (
                    "music"
                    if action == "music_volume"
                    else "effects"
                )

                slider_layout = menu_layout[
                    "sliders"
                ][slider_name]

                label_spec = slider_layout["label"]
                visible_label = label.title()

                track_spec = slider_layout["track"]
                thumb_spec = slider_layout["thumb"]

                draw_figma_rectangle(
                    surface,
                    track_spec,
                )

                volume = (
                    menu_state.music_volume
                    if action == "music_volume"
                    else menu_state.effects_volume
                )

                track_rectangle = _pygame_rect(
                    track_spec["rect"]
                )

                fill_width = round(
                    track_rectangle.width * volume
                )

                if fill_width > 0:
                    fill_spec = {
                        **thumb_spec,
                        "rect": {
                            **thumb_spec["rect"],
                            "width": fill_width,
                        },
                    }

                    draw_figma_rectangle(
                        surface,
                        fill_spec,
                    )

            else:
                label_spec = menu_layout["back"]["label"]
                visible_label = label.title()

        else:
            layout_name = (
                "no"
                if action == "back"
                else "yes"
            )

            label_spec = menu_layout["entries"][
                layout_name
            ]["label"]

            visible_label = label.title()

        draw_figma_text(
            surface,
            label_spec,
            text_override=visible_label,
            color_override=selected_color,
        )


def _smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _menu_page_layout(menu_state, theme_layouts):
    page_name = (
        "confirm"
        if menu_state.page == "confirm_abandon"
        else menu_state.page
    )

    return theme_layouts[page_name]


def _draw_menu_theme(
    surface,
    menu_state,
    game_started,
    fullscreen,
    menu_assets,
    theme,
    highest_unlocked_theme,
    menu_layout,
    selector_selected_theme,
):
    _draw_menu_background(
        surface,
        menu_assets,
        theme,
    )

    asset_theme = {
        1: "act_one",
        2: "act_two",
        3: "act_three",
    }[theme]

    title_shade = menu_layout["shades"]["title"]

    if title_shade is not None:
        draw_figma_rectangle(
            surface,
            title_shade,
        )

    _blit_layout_image(
        surface,
        menu_assets[f"{asset_theme}_menu_frame"],
        menu_layout["art"]["menu_frame"],
    )

    content_shade = menu_layout["shades"]["content"]

    if content_shade is not None:
        draw_figma_rectangle(
            surface,
            content_shade,
        )

    title_spec = menu_layout["art"]["title"]

    if title_spec["kind"] == "text":
        draw_figma_text(
            surface,
            title_spec,
        )
    else:
        _blit_layout_image(
            surface,
            menu_assets[f"{asset_theme}_menu_title"],
            title_spec["rect"],
        )

    visible_themes = _visible_menu_themes(
        highest_unlocked_theme
    )

    if (
        not game_started
        and menu_state.page == "main"
        and visible_themes
    ):
        theme_selector_shade = menu_layout[
            "shades"
        ]["theme_selector"]

        if theme_selector_shade is not None:
            last_theme = visible_themes[-1]

            last_theme_rectangle = _pygame_rect(
                menu_layout["themes"][
                    str(last_theme)
                ]["rect"]
            )

            shade_top = round(
                theme_selector_shade["rect"]["y"]
            )

            visible_shade = {
                **theme_selector_shade,
                "rect": {
                    **theme_selector_shade["rect"],
                    "height": (
                        last_theme_rectangle.bottom
                        - shade_top
                    ),
                },
            }

            draw_figma_rectangle(
                surface,
                visible_shade,
            )

        _draw_theme_selector(
            surface,
            selector_selected_theme,
            highest_unlocked_theme,
            menu_layout,
        )

    if menu_state.page == "confirm_abandon":
        draw_figma_text(
            surface,
            menu_layout["copy"]["warning"],
            text_override="Abandon the descent?",
        )

        draw_figma_text(
            surface,
            menu_layout["copy"]["consequence"],
            text_override="All progress will be lost",
        )

    entries = _entries(
        menu_state,
        game_started,
        fullscreen,
    )

    _draw_entries(
        surface,
        entries,
        menu_state.selected_index,
        menu_state,
        menu_layout,
    )

def _draw_transition_fog(
    surface,
    progress,
    elapsed_ms,
):
    strength = math.sin(math.pi * progress)

    if strength <= 0:
        return

    veil = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )

    veil.fill(
        (
            7,
            8,
            11,
            round(135 * strength),
        )
    )

    surface.blit(veil, (0, 0))

    small_width = max(
        1,
        surface.get_width() // 4,
    )

    small_height = max(
        1,
        surface.get_height() // 4,
    )

    fog = pygame.Surface(
        (small_width, small_height),
        pygame.SRCALPHA,
    )

    movement = elapsed_ms * 0.00045

    for index in range(12):
        phase = movement + index * 0.83

        horizontal_position = (
            0.5
            + math.sin(phase) * 0.58
        )

        vertical_position = (
            0.5
            + math.cos(phase * 0.71) * 0.45
        )

        center_x = round(
            horizontal_position * small_width
        )

        center_y = round(
            vertical_position * small_height
        )

        radius = round(
            small_height
            * (
                0.18
                + 0.06 * (index % 4)
            )
        )

        alpha = round(
            strength
            * (
                25
                + 5 * (index % 3)
            )
        )

        pygame.draw.circle(
            fog,
            (94, 99, 108, alpha),
            (center_x, center_y),
            radius,
        )

    fog = pygame.transform.gaussian_blur(
        fog,
        10,
    )

    fog = pygame.transform.smoothscale(
        fog,
        surface.get_size(),
    )

    surface.blit(fog, (0, 0))


def draw_menu(
    surface,
    fonts,
    menu_state,
    elapsed_ms,
    game_started,
    fullscreen,
    menu_assets,
    visual_stage,
    highest_unlocked_theme=None,
    menu_layout=None,
    menu_layouts=None,
):
    if highest_unlocked_theme is None:
        highest_unlocked_theme = visual_stage

    transition_from = (
        menu_state.transition_from_theme
    )

    if (
        transition_from is None
        or game_started
        or menu_layouts is None
    ):
        _draw_menu_theme(
            surface,
            menu_state,
            game_started,
            fullscreen,
            menu_assets,
            visual_stage,
            highest_unlocked_theme,
            menu_layout,
            menu_state.menu_theme,
        )
        return

    transition_to = menu_state.menu_theme

    if transition_from == transition_to:
        menu_state.transition_from_theme = None

        target_layout = _menu_page_layout(
            menu_state,
            menu_layouts[transition_to],
        )

        _draw_menu_theme(
            surface,
            menu_state,
            game_started,
            fullscreen,
            menu_assets,
            transition_to,
            highest_unlocked_theme,
            target_layout,
            transition_to,
        )
        return

    now = pygame.time.get_ticks()

    raw_progress = (
        now - menu_state.transition_started_at
    ) / max(
        1,
        menu_state.transition_duration_ms,
    )

    progress = max(
        0.0,
        min(1.0, raw_progress),
    )

    if progress >= 1.0:
        menu_state.transition_from_theme = None

        target_layout = _menu_page_layout(
            menu_state,
            menu_layouts[transition_to],
        )

        _draw_menu_theme(
            surface,
            menu_state,
            game_started,
            fullscreen,
            menu_assets,
            transition_to,
            highest_unlocked_theme,
            target_layout,
            transition_to,
        )
        return

    old_layout = _menu_page_layout(
        menu_state,
        menu_layouts[transition_from],
    )

    new_layout = _menu_page_layout(
        menu_state,
        menu_layouts[transition_to],
    )

    old_layer = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )

    new_layer = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )

    _draw_menu_theme(
        old_layer,
        menu_state,
        game_started,
        fullscreen,
        menu_assets,
        transition_from,
        highest_unlocked_theme,
        old_layout,
        transition_from,
    )

    _draw_menu_theme(
        new_layer,
        menu_state,
        game_started,
        fullscreen,
        menu_assets,
        transition_to,
        highest_unlocked_theme,
        new_layout,
        transition_to,
    )

    old_fade = _smoothstep(
        min(1.0, progress / 0.58)
    )

    new_fade = _smoothstep(
        max(
            0.0,
            (progress - 0.42) / 0.58,
        )
    )

    old_alpha = round(
        255 * (1.0 - old_fade)
    )

    new_alpha = round(
        255 * new_fade
    )

    surface.fill(_BACKGROUND)

    old_layer.set_alpha(old_alpha)
    new_layer.set_alpha(new_alpha)

    surface.blit(old_layer, (0, 0))
    surface.blit(new_layer, (0, 0))

    _draw_transition_fog(
        surface,
        progress,
        elapsed_ms,
    )
