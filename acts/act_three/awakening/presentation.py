import math

import pygame

from acts.act_three.awakening.assets import old_man_facing, old_man_frames, scene_frames
from acts.act_two.presentation.bosses.oracle_death import oracle_corpse_head_position
from game.dialogue import dialogue_visible_characters
from acts.act_three.presentation.dialogue_panel import draw_dialogue_panel
from acts.act_three.awakening.transition import draw_world_transition
from acts.act_three.awakening.dialogue import (
    APPEAR_MS, ARRIVAL, ARRIVAL_REVEAL_MS, FAREWELL, FAREWELL_END_MS, TRANSFORM_MS,
    TURN_END_MS, TURN_START_MS, answer_timeline,
)
from presentation.layout import ACT_THREE_TILE_SIZE, ACT_TWO_VIEW_X, ACT_TWO_VIEW_Y
from settings import TILE_SIZE


def _smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def awakening_player_sprite(game_state, assets):
    scene = game_state.act_three.awakening
    if scene is None or not scene.world_swapped or scene.phase == "complete":
        return None
    parent = game_state.player.player_class
    if parent not in ("rogue", "warrior", "mage"):
        return None
    if scene.phase == "transformation":
        frames = scene_frames(parent, f"transform_{game_state.player.subclass}")
        sprite = frames[min(7, scene.elapsed * 8 // TRANSFORM_MS)]
        if game_state.player.subclass == "summoner":
            return sprite
    elif scene.phase == "answer":
        subclass = game_state.player.subclass
        frame = (scene.elapsed // 180) % 8
        sprite = assets.get(f"player_{subclass}_idle_left_{frame}")
        if sprite is None:
            sprite = assets[f"player_{subclass}_idle_{frame}"]
    elif scene.phase == "arrival":
        direction = "awakening_right" if parent == "rogue" else "awakening_left"
        frames = scene_frames(parent, direction)
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
        elapsed = FAREWELL_END_MS if scene.phase == "blackout" else scene.elapsed
        head_position = oracle_corpse_head_position(scene.boss_position)
        boss_direction = (
            -1 if head_position[0] < scene.old_man_position[0] + 0.5 else 1,
            0,
        )
        player_direction = (
            -1 if player_position[0] < scene.old_man_position[0] else 1,
            0,
        )
        alpha = _smooth(elapsed / APPEAR_MS)
        turn = _smooth((elapsed - TURN_START_MS) / (TURN_END_MS - TURN_START_MS))
        poses = (
            (old_man_facing(boss_direction), alpha * (1 - turn), False),
            (old_man_facing(player_direction), alpha * turn, False),
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


def draw_awakening_scene(screen, game_state, fonts, act_two_fonts, camera):
    scene = game_state.act_three.awakening
    if scene is None or scene.phase in ("complete", "choice"):
        return
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
            opacity = _smooth((scene.elapsed - start) / 220)
            if speaker == "PLAYER":
                speaker = (game_state.player.subclass or game_state.player.player_class).upper()
            visible_characters = dialogue_visible_characters(game_state.dialogue, max(0, (scene.elapsed - start) // 34))
            if scene.world_swapped:
                speaker_id = "old_man" if speaker == "OLD MAN" else game_state.player.subclass
                draw_dialogue_panel(screen, fonts, speaker_id, speaker, line, visible_characters, opacity)
            else:
                from presentation.screens import _draw_awakening_text_panel

                _draw_awakening_text_panel(screen, act_two_fonts["title"], act_two_fonts["text"], speaker, line, opacity, visible_characters)
            break
    if scene.phase == "blackout" or (scene.phase == "arrival" and scene.elapsed < ARRIVAL_REVEAL_MS):
        anchor, scale = _screen_anchor(game_state, (game_state.floor.player_column, game_state.floor.player_row), camera)
        tile_size = TILE_SIZE if game_state.floor.presentation_act == 2 else ACT_THREE_TILE_SIZE
        center = (anchor[0], anchor[1] - tile_size * scale * 0.55)
        draw_world_transition(screen, scene.elapsed, center, revealing=scene.phase == "arrival")
