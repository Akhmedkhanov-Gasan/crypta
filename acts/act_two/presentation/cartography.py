import pygame
from functools import lru_cache

from presentation.figma_ui import figma_rect


BACKGROUND = (12, 13, 17)
BORDER = (102, 88, 73)
TEXT = (196, 181, 157)
FLOOR = (91, 85, 76)
VISIBLE_FLOOR = (143, 130, 108)
WALL = (48, 46, 46)
PLAYER = (239, 214, 144)
STAIRS_UP = (104, 158, 224)
STAIRS_DOWN = (202, 82, 77)
BLOOD_ALTAR = (173, 48, 66)
RUNE_ALTAR = (168, 125, 207)
NPC = (139, 179, 117)


def minimap_rectangle(hud_layout, surface_size):
    minimap = hud_layout.get("cartography", {}).get("minimap")
    if minimap is not None:
        return figma_rect(minimap["frame"])
    rectangle = pygame.Rect(0, 75, 200, 150)
    rectangle.right = surface_size[0] - 8
    return rectangle


def full_map_rectangle(surface_size, hud_layout=None):
    full_map = (hud_layout or {}).get("cartography", {}).get("full_map")
    if full_map is not None:
        return figma_rect(full_map["frame"])
    return pygame.Rect(48, 40, surface_size[0] - 96, surface_size[1] - 80)


def full_map_close_rectangle(surface_size, hud_layout=None):
    panel = full_map_rectangle(surface_size, hud_layout)
    content = _map_content_rectangle(panel)
    return pygame.Rect(content.right - 26, content.top + 4, 22, 22)


def _map_content_rectangle(panel):
    horizontal_margin = max(10, round(panel.width * 0.06))
    vertical_margin = max(10, round(panel.height * 0.10))
    return panel.inflate(-horizontal_margin * 2, -vertical_margin * 2)


@lru_cache(maxsize=16)
def _scaled_asset(image, size):
    return pygame.transform.scale(image, size)


@lru_cache(maxsize=8)
def _floor_texture(image, size, visible):
    texture = _scaled_asset(image, size).copy()
    shade = (240, 226, 200) if visible else (155, 149, 140)
    texture.fill((*shade, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return texture


def _draw_backing(surface, panel, sprites):
    interior = panel.inflate(-max(8, round(panel.width * 0.06)), -max(8, round(panel.height * 0.10)))
    pygame.draw.rect(surface, BACKGROUND, interior)
    backing = sprites.get("act_two_map_backing")
    if backing is not None:
        surface.blit(_scaled_asset(backing, interior.size), interior)
    return interior


def _draw_frame(surface, panel, sprites, key):
    image = sprites.get(key)
    if image is not None:
        surface.blit(_scaled_asset(image, panel.size), panel)
    else:
        pygame.draw.rect(surface, BORDER, panel, 1)


def _draw_map(surface, floor, viewport, local, sprites, floor_index):
    columns = len(floor.map[0])
    rows = len(floor.map)
    if local:
        scale = 6
        origin_x = viewport.centerx - (floor.player_column + 0.5) * scale
        origin_y = viewport.centery - (floor.player_row + 0.5) * scale
    else:
        scale = max(1, min(viewport.width // columns, viewport.height // rows))
        origin_x = viewport.centerx - columns * scale / 2
        origin_y = viewport.centery - rows * scale / 2

    texture = sprites.get("act_two_map_floor_texture")
    textures = {
        visible: _floor_texture(texture, (columns * scale, rows * scale), visible)
        for visible in (False, True)
    } if texture is not None else {}

    def cell_rectangle(position):
        column, row = position
        return pygame.Rect(
            round(origin_x + column * scale),
            round(origin_y + row * scale),
            scale,
            scale,
        )

    previous_clip = surface.get_clip()
    surface.set_clip(viewport.clip(previous_clip))
    try:
        for column, row in floor.explored_cells:
            if not (0 <= column < columns and 0 <= row < rows):
                continue
            position = (column, row)
            rectangle = cell_rectangle(position)
            if not rectangle.colliderect(viewport):
                continue
            color = WALL if floor.map[row][column] in ("#", "S") else (
                VISIBLE_FLOOR if position in floor.visible_cells else FLOOR
            )
            if textures and floor.map[row][column] not in ("#", "S"):
                surface.blit(
                    textures[position in floor.visible_cells],
                    rectangle,
                    pygame.Rect(column * scale, row * scale, scale, scale),
                )
            else:
                pygame.draw.rect(surface, color, rectangle)

        for first, second in floor.barriers:
            if first not in floor.explored_cells or second not in floor.explored_cells:
                continue
            rectangle = cell_rectangle(first)
            if first[0] != second[0]:
                x = rectangle.right if second[0] > first[0] else rectangle.left
                start, end = (x, rectangle.top), (x, rectangle.bottom)
            else:
                y = rectangle.bottom if second[1] > first[1] else rectangle.top
                start, end = (rectangle.left, y), (rectangle.right, y)
            pygame.draw.line(surface, BACKGROUND, start, end, max(1, scale // 6))

        for trader in (floor.trader, floor.quest_trader):
            if trader is not None and (trader.column, trader.row) in floor.explored_cells:
                center = cell_rectangle((trader.column, trader.row)).center
                pygame.draw.circle(surface, NPC, center, max(2, scale // 3))

        altars = []
        if floor.bloody_altar is not None:
            altars.append(((floor.bloody_altar.column, floor.bloody_altar.row), BLOOD_ALTAR))
        if floor.rune_room is not None:
            altars.append((floor.rune_room.pedestal_position, RUNE_ALTAR))
        for position, color in altars:
            if position not in floor.explored_cells:
                continue
            x, y = cell_rectangle(position).center
            radius = max(2, scale // 3)
            pygame.draw.polygon(surface, color, (
                (x, y - radius), (x + radius, y),
                (x, y + radius), (x - radius, y),
            ))

        for passage in floor.passages:
            if not passage.discovered:
                continue
            rectangle = cell_rectangle(passage.trigger_position)
            goes_up = (
                passage.target_floor_index > floor_index
                if passage.target_floor_index is not None
                else passage.passage_id != "entrance"
            )
            color = STAIRS_UP if goes_up else STAIRS_DOWN
            pygame.draw.rect(surface, color, rectangle, max(1, scale // 5))

        center = cell_rectangle((floor.player_column, floor.player_row)).center
        radius = max(3, scale // 3)
        pygame.draw.circle(surface, BACKGROUND, center, radius + 1)
        pygame.draw.circle(surface, PLAYER, center, radius)
    finally:
        surface.set_clip(previous_clip)


def draw_minimap(surface, game_state, hud_layout, sprites):
    panel = minimap_rectangle(hud_layout, surface.get_size())
    _draw_backing(surface, panel, sprites)
    viewport = _map_content_rectangle(panel)
    _draw_map(surface, game_state.floor, viewport, local=True, sprites=sprites, floor_index=game_state.floor_index)
    _draw_frame(surface, panel, sprites, "act_two_minimap_frame")


def draw_full_map(surface, game_state, font, heading_font, hud_layout, sprites):
    veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    veil.fill((0, 0, 0, 210))
    surface.blit(veil, (0, 0))
    panel = full_map_rectangle(surface.get_size(), hud_layout)
    _draw_backing(surface, panel, sprites)
    content = _map_content_rectangle(panel)
    title = heading_font.render("EXPLORED MAP", True, TEXT)
    title_rectangle = title.get_rect(midtop=(content.centerx, content.top + 4))
    close = full_map_close_rectangle(surface.get_size(), hud_layout)
    legend = (
        ("You", PLAYER),
        ("Stairs up", STAIRS_UP),
        ("Stairs down", STAIRS_DOWN),
        ("Trader", NPC),
        ("Blood altar", BLOOD_ALTAR),
        ("Rune altar", RUNE_ALTAR),
    )
    labels = [(font.render(name, True, TEXT), color) for name, color in legend]
    legend_height = max(label.get_height() for label, _ in labels)
    legend_top = content.bottom - legend_height - 4
    viewport = pygame.Rect(
        content.left,
        title_rectangle.bottom + 14,
        content.width,
        max(1, legend_top - title_rectangle.bottom - 28),
    )
    _draw_map(surface, game_state.floor, viewport, local=False, sprites=sprites, floor_index=game_state.floor_index)
    _draw_frame(surface, panel, sprites, "act_two_full_map_frame")
    surface.blit(title, title_rectangle)
    pygame.draw.rect(surface, BORDER, close, 1)
    close_label = font.render("X", True, TEXT)
    surface.blit(close_label, close_label.get_rect(center=close.center))
    legend_width = sum(label.get_width() + 14 for label, _ in labels) + 24 * (len(labels) - 1)
    x = content.centerx - legend_width // 2
    for label, color in labels:
        marker = pygame.Rect(x, 0, 8, 8)
        marker.centery = legend_top + legend_height // 2
        if color in (BLOOD_ALTAR, RUNE_ALTAR):
            pygame.draw.polygon(surface, color, (
                marker.midtop, marker.midright, marker.midbottom, marker.midleft,
            ))
        else:
            pygame.draw.rect(surface, color, marker)
        surface.blit(label, (x + 14, legend_top))
        x += label.get_width() + 38
