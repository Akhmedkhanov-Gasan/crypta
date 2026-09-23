from acts.act_three.abilities import (
    get_subclass_definition,
    unlock_ability_slot,
)


ACT_THREE_CONSOLE_HELP = (
    "skills - unlock all abilities and disable charges (Act III)",
)


def execute_act_three_console_command(
    game_state,
    parts,
):
    name = parts[0]

    if name != "skills":
        return None

    if len(parts) != 1:
        return "Usage: skills"

    if game_state.floor.presentation_act != 3:
        return "This command is only available in Act III."

    player = game_state.player
    definition = get_subclass_definition(player.subclass)

    if definition is None:
        return "Choose an Act III subclass first."

    for slot in definition.abilities:
        unlock_ability_slot(player, slot)

    player.debug_unlimited_abilities = True

    return (
        f"All {definition.id} abilities unlocked "
        "with unlimited charges."
    )
