import json
from pathlib import Path

import pygame

from acts.act_two.presentation.death_scene import (
    ACT_TWO_OLD_MAN_DIALOGUE_MS,
)
from presentation.figma_ui import (
    draw_figma_text,
    figma_rect,
    get_figma_font,
)
from presentation.hud import fit_text_to_width


_PROJECT_ROOT = Path(__file__).resolve().parents[3]

_DIALOGUE_READ_MS = 3000
_INPUT_GUARD_MS = 250

_ENEMY_SPRITES = {
    "goblin": "goblin",
    "brute": "brute",
    "archer": "archer",
    "sentinel": "sentinel_idle",
    "priest": "priest_idle",
    "priest_ghost": "priest_ghost_idle",
    "mimic": "mimic",
}


def load_act_two_death_score(sprites):
    layout_path = (
        _PROJECT_ROOT
        / "assets/ui/layouts/act_2/death_score.json"
    )

    with layout_path.open(encoding="utf-8") as file:
        layout = json.load(file)

    if (
        layout["screen"] != "death_score"
        or layout["act"] != 2
        or layout["frame"]["width"] != 1280
        or layout["frame"]["height"] != 720
    ):
        raise ValueError(
            "Expected a DeathScore_Act2 layout at 1280x720."
        )

    background_path = (
        _PROJECT_ROOT
        / "assets/sprites/ui/act_2/ui_v.0.2/background.png"
    )
    background = pygame.image.load(
        str(background_path)
    ).convert_alpha()

    background_rectangle = figma_rect(
        layout["background"]
    )
    background = pygame.transform.scale(
        background,
        background_rectangle.size,
    )

    icons = {}

    for slot_id, slot in layout["kills"]["slots"].items():
        sprite_name = _ENEMY_SPRITES[slot["enemy_type"]]
        source = sprites[sprite_name]

        bounds = source.get_bounding_rect()
        if bounds.width > 0 and bounds.height > 0:
            source = source.subsurface(bounds).copy()

        target = figma_rect(slot["icon"])
        scale = min(
            target.width / source.get_width(),
            target.height / source.get_height(),
        )
        size = (
            max(1, round(source.get_width() * scale)),
            max(1, round(source.get_height() * scale)),
        )

        icons[slot_id] = pygame.transform.scale(
            source,
            size,
        )

    return layout, {
        "background": background,
        "icons": icons,
    }


def handle_act_two_death_event(
    event,
    game_state,
    layout,
    mouse_position,
    current_time,
):
    state = game_state.player.act_two

    keyboard_press = (
        event.type == pygame.KEYDOWN
        and not getattr(event, "repeat", False)
        and not getattr(event, "automatic_movement", False)
    )
    mouse_press = (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button in (1, 2, 3)
    )

    if not keyboard_press and not mouse_press:
        return None

    if current_time < state.death_input_unlock_at:
        return None

    if state.death_score_open:
        menu_rectangle = figma_rect(
            layout["to_the_menu"]["hitbox"]
        )

        menu_clicked = (
            mouse_press
            and event.button == 1
            and mouse_position is not None
            and menu_rectangle.collidepoint(mouse_position)
        )
        menu_confirmed = (
            keyboard_press
            and event.key in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
            )
        )

        if menu_clicked or menu_confirmed:
            return "menu"

        return None

    started_at = game_state.player.death_animation_started_at
    if started_at < 0:
        return None

    elapsed = max(0, current_time - started_at)

    # Само появление старика пока не пропускаем.
    if elapsed < ACT_TWO_OLD_MAN_DIALOGUE_MS:
        return None

    dialogue_finished = (
        state.death_dialogue_skipped
        or elapsed >= (
            ACT_TWO_OLD_MAN_DIALOGUE_MS + _DIALOGUE_READ_MS
        )
    )

    if dialogue_finished:
        state.death_score_open = True
    else:
        state.death_dialogue_skipped = True

    state.death_input_unlock_at = (
        current_time + _INPUT_GUARD_MS
    )

    return None


def draw_act_two_death_score(
    screen,
    game_state,
    layout,
    assets,
    mouse_position,
):
    screen.fill((8, 8, 10))

    screen.blit(
        assets["background"],
        figma_rect(layout["background"]),
    )

    stats = game_state.run_stats

    cause = stats.death_cause

    if cause:
        enemy_name, separator, enemy_number = cause.rpartition(" ")
        if separator and enemy_number.isdecimal():
            cause = enemy_name

    special_causes = {
        "fire": "Consumed by fire",
        "floor spikes": "Impaled by spikes",
        "brute aftershock": "Crushed by aftershock",
        "projectile": "Slain by a projectile",
        "unknown": "The hero has fallen",
    }

    if cause is None:
        death_reason = "The hero has fallen"
    else:
        death_reason = special_causes.get(
            cause,
            f"Slain by {cause}",
        )

    reason_spec = layout["death_reason"]
    reason_rectangle = figma_rect(reason_spec["rect"])
    death_reason = fit_text_to_width(
        get_figma_font(reason_spec),
        death_reason,
        reason_rectangle.width,
    )

    draw_figma_text(screen, layout["title"])
    draw_figma_text(
        screen,
        reason_spec,
        text_override=death_reason,
    )

    draw_figma_text(screen, layout["stats"]["heading"])

    values = {
        "floors_cleared": len(stats.completed_floors),
        "level_reached": game_state.player.level,
        "turns_taken": stats.turns_taken,
        "enemies_killed": sum(stats.kills_by_type.values()),
        "gold_earned": stats.gold_earned,
        "gold_spent": stats.gold_spent,
        "chests_opened": stats.chests_opened,
        "consumables_used": stats.consumables_used,
    }

    for stat_id, row in layout["stats"]["rows"].items():
        draw_figma_text(screen, row["label"])
        draw_figma_text(
            screen,
            row["value"],
            text_override=str(values.get(stat_id, "--")),
        )

    draw_figma_text(screen, layout["kills"]["heading"])

    for slot_id, slot in layout["kills"]["slots"].items():
        icon_rectangle = figma_rect(slot["icon"])
        icon = assets["icons"][slot_id]

        screen.blit(
            icon,
            icon.get_rect(center=icon_rectangle.center),
        )

        draw_figma_text(screen, slot["name"])
        draw_figma_text(
            screen,
            slot["count"],
            text_override=str(
                stats.kills_by_type.get(
                    slot["enemy_type"],
                    0,
                )
            ),
        )

    button = layout["to_the_menu"]
    button_rectangle = figma_rect(button["hitbox"])

    hovered = (
        mouse_position is not None
        and button_rectangle.collidepoint(mouse_position)
    )

    draw_figma_text(
        screen,
        button["text"],
        color_override=(235, 211, 168) if hovered else None,
    )