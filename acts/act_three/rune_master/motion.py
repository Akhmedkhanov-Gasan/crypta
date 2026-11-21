import math
from dataclasses import dataclass

import pygame

from acts.act_three.rune_master.runtime import PHASE_DURATIONS, visible_cards
from presentation.figma_ui import figma_rect


@dataclass(frozen=True)
class CardPose:
    index: int
    rect: pygame.Rect
    mist: float
    alpha: int
    position: tuple[float, float]


def _ease(value):
    value = max(0.0, min(1.0, value))
    return value * value * value * (value * (value * 6 - 15) + 10)


def _center(layout, count, index):
    area = figma_rect(layout["slots_container"])
    width = layout["slots"]["slot_01"]["rect"]["width"]
    spacing = min(width, area.width / max(1, count))
    return area.centerx + (index - (count - 1) / 2) * spacing, area.centery


def card_poses(menu, layout, current_time):
    cards = visible_cards(menu)
    duration = PHASE_DURATIONS.get(menu.phase, 1)
    progress = max(0.0, min(1.0, (current_time - menu.started_at) / duration))
    eased = _ease(progress)
    poses = []
    confirming = menu.phase in ("confirming", "confirmed", "confirmation_fade")
    selection_progress = _ease((current_time - menu.selection_started_at) / 180)
    has_selection = menu.page == "choices" and menu.selected_choice is not None
    selection_presence = (1 if menu.previous_choice is not None else selection_progress) if has_selection else 0
    scale = layout["frame"]["width"] / 1280
    for index in range(len(cards)):
        if confirming and menu.phase != "confirming" and index != menu.selected_choice:
            continue
        spec = layout["slots"][f"slot_{index + 1:02d}"]
        target = _center(layout, len(cards), index)
        x, y = target
        float_weight = 1.0
        previous_weight = float(menu.previous_choice == index) if has_selection else 0
        selected_weight = float(menu.selected_choice == index) if has_selection else 0
        selection_weight = previous_weight + (selected_weight - previous_weight) * selection_progress
        y -= 6 * scale * selection_weight
        float_weight *= 1 - 0.55 * selection_weight
        alpha, mist = 255, 0.0
        if menu.phase in ("opening", "revealing"):
            stagger = index * 0.07
            reveal_progress = min(1, max(0, (progress - stagger) / (1 - stagger)))
            alpha = round(255 * _ease(reveal_progress))
            mist = (
                math.sin(math.pi * reveal_progress)
                if menu.phase == "opening"
                else 1 - _ease(progress)
            )
        elif menu.phase == "fading_out":
            alpha = round(255 * (1 - eased))
            mist = eased
        elif menu.phase == "mist":
            alpha, mist = 0, 1.0
        elif confirming:
            if index == menu.selected_choice:
                center_x, center_y = _center(layout, 1, 0)
                movement = eased if menu.phase == "confirming" else 1.0
                x += (center_x - x) * movement
                y += (center_y - y) * movement
                float_weight *= 1 - movement
                if menu.phase == "confirmation_fade":
                    alpha = round(255 * (1 - eased))
                    mist = eased
            else:
                alpha = round(255 * (1 - eased))
        phase = (current_time - menu.opened_at) / 1000 * 1.05 + index * 1.9
        x += math.sin(phase * 0.73) * 1.5 * scale * float_weight
        y += math.sin(phase) * 3 * scale * float_weight
        alpha = round(alpha * (1 - 0.14 * selection_presence * (1 - selection_weight)))
        bounds = figma_rect(spec["rect"])
        bounds.center = round(x), round(y)
        position = x - bounds.width / 2, y - bounds.height / 2
        poses.append(CardPose(index, bounds, mist, alpha, position))
    return poses


def card_hitbox(layout, pose):
    spec = layout["slots"][f"slot_{pose.index + 1:02d}"]
    original = figma_rect(spec["rect"])
    return figma_rect(spec["hitbox"]).move(pose.rect.x - original.x, pose.rect.y - original.y)
