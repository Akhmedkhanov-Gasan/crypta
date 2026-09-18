import pygame

from acts.act_three.abilities import (
    get_ability_definition,
    is_ability_slot_unlocked,
)
from acts.act_three.abilities.charges import (
    get_act_three_ability_charge_state,
)
from acts.act_two.presentation.hud_tooltips import (
    ability_tooltip_content as inherited_ability_tooltip_content,
)
from game.rune_catalog import RUNES_BY_ID
from presentation.figma_ui import figma_rect
from presentation.tooltips import TooltipContent


_ABILITY_ACCENT = (126, 105, 168)
_LOCKED_ACCENT = (111, 73, 73)

_PASSIVE_RUNES = frozenset({
    "rune_of_the_veil",
    "rune_of_resonance",
    "rune_of_impact",
})


def hovered_ability_slot(
    slots,
    mouse_position,
):
    if mouse_position is None:
        return None

    for slot_name, slot_layout in slots.items():
        if figma_rect(
            slot_layout["hitbox"]
        ).collidepoint(mouse_position):
            return slot_name.removeprefix(
                "ability_"
            )

    return None


def draw_ability_slot_highlight(
    screen,
    slot_layout,
    locked,
):
    rectangle = figma_rect(
        slot_layout["hitbox"]
    )
    accent = (
        _LOCKED_ACCENT
        if locked
        else _ABILITY_ACCENT
    )

    highlight = pygame.Surface(
        rectangle.size,
        pygame.SRCALPHA,
    )

    pygame.draw.rect(
        highlight,
        (*accent, 35),
        highlight.get_rect(),
        border_radius=6,
    )
    pygame.draw.rect(
        highlight,
        (*accent, 180),
        highlight.get_rect(),
        width=1,
        border_radius=6,
    )

    screen.blit(
        highlight,
        rectangle,
    )


def _format_charge(value):
    if float(value).is_integer():
        return str(int(value))

    return f"{value:.1f}"


def _ability_charge(
    player,
    slot,
    ability,
):
    return get_act_three_ability_charge_state(
        player,
        slot,
    )


def ability_tooltip_content(
    player,
    slot,
):
    if slot is None:
        return None

    ability = get_ability_definition(
        player.subclass,
        slot,
    )

    if ability is None:
        return None

    unlocked = is_ability_slot_unlocked(
        player,
        slot,
    )

    if ability.inherited:
        selected_rune = RUNES_BY_ID.get(
            player.selected_rune_id
        )
        inherited_content = (
            inherited_ability_tooltip_content(
                player.player_class,
                selected_rune,
            )
        )
        title = inherited_content.title
        description_lines = inherited_content.lines
    else:
        title = ability.name
        description_lines = (
            ability.description,
        )

    slot_title = (
        f"{slot.upper()}  |  {title}"
    )

    if not unlocked:
        return TooltipContent(
            title=f"{slot_title}  |  LOCKED",
            lines=(
                *description_lines,
                "This ability has not been unlocked.",
            ),
            accent=_LOCKED_ACCENT,
        )

    if (
        slot == "e"
        and player.selected_rune_id in _PASSIVE_RUNES
    ):
        return TooltipContent(
            title=slot_title,
            lines=(
                *description_lines,
                "This rune changes the inherited ability into a passive effect.",
            ),
            accent=_ABILITY_ACCENT,
        )

    current_charge, required_charge = (
        _ability_charge(
            player,
            slot,
            ability,
        )
    )

    charge_line = (
        "READY"
        if current_charge >= required_charge
        else (
            "CHARGE  |  "
            f"{_format_charge(current_charge)}"
            "/"
            f"{_format_charge(required_charge)}"
        )
    )

    return TooltipContent(
        title=slot_title,
        lines=(
            *description_lines,
            charge_line,
        ),
        accent=_ABILITY_ACCENT,
    )
