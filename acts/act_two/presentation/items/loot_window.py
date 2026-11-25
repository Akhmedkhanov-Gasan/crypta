import pygame

from presentation.text import fit_text_to_width
from presentation.tooltips.highlights import draw_selection_highlight


def draw_loot_window(screen, items, selected, panel, close_button, rows, sprites, fonts):
    shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 150))
    screen.blit(shade, (0, 0))

    shadow = pygame.Surface(panel.inflate(12, 12).size, pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 150), shadow.get_rect(), border_radius=5)
    screen.blit(shadow, (panel.x - 3, panel.y + 3))
    pygame.draw.rect(screen, (15, 15, 15), panel, border_radius=3)
    pygame.draw.rect(screen, (72, 72, 72), panel, width=1, border_radius=3)
    pygame.draw.line(screen, (103, 103, 103), (panel.left + 4, panel.top + 1), (panel.right - 5, panel.top + 1))
    pygame.draw.line(screen, (48, 48, 48), (panel.left + 16, panel.top + 46), (panel.right - 16, panel.top + 46))

    title_font = fonts["heading"]
    title = fit_text_to_width(title_font, f"Items on the ground ({len(items)})", panel.width - 82)
    screen.blit(title_font.render(title, True, (207, 207, 207)), (panel.left + 16, panel.top + 17))
    pygame.draw.rect(screen, (27, 27, 27), close_button, border_radius=2)
    pygame.draw.rect(screen, (65, 65, 65), close_button, width=1, border_radius=2)
    cross = close_button.inflate(-18, -18)
    pygame.draw.line(screen, (170, 170, 170), cross.topleft, cross.bottomright)
    pygame.draw.line(screen, (170, 170, 170), cross.topright, cross.bottomleft)

    text_font = fonts["text"]
    for index, rectangle in rows:
        selected_row = index == selected
        pygame.draw.rect(screen, (24, 24, 24) if selected_row else (19, 19, 19), rectangle, border_radius=2)
        if selected_row:
            draw_selection_highlight(screen, rectangle, radius=2)
            pygame.draw.line(
                screen, (150, 150, 150),
                (rectangle.left + 1, rectangle.top + 7),
                (rectangle.left + 1, rectangle.bottom - 8), width=2,
            )

        icon_box = pygame.Rect(rectangle.left + 6, rectangle.centery - 14, 28, 28)
        pygame.draw.rect(screen, (12, 12, 12), icon_box, border_radius=2)
        sprite = sprites.get(items[index].sprite_name)
        if sprite is not None:
            fitted = sprite.get_rect().fit(icon_box.inflate(-2, -2))
            image = sprite if sprite.get_size() == fitted.size else pygame.transform.smoothscale(sprite, fitted.size)
            screen.blit(image, fitted)
        name = fit_text_to_width(text_font, items[index].name, rectangle.width - 56)
        label = text_font.render(name, True, (213, 213, 213) if selected_row else (166, 166, 166))
        screen.blit(label, (rectangle.left + 44, rectangle.centery - label.get_height() // 2))

    if len(items) > len(rows):
        track = pygame.Rect(panel.right - 10, rows[0][1].top, 3, rows[-1][1].bottom - rows[0][1].top)
        pygame.draw.rect(screen, (33, 33, 33), track)
        thumb_height = max(8, round(track.height * len(rows) / len(items)))
        travel = track.height - thumb_height
        thumb = pygame.Rect(track.x, track.y + round(travel * selected / max(1, len(items) - 1)), track.width, thumb_height)
        pygame.draw.rect(screen, (99, 99, 99), thumb)

    pygame.draw.line(screen, (43, 43, 43), (panel.left + 16, panel.bottom - 57), (panel.right - 16, panel.bottom - 57))
    controls_font = fonts["log"]
    for text, y, color in (
        ("W/S / arrows: select   Space / click: take", panel.bottom - 48, (175, 175, 175)),
        (f"{selected + 1}/{len(items)}   Wheel: select   G / Esc: close", panel.bottom - 27, (123, 123, 123)),
    ):
        text = fit_text_to_width(controls_font, text, panel.width - 32)
        screen.blit(controls_font.render(text, True, color), (panel.left + 16, y))
