from weakref import WeakKeyDictionary

import pygame


_TERRAINS = WeakKeyDictionary()
_ACTIVE_TERRAIN = None
_LAYER_CACHE_BYTES = 32 * 1024 * 1024


class MapTerrain:
    def __init__(self):
        self.rows = None
        self.barriers = set()
        self.known = set()
        self.walkable = set()
        self.reveals = {}
        self.layers = {}
        self.inks = {}
        self.updated_at = -1

    def update(self, floor, current_time):
        if self.updated_at == current_time:
            return
        self.updated_at = current_time
        rows = tuple(floor.map)
        changed = self.rows != rows or self.barriers != floor.barriers
        explored_changed = self.known != floor.explored_cells
        if changed or explored_changed:
            added = floor.explored_cells - self.known
            if self.rows is not None:
                self.reveals.update((cell, current_time) for cell in added)
            removed = self.known - floor.explored_cells
            self.known = set(floor.explored_cells)
            if changed:
                self.walkable = {
                    (x, y) for x, y in self.known
                    if 0 <= y < len(rows) and 0 <= x < len(rows[y]) and rows[y][x] not in ("#", "S")
                }
            else:
                self.walkable.difference_update(removed)
                self.walkable.update(
                    (x, y) for x, y in added
                    if 0 <= y < len(rows) and 0 <= x < len(rows[y]) and rows[y][x] not in ("#", "S")
                )
            self.rows = rows
        if changed:
            self.barriers = set(floor.barriers)
            self.layers.clear()
            self.inks.clear()
        elif explored_changed:
            dirty = {
                (x + dx, y + dy)
                for x, y in added | removed
                for dx, dy in ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0))
                if 0 <= y + dy < len(rows) and 0 <= x + dx < len(rows[y + dy])
            }
            for cell_size, layer in self.layers.items():
                self._paint(layer, cell_size, dirty)
        for cell, started in tuple(self.reveals.items()):
            if cell not in self.known or not 0 <= current_time - started < 650:
                del self.reveals[cell]

    def surface(self, floor, cell_size, texture):
        if cell_size in self.layers:
            return self.layers[cell_size]
        width, height = len(floor.map[0]), len(floor.map)
        size = (width * cell_size, height * cell_size)
        required_bytes = size[0] * size[1] * 4
        while self.layers and (
            len(self.layers) >= 3
            or sum(image.get_pitch() * image.get_height() for image in self.layers.values()) + required_bytes > _LAYER_CACHE_BYTES
        ):
            removed = next(iter(self.layers))
            del self.layers[removed]
            self.inks.pop(removed, None)
        layer = pygame.Surface(size, pygame.SRCALPHA)
        tile_size = cell_size * 24
        if cell_size not in self.inks:
            ink = pygame.transform.smoothscale(texture, (tile_size, tile_size))
            ink.fill((175, 169, 154, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self.inks[cell_size] = ink
        self._paint(layer, cell_size, self.known)
        self.layers[cell_size] = layer
        return layer

    def _paint(self, layer, cell_size, cells):
        ink = self.inks[cell_size]
        for x, y in cells:
            layer.fill((0, 0, 0, 0), (x * cell_size, y * cell_size, cell_size, cell_size))
        for x, y in cells & self.walkable:
            rectangle = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
            layer.blit(ink, rectangle, ((x % 24 * cell_size, y % 24 * cell_size), rectangle.size))
        directions = (
            (0, -1, (0, 0), (1, 0)), (1, 0, (1, 0), (1, 1)),
            (0, 1, (0, 1), (1, 1)), (-1, 0, (0, 0), (0, 1)),
        )
        outline_cells = {
            (x + dx, y + dy) for x, y in cells
            for dx, dy in ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0))
        } & self.walkable
        for x, y in outline_cells:
            for dx, dy, first, second in directions:
                neighbor = (x + dx, y + dy)
                edge = tuple(sorted(((x, y), neighbor)))
                if neighbor in self.walkable and edge not in self.barriers:
                    continue
                start = ((x + first[0]) * cell_size, (y + first[1]) * cell_size)
                end = ((x + second[0]) * cell_size, (y + second[1]) * cell_size)
                pygame.draw.line(layer, (163, 155, 132, 215), start, end)
                if cell_size >= 6 and neighbor in self.known and neighbor not in self.walkable:
                    center = ((x + 0.5 + dx * 0.7) * cell_size, (y + 0.5 + dy * 0.7) * cell_size)
                    pygame.draw.line(layer, (97, 90, 77, 125), center, (center[0] + 2, center[1] - 2))


def get_terrain(floor, current_time):
    global _ACTIVE_TERRAIN

    terrain = _TERRAINS.get(floor)
    if terrain is None:
        terrain = MapTerrain()
        _TERRAINS[floor] = terrain
    if terrain is not _ACTIVE_TERRAIN:
        if _ACTIVE_TERRAIN is not None:
            _ACTIVE_TERRAIN.layers.clear()
            _ACTIVE_TERRAIN.inks.clear()
        _ACTIVE_TERRAIN = terrain
    terrain.update(floor, current_time)
    return terrain
