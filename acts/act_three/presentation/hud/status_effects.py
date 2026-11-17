from dataclasses import dataclass

import pygame

import resource_store as resources
from acts.act_three.abilities.catalog import get_passive_definition
from acts.act_two.bloody_altar_catalog import BLOODY_PACTS_BY_ID
from game.rune_catalog import RUNES_BY_ID
from presentation.figma_ui import draw_figma_rectangle, draw_figma_text, figma_rect
from presentation.layout import ASSET_ROOT
from presentation.tooltips import TooltipContent


@dataclass(frozen=True)
class Status:
    key: str
    name: str
    description: str
    count: int | None = None
    unit: str = "turns"
    icon_asset: str | None = None

    def details(self):
        if self.count is None:
            return self.description
        return f"{self.description} Remaining: {self.count} {self.unit}."


_ABILITY_ICONS = {
    "invisibility": "act_three_invisibility",
    "last_rage": "act_three_berserker_last_rage",
    "sacred_ground": "act_three_paladin_sacred_ground",
    "demon_form": "act_three_warlock_demon_form",
    "true_form": "act_three_summoner_true_form",
    "familiar": "act_three_summoner_release_familiar",
}
_ITEM_ICONS = {
    "stoneflesh": "scroll_of_stoneflesh",
    "regeneration": "regeneration_draught",
    "ironblood_guard": "ironblood_tonic",
}
_CUSTOM_ICONS = ("stun",)


def load_status_assets(ui_directory):
    directory = ui_directory / "status_effects"
    paths = {key: directory / f"{key}.png" for key in _CUSTOM_ICONS}
    paths.update({
        key: ASSET_ROOT / "ui" / "act_2" / "bloody_altar" / "icons" / f"{key}_original.png"
        for key in BLOODY_PACTS_BY_ID
    })
    frame = directory / "status_effect_frame.png"
    if not resources.is_file(frame):
        frame = ui_directory / "icon.png"
    paths["frame"] = frame
    return {
        key: resources.load_image(str(path)).convert_alpha()
        for key, path in paths.items()
        if resources.is_file(path)
    }


def _active_statuses(player):
    state = player.act_three
    timed = (
        Status("stun", "Stunned", "You cannot act.", player.stun_turns),
        Status("invisibility", "Invisibility", "Enemies cannot see you.", player.invisibility_turns),
        Status("regeneration", "Regeneration", "Restores health over time.", state.regeneration_ticks),
        Status("stoneflesh", "Stoneflesh", "Reduces incoming physical damage.", player.act_two.stoneflesh_hits, "hits"),
        Status("last_rage", "Last Rage", "Keeps the Berserker from dying.", state.berserker_last_rage_turns),
        Status("sacred_ground", "Sacred Ground", "The consecrated area is still active.", state.paladin_sacred_ground_turns),
        Status("true_form", "True Form", "Empowers the familiar.", state.summoner_true_form_charge if state.summoner_true_form_active else 0, "attacks"),
    )
    yield from (status for status in timed if status.count > 0)
    if state.ironblood_guard:
        yield Status("ironblood_guard", "Ironblood Guard", "Halves the next damaging hit.", 1, "hit")
    if state.warlock_demon_form_active:
        yield Status("demon_form", "Demon Form", "Empowers the Warlock and drains health each turn until cancelled.")
    if state.summoner_familiar_active:
        yield Status("familiar", "Familiar", "The familiar is on the battlefield.")
    rune = RUNES_BY_ID.get(player.selected_rune_id)
    if rune is not None:
        yield Status(rune.id, rune.name, rune.description)
    pact = BLOODY_PACTS_BY_ID.get(player.act_two.bloody_pact_id)
    if pact is not None:
        yield Status(pact.id, pact.name, f"{pact.reward} {pact.sacrifice}")
    passive = get_passive_definition(player.subclass)
    if passive is not None:
        yield Status(passive.id, passive.name, passive.description, icon_asset=passive.icon_asset)


def _icon(assets, custom, key):
    if key in _ITEM_ICONS:
        return assets.get("act_three_consumable_belt_sprites", {}).get(_ITEM_ICONS[key])
    if key in _ABILITY_ICONS:
        return assets.get(_ABILITY_ICONS[key])
    if key.startswith("rune_"):
        return assets.get(f"act_three_{key}")
    return custom.get(key)


def draw_player_statuses(screen, player, assets, layout, mouse_position):
    slots = layout["top_bar"].get("status_effects", {}).get("slots", {})
    if not slots:
        return None
    statuses = list(_active_statuses(player))
    overflow = statuses[len(slots) - 1:] if len(statuses) > len(slots) else []
    if overflow:
        statuses = statuses[:len(slots) - 1] + [Status("overflow", "More Effects", "")]

    custom = assets.get("hud_status_images", {})
    tooltip = None
    for name, status in zip(sorted(slots), statuses):
        slot = slots[name]
        frame = slot["frame"]
        if frame.get("asset"):
            rectangle = figma_rect(frame["rect"])
            if custom.get("frame") is not None:
                screen.blit(pygame.transform.smoothscale(custom["frame"], rectangle.size), rectangle)
            else:
                pygame.draw.rect(screen, (75, 62, 51), rectangle, width=1, border_radius=4)
        else:
            draw_figma_rectangle(screen, frame)

        icon_rect = figma_rect(slot["icon"])
        image = assets.get(status.icon_asset) if status.icon_asset else _icon(assets, custom, status.key)
        if image is None:
            label = f"+{len(overflow)}" if status.key == "overflow" else status.name[0]
            draw_figma_text(screen, {**slot["value"], "rect": slot["icon"]}, text_override=label)
        else:
            target = image.get_rect().fit(icon_rect)
            screen.blit(pygame.transform.smoothscale(image, target.size), target)
        if status.count is not None:
            draw_figma_text(screen, slot["value"], text_override=str(status.count))
        if mouse_position is not None and figma_rect(slot["hitbox"]).collidepoint(mouse_position):
            lines = (
                tuple(f"{effect.name}: {effect.details()}" for effect in overflow)
                if status.key == "overflow" else (status.details(),)
            )
            tooltip = TooltipContent(status.name, lines, (181, 145, 81))
    return tooltip
