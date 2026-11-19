import pygame

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.piercing_trial_effects import center
from acts.act_three.presentation.trial_rite_shapes import ease, envelope, relief
from acts.act_three.presentation.ability_unlock_banner import draw_unlock_banner


def draw_completion(context, trial, now):
    elapsed = now - trial["completed"]
    if not 0 <= elapsed < 4200:
        return
    size = ACT_THREE_TILE_SIZE
    px, py = center(context, trial["completion_origin"])
    strength = envelope(elapsed, 4200)
    form = ease((elapsed - 300) / 1100)
    fade = 1 - ease((elapsed - 2700) / 1100)
    layer = pygame.Surface(context.view_surface.get_size(), pygame.SRCALPHA)
    layer.fill((17, 14, 7, round(65 * strength)))
    for index, cell in enumerate(trial["cells"]):
        reveal = ease((elapsed - index * 30) / 650)
        if 0 < reveal < 1:
            x, y = center(context, cell)
            points = [(x - size * .35, y), (x, y - size * .19), (x + size * .35, y), (x, y + size * .19)]
            pygame.draw.lines(layer, (205, 175, 96, round(150 * (1 - reveal))), True, points, 2)
    cy = py - size * .42
    for side in (-1, 1):
        half = [(0, -.95), (side * .58, -.67), (side * .48, .22), (side * .27, .58), (0, .86)]
        shift = side * size * .8 * (1 - form)
        points = [(px + x * size + shift, cy + y * size) for x, y in half]
        relief(layer, points, (45, 39, 23), (209, 181, 110), strength * fade * .8, 3)
    if form > 0:
        alpha = round(235 * form * fade * strength)
        pygame.draw.line(layer, (237, 215, 157, alpha), (px, cy - size * .5), (px, cy + size * .46), 3)
        pygame.draw.line(layer, (237, 215, 157, alpha), (px - size * .27, cy - size * .12), (px + size * .27, cy - size * .12), 3)
        for side in (-1, 1):
            x = px + side * size * (.9 + (1 - form) * .4)
            points = [(x, cy + size * .6), (x + side * size * .1, cy - size * .6), (x + side * size * .22, cy - size * .78), (x + side * size * .15, cy + size * .7)]
            relief(layer, points, (76, 62, 31), (181, 152, 85), strength * fade * .22)
    context.view_surface.blit(layer, (0, 0))
    draw_unlock_banner(context.view_surface, elapsed - 700, "SHIELD CHARGE", (237, 220, 164), (193, 165, 103), (23, 21, 14))
