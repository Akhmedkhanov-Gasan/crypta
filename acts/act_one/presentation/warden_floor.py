import math

import pygame

from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import GAME_WIDTH, TILE_SIZE


def draw_archer_attack_markers(screen, enemy, current_time):
    pulse = (math.sin(current_time / 180) + 1) / 2
    border_color = (
        83,
        round(157 + pulse * 45),
        112,
    )

    marker = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    rectangle = marker.get_rect().inflate(-4, -4)

    pygame.draw.rect(marker, (31, 91, 53, 125), rectangle)
    pygame.draw.rect(marker, border_color, rectangle, width=2)

    center = TILE_SIZE // 2

    pygame.draw.line(
        marker,
        (170, 228, 154),
        (center - 4, center),
        (center + 4, center),
    )
    pygame.draw.line(
        marker,
        (170, 228, 154),
        (center, center - 4),
        (center, center + 4),
    )

    for column, row in enemy["attack_targets"]:
        screen.blit(
            marker,
            (
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
            ),
        )


def _draw_brazier(screen, column, row, current_time):
    x = MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2
    y = MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2

    phase = current_time / 120 + row * 1.7
    sway = round(math.sin(phase) * 2)
    height = 20 + round(math.sin(phase * 1.4) * 3)

    glow = pygame.Surface((72, 72), pygame.SRCALPHA)
    for radius, alpha in ((32, 10), (24, 15), (16, 23)):
        pygame.draw.circle(
            glow,
            (232, 110, 35, alpha),
            (36, 36),
            radius,
        )
    screen.blit(glow, (x - 36, y - 40))

    pygame.draw.rect(screen, (18, 18, 23), (x - 5, y + 3, 10, 11))
    pygame.draw.rect(screen, (70, 66, 66), (x - 3, y + 3, 6, 9))
    pygame.draw.rect(screen, (35, 34, 40), (x - 9, y + 12, 18, 4))

    pygame.draw.polygon(
        screen,
        (178, 60, 24),
        (
            (x - 7, y + 1),
            (x - 8, y - 7),
            (x - 3, y - 12),
            (x + sway, y - height),
            (x + 4, y - 11),
            (x + 8, y - 5),
            (x + 6, y + 2),
        ),
    )
    pygame.draw.polygon(
        screen,
        (239, 137, 43),
        (
            (x - 4, y + 1),
            (x - 4, y - 7),
            (x + sway, y - height + 6),
            (x + 4, y - 5),
            (x + 3, y + 2),
        ),
    )
    pygame.draw.polygon(
        screen,
        (255, 219, 126),
        (
            (x - 2, y + 1),
            (x, y - 7),
            (x + 2, y + 1),
        ),
    )

    pygame.draw.polygon(
        screen,
        (55, 51, 54),
        (
            (x - 11, y),
            (x + 11, y),
            (x + 7, y + 7),
            (x - 7, y + 7),
        ),
    )
    pygame.draw.line(
        screen,
        (136, 115, 94),
        (x - 10, y),
        (x + 10, y),
        2,
    )


def draw_warden_braziers(screen, floor, current_time):
    if floor.presentation_act != 1 or floor.boss_door is None:
        return

    if not any(enemy.type == "warden" for enemy in floor.enemies):
        return

    door_column, door_row = floor.boss_door

    for row_offset in (-2, 2):
        _draw_brazier(
            screen,
            door_column,
            door_row + row_offset,
            current_time,
        )


def draw_warden_status(screen, warden, font, current_time):
    panel = pygame.Rect(GAME_WIDTH // 2 - 260, 38, 520, 96)

    pygame.draw.rect(
        screen,
        (8, 9, 14),
        panel.move(3, 4),
        border_radius=5,
    )
    pygame.draw.rect(
        screen,
        (22, 18, 28),
        panel,
        border_radius=5,
    )
    pygame.draw.rect(
        screen,
        (94, 69, 101),
        panel,
        width=1,
        border_radius=5,
    )

    second_phase = warden["health"] <= warden["max_health"] // 2
    phase = "II" if second_phase else "I"
    color = (205, 74, 105) if second_phase else (151, 96, 171)

    title = font.render(
        f"CRYPT WARDEN  |  PHASE {phase}",
        True,
        (218, 198, 218),
    )
    screen.blit(
        title,
        title.get_rect(midleft=(panel.left + 16, panel.top + 22)),
    )

    health = font.render(
        f"{warden['health']}/{warden['max_health']}",
        True,
        (218, 198, 218),
    )
    screen.blit(
        health,
        health.get_rect(midright=(panel.right - 16, panel.top + 22)),
    )

    bar = pygame.Rect(panel.left + 16, panel.top + 42, panel.width - 32, 12)
    pygame.draw.rect(screen, (9, 8, 14), bar)

    ratio = max(0.0, min(1.0, warden["health"] / max(1, warden["max_health"])))
    fill = bar.inflate(-4, -4)
    fill.width = round(fill.width * ratio)
    if fill.width > 0:
        pygame.draw.rect(screen, color, fill)

    pygame.draw.rect(screen, (83, 60, 90), bar, width=1)

    phase_started_at = warden.get("phase_transition_started_at", -1)
    phase_elapsed = current_time - phase_started_at
    mode = warden.get("prepared_attack_mode")

    if phase_started_at >= 0 and 0 <= phase_elapsed < 1150:
        status = "THE WARDEN UNBOUND"
        status_color = (226, 151, 220)
    elif warden.get("warden_reposition_target") is not None:
        status = "REPOSITIONING"
        status_color = (174, 139, 218)
    elif warden["attack_targets"] and mode:
        status = f"PREPARING {mode.upper()}"
        status_color = {
            "cross": (230, 79, 86),
            "sweep": (235, 135, 57),
            "runes": (190, 95, 214),
        }.get(mode, color)
    else:
        status = ""
        status_color = color

    if status:
        surface = font.render(status, True, status_color)
        screen.blit(
            surface,
            surface.get_rect(
                center=(panel.centerx, panel.top + 76),
            ),
        )
