import random
from collections.abc import Callable
from math import ceil

from acts.act_two.settings import (
    ENEMY_GOLD_DROP_CHANCE,
    MAGE_BASIC_ATTACK_SPELL_POWER_SCALING,
    STONEFLESH_PHYSICAL_DAMAGE_MULTIPLIER,
)
from settings import (
    WARRIOR_IMPACT_BLOCK_CHANCE,
    ROGUE_CRUELTY_BLEED_RATIO,
    ROGUE_CRUELTY_BLEED_TURNS,
    ROGUE_SHADE_INVISIBILITY_TURNS,
    ROGUE_VEIL_INVISIBILITY_TURNS,
)
from acts.act_two.abilities import ability_charge_required
from acts.act_two.bloody_altar import (
    BLOOD_HUNGER,
    adjusted_outgoing_damage,
    has_bloody_pact,
    BLOOD_HUNGER_LIFESTEAL_RATIO,
)
from acts.player_stats import attribute_stat_changes_for_rank
from bosses.oracle import ORACLE_LEGACY_COMBAT_ENABLED
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.progression import (
    experience_reward_for_enemy,
    grant_experience,
)
from game.state import (
    EnemyBehaviorState,
    EnemyState,
    FloorState,
    GameState,
)
from logic import (
    get_directional_line,
    get_enemy_occupied_positions,
    get_mage_resonance_target,
    roll_player_damage,
)
from settings import (
    ARCHER_EMPOWERED_SHOT_CHARGES,
    ARCHER_BARRAGE_ZONE_CHARGES,
    ARCHER_LEAP_CHARGES,
    BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER,
    BERSERKER_RAGE_CRITICAL_HEALTH_RATIO,
    BERSERKER_CRUSHING_LEAP_CHARGES,
    BERSERKER_LAST_RAGE_CHARGES,
    BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER,
    BERSERKER_RAGE_INJURED_HEALTH_RATIO,
    CLASS_ABILITY_KILLS,
    PALADIN_HOLY_HAND_CHARGES,
    PALADIN_HOLY_SHIELD_CHARGES,
    PALADIN_HOLY_SHIELD_DAMAGE_BONUS,
    PALADIN_HOLY_SHIELD_HEALING_PER_HIT,
    PALADIN_SHIELD_CHARGE_CHARGES,
    WARLOCK_CURSE_CHARGES,
    WARLOCK_CURSE_DAMAGE_MULTIPLIER,
    WARLOCK_SOUL_EXCHANGE_CHARGES,
    SUMMONER_FAMILIAR_CHARGES,
    SUMMONER_BOND_CHARGES,
    SUMMONER_BOND_DAMAGE_BONUS,
    SUMMONER_TRUE_FORM_CHARGES,
    SUMMONER_TRUE_FORM_DAMAGE_BONUS,
)
from settings import ASSASSIN_TELEPORT_CHARGES
from settings import ASSASSIN_ULTIMATE_CHARGES
from systems.enemy_spawning import try_spawn_enemy_after_death
from systems.mimic import release_mimic_loot


OracleHitReaction = Callable[
    [EnemyState, FloorState, list[str]],
    None,
]


def try_block_enemy_attack(
    game_state: GameState,
    attacker_name: str,
    attacker_position: tuple[int, int] | None = None,
) -> bool:
    player = game_state.player
    if (
        player.health <= 0
        or player.player_class != "warrior"
        or player.selected_rune_id != "rune_of_impact"
    ):
        return False

    if random.random() >= WARRIOR_IMPACT_BLOCK_CHANCE:
        return False

    game_state.emit(
        GameEvent(
            type=GameEventType.ABILITY,
            actor="hero",
            target="hero",
            origin=attacker_position,
            destination=(
                game_state.floor.player_column,
                game_state.floor.player_row,
            ),
            data={
                "ability": "impact_block",
                "source": "rune_of_impact",
            },
        )
    )
    add_log_message(
        game_state.combat_log,
        f"Rune of Impact blocks {attacker_name}'s attack.",
        category="defense",
    )
    return True


def damage_player(
    game_state: GameState,
    damage: int,
    damage_kind: str = "physical",
) -> int:
    player = game_state.player
    stoneflesh_applied = (
        damage_kind == "physical"
        and player.act_two.stoneflesh_hits > 0
    )
    if stoneflesh_applied:
        damage = ceil(
            damage * STONEFLESH_PHYSICAL_DAMAGE_MULTIPLIER
        )
    if (
        player.subclass == "paladin"
        and player.paladin_holy_shield_turns > 0
    ):
        damage = ceil(damage / 2)
    previous_health = player.health
    minimum_health = (
        1
        if (
            player.subclass == "berserker"
            and player.berserker_last_rage_turns > 0
        )
        else 0
    )
    player.health = max(
        minimum_health,
        player.health - damage,
    )
    if player.summoner_bond_active:
        player.summoner_familiar_health = player.health
        if player.health <= 0:
            player.summoner_familiar_active = False
            player.summoner_familiar_position = None
            player.summoner_true_form_active = False
            player.summoner_true_form_charge = 0
            player.summoner_true_form_base_max_health = 0
            player.summoner_bond_active = False
            player.summoner_familiar_death_penalty = True
    damage_dealt = previous_health - player.health
    if stoneflesh_applied and damage_dealt > 0:
        player.act_two.stoneflesh_hits -= 1
        if player.act_two.stoneflesh_hits == 0:
            add_log_message(
                game_state.combat_log,
                "The hero's stoneflesh crumbles away.",
                category="buff",
            )

    if damage_dealt > 0 and player.subclass == "summoner":
        player.summoner_bond_charge = min(
            SUMMONER_BOND_CHARGES,
            player.summoner_bond_charge + 1,
        )
        if not player.summoner_true_form_active:
            player.summoner_true_form_charge = min(
                SUMMONER_TRUE_FORM_CHARGES,
                player.summoner_true_form_charge + 1,
            )

    if (
        damage_dealt > 0
        and player.subclass == "berserker"
        and player.berserker_last_rage_turns <= 0
    ):
        player.berserker_last_rage_charge = min(
            BERSERKER_LAST_RAGE_CHARGES,
            player.berserker_last_rage_charge + 1,
        )

    return damage_dealt

def _prepare_sentinel_counter(
    game_state: GameState,
    sentinel: EnemyState,
) -> None:
    if sentinel.prepared_attack_mode == "shield_counter":
        return

    target = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )

    sentinel.attack_targets = [target]
    sentinel.prepared_attack_mode = "shield_counter"
    sentinel.prepared_attack_target = "hero"
    sentinel.attack_windup_turns_remaining = 1
    sentinel.behavior_state = (
        EnemyBehaviorState.PREPARING_ATTACK
    )

    game_state.emit(
        GameEvent(
            type=GameEventType.PREPARE_ATTACK,
            actor=sentinel.name,
            origin=(
                sentinel.column,
                sentinel.row,
            ),
            positions=(target,),
            data={
                "mode": "shield_counter",
                "enemy_type": sentinel.type,
            },
        )
    )

    add_log_message(
        game_state.combat_log,
        (
            f"{sentinel.name} prepares "
            "a shield counterattack."
        ),
        category="warning",
    )


def attack_enemy(
    game_state: GameState,
    enemy: EnemyState,
    damage_minimum: int,
    damage_maximum: int,
    critical_chance: float,
    damage_bonus: int = 0,
    force_critical: bool = False,
    attacker_position: tuple[int, int] | None = None,
    grant_ability_charge: bool = True,
    attacker_name: str = "hero",
) -> bool:
    player = game_state.player
    veil_passive = (
        player.player_class == "rogue"
        and player.selected_rune_id == "rune_of_the_veil"
    )

    if (
        attacker_name == "hero"
        and veil_passive
        and player.invisibility_turns > 0
    ):
        player.invisibility_turns = 0
        add_log_message(
            game_state.combat_log,
            "The rogue emerges to attack.",
            category="ability",
        )

    from acts.act_two.presentation.bosses.oracle_phase_two import (
        reject_oracle_phase_two_head_hit,
    )

    if reject_oracle_phase_two_head_hit(
        game_state,
        enemy,
        attacker_name,
        attacker_position,
    ):
        return False
    if (
            enemy.type == "sentinel"
            and enemy.shield_blocks_remaining > 0
    ):
        enemy.shield_blocks_remaining -= 1

        game_state.emit(
            GameEvent(
                type=GameEventType.HIT,
                actor=attacker_name,
                target=enemy.name,
                origin=attacker_position,
                destination=(enemy.column, enemy.row),
                amount=0,
                data={
                    "blocked": True,
                    "player_class": player.player_class,
                    "enemy_type": enemy.type,
                    "shield_blocks_remaining": (
                        enemy.shield_blocks_remaining
                    ),
                },
            )
        )

        add_log_message(
            game_state.combat_log,
            (
                f"{enemy.name}'s shield blocks the attack. "
                f"{enemy.shield_blocks_remaining}/"
                f"{enemy.shield_durability} guard remains."
            ),
            category="defense",
        )

        if enemy.shield_blocks_remaining == 0:
            enemy.shield_cooldown = (
                enemy.shield_cooldown_duration
            )
            add_log_message(
                game_state.combat_log,
                f"{enemy.name}'s shield guard breaks.",
                category="defense",
            )
        elif attacker_name == "hero":
            _prepare_sentinel_counter(
                game_state,
                enemy,
            )

        return False
    if (
        enemy.dodge_chance > 0
        and random.random() < enemy.dodge_chance
    ):
        game_state.emit(
            GameEvent(
                type=GameEventType.DODGE,
                actor=attacker_name,
                target=enemy.name,
                origin=attacker_position,
                destination=(enemy.column, enemy.row),
                data={
                    "player_class": player.player_class,
                    "enemy_type": enemy.type,
                },
            )
        )
        attacker_label = (
            "Hero" if attacker_name == "hero" else "Familiar"
        )
        add_log_message(
            game_state.combat_log,
            f"{enemy.name} dodges {attacker_label.lower()}'s attack.",
            category="defense",
        )
        return False

    damage = (
            roll_player_damage(
                damage_minimum,
                damage_maximum,
            )
            + damage_bonus
    )

    if (
            player.subclass == "summoner"
        and player.summoner_bond_active
    ):
        damage += SUMMONER_BOND_DAMAGE_BONUS
    if (
        player.subclass == "summoner"
        and player.summoner_true_form_active
        and attacker_name == "familiar"
    ):
        damage += SUMMONER_TRUE_FORM_DAMAGE_BONUS
    if enemy.curse_turns > 0:
        damage = ceil(
            damage * WARLOCK_CURSE_DAMAGE_MULTIPLIER
        )
    if player.subclass == "berserker" and player.health > 0:
        health_ratio = player.health / player.max_health
        if (
            player.berserker_last_rage_turns > 0
            or health_ratio
            <= BERSERKER_RAGE_CRITICAL_HEALTH_RATIO
        ):
            damage = ceil(
                damage
                * BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER
            )
        elif health_ratio <= BERSERKER_RAGE_INJURED_HEALTH_RATIO:
            damage = ceil(
                damage
                * BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER
            )
    elif (
        player.subclass == "paladin"
        and player.paladin_holy_shield_turns > 0
    ):
        damage += PALADIN_HOLY_SHIELD_DAMAGE_BONUS
    critical_hit = (
        force_critical
        or random.random() < critical_chance
    )

    if critical_hit:
        damage = ceil(
            damage
            * player.critical_damage_multiplier
        )
    if attacker_name == "hero":
        damage = adjusted_outgoing_damage(
            player,
            damage,
        )
    enemy_health_before_hit = enemy.health
    enemy.health = max(
        0,
        enemy.health - damage,
    )

    damage_dealt = (
            enemy_health_before_hit
            - enemy.health
    )
    if (
        enemy.type == "oracle_pillar"
        and damage_dealt > 0
    ):
        from acts.act_two.presentation.bosses.oracle_phase_two import (
            resolve_oracle_pillar_hit,
        )

        resolve_oracle_pillar_hit(
            game_state,
            enemy,
            damage_dealt,
        )

    if (
            attacker_name == "hero"
            and damage_dealt > 0
            and has_bloody_pact(player, BLOOD_HUNGER)
    ):
        if player.health < player.max_health:
            player.act_two.blood_hunger_healing_progress += (
                    damage_dealt
                    * BLOOD_HUNGER_LIFESTEAL_RATIO
            )

            restored_health = min(
                player.max_health - player.health,
                int(
                    player.act_two.blood_hunger_healing_progress
                ),
            )

            if restored_health > 0:
                player.health += restored_health
                player.act_two.blood_hunger_healing_progress -= (
                    restored_health
                )

                game_state.emit(
                    GameEvent(
                        type=GameEventType.HEAL,
                        actor="hero",
                        target="hero",
                        amount=restored_health,
                        data={"kind": BLOOD_HUNGER},
                    )
                )

            if player.health >= player.max_health:
                player.act_two.blood_hunger_healing_progress = 0.0
        else:
            player.act_two.blood_hunger_healing_progress = 0.0
    if (
        player.subclass == "paladin"
        and player.paladin_holy_shield_turns > 0
        and player.health < player.max_health
    ):
        previous_health = player.health
        player.health = min(
            player.max_health,
            player.health
            + PALADIN_HOLY_SHIELD_HEALING_PER_HIT,
        )
        healing = player.health - previous_health
        game_state.emit(
            GameEvent(
                type=GameEventType.HEAL,
                actor="hero",
                target="hero",
                destination=attacker_position,
                amount=healing,
                data={"kind": "paladin_holy_shield"},
            )
        )
        add_log_message(
            game_state.combat_log,
            f"Holy Shield restores {healing} health.",
            category="healing",
        )
    if (
        grant_ability_charge
        and player.player_class is not None
        and player.subclass is None
        and not veil_passive
        and player.selected_rune_id not in (
            "rune_of_resonance",
            "rune_of_impact",
        )
    ):
        player.ability_kill_charge = min(
            ability_charge_required(player),
            player.ability_kill_charge + 1,
        )
    elif (
        grant_ability_charge
        and player.subclass == "assassin"
        and not player.ultimate_animation_active
    ):
        if not veil_passive:
            player.ability_kill_charge = min(
                CLASS_ABILITY_KILLS,
                player.ability_kill_charge + 1,
            )

        player.teleport_charge = min(
            ASSASSIN_TELEPORT_CHARGES,
            player.teleport_charge + 1,
        )
        player.ultimate_charge = min(
            ASSASSIN_ULTIMATE_CHARGES,
            player.ultimate_charge + 1,
        )
    elif grant_ability_charge and player.subclass == "archer":
        player.archer_empowered_shot_charge = min(
            ARCHER_EMPOWERED_SHOT_CHARGES,
            player.archer_empowered_shot_charge + 1,
        )
        player.archer_leap_charge = min(
            ARCHER_LEAP_CHARGES,
            player.archer_leap_charge + 1,
        )
        player.archer_barrage_zone_charge = min(
            ARCHER_BARRAGE_ZONE_CHARGES,
            player.archer_barrage_zone_charge + 1,
        )
    elif grant_ability_charge and player.subclass == "berserker":
        player.berserker_crushing_leap_charge = min(
            BERSERKER_CRUSHING_LEAP_CHARGES,
            player.berserker_crushing_leap_charge + 1,
        )
        if player.berserker_last_rage_turns <= 0:
            player.berserker_last_rage_charge = min(
                BERSERKER_LAST_RAGE_CHARGES,
                player.berserker_last_rage_charge + 1,
            )
    elif grant_ability_charge and player.subclass == "paladin":
        player.paladin_holy_hand_charge = min(
            PALADIN_HOLY_HAND_CHARGES,
            player.paladin_holy_hand_charge + 1,
        )
        player.paladin_shield_charge_charge = min(
            PALADIN_SHIELD_CHARGE_CHARGES,
            player.paladin_shield_charge_charge + 1,
        )
        if player.paladin_holy_shield_turns <= 0:
            player.paladin_holy_shield_charge = min(
                PALADIN_HOLY_SHIELD_CHARGES,
                player.paladin_holy_shield_charge + 1,
            )
    elif grant_ability_charge and player.subclass == "warlock":
        player.warlock_curse_charge = min(
            WARLOCK_CURSE_CHARGES,
            player.warlock_curse_charge + 1,
        )
        player.warlock_soul_exchange_charge = min(
            WARLOCK_SOUL_EXCHANGE_CHARGES,
            player.warlock_soul_exchange_charge + 1,
        )
    elif grant_ability_charge and player.subclass == "summoner":
        if not player.summoner_true_form_active:
            player.summoner_true_form_charge = min(
                SUMMONER_TRUE_FORM_CHARGES,
                player.summoner_true_form_charge + 1,
            )
        player.summoner_bond_charge = min(
            SUMMONER_BOND_CHARGES,
            player.summoner_bond_charge + 1,
        )
        charge_gain = (
            0.5
            if player.summoner_familiar_death_penalty
            else 1.0
        )
        player.summoner_familiar_charge = min(
            SUMMONER_FAMILIAR_CHARGES,
            player.summoner_familiar_charge + charge_gain,
        )
        if (
            player.summoner_familiar_charge
            >= SUMMONER_FAMILIAR_CHARGES
        ):
            player.summoner_familiar_death_penalty = False
    game_state.emit(
        GameEvent(
            type=GameEventType.HIT,
            actor=attacker_name,
            target=enemy.name,
            origin=attacker_position,
            destination=(enemy.column, enemy.row),
            amount=damage,
            data={
                "critical": critical_hit,
                "blocked": False,
                "player_class": player.player_class,
                "enemy_type": enemy.type,
            },
        )
    )

    attacker_label = (
        "Hero" if attacker_name == "hero" else "Familiar"
    )
    if critical_hit:
        add_log_message(
            game_state.combat_log,
            f"{attacker_label} critically hits "
            f"{enemy.name} for {damage}!",
            category="critical",
        )
    else:
        add_log_message(
            game_state.combat_log,
            f"{attacker_label} hits {enemy.name} for {damage}.",
            category="player_attack",
        )

    if (
            attacker_name == "hero"
            and veil_passive
            and critical_hit
            and damage_dealt > 0
    ):
        player.invisibility_turns = ROGUE_VEIL_INVISIBILITY_TURNS
        player.veil_triggered_this_turn = True
        player.ability_kill_charge = 0

        game_state.emit(
            GameEvent(
                type=GameEventType.ABILITY,
                actor="hero",
                destination=(
                    game_state.floor.player_column,
                    game_state.floor.player_row,
                ),
                data={
                    "ability": "invisibility",
                    "source": "rune_of_the_veil",
                },
            )
        )

        add_log_message(
            game_state.combat_log,
            (
                "Rune of the Veil grants "
                f"{ROGUE_VEIL_INVISIBILITY_TURNS} turns of invisibility."
            ),
            category="rune",
        )

    if (
            enemy.type in ("warden", "oracle")
        and enemy.health > 0
        and enemy.health <= enemy.max_health // 2
        and not enemy.second_phase_announced
    ):
        enemy.second_phase_announced = True

        if enemy.type == "oracle":
            enemy.phase_transition_pending = True

        add_log_message(
            game_state.combat_log,
            f"{enemy.name} enters phase two!",
            category="warning",
        )

    if enemy.health <= 0:
        enemy.behavior_state = EnemyBehaviorState.DEAD
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor=enemy.name,
                destination=(enemy.column, enemy.row),
                data={"enemy_type": enemy.type},
            )
        )
        add_log_message(
            game_state.combat_log,
            f"{enemy.name} is defeated.",
            category="death",
        )
        return True

    return False


def resolve_enemy_defeat(
    game_state: GameState,
    enemy: EnemyState,
) -> None:
    if enemy.defeat_rewards_claimed:
        return

    enemy.defeat_rewards_claimed = True

    if enemy.type == "oracle_pillar":
        return

    kills = game_state.run_stats.kills_by_type
    kills[enemy.type] = kills.get(enemy.type, 0) + 1

    if enemy.is_summoned:
        return
    player = game_state.player
    floor = game_state.floor
    player.enemies_defeated += 1

    current_act = game_state.floor.presentation_act
    if current_act == 2:
        experience_reward = experience_reward_for_enemy(enemy.type)
        levels_gained = grant_experience(player, experience_reward)
        add_log_message(
            game_state.combat_log,
            f"{enemy.name} grants {experience_reward} XP.",
            category="progress",
        )
        if levels_gained:
            game_state.emit(
                GameEvent(
                    type=GameEventType.LEVEL_UP,
                    actor="hero",
                    amount=levels_gained,
                    data={"level": player.level},
                )
            )
            add_log_message(
                game_state.combat_log,
                (
                    f"Level {player.level} reached. "
                    f"Attribute point +{levels_gained}."
                ),
                category="progress",
            )
        if random.random() < ENEMY_GOLD_DROP_CHANCE:
            drop_position = (
                enemy.column,
                enemy.row,
            )
            floor.dropped_gold.append(drop_position)
            game_state.emit(
                GameEvent(
                    type=GameEventType.ENVIRONMENT,
                    actor=enemy.name,
                    origin=drop_position,
                    destination=drop_position,
                    data={
                        "kind": "enemy_gold_drop",
                        "amount": 1,
                    },
                )
            )
            add_log_message(
                game_state.combat_log,
                f"{enemy.name} drops one gold.",
                category="loot",
            )
    try_spawn_enemy_after_death(game_state, enemy)
    release_mimic_loot(game_state, enemy)

    if enemy.type == "oracle":
        floor.projectiles.clear()
        floor.oracle_combat = None
        enemy.oracle_cast_amount = 0.0
        enemy.oracle_head_angle = 0.0
        game_state.player_attack_targets = []
        add_log_message(
            game_state.combat_log,
            "The Oracle falls. A passage is revealed.",
            category="quest",
        )
    if (
        player.player_class is not None
        and player.subclass not in (None, "assassin")
        and player.selected_rune_id not in (
            "rune_of_the_veil",
            "rune_of_resonance",
            "rune_of_impact",
        )
    ):
        player.ability_kill_charge = min(
            CLASS_ABILITY_KILLS,
            player.ability_kill_charge + 1,
        )

    if not enemy.has_key:
        return

    floor.dropped_keys.append((enemy.column, enemy.row))
    enemy.has_key = False
    add_log_message(
        game_state.combat_log,
        f"{enemy.name} drops a key.",
        category="loot",
    )


def remove_enemy_corpses_at_position(
    floor: FloorState,
    position: tuple[int, int],
) -> None:
    floor.enemies[:] = [
        enemy
        for enemy in floor.enemies
        if (
            enemy.health > 0
            or position not in get_enemy_occupied_positions(enemy)
        )
    ]


def basic_attack_damage_range(player) -> tuple[int, int]:
    if player.player_class != "mage":
        return player.damage_min, player.damage_max

    strength_contribution = attribute_stat_changes_for_rank(
        "strength",
        player.attribute_ranks.get("strength", 0),
    )
    spell_damage_bonus = ceil(
        player.spell_power
        * MAGE_BASIC_ATTACK_SPELL_POWER_SCALING
    )

    minimum = max(
        1,
        player.damage_min
        - strength_contribution.damage_min
        + spell_damage_bonus,
    )
    maximum = max(
        minimum,
        player.damage_max
        - strength_contribution.damage_max
        + spell_damage_bonus,
    )
    return minimum, maximum


def perform_mage_resonance_attack(
    game_state: GameState,
    target: tuple[int, int],
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    enemy = get_mage_resonance_target(game_state, target)
    if enemy is None:
        return False

    player = game_state.player
    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)

    player.ability_kill_charge = 0
    player.directional_ability_aiming = False
    game_state.player_attack_targets = [target]

    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    player.act_two_facing_direction = (
        (1 if dx > 0 else -1, 0)
        if abs(dx) > abs(dy)
        else (0, 1 if dy > 0 else -1)
    )

    player.act_two.ability_effect_target = target
    player.act_two.ability_effect_cells = (target,)
    player.act_two.ability_effect_hit_positions = (target,)
    player.act_two.ability_effect_kind = "resonance"

    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=origin,
            positions=(target,),
            data={
                "kind": "basic",
                "source": "rune_of_resonance",
            },
        )
    )

    damage_minimum, damage_maximum = basic_attack_damage_range(player)
    defeated = attack_enemy(
        game_state,
        enemy,
        damage_minimum,
        damage_maximum,
        player.crit_chance,
        attacker_position=origin,
    )

    if enemy.type == "oracle" and enemy.oracle_phase != 2:
        oracle_hit_reaction(
            enemy,
            floor,
            game_state.combat_log,
        )

    if defeated:
        resolve_enemy_defeat(game_state, enemy)

    return True


def perform_basic_attack(
    game_state: GameState,
    column_change: int,
    row_change: int,
    oracle_hit_reaction: OracleHitReaction,
) -> None:
    player = game_state.player
    floor = game_state.floor
    attack_was_from_invisibility = (
        player.player_class == "rogue"
        and player.invisibility_turns > 0
    )
    selected_rune_id = player.selected_rune_id

    if attack_was_from_invisibility:
        player.invisibility_turns = 0
        add_log_message(
            game_state.combat_log,
            "The rogue emerges to attack.",
            category="ability",
        )

    blocking_positions = {
        (chest["column"], chest["row"])
        for chest in floor.chests
        if not chest["is_open"]
    }
    blocking_positions.update(
        (crate.column, crate.row)
        for crate in floor.breakable_crates
        if not crate.is_broken
    )
    game_state.player_attack_targets = get_directional_line(
        floor.map,
        floor.player_column,
        floor.player_row,
        column_change,
        row_change,
        1,
        blocking_positions,
    )

    adjacent_position = (
        floor.player_column + column_change,
        floor.player_row + row_change,
    )
    adjacent_pillar = next(
        (
            enemy
            for enemy in floor.enemies
            if (
                enemy.type == "oracle_pillar"
                and enemy.health > 0
                and adjacent_position
                in get_enemy_occupied_positions(enemy)
            )
        ),
        None,
    )

    if adjacent_pillar is not None:
        game_state.player_attack_targets = [
            adjacent_position,
        ]

    living_enemies = [
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
    ]
    enemies_hit = [
        enemy
        for enemy in living_enemies
        if any(
            position in get_enemy_occupied_positions(enemy)
            for position in game_state.player_attack_targets
        )
    ]
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(floor.player_column, floor.player_row),
            positions=tuple(game_state.player_attack_targets),
            data={"kind": "basic"},
        )
    )

    damage_minimum, damage_maximum = basic_attack_damage_range(player)

    for hit_enemy in enemies_hit:
        health_before_attack = hit_enemy.health
        enemy_was_defeated = attack_enemy(
            game_state,
            hit_enemy,
            damage_minimum,
            damage_maximum,
            player.crit_chance,
            damage_bonus=0,
            force_critical=(
                attack_was_from_invisibility
                and selected_rune_id != "rune_of_the_veil"
            ),
            grant_ability_charge=(
                not attack_was_from_invisibility
                or selected_rune_id == "rune_of_the_veil"
            ),
            attacker_position=(
                floor.player_column,
                floor.player_row,
            ),
        )

        if (
            hit_enemy.type == "oracle"
            and hit_enemy.oracle_phase != 2
        ):
            oracle_hit_reaction(
                hit_enemy,
                floor,
                game_state.combat_log,
            )

        if enemy_was_defeated:
            resolve_enemy_defeat(
                game_state,
                hit_enemy,
            )
            if (
                attack_was_from_invisibility
                and selected_rune_id == "rune_of_the_shade"
            ):
                player.invisibility_turns = (
                    ROGUE_SHADE_INVISIBILITY_TURNS
                )
                add_log_message(
                    game_state.combat_log,
                    "Rune of the Shade renews invisibility.",
                    category="rune",
                )
        elif (
            attack_was_from_invisibility
            and selected_rune_id == "rune_of_cruelty"
            and hit_enemy.health < health_before_attack
        ):
            damage_dealt = health_before_attack - hit_enemy.health
            hit_enemy.bleed_turns = ROGUE_CRUELTY_BLEED_TURNS
            hit_enemy.bleed_damage = max(
                1,
                ceil(damage_dealt * ROGUE_CRUELTY_BLEED_RATIO),
            )
            add_log_message(
                game_state.combat_log,
                (
                    f"Rune of Cruelty makes {hit_enemy.name} bleed for "
                    f"{hit_enemy.bleed_damage} damage per turn "
                    f"for {hit_enemy.bleed_turns} turns."
                ),
                category="rune",
            )

from acts.act_three.combat import (
    is_valid_archer_attack_target,
    is_valid_warlock_attack_target,
    perform_warlock_attack,
    perform_archer_attack,
    is_valid_summoner_attack_target,
    perform_summoner_attack,
)


__all__ = [
    "attack_enemy",
    "damage_player",
    "is_valid_archer_attack_target",
    "is_valid_summoner_attack_target",
    "is_valid_warlock_attack_target",
    "perform_archer_attack",
    "perform_basic_attack",
    "perform_mage_resonance_attack",
    "perform_summoner_attack",
    "perform_warlock_attack",
    "resolve_enemy_defeat",
]
