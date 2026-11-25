import pygame


def draw_slot_highlight(screen, rectangle, *, scale=1.0, focused=False):
    if rectangle.width <= 0 or rectangle.height <= 0:
        return
    stroke = max(1, round(scale))
    inset = max(1, round(2 * scale))
    target = rectangle.inflate(-inset * 2, -inset * 2)
    if target.width <= 0 or target.height <= 0:
        return
    layer = pygame.Surface(target.size, pygame.SRCALPHA)
    bounds = layer.get_rect()
    radius = min(max(1, round(3 * scale)), min(bounds.size) // 2)
    pygame.draw.rect(layer, (180, 180, 180, 22 if focused else 12), bounds, border_radius=radius)
    pygame.draw.rect(layer, (123, 123, 123, 140 if focused else 85), bounds, width=stroke, border_radius=radius)
    length = min(max(2, round(7 * scale)), target.width // 3, target.height // 3)
    edge = (211, 211, 211, 235) if focused else (168, 168, 168, 180)
    for x, y, dx, dy in (
        (0, 0, 1, 1),
        (bounds.width - 1, 0, -1, 1),
        (0, bounds.height - 1, 1, -1),
        (bounds.width - 1, bounds.height - 1, -1, -1),
    ):
        pygame.draw.line(layer, edge, (x, y), (x + dx * length, y), stroke)
        pygame.draw.line(layer, edge, (x, y), (x, y + dy * length), stroke)
    screen.blit(layer, target)
