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

    plate = _darker(color, 12)
    plate_dark = _darker(color, 42)
    plate_deep = _darker(color, 68)
    plate_light = _lighter(color, 23)
    cloth = (21, 15, 28)
    cloth_mid = (38, 24, 49)
    cloth_light = (56, 35, 68)
    metal = (72, 68, 82)
    metal_light = (126, 116, 137)

    rune = (
        (239, 62, 121)
        if second_phase
        else (180, 79, 207)
        if is_aggro
        else (100, 71, 121)
    )
    rune_light = (
        (255, 148, 181)
        if second_phase
        else (227, 153, 241)
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
        cast * 2
    )
    staff_sweep = (
        round(cast * 2)
        if attack_mode == "sweep"
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
            (17, 37),
            (24, 36),
            (24, 48),
            (20, 51),
            (14, 51),
            (16, 47),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate_deep,
        (
            (32, 36),
            (39, 37),
            (40, 47),
            (43, 51),
            (36, 51),
            (32, 48),
        ),
    )
    pygame.draw.polygon(
        actor,
        metal,
        (
            (14, 49),
            (23, 49),
            (21, 52),
            (13, 52),
        ),
    )
    pygame.draw.polygon(
        actor,
        metal,
        (
            (34, 49),
            (43, 49),
            (44, 52),
            (36, 52),
        ),
    )

    pygame.draw.polygon(
        actor,
        plate_deep,
        (
            (14, 18),
            (21, 14),
            (35, 14),
            (43, 18),
            (46, 27),
            (42, 41),
            (37 + cloak_sway, 49),
            (31, 44),
            (28, 50),
            (24, 44),
            (18 - cloak_sway, 49),
            (12, 40),
            (10, 27),
        ),
    )
    pygame.draw.polygon(
        actor,
        cloth,
        (
            (17, 19),
            (23, 16),
            (34, 16),
            (40, 20),
            (42, 30),
            (38, 42),
            (34 + cloak_sway, 47),
            (29, 42),
            (27, 47),
            (23, 42),
            (19 - cloak_sway, 46),
            (15, 38),
            (14, 27),
        ),
    )
    pygame.draw.polygon(
        actor,
        cloth_mid,
        (
            (20, 20),
            (25, 17),
            (31, 17),
            (36, 21),
            (36, 35),
            (32, 42),
            (28, 39),
            (24, 43),
            (20, 35),
        ),
    )
    pygame.draw.polygon(
        actor,
        cloth_light,
        (
            (22, 21),
            (26, 18),
            (30, 18),
            (32, 22),
            (31, 36),
            (28, 39),
            (24, 34),
        ),
    )

    pygame.draw.polygon(
        actor,
        plate_deep,
        (
            (20, 17),
            (14, 16),
            (7, 19),
            (3, 24),
            (9, 28),
            (17, 26),
            (23, 20),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate,
        (
            (18, 18),
            (13, 18),
            (7, 21),
            (5, 24),
            (10, 26),
            (17, 24),
            (21, 20),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate_light,
        (
            (13, 19),
            (8, 21),
            (6, 23),
            (12, 22),
            (18, 20),
        ),
    )

    pygame.draw.polygon(
        actor,
        plate_deep,
        (
            (36, 17),
            (42, 16),
            (49, 19),
            (53, 24),
            (47, 28),
            (39, 26),
            (33, 20),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate,
        (
            (38, 18),
            (43, 18),
            (49, 21),
            (51, 24),
            (46, 26),
            (39, 24),
            (35, 20),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate_light,
        (
            (43, 19),
            (48, 21),
            (50, 23),
            (44, 22),
            (38, 20),
        ),
    )

    pygame.draw.polygon(
        actor,
        cloth,
        (
            (17, 19),
            (22, 14),
            (28, 17),
            (34, 14),
            (39, 19),
            (36, 25),
            (31, 22),
            (28, 26),
            (24, 22),
            (20, 25),
        ),
    )
    pygame.draw.polygon(
        actor,
        cloth_mid,
        (
            (20, 19),
            (23, 16),
            (28, 19),
            (33, 16),
            (36, 19),
            (33, 22),
            (29, 21),
            (28, 24),
            (25, 21),
            (22, 22),
        ),
    )
    pygame.draw.line(
        actor,
        cloth_light,
        (22, 18),
        (27, 21),
    )

    left_elbow = (
        13,
        29 - arm_lift,
    )
    left_hand = (
        8,
        34 - arm_lift,
    )
    right_elbow = (
        42,
        28 - arm_lift,
    )
    right_hand = (
        46,
        33 - arm_lift,
    )

    pygame.draw.polygon(
        actor,
        plate_dark,
        (
            (16, 24),
            (19, 27),
            (left_elbow[0] + 2, left_elbow[1]),
            (left_elbow[0], left_elbow[1] + 5),
            (9, 30),
            (10, 26),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate,
        (
            (left_elbow[0], left_elbow[1]),
            (left_elbow[0] + 3, left_elbow[1] + 2),
            (left_hand[0] + 2, left_hand[1] + 2),
            (left_hand[0] - 1, left_hand[1] + 4),
            (left_elbow[0] - 2, left_elbow[1] + 4),
        ),
    )
    pygame.draw.polygon(
        actor,
        metal,
        (
            (left_hand[0] - 2, left_hand[1] + 1),
            (left_hand[0] + 2, left_hand[1]),
            (left_hand[0] + 3, left_hand[1] + 4),
            (left_hand[0] - 1, left_hand[1] + 5),
        ),
    )

    pygame.draw.polygon(
        actor,
        plate_dark,
        (
            (37, 24),
            (40, 26),
            (right_elbow[0] + 2, right_elbow[1]),
            (right_elbow[0] + 4, right_elbow[1] + 4),
            (46, 32),
            (43, 34),
            (39, 29),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate,
        (
            (right_elbow[0], right_elbow[1]),
            (right_elbow[0] + 3, right_elbow[1] + 1),
            (right_hand[0] + 2, right_hand[1] + 2),
            (right_hand[0] - 1, right_hand[1] + 5),
            (right_elbow[0] - 2, right_elbow[1] + 4),
        ),
    )
    pygame.draw.polygon(
        actor,
        metal,
        (
            (right_hand[0] - 2, right_hand[1] + 1),
            (right_hand[0] + 2, right_hand[1]),
            (right_hand[0] + 3, right_hand[1] + 4),
            (right_hand[0] - 1, right_hand[1] + 5),
        ),
    )

    pygame.draw.polygon(
        actor,
        plate_deep,
        (
            (20, 8),
            (16, 3),
            (22, 4),
            (25, 0),
            (28, 4),
            (31, 0),
            (34, 4),
            (40, 3),
            (36, 8),
            (36, 15),
            (32, 20),
            (23, 20),
            (19, 15),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate,
        (
            (21, 8),
            (24, 5),
            (32, 5),
            (35, 8),
            (34, 15),
            (31, 18),
            (24, 18),
            (21, 14),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate_light,
        (
            (23, 7),
            (26, 5),
            (31, 6),
            (33, 8),
            (30, 10),
            (24, 10),
        ),
    )
    pygame.draw.polygon(
        actor,
        (8, 6, 12),
        (
            (22, 10),
            (34, 10),
            (33, 14),
            (30, 16),
            (24, 15),
            (21, 13),
        ),
    )
    pygame.draw.line(
        actor,
        plate_dark,
        (28, 10),
        (28, 17),
        2,
    )
    pygame.draw.rect(
        actor,
        rune,
        (23, 11, 2, 1),
    )
    pygame.draw.rect(
        actor,
        rune,
        (31, 11, 2, 1),
    )
    pygame.draw.polygon(
        actor,
        metal,
        (
            (24, 17),
            (32, 17),
            (30, 21),
            (26, 21),
        ),
    )

    core_size = (
        5
        if attack_mode == "runes"
        else 4
    )
    core_center = (
        center_x,
        29,
    )
    core_glow = (
        core_center[0],
        core_center[1] - core_size - 3,
        core_size * 2 + 6,
        core_size * 2 + 6,
    )

    pygame.draw.polygon(
        actor,
        (
            rune[0],
            rune[1],
            rune[2],
            round(45 + pulse * 45),
        ),
        (
            (
                core_center[0],
                core_glow[1],
            ),
            (
                core_glow[0] + core_glow[2],
                core_center[1],
            ),
            (
                core_center[0],
                core_glow[1] + core_glow[3],
            ),
            (
                core_glow[0],
                core_center[1],
            ),
        ),
    )
    pygame.draw.polygon(
        actor,
        rune,
        (
            (
                core_center[0],
                core_center[1] - core_size,
            ),
            (
                core_center[0] + core_size,
                core_center[1],
            ),
            (
                core_center[0],
                core_center[1] + core_size,
            ),
            (
                core_center[0] - core_size,
                core_center[1],
            ),
        ),
    )
    pygame.draw.line(
        actor,
        rune_light,
        (center_x, 26),
        (center_x + 2, 29),
    )
    pygame.draw.line(
        actor,
        rune,
        (center_x, 34),
        (center_x, 39),
        2,
    )
    pygame.draw.line(
        actor,
        rune,
        (center_x, 37),
        (center_x - 4, 41),
    )
    pygame.draw.line(
        actor,
        rune,
        (center_x, 37),
        (center_x + 4, 41),
    )

    staff_top = (
        46 + staff_sweep,
        7 + staff_sweep,
    )
    staff_bottom = (
        43 - staff_sweep,
        49,
    )

    pygame.draw.line(
        actor,
        (30, 23, 34),
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
            staff_top[1],
        ),
        (
            staff_bottom[0] - 1,
            staff_bottom[1] - 4,
        ),
    )

    blade_center = staff_top
    pygame.draw.polygon(
        actor,
        plate_deep,
        (
            (
                blade_center[0] - 3,
                blade_center[1] + 5,
            ),
            (
                blade_center[0] - 1,
                blade_center[1] - 5,
            ),
            (
                blade_center[0] + 2,
                blade_center[1] - 1,
            ),
            (
                blade_center[0] + 8,
                blade_center[1] - 3,
            ),
            (
                blade_center[0] + 5,
                blade_center[1] + 2,
            ),
            (
                blade_center[0] + 9,
                blade_center[1] + 7,
            ),
            (
                blade_center[0] + 2,
                blade_center[1] + 5,
            ),
            (
                blade_center[0] - 1,
                blade_center[1] + 10,
            ),
        ),
    )
    pygame.draw.polygon(
        actor,
        plate_light,
        (
            (
                blade_center[0],
                blade_center[1] - 3,
            ),
            (
                blade_center[0] + 2,
                blade_center[1],
            ),
            (
                blade_center[0] + 7,
                blade_center[1] - 2,
            ),
            (
                blade_center[0] + 4,
                blade_center[1] + 2,
            ),
        ),
    )

    weapon_rune = (
        blade_center[0] + 1,
        blade_center[1] + 3,
    )
    pygame.draw.polygon(
        actor,
        rune,
        (
            (
                weapon_rune[0],
                weapon_rune[1] - 3,
            ),
            (
                weapon_rune[0] + 3,
                weapon_rune[1],
            ),
            (
                weapon_rune[0],
                weapon_rune[1] + 3,
            ),
            (
                weapon_rune[0] - 3,
                weapon_rune[1],
            ),
        ),
    )

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

    intro_pose_progress = max(
        0.0,
        min(
            1.0,
            enemy.get(
                "intro_pose_progress",
                1.0,
            ),
        ),
    )
    actor_height = round(
        32 + 16 * intro_pose_progress
    )
    actor = pygame.transform.scale(
        actor,
        (44, actor_height),
    )

    screen.blit(
        actor,
        (
            x + size // 2
            - actor.get_width() // 2,
            y + size
            - 44
            + 48
            - actor_height
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
