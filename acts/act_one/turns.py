def resolve_enemy_turn(*args, **kwargs):
    from systems.enemy_turn import resolve_enemy_turn as shared_turn

    return shared_turn(*args, **kwargs)
