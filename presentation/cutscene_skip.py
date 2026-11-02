import pygame


def draw_skip_hint(screen, progress, font):
    label = font.render("Hold SPACE to skip all", True, (218, 213, 201))
    width = max(254, label.get_width() + 28)
    height = max(44, label.get_height() + 22)
    panel = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (5, 6, 9, 210), panel.get_rect(), border_radius=4)
    panel.blit(label, label.get_rect(midtop=(width // 2, 6)))
    pygame.draw.rect(panel, (60, 59, 61), (12, height - 10, width - 24, 3))
    pygame.draw.rect(panel, (178, 164, 137), (12, height - 10, round((width - 24) * max(0.0, min(1.0, progress))), 3))
    screen.blit(panel, panel.get_rect(topright=(screen.get_width() - 20, 12)))
