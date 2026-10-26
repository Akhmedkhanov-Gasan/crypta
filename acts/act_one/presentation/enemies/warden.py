import math

import pygame


WARDEN_ATTACK_DURATION_MS = 520


def _lighter(color, amount):
    return tuple(
        min(255, channel + amount)
        for channel in color
    )


def _darker(color, amount):
    return tuple(
        max(7, channel - amount)
        for channel in color
    )


def _attack_pose(enemy, current_time):
    started_at = enemy.get(
        "attack_animation_started_at",
        0,
    )
    prepared_mode = enemy.get(
        "prepared_attack_mode",
    )
    attack_mode = enemy.get(
        "attack_effect_mode",
    )

    if started_at <= 0:
        return prepared_mode, 0.18 if prepared_mode else 0.0

    elapsed = current_time - started_at
    if not 0 <= elapsed < WARDEN_ATTACK_DURATION_MS:
        return prepared_mode, 0.18 if prepared_mode else 0.0

    progress = elapsed / WARDEN_ATTACK_DURATION_MS
    cast = math.sin(math.pi * progress)

    return attack_mode or prepared_mode, cast


def draw_warden(
    screen,
    enemy,
    x,
    y,
    size,
    color,
    is_aggro,
    current_time,
):
    actor = pygame.Surface(
        (56, 54),
        pygame.SRCALPHA,
    )

    center_x = 28
    pulse = (
        math.sin(current_time / 220) + 1
    ) / 2
    slow_pulse = (
        math.sin(current_time / 420) + 1
    ) / 2
    bob = 0

    second_phase = (
        enemy["health"]
        <= enemy["max_health"] // 2
    )
    attack_mode, cast = _attack_pose(
        enemy,
        current_time,
    )

    plate = (76, 45, 94)
    plate_dark = (47, 27, 62)
    plate_deep = (25, 15, 35)
    plate_light = (119, 72, 141)
    cloth = (20, 12, 29)
    cloth_mid = (53, 30, 70)
    cloth_light = (86, 49, 108)
    metal = (66, 60, 75)
    metal_light = (124, 108, 137)

    rune = (
        (238, 55, 79)
        if second_phase
        else (190, 42, 65)
        if is_aggro
        else (139, 35, 55)
    )
    rune_light = (
        (255, 146, 151)
        if second_phase
        else (244, 101, 115)
    )

    if second_phase:
        aura_spread = round(
            slow_pulse * 2
        )
        aura_points = (
            (center_x, 3 - aura_spread),
            (43 + aura_spread, 10),
            (50 + aura_spread, 27),
            (44 + aura_spread, 43),
            (center_x, 51 + aura_spread),
            (12 - aura_spread, 43),
            (5 - aura_spread, 27),
            (12 - aura_spread, 10),
        )
        pygame.draw.polygon(
            actor,
            (
                190,
                39,
                104,
                round(18 + pulse * 18),
            ),
            aura_points,
        )
        pygame.draw.polygon(
            actor,
            (
                226,
                69,
                139,
                round(65 + pulse * 45),
            ),
            aura_points,
            width=1,
        )

    cloak_sway = 0
    arm_lift = round(
        cast * 5
    )
    staff_sweep = (
        round(cast * 4)
        if attack_mode is not None
        else 0
    )

    pygame.draw.ellipse(
        actor,
        (5, 4, 8, 180),
        (7, 46, 42, 7),
    )

    pygame.draw.polygon(
        actor,
        plate_deep,
        (
            (18, 36),
            (25, 36),
            (24, 49),
            (21, 51),
            (15, 51),
            (17, 47),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate_deep,
        (
            (31, 36),
            (38, 36),
            (39, 47),
            (42, 51),
            (36, 51),
            (32, 49),
        ),
    )
    pygame.draw.line(
        actor,
        metal,
        (15, 51),
        (22, 51),
        2,
    )
    pygame.draw.line(
        actor,
        metal,
        (36, 51),
        (43, 51),
        2,
    )

    pygame.draw.polygon(
        actor,
        plate_deep,
        (
            (15, 19),
            (22, 15),
            (34, 15),
            (41, 19),
            (44, 28),
            (40, 42),
            (35 + cloak_sway, 48),
            (29, 44),
            (27, 49),
            (23, 44),
            (18 - cloak_sway, 48),
            (13, 41),
            (11, 28),
        ),
    )
    pygame.draw.polygon(
        actor,
        cloth_mid,
        (
            (18, 20),
            (23, 17),
            (33, 17),
            (38, 20),
            (40, 29),
            (37, 40),
            (33 + cloak_sway, 46),
            (28, 42),
            (25, 46),
            (20 - cloak_sway, 43),
            (16, 36),
            (15, 27),
        ),
    )
    pygame.draw.line(
        actor,
        cloth_light,
        (22, 19),
        (21, 39),
    )
    pygame.draw.line(
        actor,
        cloth,
        (32, 18),
        (34, 40),
        2,
    )

    pygame.draw.polygon(
        actor,
        plate,
        (
            (22, 18),
            (17, 17),
            (12, 21),
            (15, 24),
            (20, 23),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate,
        (
            (34, 18),
            (39, 17),
            (44, 21),
            (41, 24),
            (36, 23),
        ),
    )

    pygame.draw.polygon(
        actor,
        cloth,
        (
            (18, 20),
            (23, 15),
            (28, 18),
            (33, 15),
            (38, 20),
            (34, 24),
            (29, 22),
            (28, 25),
            (24, 22),
            (21, 24),
        ),
    )

    left_elbow = (
        18,
        29 - arm_lift,
    )
    left_hand = (
        15,
        36 - arm_lift,
    )
    right_elbow = (
        38,
        29 - arm_lift,
    )
    right_hand = (
        41,
        35 - arm_lift,
    )

    pygame.draw.line(
        actor,
        plate_dark,
        (20, 23),
        left_elbow,
        4,
    )
    pygame.draw.line(
        actor,
        plate,
        left_elbow,
        left_hand,
        2,
    )
    pygame.draw.circle(
        actor,
        metal,
        left_hand,
        2,
    )

    pygame.draw.line(
        actor,
        plate_dark,
        (36, 23),
        right_elbow,
        4,
    )
    pygame.draw.line(
        actor,
        plate,
        right_elbow,
        right_hand,
        2,
    )
    pygame.draw.circle(
        actor,
        metal,
        right_hand,
        2,
    )

    pygame.draw.polygon(
        actor,
        plate_deep,
        (
            (20, 8),
            (22, 5),
            (34, 5),
            (36, 8),
            (35, 15),
            (32, 19),
            (24, 19),
            (20, 15),
        ),
    )

    pygame.draw.polygon(
        actor,
        plate,
        (
            (22, 8),
            (18, 2),
            (25, 6),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate_light,
        (
            (25, 6),
            (28, 0),
            (31, 6),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate,
        (
            (31, 6),
            (38, 2),
            (34, 8),
        ),
    )

    pygame.draw.polygon(
        actor,
        plate,
        (
            (22, 8),
            (25, 5),
            (31, 5),
            (34, 8),
            (33, 14),
            (30, 17),
            (25, 17),
            (22, 14),
        ),
    )
    pygame.draw.polygon(
        actor,
        (8, 6, 12),
        (
            (23, 10),
            (33, 10),
            (32, 14),
            (29, 16),
            (25, 15),
            (22, 13),
        ),
    )
    pygame.draw.rect(
        actor,
        rune_light,
        (23, 11, 3, 2),
    )
    pygame.draw.rect(
        actor,
        rune_light,
        (30, 11, 3, 2),
    )
    pygame.draw.polygon(
        actor,
        metal,
        (
            (25, 16),
            (31, 16),
            (30, 20),
            (26, 20),
        ),
    )

    mark_alpha = round(
        185 + pulse * 70
    )
    mark_color = (
        rune[0],
        rune[1],
        rune[2],
        mark_alpha,
    )

    pygame.draw.line(
        actor,
        mark_color,
        (center_x, 24),
        (center_x, 37),
        3,
    )
    pygame.draw.polygon(
        actor,
        mark_color,
        (
            (center_x - 6, 34),
            (center_x, 42),
            (center_x + 6, 34),
            (center_x + 2, 36),
            (center_x, 39),
            (center_x - 2, 36),
        ),
    )

    staff_top = (
        46 + staff_sweep,
        8 + staff_sweep,
    )
    staff_bottom = (
        43 - staff_sweep,
        49,
    )

    pygame.draw.line(
        actor,
        (25, 19, 30),
        staff_top,
        staff_bottom,
        5,
    )
    pygame.draw.line(
        actor,
        metal,
        staff_top,
        staff_bottom,
        2,
    )
    pygame.draw.line(
        actor,
        metal_light,
        (
            staff_top[0] - 1,
            staff_top[1] + 3,
        ),
        (
            staff_bottom[0] - 1,
            staff_bottom[1] - 4,
        ),
    )

    orb_radius = (
        6
        if attack_mode == "runes"
        else 5
    )
    pygame.draw.circle(
        actor,
        plate_deep,
        staff_top,
        orb_radius + 2,
    )
    pygame.draw.circle(
        actor,
        rune,
        staff_top,
        orb_radius,
    )
    pygame.draw.circle(
        actor,
        rune_light,
        (
            staff_top[0] - 1,
            staff_top[1] - 1,
        ),
        2,
    )

    weapon_rune = staff_top

    if attack_mode == "cross" and cast > 0.1:
        reach = round(
            4 + cast * 4
        )
        pygame.draw.line(
            actor,
            rune_light,
            (
                weapon_rune[0] - reach,
                weapon_rune[1],
            ),
            (
                weapon_rune[0] + reach,
                weapon_rune[1],
            ),
            2,
        )
        pygame.draw.line(
            actor,
            rune_light,
            (
                weapon_rune[0],
                weapon_rune[1] - reach,
            ),
            (
                weapon_rune[0],
                weapon_rune[1] + reach,
            ),
            2,
        )

    if attack_mode == "runes" and cast > 0.1:
        orbit_radius = round(
            10 + cast * 3
        )
        orbit_angle = math.pi / 6

        for index in range(3):
            angle = (
                orbit_angle
                + index * math.tau / 3
            )
            orbit_x = round(
                center_x
                + math.cos(angle)
                * orbit_radius
            )
            orbit_y = round(
                29
                + math.sin(angle)
                * orbit_radius
                * 0.55
            )

            pygame.draw.polygon(
                actor,
                rune_light,
                (
                    (orbit_x, orbit_y - 2),
                    (orbit_x + 2, orbit_y),
                    (orbit_x, orbit_y + 2),
                    (orbit_x - 2, orbit_y),
                ),
            )

    actor_width = 24
    actor_height = 30
    cast_lift = round(
        cast
    )
    actor = pygame.transform.scale(
        actor,
        (
            actor_width,
            actor_height,
        ),
    )

    screen.blit(
        actor,
        (
            x + size // 2
            - actor_width // 2,
            y + size
            - actor_height
            - cast_lift
            + bob,
        ),
    )


def draw_warden_corpse(
        screen,
        center_x,
        center_y,
        opacity=255,
):
    corpse = pygame.Surface(
        (52, 28),
        pygame.SRCALPHA,
    )

    pygame.draw.ellipse(
        corpse,
        (5, 4, 8, 150),
        (4, 19, 44, 7),
    )

    pygame.draw.polygon(
        corpse,
        (18, 13, 24),
        (
            (7, 15),
            (15, 9),
            (31, 8),
            (43, 13),
            (47, 20),
            (39, 23),
            (20, 22),
            (8, 20),
        ),
    )
    pygame.draw.polygon(
        corpse,
        (39, 24, 49),
        (
            (12, 14),
            (19, 10),
            (33, 10),
            (42, 15),
            (38, 20),
            (21, 19),
        ),
    )
    pygame.draw.polygon(
        corpse,
        (58, 43, 67),
        (
            (18, 10),
            (24, 6),
            (34, 8),
            (37, 13),
            (31, 16),
            (21, 15),
        ),
    )

    pygame.draw.polygon(
        corpse,
        (37, 34, 43),
        (
            (9, 12),
            (13, 7),
            (20, 6),
            (23, 11),
            (19, 15),
            (12, 15),
        ),
    )
    pygame.draw.polygon(
        corpse,
        (83, 76, 91),
        (
            (12, 8),
            (16, 5),
            (21, 7),
            (21, 11),
            (17, 13),
            (12, 11),
        ),
    )
    pygame.draw.line(
        corpse,
        (135, 112, 145),
        (13, 8),
        (20, 9),
    )

    pygame.draw.polygon(
        corpse,
        (112, 48, 129),
        (
            (27, 12),
            (31, 15),
            (27, 18),
            (23, 15),
        ),
    )
    pygame.draw.polygon(
        corpse,
        (176, 71, 138),
        (
            (27, 14),
            (29, 15),
            (27, 17),
            (25, 15),
        ),
    )

    pygame.draw.line(
        corpse,
        (26, 22, 30),
        (5, 23),
        (46, 20),
        4,
    )
    pygame.draw.line(
        corpse,
        (75, 67, 82),
        (5, 22),
        (46, 19),
        2,
    )
    pygame.draw.polygon(
        corpse,
        (94, 82, 103),
        (
            (43, 16),
            (49, 18),
            (46, 23),
        ),
    )

    corpse.set_alpha(
        max(
            0,
            min(255, opacity),
        )
    )
    screen.blit(
        corpse,
        (
            center_x - corpse.get_width() // 2,
            center_y,
        ),
    )


__all__ = [
    "draw_warden",
    "draw_warden_corpse",
]
