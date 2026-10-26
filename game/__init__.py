from importlib import import_module


_EXPORT_MODULES = {
    "EnemyState": "game.state",
    "EnemyBehaviorState": "game.state",
    "FloorState": "game.state",
    "GameState": "game.state",
    "PlayerState": "game.state",
    "create_floor_state": "game.factories",
    "create_game_state": "game.factories",
    "create_player_state": "game.factories",
    "add_log_message": "game.combat_log",
    "GameEvent": "game.events",
    "GameEventType": "game.events",
}


def __getattr__(name):
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(_EXPORT_MODULES))


__all__ = [
    "EnemyState",
    "EnemyBehaviorState",
    "FloorState",
    "GameState",
    "PlayerState",
    "create_floor_state",
    "create_game_state",
    "create_player_state",
    "add_log_message",
    "GameEvent",
    "GameEventType",
]
