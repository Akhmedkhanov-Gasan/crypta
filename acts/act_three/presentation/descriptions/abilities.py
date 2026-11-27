from acts.act_three.ability_scaling import (
    archer_shot_damage_range, basic_attack_damage_range, familiar_damage_range,
    magical_attack_damage_range, paladin_ground_damage_bonus,
)
from acts.act_three.presentation.descriptions.combat import (
    block_lines, current_damage_range, damage_range_text,
)
from acts.act_three.rune_master.definitions import equipped_rune
from acts.act_three.settings import (
    ARCHER_BASIC_ATTACK_RANGE, BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER,
    BERSERKER_RAGE_CRITICAL_HEALTH_RATIO, BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER,
    BERSERKER_RAGE_INJURED_HEALTH_RATIO, PALADIN_SACRED_GROUND_DAMAGE_MIN,
    PALADIN_SACRED_GROUND_DAMAGE_MAX, SUMMONER_TRUE_FORM_DAMAGE_BONUS,
    SUMMONER_TRUE_FORM_HEALTH_BONUS,
)


def passive_lines(player):
    if player.subclass == "warlock":
        from acts.act_three.abilities.blood_magic import skill_health_cost
        from acts.act_three.balance import WARLOCK_SKILL_HEALTH_COST_RATIOS

        return (
            "Blood Magic: skills use HP instead of attack charges.",
            f"Q / E: {WARLOCK_SKILL_HEALTH_COST_RATIOS['q']:.0%} / {WARLOCK_SKILL_HEALTH_COST_RATIOS['e']:.0%} maximum HP; form entry: {WARLOCK_SKILL_HEALTH_COST_RATIOS['f']:.0%}.",
            f"Current costs: Q {skill_health_cost(player, 'q')}, E {skill_health_cost(player, 'e')}, F {skill_health_cost(player, 'f')} HP.",
            "Rounded up; casting must leave at least 1 HP. Cancelling aim and leaving the form are free.",
            "Demon Form's attack HP cost is additional. Passive rune effects do not pay a casting cost.",
        )
    if player.subclass == "paladin":
        return block_lines(player)
    if player.subclass == "berserker":
        return (
            f"Rage: x{BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER:g} damage at {BERSERKER_RAGE_INJURED_HEALTH_RATIO:.0%} HP or less; x{BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER:g} at {BERSERKER_RAGE_CRITICAL_HEALTH_RATIO:.0%} or less.",
            "Last Rage uses the stronger bonus regardless of current HP. The two Rage bonuses do not stack.",
            f"Current ordinary hit: {damage_range_text(current_damage_range(player))} before target bonuses.",
        )
    if player.subclass == "assassin":
        return (
            "Shadow Reflex: dodging a direct enemy attack immediately counterattacks its source, including ranged attackers.",
            f"Counterattack: {damage_range_text(current_damage_range(player))} before critical hits and target bonuses.",
            "Uses physical attack damage and your critical chance; does not generate ability charges.",
        )
    if player.subclass == "archer":
        return (
            f"Marksman: shoot a visible enemy within {ARCHER_BASIC_ATTACK_RANGE} cells with a clear line of sight.",
            f"Shot: {damage_range_text(current_damage_range(player))} before critical hits and target bonuses.",
            "Valor increases shot damage; Instinct increases critical chance and dodge.",
        )
    return (
        "The bound familiar lets you attack at range. Q releases it to fight independently; Q recalls it.",
        f"Familiar / totem: {damage_range_text(current_damage_range(player, familiar_damage_range(player), attacker='familiar'))} damage; cannot critically hit.",
        "Will increases your attacks and spirit damage. Releasing the familiar reduces your attack damage to 65% and range to 2 cells.",
    )


def ability_damage_lines(player, slot):
    rune = equipped_rune(player, slot) if slot != "e" else None
    identifier = rune.id if rune else player.selected_rune_id if slot == "e" else None
    if identifier in ("rune_of_impact", "rune_of_tower_shield"):
        return block_lines(player)
    values = basic_attack_damage_range(player)
    lines = ()
    if slot == "e":
        if player.player_class == "warrior" and identifier != "rune_of_impact":
            from acts.act_two.ability_scaling import warrior_cleave_damage_bonus

            bonus = warrior_cleave_damage_bonus(player.attribute_ranks.get("valor", 0))
            values = tuple(value + bonus for value in values)
            lines = (f"Physical attack + {bonus} from Power Cleave and Valor.",)
        elif player.player_class == "mage":
            from acts.act_two.ability_scaling import mage_arcane_burst_damage_bonus
            from settings import MAGE_CONCENTRATION_DAMAGE_MULTIPLIER

            if identifier == "rune_of_resonance":
                return (f"Resonance hit: {damage_range_text(current_damage_range(player))}; uses Will and normal critical chance.",)
            bonus = mage_arcane_burst_damage_bonus(player.attribute_ranks.get("will", 0))
            if identifier != "rune_of_fracture":
                values = tuple(value + bonus for value in values)
            if identifier == "rune_of_concentration":
                values = tuple(value * MAGE_CONCENTRATION_DAMAGE_MULTIPLIER for value in values)
            lines = ("Magic attack and burst bonus scale with Will.",)
        else:
            return ()
    elif player.subclass == "archer" and slot == "q":
        from acts.act_three.rune_master.definitions import EMERALD_DAMAGE_MULTIPLIER

        values = archer_shot_damage_range(player)
        if identifier == "rune_of_emerald_piercing_shot":
            values = tuple(value * EMERALD_DAMAGE_MULTIPLIER for value in values)
        lines = ("Uses physical shot damage and your critical chance.",)
    elif player.subclass == "archer" and slot == "f":
        from acts.act_three.rune_master.definitions import MIRROR_DAMAGE_MULTIPLIER, SPECTRAL_ARCHER_COUNT

        mirror = identifier == "rune_of_phantom_archer"
        ratio = MIRROR_DAMAGE_MULTIPLIER if mirror else 0.25
        values = tuple(value * ratio for value in values)
        count = 1 if mirror else SPECTRAL_ARCHER_COUNT if identifier == "rune_of_spectral_archers" else 2
        return (f"Summons: {count}. Each ordinary shot: {damage_range_text(current_damage_range(player, values, attacker='phantom'))} before critical hits and target bonuses.",
                "Phantoms inherit your shot damage, critical chance, weapon and altar damage bonuses.")
    elif player.subclass == "paladin" and slot == "f":
        if identifier == "rune_of_fervent_crusade":
            return ("The empowered damage bonus multiplies your weapon, critical and altar bonuses.",)
        bonus = paladin_ground_damage_bonus(player)
        values = (PALADIN_SACRED_GROUND_DAMAGE_MIN + bonus, PALADIN_SACRED_GROUND_DAMAGE_MAX + bonus)
        lines = (f"Sacred Ground: {PALADIN_SACRED_GROUND_DAMAGE_MIN}-{PALADIN_SACRED_GROUND_DAMAGE_MAX} base + {bonus} from Will per hit.",)
    elif player.subclass == "summoner":
        if slot == "q":
            if identifier == "rune_of_possession":
                return ("The possessed creature keeps its own attacks, damage and health.",)
            return (f"Spirit hit: {damage_range_text(current_damage_range(player, familiar_damage_range(player), attacker='familiar'))}; scales with Will, weapon and altar damage bonuses.",)
        if slot == "f" and identifier != "rune_of_absorption":
            values = tuple(value + SUMMONER_TRUE_FORM_DAMAGE_BONUS for value in magical_attack_damage_range(player))
            return (f"Spirit hit: {damage_range_text(current_damage_range(player, values, attacker='greater_manifestation'))} before soul and target bonuses; no critical hits.",
                    f"Spirit maximum HP: {max(1, player.max_health // 2) + SUMMONER_TRUE_FORM_HEALTH_BONUS} (half your maximum HP + {SUMMONER_TRUE_FORM_HEALTH_BONUS}).")
        return ()
    elif player.subclass == "warlock":
        if slot == "q":
            from acts.act_three.settings import WARLOCK_CURSE_RANGE, WARLOCK_CURSE_TURNS

            return (f"Range {WARLOCK_CURSE_RANGE}; normal Curse lasts {WARLOCK_CURSE_TURNS} turns and multiplies incoming damage by 1.5.",) if identifier != "rune_of_madness" else ()
        from acts.act_three.abilities.warlock_runes import demon_attack_cost, demon_damage_multiplier

        if player.warlock_demon_form_active:
            return (f"Next form attack: x{demon_damage_multiplier(player, next_attack=True):.2f} damage; costs {demon_attack_cost(player)} HP even if blocked or dodged.",)
        return ()
    elif player.subclass == "assassin":
        if slot == "q":
            return ()
        if identifier == "rune_of_the_executioner":
            from acts.act_three.rune_master.definitions import EXECUTIONER_DAMAGE_MULTIPLIER

            values = tuple(value * EXECUTIONER_DAMAGE_MULTIPLIER for value in values)
        lines = ("Damage shown per strike; marks can repeat on the same target.",)
    elif player.subclass == "berserker" and slot == "f":
        return (f"Protected hits remaining: {player.berserker_last_rage_hits}.",) if player.berserker_last_rage_hits > 0 else ()
    normal = damage_range_text(current_damage_range(player, values))
    critical = damage_range_text(current_damage_range(player, values, critical=True))
    return (*lines, f"Current hit: {normal}; critical: {critical}, before target bonuses.")
