from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import (
    ChestState,
    EnemyBehaviorState,
    GameState,
    RoomState,
)
from levels import FLOOR_CONFIGS
from logic import can_move_between
from settings import POTION_HEALING


def try_use_potion(game_state: GameState) -> bool:
    player = game_state.player

    if (
        player.potion_count <= 0
        or player.health >= player.max_health
    ):
        return False

    previous_health = player.health
    player.health = min(
        player.max_health,
        player.health + POTION_HEALING,
    )
    player.potion_count -= 1
    healed_health = player.health - previous_health
    game_state.emit(
        GameEvent(
            type=GameEventType.HEAL,
            actor="hero",
            target="hero",
            amount=healed_health,
        )
    )
    add_log_message(
        game_state.combat_log,
        f"Hero heals {healed_health} HP.",
    )

    return True


def open_chest(
    game_state: GameState,
    chest: ChestState,
    effect_started_at: int = 0,
) -> bool:
    player = game_state.player

    if player.key_count <= 0:
        add_log_message(
            game_state.combat_log,
            "The chest is locked.",
        )
        return True

    chest["is_open"] = True
    chest.open_animation_started_at = effect_started_at
    player.key_count -= 1

    if chest["contains"] == "gold":
        chest["loot_available"] = True
        add_log_message(
            game_state.combat_log,
            "Chest opened: gold found.",
        )

    return True


def _position_is_inside_room(
    column: int,
    row: int,
    room: RoomState | None,
) -> bool:
    return (
        room is not None
        and room["x"] <= column < room["x"] + room["width"]
        and room["y"] <= row < room["y"] + room["height"]
    )


def _activate_boss_fight(game_state: GameState) -> None:
    floor = game_state.floor
    floor.boss_fight_started = True

    for enemy in floor.enemies:
        if enemy.boss_group:
            enemy.is_active = True
            enemy.is_aggro = True
            enemy.behavior_state = EnemyBehaviorState.CHASING

    awakened_boss = next(
        (
            enemy
            for enemy in floor.enemies
            if enemy.boss_group
        ),
        None,
    )
    add_log_message(
        game_state.combat_log,
        "The boss chamber opens!",
    )

    if awakened_boss is None:
        boss_entry_message = "The boss awakens."
    elif awakened_boss.type == "oracle":
        boss_entry_message = (
            "Oracle's dormant shell begins to move."
        )
    else:
        boss_entry_message = (
            f"{awakened_boss.name} awakens."
        )

    add_log_message(
        game_state.combat_log,
        boss_entry_message,
    )

    if floor.seal_boss_door_during_fight:
        add_log_message(
            game_state.combat_log,
            "The chamber seals behind the hero.",
        )


def _start_pickup_effect(
    game_state: GameState,
    kind: str,
    position: tuple[int, int],
    effect_started_at: int,
) -> None:
    player = game_state.player
    act_number = FLOOR_CONFIGS[game_state.floor_index]["act"]
    if act_number == 1:
        player.act_one_pickup_kind = kind
        player.act_one_pickup_origin = position
        player.act_one_pickup_started_at = effect_started_at
    elif act_number == 2:
        player.act_two_pickup_kind = kind
        player.act_two_pickup_origin = position
        player.act_two_pickup_started_at = effect_started_at


def _collect_items(
    game_state: GameState,
    effect_started_at: int = 0,
) -> None:
    floor = game_state.floor
    player = game_state.player
    player_position = (
        floor.player_column,
        floor.player_row,
    )
    found_potion = next(
        (
            potion
            for potion in floor.potions
            if (potion["column"], potion["row"])
            == player_position
        ),
        None,
    )

    if found_potion:
        player.potion_count += 1
        floor.potions.remove(found_potion)
        _start_pickup_effect(
            game_state,
            "potion",
            player_position,
            effect_started_at,
        )
        add_log_message(
            game_state.combat_log,
            "Hero picks up a potion.",
        )

    chest_with_coin = next(
        (
            chest
            for chest in floor.chests
            if (
                chest["is_open"]
                and chest["loot_available"]
                and (chest["column"], chest["row"])
                == player_position
            )
        ),
        None,
    )

    if chest_with_coin:
        player.gold_count += 1
        chest_with_coin["loot_available"] = False
        _start_pickup_effect(
            game_state,
            "gold",
            player_position,
            effect_started_at,
        )
        add_log_message(
            game_state.combat_log,
            "Hero picks up one gold.",
        )

    found_key = next(
        (
            key_position
            for key_position in floor.dropped_keys
            if key_position == player_position
        ),
        None,
    )

    if found_key is not None:
        player.key_count += 1
        floor.dropped_keys.remove(found_key)
        _start_pickup_effect(
            game_state,
            "key",
            player_position,
            effect_started_at,
        )
        add_log_message(
            game_state.combat_log,
            "Hero picks up a key.",
        )


def _resolve_stairs(
    game_state: GameState,
    first_act_final_floor: int,
) -> bool:
    floor = game_state.floor
    reached_open_stairs = (
        not any(enemy.health > 0 for enemy in floor.enemies)
        and (floor.player_column, floor.player_row)
        == (floor.stairs_column, floor.stairs_row)
    )

    if not reached_open_stairs:
        return True

    current_floor_config = FLOOR_CONFIGS[
        game_state.floor_index
    ]
    next_act = (
        FLOOR_CONFIGS[game_state.floor_index + 1]["act"]
        if game_state.floor_index + 1 < len(FLOOR_CONFIGS)
        else None
    )
    reached_end_of_act_two = (
        current_floor_config["act"] == 2
        and next_act != 2
    )

    if reached_end_of_act_two:
        if (
            game_state.player.player_class
            in ("warrior", "rogue")
            and game_state.player.subclass is None
        ):
            game_state.act_three_transition_open = True
            game_state.act_three_visual_started_at = 0
            game_state.player_attack_targets = []
            add_log_message(
                game_state.combat_log,
                "The second veil begins to fall.",
            )
            return False

        game_state.game_won = True
        add_log_message(
            game_state.combat_log,
            "The Crypta is conquered.",
        )
        return True

    if game_state.floor_index == len(FLOOR_CONFIGS) - 1:
        game_state.game_won = True
        add_log_message(
            game_state.combat_log,
            "The Crypta is conquered.",
        )
        return True

    if (
        game_state.floor_index == first_act_final_floor
        and game_state.player.player_class is None
    ):
        game_state.class_selection_open = True
        game_state.player_attack_targets = []
        add_log_message(
            game_state.combat_log,
            "The first veil falls.",
        )
        return False

    game_state.upgrade_screen_open = True
    game_state.upgrade_message = ""
    game_state.player_attack_targets = []
    add_log_message(
        game_state.combat_log,
        "The descent altar opens.",
    )

    return False


def try_move_player(
    game_state: GameState,
    new_column: int,
    new_row: int,
    first_act_final_floor: int,
    transition_started_at: int,
) -> bool:
    floor = game_state.floor
    living_enemies = [
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
    ]
    target_position = (new_column, new_row)
    stairs_are_open = not living_enemies
    target_is_locked_stairs = (
        not stairs_are_open
        and target_position
        == (floor.stairs_column, floor.stairs_row)
    )
    target_is_boss_door = (
        floor.boss_door is not None
        and target_position == floor.boss_door
    )
    living_boss_group = [
        enemy
        for enemy in living_enemies
        if enemy.boss_group
    ]
    living_boss_guards = [
        enemy
        for enemy in living_enemies
        if not enemy.boss_group
    ]
    boss_door_is_guarded = (
        target_is_boss_door
        and not floor.boss_fight_started
        and bool(living_boss_guards)
    )
    boss_door_is_sealed = (
        floor.seal_boss_door_during_fight
        and floor.boss_fight_started
        and bool(living_boss_group)
    )

    if boss_door_is_guarded:
        add_log_message(
            game_state.combat_log,
            "Defeat the guards before entering the boss chamber.",
        )
        return False

    if target_is_boss_door and boss_door_is_sealed:
        add_log_message(
            game_state.combat_log,
            "The boss chamber is sealed.",
        )
        return False

    if (
        target_is_locked_stairs
        or not can_move_between(
            floor.map,
            floor.player_column,
            floor.player_row,
            new_column,
            new_row,
            floor.barriers,
        )
    ):
        return False

    previous_position = (
        floor.player_column,
        floor.player_row,
    )
    floor.player_column = new_column
    floor.player_row = new_row
    game_state.player.movement_animation_started_at = (
        transition_started_at
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.MOVE,
            actor="hero",
            origin=previous_position,
            destination=(new_column, new_row),
        )
    )
    target_is_inside_boss_room = _position_is_inside_room(
        new_column,
        new_row,
        floor.boss_room,
    )
    entered_boss_room = (
        (
            (
                target_is_boss_door
                and not floor.seal_boss_door_during_fight
            )
            or (
                target_is_inside_boss_room
                and not target_is_boss_door
            )
        )
        and not floor.boss_fight_started
    )

    if entered_boss_room:
        _activate_boss_fight(game_state)

    _collect_items(game_state, transition_started_at)
    player_acted = _resolve_stairs(
        game_state,
        first_act_final_floor,
    )

    if game_state.class_selection_open:
        game_state.class_transition_started_at = (
            transition_started_at
        )

    if game_state.act_three_transition_open:
        game_state.act_three_transition_started_at = (
            transition_started_at
        )

    return player_acted
