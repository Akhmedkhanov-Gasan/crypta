import random
from dataclasses import dataclass

import pygame

from acts.act_two.presentation.bosses.oracle_balance import (
    BLACKFIRE_CONTACT_DAMAGE,
    BLACKFIRE_EXPLOSION_DAMAGE,
    BLACKFIRE_TURNS,
    IMPACT_MS,
)
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType


@dataclass
class OracleGroundFireState:
    cells: tuple = ()
    turns_remaining: int = 0
    impact_cells: tuple = ()
    impact_started_at: int = -1
    sound_pending: bool = False


def add_oracle_ground_fire(ground_fire, cells):
    ground_fire.cells = tuple(
        dict.fromkeys(
            (*ground_fire.cells, *cells)
        )
    )
    ground_fire.turns_remaining = BLACKFIRE_TURNS


def ground_fire_visible_cells(ground_fire, current_time):
    cells = list(ground_fire.cells)

    if (
        ground_fire.impact_started_at >= 0
        and current_time - ground_fire.impact_started_at < IMPACT_MS
    ):
        cells.extend(ground_fire.impact_cells)

    return tuple(dict.fromkeys(cells))


def _damage_player_with_ground_fire(
    game_state,
    state,
    damage,
    mode,
):
    from systems.player_combat import damage_player

    floor = game_state.floor
    player = game_state.player
    caster = state.caster
    position = (floor.player_column, floor.player_row)

    if player.health <= 0:
        return

    dealt = damage_player(
        game_state,
        damage,
        damage_kind="magic",
    )

    if dealt > 0 and player.invisibility_turns > 0:
        player.invisibility_turns = 0

    game_state.emit(
        GameEvent(
            type=GameEventType.HIT,
            actor=caster.name,
            target="hero",
            origin=position,
            destination=position,
            amount=dealt,
            data={
                "enemy_type": "oracle",
                "mode": mode,
            },
        ),
    )

    add_log_message(
        game_state.combat_log,
        (
            f"Blackfire deals {dealt} damage."
            if mode == "blackfire_contact"
            else
            f"Oracle's blackfire eruption deals {dealt} damage."
        ),
        category="enemy_attack",
    )

    if player.health <= 0:
        game_state.emit(
            GameEvent(
                type=GameEventType.DEATH,
                actor="hero",
                destination=position,
                data={"cause": caster.name},
            ),
        )
        add_log_message(
            game_state.combat_log,
            "The hero has fallen.",
            category="death",
        )


def advance_oracle_ground_fire(game_state, state):
    ground_fire = state.ground_fire

    if not ground_fire.cells:
        return

    floor = game_state.floor
    player = game_state.player
    position = (floor.player_column, floor.player_row)

    if (
        player.health > 0
        and position in ground_fire.cells
    ):
        _damage_player_with_ground_fire(
            game_state,
            state,
            BLACKFIRE_CONTACT_DAMAGE,
            "blackfire_contact",
        )

    ground_fire.turns_remaining = max(
        0,
        ground_fire.turns_remaining - 1,
    )

    if ground_fire.turns_remaining > 0:
        return

    cells = ground_fire.cells
    ground_fire.cells = ()
    ground_fire.impact_cells = cells
    ground_fire.impact_started_at = pygame.time.get_ticks()
    ground_fire.sound_pending = True

    if player.health <= 0:
        return

    if position not in cells:
        add_log_message(
            game_state.combat_log,
            "The blackfire erupts on empty stone.",
            category="defense",
        )
        return

    if random.random() < player.dodge_chance:
        game_state.emit(
            GameEvent(
                type=GameEventType.DODGE,
                actor=state.caster.name,
                target="hero",
                origin=(state.caster.column, state.caster.row),
                destination=position,
                data={
                    "enemy_type": "oracle",
                    "mode": "blast",
                },
            ),
        )
        add_log_message(
            game_state.combat_log,
            "The hero evades Oracle's blackfire eruption.",
            category="defense",
        )
        return

    _damage_player_with_ground_fire(
        game_state,
        state,
        BLACKFIRE_EXPLOSION_DAMAGE,
        "blast",
    )
