from acts.act_two.dev_commands import (
    ACT_TWO_CONSOLE_HELP,
    execute_act_two_console_command,
)


CONSOLE_HELP = (
    "help     - list commands",
    "clear    - clear console output",
    "level    - add 1 level and 1 attribute point",
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
        if len(parts) != 1:
            return "Usage: level"

        player.level += 1
        player.attribute_points += 1

        return (
            f"Level: {player.level} (+1). "
            f"Attribute points: {player.attribute_points} (+1)."
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
