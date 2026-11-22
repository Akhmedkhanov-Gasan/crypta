import math

import pygame

from acts.act_three.presentation.view import _view_position
from acts.act_three.rune_master.definitions import has_ability_rune
from presentation.layout import ACT_THREE_TILE_SIZE


def _dagger(layer, center, selected):
    x, y = center
    steel = (165, 143, 139, 235) if selected else (119, 101, 108, 210)
    pygame.draw.lines(layer, (13, 5, 12, 225), False,
                      ((x, y - 12), (x, y + 12)), 5)
    pygame.draw.polygon(layer, (40, 13, 23, 245),
                        ((x - 3, y - 3), (x + 3, y - 3), (x + 2, y + 7), (x, y + 13), (x - 2, y + 7)))
    pygame.draw.line(layer, steel, (x - 1, y - 3), (x, y + 10), 1)
    pygame.draw.line(layer, (99, 28, 40, 240), (x + 1, y - 2), (x + 1, y + 7), 1)
    pygame.draw.line(layer, steel, (x - 5, y - 4), (x + 5, y - 4), 2)
    pygame.draw.line(layer, (75, 56, 63, 240), (x, y - 11), (x, y - 5), 2)


def _carnage_sigil(layer, center, selected):
    x, y = center
    for index in range(3):
        dx = (index - 1) * 5
        points = ((x + dx + 2, y - 7 + abs(index - 1) * 2),
                  (x + dx - 1, y + 1), (x + dx, y + 8))
        pygame.draw.lines(layer, (18, 5, 13, 235), False, points, 5)
        pygame.draw.lines(layer, (113, 33, 49, 235), False, points, 2)
        pygame.draw.line(layer, (161, 105, 107, 225) if selected else (115, 69, 82, 205),
                         points[0], points[1], 1)


def draw_rune_spree_targets(surface, player, floor, camera_x, camera_y, current_time):
    executioner = has_ability_rune(player, "rune_of_the_executioner")
    carnage = has_ability_rune(player, "rune_of_carnage")
    if not player.ultimate_aiming or not (executioner or carnage):
        return False
    counts = {name: player.ultimate_targets.count(name) for name in set(player.ultimate_targets)}
    tile = ACT_THREE_TILE_SIZE
    margin = 24
    for enemy in floor.enemies:
        focused = enemy.name == player.ultimate_preview_target
        count = counts.get(enemy.name, 0)
        if enemy.health <= 0 or (not focused and not count):
            continue
        width = tile * enemy.footprint_width
        height = tile * enemy.footprint_height
        layer = pygame.Surface((width + margin * 2, height + margin * 2), pygame.SRCALPHA)
        center_x = margin + width // 2
        feet_y = margin + round(height * 0.82)
        pulse = (math.sin(current_time / 430) + 1) / 2
        ring = pygame.Rect(margin + 5, feet_y - 9, max(1, width - 10), 18)
        pygame.draw.ellipse(layer, (17, 5, 15, 100), ring.inflate(6, 4))
        for index in range(3):
            angle = index * math.tau / 3 + 0.25
            pygame.draw.arc(layer, (70, 20, 35, round(135 + pulse * 35)), ring, angle, angle + 1.35, 3)
            pygame.draw.arc(layer, (136, 73, 86, 145), ring, angle + 0.12, angle + 0.85, 1)
        if focused:
            for side in (-1, 1):
                x = margin + width // 2 + side * (width // 2 - 5)
                y = margin + height // 2
                points = ((x + side * 7, y - 13), (x + side * 2, y - 5),
                          (x + side * 4, y + 5), (x + side * 7, y + 12))
                pygame.draw.lines(layer, (11, 5, 12, 220), False, points, 5)
                pygame.draw.lines(layer, (109, 46, 63, 215), False, points, 2)
                pygame.draw.line(layer, (166, 130, 133, 170), points[0], points[1], 1)
        center = center_x, margin - 8
        if executioner:
            _dagger(layer, center, True)
        else:
            _carnage_sigil(layer, center, count > 0)
        for index in range(count):
            x = center_x + (index - (count - 1) / 2) * 7
            pygame.draw.line(layer, (20, 8, 16, 240), (round(x), feet_y + 7), (round(x), feet_y + 13), 3)
            pygame.draw.line(layer, (171, 106, 105, 225), (round(x), feet_y + 8), (round(x), feet_y + 11), 1)
        for index in range(3):
            phase = (current_time / 1900 + index / 3) % 1
            x = center_x + math.sin(index * 2.4 + 0.5) * width * 0.35
            y = feet_y - phase * 13
            pygame.draw.circle(layer, (129, 66, 83, round(80 * math.sin(phase * math.pi))),
                               (round(x), round(y)), 1)
        position = _view_position(enemy.column, enemy.row, camera_x, camera_y)
        surface.blit(layer, (round(position[0]) - margin, round(position[1]) - margin))
    return True
