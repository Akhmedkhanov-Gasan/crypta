import random
from collections.abc import Callable
from math import ceil

from acts.act_three.combat.paladin import (
    add_paladin_block_chance,
)
from acts.act_three.equipment import apply_armor_bonus, apply_weapon_bonus
from acts.act_three.ability_scaling import (
    basic_attack_damage_range as act_three_basic_attack_damage_range,
)
from acts.act_three.items.drops import drop_from_monster
from acts.act_two.ability_scaling import (
    mage_basic_attack_damage_bonus,
    rogue_ambush_damage_bonus,
)
from acts.act_two.settings import (
    ENEMY_GOLD_DROP_CHANCE,
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
from acts.act_three.abilities import (
    is_ability_slot_unlocked,
)
from acts.act_three.abilities.charges import charge_subclass_abilities
from acts.act_two.bloody_altar import (
    BLOOD_HUNGER,
    adjusted_outgoing_damage,
    has_bloody_pact,
    BLOOD_HUNGER_LIFESTEAL_RATIO,
    try_apply_open_wound_bleed,
)
from game.attributes import attribute_stat_changes_for_rank
from acts.act_two.enemies.oracle.health import (
    limit_oracle_phase_one_damage,
)
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from systems.bleeding import apply_bleed
from game.healing import healing_is_blocked
from game.progression import (
    attribute_points_per_level,
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
from acts.act_three.settings import (
    BERSERKER_LAST_RAGE_CHARGES,
    SUMMONER_TRUE_FORM_CHARGES,
    WARLOCK_CURSE_DAMAGE_MULTIPLIER,
)
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

    if player.health <= 0:
        return False
    from acts.act_three.bloody_altar.catalog import has_pact

    if has_pact(player, "blood_carapace"):
        return False

    rune_chance = (
        WARRIOR_IMPACT_BLOCK_CHANCE
        if (
            player.player_class == "warrior"
            and player.selected_rune_id == "rune_of_impact"
        )
        else 0.0
    )
    block_chance = add_paladin_block_chance(
        player,
        rune_chance,
    )
    from acts.act_three.abilities.summoner_runes import absorption_active

    absorption_guard = absorption_active(player)
    if absorption_guard:
        from acts.act_three.rune_master.definitions import ABSORPTION_BLOCK_CHANCE

        block_chance += ABSORPTION_BLOCK_CHANCE

    if block_chance <= 0 or random.random() >= block_chance:
        return False

    source = (
        "paladin_guard"
        if player.subclass == "paladin"
        else "rune_of_impact"
    )
    if absorption_guard:
        source = "rune_of_absorption"
    if player.subclass == "paladin":
        from acts.act_three.abilities.paladin_runes import tower_shield_active
        import pygame

        if tower_shield_active(player):
            player.act_three.paladin_rune_block_started_at = pygame.time.get_ticks()

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
                "source": source,
                "block_chance": block_chance,
            },
        )
    )

    defender = (
        "Paladin"
        if player.subclass == "paladin"
        else "Rune of Impact"
    )
    if absorption_guard:
        defender = "Absorption"
    add_log_message(
        game_state.combat_log,
        f"{defender} blocks {attacker_name}'s attack.",
        category="defense",
    )
    return True


def damage_player(
    game_state: GameState,
    damage: int,
    damage_kind: str = "physical",
    *,
    is_attack: bool = False,
) -> int:
    player = game_state.player
    if is_attack:
        from acts.act_three.bloody_altar.effects import incoming_attack_damage

        damage = incoming_attack_damage(player, damage)
    stoneflesh_applied = (
        damage_kind == "physical"
        and player.act_two.stoneflesh_hits > 0
    )
    if stoneflesh_applied:
        damage = ceil(
            damage * STONEFLESH_PHYSICAL_DAMAGE_MULTIPLIER
        )
    if damage_kind == "physical":
        damage = apply_armor_bonus(player, damage)
    if damage > 0 and player.act_three.ironblood_guard:
        damage = ceil(damage / 2)
        player.act_three.ironblood_guard = False
    previous_health = player.health
    rage_protected = (
        player.subclass == "berserker"
        and player.berserker_last_rage_hits > 0
        and previous_health > 0
    )
    minimum_health = (
        1
        if rage_protected
        else 0
    )
    player.health = max(
        minimum_health,
        player.health - damage,
    )
    from acts.act_three.bloody_altar.effects import prevent_death

    prevent_death(game_state)
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
        from acts.act_three.abilities.summoner_runes import summoner_ultimate_active

        if not summoner_ultimate_active(player) and is_ability_slot_unlocked(player, "f"):
            player.summoner_true_form_charge = min(
                SUMMONER_TRUE_FORM_CHARGES,
                player.summoner_true_form_charge + 1,
            )

    if (
        damage_dealt > 0
        and player.subclass == "berserker"
        and not rage_protected
        and is_ability_slot_unlocked(player, "f")
    ):
        player.berserker_last_rage_charge = min(
            BERSERKER_LAST_RAGE_CHARGES,
            player.berserker_last_rage_charge + 1,
        )

    if rage_protected and damage > 0:
        from acts.act_three.abilities.last_rage import consume_last_rage_hit

        consume_last_rage_hit(game_state)
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
    suppress_veil_retrigger: bool = False,
    damage_multiplier: float = 1.0,
    basic_attack: bool = False,
) -> bool:
    player = game_state.player
    if basic_attack and player.subclass is not None:
        from acts.act_three.bloody_altar.effects import begin_basic_attack

        begin_basic_attack(player)
    if enemy.possessed_by_summoner and attacker_name in ("hero", "familiar"):
        return False
    veil_passive = (
        player.player_class == "rogue"
        and player.selected_rune_id == "rune_of_the_veil"
    )

    attack_from_invisibility = (
        attacker_name == "hero"
        and player.invisibility_turns > 0
    )
    if attack_from_invisibility:
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
        and enemy.sentinel.recovery_turns == 0
    ):
        enemy.shield_blocks_remaining -= 1
        if basic_attack:
            from acts.act_three.bloody_altar.effects import basic_attack_failed

            basic_attack_failed(player)

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
            from systems.enemy_ai.sentinel import break_sentinel_shield

            break_sentinel_shield(game_state, enemy)

        return False
    if (
        enemy.dodge_chance > 0
        and random.random() < enemy.dodge_chance
    ):
        if basic_attack:
            from acts.act_three.bloody_altar.effects import basic_attack_failed

            basic_attack_failed(player)
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
            "Hero" if attacker_name == "hero" else "Phantom" if attacker_name == "phantom" else "Familiar"
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

    critical_hit = (
        force_critical
        or attack_from_invisibility
        or random.random() < critical_chance
    )

    if player.subclass is not None:
        from acts.act_three.combat.damage import scaled_attack_damage

        damage = scaled_attack_damage(player, enemy, damage, critical_hit, attacker_name, damage_multiplier,
                                      floor=game_state.floor, basic=basic_attack)
    else:
        if enemy.curse_turns > 0:
            damage = ceil(damage * WARLOCK_CURSE_DAMAGE_MULTIPLIER)
        if critical_hit:
            damage = ceil(damage * player.critical_damage_multiplier)
        if attacker_name in ("hero", "phantom"):
            damage = adjusted_outgoing_damage(player, damage)
            damage = apply_weapon_bonus(player, damage)
        if damage_multiplier != 1.0:
            damage = max(1, ceil(damage * damage_multiplier))
    damage = limit_oracle_phase_one_damage(
        enemy,
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

    if attacker_name == "hero":
        from acts.act_three.abilities.paladin_runes import consume_crusade_hit

        consume_crusade_hit(game_state, damage_dealt)
        from acts.act_three.abilities.berserker_runes import record_rage_damage

        record_rage_damage(player, damage_dealt)
        try_apply_open_wound_bleed(
            game_state,
            enemy,
            damage_dealt,
        )
        from acts.act_three.bloody_altar.effects import on_hero_damage

        on_hero_damage(game_state, enemy, damage_dealt)

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
            and not healing_is_blocked(player)
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
                from game.healing import heal_player

                requested_healing = restored_health
                restored_health = heal_player(player, requested_healing, source="lifesteal")
                player.act_two.blood_hunger_healing_progress -= (
                    requested_healing
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
    elif grant_ability_charge and player.subclass is not None and attacker_name == "hero":
        charge_subclass_abilities(player)
    if (
        grant_ability_charge
        and attacker_name == "hero"
        and player.subclass is not None
        and not (player.subclass == "assassin" and player.ultimate_animation_active)
        and player.selected_rune_id not in ("rune_of_the_veil", "rune_of_resonance", "rune_of_impact")
    ):
        player.ability_kill_charge = min(
            ability_charge_required(player),
            player.ability_kill_charge + 1,
        )
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
        "Hero" if attacker_name == "hero" else "Phantom" if attacker_name == "phantom" else "Familiar"
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
            and not attack_from_invisibility
            and not suppress_veil_retrigger
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

    if enemy.possessed_by_summoner:
        from acts.act_three.abilities.summoner_possession import host_defeated

        host_defeated(game_state, enemy)

    from acts.act_three.abilities.warlock_runes import resolve_warlock_defeat

    resolve_warlock_defeat(game_state, enemy)

    from acts.act_three.abilities.berserker_runes import record_rage_kill

    if not enemy.is_summoned:
        record_rage_kill(game_state)

    kills = game_state.run_stats.kills_by_type
    kills[enemy.type] = kills.get(enemy.type, 0) + 1

    if enemy.is_summoned:
        return
    player = game_state.player
    floor = game_state.floor
    player.enemies_defeated += 1

    current_act = game_state.floor.presentation_act
    if current_act == 3:
        from acts.act_three.bloody_altar.effects import record_original_kill
        from acts.act_three.abilities.unlocks import unlock_ultimate_after_boss

        record_original_kill(game_state, enemy)
        unlock_ultimate_after_boss(game_state, enemy)
    if current_act in (2, 3):
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
                    f"Attribute points +{levels_gained * attribute_points_per_level(player)}."
                ),
                category="progress",
            )
    if current_act == 2:
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
    elif current_act == 3:
        drop_from_monster(game_state, enemy)
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
    if not enemy.has_key:
        return

    if floor.presentation_act == 3:
        import pygame
        from acts.act_three.items.drops import place_ground_drop
        from acts.act_three.items.keys import CRYPTA_KEY

        place_ground_drop(floor, CRYPTA_KEY, (enemy.column, enemy.row), pygame.time.get_ticks(), animate=True)
    else:
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
    if player.subclass is not None:
        return act_three_basic_attack_damage_range(player)

    if player.player_class != "mage":
        return player.damage_min, player.damage_max

    valor_contribution = attribute_stat_changes_for_rank(
        "valor",
        player.attribute_ranks.get("valor", 0),
    )
    ability_damage_bonus = mage_basic_attack_damage_bonus(
        player.attribute_ranks.get("will", 0)
    )

    minimum = max(
        1,
        player.damage_min
        - valor_contribution.damage_min
        + ability_damage_bonus,
    )
    maximum = max(
        minimum,
        player.damage_max
        - valor_contribution.damage_max
        + ability_damage_bonus,
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
    from acts.act_three.abilities.warlock_runes import prepare_demon_attack

    if not prepare_demon_attack(game_state):
        return False
    from acts.act_three.abilities.summoner_runes import begin_summoner_attack

    begin_summoner_attack(game_state)

    player = game_state.player
    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)

    player.ability_kill_charge = 0
    player.directional_ability_aiming = False
    game_state.player_attack_targets = [target]

    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    facing_direction = (
        (1 if dx > 0 else -1, 0)
        if abs(dx) > abs(dy)
        else (0, 1 if dy > 0 else -1)
    )

    if floor.presentation_act == 3:
        player.facing_direction = facing_direction
        effect_state = player.act_three.mage_arcane_burst
    else:
        player.act_two_facing_direction = facing_direction
        effect_state = player.act_two
    effect_state.ability_effect_target = target
    effect_state.ability_effect_cells = (target,)
    effect_state.ability_effect_hit_positions = (target,)
    effect_state.ability_effect_kind = "resonance"

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

    from acts.act_three.abilities.summoner_runes import finish_summoner_attack

    finish_summoner_attack(game_state)
    return True


def perform_basic_attack(
    game_state: GameState,
    column_change: int,
    row_change: int,
    oracle_hit_reaction: OracleHitReaction,
) -> None:
    from acts.act_three.abilities.summoner_runes import begin_summoner_attack, finish_summoner_attack

    begin_summoner_attack(game_state)
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
    ambush_damage_bonus = (
        rogue_ambush_damage_bonus(
            player.attribute_ranks.get("instinct", 0)
        )
        if (
            attack_was_from_invisibility
            and selected_rune_id != "rune_of_the_veil"
        )
        else 0
    )

    for hit_enemy in enemies_hit:
        health_before_attack = hit_enemy.health
        enemy_was_defeated = attack_enemy(
            game_state,
            hit_enemy,
            damage_minimum,
            damage_maximum,
            player.crit_chance,
            damage_bonus=ambush_damage_bonus,
            basic_attack=True,
            force_critical=attack_was_from_invisibility,
            suppress_veil_retrigger=(
                attack_was_from_invisibility
            ),
            grant_ability_charge=(
                not attack_was_from_invisibility
                or selected_rune_id == "rune_of_the_veil"
                or (
                    floor.presentation_act == 3
                    and player.subclass == "assassin"
                )
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
            apply_bleed(
                hit_enemy,
                max(
                    1,
                    ceil(damage_dealt * ROGUE_CRUELTY_BLEED_RATIO),
                ),
                ROGUE_CRUELTY_BLEED_TURNS,
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
    finish_summoner_attack(game_state)

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
