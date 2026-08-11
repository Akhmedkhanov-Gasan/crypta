from acts.act_two.state import SpikeTrapPhase
from settings import TILE_SIZE
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y


def draw_act_two_spike_traps(
    screen,
    traps,
    sprites,
    visible_cells,
    _current_time,
) -> None:
    for trap in traps:
        position = (trap.column, trap.row)
        if position not in visible_cells:
            continue

        left = MAP_OFFSET_X + trap.column * TILE_SIZE
        top = MAP_OFFSET_Y + trap.row * TILE_SIZE
        sprite_name = {
            SpikeTrapPhase.WARNING: "spike_trap_warning",
            SpikeTrapPhase.ACTIVE: "spike_trap_active",
        }.get(trap.phase, "spike_trap_hole")
        screen.blit(sprites[sprite_name], (left, top))


__all__ = ["draw_act_two_spike_traps"]
