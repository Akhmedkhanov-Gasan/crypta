import pygame

from acts.act_two.enemies.oracle.behavior import resolve_oracle_hit_reaction
from acts.act_three.npcs import advance_npc_dialog
from acts.act_three.mining.runtime import advance_mining
from acts.act_three.trials.assassin import advance_trial_frame
from acts.act_three.trials.archer import advance_frame as advance_piercing_trial
from acts.act_three.settings import (
    ASSASSIN_ULTIMATE_OUTRO_MS,
    ASSASSIN_ULTIMATE_PRELUDE_MS,
    ASSASSIN_ULTIMATE_STEP_MS,
)
from presentation.layout import ACT_THREE_AWAKENING_END_MS
from systems.player_abilities import resolve_assassin_ultimate


def advance_act_three_frame(game_state, current_act, current_time, sounds):
    from acts.act_three.awakening.runtime import advance_awakening, begin_awakening

    if game_state.act_three_transition_open and game_state.act_three.awakening is None:
        begin_awakening(game_state, current_time)
    if game_state.act_three.awakening is not None:
        advance_awakening(game_state, current_time)
        if game_state.act_three.awakening.phase != "complete":
            return
    if current_act == 3:
        from acts.act_three.bloody_altar.runtime import advance_altar

        advance_altar(game_state, current_time)
        from acts.act_three.quests.trader_urn import advance_trader_quest

        advance_trader_quest(game_state, current_time)
        from acts.act_three.abilities.summoner_lifecycle import maintain_summoner

        maintain_summoner(game_state)
        from acts.act_three.enemies.lantern_warden.encounter import advance_encounter

        advance_encounter(game_state, current_time)
        from acts.act_three.rune_master.trial import advance_trial as advance_rune_trial

        advance_rune_trial(game_state, current_time)
        from acts.act_three.items.drops import advance_monster_loot

        advance_monster_loot(game_state, current_time)
        from acts.act_three.dialogue.runtime import advance_dialogue

        advance_dialogue(game_state, current_time)
        from acts.act_three.trials.safety import maintain_safety

        maintain_safety(game_state)
        if game_state.player.health <= 0 and game_state.player.death_animation_started_at >= 0:
            from game.dialogue import hold_dialogue
            from acts.act_three.presentation.renderer import (
                _OLD_MAN_DIALOGUE_START_MS, _OLD_MAN_DEFEAT_MESSAGE_START_MS, _OLD_MAN_LINES,
            )

            if game_state.player.subclass in _OLD_MAN_LINES:
                elapsed = max(0, current_time - game_state.player.death_animation_started_at)
                held = hold_dialogue(game_state, "act_three_death", elapsed, (
                    (_OLD_MAN_DIALOGUE_START_MS, _OLD_MAN_DEFEAT_MESSAGE_START_MS, _OLD_MAN_LINES[game_state.player.subclass]),
                ))
                game_state.player.death_animation_started_at += elapsed - held
        advance_trial_frame(game_state, current_time)
        advance_piercing_trial(game_state, current_time)
        from acts.act_three.trials.berserker import advance_frame as advance_crushing_trial

        advance_crushing_trial(game_state, current_time)
        from acts.act_three.trials.paladin import advance_frame as advance_shield_trial

        advance_shield_trial(game_state, current_time)
        from acts.act_three.trials.warlock import advance_frame as advance_curse_trial

        advance_curse_trial(game_state, current_time)
        from acts.act_three.trials.summoner import advance_frame as advance_summoner_trial

        advance_summoner_trial(game_state, current_time)
        advance_npc_dialog(game_state, current_time)
        advance_mining(game_state, current_time)
        sounds.environment.update_mining(game_state, current_time)
        sounds.update(game_state.player, current_time)

    if game_state.player.ultimate_animation_active:
        from acts.act_three.abilities.killing_spree_runes import advance_killing_spree

        advance_killing_spree(game_state, resolve_oracle_hit_reaction, current_time)
        animation_duration = (
            ASSASSIN_ULTIMATE_PRELUDE_MS
            + len(game_state.player.ultimate_targets) * ASSASSIN_ULTIMATE_STEP_MS
            + ASSASSIN_ULTIMATE_OUTRO_MS
        )
        if (
            current_time - game_state.player.ultimate_animation_started_at
            >= animation_duration
        ):
            resolve_assassin_ultimate(
                game_state,
                resolve_oracle_hit_reaction,
                current_time,
            )
            game_state.player.ultimate_animation_active = False
            game_state.player.ultimate_animation_started_at = 0
            pygame.event.post(
                pygame.event.Event(
                    pygame.KEYDOWN,
                    key=pygame.K_SPACE,
                    ability_turn_commit=True,
                )
            )

    if (
        game_state.act_three_transition_open
        and game_state.act_three_transition_started_at == 0
    ):
        game_state.act_three_transition_started_at = current_time

    if game_state.act_three.awakening is not None or not game_state.act_three_transition_open:
        return

    if game_state.act_three_visual_started_at == 0:
        return

    if (
        current_time - game_state.act_three_visual_started_at
        < ACT_THREE_AWAKENING_END_MS
    ):
        return

    game_state.act_three_transition_open = False
    if game_state.player.player_class in ("warrior", "rogue", "mage"):
        game_state.subclass_selection_open = True
    else:
        game_state.act_three_debug_class_selection_open = True


__all__ = ["advance_act_three_frame"]
