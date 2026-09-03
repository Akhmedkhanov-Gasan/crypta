from acts.act_two.dev_commands import (
    ACT_TWO_CONSOLE_HELP,
    execute_act_two_console_command,
)


CONSOLE_HELP = (
    "help     - list commands",
    "clear    - clear console output",
    "level [X] - add X levels and attribute points (default: 1)",
    "gold     - add 10 gold",
    "gold X   - add X gold",
    *ACT_TWO_CONSOLE_HELP,
    "Up / Down - command history",
    "Esc / ~  - close console",
)


def execute_console_command(game_state, command, close_console):
    parts = command.lower().split()

    if not parts:
        return ""

    name = parts[0]
    player = game_state.player

    if name == "level":
        if len(parts) > 2:
            return "Usage: level or level X"

        amount = 1

        if len(parts) == 2:
            try:
                amount = int(parts[1])
            except ValueError:
                return "Level amount must be a positive integer."

        if amount <= 0:
            return "Level amount must be a positive integer."

        player.level += amount
        player.attribute_points += amount

        return (
            f"Level: {player.level} (+{amount}). "
            f"Attribute points: {player.attribute_points} (+{amount})."
        )

    if name == "gold":
        if len(parts) > 2:
            return "Usage: gold or gold X"

        amount = 10

        if len(parts) == 2:
            try:
                amount = int(parts[1])
            except ValueError:
                return "Gold amount must be a positive integer."

        if amount <= 0:
            return "Gold amount must be a positive integer."

        player.gold_count += amount

        return f"Gold: {player.gold_count} (+{amount})."

    result = execute_act_two_console_command(
        game_state,
        parts,
        close_console,
    )
    if result is not None:
        return result

    return "Unknown command. Type help."
