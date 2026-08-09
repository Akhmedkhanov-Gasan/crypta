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


def _settings_entries(fullscreen):
    fullscreen_label = "ON" if fullscreen else "OFF"
    return (
        ("toggle_fullscreen", f"FULLSCREEN  {fullscreen_label}"),
        ("back", "BACK"),
    )


def _entries(menu_state, game_started, fullscreen):
    if menu_state.page == "settings":
        return _settings_entries(fullscreen)
    if menu_state.page == "confirm_abandon":
        return (
            ("back", "NO"),
            ("abandon_run", "YES"),
        )
    return _main_entries(game_started)


def get_menu_rectangles(entry_count):
    width = 286
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
):
    entries = _entries(menu_state, game_started, fullscreen)
    rectangles = get_menu_rectangles(len(entries))

    if event.type == pygame.MOUSEMOTION and mouse_position is not None:
        for index, rectangle in enumerate(rectangles):
            if rectangle.collidepoint(mouse_position):
                menu_state.selected_index = index
                break

    if (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button == 1
        and mouse_position is not None
    ):
        for index, rectangle in enumerate(rectangles):
            if rectangle.collidepoint(mouse_position):
                menu_state.selected_index = index
                return _activate_entry(menu_state, entries[index][0])

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


def _draw_title(surface, fonts):
    title = fonts["title"].render("CRYPTA", True, _TEXT)
    title = pygame.transform.smoothscale_by(title, 1.7)
    surface.blit(
        title,
        title.get_rect(center=(GAME_WIDTH // 2, 245)),
    )


def _draw_entries(surface, font, entries, selected_index):
    rectangles = get_menu_rectangles(len(entries))

    for index, ((_, label), rectangle) in enumerate(
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
):
    _draw_menu_background(surface, menu_assets, visual_stage)
    _draw_title(surface, fonts)

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
    )
