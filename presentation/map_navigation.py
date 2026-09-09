from dataclasses import dataclass, field
from weakref import WeakKeyDictionary

import pygame

from presentation.figma_ui import figma_rect


TRAIL_LIMIT = 10
TRAIL_COLOR = (0, 0, 0)
TRAIL_MAX_ALPHA = 210
TRAIL_DRAW_DELAY = 180

TRAIL_GLOW_COLOR = (255, 255, 255)
TRAIL_GLOW_ALPHA = 90
TRAIL_GLOW_SCALE = 1.7

_NAVIGATION_STATES = WeakKeyDictionary()

_ZOOM_KEYS = {
    pygame.K_EQUALS: 1,
    pygame.K_PLUS: 1,
    pygame.K_KP_PLUS: 1,
    pygame.K_MINUS: -1,
    pygame.K_KP_MINUS: -1,
}


@dataclass
class MapNavigationState:
    overview: bool = False
    trail: list[
        tuple[
            tuple[int, int],
            tuple[int, int],
            int,
        ]
    ] = field(default_factory=list)
    last_position: tuple[int, int] | None = None


def get_map_navigation(floor):
    state = _NAVIGATION_STATES.get(floor)
    if state is None:
        state = MapNavigationState()
        _NAVIGATION_STATES[floor] = state
    return state


def record_map_position(floor):
    state = get_map_navigation(floor)
    position = (floor.player_column, floor.player_row)

    if state.last_position is None:
        state.last_position = position
        return

    if state.last_position == position:
        return

    previous_position = state.last_position
    state.last_position = position

    direction = (
        position[0] - previous_position[0],
        position[1] - previous_position[1],
    )

    state.trail[:] = [
        (point, old_direction, created_at)
        for point, old_direction, created_at in state.trail
        if point not in (position, previous_position)
    ]

    state.trail.append(
        (
            previous_position,
            direction,
            pygame.time.get_ticks(),
        )
    )

    del state.trail[:-TRAIL_LIMIT]


def draw_map_trail(
    screen,
    floor,
    camera_position,
    tile_size,
    scale,
    viewport,
):
    state = get_map_navigation(floor)
    if not state.overview:
        return

    camera_x, camera_y = camera_position
    current_position = (floor.player_column, floor.player_row)

    previous_clip = screen.get_clip()
    screen.set_clip(previous_clip.clip(viewport))

    try:
        current_time = pygame.time.get_ticks()

        for rank, (position, direction, created_at) in enumerate(
                reversed(state.trail)
        ):
            if (
                    position == current_position
                    or position not in floor.explored_cells
            ):
                continue

            if current_time - created_at < TRAIL_DRAW_DELAY:
                continue

            opacity = max(0.0, 1.0 - rank / TRAIL_LIMIT) ** 1.3
            alpha = round(TRAIL_MAX_ALPHA * opacity)

            if alpha <= 0:
                continue

            stamp = pygame.Surface((11, 13), pygame.SRCALPHA)
            color = (*TRAIL_COLOR, alpha)
            heel_color = (
                *TRAIL_COLOR,
                round(alpha * 0.85),
            )

            pygame.draw.polygon(
                stamp,
                color,
                (
                    (2, 2),
                    (4, 1),
                    (5, 3),
                    (4, 6),
                    (2, 5),
                ),
            )
            pygame.draw.rect(
                stamp,
                heel_color,
                (2, 7, 2, 2),
            )

            pygame.draw.polygon(
                stamp,
                color,
                (
                    (7, 5),
                    (9, 4),
                    (10, 6),
                    (9, 9),
                    (7, 8),
                ),
            )
            pygame.draw.rect(
                stamp,
                heel_color,
                (7, 10, 2, 2),
            )

            angle = pygame.Vector2(direction).angle_to((0, -1))
            stamp = pygame.transform.rotate(stamp, angle)

            column, row = position
            center = (
                viewport.x
                + round(
                    (column * tile_size + tile_size / 2 - camera_x)
                    * scale
                ),
                viewport.y
                + round(
                    (row * tile_size + tile_size / 2 - camera_y)
                    * scale
                ),
            )

            mask = pygame.mask.from_surface(stamp, threshold=1)

            trail_surface = mask.to_surface(
                setcolor=(
                    *TRAIL_GLOW_COLOR,
                    round(TRAIL_GLOW_ALPHA * opacity),
                ),
                unsetcolor=(0, 0, 0, 0),
            )

            trail_size = (
                max(1, round(trail_surface.get_width() * TRAIL_GLOW_SCALE)),
                max(1, round(trail_surface.get_height() * TRAIL_GLOW_SCALE)),
            )

            trail_surface = pygame.transform.smoothscale(
                trail_surface,
                trail_size,
            )

            screen.blit(
                trail_surface,
                trail_surface.get_rect(center=center),
            )
    finally:
        screen.set_clip(previous_clip)


class CameraControls:
    def __init__(self, layout, images, font):
        self.rectangle = figma_rect(layout["rect"])
        self.font = font

        self.rectangles = {
            "normal": figma_rect(layout["normal"]),
            "overview": figma_rect(layout["overview"]),
            "buttons": figma_rect(layout["buttons"]["image"]),
        }
        self.images = {
            name: pygame.transform.smoothscale(
                images[name],
                rectangle.size,
            )
            for name, rectangle in self.rectangles.items()
        }
        self.buttons = {
            -1: figma_rect(layout["buttons"]["minus_hitbox"]),
            1: figma_rect(layout["buttons"]["plus_hitbox"]),
        }

    def event_direction(self, event, position, offset=(0, 0)):
        if event.type == pygame.KEYDOWN:
            return _ZOOM_KEYS.get(event.key)

        if (
            event.type != pygame.MOUSEBUTTONDOWN
            or event.button != 1
            or position is None
        ):
            return None

        for direction, rectangle in self.buttons.items():
            if rectangle.move(offset).collidepoint(position):
                return direction

        if self.rectangle.move(offset).collidepoint(position):
            return 0

        return None

    def draw(
        self,
        screen,
        overview,
        mouse_position,
        enabled=True,
        offset=(0, 0),
    ):
        mode = "overview" if overview else "normal"

        for name in ("buttons", mode):
            screen.blit(
                self.images[name],
                self.rectangles[name].move(offset),
            )

        for direction, rectangle in self.buttons.items():
            disabled = (
                not enabled
                or (direction == -1 and overview)
                or (direction == 1 and not overview)
            )
            if disabled:
                shade = pygame.Surface(rectangle.size, pygame.SRCALPHA)
                shade.fill((0, 0, 0, 125))
                screen.blit(shade, rectangle.move(offset))

        panel_rectangle = self.rectangle.move(offset)
        if (
            mouse_position is None
            or not panel_rectangle.collidepoint(mouse_position)
        ):
            return

        label = "Overview" if overview else "Normal view"
        text = self.font.render(
            f"{label}  |  - / +",
            True,
            (225, 211, 186),
        )
        tooltip = text.get_rect().inflate(16, 10)
        tooltip.midbottom = (
            panel_rectangle.centerx,
            panel_rectangle.top - 5,
        )

        if tooltip.top < 0:
            tooltip.midtop = (
                panel_rectangle.centerx,
                panel_rectangle.bottom + 5,
            )

        tooltip.clamp_ip(screen.get_rect())
        pygame.draw.rect(screen, (25, 23, 22), tooltip, border_radius=4)
        pygame.draw.rect(
            screen,
            (99, 86, 68),
            tooltip,
            width=1,
            border_radius=4,
        )
        screen.blit(text, text.get_rect(center=tooltip.center))
