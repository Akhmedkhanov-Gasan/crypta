from acts.act_three.equipment import equipment_rank_bonus

from acts.act_three.abilities import (
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
    content = attribute_tooltip_content(
        attribute,
        player.attribute_ranks.get(attribute, 0),
        player.player_class,
    )
    lines = content.lines
    if attribute == "instinct":
        lines = (
            "Increases critical chance and dodge chance.",
            "Base gains: 4 and 3 percentage points per rank.",
            "Gains diminish above 45% critical chance and 35% dodge.",
        )
    elif attribute == "will":
        lines = (
            "Adds 0.03 critical damage per rank, without a hard cap.",
            "Base critical chance gain: 1 percentage point per rank.",
            "Critical chance gains diminish above 45%.",
            *(line for line in content.lines if "Arcane Burst" in line),
        )
    elif attribute == "fortitude":
        lines = (
            "Adds 2 maximum HP per rank; this does not heal you.",
            "Base dodge gain: 1 percentage point per rank.",
            "Dodge gains diminish above 35%.",
        )
    extra_lines = {
        ("archer", "valor"): (
            "Increases basic shots, Piercing Shot and phantom damage.",
        ),
        ("assassin", "instinct"): (
            "Dodging a direct attack triggers Shadow Reflex.",
        ),
        ("paladin", "will"): (
            "Sacred Ground gains 1 damage on every odd Will rank.",
        ),
        ("warlock", "will"): (
            "Increases basic projectiles before Curse and Demon Form bonuses.",
        ),
        ("summoner", "will"): (
            "Increases your attacks, familiar, totem and greater spirit damage.",
            "While the familiar is away, your attacks deal 65% damage.",
            "The familiar and totem use half your magical damage range.",
        ),
    }.get((player.subclass, attribute), ())
    return TooltipContent(
        title=content.title,
        lines=(*lines, "Attribute ranks have no limit in Act III.", *extra_lines),
        accent=content.accent,
    )


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
    player_class,
):
    if stat_name in {
        "damage",
        "critical_chance",
        "critical_damage",
        "dodge_chance",
    }:
        content = combat_stat_tooltip_content(
            stat_name,
            value,
            player_class,
        )
        replacements = {
            "critical_chance": (
                "Gains diminish above 45%, approaching 75% without reaching it.",
            ),
            "critical_damage": ("Critical damage has no hard cap in Act III.",),
            "dodge_chance": (
                "Gains diminish above 35%, approaching 60% without reaching it.",
            ),
        }
        if stat_name not in replacements:
            return content
        return TooltipContent(
            title=content.title,
            lines=(*content.lines[:-1], *replacements[stat_name]),
            accent=content.accent,
        )

    if stat_name == "armor":
        return TooltipContent(
            title=f"ARMOR  |  {value}",
            lines=(
                "Reduces incoming physical damage.",
            ),
            accent=_PANEL_ACCENTS["armor"],
        )

    return None


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
            player.player_class,
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
                ),
                accent=_PANEL_ACCENTS["weapon"],
            )

        return TooltipContent(
            title=f"ARMOR  |  RANK {rank}",
            lines=(
                f"Physical damage reduction: {equipment_rank_bonus(rank, armor=True)}%.",
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
