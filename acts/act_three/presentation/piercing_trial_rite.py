import pygame

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.piercing_trial_effects import center
from acts.act_three.presentation.trial_rite_shapes import ease, envelope, relief
from acts.act_three.presentation.ability_unlock_banner import draw_unlock_banner


def draw_completion(context, trial, now):
    elapsed = now - trial["completed"]
    if not 0 <= elapsed < 3400:
        return
    size = ACT_THREE_TILE_SIZE
    px, py = center(context, (context.floor.player_column, context.floor.player_row))
    strength = envelope(elapsed, 3400)
    assembly = ease(elapsed / 1100)
    dissolve = 1 - ease((elapsed - 2200) / 800)
    layer = pygame.Surface(context.view_surface.get_size(), pygame.SRCALPHA)
    layer.fill((5, 12, 8, round(65 * strength)))
    for index, target in enumerate(trial["targets"]):
        sx, sy = center(context, target["position"])
        t = ease((elapsed - index * 100) / 900)
        if 0 < t < 1:
            end = sx + (px - sx) * t, sy + (py - sy) * t
            pygame.draw.line(layer, (91, 118, 74, round(100 * strength * (1 - t))), (sx, sy), end, 2)
            pygame.draw.line(layer, (186, 202, 140, round(210 * strength * (1 - t))), (end[0] - 6, end[1] - 3), (end[0] + 6, end[1] + 3), 1)
    cx, cy = px, py - size * .55
    for side in (-1, 1):
        separation = side * size * .7 * (1 - assembly)
        points = [(cx + separation, cy - size * .95), (cx + side * size * .39 + separation, cy - size * .52),
                  (cx + side * size * .48 + separation, cy), (cx + side * size * .39 + separation, cy + size * .52), (cx + separation, cy + size * .95)]
        pygame.draw.lines(layer, (34, 46, 30, round(230 * strength * dissolve)), False, points, 7)
        pygame.draw.lines(layer, (145, 169, 105, round(210 * strength * dissolve)), False, points, 2)
        pygame.draw.line(layer, (182, 198, 136, round(150 * assembly * dissolve)), points[0], points[-1], 1)
    draw = ease((elapsed - 750) / 650)
    arrow_y = cy + size * .5 * (1 - draw) - size * 1.4 * ease((elapsed - 1650) / 400)
    if elapsed > 650:
        alpha = strength * (1 - ease((elapsed - 2200) / 500))
        pygame.draw.line(layer, (187, 203, 143, round(220 * alpha)), (cx, arrow_y + size * .7), (cx, arrow_y - size * .65), 2)
        relief(layer, [(cx, arrow_y - size * .9), (cx + size * .11, arrow_y - size * .59), (cx, arrow_y - size * .65), (cx - size * .11, arrow_y - size * .59)], (111, 137, 81), (219, 226, 177), alpha)
        for side in (-1, 1):
            pygame.draw.line(layer, (128, 151, 92, round(200 * alpha)), (cx, arrow_y + size * .6), (cx + side * size * .1, arrow_y + size * .47), 2)
    context.view_surface.blit(layer, (0, 0))
    draw_unlock_banner(context.view_surface, elapsed, "PIERCING SHOT", (208, 216, 174), (158, 171, 136), (10, 15, 12))
