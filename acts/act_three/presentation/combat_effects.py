import math

import pygame

from game.events import GameEventType
from presentation.layout import ACT_THREE_TILE_SIZE


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

_ENEMY_HIT_REACTION_DURATION_MS = 190
_ENEMY_HIT_FEEDBACK_DURATION_MS = 680
_AFTERSHOCK_FEEDBACK_DELAY_MS = 330
_PLAYER_HIT_REACTION_DURATION_MS = 210
_PLAYER_HIT_SPRITE_DURATION_MS = 270
_PLAYER_HIT_FEEDBACK_DURATION_MS = 680
_PLAYER_HIT_VIGNETTE_DURATION_MS = 340
_PLAYER_HIT_CAMERA_SHAKE_DURATION_MS = 190
_FAMILIAR_HIT_REACTION_DURATION_MS = 190
_FAMILIAR_HIT_FEEDBACK_DURATION_MS = 680
_PLAYER_DEATH_HURT_HOLD_MS = 400
_PLAYER_DEATH_COLLAPSE_END_MS = 2300
_PLAYER_DEATH_FALL_END_MS = 4100
_PLAYER_DEATH_MESSAGE_START_MS = 5400
_PLAYER_DEATH_MESSAGE_FADE_MS = 650
_PLAYER_DEATH_IMPACT_SHAKE_MS = 380


def record_enemy_hit_feedback(game_state, started_at):
    hit_events_by_target = {}

    for event in game_state.events:
        if (
            event.type is not GameEventType.HIT
            or event.target in (None, "hero", "familiar")
            or (
                not event.amount
                and not event.data.get("blocked", False)
            )
        ):
            continue

        hit_events_by_target.setdefault(event.target, []).append(event)

    for enemy in game_state.floor.enemies:
        hit_events = hit_events_by_target.get(enemy.name)
        if not hit_events:
            continue

        regular_hit_events = [
            event
            for event in hit_events
            if event.data.get("kind") != "aftershock"
        ]
        aftershock_hit_events = [
            event
            for event in hit_events
            if event.data.get("kind") == "aftershock"
        ]
        if aftershock_hit_events:
            enemy.aftershock_hit_started_at = (
                started_at + _AFTERSHOCK_FEEDBACK_DELAY_MS
            )
            enemy.aftershock_hit_damage = sum(
                event.amount for event in aftershock_hit_events
            )
        if not regular_hit_events:
            continue

        enemy.hit_animation_started_at = started_at
        enemy.hit_damage = sum(
            event.amount for event in regular_hit_events
        )
        enemy.hit_critical = any(
            event.data.get("critical", False)
            for event in regular_hit_events
        )
        enemy.hit_origin = next(
            (
                event.origin
                for event in reversed(regular_hit_events)
                if event.origin is not None
            ),
            None,
        )
        enemy.hit_blocked = any(
            event.data.get("blocked", False)
            for event in regular_hit_events
        )
        enemy.hit_attacker_class = next(
            (
                event.data.get("player_class")
                for event in reversed(regular_hit_events)
                if event.data.get("player_class") is not None
            ),
            None,
        )


def record_enemy_death_feedback(game_state, started_at):
    defeated_enemy_events = {
        event.actor: event
        for event in game_state.events
        if event.type is GameEventType.DEATH
    }

    for enemy in game_state.floor.enemies:
        death_event = defeated_enemy_events.get(enemy.name)
        if (
            death_event is not None
            and enemy.death_animation_started_at < 0
        ):
            delay = (
                _AFTERSHOCK_FEEDBACK_DELAY_MS
                if death_event.data.get("cause") == "aftershock"
                else 0
            )
            enemy.death_animation_started_at = started_at + delay


def record_player_hit_feedback(game_state, started_at):
    hit_events = [
        event
        for event in game_state.events
        if (
            event.type is GameEventType.HIT
            and event.target == "hero"
            and event.amount
        )
    ]
    if not hit_events:
        return

    player = game_state.player
    player.hit_animation_started_at = started_at
    player.hit_damage = sum(event.amount for event in hit_events)
    player.hit_origin = next(
        (
            event.origin
            for event in reversed(hit_events)
            if event.origin is not None
        ),
        None,
    )


def record_player_death_feedback(game_state, started_at):
    player = game_state.player
    if (
        player.health > 0
        or player.death_animation_started_at >= 0
    ):
        return

    player.death_animation_started_at = started_at
    if player.subclass == "summoner":
        player.summoner_familiar_active = False
        player.summoner_familiar_position = None
        player.summoner_true_form_active = False
    death_identity = player.subclass or player.player_class
    if death_identity not in (
        "berserker",
        "paladin",
        "assassin",
        "archer",
        "warlock",
        "summoner",
        "warrior",
        "rogue",
        "mage",
    ):
        return

    floor = game_state.floor
    player_position = (floor.player_column, floor.player_row)
    candidate_offsets = ((1, 0), (-1, 0), (0, 1), (0, -1))
    old_man_position = None
    for offset_x, offset_y in candidate_offsets:
        column = player_position[0] + offset_x
        row = player_position[1] + offset_y
        if not (
            0 <= row < len(floor.map)
            and 0 <= column < len(floor.map[0])
        ):
            continue
        if floor.map[row][column] in ("#", "C"):
            continue
        old_man_position = (column, row)
        break

    player.old_man_position = old_man_position
    if old_man_position is None:
        return

    old_man_column, old_man_row = old_man_position
    floor.enemies[:] = [
        enemy
        for enemy in floor.enemies
        if not (
            enemy.column
            <= old_man_column
            < enemy.column + enemy.footprint_width
            and enemy.row
            <= old_man_row
            < enemy.row + enemy.footprint_height
        )
    ]


def _player_death_elapsed(player, current_time):
    if player.death_animation_started_at < 0:
        return None
    return max(0, current_time - player.death_animation_started_at)


def _player_death_frame(player, current_time):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None or elapsed < _PLAYER_DEATH_HURT_HOLD_MS:
        return None
    if elapsed < _PLAYER_DEATH_COLLAPSE_END_MS:
        return 0
    return 1


def _player_death_sprite_offset(player, current_time):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None or elapsed < _PLAYER_DEATH_HURT_HOLD_MS:
        return (0, 0)

    if elapsed < _PLAYER_DEATH_COLLAPSE_END_MS:
        progress = (
            (elapsed - _PLAYER_DEATH_HURT_HOLD_MS)
            / (
                _PLAYER_DEATH_COLLAPSE_END_MS
                - _PLAYER_DEATH_HURT_HOLD_MS
            )
        )
        progress = progress * progress * (3 - 2 * progress)
        return (
            round(-2 * (1 - progress) + 2 * progress),
            round(-9 * (1 - progress) + 5 * progress),
        )

    fall_progress = min(
        1,
        (elapsed - _PLAYER_DEATH_COLLAPSE_END_MS)
        / (
            _PLAYER_DEATH_FALL_END_MS
            - _PLAYER_DEATH_COLLAPSE_END_MS
        ),
    )
    fall_progress = 1 - (1 - fall_progress) ** 3
    return (
        round(-5 * (1 - fall_progress)),
        round(-11 * (1 - fall_progress) + 4 * fall_progress),
    )


def _player_death_camera_offset(player, current_time):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return (0, 0)

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if not 0 <= impact_elapsed < _PLAYER_DEATH_IMPACT_SHAKE_MS:
        return (0, 0)

    progress = impact_elapsed / _PLAYER_DEATH_IMPACT_SHAKE_MS
    decay = (1 - progress) ** 2
    return (
        round(math.sin(impact_elapsed * 0.31) * 4 * decay),
        round(math.cos(impact_elapsed * 0.43) * 3 * decay),
    )


def _draw_berserker_death_echoes(
    surface,
    assets,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    if 150 <= elapsed < 1650:
        visibility = 1 - (elapsed - 150) / 1500
        hurt_sprite = assets["player_berserker_hurt"]
        for echo_index, (offset_x, offset_y, base_alpha) in enumerate(
            ((-2, -2, 78), (-4, -5, 48), (-6, -8, 26))
        ):
            echo = hurt_sprite.copy()
            echo.fill(
                (92, 8 + echo_index * 3, 5, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            echo.set_alpha(round(base_alpha * visibility))
            surface.blit(
                echo,
                (position[0] + offset_x, position[1] + offset_y),
            )

    spirit_end = _PLAYER_DEATH_MESSAGE_START_MS - 350
    if _PLAYER_DEATH_COLLAPSE_END_MS <= elapsed < spirit_end:
        spirit_progress = (
            (elapsed - _PLAYER_DEATH_COLLAPSE_END_MS)
            / (spirit_end - _PLAYER_DEATH_COLLAPSE_END_MS)
        )
        spirit = assets["player_berserker_hurt"].copy()
        spirit.fill(
            (105, 12, 8, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        spirit.set_alpha(
            round(105 * (1 - spirit_progress) ** 1.5)
        )
        surface.blit(
            spirit,
            (
                position[0] - round(spirit_progress * 3),
                position[1] - 4 - round(spirit_progress * 15),
            ),
        )


def _draw_berserker_death_impact(
    surface,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    ember_start = _PLAYER_DEATH_HURT_HOLD_MS
    ember_end = _PLAYER_DEATH_MESSAGE_START_MS
    if ember_start <= elapsed < ember_end:
        ember_progress = (
            (elapsed - ember_start) / (ember_end - ember_start)
        )
        ember_surface = pygame.Surface(
            (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
            pygame.SRCALPHA,
        )
        for ember_index in range(9):
            phase = (ember_progress + ember_index * 0.137) % 1
            visibility = math.sin(math.pi * phase)
            ember_x = round(
                ACT_THREE_TILE_SIZE // 2
                + math.sin(ember_index * 2.17) * (8 + phase * 15)
            )
            ember_y = round(
                ACT_THREE_TILE_SIZE - 10 - phase * (22 + ember_index % 4 * 3)
            )
            pygame.draw.rect(
                ember_surface,
                (
                    186 + ember_index % 3 * 18,
                    34 + ember_index % 2 * 16,
                    20,
                    round(190 * visibility * (1 - ember_progress * 0.6)),
                ),
                (ember_x, ember_y, 2 if ember_index % 3 == 0 else 1, 2),
            )
        surface.blit(ember_surface, position)

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if not 0 <= impact_elapsed < 460:
        return

    impact_progress = impact_elapsed / 460
    visibility = (1 - impact_progress) ** 2
    impact_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    center = (ACT_THREE_TILE_SIZE // 2, ACT_THREE_TILE_SIZE - 7)
    pygame.draw.ellipse(
        impact_surface,
        (128, 112, 101, round(150 * visibility)),
        (
            center[0] - round(10 + impact_progress * 22),
            center[1] - round(3 + impact_progress * 3),
            round(20 + impact_progress * 44),
            round(6 + impact_progress * 6),
        ),
        width=2,
    )
    for dust_index in range(8):
        angle = math.pi + dust_index * math.pi / 7
        distance = 7 + impact_progress * (14 + dust_index % 3 * 4)
        dust_position = (
            round(center[0] + math.cos(angle) * distance),
            round(center[1] + math.sin(angle) * distance * 0.45),
        )
        pygame.draw.circle(
            impact_surface,
            (150, 132, 116, round(180 * visibility)),
            dust_position,
            2 if dust_index % 3 == 0 else 1,
        )
    surface.blit(impact_surface, position)


def _draw_berserker_death_foreground(
    surface,
    assets,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    spirit_start = _PLAYER_DEATH_COLLAPSE_END_MS
    spirit_end = _PLAYER_DEATH_MESSAGE_START_MS - 250
    if spirit_start <= elapsed < spirit_end:
        spirit_progress = (
            (elapsed - spirit_start) / (spirit_end - spirit_start)
        )
        spirit = assets["player_berserker_hurt"].copy()
        spirit.fill(
            (130, 10, 7, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        spirit.set_alpha(
            round(138 * math.sin(math.pi * spirit_progress))
        )
        surface.blit(
            spirit,
            (
                position[0] - round(spirit_progress * 4),
                position[1] - 8 - round(spirit_progress * 24),
            ),
        )

    ember_start = _PLAYER_DEATH_HURT_HOLD_MS
    ember_end = _PLAYER_DEATH_MESSAGE_START_MS
    if ember_start <= elapsed < ember_end:
        cycle = (elapsed - ember_start) / 1450
        effect_surface = pygame.Surface(
            (ACT_THREE_TILE_SIZE * 2, ACT_THREE_TILE_SIZE * 2),
            pygame.SRCALPHA,
        )
        effect_center_x = ACT_THREE_TILE_SIZE
        effect_base_y = ACT_THREE_TILE_SIZE + 22
        fade_out = min(
            1,
            max(0, (elapsed - _PLAYER_DEATH_FALL_END_MS) / 1300),
        )
        for ember_index in range(14):
            phase = (cycle + ember_index * 0.163) % 1
            visibility = math.sin(math.pi * phase) * (1 - fade_out * 0.75)
            drift = math.sin(ember_index * 2.31 + phase * 4.2)
            ember_x = round(
                effect_center_x
                + drift * (9 + phase * 23)
            )
            ember_y = round(
                effect_base_y
                - phase * (30 + ember_index % 5 * 5)
            )
            ember_color = (
                226,
                42 + ember_index % 3 * 17,
                25,
                round(220 * visibility),
            )
            pygame.draw.circle(
                effect_surface,
                ember_color,
                (ember_x, ember_y),
                2 if ember_index % 4 == 0 else 1,
            )
            if ember_index % 3 == 0:
                pygame.draw.line(
                    effect_surface,
                    (176, 22, 18, round(125 * visibility)),
                    (ember_x, ember_y + 2),
                    (ember_x - round(drift * 3), ember_y + 7),
                    1,
                )
        surface.blit(
            effect_surface,
            (
                position[0] - ACT_THREE_TILE_SIZE // 2,
                position[1] - ACT_THREE_TILE_SIZE // 2,
            ),
        )

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if not 0 <= impact_elapsed < 900:
        return

    impact_progress = impact_elapsed / 900
    visibility = (1 - impact_progress) ** 2
    wave_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE * 3, ACT_THREE_TILE_SIZE * 2),
        pygame.SRCALPHA,
    )
    wave_center = (
        wave_surface.get_width() // 2,
        ACT_THREE_TILE_SIZE + 16,
    )
    for wave_index, delay in enumerate((0.0, 0.16, 0.32)):
        wave_progress = max(0, min(1, (impact_progress - delay) / 0.68))
        if wave_progress <= 0:
            continue
        radius_x = round(14 + wave_progress * (50 + wave_index * 10))
        radius_y = round(4 + wave_progress * 12)
        pygame.draw.ellipse(
            wave_surface,
            (
                196 - wave_index * 24,
                38 - wave_index * 7,
                31,
                round(180 * visibility * (1 - wave_progress)),
            ),
            (
                wave_center[0] - radius_x,
                wave_center[1] - radius_y,
                radius_x * 2,
                radius_y * 2,
            ),
            width=2,
        )
    surface.blit(
        wave_surface,
        (
            position[0] - ACT_THREE_TILE_SIZE,
            position[1] - ACT_THREE_TILE_SIZE // 2,
        ),
    )


def _draw_paladin_death_echoes(
    surface,
    assets,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    if 180 <= elapsed < _PLAYER_DEATH_COLLAPSE_END_MS:
        fade = 1 - (
            (elapsed - 180)
            / (_PLAYER_DEATH_COLLAPSE_END_MS - 180)
        )
        hurt_sprite = assets["player_paladin_hurt"]
        for offset_y, alpha in ((-2, 58), (-5, 30)):
            echo = hurt_sprite.copy()
            echo.fill(
                (92, 71, 18, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            echo.set_alpha(round(alpha * fade))
            surface.blit(
                echo,
                (position[0], position[1] + offset_y),
            )

    spirit_end = _PLAYER_DEATH_MESSAGE_START_MS - 300
    if _PLAYER_DEATH_COLLAPSE_END_MS <= elapsed < spirit_end:
        progress = (
            (elapsed - _PLAYER_DEATH_COLLAPSE_END_MS)
            / (spirit_end - _PLAYER_DEATH_COLLAPSE_END_MS)
        )
        spirit = assets["player_paladin_hurt"].copy()
        spirit.fill(
            (116, 96, 38, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        spirit.set_alpha(round(78 * (1 - progress) ** 1.7))
        surface.blit(
            spirit,
            (
                position[0] + round(math.sin(progress * math.pi) * 2),
                position[1] - 5 - round(progress * 18),
            ),
        )


def _draw_paladin_death_impact(
    surface,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    mote_start = _PLAYER_DEATH_HURT_HOLD_MS
    mote_end = _PLAYER_DEATH_MESSAGE_START_MS
    if mote_start <= elapsed < mote_end:
        progress = (elapsed - mote_start) / (mote_end - mote_start)
        mote_surface = pygame.Surface(
            (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
            pygame.SRCALPHA,
        )
        for mote_index in range(10):
            phase = (progress * 0.82 + mote_index * 0.173) % 1
            visibility = math.sin(math.pi * phase)
            mote_x = round(
                ACT_THREE_TILE_SIZE // 2
                + math.sin(mote_index * 2.41 + phase) * (9 + phase * 11)
            )
            mote_y = round(
                ACT_THREE_TILE_SIZE - 9
                - phase * (26 + mote_index % 3 * 5)
            )
            color = (
                238,
                212 + mote_index % 2 * 18,
                128 + mote_index % 3 * 25,
                round(170 * visibility * (1 - progress * 0.55)),
            )
            pygame.draw.circle(
                mote_surface,
                color,
                (mote_x, mote_y),
                2 if mote_index % 4 == 0 else 1,
            )
        surface.blit(mote_surface, position)

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if not 0 <= impact_elapsed < 720:
        return

    progress = impact_elapsed / 720
    visibility = (1 - progress) ** 2
    ring_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    radius_x = round(8 + progress * 27)
    radius_y = round(3 + progress * 7)
    center = (ACT_THREE_TILE_SIZE // 2, ACT_THREE_TILE_SIZE - 7)
    pygame.draw.ellipse(
        ring_surface,
        (226, 199, 109, round(175 * visibility)),
        (
            center[0] - radius_x,
            center[1] - radius_y,
            radius_x * 2,
            radius_y * 2,
        ),
        width=2,
    )
    surface.blit(ring_surface, position)


def _draw_paladin_death_foreground(
    surface,
    assets,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    mote_start = _PLAYER_DEATH_HURT_HOLD_MS
    mote_end = _PLAYER_DEATH_MESSAGE_START_MS
    if mote_start <= elapsed < mote_end:
        cycle = (elapsed - mote_start) / 1900
        fade = min(
            1,
            max(0, (elapsed - _PLAYER_DEATH_FALL_END_MS) / 1250),
        )
        effect_surface = pygame.Surface(
            (ACT_THREE_TILE_SIZE * 2, ACT_THREE_TILE_SIZE * 2),
            pygame.SRCALPHA,
        )
        center_x = ACT_THREE_TILE_SIZE
        base_y = ACT_THREE_TILE_SIZE + 19
        for mote_index in range(16):
            phase = (cycle + mote_index * 0.149) % 1
            visibility = math.sin(math.pi * phase) * (1 - fade * 0.8)
            drift = math.sin(mote_index * 1.91 + phase * 3.1)
            mote_x = round(center_x + drift * (8 + phase * 20))
            mote_y = round(
                base_y - phase * (34 + mote_index % 4 * 7)
            )
            pygame.draw.circle(
                effect_surface,
                (
                    245,
                    221,
                    142 + mote_index % 3 * 24,
                    round(205 * visibility),
                ),
                (mote_x, mote_y),
                2 if mote_index % 5 == 0 else 1,
            )
        surface.blit(
            effect_surface,
            (
                position[0] - ACT_THREE_TILE_SIZE // 2,
                position[1] - ACT_THREE_TILE_SIZE // 2,
            ),
        )

    spirit_start = _PLAYER_DEATH_COLLAPSE_END_MS
    spirit_end = _PLAYER_DEATH_MESSAGE_START_MS - 250
    if spirit_start <= elapsed < spirit_end:
        progress = (
            (elapsed - spirit_start) / (spirit_end - spirit_start)
        )
        spirit = assets["player_paladin_hurt"].copy()
        spirit.fill(
            (158, 130, 48, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        spirit.set_alpha(
            round(105 * math.sin(math.pi * progress))
        )
        surface.blit(
            spirit,
            (
                position[0] + round(math.sin(progress * 4) * 2),
                position[1] - 8 - round(progress * 25),
            ),
        )

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if not 0 <= impact_elapsed < 1000:
        return

    progress = impact_elapsed / 1000
    visibility = (1 - progress) ** 2
    halo_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE * 3, ACT_THREE_TILE_SIZE * 2),
        pygame.SRCALPHA,
    )
    center = (
        halo_surface.get_width() // 2,
        ACT_THREE_TILE_SIZE + 16,
    )
    for halo_index, delay in enumerate((0.0, 0.24)):
        halo_progress = max(
            0,
            min(1, (progress - delay) / (1 - delay)),
        )
        if halo_progress <= 0:
            continue
        radius_x = round(12 + halo_progress * (45 + halo_index * 12))
        radius_y = round(4 + halo_progress * 10)
        pygame.draw.ellipse(
            halo_surface,
            (
                235,
                207,
                112,
                round(145 * visibility * (1 - halo_progress)),
            ),
            (
                center[0] - radius_x,
                center[1] - radius_y,
                radius_x * 2,
                radius_y * 2,
            ),
            width=2,
        )
    surface.blit(
        halo_surface,
        (
            position[0] - ACT_THREE_TILE_SIZE,
            position[1] - ACT_THREE_TILE_SIZE // 2,
        ),
    )


def _draw_assassin_death_echoes(
    surface,
    assets,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    if 120 <= elapsed < _PLAYER_DEATH_COLLAPSE_END_MS:
        fade = 1 - (
            (elapsed - 120)
            / (_PLAYER_DEATH_COLLAPSE_END_MS - 120)
        )
        hurt_sprite = assets["player_assassin_hurt"]
        for echo_index, (offset_x, alpha) in enumerate(
            ((-3, 62), (3, 42), (-6, 24))
        ):
            echo = hurt_sprite.copy()
            echo.fill(
                (10, 28 + echo_index * 7, 74, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            echo.set_alpha(round(alpha * fade))
            surface.blit(
                echo,
                (
                    position[0] + offset_x,
                    position[1] - 2 - echo_index * 2,
                ),
            )

    spirit_end = _PLAYER_DEATH_MESSAGE_START_MS - 260
    if _PLAYER_DEATH_COLLAPSE_END_MS <= elapsed < spirit_end:
        progress = (
            (elapsed - _PLAYER_DEATH_COLLAPSE_END_MS)
            / (spirit_end - _PLAYER_DEATH_COLLAPSE_END_MS)
        )
        shadow = assets["player_assassin_hurt"].copy()
        shadow.fill(
            (8, 25, 68, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        shadow.set_alpha(round(72 * (1 - progress) ** 1.6))
        surface.blit(
            shadow,
            (
                position[0] + round(math.sin(progress * 5) * 5),
                position[1] - 3 - round(progress * 14),
            ),
        )


def _draw_assassin_death_impact(
    surface,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    particle_start = _PLAYER_DEATH_HURT_HOLD_MS
    particle_end = _PLAYER_DEATH_MESSAGE_START_MS
    if particle_start <= elapsed < particle_end:
        progress = (
            (elapsed - particle_start)
            / (particle_end - particle_start)
        )
        particle_surface = pygame.Surface(
            (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
            pygame.SRCALPHA,
        )
        for particle_index in range(9):
            phase = (progress * 0.9 + particle_index * 0.181) % 1
            visibility = math.sin(math.pi * phase)
            particle_x = round(
                ACT_THREE_TILE_SIZE // 2
                + math.sin(particle_index * 2.57 + phase * 2) * (
                    7 + phase * 17
                )
            )
            particle_y = round(
                ACT_THREE_TILE_SIZE - 8
                - phase * (20 + particle_index % 4 * 5)
            )
            pygame.draw.rect(
                particle_surface,
                (
                    66 + particle_index % 2 * 26,
                    112 + particle_index % 3 * 17,
                    205,
                    round(150 * visibility * (1 - progress * 0.6)),
                ),
                (particle_x, particle_y, 1, 2),
            )
        surface.blit(particle_surface, position)

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if not 0 <= impact_elapsed < 620:
        return

    progress = impact_elapsed / 620
    visibility = (1 - progress) ** 2
    ripple_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    center = (ACT_THREE_TILE_SIZE // 2, ACT_THREE_TILE_SIZE - 7)
    radius_x = round(7 + progress * 30)
    radius_y = round(2 + progress * 6)
    pygame.draw.ellipse(
        ripple_surface,
        (66, 105, 183, round(135 * visibility)),
        (
            center[0] - radius_x,
            center[1] - radius_y,
            radius_x * 2,
            radius_y * 2,
        ),
        width=1,
    )
    surface.blit(ripple_surface, position)


def _draw_assassin_death_foreground(
    surface,
    assets,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    particle_start = _PLAYER_DEATH_HURT_HOLD_MS
    particle_end = _PLAYER_DEATH_MESSAGE_START_MS
    if particle_start <= elapsed < particle_end:
        cycle = (elapsed - particle_start) / 1650
        fade = min(
            1,
            max(0, (elapsed - _PLAYER_DEATH_FALL_END_MS) / 1200),
        )
        effect_surface = pygame.Surface(
            (ACT_THREE_TILE_SIZE * 2, ACT_THREE_TILE_SIZE * 2),
            pygame.SRCALPHA,
        )
        center_x = ACT_THREE_TILE_SIZE
        base_y = ACT_THREE_TILE_SIZE + 19
        for particle_index in range(15):
            phase = (cycle + particle_index * 0.157) % 1
            visibility = math.sin(math.pi * phase) * (1 - fade * 0.8)
            drift = math.sin(particle_index * 2.13 + phase * 4.6)
            particle_x = round(
                center_x + drift * (8 + phase * 22)
            )
            particle_y = round(
                base_y - phase * (28 + particle_index % 5 * 6)
            )
            color = (
                55 + particle_index % 3 * 18,
                94 + particle_index % 2 * 25,
                190 + particle_index % 3 * 18,
                round(185 * visibility),
            )
            pygame.draw.line(
                effect_surface,
                color,
                (particle_x, particle_y),
                (
                    particle_x - round(drift * 3),
                    particle_y + 3,
                ),
                1,
            )
        surface.blit(
            effect_surface,
            (
                position[0] - ACT_THREE_TILE_SIZE // 2,
                position[1] - ACT_THREE_TILE_SIZE // 2,
            ),
        )

    spirit_start = _PLAYER_DEATH_COLLAPSE_END_MS
    spirit_end = _PLAYER_DEATH_MESSAGE_START_MS - 220
    if spirit_start <= elapsed < spirit_end:
        progress = (
            (elapsed - spirit_start) / (spirit_end - spirit_start)
        )
        spirit = assets["player_assassin_hurt"].copy()
        spirit.fill(
            (14, 38, 98, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        spirit.set_alpha(
            round(88 * math.sin(math.pi * progress))
        )
        surface.blit(
            spirit,
            (
                position[0] + round(math.sin(progress * 8) * 6),
                position[1] - 7 - round(progress * 21),
            ),
        )

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if not 0 <= impact_elapsed < 820:
        return

    progress = impact_elapsed / 820
    visibility = (1 - progress) ** 2
    ripple_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE * 3, ACT_THREE_TILE_SIZE * 2),
        pygame.SRCALPHA,
    )
    center = (
        ripple_surface.get_width() // 2,
        ACT_THREE_TILE_SIZE + 16,
    )
    for ripple_index, delay in enumerate((0.0, 0.28)):
        ripple_progress = max(
            0,
            min(1, (progress - delay) / (1 - delay)),
        )
        if ripple_progress <= 0:
            continue
        radius_x = round(10 + ripple_progress * (42 + ripple_index * 10))
        radius_y = round(3 + ripple_progress * 8)
        pygame.draw.ellipse(
            ripple_surface,
            (
                48,
                79,
                151 + ripple_index * 20,
                round(120 * visibility * (1 - ripple_progress)),
            ),
            (
                center[0] - radius_x,
                center[1] - radius_y,
                radius_x * 2,
                radius_y * 2,
            ),
            width=1,
        )
    surface.blit(
        ripple_surface,
        (
            position[0] - ACT_THREE_TILE_SIZE,
            position[1] - ACT_THREE_TILE_SIZE // 2,
        ),
    )


def _draw_archer_death_echoes(
    surface,
    assets,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    if 160 <= elapsed < _PLAYER_DEATH_COLLAPSE_END_MS:
        fade = 1 - (
            (elapsed - 160)
            / (_PLAYER_DEATH_COLLAPSE_END_MS - 160)
        )
        hurt_sprite = assets["player_archer_hurt"]
        for echo_index, (offset_x, offset_y, alpha) in enumerate(
            ((-4, -1, 54), (-7, -3, 33), (-10, -5, 18))
        ):
            echo = hurt_sprite.copy()
            echo.fill(
                (42 + echo_index * 8, 61, 18, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            echo.set_alpha(round(alpha * fade))
            surface.blit(
                echo,
                (position[0] + offset_x, position[1] + offset_y),
            )

    spirit_end = _PLAYER_DEATH_MESSAGE_START_MS - 250
    if _PLAYER_DEATH_COLLAPSE_END_MS <= elapsed < spirit_end:
        progress = (
            (elapsed - _PLAYER_DEATH_COLLAPSE_END_MS)
            / (spirit_end - _PLAYER_DEATH_COLLAPSE_END_MS)
        )
        spirit = assets["player_archer_hurt"].copy()
        spirit.fill(
            (70, 86, 28, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        spirit.set_alpha(round(68 * (1 - progress) ** 1.5))
        surface.blit(
            spirit,
            (
                position[0] + round(progress * 8),
                position[1] - 4 - round(progress * 13),
            ),
        )


def _draw_archer_death_impact(
    surface,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    particle_start = _PLAYER_DEATH_HURT_HOLD_MS
    particle_end = _PLAYER_DEATH_MESSAGE_START_MS
    if particle_start <= elapsed < particle_end:
        progress = (
            (elapsed - particle_start)
            / (particle_end - particle_start)
        )
        particle_surface = pygame.Surface(
            (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
            pygame.SRCALPHA,
        )
        for particle_index in range(10):
            phase = (progress * 0.85 + particle_index * 0.171) % 1
            visibility = math.sin(math.pi * phase)
            direction = -1 if particle_index % 2 else 1
            particle_x = round(
                ACT_THREE_TILE_SIZE // 2
                + direction * phase * (16 + particle_index % 3 * 4)
                + math.sin(particle_index * 2.1) * 5
            )
            particle_y = round(
                ACT_THREE_TILE_SIZE - 10
                - phase * (18 + particle_index % 4 * 5)
            )
            color = (
                137 + particle_index % 3 * 18,
                151 + particle_index % 2 * 17,
                73,
                round(155 * visibility * (1 - progress * 0.55)),
            )
            pygame.draw.line(
                particle_surface,
                color,
                (particle_x - direction * 2, particle_y + 1),
                (particle_x + direction * 2, particle_y - 1),
                1,
            )
        surface.blit(particle_surface, position)

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if not 0 <= impact_elapsed < 650:
        return
    progress = impact_elapsed / 650
    visibility = (1 - progress) ** 2
    ripple_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    center = (ACT_THREE_TILE_SIZE // 2, ACT_THREE_TILE_SIZE - 7)
    radius_x = round(8 + progress * 29)
    radius_y = round(2 + progress * 6)
    pygame.draw.ellipse(
        ripple_surface,
        (129, 146, 77, round(130 * visibility)),
        (
            center[0] - radius_x,
            center[1] - radius_y,
            radius_x * 2,
            radius_y * 2,
        ),
        width=1,
    )
    surface.blit(ripple_surface, position)


def _draw_archer_death_foreground(
    surface,
    assets,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    particle_start = _PLAYER_DEATH_HURT_HOLD_MS
    particle_end = _PLAYER_DEATH_MESSAGE_START_MS
    if particle_start <= elapsed < particle_end:
        cycle = (elapsed - particle_start) / 1750
        fade = min(
            1,
            max(0, (elapsed - _PLAYER_DEATH_FALL_END_MS) / 1200),
        )
        effect_surface = pygame.Surface(
            (ACT_THREE_TILE_SIZE * 2, ACT_THREE_TILE_SIZE * 2),
            pygame.SRCALPHA,
        )
        center_x = ACT_THREE_TILE_SIZE
        base_y = ACT_THREE_TILE_SIZE + 18
        for particle_index in range(14):
            phase = (cycle + particle_index * 0.163) % 1
            visibility = math.sin(math.pi * phase) * (1 - fade * 0.8)
            direction = -1 if particle_index % 2 else 1
            particle_x = round(
                center_x
                + direction * phase * (18 + particle_index % 5 * 4)
                + math.sin(particle_index * 1.8) * 7
            )
            particle_y = round(
                base_y - phase * (26 + particle_index % 4 * 7)
            )
            color = (
                144 + particle_index % 3 * 17,
                158 + particle_index % 2 * 15,
                82,
                round(180 * visibility),
            )
            pygame.draw.line(
                effect_surface,
                color,
                (particle_x - direction * 3, particle_y + 1),
                (particle_x + direction * 3, particle_y - 1),
                1,
            )
        surface.blit(
            effect_surface,
            (
                position[0] - ACT_THREE_TILE_SIZE // 2,
                position[1] - ACT_THREE_TILE_SIZE // 2,
            ),
        )

    spirit_start = _PLAYER_DEATH_COLLAPSE_END_MS
    spirit_end = _PLAYER_DEATH_MESSAGE_START_MS - 220
    if spirit_start <= elapsed < spirit_end:
        progress = (
            (elapsed - spirit_start) / (spirit_end - spirit_start)
        )
        spirit = assets["player_archer_hurt"].copy()
        spirit.fill(
            (80, 93, 31, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        spirit.set_alpha(
            round(82 * math.sin(math.pi * progress))
        )
        surface.blit(
            spirit,
            (
                position[0] + round(progress * 12),
                position[1] - 7 - round(progress * 18),
            ),
        )

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if not 0 <= impact_elapsed < 860:
        return
    progress = impact_elapsed / 860
    visibility = (1 - progress) ** 2
    ripple_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE * 3, ACT_THREE_TILE_SIZE * 2),
        pygame.SRCALPHA,
    )
    center = (
        ripple_surface.get_width() // 2,
        ACT_THREE_TILE_SIZE + 16,
    )
    for ripple_index, delay in enumerate((0.0, 0.3)):
        ripple_progress = max(
            0,
            min(1, (progress - delay) / (1 - delay)),
        )
        if ripple_progress <= 0:
            continue
        radius_x = round(11 + ripple_progress * (44 + ripple_index * 9))
        radius_y = round(3 + ripple_progress * 8)
        pygame.draw.ellipse(
            ripple_surface,
            (
                114,
                133,
                65,
                round(115 * visibility * (1 - ripple_progress)),
            ),
            (
                center[0] - radius_x,
                center[1] - radius_y,
                radius_x * 2,
                radius_y * 2,
            ),
            width=1,
        )
    surface.blit(
        ripple_surface,
        (
            position[0] - ACT_THREE_TILE_SIZE,
            position[1] - ACT_THREE_TILE_SIZE // 2,
        ),
    )


def _draw_warlock_death_echoes(
    surface,
    assets,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    if player.warlock_demon_form_active and elapsed < 950:
        progress = elapsed / 950
        demon = assets["player_warlock_demon_hurt"].copy()
        demon.fill(
            (76, 9, 91, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        demon.set_alpha(round(145 * (1 - progress) ** 1.7))
        surface.blit(
            demon,
            (
                position[0] + round(math.sin(progress * 8) * 3),
                position[1] - round(progress * 9),
            ),
        )

    if 150 <= elapsed < _PLAYER_DEATH_COLLAPSE_END_MS:
        fade = 1 - (
            (elapsed - 150)
            / (_PLAYER_DEATH_COLLAPSE_END_MS - 150)
        )
        hurt_sprite = assets["player_warlock_hurt"]
        for echo_index, (offset_x, offset_y, alpha) in enumerate(
            ((-2, -2, 56), (3, -5, 34), (-4, -8, 19))
        ):
            echo = hurt_sprite.copy()
            echo.fill(
                (57 + echo_index * 8, 10, 70, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            echo.set_alpha(round(alpha * fade))
            surface.blit(
                echo,
                (position[0] + offset_x, position[1] + offset_y),
            )

    spirit_end = _PLAYER_DEATH_MESSAGE_START_MS - 250
    if _PLAYER_DEATH_COLLAPSE_END_MS <= elapsed < spirit_end:
        progress = (
            (elapsed - _PLAYER_DEATH_COLLAPSE_END_MS)
            / (spirit_end - _PLAYER_DEATH_COLLAPSE_END_MS)
        )
        spirit = assets["player_warlock_hurt"].copy()
        spirit.fill(
            (85, 16, 98, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        spirit.set_alpha(round(76 * (1 - progress) ** 1.5))
        surface.blit(
            spirit,
            (
                position[0] + round(math.sin(progress * 6) * 4),
                position[1] - 5 - round(progress * 18),
            ),
        )


def _draw_warlock_death_impact(
    surface,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    particle_start = _PLAYER_DEATH_HURT_HOLD_MS
    particle_end = _PLAYER_DEATH_MESSAGE_START_MS
    if particle_start <= elapsed < particle_end:
        progress = (
            (elapsed - particle_start)
            / (particle_end - particle_start)
        )
        particle_surface = pygame.Surface(
            (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
            pygame.SRCALPHA,
        )
        for particle_index in range(11):
            phase = (progress * 0.9 + particle_index * 0.149) % 1
            visibility = math.sin(math.pi * phase)
            particle_x = round(
                ACT_THREE_TILE_SIZE // 2
                + math.sin(particle_index * 2.43 + phase * 3) * (
                    8 + phase * 17
                )
            )
            particle_y = round(
                ACT_THREE_TILE_SIZE - 9
                - phase * (22 + particle_index % 4 * 5)
            )
            pygame.draw.polygon(
                particle_surface,
                (
                    150 + particle_index % 3 * 20,
                    54 + particle_index % 2 * 22,
                    185 + particle_index % 3 * 16,
                    round(165 * visibility * (1 - progress * 0.6)),
                ),
                (
                    (particle_x, particle_y - 2),
                    (particle_x + 1, particle_y + 1),
                    (particle_x - 1, particle_y + 1),
                ),
            )
        surface.blit(particle_surface, position)

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if not 0 <= impact_elapsed < 700:
        return
    progress = impact_elapsed / 700
    visibility = (1 - progress) ** 2
    ripple_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    center = (ACT_THREE_TILE_SIZE // 2, ACT_THREE_TILE_SIZE - 7)
    radius_x = round(8 + progress * 30)
    radius_y = round(2 + progress * 7)
    pygame.draw.ellipse(
        ripple_surface,
        (135, 55, 164, round(145 * visibility)),
        (
            center[0] - radius_x,
            center[1] - radius_y,
            radius_x * 2,
            radius_y * 2,
        ),
        width=1,
    )
    surface.blit(ripple_surface, position)


def _draw_warlock_death_foreground(
    surface,
    assets,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    particle_start = _PLAYER_DEATH_HURT_HOLD_MS
    particle_end = _PLAYER_DEATH_MESSAGE_START_MS
    if particle_start <= elapsed < particle_end:
        cycle = (elapsed - particle_start) / 1550
        fade = min(
            1,
            max(0, (elapsed - _PLAYER_DEATH_FALL_END_MS) / 1200),
        )
        effect_surface = pygame.Surface(
            (ACT_THREE_TILE_SIZE * 2, ACT_THREE_TILE_SIZE * 2),
            pygame.SRCALPHA,
        )
        center_x = ACT_THREE_TILE_SIZE
        base_y = ACT_THREE_TILE_SIZE + 19
        for particle_index in range(16):
            phase = (cycle + particle_index * 0.151) % 1
            visibility = math.sin(math.pi * phase) * (1 - fade * 0.8)
            drift = math.sin(particle_index * 2.29 + phase * 4.5)
            particle_x = round(
                center_x + drift * (9 + phase * 23)
            )
            particle_y = round(
                base_y - phase * (30 + particle_index % 5 * 6)
            )
            pygame.draw.polygon(
                effect_surface,
                (
                    164 + particle_index % 3 * 18,
                    55 + particle_index % 2 * 25,
                    197 + particle_index % 3 * 15,
                    round(195 * visibility),
                ),
                (
                    (particle_x, particle_y - 2),
                    (particle_x + 1, particle_y + 2),
                    (particle_x - 1, particle_y + 1),
                ),
            )
        surface.blit(
            effect_surface,
            (
                position[0] - ACT_THREE_TILE_SIZE // 2,
                position[1] - ACT_THREE_TILE_SIZE // 2,
            ),
        )

    spirit_start = _PLAYER_DEATH_COLLAPSE_END_MS
    spirit_end = _PLAYER_DEATH_MESSAGE_START_MS - 220
    if spirit_start <= elapsed < spirit_end:
        progress = (
            (elapsed - spirit_start) / (spirit_end - spirit_start)
        )
        spirit = assets["player_warlock_hurt"].copy()
        spirit.fill(
            (102, 17, 117, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        spirit.set_alpha(
            round(92 * math.sin(math.pi * progress))
        )
        surface.blit(
            spirit,
            (
                position[0] + round(math.sin(progress * 7) * 5),
                position[1] - 8 - round(progress * 22),
            ),
        )

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if not 0 <= impact_elapsed < 900:
        return
    progress = impact_elapsed / 900
    visibility = (1 - progress) ** 2
    ripple_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE * 3, ACT_THREE_TILE_SIZE * 2),
        pygame.SRCALPHA,
    )
    center = (
        ripple_surface.get_width() // 2,
        ACT_THREE_TILE_SIZE + 16,
    )
    for ripple_index, delay in enumerate((0.0, 0.27)):
        ripple_progress = max(
            0,
            min(1, (progress - delay) / (1 - delay)),
        )
        if ripple_progress <= 0:
            continue
        radius_x = round(11 + ripple_progress * (45 + ripple_index * 10))
        radius_y = round(3 + ripple_progress * 9)
        pygame.draw.ellipse(
            ripple_surface,
            (
                122,
                43,
                151 + ripple_index * 18,
                round(130 * visibility * (1 - ripple_progress)),
            ),
            (
                center[0] - radius_x,
                center[1] - radius_y,
                radius_x * 2,
                radius_y * 2,
            ),
            width=1,
        )
    surface.blit(
        ripple_surface,
        (
            position[0] - ACT_THREE_TILE_SIZE,
            position[1] - ACT_THREE_TILE_SIZE // 2,
        ),
    )


def _draw_summoner_death_echoes(
    surface,
    assets,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    if 160 <= elapsed < _PLAYER_DEATH_COLLAPSE_END_MS:
        fade = 1 - (
            (elapsed - 160)
            / (_PLAYER_DEATH_COLLAPSE_END_MS - 160)
        )
        hurt_sprite = assets["player_summoner_no_familiar_hurt"]
        for echo_index, (offset_x, offset_y, alpha) in enumerate(
            ((-2, -2, 54), (2, -5, 32), (-3, -8, 18))
        ):
            echo = hurt_sprite.copy()
            echo.fill(
                (8, 61 + echo_index * 8, 68, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            echo.set_alpha(round(alpha * fade))
            surface.blit(
                echo,
                (position[0] + offset_x, position[1] + offset_y),
            )

    spirit_end = _PLAYER_DEATH_MESSAGE_START_MS - 250
    if _PLAYER_DEATH_COLLAPSE_END_MS <= elapsed < spirit_end:
        progress = (
            (elapsed - _PLAYER_DEATH_COLLAPSE_END_MS)
            / (spirit_end - _PLAYER_DEATH_COLLAPSE_END_MS)
        )
        spirit = assets["player_summoner_no_familiar_hurt"].copy()
        spirit.fill(
            (9, 86, 91, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        spirit.set_alpha(round(72 * (1 - progress) ** 1.5))
        surface.blit(
            spirit,
            (
                position[0] + round(math.sin(progress * 6) * 3),
                position[1] - 5 - round(progress * 18),
            ),
        )


def _draw_summoner_death_impact(
    surface,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    thread_start = _PLAYER_DEATH_HURT_HOLD_MS
    thread_end = _PLAYER_DEATH_MESSAGE_START_MS
    if thread_start <= elapsed < thread_end:
        progress = (elapsed - thread_start) / (thread_end - thread_start)
        thread_surface = pygame.Surface(
            (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
            pygame.SRCALPHA,
        )
        center = (ACT_THREE_TILE_SIZE // 2, ACT_THREE_TILE_SIZE // 2 + 7)
        for thread_index in range(10):
            phase = (progress * 0.88 + thread_index * 0.167) % 1
            visibility = math.sin(math.pi * phase)
            angle = thread_index * math.tau / 10 + phase * 0.55
            distance = 7 + phase * (13 + thread_index % 3 * 4)
            endpoint = (
                round(center[0] + math.cos(angle) * distance),
                round(center[1] + math.sin(angle) * distance),
            )
            pygame.draw.line(
                thread_surface,
                (
                    58,
                    181 + thread_index % 3 * 18,
                    190,
                    round(125 * visibility * (1 - progress * 0.6)),
                ),
                center,
                endpoint,
                1,
            )
        surface.blit(thread_surface, position)

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if not 0 <= impact_elapsed < 680:
        return
    progress = impact_elapsed / 680
    visibility = (1 - progress) ** 2
    ripple_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    center = (ACT_THREE_TILE_SIZE // 2, ACT_THREE_TILE_SIZE - 7)
    radius_x = round(8 + progress * 29)
    radius_y = round(2 + progress * 7)
    pygame.draw.ellipse(
        ripple_surface,
        (65, 177, 181, round(140 * visibility)),
        (
            center[0] - radius_x,
            center[1] - radius_y,
            radius_x * 2,
            radius_y * 2,
        ),
        width=1,
    )
    surface.blit(ripple_surface, position)


def _draw_summoner_death_foreground(
    surface,
    assets,
    position,
    player,
    current_time,
):
    elapsed = _player_death_elapsed(player, current_time)
    if elapsed is None:
        return

    thread_start = _PLAYER_DEATH_HURT_HOLD_MS
    thread_end = _PLAYER_DEATH_MESSAGE_START_MS
    if thread_start <= elapsed < thread_end:
        cycle = (elapsed - thread_start) / 1650
        fade = min(
            1,
            max(0, (elapsed - _PLAYER_DEATH_FALL_END_MS) / 1200),
        )
        effect_surface = pygame.Surface(
            (ACT_THREE_TILE_SIZE * 2, ACT_THREE_TILE_SIZE * 2),
            pygame.SRCALPHA,
        )
        center = (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE + 15)
        for thread_index in range(15):
            phase = (cycle + thread_index * 0.153) % 1
            visibility = math.sin(math.pi * phase) * (1 - fade * 0.8)
            angle = thread_index * math.tau / 15 + phase * 0.7
            inner_distance = 7 + phase * 4
            outer_distance = 14 + phase * (18 + thread_index % 4 * 4)
            start = (
                round(center[0] + math.cos(angle) * inner_distance),
                round(center[1] + math.sin(angle) * inner_distance),
            )
            end = (
                round(center[0] + math.cos(angle) * outer_distance),
                round(center[1] + math.sin(angle) * outer_distance),
            )
            pygame.draw.line(
                effect_surface,
                (
                    53,
                    190 + thread_index % 3 * 17,
                    197,
                    round(170 * visibility),
                ),
                start,
                end,
                1,
            )
        surface.blit(
            effect_surface,
            (
                position[0] - ACT_THREE_TILE_SIZE // 2,
                position[1] - ACT_THREE_TILE_SIZE // 2,
            ),
        )

    spirit_start = _PLAYER_DEATH_COLLAPSE_END_MS
    spirit_end = _PLAYER_DEATH_MESSAGE_START_MS - 220
    if spirit_start <= elapsed < spirit_end:
        progress = (
            (elapsed - spirit_start) / (spirit_end - spirit_start)
        )
        spirit = assets["player_summoner_no_familiar_hurt"].copy()
        spirit.fill(
            (11, 105, 109, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        spirit.set_alpha(
            round(88 * math.sin(math.pi * progress))
        )
        surface.blit(
            spirit,
            (
                position[0] + round(math.sin(progress * 7) * 4),
                position[1] - 8 - round(progress * 22),
            ),
        )

    impact_elapsed = elapsed - _PLAYER_DEATH_FALL_END_MS
    if not 0 <= impact_elapsed < 880:
        return
    progress = impact_elapsed / 880
    visibility = (1 - progress) ** 2
    ripple_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE * 3, ACT_THREE_TILE_SIZE * 2),
        pygame.SRCALPHA,
    )
    center = (
        ripple_surface.get_width() // 2,
        ACT_THREE_TILE_SIZE + 16,
    )
    for ripple_index, delay in enumerate((0.0, 0.29)):
        ripple_progress = max(
            0,
            min(1, (progress - delay) / (1 - delay)),
        )
        if ripple_progress <= 0:
            continue
        radius_x = round(11 + ripple_progress * (44 + ripple_index * 10))
        radius_y = round(3 + ripple_progress * 9)
        pygame.draw.ellipse(
            ripple_surface,
            (
                47,
                151,
                158,
                round(125 * visibility * (1 - ripple_progress)),
            ),
            (
                center[0] - radius_x,
                center[1] - radius_y,
                radius_x * 2,
                radius_y * 2,
            ),
            width=1,
        )
    surface.blit(
        ripple_surface,
        (
            position[0] - ACT_THREE_TILE_SIZE,
            position[1] - ACT_THREE_TILE_SIZE // 2,
        ),
    )


def record_familiar_hit_feedback(game_state, started_at):
    hit_events = [
        event
        for event in game_state.events
        if (
            event.type is GameEventType.HIT
            and event.target == "familiar"
            and event.amount
        )
    ]
    if not hit_events:
        return

    player = game_state.player
    player.summoner_familiar_hit_animation_started_at = started_at
    player.summoner_familiar_hit_damage = sum(
        event.amount for event in hit_events
    )
    player.summoner_familiar_hit_origin = next(
        (
            event.origin
            for event in reversed(hit_events)
            if event.origin is not None
        ),
        None,
    )
    player.summoner_familiar_hit_position = next(
        (
            event.destination
            for event in reversed(hit_events)
            if event.destination is not None
        ),
        None,
    )


def _familiar_hit_feedback_active(player, current_time):
    elapsed = (
        current_time
        - player.summoner_familiar_hit_animation_started_at
    )
    return (
        player.summoner_familiar_hit_animation_started_at >= 0
        and 0 <= elapsed < _FAMILIAR_HIT_FEEDBACK_DURATION_MS
    )


def _familiar_hit_is_heavy(player):
    return player.summoner_familiar_hit_damage >= max(
        2,
        player.summoner_familiar_max_health * 0.25,
    )


def _familiar_hit_direction(player, familiar_column, familiar_row):
    origin = player.summoner_familiar_hit_origin
    if origin is None:
        return (0.0, 1.0)

    direction_x = familiar_column - origin[0]
    direction_y = familiar_row - origin[1]
    direction_length = max(
        1,
        math.hypot(direction_x, direction_y),
    )
    return (
        direction_x / direction_length,
        direction_y / direction_length,
    )


def _draw_familiar_hit_feedback(
    surface,
    sprite,
    position,
    player,
    familiar_column,
    familiar_row,
    current_time,
    damage_font,
):
    if not _familiar_hit_feedback_active(player, current_time):
        if sprite is not None:
            surface.blit(sprite, position)
        return

    elapsed = (
        current_time
        - player.summoner_familiar_hit_animation_started_at
    )
    direction_x, direction_y = _familiar_hit_direction(
        player,
        familiar_column,
        familiar_row,
    )
    recoil_progress = min(
        1,
        elapsed / _FAMILIAR_HIT_REACTION_DURATION_MS,
    )
    recoil = math.sin(math.pi * recoil_progress)
    recoil_distance = 6 if _familiar_hit_is_heavy(player) else 4
    sprite_position = (
        position[0] + round(direction_x * recoil_distance * recoil),
        position[1] + round(direction_y * recoil_distance * recoil),
    )

    if sprite is not None:
        surface.blit(sprite, sprite_position)
        if elapsed < _FAMILIAR_HIT_REACTION_DURATION_MS:
            flash = sprite.copy()
            flash.fill(
                (164, 226, 255, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            flash.set_alpha(round(225 * (1 - recoil_progress)))
            surface.blit(flash, sprite_position)

    center_x = position[0] + ACT_THREE_TILE_SIZE // 2
    center_y = position[1] + ACT_THREE_TILE_SIZE // 2
    particle_visibility = max(0, 1 - recoil_progress)
    particle_count = 9 if _familiar_hit_is_heavy(player) else 6
    particle_distance = 8 + recoil_progress * 18
    base_angle = math.atan2(direction_y, direction_x) + math.pi
    for particle_index in range(particle_count):
        spread = (
            particle_index - (particle_count - 1) / 2
        ) * 0.28
        angle = base_angle + spread
        particle_radius = 2 if particle_index % 3 == 0 else 1
        particle_surface = pygame.Surface(
            (particle_radius * 2 + 2, particle_radius * 2 + 2),
            pygame.SRCALPHA,
        )
        pygame.draw.circle(
            particle_surface,
            (91, 211, 255, round(245 * particle_visibility)),
            (particle_radius + 1, particle_radius + 1),
            particle_radius,
        )
        particle_position = (
            round(center_x + math.cos(angle) * particle_distance),
            round(center_y + math.sin(angle) * particle_distance),
        )
        surface.blit(
            particle_surface,
            (
                particle_position[0] - particle_radius - 1,
                particle_position[1] - particle_radius - 1,
            ),
        )

    number_progress = min(
        1,
        elapsed / _FAMILIAR_HIT_FEEDBACK_DURATION_MS,
    )
    number_alpha = round(
        255 * min(1, (1 - number_progress) * 2.6)
    )
    number_text = f"-{player.summoner_familiar_hit_damage}"
    number_color = (
        (195, 242, 255)
        if _familiar_hit_is_heavy(player)
        else (103, 218, 255)
    )
    number_surface = damage_font.render(
        number_text,
        True,
        number_color,
    )
    number_surface.set_alpha(number_alpha)
    number_position = number_surface.get_rect(
        center=(
            center_x,
            position[1] - 7 - round(number_progress * 13),
        )
    )
    shadow = damage_font.render(number_text, True, (5, 18, 27))
    shadow.set_alpha(number_alpha)
    surface.blit(shadow, number_position.move(1, 2))
    surface.blit(number_surface, number_position)


def _player_hit_feedback_active(player, current_time):
    elapsed = current_time - player.hit_animation_started_at
    return (
        player.hit_animation_started_at >= 0
        and 0 <= elapsed < _PLAYER_HIT_FEEDBACK_DURATION_MS
    )


def _player_hurt_sprite_active(player, current_time):
    elapsed = current_time - player.hit_animation_started_at
    return (
        player.hit_animation_started_at >= 0
        and 0 <= elapsed < _PLAYER_HIT_SPRITE_DURATION_MS
    )


def _player_hit_is_heavy(player):
    return (
        player.health <= 0
        or player.hit_damage >= max(2, player.max_health * 0.25)
    )


def _player_hit_direction(player, player_column, player_row):
    origin = player.hit_origin
    if origin is None:
        return (0.0, 1.0)

    direction_x = player_column - origin[0]
    direction_y = player_row - origin[1]
    direction_length = max(
        1,
        math.hypot(direction_x, direction_y),
    )
    return (
        direction_x / direction_length,
        direction_y / direction_length,
    )


def _player_hit_offset(
    player,
    player_column,
    player_row,
    current_time,
):
    elapsed = current_time - player.hit_animation_started_at
    if not 0 <= elapsed < _PLAYER_HIT_REACTION_DURATION_MS:
        return (0, 0)

    direction_x, direction_y = _player_hit_direction(
        player,
        player_column,
        player_row,
    )
    progress = elapsed / _PLAYER_HIT_REACTION_DURATION_MS
    recoil = math.sin(math.pi * progress)
    distance = 6 if _player_hit_is_heavy(player) else 4
    return (
        round(direction_x * distance * recoil),
        round(direction_y * distance * recoil),
    )


def _player_hit_camera_offset(player, current_time):
    elapsed = current_time - player.hit_animation_started_at
    if not 0 <= elapsed < _PLAYER_HIT_CAMERA_SHAKE_DURATION_MS:
        return (0, 0)

    progress = elapsed / _PLAYER_HIT_CAMERA_SHAKE_DURATION_MS
    strength = 4 if _player_hit_is_heavy(player) else 2
    decay = 1 - progress
    return (
        round(math.sin(elapsed * 0.19) * strength * decay),
        round(math.cos(elapsed * 0.27) * strength * 0.7 * decay),
    )


def _draw_player_hit_feedback(
    surface,
    sprite,
    position,
    player,
    player_column,
    player_row,
    current_time,
    damage_font,
):
    if not _player_hit_feedback_active(player, current_time):
        surface.blit(sprite, position)
        return

    elapsed = current_time - player.hit_animation_started_at
    offset_x, offset_y = _player_hit_offset(
        player,
        player_column,
        player_row,
        current_time,
    )
    sprite_position = (
        position[0] + offset_x,
        position[1] + offset_y,
    )
    surface.blit(sprite, sprite_position)

    if elapsed < _PLAYER_HIT_REACTION_DURATION_MS:
        reaction_progress = (
            elapsed / _PLAYER_HIT_REACTION_DURATION_MS
        )
        flash = sprite.copy()
        flash.fill(
            (255, 205, 185, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        flash.set_alpha(round(225 * (1 - reaction_progress)))
        surface.blit(flash, sprite_position)

        center_x = position[0] + ACT_THREE_TILE_SIZE // 2
        center_y = position[1] + ACT_THREE_TILE_SIZE // 2
        direction_x, direction_y = _player_hit_direction(
            player,
            player_column,
            player_row,
        )
        base_angle = math.atan2(direction_y, direction_x) + math.pi
        particle_count = 9 if _player_hit_is_heavy(player) else 6
        particle_distance = 8 + reaction_progress * 18
        particle_alpha = round(245 * (1 - reaction_progress))
        for particle_index in range(particle_count):
            spread = (
                particle_index - (particle_count - 1) / 2
            ) * 0.24
            angle = base_angle + spread
            particle_position = (
                round(center_x + math.cos(angle) * particle_distance),
                round(center_y + math.sin(angle) * particle_distance),
            )
            particle_radius = 2 if particle_index % 3 == 0 else 1
            particle_surface = pygame.Surface(
                (particle_radius * 2 + 2, particle_radius * 2 + 2),
                pygame.SRCALPHA,
            )
            pygame.draw.circle(
                particle_surface,
                (255, 112, 82, particle_alpha),
                (particle_radius + 1, particle_radius + 1),
                particle_radius,
            )
            surface.blit(
                particle_surface,
                (
                    particle_position[0] - particle_radius - 1,
                    particle_position[1] - particle_radius - 1,
                ),
            )

    number_progress = min(
        1,
        elapsed / _PLAYER_HIT_FEEDBACK_DURATION_MS,
    )
    number_alpha = round(
        255 * min(1, (1 - number_progress) * 2.6)
    )
    number_text = f"-{player.hit_damage}"
    number_color = (
        (255, 72, 52)
        if _player_hit_is_heavy(player)
        else (255, 126, 105)
    )
    number_surface = damage_font.render(
        number_text,
        True,
        number_color,
    )
    number_surface.set_alpha(number_alpha)
    number_position = number_surface.get_rect(
        center=(
            position[0] + ACT_THREE_TILE_SIZE // 2,
            position[1] - 7 - round(number_progress * 13),
        )
    )
    shadow = damage_font.render(number_text, True, (18, 7, 8))
    shadow.set_alpha(number_alpha)
    surface.blit(shadow, number_position.move(1, 2))
    surface.blit(number_surface, number_position)


def _draw_player_hit_vignette(surface, player, current_time):
    elapsed = current_time - player.hit_animation_started_at
    if not 0 <= elapsed < _PLAYER_HIT_VIGNETTE_DURATION_MS:
        return

    progress = elapsed / _PLAYER_HIT_VIGNETTE_DURATION_MS
    visibility = (1 - progress) ** 2
    base_alpha = round(
        (105 if _player_hit_is_heavy(player) else 72)
        * visibility
    )
    width, height = surface.get_size()
    vignette = pygame.Surface((width, height), pygame.SRCALPHA)
    for inset, alpha_scale in (
        (0, 1.0),
        (7, 0.72),
        (15, 0.42),
        (25, 0.18),
    ):
        pygame.draw.rect(
            vignette,
            (116, 8, 12, round(base_alpha * alpha_scale)),
            (inset, inset, width - inset * 2, height - inset * 2),
            width=8,
        )
    surface.blit(vignette, (0, 0))


def _enemy_hit_feedback_active(enemy, current_time):
    elapsed = current_time - enemy.hit_animation_started_at
    return (
        enemy.hit_animation_started_at >= 0
        and 0 <= elapsed < _ENEMY_HIT_FEEDBACK_DURATION_MS
    )


def _enemy_hit_offset(enemy, elapsed):
    if elapsed >= _ENEMY_HIT_REACTION_DURATION_MS:
        return (0, 0)

    origin = enemy.hit_origin
    direction_x = 0
    direction_y = -1
    if origin is not None:
        direction_x = enemy.column - origin[0]
        direction_y = enemy.row - origin[1]
        direction_length = max(
            1,
            math.hypot(direction_x, direction_y),
        )
        direction_x /= direction_length
        direction_y /= direction_length

    progress = elapsed / _ENEMY_HIT_REACTION_DURATION_MS
    recoil = math.sin(math.pi * progress)
    distance = 7 if enemy.hit_critical else 4
    return (
        round(direction_x * distance * recoil),
        round(direction_y * distance * recoil),
    )


def _draw_enemy_hit_feedback(
    surface,
    sprite,
    position,
    enemy,
    current_time,
    damage_font,
):
    if not _enemy_hit_feedback_active(enemy, current_time):
        surface.blit(sprite, position)
        return

    elapsed = current_time - enemy.hit_animation_started_at
    offset_x, offset_y = _enemy_hit_offset(enemy, elapsed)
    sprite_position = (
        position[0] + offset_x,
        position[1] + offset_y,
    )
    surface.blit(sprite, sprite_position)

    if elapsed < _ENEMY_HIT_REACTION_DURATION_MS:
        flash_progress = (
            elapsed / _ENEMY_HIT_REACTION_DURATION_MS
        )
        flash_alpha = round(220 * (1 - flash_progress))
        flash = sprite.copy()
        flash.fill(
            (255, 238, 205, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        flash.set_alpha(flash_alpha)
        surface.blit(flash, sprite_position)

    center_x = position[0] + ACT_THREE_TILE_SIZE // 2
    center_y = position[1] + ACT_THREE_TILE_SIZE // 2
    particle_progress = min(
        1,
        elapsed / _ENEMY_HIT_REACTION_DURATION_MS,
    )
    particle_visibility = max(0, 1 - particle_progress)
    particle_color = (
        (255, 194, 72)
        if enemy.hit_critical
        else (238, 224, 205)
    )
    particle_count = 8 if enemy.hit_critical else 6
    particle_distance = 10 + particle_progress * (
        20 if enemy.hit_critical else 14
    )

    for particle_index in range(particle_count):
        angle = (
            particle_index * math.tau / particle_count
            + (enemy.column * 0.71 + enemy.row * 1.13)
        )
        particle_position = (
            round(center_x + math.cos(angle) * particle_distance),
            round(center_y + math.sin(angle) * particle_distance),
        )
        particle_radius = 2 if particle_index % 3 == 0 else 1
        particle_surface = pygame.Surface(
            (particle_radius * 2 + 2, particle_radius * 2 + 2),
            pygame.SRCALPHA,
        )
        pygame.draw.circle(
            particle_surface,
            (*particle_color, round(255 * particle_visibility)),
            (particle_radius + 1, particle_radius + 1),
            particle_radius,
        )
        surface.blit(
            particle_surface,
            (
                particle_position[0] - particle_radius - 1,
                particle_position[1] - particle_radius - 1,
            ),
        )

    number_progress = min(
        1,
        elapsed / _ENEMY_HIT_FEEDBACK_DURATION_MS,
    )
    number_alpha = round(
        255 * min(1, (1 - number_progress) * 2.6)
    )
    number_color = (
        (255, 196, 64)
        if enemy.hit_critical
        else (245, 235, 220)
    )
    number_text = (
        f"{enemy.hit_damage}!"
        if enemy.hit_critical
        else str(enemy.hit_damage)
    )
    number_surface = damage_font.render(
        number_text,
        True,
        number_color,
    )
    number_surface.set_alpha(number_alpha)
    number_position = number_surface.get_rect(
        center=(
            center_x,
            position[1] - 7 - round(number_progress * 13),
        )
    )
    shadow = damage_font.render(number_text, True, (18, 10, 12))
    shadow.set_alpha(number_alpha)
    surface.blit(shadow, number_position.move(1, 2))
    surface.blit(number_surface, number_position)

def _draw_attack_impact_flash(
    surface,
    position,
    current_time,
    started_at,
    flash_color,
):
    elapsed = current_time - started_at
    if not 0 <= elapsed < _ATTACK_FRAME_DURATION_MS:
        return

    progress = elapsed / _ATTACK_FRAME_DURATION_MS
    visibility = math.sin(math.pi * progress)
    center = (
        position[0] + ACT_THREE_TILE_SIZE // 2,
        position[1] + ACT_THREE_TILE_SIZE // 2,
    )
    radius = round(7 + visibility * 9)
    alpha = round(190 * visibility)
    flash_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    local_center = (
        center[0] - position[0],
        center[1] - position[1],
    )
    pygame.draw.circle(
        flash_surface,
        (*flash_color, alpha),
        local_center,
        radius,
        width=2,
    )
    pygame.draw.line(
        flash_surface,
        (235, 255, 235, alpha),
        (local_center[0] - radius, local_center[1] + radius // 2),
        (local_center[0] + radius, local_center[1] - radius // 2),
        width=2,
    )
    surface.blit(flash_surface, position)


def _draw_archer_projectile(
    surface,
    arrow_sprite,
    origin,
    destination,
    progress,
    empowered=False,
    current_time=0,
):
    direction = math.atan2(
        destination[1] - origin[1],
        destination[0] - origin[0],
    )
    rotation = -math.degrees(direction) - 45
    arrow_position = (
        round(origin[0] + (destination[0] - origin[0]) * progress),
        round(origin[1] + (destination[1] - origin[1]) * progress),
    )

    for trail_progress, trail_alpha in (
        (progress - 0.18, 38),
        (progress - 0.10, 78),
    ):
        if trail_progress <= 0:
            continue
        trail_position = (
            round(origin[0] + (destination[0] - origin[0]) * trail_progress),
            round(origin[1] + (destination[1] - origin[1]) * trail_progress),
        )
        trail = pygame.transform.rotate(arrow_sprite, rotation).copy()
        trail.set_alpha(trail_alpha)
        surface.blit(trail, trail.get_rect(center=trail_position))

    if empowered:
        effect_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        travel_dx = destination[0] - origin[0]
        travel_dy = destination[1] - origin[1]
        travel_length = max(1, math.hypot(travel_dx, travel_dy))
        direction_x = travel_dx / travel_length
        direction_y = travel_dy / travel_length
        normal_x = -travel_dy / travel_length
        normal_y = travel_dx / travel_length

        trail_start_progress = max(0, progress - 0.34)
        trail_start = (
            round(origin[0] + travel_dx * trail_start_progress),
            round(origin[1] + travel_dy * trail_start_progress),
        )
        for width, color in (
            (12, (20, 135, 85, 24)),
            (7, (40, 220, 125, 48)),
            (3, (125, 255, 180, 145)),
            (1, (235, 255, 240, 225)),
        ):
            pygame.draw.line(
                effect_surface,
                color,
                trail_start,
                arrow_position,
                width=width,
            )

        for wave_index, (wave_color, wave_alpha) in enumerate(
            (
                ((75, 235, 135), 115),
                ((145, 255, 190), 70),
            )
        ):
            points = []
            for point_index in range(15):
                wave_progress = max(
                    0,
                    progress - 0.31 + point_index * 0.021,
                )
                wave_x = origin[0] + travel_dx * wave_progress
                wave_y = origin[1] + travel_dy * wave_progress
                wave = math.sin(
                    current_time * 0.014
                    + point_index * 0.82
                    + wave_index * math.pi
                ) * (3.5 + wave_index * 2)
                points.append(
                    (
                        round(wave_x + normal_x * wave),
                        round(wave_y + normal_y * wave),
                    )
                )
            if len(points) > 1:
                pygame.draw.lines(
                    effect_surface,
                    (*wave_color, wave_alpha),
                    False,
                    points,
                    width=1 if wave_index else 2,
                )

        for particle_index in range(9):
            particle_progress = progress - 0.035 - particle_index * 0.032
            if particle_progress <= 0:
                continue
            particle_wave = math.sin(
                current_time * 0.021 + particle_index * 2.15
            ) * (2 + particle_index * 0.45)
            particle_position = (
                round(
                    origin[0]
                    + travel_dx * particle_progress
                    + normal_x * particle_wave
                ),
                round(
                    origin[1]
                    + travel_dy * particle_progress
                    + normal_y * particle_wave
                ),
            )
            particle_alpha = max(30, 185 - particle_index * 17)
            particle_radius = 2 if particle_index < 3 else 1
            pygame.draw.circle(
                effect_surface,
                (155, 255, 195, particle_alpha),
                particle_position,
                particle_radius,
            )

        pulse = (math.sin(current_time * 0.025) + 1) / 2
        for radius, alpha in (
            (13, round(18 + pulse * 10)),
            (8, round(30 + pulse * 14)),
            (4, round(65 + pulse * 25)),
        ):
            pygame.draw.circle(
                effect_surface,
                (75, 245, 145, alpha),
                arrow_position,
                radius,
            )

        ring_angle = current_time * 0.012
        for angle_offset in (-0.9, 0.9):
            ring_length = 9
            ring_center = (
                round(
                    arrow_position[0]
                    - direction_x * 4
                    + normal_x * math.sin(ring_angle + angle_offset) * 5
                ),
                round(
                    arrow_position[1]
                    - direction_y * 4
                    + normal_y * math.sin(ring_angle + angle_offset) * 5
                ),
            )
            ring_end = (
                round(ring_center[0] + normal_x * ring_length),
                round(ring_center[1] + normal_y * ring_length),
            )
            pygame.draw.line(
                effect_surface,
                (205, 255, 220, 155),
                ring_center,
                ring_end,
                width=1,
            )

        if progress > 0.82:
            impact_progress = min(1, (progress - 0.82) / 0.18)
            impact_visibility = math.sin(math.pi * impact_progress)
            impact_radius = round(5 + impact_progress * 12)
            pygame.draw.circle(
                effect_surface,
                (
                    95,
                    255,
                    160,
                    round(150 * impact_visibility),
                ),
                destination,
                impact_radius,
                width=2,
            )
            for ray_index in range(6):
                ray_angle = ray_index * math.tau / 6 + direction
                ray_start = (
                    round(
                        destination[0]
                        + math.cos(ray_angle) * 4
                    ),
                    round(
                        destination[1]
                        + math.sin(ray_angle) * 4
                    ),
                )
                ray_end = (
                    round(
                        destination[0]
                        + math.cos(ray_angle) * impact_radius
                    ),
                    round(
                        destination[1]
                        + math.sin(ray_angle) * impact_radius
                    ),
                )
                pygame.draw.line(
                    effect_surface,
                    (
                        220,
                        255,
                        225,
                        round(175 * impact_visibility),
                    ),
                    ray_start,
                    ray_end,
                    width=1,
                )

        surface.blit(effect_surface, (0, 0))

    arrow = pygame.transform.rotate(arrow_sprite, rotation)
    surface.blit(arrow, arrow.get_rect(center=arrow_position))


def _draw_warlock_orb(
    surface,
    origin,
    destination,
    progress,
    current_time,
):
    orb_position = (
        round(
            origin[0]
            + (destination[0] - origin[0]) * progress
        ),
        round(
            origin[1]
            + (destination[1] - origin[1]) * progress
        ),
    )
    effect_surface = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    trail_start_progress = max(0, progress - 0.34)
    trail_start = (
        round(
            origin[0]
            + (destination[0] - origin[0])
            * trail_start_progress
        ),
        round(
            origin[1]
            + (destination[1] - origin[1])
            * trail_start_progress
        ),
    )
    for width, color in (
        (10, (72, 18, 112, 32)),
        (6, (126, 35, 188, 68)),
        (2, (211, 105, 255, 175)),
    ):
        pygame.draw.line(
            effect_surface,
            color,
            trail_start,
            orb_position,
            width=width,
        )

    pulse = (math.sin(current_time * 0.028) + 1) / 2
    for radius, color in (
        (10, (86, 20, 142, round(38 + pulse * 20))),
        (7, (144, 42, 222, round(95 + pulse * 35))),
        (4, (210, 105, 255, 235)),
        (2, (246, 220, 255, 255)),
    ):
        pygame.draw.circle(
            effect_surface,
            color,
            orb_position,
            radius,
        )

    for particle_index in range(5):
        angle = (
            current_time * 0.012
            + particle_index * math.tau / 5
        )
        particle_position = (
            round(orb_position[0] + math.cos(angle) * 9),
            round(orb_position[1] + math.sin(angle) * 7),
        )
        pygame.draw.circle(
            effect_surface,
            (225, 125, 255, 170),
            particle_position,
            1,
        )

    if progress > 0.78:
        impact_progress = min(
            1,
            (progress - 0.78) / 0.22,
        )
        impact_visibility = math.sin(
            math.pi * impact_progress
        )
        pygame.draw.circle(
            effect_surface,
            (
                205,
                75,
                255,
                round(190 * impact_visibility),
            ),
            destination,
            round(7 + impact_progress * 13),
            width=2,
        )

    surface.blit(effect_surface, (0, 0))


def _draw_assassin_slash_particles(
    surface,
    position,
    progress,
    identity_seed,
    strike_index,
):
    particle_surface = pygame.Surface(
        (ACT_THREE_TILE_SIZE, ACT_THREE_TILE_SIZE),
        pygame.SRCALPHA,
    )
    center = ACT_THREE_TILE_SIZE // 2
    visibility = math.sin(math.pi * progress)
    alpha = round(245 * visibility)
    slash_patterns = (
        ((-1.10, 25, -5), (-0.28, 19, 4), (0.62, 22, 0)),
        ((-0.55, 22, -7), (0.38, 28, 4), (1.18, 18, 1)),
        ((-1.38, 18, 3), (-0.72, 27, -4), (0.20, 24, 5)),
        ((-0.92, 29, 5), (0.02, 18, -5), (0.82, 26, 2)),
        ((-0.35, 20, -4), (0.56, 25, 5), (1.36, 19, -1)),
    )
    slash_pattern = slash_patterns[strike_index % len(slash_patterns)]
    for slash_index, (base_angle, length, offset) in enumerate(
        slash_pattern
    ):
        angle = (
            base_angle
            + math.sin(progress * math.tau + slash_index) * 0.16
            + (identity_seed % 11) * 0.01
        )
        bend = 5 + slash_index * 2
        start = (
            round(center + math.cos(angle) * offset - math.cos(angle) * length / 2),
            round(center + math.sin(angle) * offset - math.sin(angle) * length / 2),
        )
        end = (
            round(center + math.cos(angle) * offset + math.cos(angle) * length / 2),
            round(center + math.sin(angle) * offset + math.sin(angle) * length / 2),
        )
        middle = (
            round((start[0] + end[0]) / 2 - math.sin(angle) * bend),
            round((start[1] + end[1]) / 2 + math.cos(angle) * bend),
        )
        pygame.draw.line(
            particle_surface,
            (65, 145, 255, alpha // 3),
            start,
            middle,
            width=8,
        )
        pygame.draw.line(
            particle_surface,
            (65, 145, 255, alpha // 3),
            middle,
            end,
            width=8,
        )
        pygame.draw.line(
            particle_surface,
            (185, 230, 255, alpha),
            start,
            middle,
            width=2,
        )
        pygame.draw.line(
            particle_surface,
            (220, 245, 255, alpha),
            middle,
            end,
            width=2,
        )
        for shard_index, shard_side in enumerate((-1, 1)):
            shard_origin = (
                end[0] + round(math.cos(angle + math.pi / 2) * shard_side * 4),
                end[1] + round(math.sin(angle + math.pi / 2) * shard_side * 4),
            )
            shard_end = (
                shard_origin[0] + round(math.cos(angle + shard_side) * (5 + shard_index * 2)),
                shard_origin[1] + round(math.sin(angle + shard_side) * (5 + shard_index * 2)),
            )
            pygame.draw.line(
                particle_surface,
                (125, 205, 255, alpha),
                shard_origin,
                shard_end,
                width=2,
            )
    surface.blit(particle_surface, position)
