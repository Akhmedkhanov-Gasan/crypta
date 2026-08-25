import pygame

from presentation.hud import wrap_text
from settings import GAME_HEIGHT, GAME_WIDTH


_TRADER_DIALOGUE_FADE_IN_MS = 250
_TRADER_DIALOGUE_FADE_OUT_MS = 400

_DIALOGUE_WIDTH = 760
_DIALOGUE_HEIGHT = 132

_DIALOGUE_RECT = pygame.Rect(
    (GAME_WIDTH - _DIALOGUE_WIDTH) // 2,
    GAME_HEIGHT - _DIALOGUE_HEIGHT - 28,
    _DIALOGUE_WIDTH,
    _DIALOGUE_HEIGHT,
)


def draw_trader_dialogue(
    screen,
    text,
    started_at,
    dismiss_started_at,
    current_time,
    fonts,
):
    if not text or started_at < 0:
        return

    elapsed = current_time - started_at
    fade_in = min(
        1.0,
        max(
            0.0,
            elapsed / _TRADER_DIALOGUE_FADE_IN_MS,
        ),
    )

    if dismiss_started_at >= started_at:
        dismiss_elapsed = (
            current_time - dismiss_started_at
        )
        fade_out = max(
            0.0,
            1.0
            - dismiss_elapsed
            / _TRADER_DIALOGUE_FADE_OUT_MS,
        )
    else:
        fade_out = 1.0

    alpha = round(
        255 * min(fade_in, fade_out)
    )

    if alpha <= 0:
        return

    panel = pygame.Surface(
        _DIALOGUE_RECT.size,
        pygame.SRCALPHA,
    )

    pygame.draw.rect(
        panel,
        (
            12,
            10,
            15,
            round(235 * alpha / 255),
        ),
        panel.get_rect(),
        border_radius=5,
    )
    pygame.draw.rect(
        panel,
        (151, 113, 62, alpha),
        panel.get_rect(),
        width=2,
        border_radius=5,
    )

    title_font = fonts["heading"]
    text_font = fonts["text"]

    title = title_font.render(
        "TRADER",
        True,
        (220, 174, 92),
    )
    title.set_alpha(alpha)

    panel.blit(
        title,
        (18, 10),
    )

    lines = wrap_text(
        text_font,
        text,
        _DIALOGUE_RECT.width - 36,
    )[:4]

    line_y = 39

    for line in lines:
        line_surface = text_font.render(
            line,
            True,
            (224, 218, 207),
        )
        line_surface.set_alpha(alpha)

        panel.blit(
            line_surface,
            (18, line_y),
        )
        line_y += text_font.get_linesize()

    screen.blit(
        panel,
        _DIALOGUE_RECT.topleft,
    )


__all__ = ["draw_trader_dialogue"]
