import random

from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import (
    EnemyBehaviorState,
    GameState,
    ProjectileState,
)
from logic import (
    can_move_to,
    direction_toward,
    get_enemy_occupied_positions,
    get_oracle_ray,
)

def choose_oracle_action(oracle):
    if oracle["oracle_awakened"]:
        actions = ("straight", "terrain", "homing")
        action_weights = {
            "straight": (
                25
                if oracle["last_oracle_action"] == "straight"
                else 45
            ),
            "terrain": 30,
            "homing": 25,
        }
    else:
        actions = ("straight", "terrain")
        action_weights = {
            "straight": (
                30
                if oracle["last_oracle_action"] == "straight"
                else 60
            ),
            "terrain": 40,
        }
    available_actions = [
        action
        for action in actions
        if not (
            action == "homing"
            and oracle["last_oracle_action"] == "homing"
        )
    ]
    selected_action = random.choices(
        available_actions,
        weights=[
            action_weights[action]
            for action in available_actions
        ],
        k=1,
    )[0]
    oracle["last_oracle_action"] = selected_action

    return selected_action


def choose_straight_pattern(oracle):
    patterns = (
        "cross",
        "diagonal",
        "horizontal",
        "vertical",
    )
    available_patterns = [
        pattern
        for pattern in patterns
        if pattern != oracle["last_straight_pattern"]
    ]
    selected_pattern = random.choice(available_patterns)
    oracle["last_straight_pattern"] = selected_pattern

    return selected_pattern


def spawn_oracle_projectiles(
    oracle,
    floor_state,
    combat_log,
    projectile_kind,
):
    second_phase = (
        oracle["health"] <= oracle["max_health"] // 2
    )
    pattern_name = None

    if projectile_kind == "straight":
        pattern_name = choose_straight_pattern(oracle)
        pattern_projectiles = {
            "cross": [
                ((0, -3), (0, -1)),
                ((3, 0), (1, 0)),
                ((0, 3), (0, 1)),
                ((-3, 0), (-1, 0)),
            ],
            "diagonal": [
                ((-3, -3), (-1, -1)),
                ((3, -3), (1, -1)),
                ((3, 3), (1, 1)),
                ((-3, 3), (-1, 1)),
            ],
            "horizontal": [
                ((-3, -1), (-1, 0)),
                ((-3, 0), (-1, 0)),
                ((-3, 1), (-1, 0)),
                ((3, -1), (1, 0)),
                ((3, 0), (1, 0)),
                ((3, 1), (1, 0)),
            ],
            "vertical": [
                ((-1, -3), (0, -1)),
                ((0, -3), (0, -1)),
                ((1, -3), (0, -1)),
                ((-1, 3), (0, 1)),
                ((0, 3), (0, 1)),
                ((1, 3), (0, 1)),
            ],
        }
        projectile_specs = pattern_projectiles[pattern_name]
    else:
        occupied_projectile_positions = {
            (projectile["column"], projectile["row"])
            for projectile in floor_state["projectiles"]
        }
        available_emitters = [
            emitter
            for emitter in floor_state["boss_emitters"]
            if emitter not in occupied_projectile_positions
        ]
        selected_emitters = random.sample(
            available_emitters,
            min(2, len(available_emitters)),
        )
        projectile_specs = [
            (
                (
                    emitter[0] - oracle["column"],
                    emitter[1] - oracle["row"],
                ),
                (0, 0),
            )
            for emitter in selected_emitters
        ]

    projectile_damage = (
        5
        if projectile_kind == "homing"
        else (3 if second_phase else 2)
    )
    player_position = (
        floor_state["player_column"],
        floor_state["player_row"],
    )
    occupied_projectile_positions = {
        (projectile["column"], projectile["row"])
        for projectile in floor_state["projectiles"]
    }

    for (
        (column_offset, row_offset),
        projectile_direction,
    ) in projectile_specs:
        column = oracle["column"] + column_offset
        row = oracle["row"] + row_offset
        is_emitter_projectile = (
            projectile_kind == "homing"
            and (column, row) in floor_state["boss_emitters"]
        )

        if (
            (column, row) == player_position
            or (column, row) in occupied_projectile_positions
            or (
                not is_emitter_projectile
                and not can_move_to(
                    floor_state["map"],
                    column,
                    row,
                )
            )
        ):
            continue

        floor_state["projectiles"].append(
            ProjectileState(
                column=column,
                row=row,
                state="charging",
                kind=projectile_kind,
                direction=projectile_direction,
                damage=projectile_damage,
            )
        )

    oracle["projectile_cooldown"] = (
        0
        if oracle["oracle_awakened"]
        else oracle["projectile_cooldown_duration"]
    )
    add_log_message(
        combat_log,
        (
            (
                f"Oracle forms a {pattern_name} "
                "straight volley."
            )
            if projectile_kind == "straight"
            else "Oracle calls forth seeking projectiles."
        ),
    )


def hit_player_with_projectile(
    projectile,
    game_state: GameState,
) -> None:
    if random.random() < game_state.player.dodge_chance:
        add_log_message(
            game_state.combat_log,
            "Hero dodges an Oracle projectile.",
        )
        return

    damage = projectile["damage"]
    game_state.player.health = max(
        0,
        game_state.player.health - damage,
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.HIT,
            actor="Oracle",
            target="hero",
            origin=(
                projectile["column"],
                projectile["row"],
            ),
            destination=(
                game_state.floor.player_column,
                game_state.floor.player_row,
            ),
            amount=damage,
            data={"projectile": projectile["kind"]},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"An Oracle projectile hits hero for {damage}.",
    )


def update_oracle_projectiles(
    game_state: GameState,
) -> None:
    floor_state = game_state.floor
    player_position = (
        floor_state["player_column"],
        floor_state["player_row"],
    )
    blocking_positions = {
        (chest["column"], chest["row"])
        for chest in floor_state["chests"]
        if not chest["is_open"]
    }
    blocking_positions.update(
        position
        for enemy in floor_state["enemies"]
        if enemy["type"] == "oracle" and enemy["health"] > 0
        for position in get_enemy_occupied_positions(enemy)
    )
    remaining_projectiles = []
    launched_kinds = set()

    for projectile in floor_state["projectiles"]:
        projectile_position = (
            projectile["column"],
            projectile["row"],
        )

        if game_state.player.health <= 0:
            remaining_projectiles.append(projectile)
            continue

        if projectile_position == player_position:
            hit_player_with_projectile(
                projectile,
                game_state,
            )
            continue

        if projectile["state"] == "charging":
            projectile["state"] = "flying"
            launched_kinds.add(projectile["kind"])
            game_state.emit(
                GameEvent(
                    type=GameEventType.ATTACK,
                    actor="Oracle",
                    origin=projectile_position,
                    data={
                        "projectile": projectile["kind"],
                    },
                )
            )

        if projectile["kind"] == "homing":
            projectile_path = get_oracle_ray(
                floor_state["map"],
                projectile["column"],
                projectile["row"],
                floor_state["player_column"],
                floor_state["player_row"],
                blocking_positions,
            )

            if not projectile_path:
                continue

            next_column, next_row = projectile_path[0]
        else:
            next_column = (
                projectile["column"]
                + projectile["direction"][0]
            )
            next_row = (
                projectile["row"]
                + projectile["direction"][1]
            )

            if (
                not (
                    0 <= next_row < len(floor_state["map"])
                    and 0
                    <= next_column
                    < len(floor_state["map"][0])
                )
                or (next_column, next_row)
                in blocking_positions
                or not can_move_to(
                    floor_state["map"],
                    next_column,
                    next_row,
                )
            ):
                continue

        projectile["column"] = next_column
        projectile["row"] = next_row
        game_state.emit(
            GameEvent(
                type=GameEventType.MOVE,
                actor="Oracle projectile",
                origin=projectile_position,
                destination=(next_column, next_row),
                data={"projectile": projectile["kind"]},
            )
        )

        if (next_column, next_row) == player_position:
            hit_player_with_projectile(
                projectile,
                game_state,
            )
            continue

        remaining_projectiles.append(projectile)

    floor_state["projectiles"] = remaining_projectiles

    if "straight" in launched_kinds:
        add_log_message(
            game_state.combat_log,
            "Oracle releases its straight volley.",
        )

    if "homing" in launched_kinds:
        add_log_message(
            game_state.combat_log,
            "Oracle releases its seeking projectiles.",
        )

def resolve_oracle_phase_transition(
    oracle,
    floor_state,
    combat_log,
):
    if not oracle["phase_transition_pending"]:
        return False

    oracle["phase_transition_pending"] = False
    oracle["oracle_awakened"] = True
    oracle["attack_targets"] = []
    oracle["prepared_attack_mode"] = None
    oracle.behavior_state = EnemyBehaviorState.CHASING
    oracle["projectile_cooldown"] = 1
    floor_state["projectiles"].clear()
    column_change, row_change = direction_toward(
        oracle["column"],
        oracle["row"],
        floor_state["player_column"],
        floor_state["player_row"],
    )
    occupied_positions = {
        position
        for enemy in floor_state["enemies"]
        if enemy is not oracle and enemy["health"] > 0
        for position in get_enemy_occupied_positions(enemy)
    }

    for _ in range(2):
        new_column = (
            floor_state["player_column"] + column_change
        )
        new_row = floor_state["player_row"] + row_change

        if not (
            0 <= new_row < len(floor_state["map"])
            and 0 <= new_column < len(floor_state["map"][0])
            and (new_column, new_row)
            not in occupied_positions
            and can_move_to(
                floor_state["map"],
                new_column,
                new_row,
            )
        ):
            break

        floor_state["player_column"] = new_column
        floor_state["player_row"] = new_row

    add_log_message(
        combat_log,
        "Oracle awakens and releases a wave of force.",
    )
    add_log_message(
        combat_log,
        "The hero is hurled away.",
    )

    return True


def get_oracle_reposition_blockers(
    oracle,
    floor_state,
):
    blocked_positions = {
        position
        for enemy in floor_state["enemies"]
        if enemy["health"] > 0
        for position in get_enemy_occupied_positions(enemy)
    }
    blocked_positions.update(
        (projectile["column"], projectile["row"])
        for projectile in floor_state["projectiles"]
    )
    blocked_positions.update(
        position
        for enemy in floor_state["enemies"]
        for position in enemy["attack_targets"]
    )
    blocked_positions.add(
        (
            floor_state["player_column"],
            floor_state["player_row"],
        )
    )

    for projectile in floor_state["projectiles"]:
        if projectile["kind"] != "straight":
            continue

        blocked_positions.add(
            (
                projectile["column"]
                + projectile["direction"][0],
                projectile["row"]
                + projectile["direction"][1],
            )
        )

    return blocked_positions


def push_player_randomly_from_oracle(
    oracle,
    floor_state,
    combat_log,
):
    directions = [
        (0, -1),
        (1, 0),
        (0, 1),
        (-1, 0),
    ]
    random.shuffle(directions)
    blocked_positions = get_oracle_reposition_blockers(
        oracle,
        floor_state,
    )
    selected_path = []

    for column_change, row_change in directions:
        candidate_path = []
        column = floor_state["player_column"]
        row = floor_state["player_row"]

        for _ in range(2):
            column += column_change
            row += row_change

            if not (
                0 <= row < len(floor_state["map"])
                and 0 <= column < len(floor_state["map"][0])
                and (column, row) not in blocked_positions
                and can_move_to(
                    floor_state["map"],
                    column,
                    row,
                )
            ):
                break

            candidate_path.append((column, row))

        if candidate_path:
            final_column, final_row = candidate_path[-1]

            if (
                max(
                    abs(final_column - oracle["column"]),
                    abs(final_row - oracle["row"]),
                )
                < 3
            ):
                continue

        if len(candidate_path) > len(selected_path):
            selected_path = candidate_path

        if len(selected_path) == 2:
            break

    if not selected_path:
        return

    (
        floor_state["player_column"],
        floor_state["player_row"],
    ) = selected_path[-1]
    add_log_message(
        combat_log,
        "Dormant force throws the hero aside.",
    )


def teleport_player_from_oracle(
    oracle,
    floor_state,
    combat_log,
):
    boss_room = floor_state["boss_room"]
    blocked_positions = get_oracle_reposition_blockers(
        oracle,
        floor_state,
    )
    candidate_positions = [
        (column, row)
        for row in range(
            boss_room["y"] + 1,
            boss_room["y"] + boss_room["height"] - 1,
        )
        for column in range(
            boss_room["x"] + 1,
            boss_room["x"] + boss_room["width"] - 1,
        )
        if (
            can_move_to(floor_state["map"], column, row)
            and (column, row) not in blocked_positions
            and max(
                abs(column - oracle["column"]),
                abs(row - oracle["row"]),
            )
            >= 3
        )
    ]

    if not candidate_positions:
        return

    (
        floor_state["player_column"],
        floor_state["player_row"],
    ) = random.choice(candidate_positions)
    add_log_message(
        combat_log,
        "Oracle warps the hero across the arena.",
    )


def resolve_oracle_hit_reaction(
    oracle,
    floor_state,
    combat_log,
):
    if oracle["health"] <= 0:
        return

    if resolve_oracle_phase_transition(
        oracle,
        floor_state,
        combat_log,
    ):
        return

    if oracle["oracle_awakened"]:
        teleport_player_from_oracle(
            oracle,
            floor_state,
            combat_log,
        )
    else:
        push_player_randomly_from_oracle(
            oracle,
            floor_state,
            combat_log,
        )


