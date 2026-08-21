import pygame

from acts.act_two.rune_catalog import runes_for_class
from presentation.hud import fit_text_to_width, wrap_text
from settings import GAME_HEIGHT, GAME_WIDTH


_WINDOW_RECT = pygame.Rect(240, 153, 756, 426)
_CARD_RECTS = (
    pygame.Rect(311, 247, 194, 240),
    pygame.Rect(514, 247, 194, 240),
    pygame.Rect(717, 247, 194, 240),
)
_CONFIRM_RECT = pygame.Rect(545, 491, 132, 44)
_CONFIRM_HIT_RECT = _CONFIRM_RECT.inflate(-16, -8)


def get_rune_selection_card_rectangles(player_class):
    return {
        rune.id: rectangle.copy()
        for rune, rectangle in zip(
            runes_for_class(player_class),
            _CARD_RECTS,
        )
    }


def get_rune_selection_confirm_rectangle():
    return _CONFIRM_HIT_RECT.copy()


def draw_rune_selection(
    screen,
    game_state,
    fonts,
    sprites,
    mouse_position,
):
    veil = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
    veil.fill((4, 3, 5, 205))
    screen.blit(veil, (0, 0))
    screen.blit(sprites["act_two_rune_window"], _WINDOW_RECT)

    title_color = (229, 205, 154)
    body_color = (205, 197, 184)
    muted_color = (149, 136, 128)
    accent_color = (168, 45, 43)
    selected_color = (225, 174, 77)

    title = fonts["heading"].render(
        "CHOOSE ONE RUNE",
        True,
        title_color,
    )
    screen.blit(title, title.get_rect(center=(GAME_WIDTH // 2, 197)))

    class_name = (game_state.player.player_class or "unbound").upper()
    subtitle = fonts["ability_text"].render(
        f"{class_name}  -  ONE BLESSING FOR THIS RUN",
        True,
        muted_color,
    )
    screen.blit(
        subtitle,
        subtitle.get_rect(center=(GAME_WIDTH // 2, 228)),
    )

    pending_id = game_state.rune_selection_pending_id
    available_runes = runes_for_class(game_state.player.player_class)
    for rune_index, (rune, card_rect) in enumerate(
        zip(available_runes, _CARD_RECTS),
        start=1,
    ):
        hovered = (
            mouse_position is not None
            and card_rect.collidepoint(mouse_position)
        )
        selected = pending_id == rune.id

        card = pygame.Surface(card_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            card,
            (30, 20, 23, 118 if hovered or selected else 56),
            card.get_rect(),
            border_radius=6,
        )
        pygame.draw.rect(
            card,
            (
                selected_color
                if selected
                else accent_color
                if hovered
                else (83, 68, 65)
            ),
            card.get_rect(),
            3 if selected else 1,
            border_radius=6,
        )
        screen.blit(card, card_rect)

        rune_image = sprites[f"{rune.id}_original"]
        image_rect = rune_image.get_rect(
            midtop=(card_rect.centerx, card_rect.y + 21)
        )
        screen.blit(rune_image, image_rect)

        number_surface = fonts["ability_text"].render(
            str(rune_index),
            True,
            selected_color if selected else muted_color,
        )
        screen.blit(
            number_surface,
            number_surface.get_rect(
                topright=(card_rect.right - 10, card_rect.top + 8)
            ),
        )

        name_surface = fonts["ability_text"].render(
            rune.name,
            True,
            selected_color if selected else title_color,
        )
        if name_surface.get_width() > card_rect.width - 20:
            name_text = fit_text_to_width(
                fonts["ability_text"],
                rune.name,
                card_rect.width - 20,
            )
            name_surface = fonts["ability_text"].render(
                name_text,
                True,
                selected_color if selected else title_color,
            )
        screen.blit(
            name_surface,
            name_surface.get_rect(
                center=(card_rect.centerx, card_rect.y + 181)
            ),
        )

        description_rect = pygame.Rect(
            card_rect.x + 20,
            card_rect.y + 198,
            card_rect.width - 40,
            40,
        )
        description_lines = wrap_text(
            fonts["ability_text"],
            rune.description,
            description_rect.width,
        )[:3]
        description_y = description_rect.y
        for line in description_lines:
            line_surface = fonts["ability_text"].render(
                line,
                True,
                body_color,
            )
            screen.blit(
                line_surface,
                line_surface.get_rect(
                    midtop=(description_rect.centerx, description_y)
                ),
            )
            description_y += 14

    if pending_id is not None:
        confirm_button = sprites["act_two_rune_confirm_button"]
        screen.blit(confirm_button, _CONFIRM_RECT)
        if (
            mouse_position is not None
            and _CONFIRM_HIT_RECT.collidepoint(mouse_position)
        ):
            highlight = confirm_button.copy()
            highlight.fill(
                (38, 20, 7, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            screen.blit(highlight, _CONFIRM_RECT)

    hint = fonts["ability_text"].render(
        "CLICK A RUNE, THEN CONFIRM  -  ESC / RMB TO RETURN",
        True,
        muted_color,
    )
    screen.blit(hint, hint.get_rect(center=(GAME_WIDTH // 2, 556)))


__all__ = [
    "draw_rune_selection",
    "get_rune_selection_card_rectangles",
    "get_rune_selection_confirm_rectangle",
]
