import json
import math
from copy import deepcopy
from functools import lru_cache
from types import SimpleNamespace

import pygame
import resource_store as resources

from acts.act_one.settings import PLAYER_STARTING_ATTRIBUTE_RANKS
from acts.act_two.settings import CLASS_BASE_ATTRIBUTE_RANKS
from acts.player_stats import apply_attribute_rank_transition
from presentation.figma_ui import (
    draw_figma_rectangle,
    draw_figma_text,
    figma_rect,
    get_figma_font,
)

from presentation.layout import (
    AWAKENING_OLD_MAN_APPROACH_START_MS,
    AWAKENING_RECOVERY_BLINK_END_MS,
    AWAKENING_RECOVERY_BLINK_START_MS,
    AWAKENING_SECOND_OPEN_START_MS,
    CLASS_SELECTION_READY_MS,
    PROJECT_ROOT,
)
from settings import GAME_HEIGHT, GAME_WIDTH, MAX_ATTRIBUTE_RANK


OLD_MAN_RESPONSES = {
    "warrior": "Then stand, and let the Crypta break against you.",
    "rogue": "Then walk where even the Crypta cannot see.",
    "mage": "Then look deeper. But beware what looks back.",
}

ATTRIBUTE_LABELS = {
    "strength": "STR",
    "dexterity": "DEX",
    "intelligence": "INT",
    "vitality": "VIT",
}

ATTRIBUTE_GAIN_COLOR = (57, 114, 42)
ATTRIBUTE_LOSS_COLOR = (152, 51, 51)


@lru_cache(maxsize=1)
def load_awakening_layout():
    path = (
        PROJECT_ROOT
        / "assets"
        / "ui"
        / "layouts"
        / "act_2"
        / "Awakening_Act2.json"
    )
    with resources.open_text(path, encoding="utf-8-sig") as source:
        layout = json.load(source)

    if (
        layout.get("schema_version") != 1
        or layout.get("screen") != "awakening"
        or layout.get("act") != 2
        or layout.get("coordinate_space") != "frame"
    ):
        raise ValueError(f"Unsupported awakening layout: {path}")

    frame = layout["frame"]
    if (frame["width"], frame["height"]) != (GAME_WIDTH, GAME_HEIGHT):
        raise ValueError(
            "Awakening frame must match the internal game resolution: "
            f"{GAME_WIDTH}x{GAME_HEIGHT}"
        )

    choices = layout["class_choices"]
    order = choices["order"]
    if len(order) != 3 or set(order) != set(OLD_MAN_RESPONSES):
        raise ValueError("Awakening must contain mage, warrior and rogue")

    for class_name in order:
        option = choices["options"][class_name]
        if option["class_id"] != class_name:
            raise ValueError(f"Invalid awakening class_id: {class_name}")
        if not option["info_panel"]["attributes"]["values"]["items"]:
            raise ValueError(f"Missing attribute text style: {class_name}")

    return layout


def get_awakening_hitboxes():
    choices = load_awakening_layout()["class_choices"]
    return {
        class_name: figma_rect(
            choices["options"][class_name]["hitbox"]
        )
        for class_name in choices["order"]
    }


def class_attribute_changes(class_name, current_ranks=None):
    if current_ranks is None:
        current_ranks = PLAYER_STARTING_ATTRIBUTE_RANKS

    preview_player = SimpleNamespace(
        attribute_ranks=dict(current_ranks)
    )
    apply_attribute_rank_transition(
        preview_player,
        PLAYER_STARTING_ATTRIBUTE_RANKS,
        CLASS_BASE_ATTRIBUTE_RANKS[class_name],
    )

    if class_name == "mage":
        invested = max(
            0,
            current_ranks.get("strength", 0)
            - PLAYER_STARTING_ATTRIBUTE_RANKS["strength"],
        )
        preview_player.attribute_ranks["strength"] = (
            CLASS_BASE_ATTRIBUTE_RANKS["mage"]["strength"]
        )
        preview_player.attribute_ranks["intelligence"] = min(
            MAX_ATTRIBUTE_RANK,
            preview_player.attribute_ranks["intelligence"] + invested,
        )

    changes = []
    for attribute, label in ATTRIBUTE_LABELS.items():
        before = current_ranks.get(attribute, 0)
        after = preview_player.attribute_ranks.get(attribute, 0)
        difference = after - before
        if difference:
            changes.append((label, before, after, difference))

    return tuple(changes)


def _progress(elapsed_ms, start_ms, end_ms):
    value = max(
        0.0,
        min(1.0, (elapsed_ms - start_ms) / (end_ms - start_ms)),
    )
    return value * value * (3.0 - 2.0 * value)


def _draw_image(screen, sprites, spec, *, rect=None, opacity=1.0):
    target = figma_rect(spec["rect"]) if rect is None else rect
    alpha = max(
        0.0,
        min(1.0, opacity * spec.get("opacity", 1.0)),
    )
    if alpha <= 0:
        return

    image = pygame.transform.scale(
        sprites[spec["asset_key"]],
        (max(1, target.width), max(1, target.height)),
    )
    image.set_alpha(round(255 * alpha))
    screen.blit(image, target)


def _wrap_lines(text, font, width):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        line = words[0]
        for word in words[1:]:
            candidate = f"{line} {word}"
            if font.size(candidate)[0] <= width:
                line = candidate
            else:
                lines.append(line)
                line = word
        lines.append(line)

    return lines


def _draw_text(screen, source_spec, *, wrap=False):
    spec = deepcopy(source_spec)
    rect = figma_rect(spec["rect"])
    text = str(spec.get("text", ""))

    text_case = str(spec.get("text_case", "ORIGINAL")).upper()
    if text_case == "UPPER":
        text = text.upper()
    elif text_case == "LOWER":
        text = text.lower()
    elif text_case == "TITLE":
        text = text.title()
    spec["text_case"] = "ORIGINAL"

    original_size = max(1, round(spec["font"]["size"]))
    minimum_size = min(8, original_size)

    for size in range(original_size, minimum_size - 1, -1):
        spec["font"]["size"] = size
        font = get_figma_font(spec)
        lines = (
            _wrap_lines(text, font, rect.width)
            if wrap
            else text.split("\n")
        )

        height_spec = spec.get("line_height", {})
        unit = height_spec.get("unit", "AUTO")
        value = height_spec.get("value")
        if unit == "PIXELS" and value is not None:
            line_height = max(
                1, round(value * size / original_size)
            )
        elif unit == "PERCENT" and value is not None:
            line_height = max(1, round(size * value / 100))
        else:
            line_height = font.get_linesize()

        if (
            max(font.size(line)[0] for line in lines) <= rect.width
            and line_height * len(lines) <= rect.height
            and font.get_height() <= rect.height
        ):
            break
    else:
        raise ValueError(
            f"Awakening text does not fit its Figma frame: {text!r}"
        )

    spec["line_height"] = {
        "unit": "PIXELS",
        "value": line_height,
    }
    draw_figma_text(
        screen,
        spec,
        text_override="\n".join(lines),
    )


def _draw_attributes(screen, attributes, class_name, current_ranks):
    _draw_text(screen, attributes["title"])

    values = attributes["values"]
    rect = figma_rect(values["rect"])
    template = values["items"][0]
    font = get_figma_font(template)
    changes = class_attribute_changes(class_name, current_ranks)

    if not changes:
        text = font.render(
            "No attribute changes",
            True,
            (167, 167, 167),
        )
        screen.blit(text, text.get_rect(center=rect.center))
        return

    labels = [
        f"{label} {before}→{after} ({difference:+d})"
        for label, before, after, difference in changes
    ]
    gap = max(0, round(values.get("layout", {}).get("gap", 12)))

    total_width = (
        sum(font.size(label)[0] for label in labels)
        + gap * (len(labels) - 1)
    )

    if total_width > rect.width:
        labels = [
            f"{label} {difference:+d}"
            for label, before, after, difference in changes
        ]

    text_width = sum(font.size(label)[0] for label in labels)
    if len(labels) > 1:
        gap = min(
            gap,
            max(0, (rect.width - text_width) // (len(labels) - 1)),
        )

    total_width = text_width + gap * (len(labels) - 1)
    if total_width > rect.width:
        raise ValueError(
            f"Attribute row is too narrow for {class_name}"
        )

    x = rect.centerx - total_width // 2
    for label, change in zip(labels, changes):
        color = (
            ATTRIBUTE_GAIN_COLOR
            if change[3] > 0
            else ATTRIBUTE_LOSS_COLOR
        )
        rendered = font.render(label, True, color)
        screen.blit(
            rendered,
            rendered.get_rect(midleft=(x, rect.centery)),
        )
        x += rendered.get_width() + gap


def draw_awakening_old_man(
    screen,
    sprites,
    elapsed_ms,
    choice_elapsed_ms,
):
    if elapsed_ms < AWAKENING_SECOND_OPEN_START_MS:
        return

    states = load_awakening_layout()["art"]["old_man_states"]
    midpoint = (
        AWAKENING_RECOVERY_BLINK_START_MS
        + AWAKENING_RECOVERY_BLINK_END_MS
    ) // 2

    near = elapsed_ms >= midpoint
    spec = states["near" if near else "far"]
    original = figma_rect(spec["rect"])
    scale = 1.0
    opacity = 1.0

    if not near:
        approach = _progress(
            elapsed_ms,
            AWAKENING_OLD_MAN_APPROACH_START_MS,
            midpoint,
        )
        scale = 0.88 + 0.12 * approach

    retreat = 0.0
    if choice_elapsed_ms is not None:
        retreat = _progress(choice_elapsed_ms, 300, 1700)
        scale *= 1.0 - 0.18 * retreat
        opacity *= 1.0 - retreat

    rect = pygame.Rect(
        0,
        0,
        max(1, round(original.width * scale)),
        max(1, round(original.height * scale)),
    )
    rect.midbottom = (
        original.centerx,
        original.bottom
        + round(math.sin(elapsed_ms / 850) * 1.2)
        - round(12 * retreat),
    )
    _draw_image(
        screen,
        sprites,
        spec,
        rect=rect,
        opacity=opacity,
    )


def draw_awakening_choices(
    screen,
    sprites,
    elapsed_ms,
    mouse_position,
    selected_class,
    choice_elapsed_ms,
    attribute_ranks,
):
    layout = load_awakening_layout()
    choices = layout["class_choices"]
    hitboxes = get_awakening_hitboxes()

    hovered_class = None
    if selected_class is None and mouse_position is not None:
        hovered_class = next(
            (
                name
                for name, rect in hitboxes.items()
                if rect.collidepoint(mouse_position)
            ),
            None,
        )

    opacity = _progress(
        elapsed_ms,
        CLASS_SELECTION_READY_MS,
        CLASS_SELECTION_READY_MS + 520,
    )
    if selected_class is not None:
        opacity *= 1.0 - _progress(choice_elapsed_ms, 0, 480)

    if opacity > 0:
        layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        _draw_text(layer, layout["screen_title"]["text"])

        for class_name in choices["order"]:
            option = choices["options"][class_name]
            panel = option["info_panel"]

            if class_name != selected_class:
                _draw_image(layer, sprites, option["portrait"])

            background = deepcopy(panel["background"])
            if class_name == hovered_class:
                background["stroke"] = {
                    **panel["class_name"]["color"],
                    "a": 220,
                }
            draw_figma_rectangle(layer, background)

            _draw_text(layer, panel["class_name"])
            _draw_text(layer, panel["class_description"], wrap=True)
            _draw_attributes(
                layer,
                panel["attributes"],
                class_name,
                attribute_ranks,
            )

            ability = panel["ability"]
            header = ability["header"]
            _draw_image(layer, sprites, header["icon"])
            _draw_text(layer, header["name"])
            _draw_text(layer, ability["description"], wrap=True)

        layer.set_alpha(round(255 * opacity))
        screen.blit(layer, (0, 0))

    if selected_class is not None:
        spec = choices["options"][selected_class]["portrait"]
        original = figma_rect(spec["rect"])
        progress = _progress(choice_elapsed_ms, 180, 1550)
        scale = 1.0 + 2.2 * progress

        rect = pygame.Rect(
            0,
            0,
            round(original.width * scale),
            round(original.height * scale),
        )
        rect.center = (
            round(
                original.centerx
                + (GAME_WIDTH / 2 - original.centerx) * progress
            ),
            round(
                original.centery
                + (GAME_HEIGHT * 0.62 - original.centery) * progress
            ),
        )
        _draw_image(
            screen,
            sprites,
            spec,
            rect=rect,
            opacity=1.0 - _progress(choice_elapsed_ms, 1200, 1950),
        )

    return hovered_class