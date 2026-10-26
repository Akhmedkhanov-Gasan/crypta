from acts.act_one.visibility import update_act_one_visibility
from acts.act_two.class_selection import begin_act_two_awakening


ACT_ONE_CONSOLE_HELP = (
    "wake     - jump to the post-Warden awakening scene",
)


def execute_act_one_console_command(
    parts,
    close_console,
    request_debug_jump,
):
    name = parts[0]

    if name != "wake":
        return None

    if len(parts) != 1:
        return "Usage: wake"

    request_debug_jump("act_one_awakening")
    close_console()
    return "Jumping to the post-Warden awakening scene."


def prepare_act_one_awakening_debug_state(
    game_state,
    current_time,
):
    floor = game_state.floor
    floor.player_column = 18
    floor.player_row = 7
    floor.boss_fight_started = True

    intro = floor.act_one_warden_intro
    if intro is not None:
        intro.started = True
        intro.finished = True
        intro.skip_held_ms = 0
        intro.updated_at = current_time

    for enemy in floor.enemies:
        enemy.health = 0
        enemy.is_active = False
        enemy.attack_targets.clear()
        enemy.prepared_attack_mode = None
        enemy.death_animation_started_at = max(
            1,
            current_time - 2400,
        )

    update_act_one_visibility(floor)
    begin_act_two_awakening(
        game_state,
        current_time,
    )


__all__ = [
    "ACT_ONE_CONSOLE_HELP",
    "execute_act_one_console_command",
    "prepare_act_one_awakening_debug_state",
]
