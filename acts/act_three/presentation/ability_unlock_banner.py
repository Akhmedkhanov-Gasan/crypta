from functools import lru_cache

import pygame


@lru_cache(maxsize=8)
def banner_text(name, title_color, subtitle_color):
    title = pygame.font.SysFont("georgia", 26).render(name, True, title_color)
    subtitle = pygame.font.SysFont("consolas", 15).render("ABILITY UNLOCKED  [Q]", True, subtitle_color)
    return title, subtitle


def draw_unlock_banner(surface, elapsed, name, title_color, subtitle_color, background):
    if not 0 <= elapsed < 3400:
        return
    opacity = min(1, elapsed / 320, (3400 - elapsed) / 700)
    title, subtitle = banner_text(name, title_color, subtitle_color)
    banner = pygame.Surface((min(surface.get_width(), 380), 76), pygame.SRCALPHA)
    banner.fill((*background, round(205 * opacity)))
    for image, y in ((title, 12), (subtitle, 46)):
        image.set_alpha(round(255 * opacity))
        banner.blit(image, image.get_rect(midtop=(banner.get_width() // 2, y)))
    surface.blit(banner, ((surface.get_width() - banner.get_width()) // 2, 24))
