import pygame

from acts.act_three.abilities import (
    get_mastery_charge_rate,
    get_passive_definition,
)
from acts.act_two.presentation.stats_tooltips import (
    attribute_tooltip_content,
    combat_stat_tooltip_content,
    draw_attribute_row_highlight,
    draw_stat_row_highlight,
    hovered_row_at,
)
from presentation.figma_ui import figma_rect
from presentation.tooltips import TooltipContent


_PANEL_ACCENTS = {
    "damage": (184, 82, 64),
    "armor": (151, 151, 151),
    "critical_chance": (190, 151, 69),
    "critical_damage": (156, 95, 161),
    "dodge_chance": (92, 128, 185),
    "charge_rate": (121, 103, 175),
    "mastery": (121, 103, 175),
    "weapon": (184, 82, 64),
    "equipment_armor": (151, 151, 151),
    "passive": (156, 95, 161),
}


def _draw_hitbox_highlight(
    screen,
    hitbox,
    accent,
):
    rectangle = figma_rect(hitbox)

    highlight = pygame.Surface(
        rectangle.size,
        pygame.SRCALPHA,
    )

    pygame.draw.rect(
        highlight,
        (*accent, 30),
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

    screen.blit(
        highlight,
        rectangle,
    )


def get_character_panel_hover(
    panel,
    mouse_position,
):
    if mouse_position is None:
        return None

    hovered_attribute = hovered_row_at(
        panel["attributes"]["rows"],
        mouse_position,
    )

    if hovered_attribute is not None:
        return "attribute", hovered_attribute

    hovered_combat_stat = hovered_row_at(
        panel["combat_stats"]["rows"],
        mouse_position,
    )

    if hovered_combat_stat is not None:
        return "combat_stat", hovered_combat_stat

    fixed_hitboxes = (
        (
            "mastery",
            "mastery",
            panel["mastery"]["hitbox"],
        ),
        (
            "equipment",
            "weapon",
            panel["equipment"]["weapon"]["hitbox"],
        ),
        (
            "equipment",
            "armor",
            panel["equipment"]["armor"]["hitbox"],
        ),
        (
            "passive",
            "passive",
            panel["subclass_passive"]["hitbox"],
        ),
    )

    for category, name, hitbox in fixed_hitboxes:
        if figma_rect(hitbox).collidepoint(
            mouse_position
        ):
            return category, name

    return None


def draw_character_panel_highlight(
    screen,
    panel,
    hovered_item,
):
    if hovered_item is None:
        return

    category, name = hovered_item

    if category == "attribute":
        draw_attribute_row_highlight(
            screen,
            panel["attributes"]["rows"][name],
            name,
        )
        return

    if category == "combat_stat":
        draw_stat_row_highlight(
            screen,
            panel["combat_stats"]["rows"][name],
            _PANEL_ACCENTS[name],
        )
        return

    if category == "mastery":
        _draw_hitbox_highlight(
            screen,
            panel["mastery"]["hitbox"],
            _PANEL_ACCENTS["mastery"],
        )
        return

    if category == "equipment":
        accent_name = (
            "weapon"
            if name == "weapon"
            else "equipment_armor"
        )

        _draw_hitbox_highlight(
            screen,
            panel["equipment"][name]["hitbox"],
            _PANEL_ACCENTS[accent_name],
        )
        return

    _draw_hitbox_highlight(
        screen,
        panel["subclass_passive"]["hitbox"],
        _PANEL_ACCENTS["passive"],
    )


def _act_three_combat_tooltip(
    stat_name,
    value,
    player_class,
):
    if stat_name in {
        "damage",
        "critical_chance",
        "critical_damage",
        "dodge_chance",
    }:
        return combat_stat_tooltip_content(
            stat_name,
            value,
            player_class,
        )

    if stat_name == "armor":
        return TooltipContent(
            title=f"ARMOR  |  {value}",
            lines=(
                "Shows the protection granted by armor and other effects.",
                "Armor upgrades increase this value.",
                "It does not replace dodge chance.",
            ),
            accent=_PANEL_ACCENTS["armor"],
        )

    return TooltipContent(
        title=f"CHARGE RATE  |  {value}",
        lines=(
            "Controls how quickly abilities gain charge.",
            "Mastery increases charge rate by 10% per rank.",
            "It does not reduce the charge required to cast an ability.",
        ),
        accent=_PANEL_ACCENTS["charge_rate"],
    )


def character_panel_tooltip_content(
    hovered_item,
    player,
    combat_values,
):
    if hovered_item is None:
        return None

    category, name = hovered_item

    if category == "attribute":
        return attribute_tooltip_content(
            name,
            player.attribute_ranks.get(name, 0),
            player.player_class,
        )

    if category == "combat_stat":
        return _act_three_combat_tooltip(
            name,
            combat_values[name],
            player.player_class,
        )

    if category == "mastery":
        mastery_rank = getattr(
            player,
            "mastery_rank",
            0,
        )
        charge_rate = round(
            get_mastery_charge_rate(player) * 100
        )

        return TooltipContent(
            title=f"MASTERY  |  RANK {mastery_rank}",
            lines=(
                f"Current ability charge rate: {charge_rate}%.",
                "Each rank increases charge rate by 10%.",
                "Mastery has a maximum of 5 ranks.",
            ),
            accent=_PANEL_ACCENTS["mastery"],
        )

    if category == "equipment":
        rank_attribute = (
            "weapon_rank"
            if name == "weapon"
            else "armor_rank"
        )
        rank = getattr(
            player,
            rank_attribute,
            0,
        )

        if name == "weapon":
            return TooltipContent(
                title=f"WEAPON  |  RANK {rank}",
                lines=(
                    "Shows the current weapon upgrade rank.",
                    "Weapon rank is increased by the blacksmith.",
                    "Its effects depend on the subclass weapon.",
                ),
                accent=_PANEL_ACCENTS["weapon"],
            )

        return TooltipContent(
            title=f"ARMOR  |  RANK {rank}",
            lines=(
                "Shows the current armor upgrade rank.",
                "Armor rank is increased by the blacksmith.",
                "Its effects depend on the subclass armor.",
            ),
            accent=_PANEL_ACCENTS["equipment_armor"],
        )

    passive = get_passive_definition(
        player.subclass
    )

    if passive is None:
        return None

    return TooltipContent(
        title=passive.name,
        lines=(
            passive.description.replace(
                "\n",
                " ",
            ),
            "Subclass passive acquired upon entering Act III.",
        ),
        accent=_PANEL_ACCENTS["passive"],
    )
