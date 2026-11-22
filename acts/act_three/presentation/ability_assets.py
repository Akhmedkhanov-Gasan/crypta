import resource_store as resources
from presentation.layout import ASSET_ROOT


_UI_ROOT = ASSET_ROOT / "ui" / "act_3" / "skills"
ABILITY_ICON_ROOT = _UI_ROOT / "abilities" / "icon"
_SUBCLASS_ICONS = {
    "berserker": ("power_cleave", "crushing_leap", "last_rage",
                  "rune_of_impact", "rune_of_reaping", "rune_of_aftershock"),
    "paladin": ("power_cleave", "shield_charge", "sacred_ground",
                "rune_of_impact", "rune_of_reaping", "rune_of_aftershock"),
    "assassin": ("invisibility", "shadow_step", "killing_spree",
                 "rune_of_the_shade", "rune_of_cruelty", "rune_of_the_veil",
                 "rune_of_displacement", "rune_of_the_doppelganger",
                 "rune_of_carnage", "rune_of_the_executioner"),
    "archer": ("invisibility", "piercing_shot", "barrage_zone",
               "rune_of_the_shade", "rune_of_cruelty", "rune_of_the_veil",
               "rune_of_emerald_piercing_shot", "rune_of_splitfang_arrow",
               "rune_of_phantom_archer", "rune_of_spectral_archers"),
    "warlock": ("arcane_burst", "curse", "demon_form",
                "rune_of_fracture", "rune_of_resonance", "rune_of_concentration"),
    "summoner": ("arcane_burst", "release_familiar", "true_form",
                 "rune_of_fracture", "rune_of_resonance", "rune_of_concentration"),
}


def ability_icon_filename(subclass, identifier):
    if identifier == "barrage_zone":
        identifier = "phantom_retinue"
    if subclass == "archer":
        identifier = {
            "rune_of_the_shade": "rune_of_shade",
            "rune_of_the_veil": "rune_of_veil",
        }.get(identifier, identifier)
    return f"{identifier}.png"


ACT_THREE_ABILITY_ICON_PATHS = {
    f"act_three_{subclass}_{identifier}": (
        ABILITY_ICON_ROOT / subclass / ability_icon_filename(subclass, identifier)
    )
    for subclass, identifiers in _SUBCLASS_ICONS.items()
    for identifier in identifiers
}
ACT_THREE_ABILITY_ICON_PATHS.update({
    f"act_three_{subclass}_passive": _UI_ROOT / "passives" / f"{subclass}.png"
    for subclass in _SUBCLASS_ICONS
})
_LEGACY_ICON_OWNERS = {
    "power_cleave": "berserker",
    "invisibility": "assassin",
    "rune_of_impact": "berserker",
    "rune_of_reaping": "berserker",
    "rune_of_aftershock": "berserker",
    "rune_of_the_shade": "assassin",
    "rune_of_cruelty": "assassin",
    "rune_of_the_veil": "assassin",
    "rune_of_fracture": "warlock",
    "rune_of_resonance": "warlock",
    "rune_of_concentration": "warlock",
}
ACT_THREE_ABILITY_ICON_PATHS.update({
    f"act_three_{identifier}": ACT_THREE_ABILITY_ICON_PATHS[f"act_three_{owner}_{identifier}"]
    for identifier, owner in _LEGACY_ICON_OWNERS.items()
})


def ability_icon_key(player, ability):
    from game.rune_catalog import RUNES_BY_ID

    rune = RUNES_BY_ID.get(player.selected_rune_id) if ability.inherited else None
    if rune is not None and rune.player_class == player.player_class:
        identifier = rune.id
    else:
        identifier = ability.id
    return f"act_three_{player.subclass}_{identifier}"


def load_act_three_ability_assets():
    assets = {}
    images = {}
    for asset_name, path in ACT_THREE_ABILITY_ICON_PATHS.items():
        if not resources.is_file(path):
            continue
        if path not in images:
            images[path] = resources.load_image(str(path)).convert_alpha()
        assets[asset_name] = images[path]
    return assets
