import pygame

from acts.act_two.abilities import is_valid_mage_arcane_burst_target
from acts.act_three.settings import MAGE_ARCANE_BURST_RANGE as ACT_THREE_BURST_RANGE
from logic import get_mage_resonance_target
from settings import MAGE_RESONANCE_RANGE
from acts.act_two.settings import MAGE_ARCANE_BURST_RANGE


def mage_aiming(player):
    return player.player_class == "mage" and player.directional_ability_aiming


def mage_uses_resonance(player):
    return player.selected_rune_id == "rune_of_resonance"


def mage_preview_target(game_state):
    floor = game_state.floor
    return game_state.player.mage_aim_target or (floor.player_column, floor.player_row)


def select_mage_aim_target(game_state, target):
    if target is None:
        return

    floor = game_state.floor
    column, row = target
    if mage_uses_resonance(game_state.player):
        reach = MAGE_RESONANCE_RANGE
    elif floor.presentation_act == 3:
        reach = ACT_THREE_BURST_RANGE
    else:
        reach = MAGE_ARCANE_BURST_RANGE
    if (
        0 <= row < len(floor.map)
        and 0 <= column < len(floor.map[row])
        and abs(column - floor.player_column) <= reach
        and abs(row - floor.player_row) <= reach
    ):
        game_state.player.mage_aim_target = target


def valid_mage_aim_target(game_state, target):
    if mage_uses_resonance(game_state.player):
        return get_mage_resonance_target(game_state, target) is not None
    if game_state.floor.presentation_act == 3:
        from acts.act_three.abilities.mage import is_valid_act_three_arcane_burst_target

        return is_valid_act_three_arcane_burst_target(game_state, target)
    return is_valid_mage_arcane_burst_target(game_state, target)


def mage_target_event(game_state, target):
    if not valid_mage_aim_target(game_state, target):
        return None

    target_key = (
        "resonance_target"
        if mage_uses_resonance(game_state.player)
        else "mage_ability_target"
    )
    return pygame.event.Event(
        pygame.KEYDOWN,
        key=pygame.K_UNKNOWN,
        **{target_key: target},
    )


def post_mage_aim_toggle():
    pygame.event.post(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e, mage_aim_toggle=True)
    )
