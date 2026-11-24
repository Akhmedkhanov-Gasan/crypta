import math

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE


def _glyph(surface, center, size, color, variant=0):
    x, y = center
    points = [(x, y - size), (x + size * 0.65, y), (x, y + size), (x - size * 0.65, y)]
    pygame.draw.lines(surface, color, True, points, 2)
    if variant % 2:
        pygame.draw.line(surface, color, (x, y - size * 1.5), (x, y + size * 1.5), 1)
    else:
        pygame.draw.lines(surface, color, False, [(x - size, y + size), (x, y), (x + size, y + size)], 1)


def draw_runebound_aura(surface, position, tile_size, now, seed, started_at):
    size = tile_size
    overlay = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    t = now / 1000
    pulse = 0.5 + 0.5 * math.sin(t * 3.2 + seed)
    center = size, size * 1.24
    pygame.draw.ellipse(overlay, (66, 20, 100, 60), (size * 0.54, size * 1.07, size * 0.92, size * 0.35))
    pygame.draw.ellipse(overlay, (143, 69, 190, 140), (size * 0.6, size * 1.12, size * 0.8, size * 0.23), 1)
    for index in range(4):
        angle = t * 1.15 + index * math.tau / 4 + seed
        x = center[0] + math.cos(angle) * size * 0.43
        y = center[1] - size * 0.48 + math.sin(angle) * size * 0.32
        alpha = round(120 + 90 * pulse)
        pygame.draw.circle(overlay, (105, 43, 160, 65), (round(x), round(y)), max(2, round(size * 0.1)))
        _glyph(overlay, (x, y), max(3, size * 0.055), (177, 100, 220, alpha), index)
    emergence = max(0, 1 - (now - started_at) / 800)
    if emergence:
        pygame.draw.ellipse(overlay, (183, 108, 227, round(170 * emergence)),
                         (size * 0.55, size * (1.2 - emergence * 0.75), size * 0.9, size * 0.2), 2)
    surface.blit(overlay, (round(position[0] - size * 0.5), round(position[1] - size * 0.5)))


def draw_rune_trial(context, now):
    trial = context.floor.rune_trial
    if trial is None or trial["phase"] == "idle":
        return
    visible = context.floor.visible_cells
    if not set(trial["altars"]) & visible and trial["door"] not in visible:
        return
    size = ACT_THREE_TILE_SIZE
    overlay = pygame.Surface(context.view_surface.get_size(), pygame.SRCALPHA)
    t = now / 1000
    active = trial["phase"] != "completed"
    strength = min(1, max(0, (now - trial["started_at"]) / 600)) if trial["phase"] == "opening" else 1
    if not active:
        strength = 0.25 + 0.75 * max(0, 1 - (now - trial["started_at"]) / 1200)
    if set(trial["altars"]) & context.floor.visible_cells:
        center_x = (sum(cell[0] for cell in trial["altars"]) / 2 + 0.5) * size - context.camera_x
        center_y = (sum(cell[1] for cell in trial["altars"]) / 2 + 0.65) * size - context.camera_y
        pulse = 0.8 + 0.2 * math.sin(t * 2.8)
        for radius in (1.15, 0.9, 0.65):
            rectangle = (center_x - size * radius, center_y - size * radius * 0.27,
                         size * radius * 2, size * radius * 0.54)
            pygame.draw.ellipse(overlay, (102, 35, 152, round(35 * strength * pulse)), rectangle)
            pygame.draw.ellipse(overlay, (155, 67, 202, round(145 * strength * pulse)), rectangle, 2)
        for index in range(10):
            angle = t * 0.65 + index * math.tau / 10
            _glyph(overlay, (center_x + math.cos(angle) * size * 0.98,
                             center_y + math.sin(angle) * size * 0.26), size * 0.055,
                   (185, 108, 225, round(185 * strength)), index)
        for index in range(24):
            progress = (t * 0.35 + index * 0.173) % 1
            x = center_x + math.sin(index * 9.3 + t * 0.4) * size * 0.9
            y = center_y - progress * size * 1.3
            pygame.draw.circle(overlay, (145, 65, 194, round(125 * (1 - progress) * strength)),
                               (round(x), round(y)), 1 if index % 3 else 2)
    door_alpha = 1 if active else max(0, 1 - (now - trial["started_at"]) / 650)
    if trial["door"] in context.floor.visible_cells and door_alpha:
        x = (trial["door"][0] + 0.5) * size - context.camera_x
        y = trial["door"][1] * size - context.camera_y
        rectangle = (x - size * 0.28, y - size * 0.65, size * 0.56, size * 1.65)
        pygame.draw.rect(overlay, (55, 12, 90, round(170 * door_alpha)), rectangle, border_radius=7)
        pygame.draw.rect(overlay, (154, 70, 211, round(220 * door_alpha)), rectangle, 2, border_radius=7)
        for index in range(5):
            _glyph(overlay, (x + math.sin(t * 2 + index) * size * 0.06,
                             y - size * 0.45 + index * size * 0.29), size * 0.085,
                   (183, 111, 230, round(210 * door_alpha)), index)
        for index in range(8):
            progress = (t * 0.7 + index / 8) % 1
            pygame.draw.line(overlay, (126, 48, 190, round(95 * door_alpha)),
                             (x - size * 0.24, y + size * (1 - progress * 1.6)),
                             (x + size * 0.24, y + size * (0.85 - progress * 1.6)), 1)
    context.view_surface.blit(overlay, (0, 0))
