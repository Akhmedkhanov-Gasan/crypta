import re

from enemies import ENEMY_TYPES
from settings import COMBAT_LOG_LIMIT


_ENEMY_DISPLAY_NAMES = tuple(
    sorted(
        {
            config["display_name"]
            for config in ENEMY_TYPES.values()
        }
        | {"Goblin Reinforcement"},
        key=len,
        reverse=True,
    )
)

_ENEMY_NUMBER_PATTERN = re.compile(
    rf"\b("
    + "|".join(
        re.escape(name)
        for name in _ENEMY_DISPLAY_NAMES
    )
    + rf") \d+\b"
)


def _remove_enemy_numbers(text: str) -> str:
    return _ENEMY_NUMBER_PATTERN.sub(
        r"\1",
        text,
    )


class LogMessage(str):
    def __new__(
        cls,
        text: str,
        category: str = "neutral",
    ):
        visible_text = _remove_enemy_numbers(text)

        message = super().__new__(
            cls,
            visible_text,
        )
        message.category = category
        return message


def add_log_message(
    combat_log: list[str],
    message: str,
    category: str = "neutral",
) -> None:
    combat_log.append(
        LogMessage(message, category)
    )

    if len(combat_log) > COMBAT_LOG_LIMIT:
        combat_log.pop(0)
