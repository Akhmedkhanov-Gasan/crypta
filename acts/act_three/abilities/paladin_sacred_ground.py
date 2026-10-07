from game.combat_log import add_log_message
from game.state import GameState
from logic import (
    can_move_to,
    get_enemy_occupied_positions,
)
from acts.act_three.events import GameEvent, GameEventType
from acts.act_three.settings import (
    PALADIN_SACRED_GROUND_CHARGES,
    PALADIN_SACRED_GROUND_DAMAGE_MAX,
    PALADIN_SACRED_GROUND_DAMAGE_MIN,
    PALADIN_SACRED_GROUND_IMPACT_MS,
    PALADIN_SACRED_GROUND_RADIUS,
    PALADIN_SACRED_GROUND_TURNS,
    PALADIN_SACRED_GROUND_CAST_MS,
)
from acts.act_three.state import PaladinSacredLightningState
from systems.player_combat import (
    attack_enemy,
    resolve_enemy_defeat,
)


def get_paladin_sacred_ground_cells(
    game_state: GameState,
    anchor: tuple[int, int],
) -> list[tuple[int, int]]:
    dungeon_map = game_state.floor.map
    cells = []

    for row in range(
        anchor[1] - PALADIN_SACRED_GROUND_RADIUS,
        anchor[1] + PALADIN_SACRED_GROUND_RADIUS + 1,
    ):
        for column in range(
            anchor[0] - PALADIN_SACRED_GROUND_RADIUS,
            anchor[0] + PALADIN_SACRED_GROUND_RADIUS + 1,
        ):
            if not (
                0 <= row < len(dungeon_map)
                and 0 <= column < len(dungeon_map[0])
                and can_move_to(dungeon_map, column, row)
            ):
                continue

            cells.append((column, row))

    return cells


def request_paladin_sacred_ground(
    game_state: GameState,
    current_time: int,
) -> bool:
    player = game_state.player

    if (
        player.subclass != "paladin"
        or player.paladin_sacred_ground_cast_requested
        or paladin_sacred_ground_cast_active(
            player,
            current_time,
        )
    ):
        return False

    if (
        not player.debug_unlimited_abilities
        and player.paladin_sacred_ground_charge
        < PALADIN_SACRED_GROUND_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Sacred Ground is not charged.",
        )
        return False

    player.paladin_shield_charge_aiming = False
    player.paladin_shield_charge_target = None
    player.paladin_shield_charge_preview_cells.clear()
    player.paladin_sacred_ground_cast_requested = True
    player.paladin_sacred_ground_started_at = current_time

    add_log_message(
        game_state.combat_log,
        "The paladin raises his blade for Sacred Ground.",
    )
    return True


def paladin_sacred_ground_cast_active(
    player,
    current_time: int,
) -> bool:
    started_at = player.paladin_sacred_ground_started_at
    return (
        player.subclass == "paladin"
        and started_at > 0
        and 0
        <= current_time - started_at
        < PALADIN_SACRED_GROUND_CAST_MS
    )


def paladin_sacred_ground_impact_ready(
    game_state: GameState,
    current_time: int,
) -> bool:
    player = game_state.player
    return (
        player.subclass == "paladin"
        and player.paladin_sacred_ground_cast_requested
        and player.paladin_sacred_ground_started_at > 0
        and current_time
        - player.paladin_sacred_ground_started_at
        >= PALADIN_SACRED_GROUND_IMPACT_MS
    )


def perform_paladin_sacred_ground(
    game_state: GameState,
    current_time: int,
) -> bool:
    player = game_state.player
    floor = game_state.floor

    if (
        player.subclass != "paladin"
        or not player.paladin_sacred_ground_cast_requested
        or current_time
        - player.paladin_sacred_ground_started_at
        < PALADIN_SACRED_GROUND_IMPACT_MS
    ):
        return False

    anchor = (
        floor.player_column,
        floor.player_row,
    )

    player.paladin_sacred_ground_charge = 0
    player.paladin_sacred_ground_cast_requested = False
    player.paladin_sacred_ground_anchor = anchor
    player.paladin_sacred_ground_cells = (
        get_paladin_sacred_ground_cells(
            game_state,
            anchor,
        )
    )
    player.paladin_sacred_ground_turns = (
        PALADIN_SACRED_GROUND_TURNS
    )
    player.paladin_sacred_ground_lightnings.clear()

    add_log_message(
        game_state.combat_log,
        "The paladin drives his blade into the earth.",
    )
    add_log_message(
        game_state.combat_log,
        "Sacred Ground erupts in corrupted light.",
    )

    resolve_paladin_sacred_ground(game_state)
    return True


def resolve_paladin_sacred_ground(
    game_state: GameState,
) -> int:
    player = game_state.player
    zone_cells = set(player.paladin_sacred_ground_cells)

    if (
        player.subclass != "paladin"
        or player.paladin_sacred_ground_turns <= 0
        or not zone_cells
    ):
        return 0

    enemies_hit = 0

    for enemy in tuple(game_state.floor.enemies):
        if (
            enemy.health <= 0
            or not (
                get_enemy_occupied_positions(enemy)
                & zone_cells
            )
        ):
            continue

        target = (
            enemy.column,
            enemy.row,
        )
        player.paladin_sacred_ground_lightnings.append(
            PaladinSacredLightningState(
                target=target,
            )
        )
        game_state.emit(
            GameEvent(
                type=GameEventType.ATTACK,
                actor="hero",
                target=enemy.name,
                origin=player.paladin_sacred_ground_anchor,
                destination=target,
                positions=(target,),
                data={"kind": "paladin_sacred_ground"},
            )
        )

        enemy_was_defeated = attack_enemy(
            game_state,
            enemy,
            PALADIN_SACRED_GROUND_DAMAGE_MIN,
            PALADIN_SACRED_GROUND_DAMAGE_MAX,
            player.crit_chance,
            attacker_position=(
                player.paladin_sacred_ground_anchor
            ),
            grant_ability_charge=False,
        )

        add_log_message(
            game_state.combat_log,
            f"Black lightning strikes {enemy.name}.",
        )

        if enemy.type == "oracle":
            from bosses.oracle import resolve_oracle_hit_reaction

            resolve_oracle_hit_reaction(
                enemy,
                game_state.floor,
                game_state.combat_log,
            )

        if enemy_was_defeated:
            resolve_enemy_defeat(game_state, enemy)

        enemies_hit += 1

    return enemies_hit


def advance_paladin_sacred_ground(
    game_state: GameState,
) -> None:
    player = game_state.player

    if (
        player.subclass != "paladin"
        or player.paladin_sacred_ground_turns <= 0
    ):
        return

    player.paladin_sacred_ground_turns -= 1

    if player.paladin_sacred_ground_turns > 0:
        return

    player.paladin_sacred_ground_cells.clear()
    player.paladin_sacred_ground_anchor = None

    add_log_message(
        game_state.combat_log,
        "The corrupted ground falls silent.",
    )
