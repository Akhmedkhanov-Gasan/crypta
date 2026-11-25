from acts.act_three.presentation.camera import act_three_world_view_size
from acts.act_three.presentation.view import _camera_position
from acts.ground_items import ground_items_at_player
from presentation.ground_items import ground_item_window_layout
from presentation.layout import (
    ACT_THREE_TILE_SIZE,
    ACT_THREE_VIEW_HEIGHT,
    ACT_THREE_VIEW_WIDTH,
    ACT_THREE_VIEW_X,
    ACT_THREE_VIEW_Y,
)
from presentation.tooltips import TooltipContent
from presentation.tooltips.dark import draw_tooltip


PICKUP_NOTICE_MS = 1250


def _cell_anchor(floor, position):
    column, row = position
    camera_x, camera_y = _camera_position(floor)
    width, height = act_three_world_view_size(floor)
    view_x = (column + 0.5) * ACT_THREE_TILE_SIZE - camera_x
    view_y = (row - 0.45) * ACT_THREE_TILE_SIZE - camera_y
    return (
        ACT_THREE_VIEW_X + round(view_x * ACT_THREE_VIEW_WIDTH / width),
        ACT_THREE_VIEW_Y + round(view_y * ACT_THREE_VIEW_HEIGHT / height),
    )


def draw_pickup_feedback(screen, game_state, window, current_time, *, show_prompt, scale=1.0):
    floor = game_state.floor
    items = ground_items_at_player(game_state, current_time)
    notice = window.pickup_notice

    if notice is not None:
        pickup_floor, item, started_at = notice
        elapsed = current_time - started_at
        if pickup_floor is floor and 0 <= elapsed < PICKUP_NOTICE_MS:
            if window.is_open and items:
                panel, _, _ = ground_item_window_layout(
                    screen.get_size(), len(items), window.selected,
                    act_three=True,
                    scale=scale,
                )
                x, y = panel.midtop
            else:
                x, y = _cell_anchor(floor, item.position)
                x, y = round(x * scale), round(y * scale)

            opacity = min(1.0, elapsed / 90, (PICKUP_NOTICE_MS - elapsed) / 280)
            rise = round(16 * scale * elapsed / PICKUP_NOTICE_MS)
            draw_tooltip(
                screen,
                TooltipContent("Picked up", (item.name,), (222, 188, 123)),
                (x, y - rise),
                above=True,
                opacity=opacity,
                scale=scale,
            )
            return

    if not show_prompt or window.is_open or not items:
        return

    action, description = (
        ("[G] Pick up", items[0].name)
        if len(items) == 1
        else ("[G] Search pile", f"{len(items)} items")
    )
    x, y = _cell_anchor(floor, (floor.player_column, floor.player_row))
    draw_tooltip(
        screen,
        TooltipContent(action, (description,), (181, 145, 81)),
        (round(x * scale), round(y * scale)),
        above=True,
        scale=scale,
    )
