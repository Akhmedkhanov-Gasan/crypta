from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from acts.act_two.crates import collect_crate_loot
from acts.act_two.consumables import (
    FIRE_BOMB,
    KEY,
    POTION,
    act_two_belt_is_full,
    consume_act_two_potion,
    consume_act_two_key,
    get_act_two_consumable_slots,
    store_act_two_consumable,
)
from game.state import (
    ChestState,
    EnemyBehaviorState,
    GameState,
    RoomState,
)
from acts.act_two.treasury import collect_treasury_reward
from levels import FLOOR_CONFIGS
from logic import can_player_move_between
from settings import POTION_HEALING


def try_use_potion(
    game_state: GameState,
    slot_index: int | None = None,
) -> bool:
    player = game_state.player
    act_number = FLOOR_CONFIGS[game_state.floor_index]["act"]
    if act_number == 2:
        slots = get_act_two_consumable_slots(player)
        potion_is_available = (
            any(item == POTION for item in slots)
            if slot_index is None
            else (
                0 <= slot_index < len(slots)
                and slots[slot_index] == POTION
            )
        )
    else:
        potion_is_available = player.potion_count > 0

    if (
        not potion_is_available
        or player.health >= player.max_health
    ):
        return False

    previous_health = player.health
    player.health = min(
        player.max_health,
        player.health + POTION_HEALING,
    )
    if act_number == 2:
        consume_act_two_potion(player, slot_index)
    else:
        player.potion_count -= 1
    healed_health = player.health - previous_health
    game_state.emit(
        GameEvent(
            type=GameEventType.HEAL,
            actor="hero",
            target="hero",
            amount=healed_health,
            data={"kind": "potion"},
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
    act_number = FLOOR_CONFIGS[game_state.floor_index]["act"]

    has_required_key = (
        KEY in get_act_two_consumable_slots(player)
        if act_number == 2
        else player.key_count > 0
    )
    if chest.requires_key and not has_required_key:
        add_log_message(
            game_state.combat_log,
            "The chest is locked.",
        )
        return True

    chest["is_open"] = True
    chest.open_animation_started_at = effect_started_at
    game_state.emit(
        GameEvent(
            type=GameEventType.CHEST_OPEN,
            actor="hero",
            destination=(chest.column, chest.row),
            data={"contains": chest.contains},
        )
    )
    if chest.requires_key:
        if act_number == 2:
            consume_act_two_key(player)
        else:
            player.key_count -= 1

    if chest["contains"] in ("gold", POTION, FIRE_BOMB):
        chest["loot_available"] = True
        loot_name = {
            POTION: "a healing potion",
            FIRE_BOMB: "a fire bomb",
            "gold": "gold",
        }[chest["contains"]]
        add_log_message(
            game_state.combat_log,
            f"Chest opened: {loot_name} found.",
        )

    return True


def break_secret_passage(
    game_state: GameState,
    column: int,
    row: int,
) -> bool:
    floor = game_state.floor
    if not (
        0 <= row < len(floor.map)
        and 0 <= column < len(floor.map[row])
        and floor.map[row][column] == "S"
    ):
        return False

    passage_row = floor.map[row]
    floor.map[row] = (
        passage_row[:column]
        + "s"
        + passage_row[column + 1:]
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(floor.player_column, floor.player_row),
            positions=((column, row),),
            data={"kind": "secret_wall"},
        )
    )
    add_log_message(
        game_state.combat_log,
        "Hero shatters a weakened wall.",
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
    game_state.emit(
        GameEvent(
            type=GameEventType.PICKUP,
            actor="hero",
            destination=position,
            data={"kind": kind},
        )
    )
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
    act_number = FLOOR_CONFIGS[game_state.floor_index]["act"]
    collect_treasury_reward(game_state, player_position)
    crate_loot_kind = collect_crate_loot(
        game_state,
        player_position,
    )
    if crate_loot_kind is not None:
        pickup_kind = (
            "potion" if crate_loot_kind == "potion" else "gold"
        )
        _start_pickup_effect(
            game_state,
            pickup_kind,
            player_position,
            effect_started_at,
        )
        add_log_message(
            game_state.combat_log,
            (
                "Hero picks up a potion."
                if crate_loot_kind == "potion"
                else "Hero picks up one gold."
            ),
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

    if found_potion and not (
        act_number == 2 and act_two_belt_is_full(player)
    ):
        if act_number == 2:
            store_act_two_consumable(player, POTION)
        else:
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
    elif found_potion:
        add_log_message(
            game_state.combat_log,
            "The consumable belt is full.",
        )

    chest_with_loot = next(
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

    if (
        chest_with_loot
        and chest_with_loot["contains"] in (POTION, FIRE_BOMB)
        and act_number == 2
        and act_two_belt_is_full(player)
    ):
        add_log_message(
            game_state.combat_log,
            "The consumable belt is full.",
        )
    elif chest_with_loot:
        loot_kind = chest_with_loot["contains"]
        if loot_kind == POTION:
            if act_number == 2:
                store_act_two_consumable(player, POTION)
            else:
                player.potion_count += 1
            pickup_kind = "potion"
            message = "Hero picks up a potion."
        elif loot_kind == FIRE_BOMB:
            store_act_two_consumable(player, FIRE_BOMB)
            pickup_kind = FIRE_BOMB
            message = "Hero picks up a fire bomb."
        else:
            player.gold_count += 1
            pickup_kind = "gold"
            message = "Hero picks up one gold."
        chest_with_loot["loot_available"] = False
        _start_pickup_effect(
            game_state,
            pickup_kind,
            player_position,
            effect_started_at,
        )
        add_log_message(
            game_state.combat_log,
            message,
        )

    found_key = next(
        (
            key_position
            for key_position in floor.dropped_keys
            if key_position == player_position
        ),
        None,
    )

    if (
        found_key is not None
        and act_number == 2
        and act_two_belt_is_full(player)
    ):
        add_log_message(
            game_state.combat_log,
            "The consumable belt is full.",
        )
    elif found_key is not None:
        if act_number == 2:
            store_act_two_consumable(player, KEY)
        else:
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

    if current_floor_config["act"] == 1:
        game_state.act_one_upgrades_remaining = current_floor_config[
            "act_floor"
        ]
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
    if any(
        not crate.is_broken
        and (crate.column, crate.row) == target_position
        for crate in floor.breakable_crates
    ):
        return False
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
        or not can_player_move_between(
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
