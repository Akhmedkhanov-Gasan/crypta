import pygame

from acts.act_three.settings import BERSERKER_LAST_RAGE_HITS
from game.combat_log import add_log_message


def consume_last_rage_hit(game_state):
    player = game_state.player
    if player.subclass != "berserker" or player.berserker_last_rage_hits <= 0:
        return
    player.berserker_last_rage_hits -= 1
    if player.berserker_last_rage_hits > 0:
        return
    from acts.act_three.abilities.berserker_runes import finish_rage_rune

    finish_rage_rune(game_state, pygame.time.get_ticks())
    add_log_message(game_state.combat_log,
                    "Last Rage is exhausted. Death can claim the berserker again.", category="ability")


def migrate_last_rage(player):
    legacy = player.act_three.berserker_last_rage_turns
    if legacy > 0 and player.berserker_last_rage_hits <= 0:
        player.berserker_last_rage_hits = BERSERKER_LAST_RAGE_HITS
    player.act_three.berserker_last_rage_turns = 0
