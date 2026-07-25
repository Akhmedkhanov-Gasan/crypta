from settings import COMBAT_LOG_LIMIT


def add_log_message(combat_log: list[str], message: str) -> None:
    combat_log.append(message)

    if len(combat_log) > COMBAT_LOG_LIMIT:
        combat_log.pop(0)
