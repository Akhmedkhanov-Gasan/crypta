import pygame


def set_assassin_target_cursor(cursor_kind=None):
    if cursor_kind is None:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        return

    cursor_surface = pygame.Surface((24, 24), pygame.SRCALPHA)
    center = (12, 12)
    if cursor_kind == "teleport":
        color = (105, 195, 255, 235)
        pygame.draw.polygon(
            cursor_surface,
            color,
            ((12, 2), (22, 12), (12, 22), (2, 12)),
            width=2,
        )
        pygame.draw.circle(cursor_surface, (220, 245, 255, 240), center, 2)
    else:
        color = (235, 75, 85, 240)
        pygame.draw.circle(cursor_surface, color, center, 8, width=2)
        pygame.draw.line(cursor_surface, color, (1, 12), (23, 12), width=2)
        pygame.draw.line(cursor_surface, color, (12, 1), (12, 23), width=2)

    pygame.mouse.set_cursor(
        pygame.cursors.Cursor(center, cursor_surface)
    )


def set_archer_attack_cursor(active=False):
    if not active:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        return

    cursor_surface = pygame.Surface((22, 22), pygame.SRCALPHA)
    edge_color = (215, 222, 226, 255)
    steel_color = (125, 137, 148, 255)
    pygame.draw.line(
        cursor_surface,
        steel_color,
        (3, 18),
        (17, 4),
        width=3,
    )
    pygame.draw.polygon(
        cursor_surface,
        edge_color,
        ((19, 1), (16, 9), (12, 5)),
    )
    pygame.draw.line(
        cursor_surface,
        (75, 83, 91, 255),
        (3, 18),
        (14, 7),
        width=1,
    )
    pygame.mouse.set_cursor(
        pygame.cursors.Cursor((1, 1), cursor_surface)
    )


def set_warlock_staff_cursor(active=False):
    if not active:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        return

    cursor_surface = pygame.Surface((26, 26), pygame.SRCALPHA)
    wood_color = (116, 83, 91, 255)
    edge_color = (198, 158, 213, 255)
    magic_color = (190, 75, 255, 255)
    pygame.draw.line(
        cursor_surface,
        wood_color,
        (5, 23),
        (17, 6),
        width=4,
    )
    pygame.draw.line(
        cursor_surface,
        edge_color,
        (5, 23),
        (17, 6),
        width=1,
    )
    pygame.draw.arc(
        cursor_surface,
        edge_color,
        (13, 1, 11, 12),
        0.4,
        4.9,
        width=2,
    )
    pygame.draw.circle(
        cursor_surface,
        (92, 24, 135, 220),
        (19, 6),
        5,
    )
    pygame.draw.circle(
        cursor_surface,
        magic_color,
        (19, 6),
        2,
    )
    pygame.mouse.set_cursor(
        pygame.cursors.Cursor((4, 23), cursor_surface)
    )


def set_summoner_staff_cursor(active=False):
    if not active:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        return

    cursor_surface = pygame.Surface((26, 26), pygame.SRCALPHA)
    wood_color = (116, 83, 91, 255)
    edge_color = (198, 158, 213, 255)
    magic_color = (74, 240, 224, 255)
    pygame.draw.line(cursor_surface, wood_color, (5, 23), (17, 6), width=4)
    pygame.draw.line(cursor_surface, edge_color, (5, 23), (17, 6), width=1)
    pygame.draw.arc(cursor_surface, edge_color, (13, 1, 11, 12), 0.4, 4.9, width=2)
    pygame.draw.circle(cursor_surface, (26, 139, 145, 220), (19, 6), 5)
    pygame.draw.circle(cursor_surface, magic_color, (19, 6), 2)
    pygame.mouse.set_cursor(pygame.cursors.Cursor((4, 23), cursor_surface))


def set_archer_empowered_cursor(active=False):
    if not active:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        return

    cursor_surface = pygame.Surface((26, 26), pygame.SRCALPHA)
    color = (105, 235, 135, 245)
    center = (13, 13)
    pygame.draw.circle(cursor_surface, color, center, 9, width=2)
    pygame.draw.line(cursor_surface, color, (2, 13), (24, 13), width=2)
    pygame.draw.line(cursor_surface, color, (13, 2), (13, 24), width=2)
    pygame.draw.circle(cursor_surface, (220, 255, 225, 255), center, 2)
    pygame.mouse.set_cursor(
        pygame.cursors.Cursor(center, cursor_surface)
    )


def set_archer_leap_cursor(active=False):
    if not active:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        return

    cursor_surface = pygame.Surface((24, 24), pygame.SRCALPHA)
    color = (105, 235, 175, 245)
    pygame.draw.polygon(
        cursor_surface,
        color,
        ((12, 2), (22, 12), (12, 22), (2, 12)),
        width=2,
    )
    pygame.draw.circle(
        cursor_surface,
        (225, 255, 235, 255),
        (12, 12),
        2,
    )
    pygame.mouse.set_cursor(
        pygame.cursors.Cursor((12, 12), cursor_surface)
    )


def set_berserker_crushing_leap_cursor(active=False):
    if not active:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        return

    cursor_surface = pygame.Surface((26, 26), pygame.SRCALPHA)
    color = (238, 64, 48, 245)
    pygame.draw.circle(
        cursor_surface,
        color,
        (13, 13),
        10,
        width=2,
    )
    pygame.draw.line(
        cursor_surface,
        color,
        (4, 13),
        (22, 13),
        width=2,
    )
    pygame.draw.line(
        cursor_surface,
        color,
        (13, 4),
        (13, 22),
        width=2,
    )
    pygame.draw.circle(
        cursor_surface,
        (255, 205, 185, 255),
        (13, 13),
        2,
    )
    pygame.mouse.set_cursor(
        pygame.cursors.Cursor((13, 13), cursor_surface)
    )


def set_paladin_shield_charge_cursor(active=False):
    if not active:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        return

    cursor_surface = pygame.Surface((26, 26), pygame.SRCALPHA)
    color = (246, 198, 76, 245)
    pygame.draw.polygon(
        cursor_surface,
        color,
        ((13, 2), (22, 7), (20, 19), (13, 24), (6, 19), (4, 7)),
        width=2,
    )
    pygame.draw.line(
        cursor_surface,
        (255, 239, 174, 255),
        (13, 6),
        (13, 20),
        width=2,
    )
    pygame.draw.line(
        cursor_surface,
        (255, 239, 174, 255),
        (8, 12),
        (18, 12),
        width=2,
    )
    pygame.mouse.set_cursor(
        pygame.cursors.Cursor((13, 13), cursor_surface)
    )


def set_archer_barrage_zone_cursor(active=False):
    if not active:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        return

    cursor_surface = pygame.Surface((26, 26), pygame.SRCALPHA)
    color = (115, 245, 155, 245)
    pygame.draw.rect(
        cursor_surface,
        color,
        (3, 6, 20, 15),
        width=2,
        border_radius=3,
    )
    pygame.draw.circle(
        cursor_surface,
        (225, 255, 230, 255),
        (13, 13),
        3,
        width=1,
    )
    pygame.mouse.set_cursor(
        pygame.cursors.Cursor((13, 13), cursor_surface)
    )
