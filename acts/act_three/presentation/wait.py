from game.combat_log import add_log_message
from presentation.wait_indicator import draw_wait_indicator


_WAIT_STATE = None


def record_wait_feedback(game_state, current_time):
    global _WAIT_STATE

    _WAIT_STATE = (game_state.player, game_state.floor, current_time)
    add_log_message(game_state.combat_log, "The player skips a turn and waits.")


def clear_wait_feedback():
    global _WAIT_STATE

    _WAIT_STATE = None


def draw_wait_feedback(surface, game_state, position, sprite, current_time):
    if _WAIT_STATE is None:
        return

    player, floor, started_at = _WAIT_STATE
    if (
        player is not game_state.player
        or floor is not game_state.floor
        or player.health <= 0
    ):
        return

    draw_wait_indicator(
        surface,
        position[0] + sprite.get_width() // 2,
        position[1] - 24,
        current_time,
        started_at,
    )
