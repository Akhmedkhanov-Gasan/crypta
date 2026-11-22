from acts.act_three.presentation.archer.arrows import draw_arrow_flight, draw_arrow_impact
from acts.act_three.presentation.view import _view_position


def draw_rune_projectiles(surface, game_state, camera_x, camera_y, current_time, tile_size):
    projectiles = game_state.player.act_three.archer_rune_projectiles
    projectiles[:] = [shot for shot in projectiles if current_time < shot["started_at"] + 440]
    for shot in projectiles:
        age = current_time - shot["started_at"]
        if age < 0:
            continue
        start = _view_position(*shot["origin"], camera_x, camera_y)
        end = _view_position(*shot["target"], camera_x, camera_y)
        start = start[0] + tile_size / 2, start[1] + tile_size / 2
        end = end[0] + tile_size / 2, end[1] + tile_size / 2
        if age < 320:
            draw_arrow_flight(surface, start, end, age / 320, phantom=shot["phantom"])
        else:
            draw_arrow_impact(surface, end, (age - 320) / 120, phantom=shot["phantom"])
