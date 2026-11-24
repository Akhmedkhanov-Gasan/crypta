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
    "greater_manifestation": "act_three_summoner_greater_manifestation",
    "familiar": "act_three_summoner_summon_familiar",
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
    if state.summoner_loss_turns > 0:
        yield Status("familiar_loss", "Familiar Recovery", "The familiar cannot be summoned until this penalty expires.",
                     state.summoner_loss_turns, "turns", "act_three_summoner_summon_familiar")
    rage_description = "Maximum Rage; health cannot fall below 1. Each damaging hit spends one protection. No turn limit."
    rage_icon = "act_three_berserker_last_rage"
    if state.berserker_rage_rune == "rune_of_second_wind":
        rage_description += f" Stored healing: {int(state.berserker_deferred_healing)} HP. Released when Last Rage ends."
        rage_icon = "act_three_berserker_rune_of_second_wind"
    elif state.berserker_rage_rune == "rune_of_death_wish":
        rage_description += f" +35% attack damage; healing blocked. Extra protected hits earned: {state.berserker_rage_extensions}/2."
        rage_icon = "act_three_berserker_rune_of_death_wish"
    timed = (
        Status("stun", "Stunned", "You cannot act.", player.stun_turns),
        Status("invisibility", "Invisibility", "Enemies cannot see you.", player.invisibility_turns,
               icon_asset=f"act_three_{player.subclass}_invisibility"),
        Status("regeneration", "Regeneration", "Restores health over time.", state.regeneration_ticks),
        Status("stoneflesh", "Stoneflesh", "Reduces incoming physical damage.", player.act_two.stoneflesh_hits, "hits"),
        Status("last_rage", "Last Rage", rage_description, state.berserker_last_rage_hits, "hits", icon_asset=rage_icon),
        Status("sacred_ground", "Sacred Ground", "Damaging enemy hits remaining. Empty turns do not spend the zone.", state.paladin_sacred_ground_hits, "hits"),
    )
    yield from (status for status in timed if status.count > 0)
    spirit = state.summoner_manifestation
    if spirit is not None and spirit["health"] > 0:
        from acts.act_three.abilities.greater_manifestation import SOUL_DAMAGE_STEP, manifestation_attack_cost

        souls = spirit["souls"]
        description = f"Independent spirit. +{souls * SOUL_DAMAGE_STEP:.0%} damage from souls; next attack costs {manifestation_attack_cost(spirit)} HP. F dismisses it."
        if spirit["devourer"]:
            description += " Each kill restores 90% maximum HP, capped at full health, after paying the attack cost. Lethal costs cannot be healed."
        name = f"Soul Devourer · {souls} souls" if spirit["devourer"] else "Greater Manifestation"
        icon = "rune_of_soul_devourer" if spirit["devourer"] else "greater_manifestation"
        yield Status("greater_manifestation", name, description, spirit["health"], "HP", f"act_three_summoner_{icon}")
    if state.paladin_crusade_hits > 0:
        yield Status("fervent_crusade", "Fervent Crusade", "+75% attack damage. Cannot block or dodge.",
                     state.paladin_crusade_hits, "hits", "act_three_paladin_rune_of_fervent_crusade")
    if player.subclass == "archer" and player.health > 0:
        for phantom in state.archer_phantoms:
            if phantom.shots_remaining > 0:
                yield Status(
                    f"archer_phantom_{phantom.number}",
                    "Phantom Double" if phantom.mirror else f"Phantom {phantom.number}",
                    ("Echoes your attacks, invisibility and Piercing Shot at 50% damage. "
                     "Never attacks independently." if phantom.mirror else
                     "Follows you and fires within 3 cells, prioritizing your target. "
                     "Deals 25% basic shot damage. Fades after its sixth shot."),
                    phantom.shots_remaining,
                    "actions" if phantom.mirror else "shots",
                    "act_three_archer_barrage_zone",
                )
    if state.ironblood_guard:
        yield Status("ironblood_guard", "Ironblood Guard", "Halves the next damaging hit.", 1, "hit")
    if state.warlock_demon_form_active:
        from acts.act_three.abilities.warlock_runes import demon_attack_cost, demon_damage_multiplier

        description = f"Next attack: +{(demon_damage_multiplier(player, next_attack=True) - 1):.0%} damage; {demon_attack_cost(player)} HP cost."
        description += " Permanent; no healing on kills." if state.warlock_eternal_bound else " F reverts to mortal form."
        yield Status("demon_form", "Demon Form", description,
                     icon_asset=f"act_three_warlock_{state.warlock_demon_rune or 'demon_form'}")
    if state.summoner_familiar_active:
        if state.summoner_possession_host is not None:
            yield Status("possession", "Possession", f"The familiar controls {state.summoner_possession_host} until death or transfer. Q selects another host; Escape keeps the current one.",
                         icon_asset="act_three_summoner_rune_of_possession")
        else:
            yield Status("familiar", "Spirit Totem" if state.summoner_familiar_mode == "totem" else "Familiar",
                         "The familiar is on the battlefield.", icon_asset="act_three_summoner_rune_of_spirit_totem" if state.summoner_familiar_mode == "totem" else None)
    if state.summoner_absorption_attacks > 0:
        yield Status("absorption", "Absorption", f"+{(state.summoner_absorption_damage - 1):.0%} attack damage, +25% block chance, attack range 3. The greater spirit's power fades after the last attack.",
                     state.summoner_absorption_attacks, "attacks", "act_three_summoner_rune_of_absorption")
    rune = RUNES_BY_ID.get(player.selected_rune_id)
    if rune is not None:
        yield Status(rune.id, rune.name, rune.description,
                     icon_asset=f"act_three_{player.subclass}_{rune.id}")
    pact = BLOODY_PACTS_BY_ID.get(player.act_two.bloody_pact_id)
    if pact is not None:
        yield Status(pact.id, pact.name, f"{pact.reward} {pact.sacrifice}")
    passive = get_passive_definition(player.subclass)
    if passive is not None:
        description = passive.description
        if player.subclass == "paladin":
            from acts.act_three.combat.paladin import add_paladin_block_chance
            from settings import WARRIOR_IMPACT_BLOCK_CHANCE

            chance = add_paladin_block_chance(player, WARRIOR_IMPACT_BLOCK_CHANCE if player.selected_rune_id == "rune_of_impact" else 0)
            description = f"Current total block chance: {chance:.0%}. Includes equipped runes; disabled during Fervent Crusade."
        yield Status(passive.id, passive.name, description, icon_asset=passive.icon_asset)


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
