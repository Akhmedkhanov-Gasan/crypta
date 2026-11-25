import pygame


def draw_selection_highlight(screen, rectangle, *, radius=3):
    if rectangle.width <= 0 or rectangle.height <= 0:
        return
    highlight = pygame.Surface(rectangle.size, pygame.SRCALPHA)
    pygame.draw.rect(
        highlight, (140, 140, 140, 24), highlight.get_rect(),
        border_radius=radius,
    )
    pygame.draw.rect(
        highlight, (115, 115, 115, 110), highlight.get_rect(),
        width=1, border_radius=radius,
    )
    screen.blit(highlight, rectangle)
