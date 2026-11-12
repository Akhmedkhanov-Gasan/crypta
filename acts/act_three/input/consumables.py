import pygame

from acts.act_three.items.use import TARGETED_ITEMS, belt_item, valid_consumable_target
from acts.act_three.presentation.hit_testing import get_act_three_cell_from_position
from acts.act_three.presentation.hud.layout import get_act_three_hud_layout
from acts.act_three.trader_catalog import TRADER_ITEMS
from presentation.figma_ui import figma_rect


def _post_use(slot, target=None):
    pygame.event.post(pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_UNKNOWN, act_three_belt_slot=slot,
        act_three_belt_target=target,
    ))


def activate_belt_slot(player, slot):
    item_id = belt_item(player, slot)
    if item_id in TARGETED_ITEMS:
        player.act_three.consumable_aim_slot = slot
        player.act_three.consumable_aim_target = None
    elif item_id in TRADER_ITEMS:
        _post_use(slot)


def handle_consumable_pointer(event, game_state, mouse_position, movement_available):
    player = game_state.player
    state = player.act_three
    slot = state.consumable_aim_slot
    if slot is not None:
        if event.type not in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            return False
        target = get_act_three_cell_from_position(game_state, mouse_position)
        state.consumable_aim_target = target
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                state.consumable_aim_slot = None
            elif event.button == 1 and valid_consumable_target(game_state, belt_item(player, slot), target):
                _post_use(slot, target)
        return True

    if (
        not movement_available
        or event.type != pygame.MOUSEBUTTONDOWN
        or event.button != 1
        or mouse_position is None
    ):
        return False
    slots = get_act_three_hud_layout()["down_bar"]["consumable_belt"]["slots"]
    for index, name in enumerate(sorted(slots)):
        if not figma_rect(slots[name]["hitbox"]).collidepoint(mouse_position):
            continue
        activate_belt_slot(player, index)
        return True
    return False
