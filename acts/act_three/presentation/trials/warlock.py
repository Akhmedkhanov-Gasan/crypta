import math
from functools import lru_cache
from pathlib import Path

import pygame
import resource_store as resources

from presentation.layout import ACT_THREE_TILE_SIZE, ACT_THREE_VIEW_X, ACT_THREE_VIEW_Y, ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT
from acts.act_three.trials.warlock import PARTS, is_spirit
from acts.act_three.presentation.trials.archer import screen_position
from acts.act_three.presentation.trials.archer_effects import glow
from acts.act_three.presentation.trials.door import door_frames
from acts.act_three.presentation.tile_layers import draw_tile_layers, layer_names_by_prefix


@lru_cache(maxsize=1)
def sprites():
    root = Path(__file__).resolve().parents[4] / "assets/maps/act_3/trials/warlock_curse"
    return [pygame.transform.scale(resources.load_image(str(root / f"{name}.png")).convert_alpha(), (64, 64)) for name in PARTS]


def board_rect(trial):
    left, top, right, bottom = trial["bounds"]
    bottom += 1
    tile_size = min((ACT_THREE_VIEW_WIDTH - 48) / (right - left), (ACT_THREE_VIEW_HEIGHT - 118) / (bottom - top))
    width, height = round((right - left) * tile_size), round((bottom - top) * tile_size)
    return pygame.Rect(ACT_THREE_VIEW_X + (ACT_THREE_VIEW_WIDTH - width) // 2, ACT_THREE_VIEW_Y + 46, width, height)


def draw_ground(context):
    trial = context.floor.curse_trial
    if trial is None:
        return
    now = pygame.time.get_ticks()
    frame = min(7, (now - trial["started"]) // 80) if trial["phase"] == "opening" else (0 if trial["phase"] == "closed" else 7)
    context.view_surface.blit(door_frames()[frame], screen_position(context, trial["door"]))
    if trial["phase"] in ("closed", "opening"):
        return
    x, y = screen_position(context, trial["start"])
    size = ACT_THREE_TILE_SIZE
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    strength = .7 + .15 * math.sin(now / 700)
    color = (150, 104, 189, round(210 * strength))
    points = [(size * .18, size * .35), (size * .35, size * .27), (size * .5, size * .45), (size * .65, size * .27), (size * .82, size * .35), (size * .67, size * .62), (size * .5, size * .75), (size * .33, size * .62), (size * .18, size * .35)]
    pygame.draw.lines(image, color, False, points, 2)
    pygame.draw.lines(image, color, False, [(size * .5, size * .45), (size * .5, size * .65)], 2)
    context.view_surface.blit(image, (x, y))


def draw_spirit_view(screen, game_state, assets, now):
    floor = game_state.floor
    trial = floor.curse_trial
    if not is_spirit(trial):
        return
    size = ACT_THREE_TILE_SIZE
    left, top, right, bottom = trial["bounds"]
    bottom += 1
    board = pygame.Surface(((right - left) * size, (bottom - top) * size), pygame.SRCALPHA)
    board.fill((15, 13, 20))
    tile_assets = assets
    floor_tiles = assets.get("tmx_tiles_by_floor", {}).get(game_state.floor_index)
    if floor_tiles is not None:
        tile_assets = {**assets, "tmx_tiles": floor_tiles, "tmx_animations": assets.get("tmx_animations_by_floor", {}).get(game_state.floor_index, {})}
    draw_tile_layers(board, floor, tile_assets, layer_names_by_prefix(floor, "Ground", "GroundDetails", "WallsBack", "DecorBack", "WallsFront", "DecorFront"), left, top, right, bottom, left * size, top * size, now)
    ground = floor.tile_layers.get("Ground", [])
    for y in range(top, bottom):
        for x in range(left, right):
            if floor.map[y][x] == "." and y < len(ground) and x < len(ground[y]) and ground[y][x] & 0x0FFFFFFF:
                rect = pygame.Rect((x - left) * size + 2, (y - top) * size + 2, size - 4, size - 4)
                pygame.draw.rect(board, (104, 85, 125, 70), rect, 1, border_radius=3)
    for index, cell in enumerate(trial["parts"]):
        if trial["phase"] == "sliding" and index == trial["selected"]:
            t = max(0, min(1, (now - trial["started"]) / trial["duration"]))
            t = t * t * (3 - 2 * t)
            origin, target = trial["slide_origin"], trial["slide_target"]
            cell = origin[0] + (target[0] - origin[0]) * t, origin[1] + (target[1] - origin[1]) * t
        position = (round((cell[0] - left) * size), round((cell[1] - top) * size))
        if index == trial["selected"]:
            aura = glow(size // 2, (140, 73, 178))
            aura.set_alpha(180)
            board.blit(aura, position)
            corners = pygame.Rect(position[0] + 2, position[1] + 2, size - 4, size - 4)
            pygame.draw.rect(board, (183, 139, 209, 220), corners, 2, border_radius=5)
        board.blit(pygame.transform.scale(sprites()[index], (size, size)), position)
    if trial["phase"] == "completion":
        elapsed = now - trial["completed"]
        mask = trial["parts"][1]
        aura = glow(size * 2, (138, 62, 178))
        aura.set_alpha(round(210 * max(0, math.sin(min(1, elapsed / 3300) * math.pi))))
        board.blit(aura, (round((mask[0] - left - 1.5) * size), round((mask[1] - top - 1.5) * size)))
    viewport = pygame.Rect(ACT_THREE_VIEW_X, ACT_THREE_VIEW_Y, ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT)
    veil = pygame.Surface(viewport.size, pygame.SRCALPHA)
    veil.fill((6, 4, 11, 255))
    for index in range(14):
        x = round((index * 97 + now * .008) % viewport.width)
        y = round((index * 71) % viewport.height)
        pygame.draw.ellipse(veil, (24, 17, 33, 255), (x - 70, y - 15, 140, 30))
    rect = board_rect(trial)
    screen.blit(veil, viewport)
    screen.blit(pygame.transform.smoothscale(board, rect.size), rect)
    pygame.draw.rect(screen, (76, 54, 91), rect.inflate(4, 4), 1)
    font = pygame.font.SysFont("consolas", 14)
    for text, y in (("TAB / 1-3: select   WASD: slide   Drag: slide", rect.bottom + 9), ("T: reset   ESC: return to body", rect.bottom + 28)):
        label = font.render(text, True, (184, 160, 201))
        screen.blit(label, label.get_rect(midtop=(rect.centerx, y)))
    if trial["phase"] in ("entering", "leaving", "reset"):
        elapsed = now - trial["started"]
        duration = 700 if trial["phase"] == "entering" else 600
        alpha = round(255 * max(0, 1 - elapsed / duration)) if trial["phase"] != "leaving" else round(255 * min(1, elapsed / duration))
        veil.fill((7, 4, 11, alpha))
        screen.blit(veil, viewport)
