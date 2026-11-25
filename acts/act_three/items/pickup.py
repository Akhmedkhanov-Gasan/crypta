import pygame


def request_item_pickup(floor, item, on_pickup, take_all=False):
    pygame.event.post(pygame.event.Event(
        pygame.KEYDOWN,
        key=pygame.K_UNKNOWN,
        act_three_pickup_item=item,
        act_three_pickup_floor=floor,
        act_three_pickup_callback=on_pickup,
        act_three_pickup_all=take_all,
    ))


def resolve_item_pickup(game_state, event, current_time):
    from acts.ground_items import ground_items_at_player, pick_up_ground_item

    floor = game_state.floor
    if floor is not event.act_three_pickup_floor or game_state.player.health <= 0:
        return False
    item = event.act_three_pickup_item
    if not pick_up_ground_item(game_state, item, current_time):
        return False
    event.act_three_pickup_callback(floor, item, current_time)
    if event.act_three_pickup_all:
        while True:
            remaining = ground_items_at_player(game_state, current_time)
            if not remaining:
                break
            item = remaining[0]
            if not pick_up_ground_item(game_state, item, current_time):
                break
            event.act_three_pickup_callback(floor, item, current_time)
    return True
