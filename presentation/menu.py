from dataclasses import dataclass

import pygame

from settings import GAME_HEIGHT, GAME_WIDTH


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
        menu_layout["sliders"][slider_name]["track"]
    )


def get_menu_theme_rectangles(menu_layout):
    return tuple(
        _pygame_rect(
            menu_layout["themes"][str(theme)]["rect"]
        )
        for theme in range(1, 4)
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
                get_menu_theme_rectangles(menu_layout),
                start=1,
            ):
                if rectangle.collidepoint(mouse_position):
                    if theme <= highest_unlocked_theme:
                        menu_state.menu_theme = theme
                        return "menu_theme_changed"
                    return None
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
    font,
    selected_theme,
    highest_unlocked_theme,
    menu_layout=None,
):
    numerals = ("I", "II", "III")
    for theme, (numeral, rectangle) in enumerate(
        zip(
            numerals,
            get_menu_theme_rectangles(menu_layout),
        ),
        start=1,
    ):
        unlocked = theme <= highest_unlocked_theme
        selected = theme == selected_theme
        border_color = _INTERACTIVE if selected else _TEXT_DIM
        text_color = _TEXT if unlocked else (42, 39, 42)
        pygame.draw.rect(surface, _STONE_DARK, rectangle)
        pygame.draw.rect(
            surface,
            border_color,
            rectangle,
            width=2 if selected else 1,
            border_radius=11,
        )
        numeral_surface = font.render(numeral, True, text_color)
        surface.blit(
            numeral_surface,
            numeral_surface.get_rect(center=rectangle.center),
        )


def _draw_entries(
    surface,
    font,
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
        color = _TEXT if selected else (135, 128, 121)

        if menu_state.page == "main":
            layout_name = _layout_entry_name(action)
            label_rectangle = _pygame_rect(
                menu_layout["entries"][layout_name]["label"]
            )
            visible_label = label.title()

        elif menu_state.page == "settings":
            if action == "toggle_fullscreen":
                label_rectangle = _pygame_rect(
                    menu_layout["fullscreen"]["label"]
                )
                visible_label = "Fullscreen"

                value_rectangle = _pygame_rect(
                    menu_layout["fullscreen"]["value"]
                )
                enabled = label.strip().endswith("ON")

                pygame.draw.ellipse(
                    surface,
                    _INTERACTIVE if enabled else _TEXT_DIM,
                    value_rectangle,
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
                slider_layout = menu_layout["sliders"][
                    slider_name
                ]

                label_rectangle = _pygame_rect(
                    slider_layout["label"]
                )
                visible_label = label.title()

                track = _pygame_rect(
                    slider_layout["track"]
                )
                thumb = _pygame_rect(
                    slider_layout["thumb"]
                )

                pygame.draw.rect(
                    surface,
                    (72, 68, 67),
                    track,
                    border_radius=track.height // 2,
                )

                volume = (
                    menu_state.music_volume
                    if action == "music_volume"
                    else menu_state.effects_volume
                )
                fill_width = round(track.width * volume)

                if fill_width > 0:
                    pygame.draw.rect(
                        surface,
                        _INTERACTIVE,
                        (
                            thumb.x,
                            thumb.y,
                            fill_width,
                            thumb.height,
                        ),
                        border_radius=thumb.height // 2,
                    )

            else:
                label_rectangle = _pygame_rect(
                    menu_layout["back"]["label"]
                )
                visible_label = label.title()

        else:
            layout_name = (
                "no"
                if action == "back"
                else "yes"
            )
            label_rectangle = _pygame_rect(
                menu_layout["entries"][layout_name]["label"]
            )
            visible_label = label.title()

        label_surface = font.render(
            visible_label,
            True,
            color,
        )
        surface.blit(
            label_surface,
            label_surface.get_rect(
                center=label_rectangle.center,
            ),
        )


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
):
    _draw_menu_background(
        surface,
        menu_assets,
        visual_stage,
    )

    asset_theme = {
        1: "act_one",
        2: "act_two",
        3: "act_three",
    }[visual_stage]

    if menu_layout is not None:
        _draw_layout_shade(
            surface,
            menu_layout["shades"]["title"],
            alpha=_TITLE_SHADE_ALPHA,
        )

        _blit_layout_image(
            surface,
            menu_assets[f"{asset_theme}_menu_frame"],
            menu_layout["art"]["menu_frame"],
        )

        if menu_state.page == "main":
            shade_name = "menu_bar"
        elif menu_state.page == "settings":
            shade_name = "settings"
        else:
            shade_name = "confirm"

        _draw_layout_shade(
            surface,
            menu_layout["shades"][shade_name],
            alpha=_CONTENT_SHADE_ALPHA,
            border_radius=8,
        )

        _blit_layout_image(
            surface,
            menu_assets[f"{asset_theme}_menu_title"],
            menu_layout["art"]["title"],
        )

        if (
                not game_started
                and menu_state.page == "main"
        ):
            _draw_layout_shade(
                surface,
                menu_layout["shades"]["theme_selector"],
                alpha=_THEME_SHADE_ALPHA,
                border_radius=10,
            )

    if highest_unlocked_theme is None:
        highest_unlocked_theme = visual_stage
    if not game_started and menu_state.page == "main":
        _draw_theme_selector(
            surface,
            fonts["status"],
            menu_state.menu_theme,
            highest_unlocked_theme,
            menu_layout,
        )

    if menu_state.page == "confirm_abandon":
        warning_rectangle = _pygame_rect(
            menu_layout["copy"]["warning"]
        )
        consequence_rectangle = _pygame_rect(
            menu_layout["copy"]["consequence"]
        )

        warning = _render_text_fitted(
            fonts["heading"],
            "Abandon the descent?",
            _TEXT,
            warning_rectangle,
        )
        surface.blit(
            warning,
            warning.get_rect(
                center=warning_rectangle.center,
            ),
        )

        consequence = _render_text_fitted(
            fonts["text"],
            "All progress will be lost",
            _ACCENT,
            consequence_rectangle,
        )
        surface.blit(
            consequence,
            consequence.get_rect(
                center=consequence_rectangle.center,
            ),
        )

    entries = _entries(menu_state, game_started, fullscreen)
    _draw_entries(
        surface,
        fonts["status"],
        entries,
        menu_state.selected_index,
        menu_state,
        menu_layout,
    )
