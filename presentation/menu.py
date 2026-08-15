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


def get_menu_rectangles(entry_count, width=286):
    height = 48
    gap = 13
    first_y = 354

    return tuple(
        pygame.Rect(
            (GAME_WIDTH - width) // 2,
            first_y + index * (height + gap),
            width,
            height,
        )
        for index in range(entry_count)
    )


def _rectangles_for_page(menu_state, entry_count):
    width = 420 if menu_state.page == "settings" else 286
    return get_menu_rectangles(entry_count, width)


def _slider_rectangle(entry_rectangle):
    return pygame.Rect(
        entry_rectangle.x + 214,
        entry_rectangle.centery - 5,
        174,
        10,
    )


def get_menu_theme_rectangles():
    return tuple(
        pygame.Rect(GAME_WIDTH - 102, 334 + index * 62, 48, 48)
        for index in range(3)
    )


def _set_slider_from_mouse(menu_state, action, rectangle, mouse_x):
    slider = _slider_rectangle(rectangle)
    volume = max(0.0, min(1.0, (mouse_x - slider.x) / slider.width))
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
):
    entries = _entries(menu_state, game_started, fullscreen)
    rectangles = _rectangles_for_page(menu_state, len(entries))

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
                    rectangles[index],
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
                get_menu_theme_rectangles(),
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
                        rectangle,
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
):
    label = font.render("VEIL", True, _TEXT_DIM)
    surface.blit(
        label,
        label.get_rect(center=(GAME_WIDTH - 78, 306)),
    )
    numerals = ("I", "II", "III")
    for theme, (numeral, rectangle) in enumerate(
        zip(numerals, get_menu_theme_rectangles()),
        start=1,
    ):
        unlocked = theme <= highest_unlocked_theme
        selected = theme == selected_theme
        border_color = _ACCENT if selected else _TEXT_DIM
        text_color = _TEXT if unlocked else (42, 39, 42)
        pygame.draw.rect(surface, _STONE_DARK, rectangle)
        pygame.draw.rect(
            surface,
            border_color,
            rectangle,
            width=2 if selected else 1,
        )
        numeral_surface = font.render(numeral, True, text_color)
        surface.blit(
            numeral_surface,
            numeral_surface.get_rect(center=rectangle.center),
        )


def _draw_title(surface, fonts):
    title = fonts["title"].render("CRYPTA", True, _TEXT)
    title = pygame.transform.smoothscale_by(title, 1.7)
    surface.blit(
        title,
        title.get_rect(center=(GAME_WIDTH // 2, 245)),
    )


def _draw_entries(surface, font, entries, selected_index, menu_state):
    rectangles = _rectangles_for_page(menu_state, len(entries))

    for index, ((action, label), rectangle) in enumerate(
        zip(entries, rectangles)
    ):
        selected = index == selected_index
        if selected:
            pygame.draw.rect(surface, (16, 14, 19), rectangle)
            pygame.draw.rect(surface, _ACCENT, rectangle, width=2)
            pygame.draw.rect(
                surface,
                _ACCENT,
                (rectangle.x - 10, rectangle.centery - 3, 6, 6),
            )
            color = _TEXT
        else:
            pygame.draw.rect(surface, _STONE_DARK, rectangle, width=1)
            color = _TEXT_DIM

        if action in ("music_volume", "effects_volume"):
            label_surface = font.render(label, True, color)
            surface.blit(
                label_surface,
                label_surface.get_rect(
                    midleft=(rectangle.x + 16, rectangle.centery)
                ),
            )
            slider = _slider_rectangle(rectangle)
            pygame.draw.rect(surface, (36, 32, 38), slider)
            volume = (
                menu_state.music_volume
                if action == "music_volume"
                else menu_state.effects_volume
            )
            fill_width = round(slider.width * volume)
            if fill_width > 0:
                pygame.draw.rect(
                    surface,
                    _ACCENT,
                    (slider.x, slider.y, fill_width, slider.height),
                )
            pygame.draw.circle(
                surface,
                _TEXT,
                (slider.x + fill_width, slider.centery),
                6,
            )
        else:
            label_surface = font.render(label, True, color)
            surface.blit(
                label_surface,
                label_surface.get_rect(center=rectangle.center),
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
):
    _draw_menu_background(surface, menu_assets, visual_stage)
    _draw_title(surface, fonts)

    if highest_unlocked_theme is None:
        highest_unlocked_theme = visual_stage
    if not game_started and menu_state.page == "main":
        _draw_theme_selector(
            surface,
            fonts["status"],
            menu_state.menu_theme,
            highest_unlocked_theme,
        )

    if menu_state.page == "confirm_abandon":
        warning = fonts["heading"].render(
            "ABANDON THE DESCENT?",
            True,
            _TEXT,
        )
        surface.blit(
            warning,
            warning.get_rect(center=(GAME_WIDTH // 2, 300)),
        )
        consequence = fonts["text"].render(
            "ALL PROGRESS WILL BE LOST",
            True,
            _ACCENT,
        )
        surface.blit(
            consequence,
            consequence.get_rect(center=(GAME_WIDTH // 2, 327)),
        )

    entries = _entries(menu_state, game_started, fullscreen)
    _draw_entries(
        surface,
        fonts["status"],
        entries,
        menu_state.selected_index,
        menu_state,
    )
