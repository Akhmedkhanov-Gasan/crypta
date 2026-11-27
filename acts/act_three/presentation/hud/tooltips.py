from acts.act_three.equipment import equipment_rank_bonus
from acts.act_three.presentation.descriptions.abilities import passive_lines
from acts.act_three.presentation.descriptions.attributes import attribute_tooltip
from acts.act_three.presentation.descriptions.combat import armor_lines, chance_lines, critical_lines, damage_lines

from acts.act_three.abilities import (
    get_passive_definition,
)
from acts.act_two.presentation.stats_tooltips import (
    draw_attribute_row_highlight,
    draw_stat_row_highlight,
    hovered_row_at,
)
from presentation.figma_ui import figma_rect
from presentation.tooltips import TooltipContent
from presentation.tooltips.highlights import draw_selection_highlight


_PANEL_ACCENTS = {
    "damage": (184, 82, 64),
    "armor": (151, 151, 151),
    "critical_chance": (190, 151, 69),
    "critical_damage": (156, 95, 161),
    "dodge_chance": (92, 128, 185),
    "weapon": (184, 82, 64),
    "equipment_armor": (151, 151, 151),
    "passive": (156, 95, 161),
}


def _attribute_tooltip(player, attribute):
    return attribute_tooltip(player, attribute)


def _draw_hitbox_highlight(
    screen,
    hitbox,
    accent,
):
    rectangle = figma_rect(hitbox)
    draw_selection_highlight(screen, rectangle)


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
    player,
):
    builders = {
        "damage": damage_lines,
        "critical_chance": chance_lines,
        "critical_damage": critical_lines,
        "dodge_chance": lambda current: chance_lines(current, dodge=True),
        "armor": armor_lines,
    }
    builder = builders.get(stat_name)
    if builder is None:
        return None
    title = stat_name.replace("_", " ").upper()
    return TooltipContent(f"{title} | {value}", builder(player), _PANEL_ACCENTS[stat_name])


def character_panel_tooltip_content(
    hovered_item,
    player,
    combat_values,
):
    if hovered_item is None:
        return None

    category, name = hovered_item

    if category == "attribute":
        return _attribute_tooltip(player, name)

    if category == "combat_stat":
        return _act_three_combat_tooltip(
            name,
            combat_values[name],
            player,
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
                    f"Weapon damage bonus: +{equipment_rank_bonus(rank)}%.",
                    "Multiplies weapon attacks, spells, phantoms and spirit damage; stacks with critical hits, runes and pacts.",
                ),
                accent=_PANEL_ACCENTS["weapon"],
            )

        return TooltipContent(
            title=f"ARMOR  |  RANK {rank}",
            lines=armor_lines(player),
            accent=_PANEL_ACCENTS["equipment_armor"],
        )

    passive = get_passive_definition(
        player.subclass
    )

    if passive is None:
        return None

    return TooltipContent(
        title=passive.name,
        lines=passive_lines(player),
        accent=_PANEL_ACCENTS["passive"],
    )
