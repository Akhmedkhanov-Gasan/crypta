import pygame

from game.attributes import get_attribute_definition
from presentation.figma_ui import figma_rect
from presentation.tooltips import TooltipContent


_ATTRIBUTE_ACCENTS = {
    "valor": (184, 82, 64),
    "instinct": (190, 151, 69),
    "will": (92, 128, 185),
    "fortitude": (139, 74, 89),
}

_COMBAT_STAT_ACCENTS = {
    "damage": (184, 82, 64),
    "critical_chance": (190, 151, 69),
    "critical_damage": (156, 95, 161),
    "dodge_chance": (92, 128, 185),
}

_ATTRIBUTE_LINES = {
    "valor": (
        "Increases physical damage as ranks increase.",
        "Adds 0.05 to critical damage per rank.",
        "Adds 1 maximum HP every 2 ranks.",
    ),
    "instinct": (
        "Adds 4% critical chance per rank.",
        "Adds 3% dodge chance per rank.",
    ),
    "will": (
        "Adds 1% critical chance per rank.",
        "Adds 0.03 to critical damage per rank.",
    ),
    "fortitude": (
        "Adds 2 maximum HP per rank.",
        "Adds 1% dodge chance per rank.",
    ),
}

_CLASS_ATTRIBUTE_LINES = {
    ("warrior", "valor"): (
        "Power Cleave gains 1 damage on every odd Valor rank.",
    ),
    ("rogue", "instinct"): (
        "An attack from invisibility gains 1 damage every 3 ranks.",
        "Invisibility always lasts 5 turns.",
    ),
    ("mage", "will"): (
        "Mage attacks gain 1 damage on every odd Will rank.",
        "Arcane Burst also gains damage from Will.",
    ),
}


def stat_row_rectangle(row_layout):
    rectangles = [
        figma_rect(row_layout["label"]["rect"]),
        figma_rect(row_layout["value"]["rect"]),
    ]

    for control_name in (
        "minus_hitbox",
        "plus_hitbox",
    ):
        if control_name in row_layout:
            rectangles.append(
                figma_rect(row_layout[control_name])
            )

    rectangle = rectangles[0].copy()

    for part in rectangles[1:]:
        rectangle.union_ip(part)

    rectangle.inflate_ip(8, 6)
    return rectangle


def hovered_row_at(
    rows,
    mouse_position,
):
    if mouse_position is None:
        return None

    for row_name, row_layout in rows.items():
        if stat_row_rectangle(
            row_layout
        ).collidepoint(mouse_position):
            return row_name

    return None


def draw_stat_row_highlight(
    screen,
    row_layout,
    accent,
):
    rectangle = stat_row_rectangle(row_layout)

    highlight = pygame.Surface(
        rectangle.size,
        pygame.SRCALPHA,
    )
    pygame.draw.rect(
        highlight,
        (*accent, 34),
        highlight.get_rect(),
        border_radius=4,
    )
    pygame.draw.rect(
        highlight,
        (*accent, 135),
        highlight.get_rect(),
        width=1,
        border_radius=4,
    )
    screen.blit(highlight, rectangle)


def draw_attribute_row_highlight(
    screen,
    row_layout,
    attribute,
):
    draw_stat_row_highlight(
        screen,
        row_layout,
        _ATTRIBUTE_ACCENTS[attribute],
    )


def draw_combat_stat_row_highlight(
    screen,
    row_layout,
    stat_name,
):
    draw_stat_row_highlight(
        screen,
        row_layout,
        _COMBAT_STAT_ACCENTS[stat_name],
    )


def attribute_tooltip_content(
    attribute,
    rank,
    player_class,
):
    definition = get_attribute_definition(attribute)
    lines = (
        *_ATTRIBUTE_LINES[attribute],
        *_CLASS_ATTRIBUTE_LINES.get(
            (player_class, attribute),
            (),
        ),
    )

    return TooltipContent(
        title=(
            f"{definition.title.upper()}  |  RANK {rank}"
        ),
        lines=lines,
        accent=_ATTRIBUTE_ACCENTS[attribute],
    )


def combat_stat_tooltip_content(
    stat_name,
    value,
    player_class,
):
    if stat_name == "damage":
        if player_class == "mage":
            lines = (
                "A basic magical attack deals a random amount within this range.",
                "Will increases Mage attack damage.",
                "Ability damage and critical hits are applied separately.",
            )
        else:
            lines = (
                "A basic attack deals a random amount within this range.",
                "Valor increases physical attack damage.",
                "Ability damage and critical hits are applied separately.",
            )

        title = f"DAMAGE  |  {value}"

    elif stat_name == "critical_chance":
        title = f"CRITICAL CHANCE  |  {value}"
        lines = (
            "The chance for an attack to become a critical hit.",
            "Instinct adds 4% per rank. Will adds 1% per rank.",
            "Critical chance cannot exceed 45%.",
        )

    elif stat_name == "critical_damage":
        title = f"CRITICAL DAMAGE  |  {value}"
        lines = (
            "The damage multiplier applied when an attack critically hits.",
            "Valor adds 0.05 per rank. Will adds 0.03 per rank.",
            "Critical damage cannot exceed x2.75.",
        )

    else:
        title = f"DODGE CHANCE  |  {value}"
        lines = (
            "The chance to avoid a direct enemy attack.",
            "Instinct adds 3% per rank. Fortitude adds 1% per rank.",
            "It does not protect from traps, ground hazards or unavoidable attacks.",
            "Dodge chance cannot exceed 35%.",
        )

    return TooltipContent(
        title=title,
        lines=lines,
        accent=_COMBAT_STAT_ACCENTS[stat_name],
    )
