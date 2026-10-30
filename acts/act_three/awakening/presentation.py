import math

import pygame

from acts.act_three.awakening.assets import old_man_frames, old_man_sprite, scene_frames
from acts.act_three.presentation.dialogue_panel import draw_dialogue_panel
from acts.act_three.awakening.dialogue import (
    APPEAR_MS, ARRIVAL, BLACKOUT_MS, FAREWELL, TRANSFORM_MS,
    TURN_END_MS, TURN_START_MS, answer_timeline,
)
from presentation.layout import ACT_THREE_TILE_SIZE, ACT_TWO_VIEW_X, ACT_TWO_VIEW_Y
from settings import GAME_HEIGHT, GAME_WIDTH, TILE_SIZE


def _smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def awakening_player_sprite(game_state):
    scene = game_state.act_three.awakening
    if scene is None or not scene.world_swapped or scene.phase == "complete":
        return None
    parent = game_state.player.player_class
    if parent not in ("rogue", "warrior", "mage"):
        return None
    if scene.phase == "transformation":
        frames = scene_frames(parent, f"transform_{game_state.player.subclass}")
        sprite = frames[min(7, scene.elapsed * 8 // TRANSFORM_MS)]
    elif scene.phase == "answer":
        return None
    elif scene.phase == "arrival":
        frames = scene_frames(parent, "awakening_left")
        sprite = frames[min(7, max(0, scene.elapsed - 700) * 8 // 2300)]
    else:
        sprite = scene_frames(parent, "idle_left")[(scene.elapsed // 180) % 8]
    if scene.old_man_position[0] > game_state.floor.player_column:
        sprite = pygame.transform.flip(sprite, True, False)
    return sprite


def _screen_anchor(game_state, position, camera):
    if game_state.floor.presentation_act == 2:
        return (
            ACT_TWO_VIEW_X + ((position[0] + 0.5) * TILE_SIZE - camera.x) * camera.zoom,
            ACT_TWO_VIEW_Y + ((position[1] + 1) * TILE_SIZE - camera.y) * camera.zoom,
        ), camera.zoom
    from acts.act_three.presentation.camera import act_three_camera_position, act_three_camera_scale
    camera_x, camera_y = act_three_camera_position()
    scale = act_three_camera_scale(game_state.floor)
    return (
        ((position[0] + 0.5) * ACT_THREE_TILE_SIZE - camera_x) * scale,
        ((position[1] + 1) * ACT_THREE_TILE_SIZE - camera_y) * scale,
    ), scale


def _draw_old_man(screen, game_state, camera):
    scene = game_state.act_three.awakening
    act = game_state.floor.presentation_act
    anchor, scale = _screen_anchor(game_state, scene.old_man_position, camera)
    player_position = (game_state.floor.player_column, game_state.floor.player_row)
    if act == 2:
        source = old_man_sprite(2)
        alpha = _smooth(scene.elapsed / APPEAR_MS)
        turn = _smooth((scene.elapsed - TURN_START_MS) / (TURN_END_MS - TURN_START_MS))
        poses = (
            (source, alpha * (1 - turn), scene.boss_position[0] > scene.old_man_position[0]),
            (source, alpha * turn, player_position[0] > scene.old_man_position[0]),
        )
    else:
        frame = (scene.elapsed // 180) % 8
        idle = old_man_frames("idle_left")[frame]
        flip = player_position[0] > scene.old_man_position[0]
        poses = ((idle, 1.0, flip),)
        if scene.phase == "arrival" and scene.elapsed < 2800:
            stand = _smooth((scene.elapsed - 2000) / 800)
            poses = (
                (old_man_frames("kneeling_left")[frame], 1 - stand, flip),
                (idle, stand, flip),
            )
    if scene.phase == "answer":
        first_end = answer_timeline(game_state.player.subclass)[0][1]
        fade = _smooth((scene.elapsed - first_end - 350) / 1500)
        away = _smooth((scene.elapsed - first_end) / 550)
        poses = (
            (idle, (1 - fade) * (1 - away), flip),
            (old_man_frames("idle_down")[frame], (1 - fade) * away, False),
        )
    for source, opacity, flip in poses:
        if opacity <= 0:
            continue
        sprite = pygame.transform.scale(source, (max(1, round(source.get_width() * scale)), max(1, round(source.get_height() * scale))))
        if flip:
            sprite = pygame.transform.flip(sprite, True, False)
        sprite.set_alpha(round(255 * opacity))
        screen.blit(sprite, sprite.get_rect(midbottom=(round(anchor[0]), round(anchor[1]))))


def _draw_veil(screen, progress, center):
    progress = _smooth(progress)
    layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    layer.fill((1, 2, 6, round(255 * progress)))
    if 0 < progress < 1:
        for index in range(22):
            angle = index * math.tau / 22 + progress * 0.22
            radius = (1 - progress) * 1100
            tip = (round(center[0] + math.cos(angle) * radius), round(center[1] + math.sin(angle) * radius))
            left = (round(center[0] + math.cos(angle - 0.07) * 1700), round(center[1] + math.sin(angle - 0.07) * 1700))
            right = (round(center[0] + math.cos(angle + 0.07) * 1700), round(center[1] + math.sin(angle + 0.07) * 1700))
            pygame.draw.polygon(layer, (2, 3, 9, round(230 * progress)), (tip, left, right))
            pygame.draw.line(layer, (85, 74, 117, round(120 * math.sin(progress * math.pi))), tip, left, 1)
        pygame.draw.ellipse(layer, (145, 137, 170, round(100 * math.sin(progress * math.pi))), (center[0] - 600 * (1 - progress), center[1] - 5, 1200 * (1 - progress) + 1, 10), 2)
    screen.blit(layer, (0, 0))


def draw_awakening_scene(screen, game_state, fonts, act_two_fonts, camera):
    scene = game_state.act_three.awakening
    if scene is None or scene.phase in ("complete", "choice"):
        return
    if scene.phase != "blackout":
        _draw_old_man(screen, game_state, camera)
    if scene.phase == "transformation":
        anchor, _ = _screen_anchor(game_state, (game_state.floor.player_column, game_state.floor.player_row), camera)
        progress = scene.elapsed / TRANSFORM_MS
        glow = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        for index in range(30):
            angle = index * 2.399 + progress * 9
            radius = 20 + 110 * math.sin(progress * math.pi) * (index % 5 + 1) / 5
            point = (round(anchor[0] + math.cos(angle) * radius), round(anchor[1] - 38 + math.sin(angle) * radius * 0.6))
            pygame.draw.circle(glow, (174, 148, 213, round(200 * math.sin(progress * math.pi))), point, 2)
        screen.blit(glow, (0, 0))
    timeline = {"farewell": FAREWELL, "arrival": ARRIVAL}.get(scene.phase, ())
    if scene.phase == "answer":
        timeline = answer_timeline(game_state.player.subclass)
    for start, end, speaker, line in timeline:
        if start <= scene.elapsed < end:
            opacity = _smooth((scene.elapsed - start) / 220) * (1 - _smooth((scene.elapsed - end + 250) / 250))
            visible_characters = max(0, (scene.elapsed - start) // 34)
            if scene.world_swapped:
                speaker_id = "old_man" if speaker == "OLD MAN" else game_state.player.subclass
                draw_dialogue_panel(screen, fonts, speaker_id, speaker, line, visible_characters, opacity)
            else:
                from presentation.screens import _draw_awakening_text_panel

                _draw_awakening_text_panel(screen, act_two_fonts["title"], act_two_fonts["text"], speaker, line[:visible_characters], opacity)
            break
    if scene.phase == "blackout":
        anchor, _ = _screen_anchor(game_state, (game_state.floor.player_column, game_state.floor.player_row), camera)
        _draw_veil(screen, min(1, scene.elapsed / (BLACKOUT_MS - 650)), (anchor[0], anchor[1] - 20))
    elif scene.phase == "arrival" and scene.elapsed < 1800:
        _draw_veil(screen, 1 - scene.elapsed / 1800, (GAME_WIDTH // 2, GAME_HEIGHT // 2))
