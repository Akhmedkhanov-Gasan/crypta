import resource_store as resources
from presentation.layout import ASSET_ROOT


_UI_ROOT = ASSET_ROOT / "act_3" / "ui"


ACT_THREE_ABILITY_ICON_PATHS = {
    "act_three_power_cleave": (
        _UI_ROOT
        / "abilities"
        / "inherited"
        / "warrior"
        / "power_cleave.png"
    ),
    "act_three_invisibility": (
        _UI_ROOT
        / "abilities"
        / "inherited"
        / "rogue"
        / "invisibility.png"
    ),
    "act_three_arcane_burst": (
        _UI_ROOT
        / "abilities"
        / "inherited"
        / "mage"
        / "arcane_burst.png"
    ),
    "act_three_rune_of_impact": (
        _UI_ROOT
        / "abilities"
        / "runes"
        / "warrior"
        / "rune_of_impact.png"
    ),
    "act_three_rune_of_reaping": (
        _UI_ROOT
        / "abilities"
        / "runes"
        / "warrior"
        / "rune_of_reaping.png"
    ),
    "act_three_rune_of_aftershock": (
        _UI_ROOT
        / "abilities"
        / "runes"
        / "warrior"
        / "rune_of_aftershock.png"
    ),
    "act_three_rune_of_the_shade": (
        _UI_ROOT
        / "abilities"
        / "runes"
        / "rogue"
        / "rune_of_the_shade.png"
    ),
    "act_three_rune_of_cruelty": (
        _UI_ROOT
        / "abilities"
        / "runes"
        / "rogue"
        / "rune_of_cruelty.png"
    ),
    "act_three_rune_of_the_veil": (
        _UI_ROOT
        / "abilities"
        / "runes"
        / "rogue"
        / "rune_of_the_veil.png"
    ),
    "act_three_rune_of_fracture": (
        _UI_ROOT
        / "abilities"
        / "runes"
        / "mage"
        / "rune_of_fracture.png"
    ),
    "act_three_rune_of_resonance": (
        _UI_ROOT
        / "abilities"
        / "runes"
        / "mage"
        / "rune_of_resonance.png"
    ),
    "act_three_rune_of_concentration": (
        _UI_ROOT
        / "abilities"
        / "runes"
        / "mage"
        / "rune_of_concentration.png"
    ),
    "act_three_berserker_crushing_leap": (
        _UI_ROOT
        / "abilities"
        / "subclasses"
        / "berserker"
        / "crushing_leap.png"
    ),
    "act_three_berserker_last_rage": (
        _UI_ROOT
        / "abilities"
        / "subclasses"
        / "berserker"
        / "last_rage.png"
    ),
    "act_three_paladin_shield_charge": (
        _UI_ROOT
        / "abilities"
        / "subclasses"
        / "paladin"
        / "shield_charge.png"
    ),
    "act_three_paladin_sacred_ground": (
        _UI_ROOT
        / "abilities"
        / "subclasses"
        / "paladin"
        / "sacred_ground.png"
    ),
    "act_three_assassin_shadow_step": (
        _UI_ROOT
        / "abilities"
        / "subclasses"
        / "assassin"
        / "shadow_step.png"
    ),
    "act_three_assassin_killing_spree": (
        _UI_ROOT
        / "abilities"
        / "subclasses"
        / "assassin"
        / "killing_spree.png"
    ),
    "act_three_archer_piercing_shot": (
        _UI_ROOT
        / "abilities"
        / "subclasses"
        / "archer"
        / "piercing_shot.png"
    ),
    "act_three_archer_barrage_zone": (
        _UI_ROOT
        / "abilities"
        / "subclasses"
        / "archer"
        / "barrage_zone.png"
    ),
    "act_three_warlock_curse": (
        _UI_ROOT
        / "abilities"
        / "subclasses"
        / "warlock"
        / "curse.png"
    ),
    "act_three_warlock_demon_form": (
        _UI_ROOT
        / "abilities"
        / "subclasses"
        / "warlock"
        / "demon_form.png"
    ),
    "act_three_summoner_release_familiar": (
        _UI_ROOT
        / "abilities"
        / "subclasses"
        / "summoner"
        / "release_familiar.png"
    ),
    "act_three_summoner_true_form": (
        _UI_ROOT
        / "abilities"
        / "subclasses"
        / "summoner"
        / "true_form.png"
    ),
    "act_three_berserker_passive": (
        _UI_ROOT / "passives" / "berserker.png"
    ),
    "act_three_paladin_passive": (
        _UI_ROOT / "passives" / "paladin.png"
    ),
    "act_three_assassin_passive": (
        _UI_ROOT / "passives" / "assassin.png"
    ),
    "act_three_archer_passive": (
        _UI_ROOT / "passives" / "archer.png"
    ),
    "act_three_warlock_passive": (
        _UI_ROOT / "passives" / "warlock.png"
    ),
    "act_three_summoner_passive": (
        _UI_ROOT / "passives" / "summoner.png"
    ),
}


def load_act_three_ability_assets():
    assets = {}

    for asset_name, path in (
        ACT_THREE_ABILITY_ICON_PATHS.items()
    ):
        if not resources.is_file(path):
            continue

        assets[asset_name] = (
            resources.load_image(
                str(path)
            ).convert_alpha()
        )

    return assets
