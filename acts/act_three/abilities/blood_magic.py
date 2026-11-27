from math import ceil

from acts.act_three.balance import WARLOCK_SKILL_HEALTH_COST_RATIOS
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType


def skill_health_cost(player, slot):
    if player.subclass != "warlock" or player.debug_unlimited_abilities:
        return 0
    if slot == "e" and player.selected_rune_id == "rune_of_resonance":
        return 0
    if slot == "f":
        from acts.act_three.rune_master.definitions import has_ability_rune

        if player.warlock_demon_form_active or has_ability_rune(player, "rune_of_blood_pact"):
            return 0
    ratio = WARLOCK_SKILL_HEALTH_COST_RATIOS.get(slot, 0)
    return max(1, ceil(player.max_health * ratio)) if ratio else 0


def can_pay_skill(player, slot, extra_cost=0):
    return player.health > skill_health_cost(player, slot) + extra_cost


def pay_skill_health(game_state, slot, extra_cost=0):
    player = game_state.player
    if player.subclass != "warlock":
        return True
    cost = skill_health_cost(player, slot)
    if not can_pay_skill(player, slot, extra_cost):
        add_log_message(game_state.combat_log,
                        f"Blood Magic needs {cost + extra_cost} HP and must leave at least 1 HP.",
                        category="warning")
        return False
    if cost:
        player.health -= cost
        game_state.emit(GameEvent(type=GameEventType.ABILITY, actor="hero", target="hero", amount=cost,
                                  data={"kind": "blood_magic", "slot": slot}))
    return True
