TRIAL_MAPS = {
    "summoner": "assets/maps/act_3/trials/summoner_release_familiar/summoner_release_familiar.tmx",
    "warlock": "assets/maps/act_3/trials/warlock_curse/warlock_curse.tmx",
    "paladin": "assets/maps/act_3/trials/paladin_shield_charge/paladin_shield_charge.tmx",
    "berserker": "assets/maps/act_3/trials/berserker_crushing_leap/berserker_crushing_leap.tmx",
    "assassin": "assets/maps/act_3/trials/assassin_shadow_step/assassin_shadow_step.tmx",
    "archer": "assets/maps/act_3/trials/archer_piercing_trial/archer_piercing_trial.tmx",
}


def trial_map_path(subclass):
    return TRIAL_MAPS.get(subclass, TRIAL_MAPS["assassin"])
