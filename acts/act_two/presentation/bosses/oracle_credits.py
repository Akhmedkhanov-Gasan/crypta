from functools import lru_cache

import pygame

from game.combat_log import add_log_message
from presentation.layout import (
    FONT_ROOT,
    PROJECT_ROOT,
)
from settings import (
    GAME_HEIGHT,
    GAME_WIDTH,
)


FADE_TO_BLACK_MS = 1800

FIRST_CARD_START_MS = 1900
FIRST_CARD_END_MS = 4300

SECOND_CARD_START_MS = 4800
SECOND_CARD_END_MS = 7200

SCROLL_START_MS = 8000
SCROLL_END_MS = 31000
SCROLL_SPEED = 0.065

FINAL_START_MS = 31500
BUTTON_START_MS = 36500

END_MUSIC_VOLUME = 0.70

RED = (152, 51, 51)
BONE = (205, 196, 180)
GOLD = (210, 179, 119)
DIM = (132, 126, 118)

RETURN_BUTTON = pygame.Rect(
    GAME_WIDTH // 2 - 170,
    GAME_HEIGHT - 105,
    340,
    52,
)

SCROLL_LINES = (
    ("CRYPTA", 54, RED, 92),
    ("CREATED BY", 24, DIM, 48),
    ("AKHMEDKHANOV GASAN", 38, GOLD, 110),
    ("GAME DESIGN", 25, BONE, 42),
    ("PROGRAMMING", 25, BONE, 42),
    ("STORY", 25, BONE, 42),
    ("ART DIRECTION", 25, BONE, 76),
    ("AKHMEDKHANOV GASAN", 31, GOLD, 126),
    ("SPECIAL THANKS", 27, RED, 58),
    ("To nobody, you all suck...", 28, BONE, 100),
)


def _smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _card_alpha(
    elapsed,
    start_time,
    end_time,
):
    if elapsed < start_time or elapsed >= end_time:
        return 0

    local_time = elapsed - start_time
    duration = end_time - start_time

    return round(
        255
        * min(
            _smooth(local_time / 500),
            _smooth(
                (duration - local_time) / 650
            ),
        )
    )


@lru_cache(maxsize=16)
def _font(size):
    return pygame.font.Font(
        str(FONT_ROOT / "Almendra-Bold.ttf"),
        size,
    )


def _text_surface(
    text,
    size,
    color,
    alpha=255,
    outline_size=2,
):
    font = _font(size)
    foreground = font.render(
        text,
        True,
        color,
    )
    outline = font.render(
        text,
        True,
        (5, 3, 4),
    )
    padding = outline_size * 2 + 4
    surface = pygame.Surface(
        (
            foreground.get_width() + padding * 2,
            foreground.get_height() + padding * 2,
        ),
        pygame.SRCALPHA,
    )
    rectangle = foreground.get_rect(
        center=(
            surface.get_width() // 2,
            surface.get_height() // 2,
        ),
    )

    for dx in range(
        -outline_size,
        outline_size + 1,
    ):
        for dy in range(
            -outline_size,
            outline_size + 1,
        ):
            if dx == 0 and dy == 0:
                continue

            surface.blit(
                outline,
                rectangle.move(dx, dy),
            )

    surface.blit(
        foreground,
        rectangle,
    )
    surface.set_alpha(alpha)
    return surface


def _draw_centered_text(
    screen,
    text,
    y,
    size,
    color,
    alpha=255,
):
    surface = _text_surface(
        text,
        size,
        color,
        alpha,
    )
    screen.blit(
        surface,
        surface.get_rect(
            center=(
                GAME_WIDTH // 2,
                round(y),
            ),
        ),
    )


def start_oracle_credits(
    game_state,
    scene,
    music_volume,
):
    if scene.credits_music_started:
        return

    scene.credits_music_started = True
    path = (
        PROJECT_ROOT
        / "assets/audio/sounds_act_2/end.mp3"
    )

    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()

        pygame.mixer.music.load(
            str(path)
        )
        pygame.mixer.music.set_volume(
            max(
                0.0,
                min(
                    1.0,
                    music_volume
                    * END_MUSIC_VOLUME,
                ),
            )
        )
        pygame.mixer.music.play(
            0,
            fade_ms=1800,
        )
    except (OSError, pygame.error) as error:
        add_log_message(
            game_state.combat_log,
            f"End music unavailable: {error}",
            category="system",
        )


def handle_oracle_credits_event(
    event,
    elapsed,
    mouse_position,
):
    if elapsed < BUTTON_START_MS:
        return None

    keyboard_confirmed = (
        event.type == pygame.KEYDOWN
        and event.key in (
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
        )
        and not getattr(
            event,
            "repeat",
            False,
        )
    )
    button_clicked = (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button == 1
        and mouse_position is not None
        and RETURN_BUTTON.collidepoint(
            mouse_position
        )
    )

    if keyboard_confirmed or button_clicked:
        return "menu"

    return None


def _draw_scroll(
    screen,
    elapsed,
):
    scroll_elapsed = max(
        0,
        elapsed - SCROLL_START_MS,
    )
    y = (
        GAME_HEIGHT
        + 80
        - scroll_elapsed * SCROLL_SPEED
    )

    for text, size, color, gap in SCROLL_LINES:
        if -80 <= y <= GAME_HEIGHT + 80:
            distance = abs(
                y - GAME_HEIGHT / 2
            )
            edge_visibility = max(
                0.0,
                min(
                    1.0,
                    (
                        GAME_HEIGHT * 0.62
                        - distance
                    )
                    / 90,
                ),
            )

            _draw_centered_text(
                screen,
                text,
                y,
                size,
                color,
                round(
                    255 * edge_visibility
                ),
            )

        y += gap


def _draw_final(
    screen,
    elapsed,
    mouse_position,
):
    progress = _smooth(
        (
            elapsed - FINAL_START_MS
        )
        / 900
    )
    alpha = round(
        255 * progress
    )

    _draw_centered_text(
        screen,
        "THANK YOU FOR PLAYING",
        238,
        34,
        BONE,
        alpha,
    )
    _draw_centered_text(
        screen,
        "CRYPTA",
        322,
        47,
        RED,
        alpha,
    )
    _draw_centered_text(
        screen,
        "THE DESCENT WILL CONTINUE...",
        397,
        27,
        DIM,
        alpha,
    )

    if elapsed < BUTTON_START_MS:
        return

    button_progress = _smooth(
        (
            elapsed - BUTTON_START_MS
        )
        / 700
    )
    hovered = (
        mouse_position is not None
        and RETURN_BUTTON.collidepoint(
            mouse_position
        )
    )
    button_alpha = round(
        255 * button_progress
    )
    button = pygame.Surface(
        RETURN_BUTTON.size,
        pygame.SRCALPHA,
    )

    pygame.draw.rect(
        button,
        (
            24,
            14,
            16,
            round(
                (
                    210
                    if hovered
                    else 165
                )
                * button_progress
            ),
        ),
        button.get_rect(),
    )
    pygame.draw.rect(
        button,
        (
            184,
            79,
            76,
            button_alpha,
        ),
        button.get_rect(),
        2,
    )

    if hovered:
        inner = button.get_rect().inflate(
            -8,
            -8,
        )
        pygame.draw.rect(
            button,
            (
                109,
                31,
                35,
                round(
                    75 * button_progress
                ),
            ),
            inner,
        )

    screen.blit(
        button,
        RETURN_BUTTON,
    )

    text = _text_surface(
        "RETURN TO MAIN MENU",
        24,
        (
            GOLD
            if hovered
            else BONE
        ),
        button_alpha,
    )
    screen.blit(
        text,
        text.get_rect(
            center=RETURN_BUTTON.center,
        ),
    )


def draw_oracle_credits(
    screen,
    elapsed,
    mouse_position,
):
    darkness = _smooth(
        elapsed / FADE_TO_BLACK_MS
    )
    overlay = pygame.Surface(
        (GAME_WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA,
    )
    overlay.fill(
        (
            0,
            0,
            0,
            round(255 * darkness),
        )
    )
    screen.blit(
        overlay,
        (0, 0),
    )

    if elapsed < FADE_TO_BLACK_MS:
        return

    first_alpha = _card_alpha(
        elapsed,
        FIRST_CARD_START_MS,
        FIRST_CARD_END_MS,
    )

    if first_alpha > 0:
        _draw_centered_text(
            screen,
            "THE ORACLE HAS FALLEN",
            GAME_HEIGHT // 2,
            45,
            RED,
            first_alpha,
        )

    second_alpha = _card_alpha(
        elapsed,
        SECOND_CARD_START_MS,
        SECOND_CARD_END_MS,
    )

    if second_alpha > 0:
        _draw_centered_text(
            screen,
            "BUT FATE REMAINS",
            GAME_HEIGHT // 2,
            39,
            BONE,
            second_alpha,
        )

    if SCROLL_START_MS <= elapsed < SCROLL_END_MS:
        _draw_scroll(
            screen,
            elapsed,
        )

    if elapsed >= FINAL_START_MS:
        _draw_final(
            screen,
            elapsed,
            mouse_position,
        )
