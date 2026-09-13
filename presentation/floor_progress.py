import pygame

from levels import FLOOR_CONFIGS


_ROMAN_VALUES = (
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)


def tower_floor_number(floor_index):
    return sum(
        0
        if floor_config.get(
            "continues_previous_floor",
            False,
        )
        else 1
        for floor_config in FLOOR_CONFIGS[
            :floor_index + 1
        ]
    )


def roman_number(number):
    result = []
    remaining = number

    for value, numeral in _ROMAN_VALUES:
        while remaining >= value:
            result.append(numeral)
            remaining -= value

    return "".join(result)


def floor_indicator_text(floor_index):
    floor_config = FLOOR_CONFIGS[floor_index]
    tower_floor = tower_floor_number(floor_index)
    act_number = roman_number(
        floor_config["act"]
    )

    return (
        f"FLOOR {tower_floor}"
        f"  |  ACT {act_number}"
    )


def draw_floor_indicator(
    surface,
    font,
    floor_index,
    center_x,
    top=4,
):
    text = floor_indicator_text(floor_index)
    text_surface = font.render(
        text,
        True,
        (202, 194, 176),
    )
    text_rectangle = text_surface.get_rect(
        midtop=(center_x, top)
    )

    shadow_surface = font.render(
        text,
        True,
        (10, 12, 16),
    )
    surface.blit(
        shadow_surface,
        text_rectangle.move(1, 2),
    )
    surface.blit(
        text_surface,
        text_rectangle,
    )

    line_y = text_rectangle.centery
    gap = 13
    line_length = 46
    line_color = (75, 65, 53)

    pygame.draw.line(
        surface,
        line_color,
        (
            text_rectangle.left
            - gap
            - line_length,
            line_y,
        ),
        (
            text_rectangle.left - gap,
            line_y,
        ),
    )
    pygame.draw.line(
        surface,
        line_color,
        (
            text_rectangle.right + gap,
            line_y,
        ),
        (
            text_rectangle.right
            + gap
            + line_length,
            line_y,
        ),
    )
