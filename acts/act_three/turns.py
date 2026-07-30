def resolve_enemy_turn(*args, **kwargs):
    """Current Act Three turn adapter.

    The implementation deliberately delegates to the shared turn system until
    the new Act Three AI replaces it.
    """

    from systems.enemy_turn import resolve_enemy_turn as shared_turn

    return shared_turn(*args, **kwargs)
