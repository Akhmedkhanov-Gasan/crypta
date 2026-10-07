import pygame


_CURSOR_CACHE = {}
_CURRENT_CURSOR_NAME = None


def _apply_cursor(name, builder):
    global _CURRENT_CURSOR_NAME

    if name not in _CURSOR_CACHE:
        hotspot, surface = builder()
        _CURSOR_CACHE[name] = pygame.cursors.Cursor(
            hotspot,
            surface,
        )

    pygame.mouse.set_cursor(_CURSOR_CACHE[name])
    _CURRENT_CURSOR_NAME = name


def refresh_cursor():
    if _CURRENT_CURSOR_NAME is None:
        set_default_cursor()
        return

    pygame.mouse.set_cursor(
        _CURSOR_CACHE[_CURRENT_CURSOR_NAME]
    )


def _build_default_cursor():
    scale = 3
    canvas = pygame.Surface(
        (36 * scale, 36 * scale),
        pygame.SRCALPHA,
    )

    def point(x, y):
        return (
            round(x * scale),
            round(y * scale),
        )

    def points(values):
        return tuple(
            point(x, y)
            for x, y in values
        )

    blade_shadow = points(
        (
            (3.0, 3.0),
            (23.8, 16.8),
            (26.0, 19.5),
            (20.0, 26.0),
            (17.0, 23.8),
        )
    )
    pygame.draw.polygon(
        canvas,
        (3, 3, 4, 190),
        blade_shadow,
    )

    blade = points(
        (
            (1.5, 1.5),
            (23.0, 16.5),
            (25.0, 19.0),
            (19.0, 25.0),
            (16.5, 23.0),
        )
    )
    pygame.draw.polygon(
        canvas,
        (48, 48, 52, 255),
        blade,
    )
    pygame.draw.polygon(
        canvas,
        (163, 159, 151, 255),
        blade,
        width=scale,
    )

    upper_facet = points(
        (
            (2.8, 2.8),
            (22.6, 17.2),
            (20.8, 20.8),
        )
    )
    pygame.draw.polygon(
        canvas,
        (205, 201, 190, 245),
        upper_facet,
    )

    lower_facet = points(
        (
            (2.8, 2.8),
            (20.8, 20.8),
            (17.2, 22.6),
        )
    )
    pygame.draw.polygon(
        canvas,
        (82, 79, 83, 245),
        lower_facet,
    )

    pygame.draw.line(
        canvas,
        (232, 225, 209, 235),
        point(3.0, 3.0),
        point(20.8, 20.8),
        width=scale,
    )

    red_tip = points(
        (
            (1.3, 1.3),
            (5.5, 3.7),
            (3.7, 5.5),
        )
    )
    pygame.draw.polygon(
        canvas,
        (127, 16, 23, 255),
        red_tip,
    )
    pygame.draw.line(
        canvas,
        (244, 72, 61, 255),
        point(1.8, 1.8),
        point(4.5, 3.7),
        width=scale,
    )

    guard_shadow = points(
        (
            (13.0, 27.0),
            (16.5, 29.0),
            (29.0, 16.5),
            (27.0, 13.0),
        )
    )
    pygame.draw.polygon(
        canvas,
        (4, 3, 5, 180),
        guard_shadow,
    )

    guard = points(
        (
            (12.0, 25.5),
            (15.5, 28.0),
            (28.0, 15.5),
            (25.5, 12.0),
        )
    )
    pygame.draw.polygon(
        canvas,
        (31, 26, 29, 255),
        guard,
    )
    pygame.draw.polygon(
        canvas,
        (177, 148, 108, 255),
        guard,
        width=scale,
    )

    pygame.draw.line(
        canvas,
        (211, 184, 137, 230),
        point(14.0, 25.5),
        point(25.5, 14.0),
        width=scale,
    )

    pygame.draw.circle(
        canvas,
        (65, 11, 17, 255),
        point(21.5, 21.5),
        2 * scale,
    )
    pygame.draw.circle(
        canvas,
        (203, 47, 43, 255),
        point(21.0, 21.0),
        scale,
    )

    pygame.draw.line(
        canvas,
        (19, 15, 18, 255),
        point(23.0, 23.0),
        point(31.0, 31.0),
        width=6 * scale,
    )
    pygame.draw.line(
        canvas,
        (83, 38, 41, 255),
        point(23.2, 23.2),
        point(31.0, 31.0),
        width=4 * scale,
    )

    for start, end in (
        ((24.0, 23.0), (22.8, 25.0)),
        ((26.5, 25.5), (25.2, 27.5)),
        ((29.0, 28.0), (27.7, 30.0)),
    ):
        pygame.draw.line(
            canvas,
            (181, 143, 105, 245),
            point(*start),
            point(*end),
            width=scale,
        )

    pommel = points(
        (
            (30.0, 29.0),
            (34.0, 31.5),
            (31.5, 35.0),
            (28.8, 31.0),
        )
    )
    pygame.draw.polygon(
        canvas,
        (28, 23, 27, 255),
        pommel,
    )
    pygame.draw.polygon(
        canvas,
        (151, 126, 94, 255),
        pommel,
        width=scale,
    )

    surface = pygame.transform.smoothscale(
        canvas,
        (36, 36),
    )
    return (1, 1), surface


def _build_target_cursor(
        color,
        inner_color,
):
    surface = pygame.Surface(
        (28, 28),
        pygame.SRCALPHA,
    )
    center = (14, 14)

    pygame.draw.circle(
        surface,
        (18, 14, 19, 190),
        center,
        11,
    )
    pygame.draw.circle(
        surface,
        color,
        center,
        10,
        width=2,
    )
    pygame.draw.line(
        surface,
        color,
        (2, 14),
        (8, 14),
        width=2,
    )
    pygame.draw.line(
        surface,
        color,
        (20, 14),
        (26, 14),
        width=2,
    )
    pygame.draw.line(
        surface,
        color,
        (14, 2),
        (14, 8),
        width=2,
    )
    pygame.draw.line(
        surface,
        color,
        (14, 20),
        (14, 26),
        width=2,
    )
    pygame.draw.circle(
        surface,
        inner_color,
        center,
        2,
    )

    return center, surface


def _build_teleport_cursor():
    surface = pygame.Surface((28, 28), pygame.SRCALPHA)
    center = (14, 14)

    pygame.draw.polygon(
        surface,
        (19, 22, 29, 210),
        ((14, 1), (27, 14), (14, 27), (1, 14)),
    )
    pygame.draw.polygon(
        surface,
        (92, 175, 222, 255),
        ((14, 2), (26, 14), (14, 26), (2, 14)),
        width=2,
    )
    pygame.draw.polygon(
        surface,
        (178, 228, 250, 245),
        ((14, 7), (21, 14), (14, 21), (7, 14)),
        width=1,
    )
    pygame.draw.circle(
        surface,
        (225, 249, 255, 255),
        center,
        2,
    )

    return center, surface


def _build_attack_cursor():
    surface = pygame.Surface((28, 28), pygame.SRCALPHA)

    pygame.draw.line(
        surface,
        (28, 22, 24, 230),
        (4, 24),
        (22, 4),
        width=6,
    )
    pygame.draw.line(
        surface,
        (117, 112, 112, 255),
        (5, 23),
        (21, 5),
        width=4,
    )
    pygame.draw.line(
        surface,
        (225, 216, 196, 255),
        (7, 21),
        (20, 6),
        width=1,
    )
    pygame.draw.polygon(
        surface,
        (205, 198, 181, 255),
        ((24, 2), (21, 10), (17, 6)),
    )
    pygame.draw.line(
        surface,
        (115, 24, 30, 255),
        (3, 20),
        (8, 25),
        width=3,
    )
    pygame.draw.circle(
        surface,
        (178, 46, 43, 255),
        (4, 24),
        2,
    )

    return (23, 3), surface


def _build_staff_cursor(
    magic_color,
    shadow_color,
):
    surface = pygame.Surface((28, 28), pygame.SRCALPHA)

    pygame.draw.line(
        surface,
        (25, 19, 24, 235),
        (5, 25),
        (18, 6),
        width=6,
    )
    pygame.draw.line(
        surface,
        (105, 73, 76, 255),
        (5, 25),
        (18, 6),
        width=4,
    )
    pygame.draw.line(
        surface,
        (190, 153, 151, 245),
        (6, 24),
        (18, 7),
        width=1,
    )
    pygame.draw.arc(
        surface,
        magic_color,
        (14, 1, 12, 13),
        0.35,
        5.0,
        width=2,
    )
    pygame.draw.circle(
        surface,
        shadow_color,
        (20, 7),
        6,
    )
    pygame.draw.circle(
        surface,
        magic_color,
        (20, 7),
        3,
    )
    pygame.draw.circle(
        surface,
        (245, 232, 225, 255),
        (20, 7),
        1,
    )

    return (5, 25), surface


def _build_curse_cursor(valid):
    outer_color = (
        (201, 78, 224, 255)
        if valid
        else (110, 67, 119, 245)
    )
    inner_color = (
        (255, 208, 250, 255)
        if valid
        else (171, 132, 177, 240)
    )
    surface = pygame.Surface((30, 30), pygame.SRCALPHA)
    center = (15, 15)

    pygame.draw.circle(
        surface,
        (22, 13, 24, 205),
        center,
        12,
    )
    pygame.draw.circle(
        surface,
        outer_color,
        center,
        11,
        width=2,
    )

    for offset_x, offset_y in (
        (0, -12),
        (10, -6),
        (10, 6),
        (0, 12),
        (-10, 6),
        (-10, -6),
    ):
        pygame.draw.circle(
            surface,
            outer_color,
            (
                center[0] + offset_x,
                center[1] + offset_y,
            ),
            2,
        )

    pygame.draw.line(
        surface,
        outer_color,
        (6, 15),
        (24, 15),
        width=1,
    )
    pygame.draw.line(
        surface,
        outer_color,
        (15, 6),
        (15, 24),
        width=1,
    )
    pygame.draw.circle(
        surface,
        inner_color,
        center,
        3,
    )

    return center, surface


def _build_leap_cursor(color, inner_color):
    surface = pygame.Surface((28, 28), pygame.SRCALPHA)
    center = (14, 14)

    pygame.draw.polygon(
        surface,
        (19, 21, 20, 200),
        ((14, 1), (27, 14), (14, 27), (1, 14)),
    )
    pygame.draw.polygon(
        surface,
        color,
        ((14, 2), (26, 14), (14, 26), (2, 14)),
        width=2,
    )
    pygame.draw.line(
        surface,
        color,
        (8, 18),
        (14, 8),
        width=2,
    )
    pygame.draw.line(
        surface,
        color,
        (14, 8),
        (20, 18),
        width=2,
    )
    pygame.draw.circle(
        surface,
        inner_color,
        center,
        2,
    )

    return center, surface


def _build_shield_cursor():
    surface = pygame.Surface((28, 28), pygame.SRCALPHA)
    center = (14, 14)
    points = (
        (14, 2),
        (24, 7),
        (22, 20),
        (14, 27),
        (6, 20),
        (4, 7),
    )

    pygame.draw.polygon(
        surface,
        (29, 20, 31, 235),
        points,
    )
    pygame.draw.polygon(
        surface,
        (205, 163, 74, 255),
        points,
        width=2,
    )
    pygame.draw.line(
        surface,
        (255, 231, 165, 255),
        (14, 6),
        (14, 22),
        width=2,
    )
    pygame.draw.line(
        surface,
        (255, 231, 165, 255),
        (9, 13),
        (19, 13),
        width=2,
    )
    pygame.draw.circle(
        surface,
        (98, 57, 100, 255),
        center,
        2,
    )

    return center, surface


def _build_zone_cursor():
    surface = pygame.Surface((28, 28), pygame.SRCALPHA)
    center = (14, 14)
    color = (99, 213, 133, 255)

    pygame.draw.rect(
        surface,
        (16, 25, 20, 210),
        (2, 5, 24, 18),
        border_radius=4,
    )
    pygame.draw.rect(
        surface,
        color,
        (3, 6, 22, 16),
        width=2,
        border_radius=4,
    )
    pygame.draw.line(
        surface,
        color,
        (5, 14),
        (23, 14),
        width=1,
    )
    pygame.draw.line(
        surface,
        color,
        (14, 7),
        (14, 21),
        width=1,
    )
    pygame.draw.circle(
        surface,
        (222, 247, 218, 255),
        center,
        3,
        width=1,
    )

    return center, surface


def set_default_cursor():
    _apply_cursor(
        "default",
        _build_default_cursor,
    )


def set_assassin_target_cursor(cursor_kind=None):
    if cursor_kind is None:
        set_default_cursor()
        return

    if cursor_kind == "teleport":
        _apply_cursor(
            "assassin_teleport",
            _build_teleport_cursor,
        )
        return

    _apply_cursor(
        "assassin_target",
        lambda: _build_target_cursor(
            (213, 65, 72, 255),
            (255, 204, 190, 255),
        ),
    )


def set_archer_attack_cursor(active=False):
    if not active:
        set_default_cursor()
        return

    _apply_cursor(
        "attack",
        _build_attack_cursor,
    )


def set_warlock_staff_cursor(active=False):
    if not active:
        set_default_cursor()
        return

    _apply_cursor(
        "warlock_staff",
        lambda: _build_staff_cursor(
            (192, 75, 230, 255),
            (78, 25, 99, 235),
        ),
    )


def set_summoner_staff_cursor(active=False):
    if not active:
        set_default_cursor()
        return

    _apply_cursor(
        "summoner_staff",
        lambda: _build_staff_cursor(
            (65, 220, 202, 255),
            (20, 103, 105, 235),
        ),
    )


def set_warlock_curse_cursor(
    aiming=False,
    valid=False,
):
    if not aiming:
        set_default_cursor()
        return

    _apply_cursor(
        f"warlock_curse_{valid}",
        lambda: _build_curse_cursor(valid),
    )


def set_archer_empowered_cursor(active=False):
    if not active:
        set_default_cursor()
        return

    _apply_cursor(
        "archer_empowered",
        lambda: _build_target_cursor(
            (91, 213, 119, 255),
            (221, 255, 221, 255),
        ),
    )


def set_archer_leap_cursor(active=False):
    if not active:
        set_default_cursor()
        return

    _apply_cursor(
        "archer_leap",
        lambda: _build_leap_cursor(
            (80, 211, 151, 255),
            (222, 255, 228, 255),
        ),
    )


def set_berserker_crushing_leap_cursor(active=False):
    if not active:
        set_default_cursor()
        return

    _apply_cursor(
        "berserker_crushing_leap",
        lambda: _build_target_cursor(
            (221, 56, 46, 255),
            (255, 198, 174, 255),
        ),
    )


def set_paladin_shield_charge_cursor(active=False):
    if not active:
        set_default_cursor()
        return

    _apply_cursor(
        "paladin_shield_charge",
        _build_shield_cursor,
    )


def set_archer_barrage_zone_cursor(active=False):
    if not active:
        set_default_cursor()
        return

    _apply_cursor(
        "archer_barrage_zone",
        _build_zone_cursor,
    )
