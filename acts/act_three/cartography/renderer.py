from functools import lru_cache
import math

import pygame

import resource_store as resources
from acts.act_three.cartography.geometry import close_rectangle, map_content_rectangle, map_rectangle, map_viewport
from acts.act_three.cartography.lifecycle import map_visible, minimap_visible
from acts.act_three.cartography.terrain import get_terrain
from acts.act_three.altar import get_upgrade_altar_cells
from acts.act_three.npcs import get_npc_cells
from acts.act_three.presentation.player_locomotion import sample_player_locomotion
from presentation.layout import ACT_THREE_TILE_SIZE
from presentation.movement import smoothstep


_TEXT = (195, 186, 163)
_PLAYER = (238, 215, 159)
_UP = (112, 166, 215)
_DOWN = (196, 82, 78)
_ALTAR = (190, 144, 125)
_PANEL_FRAMES = {}
_FRAME_INTERVAL_MS = 33


@lru_cache(maxsize=16)
def _scaled(image, size):
    return pygame.transform.smoothscale(image, size)


@lru_cache(maxsize=12)
def _font(size):
    return resources.load_font("assets/fonts/Almendra-Regular.ttf", max(10, size))


@lru_cache(maxsize=64)
def _text(value, size):
    return _font(size).render(value, True, _TEXT)


@lru_cache(maxsize=2)
def _overlay(size):
    layer = pygame.Surface(size, pygame.SRCALPHA)
    layer.fill((0, 0, 0, 255))
    return layer


@lru_cache(maxsize=4)
def _effect_buffer(size):
    return pygame.Surface(size, pygame.SRCALPHA)


@lru_cache(maxsize=8)
def _vignette(size, render_scale):
    layer = pygame.Surface(size, pygame.SRCALPHA)
    for inset, alpha in ((0, 55), (2, 26), (4, 12)):
        pygame.draw.rect(layer, (0, 0, 0, alpha), layer.get_rect().inflate(-inset * 2, -inset * 2), max(1, round(3 * render_scale)))
    return layer


@lru_cache(maxsize=64)
def _player_glow(radius, render_scale, pulse):
    extent = radius + round(5 * render_scale) + 1
    glow = pygame.Surface((extent * 2, extent * 2), pygame.SRCALPHA)
    for extra, alpha in ((5, 12), (2, 25)):
        pygame.draw.circle(glow, (*_PLAYER, alpha + pulse), (extent, extent), radius + round(extra * render_scale))
    return glow


@lru_cache(maxsize=4)
def _panel_buffer(size):
    return pygame.Surface(size, pygame.SRCALPHA)


@lru_cache(maxsize=8)
def _frame_opening(image, size):
    opening = pygame.mask.from_surface(_scaled(image, size), threshold=8)
    opening.invert()
    opening = opening.connected_component((size[0] // 2, size[1] // 2))
    return opening.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))


def _icon(image, size):
    rectangle = image.get_rect().fit(pygame.Rect(0, 0, size, size))
    return _scaled(image, rectangle.size)


def _draw_plan(surface, game_state, viewport, images, current_time, full, render_scale):
    floor = game_state.floor
    state = game_state.act_three
    columns, rows = len(floor.map[0]), len(floor.map)
    terrain = get_terrain(floor, current_time)
    pose = sample_player_locomotion(game_state.player, floor, current_time, ACT_THREE_TILE_SIZE)
    player = (pose.position[0] / ACT_THREE_TILE_SIZE + 0.5, pose.position[1] / ACT_THREE_TILE_SIZE + 0.5)
    if full:
        fit = min(viewport.width / columns, viewport.height / rows)
        cell_size = max(1, round(fit * state.map_zoom))
        origin = (
            round(viewport.centerx - columns * cell_size / 2 + state.map_offset[0] * render_scale),
            round(viewport.centery - rows * cell_size / 2 + state.map_offset[1] * render_scale),
        )
    else:
        cell_size = max(2, round(4 * render_scale))
        origin = (round(viewport.centerx - player[0] * cell_size), round(viewport.centery - player[1] * cell_size))

    def point(position):
        return (round(origin[0] + (position[0] + 0.5) * cell_size), round(origin[1] + (position[1] + 0.5) * cell_size))

    previous_clip = surface.get_clip()
    surface.set_clip(previous_clip.clip(viewport))
    try:
        surface.blit(terrain.surface(floor, cell_size, images["floor"]), origin)
        effect = _effect_buffer(viewport.size)
        effect.fill((0, 0, 0, 0))
        for column, row in floor.visible_cells:
            if 0 <= row < rows and 0 <= column < columns and floor.map[row][column] not in ("#", "S"):
                rectangle = pygame.Rect(origin[0] + column * cell_size - viewport.x, origin[1] + row * cell_size - viewport.y, cell_size, cell_size)
                pygame.draw.rect(effect, (192, 175, 132, 18), rectangle)
        for position, started in terrain.reveals.items():
            progress = smoothstep((current_time - started) / 650)
            x, y = point(position)
            rectangle = pygame.Rect(x - viewport.x - cell_size // 2, y - viewport.y - cell_size // 2, cell_size + 1, cell_size + 1)
            pygame.draw.rect(effect, (24, 23, 23, round(230 * (1 - progress))), rectangle)
        surface.blit(effect, viewport)

        icon_size = round((23 if full else 12) * render_scale)
        for npc in floor.act_three_npcs:
            if npc["type"] not in images or not get_npc_cells(npc).intersection(floor.explored_cells):
                continue
            marker = _icon(images[npc["type"]], icon_size)
            center = point((npc["position"][0] + 0.5, npc["position"][1]))
            surface.blit(marker, marker.get_rect(center=center))

        for passage in floor.passages:
            if not passage.discovered and not {passage.wall_position, passage.trigger_position}.intersection(floor.explored_cells):
                continue
            target = passage.target_floor_index
            up = target > game_state.floor_index if target is not None else passage.passage_id in ("exit", "exit_down")
            color = _UP if up else _DOWN
            x, y = point(passage.trigger_position)
            radius = max(3, round((5 if full else 3) * render_scale))
            sign = -1 if up else 1
            pygame.draw.polygon(surface, color, ((x, y + sign * radius), (x - radius, y - sign * radius), (x + radius, y - sign * radius)))

        if get_upgrade_altar_cells(floor).intersection(floor.explored_cells):
            x, y = point((floor.upgrade_altar[0] + 0.5, floor.upgrade_altar[1] + 0.5))
            radius = max(3, round((5 if full else 3) * render_scale))
            pygame.draw.polygon(surface, _ALTAR, ((x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y)), max(1, round(render_scale)))

        x = round(origin[0] + player[0] * cell_size)
        y = round(origin[1] + player[1] * cell_size)
        pulse = (math.sin(current_time / 380) + 1) / 2
        radius = max(3, round((5 if full else 3) * render_scale))
        glow = _player_glow(radius, render_scale, round(12 * pulse))
        surface.blit(glow, glow.get_rect(center=(x, y)))
        direction = pygame.Vector2(game_state.player.act_three.facing_direction)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(0, -1)
        direction = direction.normalize()
        perpendicular = pygame.Vector2(-direction.y, direction.x)
        center = pygame.Vector2(x, y)
        vertices = (center + direction * radius * 1.6, center - direction * radius + perpendicular * radius, center - direction * radius - perpendicular * radius)
        pygame.draw.polygon(surface, (20, 18, 17), vertices, max(1, round(2 * render_scale)))
        pygame.draw.polygon(surface, _PLAYER, vertices)
    finally:
        surface.set_clip(previous_clip)


def _draw_sheet_contents(surface, game_state, layout, images, current_time, full, render_scale):
    panel = map_rectangle(layout, full)
    backing = panel.inflate(-max(4, round(panel.width * 0.035)), -max(4, round(panel.height * 0.045)))
    surface.blit(_scaled(images["backing"], backing.size), backing)
    viewport = map_viewport(layout, full)
    _draw_plan(surface, game_state, viewport, images, current_time, full, render_scale)
    surface.blit(_vignette(backing.size, render_scale), backing)
    if not full:
        return
    content = map_content_rectangle(layout, True)
    font = _font(round(16 * render_scale))
    title = _text("CHART OF THE CRYPT", round(22 * render_scale))
    surface.blit(title, title.get_rect(midtop=(content.centerx, content.top + round(3 * render_scale))))
    close = close_rectangle(layout)
    cross = _text("X", round(16 * render_scale))
    surface.blit(cross, cross.get_rect(center=close.center))
    entries = (("You", None, _PLAYER), ("Up", None, _UP), ("Down", None, _DOWN), ("Trader", "trader", _TEXT), ("Smith", "blacksmith", _TEXT), ("Runes", "rune_master", _TEXT), ("Altar", None, _ALTAR))
    gap = round(18 * render_scale)
    marker_size = round(16 * render_scale)
    labels = [(_text(label, round(16 * render_scale)), icon, color) for label, icon, color in entries]
    width = sum(label.get_width() + marker_size + round(5 * render_scale) for label, _, _ in labels) + gap * (len(labels) - 1)
    x = content.centerx - width // 2
    y = content.bottom - font.get_height() - round(4 * render_scale)
    for label, icon, color in labels:
        center = (x + marker_size // 2, y + font.get_height() // 2)
        if icon is not None:
            marker = _icon(images[icon], marker_size)
            surface.blit(marker, marker.get_rect(center=center))
        elif color == _ALTAR:
            radius = max(2, round(3 * render_scale))
            pygame.draw.polygon(surface, color, ((center[0], center[1] - radius), (center[0] + radius, center[1]), (center[0], center[1] + radius), (center[0] - radius, center[1])), max(1, round(render_scale)))
        else:
            radius = max(2, round(3 * render_scale))
            sign = 1 if color == _DOWN else -1
            pygame.draw.polygon(surface, color, ((center[0], center[1] + sign * radius), (center[0] - radius, center[1] - sign * radius), (center[0] + radius, center[1] - sign * radius)))
        surface.blit(label, (x + marker_size + round(5 * render_scale), y))
        x += label.get_width() + marker_size + round(5 * render_scale) + gap


def _map_panel(game_state, layout, images, current_time, full, render_scale, refresh=True):
    panel = map_rectangle(layout, full)
    state = game_state.act_three
    cache_key = (
        game_state.floor, id(images), panel.size, render_scale,
        state.map_zoom if full else 1.0, state.map_offset if full else (0.0, 0.0),
    )
    cached = _PANEL_FRAMES.get(full)
    if cached is not None and cached[0] == cache_key:
        elapsed = current_time - cached[1]
        if elapsed >= 0 and (not refresh or elapsed < _FRAME_INTERVAL_MS):
            return cached[2]
    key = "full_map" if full else "minimap"
    local_layout = {
        **layout,
        "cartography": {
            **layout["cartography"],
            key: {
                **layout["cartography"][key],
                "frame": {"x": 0, "y": 0, "width": panel.width, "height": panel.height},
            },
        },
    }
    layer = _panel_buffer(panel.size)
    layer.fill((0, 0, 0, 0))
    _draw_sheet_contents(layer, game_state, local_layout, images, current_time, full, render_scale)
    frame = images["full_map_frame" if full else "minimap_frame"]
    layer.blit(_frame_opening(frame, panel.size), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    layer.blit(_scaled(frame, panel.size), (0, 0))
    _PANEL_FRAMES[full] = (cache_key, current_time, layer)
    return layer


def draw_minimap(surface, game_state, assets, current_time):
    if not minimap_visible(game_state):
        return
    layout = assets["act_three_hud_layout"]
    images = assets["act_three_map_images"]
    scale = assets.get("hud_render_scale", 1.0)
    panel = _map_panel(game_state, layout, images, current_time, False, scale, refresh=not game_state.act_three.map_open)
    surface.blit(panel, map_rectangle(layout))


def draw_full_map(surface, game_state, assets, current_time):
    state = game_state.act_three
    if not state.map_open or not map_visible(game_state):
        return
    layout = assets["act_three_hud_layout"]
    images = assets["act_three_map_images"]
    scale = assets.get("hud_render_scale", 1.0)
    opacity = smoothstep((current_time - state.map_opened_at) / 240)
    if state.map_closing_at >= 0:
        opacity *= 1 - smoothstep((current_time - state.map_closing_at) / 180)
    layer = _overlay(surface.get_size())
    layer.set_alpha(round(175 * opacity))
    surface.blit(layer, (0, 0))
    panel = _map_panel(game_state, layout, images, current_time, True, scale)
    rectangle = map_rectangle(layout, True).move(0, round((1 - opacity) * 8 * scale))
    panel.set_alpha(round(255 * opacity))
    surface.blit(panel, rectangle)
    panel.set_alpha(255)
