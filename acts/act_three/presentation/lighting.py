
import pygame




_TORCH_LIGHT_SURFACE = None
_IDLE_FRAME_SEQUENCE = (0, 1, 2, 1)
_IDLE_TIMELINE_CYCLE_COUNT = 4
_MOVE_FRAME_COUNT = 2
_MOVE_FRAME_DURATION_MS = 90
_ATTACK_FRAME_DURATION_MS = 240
_FAMILIAR_MOVE_DURATION_MS = 180
_TELEPORT_CAMERA_DURATION_MS = 480
_TELEPORT_EFFECT_DURATION_MS = 600
_ARCHER_BARRAGE_SHOT_EFFECT_MS = 360
_TOP_VOID_CORNER_Y_OFFSET = 47
_TOP_VOID_CORNER_X_OFFSETS = {
    "wall_corner_top_left": -18,
    "wall_corner_top_right": 18,
}
_TOP_VOID_DOUBLE_CORNER_CROP_WIDTH = 24

def _get_torch_light_surface():
    global _TORCH_LIGHT_SURFACE

    if _TORCH_LIGHT_SURFACE is not None:
        return _TORCH_LIGHT_SURFACE

    radius = 112
    light_surface = pygame.Surface(
        (radius * 2, radius * 2)
    )
    light_surface.fill((0, 0, 0))

    for current_radius in range(radius, 0, -2):
        proximity = 1 - current_radius / radius
        intensity = proximity**1.8
        color = (
            round(35 * intensity),
            round(17 * intensity),
            round(5 * intensity),
        )
        pygame.draw.circle(
            light_surface,
            color,
            (radius, radius),
            current_radius,
        )

    _TORCH_LIGHT_SURFACE = light_surface
    return _TORCH_LIGHT_SURFACE
