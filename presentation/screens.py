import math

import pygame

from acts.act_three.settings import SUBCLASS_BASE_STATS
from acts.act_two.settings import CLASS_BASE_STATS
from acts.player_stats import (
    describe_player_stat_changes,
    player_stat_changes_for_attribute_upgrade,
    player_stat_changes_between,
)
from acts.act_two.presentation.awakening  import (
    OLD_MAN_RESPONSES,
    draw_awakening_choices,
    draw_awakening_old_man,
)
from presentation.hud import wrap_text
from presentation.layout import (
    ACT_THREE_AWAKENING_END_MS,
    ACT_THREE_CAMERA_END_MS,
    ACT_THREE_CLENCH_END_MS,
    ACT_THREE_EYES_OPEN_END_MS,
    ACT_THREE_EYES_OPEN_START_MS,
    ACT_THREE_FINAL_HOLD_END_MS,
    ACT_THREE_HANDS_HOLD_END_MS,
    ACT_THREE_HANDS_RISE_END_MS,
    ACT_THREE_HANDS_RISE_START_MS,
    ACT_THREE_NARRATIVE_READY_MS,
    ACT_THREE_NARRATIVE_START_MS,
    AWAKENING_FADE_END_MS,
    AWAKENING_HOLD_END_MS,
    AWAKENING_DIALOGUE_START_MS,
    AWAKENING_OPEN_END_MS,
    AWAKENING_OPEN_START_MS,
    AWAKENING_OLD_MAN_APPROACH_END_MS,
    AWAKENING_OLD_MAN_APPROACH_START_MS,
    AWAKENING_RECOVERY_BLINK_END_MS,
    AWAKENING_RECOVERY_BLINK_START_MS,
    AWAKENING_SECOND_OPEN_END_MS,
    AWAKENING_SECOND_OPEN_START_MS,
    CLASS_SELECTION_CHOICE_END_MS,
    CLASS_SELECTION_READY_MS,
)
from settings import (
    GAME_HEIGHT,
    GAME_WIDTH,
    MAX_ATTRIBUTE_RANK,
    PLAYER_ATTACK_BORDER_COLOR,
    TEXT_COLOR,
)
from presentation.transition_timing import (
    FLOOR_TRANSITION_CLOSE_END_MS,
    FLOOR_TRANSITION_END_MS,
    FLOOR_TRANSITION_HOLD_END_MS,
    FLOOR_TRANSITION_REVEAL_END_MS,
)


def draw_floor_transition(
    screen,
    title_font,
    text_font,
    elapsed_ms,
    floor_number,
    subtitle,
):
    if not 0 <= elapsed_ms < FLOOR_TRANSITION_END_MS:
        return

    center = (GAME_WIDTH // 2, GAME_HEIGHT // 2)
    maximum_radius = round(
        (GAME_WIDTH * GAME_WIDTH + GAME_HEIGHT * GAME_HEIGHT) ** 0.5
        / 2
    ) + 24
    overlay = pygame.Surface(
        (GAME_WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA,
    )
    ring_radius = None

    if elapsed_ms < FLOOR_TRANSITION_CLOSE_END_MS:
        progress = elapsed_ms / FLOOR_TRANSITION_CLOSE_END_MS
        eased = progress * progress * (3 - 2 * progress)
        ring_radius = round(maximum_radius * (1 - eased))
        overlay.fill((3, 3, 7, 255))
        pygame.draw.circle(
            overlay,
            (0, 0, 0, 0),
            center,
            ring_radius,
        )
    elif elapsed_ms < FLOOR_TRANSITION_HOLD_END_MS:
        overlay.fill((3, 3, 7, 255))
    elif elapsed_ms < FLOOR_TRANSITION_REVEAL_END_MS:
        progress = (
            elapsed_ms - FLOOR_TRANSITION_HOLD_END_MS
        ) / (
            FLOOR_TRANSITION_REVEAL_END_MS
            - FLOOR_TRANSITION_HOLD_END_MS
        )
        eased = progress * progress * (3 - 2 * progress)
        ring_radius = round(maximum_radius * eased)
        overlay.fill((3, 3, 7, 255))
        pygame.draw.circle(
            overlay,
            (0, 0, 0, 0),
            center,
            ring_radius,
        )

    if overlay.get_at((0, 0)).a:
        screen.blit(overlay, (0, 0))

    if ring_radius is not None and 8 < ring_radius < maximum_radius:
        rim = pygame.Surface(
            (GAME_WIDTH, GAME_HEIGHT),
            pygame.SRCALPHA,
        )
        pygame.draw.circle(
            rim,
            (122, 111, 92, 75),
            center,
            ring_radius,
            width=2,
        )
        screen.blit(rim, (0, 0))

    title_start = FLOOR_TRANSITION_CLOSE_END_MS + 45
    if elapsed_ms < title_start:
        return

    if elapsed_ms < title_start + 180:
        title_alpha = round(
            255 * (elapsed_ms - title_start) / 180
        )
    elif elapsed_ms > FLOOR_TRANSITION_END_MS - 350:
        title_alpha = round(
            255
            * (FLOOR_TRANSITION_END_MS - elapsed_ms)
            / 350
        )
    else:
        title_alpha = 255
    title_alpha = max(0, min(255, title_alpha))

    caption_panel = pygame.Surface((600, 118), pygame.SRCALPHA)
    caption_panel.fill((3, 3, 7, round(145 * title_alpha / 255)))
    pygame.draw.line(
        caption_panel,
        (105, 98, 91, round(90 * title_alpha / 255)),
        (80, 12),
        (520, 12),
    )
    pygame.draw.line(
        caption_panel,
        (105, 98, 91, round(65 * title_alpha / 255)),
        (150, 106),
        (450, 106),
    )
    screen.blit(
        caption_panel,
        caption_panel.get_rect(center=center),
    )

    title = title_font.render(
        f"FLOOR {floor_number}",
        True,
        (218, 209, 193),
    )
    title.set_alpha(title_alpha)
    screen.blit(
        title,
        title.get_rect(center=(center[0], center[1] - 18)),
    )

    if subtitle:
        subtitle_surface = text_font.render(
            subtitle,
            True,
            (143, 137, 132),
        )
        subtitle_surface.set_alpha(title_alpha)
        screen.blit(
            subtitle_surface,
            subtitle_surface.get_rect(
                center=(center[0], center[1] + 28)
            ),
        )


def get_upgrade_card_rectangles(show_intelligence=False):
    if show_intelligence:
        return {
            "strength": pygame.Rect(210, 240, 410, 132),
            "dexterity": pygame.Rect(660, 240, 410, 132),
            "intelligence": pygame.Rect(210, 394, 410, 132),
            "vitality": pygame.Rect(660, 394, 410, 132),
        }
    return {
        "strength": pygame.Rect(190, 240, 280, 250),
        "dexterity": pygame.Rect(500, 240, 280, 250),
        "vitality": pygame.Rect(810, 240, 280, 250),
    }


def get_act_one_upgrade_card_rectangles():
    """Clickable regions matching the flattened Act One Figma export."""
    return {
        "strength": pygame.Rect(210, 304, 275, 233),
        "dexterity": pygame.Rect(503, 304, 275, 233),
        "vitality": pygame.Rect(798, 304, 275, 233),
    }


def draw_act_one_upgrade_screen(
    screen,
    upgrade_background,
    text_font,
    upgrades_remaining,
    message,
    mouse_position=None,
):
    dark_overlay = pygame.Surface(
        (GAME_WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA,
    )
    dark_overlay.fill((0, 0, 0, 150))
    screen.blit(dark_overlay, (0, 0))

    background_rectangle = upgrade_background.get_rect(
        center=(GAME_WIDTH // 2, GAME_HEIGHT // 2),
    )
    screen.blit(upgrade_background, background_rectangle)

    card_rectangles = get_act_one_upgrade_card_rectangles()
    for rectangle in card_rectangles.values():
        if (
            mouse_position is not None
            and rectangle.collidepoint(mouse_position)
        ):
            highlight = pygame.Surface(
                rectangle.size,
                pygame.SRCALPHA,
            )
            highlight.fill((185, 199, 225, 22))
            screen.blit(highlight, rectangle.topleft)
            pygame.draw.rect(
                screen,
                (181, 196, 225),
                rectangle,
                width=2,
                border_radius=8,
            )

    counter_background = pygame.Surface((430, 38), pygame.SRCALPHA)
    counter_background.fill((9, 10, 16, 238))
    counter_rectangle = counter_background.get_rect(
        center=(GAME_WIDTH // 2, 220),
    )
    screen.blit(counter_background, counter_rectangle)
    counter_text = (
        f"{upgrades_remaining} BLESSING"
        f"{'S' if upgrades_remaining != 1 else ''} AVAILABLE"
        if upgrades_remaining > 0
        else "[ENTER] DESCEND"
    )
    counter_surface = text_font.render(
        counter_text,
        True,
        (211, 186, 126),
    )
    screen.blit(
        counter_surface,
        counter_surface.get_rect(center=counter_rectangle.center),
    )

    if message:
        message_background = pygame.Surface((520, 34), pygame.SRCALPHA)
        message_background.fill((9, 10, 16, 230))
        message_rectangle = message_background.get_rect(
            center=(GAME_WIDTH // 2, 590),
        )
        screen.blit(message_background, message_rectangle)
        message_surface = text_font.render(
            message,
            True,
            (211, 186, 126),
        )
        screen.blit(
            message_surface,
            message_surface.get_rect(center=message_rectangle.center),
        )


def _draw_upgrade_icon(screen, kind, center, color):
    icon_surface = pygame.Surface((44, 44), pygame.SRCALPHA)
    pygame.draw.circle(icon_surface, (11, 12, 16, 220), (22, 22), 21)
    pygame.draw.circle(icon_surface, color, (22, 22), 20, width=2)

    if kind == "strength":
        # Raised-fist silhouette based on the reference. Drawing at 4x keeps
        # the separated fingers and thumb readable after downscaling.
        scale = 4
        glyph = pygame.Surface((44 * scale, 44 * scale), pygame.SRCALPHA)

        def scaled_points(points):
            return [(x * scale, y * scale) for x, y in points]

        def draw_finger(center_position, size, angle):
            padding = 4 * scale
            width, height = size
            finger = pygame.Surface(
                (
                    width * scale + padding * 2,
                    height * scale + padding * 2,
                ),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                finger,
                color,
                (
                    padding,
                    padding,
                    width * scale,
                    height * scale,
                ),
                border_radius=2 * scale,
            )
            rotated = pygame.transform.rotate(finger, angle)
            glyph.blit(
                rotated,
                rotated.get_rect(
                    center=(
                        center_position[0] * scale,
                        center_position[1] * scale,
                    )
                ),
            )

        # Four separated fingers. Their lower ends are covered by the palm,
        # which keeps the silhouette joined without losing the gaps on top.
        draw_finger((16, 10), (5, 12), -34)
        draw_finger((22, 12), (5, 13), -34)
        draw_finger((28, 16), (5, 13), -34)
        draw_finger((33, 21), (5, 11), -34)

        # Left palm and straight wrist.
        pygame.draw.polygon(
            glyph,
            color,
            scaled_points(
                [
                    (9, 18), (13, 15), (24, 19), (28, 21),
                    (28, 25), (25, 28), (20, 29), (16, 27),
                    (15, 25), (17, 23), (15, 22), (13, 24),
                    (9, 23), (8, 20),
                ]
            ),
        )
        pygame.draw.polygon(
            glyph,
            color,
            scaled_points(
                [
                    (13, 25), (22, 28), (22, 38), (12, 38),
                    (13, 31),
                ]
            ),
        )
        # Thumb wrapping over the fist and the second straight wrist edge.
        pygame.draw.polygon(
            glyph,
            color,
            scaled_points(
                [
                    (19, 24), (24, 26), (29, 30), (32, 28),
                    (34, 23), (35, 22), (34, 31), (29, 35),
                    (29, 38), (23, 38), (23, 32), (20, 28),
                ]
            ),
        )
        # Negative crease under the thumb, matching the reference's cutout.
        pygame.draw.polygon(
            glyph,
            (11, 12, 16),
            scaled_points(
                [
                    (16, 22), (18, 24), (23, 25), (25, 23),
                    (25, 26), (22, 28), (18, 26), (15, 24),
                ]
            ),
        )

        icon_surface.blit(
            pygame.transform.smoothscale(glyph, (38, 38)),
            (3, 3),
        )
    elif kind == "dexterity":
        # Running figure with three speed trails, based on the reference.
        scale = 4
        glyph = pygame.Surface((44 * scale, 44 * scale), pygame.SRCALPHA)

        def scaled_point(point):
            return point[0] * scale, point[1] * scale

        def draw_limb(start, end, width):
            start = scaled_point(start)
            end = scaled_point(end)
            radius = width * scale // 2
            pygame.draw.line(glyph, color, start, end, width * scale)
            pygame.draw.circle(glyph, color, start, radius)
            pygame.draw.circle(glyph, color, end, radius)

        pygame.draw.circle(
            glyph,
            color,
            scaled_point((29, 10)),
            4 * scale,
        )
        draw_limb((23, 16), (21, 25), 6)
        draw_limb((21, 17), (15, 15), 4)
        draw_limb((15, 15), (10, 16), 4)
        draw_limb((24, 17), (28, 21), 4)
        draw_limb((28, 21), (35, 21), 4)
        draw_limb((21, 25), (15, 30), 6)
        draw_limb((15, 30), (11, 35), 5)
        draw_limb((22, 25), (27, 31), 6)
        draw_limb((27, 31), (33, 36), 5)

        for start, end, width in (
            ((7, 14), (14, 14), 2),
            ((6, 21), (13, 21), 2),
            ((8, 28), (14, 28), 2),
        ):
            pygame.draw.line(
                glyph,
                color,
                scaled_point(start),
                scaled_point(end),
                width * scale,
            )

        icon_surface.blit(
            pygame.transform.smoothscale(glyph, (38, 38)),
            (3, 3),
        )
    elif kind == "intelligence":
        # Centered brain with a consistent gap from the circular frame.
        for brain_center, radius in (
            ((15, 17), 5), ((20, 14), 5), ((25, 14), 5),
            ((30, 17), 5), ((14, 23), 5), ((18, 29), 5),
            ((24, 30), 5), ((29, 28), 5), ((31, 22), 5),
            ((22, 22), 9),
        ):
            pygame.draw.circle(icon_surface, color, brain_center, radius)
        dark = (12, 13, 17)
        pygame.draw.line(icon_surface, dark, (22, 12), (22, 32), 2)
        pygame.draw.arc(icon_surface, dark, (12, 15, 11, 10), 4.5, 1.4, 2)
        pygame.draw.arc(icon_surface, dark, (22, 15, 10, 10), 1.7, 4.8, 2)
        pygame.draw.arc(icon_surface, dark, (13, 22, 10, 10), 4.5, 1.5, 2)
        pygame.draw.arc(icon_surface, dark, (22, 22, 10, 9), 1.7, 4.8, 2)
    else:
        pygame.draw.polygon(
            icon_surface,
            color,
            [(22, 34), (10, 21), (12, 14), (18, 12), (22, 17),
             (26, 12), (32, 14), (34, 21)],
        )

    screen.blit(icon_surface, (center[0] - 22, center[1] - 22))


def _draw_upgrade_card(
    screen,
    text_font,
    rectangle,
    kind,
    key_label,
    title,
    description,
    value_text,
    accent_color,
    disabled,
    capped,
    hovered,
):
    if disabled:
        fill_color = (20, 20, 25)
        border_color = (51, 49, 56)
        text_color = (104, 101, 108)
    else:
        fill_color = (36, 35, 43) if hovered else (28, 28, 35)
        border_color = accent_color if hovered else (76, 72, 81)
        text_color = (224, 216, 204)

    pygame.draw.rect(screen, (8, 8, 11), rectangle.move(3, 4), border_radius=7)
    pygame.draw.rect(screen, fill_color, rectangle, border_radius=7)
    pygame.draw.rect(screen, border_color, rectangle, width=2, border_radius=7)
    pygame.draw.line(
        screen,
        (62, 59, 68) if not disabled else (35, 34, 40),
        (rectangle.x + 12, rectangle.y + 3),
        (rectangle.right - 12, rectangle.y + 3),
    )

    badge_rectangle = pygame.Rect(rectangle.x + 12, rectangle.y + 12, 30, 27)
    pygame.draw.rect(screen, (12, 12, 16), badge_rectangle, border_radius=4)
    pygame.draw.rect(screen, border_color, badge_rectangle, width=1, border_radius=4)
    badge = text_font.render(key_label, True, text_color)
    screen.blit(badge, badge.get_rect(center=badge_rectangle.center))

    if rectangle.width < 350:
        _draw_upgrade_icon(
            screen,
            kind,
            (rectangle.centerx, rectangle.y + 53),
            border_color,
        )
        title_surface = text_font.render(title, True, text_color)
        screen.blit(
            title_surface,
            title_surface.get_rect(
                center=(rectangle.centerx, rectangle.y + 91)
            ),
        )
        description_surface = text_font.render(
            description,
            True,
            (178, 173, 181) if not disabled else (96, 93, 101),
        )
        screen.blit(
            description_surface,
            description_surface.get_rect(
                center=(rectangle.centerx, rectangle.y + 128)
            ),
        )
        value_surface = text_font.render(
            value_text,
            True,
            accent_color if not disabled else (91, 88, 95),
        )
        screen.blit(
            value_surface,
            value_surface.get_rect(
                center=(rectangle.centerx, rectangle.y + 164)
            ),
        )
        pygame.draw.line(
            screen,
            (62, 59, 68) if not disabled else (35, 34, 40),
            (rectangle.x + 24, rectangle.bottom - 53),
            (rectangle.right - 24, rectangle.bottom - 53),
        )
        cost_text = "MAX" if capped else "1 GOLD"
        cost_surface = text_font.render(
            cost_text,
            True,
            (195, 151, 67) if not disabled else (86, 82, 75),
        )
        screen.blit(
            cost_surface,
            cost_surface.get_rect(
                center=(rectangle.centerx, rectangle.bottom - 27)
            ),
        )
        return

    _draw_upgrade_icon(
        screen,
        kind,
        (rectangle.x + 70, rectangle.centery),
        border_color,
    )
    title_surface = text_font.render(title, True, text_color)
    screen.blit(title_surface, (rectangle.x + 105, rectangle.y + 17))

    description_surface = text_font.render(
        description,
        True,
        (178, 173, 181) if not disabled else (96, 93, 101),
    )
    screen.blit(description_surface, (rectangle.x + 105, rectangle.y + 50))

    value_surface = text_font.render(
        value_text,
        True,
        accent_color if not disabled else (91, 88, 95),
    )
    screen.blit(value_surface, (rectangle.x + 105, rectangle.y + 82))

    cost_text = "MAX" if capped else "1 GOLD"
    cost_surface = text_font.render(
        cost_text,
        True,
        (195, 151, 67) if not disabled else (86, 82, 75),
    )
    screen.blit(
        cost_surface,
        cost_surface.get_rect(
            bottomright=(rectangle.right - 14, rectangle.bottom - 12)
        ),
    )


def draw_upgrade_screen(
    screen,
    title_font,
    text_font,
    gold_count,
    player_health,
    player_max_health,
    player_damage_min,
    player_damage_max,
    player_crit_chance,
    player_dodge_chance,
    player_critical_damage_multiplier,
    player_spell_power,
    attribute_ranks,
    message,
    mouse_position=None,
    show_intelligence=False,
):
    dark_overlay = pygame.Surface(
        (GAME_WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA,
    )
    dark_overlay.fill((0, 0, 0, 205))
    screen.blit(dark_overlay, (0, 0))

    panel_rectangle = pygame.Rect(
        170,
        66,
        940,
        588 if show_intelligence else 520,
    )
    pygame.draw.rect(
        screen,
        (6, 6, 9),
        panel_rectangle.move(6, 8),
        border_radius=10,
    )
    pygame.draw.rect(
        screen,
        (18, 18, 24),
        panel_rectangle,
        border_radius=10,
    )
    pygame.draw.rect(
        screen,
        (70, 68, 77),
        panel_rectangle,
        width=3,
        border_radius=10,
    )
    pygame.draw.rect(
        screen,
        (38, 37, 45),
        panel_rectangle.inflate(-12, -12),
        width=1,
        border_radius=7,
    )
    for corner in (
        panel_rectangle.topleft,
        panel_rectangle.topright,
        panel_rectangle.bottomleft,
        panel_rectangle.bottomright,
    ):
        pygame.draw.circle(screen, (10, 10, 13), corner, 6)
        pygame.draw.circle(screen, (116, 104, 82), corner, 2)

    title_surface = title_font.render(
        "DESCENT ALTAR",
        True,
        (188, 177, 157),
    )
    title_rectangle = title_surface.get_rect(
        center=(GAME_WIDTH // 2, 108)
    )
    screen.blit(title_surface, title_rectangle)

    instruction = (
        f"{gold_count} BLESSING{'S' if gold_count != 1 else ''} AVAILABLE"
    )
    instruction_surface = text_font.render(
        instruction,
        True,
        (211, 169, 77),
    )
    screen.blit(
        instruction_surface,
        instruction_surface.get_rect(center=(GAME_WIDTH // 2, 153)),
    )

    stats = (
        f"HP {player_health}/{player_max_health}     "
        f"DAMAGE {player_damage_min}-{player_damage_max}     "
        f"CRIT {round(player_crit_chance * 100)}%     "
        f"DODGE {round(player_dodge_chance * 100)}%"
    )
    stats_surface = text_font.render(
        stats,
        True,
        (184, 179, 187),
    )
    screen.blit(
        stats_surface,
        stats_surface.get_rect(center=(GAME_WIDTH // 2, 196)),
    )

    no_gold = gold_count <= 0
    strength_change = player_stat_changes_for_attribute_upgrade(
        "strength",
        attribute_ranks["strength"],
    )
    dexterity_change = player_stat_changes_for_attribute_upgrade(
        "dexterity",
        attribute_ranks["dexterity"],
    )
    vitality_change = player_stat_changes_for_attribute_upgrade(
        "vitality",
        attribute_ranks["vitality"],
    )
    cards = [
        (
            "strength", "1", "STRENGTH",
            f"Rank {attribute_ranks['strength']} | Physical attack damage",
            f"{player_damage_min}-{player_damage_max}  >  "
            f"{player_damage_min + strength_change.damage_min}-"
            f"{player_damage_max + strength_change.damage_max}",
            (184, 82, 64),
        ),
        (
            "dexterity", "2", "DEXTERITY",
            f"Rank {attribute_ranks['dexterity']} | Crit damage "
            f"x{player_critical_damage_multiplier:.1f} > "
            f"x{player_critical_damage_multiplier + dexterity_change.critical_damage_multiplier:.1f}",
            f"C/D {round(player_crit_chance * 100)}/"
            f"{round(player_dodge_chance * 100)}% > "
            f"{round((player_crit_chance + dexterity_change.crit_chance) * 100)}/"
            f"{round((player_dodge_chance + dexterity_change.dodge_chance) * 100)}%",
            (190, 151, 69),
        ),
    ]
    if show_intelligence:
        intelligence_change = player_stat_changes_for_attribute_upgrade(
            "intelligence",
            attribute_ranks["intelligence"],
        )
        cards.append(
            (
                "intelligence", "3", "INTELLIGENCE",
                f"Rank {attribute_ranks['intelligence']} | Magical attack power",
                f"{player_spell_power}  >  "
                f"{player_spell_power + intelligence_change.spell_power} SPELL POWER",
                (92, 128, 185),
            )
        )
    cards.append(
        (
            "vitality", "4" if show_intelligence else "3", "VITALITY",
            f"Rank {attribute_ranks['vitality']} | Maximum health",
            f"{player_max_health}  >  "
            f"{player_max_health + vitality_change.max_health} HP",
            (139, 74, 89),
        )
    )
    card_rectangles = get_upgrade_card_rectangles(show_intelligence)
    for (
        kind,
        key_label,
        title,
        description,
        value_text,
        accent_color,
    ) in cards:
        capped = attribute_ranks[kind] >= MAX_ATTRIBUTE_RANK
        if capped:
            value_text = f"RANK {attribute_ranks[kind]} | MAXIMUM"
        rectangle = card_rectangles[kind]
        hovered = (
            mouse_position is not None
            and rectangle.collidepoint(mouse_position)
        )
        _draw_upgrade_card(
            screen,
            text_font,
            rectangle,
            kind,
            key_label,
            title,
            description,
            value_text,
            accent_color,
            no_gold or capped,
            capped,
            hovered,
        )

    if message:
        message_surface = text_font.render(
            message,
            True,
            (211, 169, 77),
        )
        message_rectangle = message_surface.get_rect(
            center=(
                GAME_WIDTH // 2,
                565 if show_intelligence else 516,
            )
        )
        screen.blit(message_surface, message_rectangle)

    footer = (
        f"[ENTER] KEEP {gold_count} GOLD AND DESCEND"
        if gold_count > 0
        else "DESCENDING..."
    )
    footer_surface = text_font.render(footer, True, (171, 166, 174))
    screen.blit(
        footer_surface,
        footer_surface.get_rect(
            center=(
                GAME_WIDTH // 2,
                620 if show_intelligence else 554,
            )
        ),
    )


def _awakening_eye_openness(elapsed_ms):
    if elapsed_ms < AWAKENING_OPEN_START_MS:
        return 0.0
    if elapsed_ms < AWAKENING_OPEN_END_MS:
        return _smooth_progress(
            elapsed_ms,
            AWAKENING_OPEN_START_MS,
            AWAKENING_OPEN_END_MS,
        )
    if elapsed_ms < AWAKENING_HOLD_END_MS:
        return 1.0
    if elapsed_ms < AWAKENING_FADE_END_MS:
        return 1.0 - _smooth_progress(
            elapsed_ms,
            AWAKENING_HOLD_END_MS,
            AWAKENING_FADE_END_MS,
        )
    if elapsed_ms < AWAKENING_SECOND_OPEN_START_MS:
        return 0.0
    if elapsed_ms < AWAKENING_SECOND_OPEN_END_MS:
        return _smooth_progress(
            elapsed_ms,
            AWAKENING_SECOND_OPEN_START_MS,
            AWAKENING_SECOND_OPEN_END_MS,
        )
    if elapsed_ms < AWAKENING_RECOVERY_BLINK_START_MS:
        return 1.0
    recovery_midpoint = (
        AWAKENING_RECOVERY_BLINK_START_MS
        + AWAKENING_RECOVERY_BLINK_END_MS
    ) // 2
    if elapsed_ms < recovery_midpoint:
        blink_progress = _smooth_progress(
            elapsed_ms,
            AWAKENING_RECOVERY_BLINK_START_MS,
            recovery_midpoint,
        )
        return 1.0 - blink_progress
    if elapsed_ms < AWAKENING_RECOVERY_BLINK_END_MS:
        blink_progress = _smooth_progress(
            elapsed_ms,
            recovery_midpoint,
            AWAKENING_RECOVERY_BLINK_END_MS,
        )
        return blink_progress
    return 1.0


def _draw_awakening_eyelids(screen, openness):
    if openness >= 1:
        return
    aperture_height = max(
        0,
        round(GAME_HEIGHT * 1.72 * max(0, openness)),
    )
    eyelids = pygame.Surface(
        (GAME_WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA,
    )
    eyelids.fill((1, 1, 3, 255))
    if aperture_height > 0:
        pygame.draw.ellipse(
            eyelids,
            (0, 0, 0, 0),
            (
                -GAME_WIDTH // 4,
                GAME_HEIGHT // 2 - aperture_height // 2,
                GAME_WIDTH * 3 // 2,
                aperture_height,
            ),
        )
    screen.blit(eyelids, (0, 0))


def _draw_awakening_background(screen, image, elapsed_ms, detailed):
    if not detailed:
        screen.blit(image, (0, 0))
        return
    focus_progress = _smooth_progress(
        elapsed_ms,
        AWAKENING_SECOND_OPEN_START_MS,
        AWAKENING_OLD_MAN_APPROACH_END_MS,
    )
    scale = 1.0 + 0.025 * focus_progress
    size = (
        round(GAME_WIDTH * scale),
        round(GAME_HEIGHT * scale),
    )
    pushed_image = pygame.transform.scale(image, size)
    breath_y = round(math.sin(elapsed_ms / 620) * 3 * focus_progress)
    screen.blit(
        pushed_image,
        (
            (GAME_WIDTH - size[0]) // 2,
            (GAME_HEIGHT - size[1]) // 2 + breath_y,
        ),
    )

def _draw_awakening_dialogue(
    screen,
    intro_title_font,
    intro_text_font,
    elapsed_ms,
):
    start = AWAKENING_DIALOGUE_START_MS
    dialogue = (
        (
            start,
            start + 2600,
            "You have learned how to survive.",
        ),
        (
            start + 2900,
            start + 5400,
            "But survival is not an answer.",
        ),
        (start + 5700, start + 7300, "Tell me..."),
        (
            start + 7600,
            CLASS_SELECTION_READY_MS,
            "Who are you?",
        ),
    )
    for start_ms, end_ms, line in dialogue:
        if not start_ms <= elapsed_ms < end_ms:
            continue
        fade_in = _smooth_progress(elapsed_ms, start_ms, start_ms + 380)
        fade_out = 1.0
        if elapsed_ms > end_ms - 360:
            fade_out = 1.0 - _smooth_progress(
                elapsed_ms,
                end_ms - 360,
                end_ms,
            )
        character_count = max(0, (elapsed_ms - start_ms) // 46)
        visible_line = line[:character_count]
        font = intro_title_font if line == "Who are you?" else intro_text_font
        color = (
            (151, 125, 76)
            if line == "Who are you?"
            else (184, 176, 160)
        )
        text_surface = font.render(visible_line, True, color)
        text_surface.set_alpha(round(255 * fade_in * fade_out))
        shadow = font.render(visible_line, True, (1, 1, 2))
        shadow.set_alpha(round(230 * fade_in * fade_out))
        rectangle = text_surface.get_rect(center=(GAME_WIDTH // 2, 648))
        screen.blit(shadow, rectangle.move(3, 3))
        screen.blit(text_surface, rectangle)
        return


def draw_class_selection_screen(
    screen,
    intro_title_font,
    intro_text_font,
    class_title_font,
    class_text_font,
    sprites,
    elapsed_ms,
    mouse_position,
    selected_class=None,
    choice_elapsed_ms=None,
    *,
    attribute_ranks,
):
    screen.fill((1, 1, 3))

    detailed = elapsed_ms >= AWAKENING_SECOND_OPEN_START_MS
    background = sprites[
        "awakening_act_two" if detailed else "awakening_act_one"
    ]
    _draw_awakening_background(
        screen,
        background,
        elapsed_ms,
        detailed,
    )
    draw_awakening_old_man(
        screen,
        sprites,
        elapsed_ms,
        choice_elapsed_ms,
    )

    if elapsed_ms < CLASS_SELECTION_READY_MS:
        _draw_awakening_dialogue(
            screen,
            intro_title_font,
            intro_text_font,
            elapsed_ms,
        )
    else:
        hovered_class = draw_awakening_choices(
            screen,
            sprites,
            elapsed_ms,
            mouse_position,
            selected_class,
            choice_elapsed_ms,
            attribute_ranks,
        )

        if selected_class is None and hovered_class is not None:
            response = intro_text_font.render(
                OLD_MAN_RESPONSES[hovered_class],
                True,
                (184, 176, 160),
            )
            response.set_alpha(
                round(
                    255 * _smooth_progress(
                        elapsed_ms,
                        CLASS_SELECTION_READY_MS,
                        CLASS_SELECTION_READY_MS + 520,
                    )
                )
            )
            screen.blit(
                response,
                response.get_rect(
                    center=(GAME_WIDTH // 2, 112)
                ),
            )

        elif selected_class is not None:
            answer = intro_title_font.render(
                "We shall see.",
                True,
                (184, 176, 160),
            )
            answer.set_alpha(
                round(
                    255 * _smooth_progress(
                        choice_elapsed_ms,
                        350,
                        850,
                    )
                )
            )
            screen.blit(
                answer,
                answer.get_rect(
                    center=(GAME_WIDTH // 2, 112)
                ),
            )

    _draw_awakening_eyelids(
        screen,
        _awakening_eye_openness(elapsed_ms),
    )

    if choice_elapsed_ms is not None:
        fade = _smooth_progress(
            choice_elapsed_ms,
            CLASS_SELECTION_CHOICE_END_MS - 650,
            CLASS_SELECTION_CHOICE_END_MS,
        )
        if fade > 0:
            fade_surface = pygame.Surface(
                (GAME_WIDTH, GAME_HEIGHT),
                pygame.SRCALPHA,
            )
            fade_surface.fill((1, 1, 3, round(255 * fade)))
            screen.blit(fade_surface, (0, 0))


def _smooth_progress(elapsed_ms, start_ms, end_ms):
    progress = max(
        0.0,
        min(1.0, (elapsed_ms - start_ms) / (end_ms - start_ms)),
    )
    return progress * progress * (3 - 2 * progress)


def _blit_with_alpha(screen, image, position, alpha):
    if alpha >= 255:
        screen.blit(image, position)
        return

    faded_image = image.copy()
    faded_image.set_alpha(max(0, min(255, round(alpha))))
    screen.blit(faded_image, position)


def _draw_act_three_narrative(
    screen,
    narrative_font,
    elapsed_ms,
):
    lines = (
        "THE SECOND VEIL FALLS.",
        "The world returns sharper than before.",
        "You begin to see what was hidden.",
        "Again, a silhouette waits at the end of the Crypta.",
        "Who is it?",
        "Who are you?",
    )
    line_delay_ms = 1400
    character_delay_ms = 55
    active_lines = [
        (index, line)
        for index, line in enumerate(lines)
        if (
            elapsed_ms
            >= ACT_THREE_NARRATIVE_START_MS
            + index * line_delay_ms
        )
    ]

    if not active_lines:
        return

    page_rectangle = pygame.Rect(140, 72, 1000, 575)
    page_shadow = page_rectangle.move(8, 10)
    pygame.draw.rect(
        screen,
        (6, 4, 3),
        page_shadow,
        border_radius=6,
    )
    pygame.draw.rect(
        screen,
        (27, 21, 17),
        page_rectangle,
        border_radius=6,
    )
    pygame.draw.rect(
        screen,
        (104, 76, 48),
        page_rectangle,
        width=2,
        border_radius=6,
    )
    inner_rectangle = page_rectangle.inflate(-22, -22)
    pygame.draw.rect(
        screen,
        (61, 46, 34),
        inner_rectangle,
        width=1,
        border_radius=4,
    )
    ornament_y = page_rectangle.y + 92
    pygame.draw.line(
        screen,
        (83, 58, 39),
        (page_rectangle.x + 60, ornament_y),
        (page_rectangle.right - 60, ornament_y),
        1,
    )
    pygame.draw.polygon(
        screen,
        (151, 64, 48),
        (
            (GAME_WIDTH // 2, ornament_y - 5),
            (GAME_WIDTH // 2 + 5, ornament_y),
            (GAME_WIDTH // 2, ornament_y + 5),
            (GAME_WIDTH // 2 - 5, ornament_y),
        ),
    )

    for visible_index, (line_index, line) in enumerate(active_lines):
        line_started_at = (
            ACT_THREE_NARRATIVE_START_MS
            + line_index * line_delay_ms
        )
        visible_character_count = max(
            0,
            int(
                (elapsed_ms - line_started_at)
                / character_delay_ms
            ),
        )
        visible_text = line[:visible_character_count]

        if not visible_text:
            continue

        color = (
            (205, 67, 59)
            if line_index == 0
            else TEXT_COLOR
        )
        line_surface = narrative_font.render(
            visible_text,
            True,
            color,
        )
        line_y = (
            page_rectangle.y + 47
            if line_index == 0
            else page_rectangle.y + 135 + (line_index - 1) * 67
        )
        screen.blit(
            line_surface,
            (page_rectangle.x + 60, line_y),
        )

    if elapsed_ms >= ACT_THREE_NARRATIVE_READY_MS:
        prompt_alpha = (
            255
            if (elapsed_ms // 650) % 2 == 0
            else 115
        )
        prompt = narrative_font.render(
            "CLICK / SPACE TO OPEN YOUR EYES",
            True,
            (171, 129, 83),
        )
        prompt.set_alpha(prompt_alpha)
        screen.blit(
            prompt,
            prompt.get_rect(
                bottomright=(
                    page_rectangle.right - 58,
                    page_rectangle.bottom - 34,
                )
            ),
        )


def get_act_three_debug_class_rectangles():
    button_width = 280
    button_height = 94
    gap = 34
    total_width = button_width * 3 + gap * 2
    left = (GAME_WIDTH - total_width) // 2
    top = 335

    return {
        "warrior": pygame.Rect(
            left,
            top,
            button_width,
            button_height,
        ),
        "rogue": pygame.Rect(
            left + button_width + gap,
            top,
            button_width,
            button_height,
        ),
        "mage": pygame.Rect(
            left + (button_width + gap) * 2,
            top,
            button_width,
            button_height,
        ),
    }


def draw_act_three_debug_class_selection(
    screen,
    title_font,
    heading_font,
    text_font,
    mouse_position,
):
    screen.fill((5, 4, 8))
    title = title_font.render(
        "ACT III AWAKENING",
        True,
        TEXT_COLOR,
    )
    screen.blit(
        title,
        title.get_rect(center=(GAME_WIDTH // 2, 165)),
    )
    subtitle = text_font.render(
        "DEBUG: CHOOSE THE CLASS TO PREVIEW",
        True,
        (143, 134, 151),
    )
    screen.blit(
        subtitle,
        subtitle.get_rect(center=(GAME_WIDTH // 2, 235)),
    )

    class_colors = {
        "warrior": (190, 57, 52),
        "rogue": (137, 75, 175),
        "mage": (67, 110, 190),
    }
    class_labels = {
        "warrior": "[1] WARRIOR",
        "rogue": "[2] ROGUE",
        "mage": "[3] MAGE",
    }

    for class_name, rectangle in (
        get_act_three_debug_class_rectangles().items()
    ):
        hovered = (
            mouse_position is not None
            and rectangle.collidepoint(mouse_position)
        )
        color = class_colors[class_name]
        pygame.draw.rect(
            screen,
            (22, 17, 25) if hovered else (13, 11, 16),
            rectangle,
            border_radius=8,
        )
        pygame.draw.rect(
            screen,
            color,
            rectangle,
            width=3 if hovered else 2,
            border_radius=8,
        )
        label = heading_font.render(
            class_labels[class_name],
            True,
            color if not hovered else TEXT_COLOR,
        )
        screen.blit(
            label,
            label.get_rect(center=rectangle.center),
        )

    hint = text_font.render(
        "CLICK A BUTTON OR PRESS 1 / 2 / 3",
        True,
        (117, 108, 125),
    )
    screen.blit(
        hint,
        hint.get_rect(center=(GAME_WIDTH // 2, 510)),
    )


def draw_act_three_awakening(
    screen,
    assets,
    narrative_font,
    narrative_elapsed_ms,
    visual_elapsed_ms,
    player_class,
):
    screen.fill((0, 0, 0))

    if visual_elapsed_ms is None:
        _draw_act_three_narrative(
            screen,
            narrative_font,
            narrative_elapsed_ms,
        )
        return

    elapsed_ms = visual_elapsed_ms

    background = assets["background"]
    camera_progress = _smooth_progress(
        elapsed_ms,
        ACT_THREE_EYES_OPEN_END_MS,
        ACT_THREE_CAMERA_END_MS,
    )
    background_overflow = max(
        0,
        background.get_height() - GAME_HEIGHT,
    )
    background_position = (
        (GAME_WIDTH - background.get_width()) // 2,
        -round(background_overflow * camera_progress),
    )
    screen.blit(background, background_position)

    hands_progress = _smooth_progress(
        elapsed_ms,
        ACT_THREE_HANDS_RISE_START_MS,
        ACT_THREE_HANDS_RISE_END_MS,
    )

    if hands_progress > 0:
        hands_class = (
            player_class
            if player_class in ("warrior", "rogue", "mage")
            else "warrior"
        )
        open_hands = assets[f"{hands_class}_hands_open"]
        clenched_hands = assets[
            f"{hands_class}_hands_clenched"
        ]
        hands_final_y = GAME_HEIGHT - open_hands.get_height()
        hands_start_y = hands_final_y + 300
        hands_y = round(
            hands_start_y
            + (hands_final_y - hands_start_y) * hands_progress
        )
        hands_position = (
            (GAME_WIDTH - open_hands.get_width()) // 2,
            hands_y,
        )

        if elapsed_ms < ACT_THREE_HANDS_HOLD_END_MS:
            _blit_with_alpha(
                screen,
                open_hands,
                hands_position,
                255 * hands_progress,
            )
        elif elapsed_ms < ACT_THREE_CLENCH_END_MS:
            clench_progress = _smooth_progress(
                elapsed_ms,
                ACT_THREE_HANDS_HOLD_END_MS,
                ACT_THREE_CLENCH_END_MS,
            )

            if clench_progress < 0.5:
                screen.blit(open_hands, hands_position)
            else:
                screen.blit(clenched_hands, hands_position)

            crossfade_darkness = pygame.Surface(
                (GAME_WIDTH, GAME_HEIGHT),
                pygame.SRCALPHA,
            )
            crossfade_darkness.fill(
                (
                    0,
                    0,
                    0,
                    round(225 * (1 - abs(2 * clench_progress - 1))),
                )
            )
            screen.blit(crossfade_darkness, (0, 0))
        else:
            screen.blit(clenched_hands, hands_position)

    opening_progress = _smooth_progress(
        elapsed_ms,
        ACT_THREE_EYES_OPEN_START_MS,
        ACT_THREE_EYES_OPEN_END_MS,
    )

    if opening_progress < 1:
        aperture_height = max(
            2,
            round(GAME_HEIGHT * 1.8 * opening_progress),
        )
        eyelids = pygame.Surface(
            (GAME_WIDTH, GAME_HEIGHT),
            pygame.SRCALPHA,
        )
        eyelids.fill((0, 0, 0, 255))
        pygame.draw.ellipse(
            eyelids,
            (0, 0, 0, 0),
            (
                -GAME_WIDTH // 4,
                GAME_HEIGHT // 2 - aperture_height // 2,
                GAME_WIDTH * 3 // 2,
                aperture_height,
            ),
        )
        screen.blit(eyelids, (0, 0))

    if elapsed_ms > ACT_THREE_FINAL_HOLD_END_MS:
        fade_progress = _smooth_progress(
            elapsed_ms,
            ACT_THREE_FINAL_HOLD_END_MS,
            ACT_THREE_AWAKENING_END_MS,
        )
        fade_overlay = pygame.Surface(
            (GAME_WIDTH, GAME_HEIGHT),
            pygame.SRCALPHA,
        )
        fade_overlay.fill((0, 0, 0, round(255 * fade_progress)))
        screen.blit(fade_overlay, (0, 0))


def _subclass_card_rectangles():
    card_width = 410
    card_height = 475
    gap = 50
    total_width = card_width * 2 + gap
    left = (GAME_WIDTH - total_width) // 2
    top = 155

    return (
        pygame.Rect(
            left,
            top,
            card_width,
            card_height,
        ),
        pygame.Rect(
            left + card_width + gap,
            top,
            card_width,
            card_height,
        ),
    )


def get_subclass_selection_rectangles(
    player_class="warrior",
):
    first_rectangle, second_rectangle = (
        _subclass_card_rectangles()
    )

    if player_class == "rogue":
        return {
            "assassin": first_rectangle,
            "archer": second_rectangle,
        }
    if player_class == "mage":
        return {
            "warlock": first_rectangle,
            "summoner": second_rectangle,
        }

    return {
        "berserker": first_rectangle,
        "paladin": second_rectangle,
    }


def draw_subclass_selection_screen(
    screen,
    title_font,
    heading_font,
    text_font,
    assets,
    mouse_position,
    selected_subclass,
    player_class,
):
    background = assets["background"]
    screen.blit(
        background,
        (
            (GAME_WIDTH - background.get_width()) // 2,
            GAME_HEIGHT - background.get_height(),
        ),
    )
    veil = pygame.Surface(
        (GAME_WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA,
    )
    veil.fill((3, 2, 5, 205))
    screen.blit(veil, (0, 0))

    is_rogue = player_class == "rogue"
    is_mage = player_class == "mage"
    title_color = (
        (70, 137, 230)
        if is_rogue
        else (163, 88, 221)
        if is_mage
        else (214, 70, 62)
    )
    title = title_font.render(
        "THE SECOND VEIL FALLS",
        True,
        title_color,
    )
    screen.blit(
        title,
        title.get_rect(center=(GAME_WIDTH // 2, 60)),
    )
    prompt = text_font.render(
        (
            "Choose what the rogue will become."
            if is_rogue
            else "Choose what the mage will become."
            if is_mage
            else "Choose what the warrior will become."
        ),
        True,
        TEXT_COLOR,
    )
    screen.blit(
        prompt,
        prompt.get_rect(center=(GAME_WIDTH // 2, 112)),
    )

    if is_rogue:
        card_configs = (
            {
                "name": "assassin",
                "number": 1,
                "title": "ASSASSIN",
                "description": (
                    "One blade. One breath. No witness."
                ),
                "portrait": "assassin_portrait",
                "color": (75, 143, 238),
                "dim_color": (39, 72, 116),
                "background": (9, 13, 22),
            },
            {
                "name": "archer",
                "number": 2,
                "title": "ARCHER",
                "description": (
                    "One arrow. One heartbeat. No escape."
                ),
                "portrait": "archer_portrait",
                "color": (105, 151, 76),
                "dim_color": (55, 79, 47),
                "background": (11, 17, 13),
            },
        )
    elif is_mage:
        card_configs = (
            {
                "name": "warlock",
                "number": 1,
                "title": "WARLOCK",
                "description": (
                    "One pact. Endless consequence."
                ),
                "portrait": "warlock_portrait",
                "color": (176, 91, 232),
                "dim_color": (88, 51, 111),
                "background": (17, 10, 22),
            },
            {
                "name": "summoner",
                "number": 2,
                "title": "SUMMONER",
                "description": (
                    "One call. Another world answers."
                ),
                "portrait": "summoner_portrait",
                "color": (77, 184, 193),
                "dim_color": (46, 94, 101),
                "background": (8, 18, 21),
            },
        )
    else:
        card_configs = (
            {
                "name": "berserker",
                "number": 1,
                "title": "BERSERKER",
                "description": "Two blades. No restraint.",
                "portrait": "berserker_portrait",
                "color": (225, 78, 62),
                "dim_color": (112, 54, 50),
                "background": (24, 13, 15),
            },
            {
                "name": "paladin",
                "number": 2,
                "title": "PALADIN",
                "description": "Sword. Shield. Unbroken oath.",
                "portrait": "paladin_portrait",
                "color": (218, 178, 86),
                "dim_color": (103, 87, 55),
                "background": (15, 16, 18),
            },
        )

    card_rectangles = _subclass_card_rectangles()

    for card_config, rectangle in zip(
        card_configs,
        card_rectangles,
    ):
        subclass = card_config["name"]
        hovered = (
            selected_subclass is None
            and mouse_position is not None
            and rectangle.collidepoint(mouse_position)
        )
        border_color = (
            card_config["color"]
            if hovered or selected_subclass == subclass
            else card_config["dim_color"]
        )
        pygame.draw.rect(
            screen,
            card_config["background"],
            rectangle,
            border_radius=12,
        )
        pygame.draw.rect(
            screen,
            border_color,
            rectangle,
            width=3,
            border_radius=12,
        )
        portrait = assets[card_config["portrait"]]
        screen.blit(
            portrait,
            portrait.get_rect(
                center=(rectangle.centerx, 285)
            ),
        )
        card_title = heading_font.render(
            (
                f"[{card_config['number']}] "
                f"{card_config['title']}"
            ),
            True,
            card_config["color"],
        )
        screen.blit(
            card_title,
            card_title.get_rect(
                center=(rectangle.centerx, 445)
            ),
        )
        description = text_font.render(
            card_config["description"],
            True,
            TEXT_COLOR,
        )
        screen.blit(
            description,
            description.get_rect(
                center=(rectangle.centerx, 490)
            ),
        )
        stat_changes = describe_player_stat_changes(
            player_stat_changes_between(
                CLASS_BASE_STATS[player_class],
                SUBCLASS_BASE_STATS[subclass],
            )
        )
        for index, stat_change in enumerate(stat_changes):
            stat_surface = text_font.render(
                stat_change,
                True,
                card_config["color"],
            )
            screen.blit(
                stat_surface,
                stat_surface.get_rect(
                    center=(rectangle.centerx, 525 + index * 24)
                ),
            )
        action_label = (
            "PATH CHOSEN"
            if selected_subclass == subclass
            else "CLICK TO CHOOSE"
            if hovered
            else f"PRESS {card_config['number']}"
        )
        action_surface = text_font.render(
            action_label,
            True,
            border_color,
        )
        screen.blit(
            action_surface,
            action_surface.get_rect(
                center=(rectangle.centerx, 585)
            ),
        )

