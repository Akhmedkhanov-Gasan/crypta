from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


_TRADER_FRAME_DURATION_MS = 1000
_TRADER_FRAME_SEQUENCE = (0, 1, 2, 3, 2, 1)


def draw_act_two_trader(
    screen,
    trader,
    sprites,
    visible_cells,
    current_time,
):
    if trader is None:
        return

    position = (trader.column, trader.row)
    if position not in visible_cells:
        return

    timeline_frame = (
        current_time // _TRADER_FRAME_DURATION_MS
    ) % len(_TRADER_FRAME_SEQUENCE)
    frame_index = _TRADER_FRAME_SEQUENCE[timeline_frame]

    screen.blit(
        sprites[f"trader_idle_{frame_index}"],
        (
            MAP_OFFSET_X + trader.column * TILE_SIZE,
            MAP_OFFSET_Y + trader.row * TILE_SIZE,
        ),
    )


__all__ = ["draw_act_two_trader"]
