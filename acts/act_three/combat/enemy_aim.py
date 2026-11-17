from logic import get_enemy_occupied_positions


def enemy_aim_targets(game_state, is_valid_target):
    floor = game_state.floor
    origin = (
        floor.player_column,
        floor.player_row,
    )
    targets = []

    for enemy in floor.enemies:
        if enemy.health <= 0:
            continue

        cells = [
            cell
            for cell in get_enemy_occupied_positions(enemy)
            if (
                cell in floor.visible_cells
                and is_valid_target(
                    game_state,
                    cell,
                )
            )
        ]
        if not cells:
            continue

        target = min(
            cells,
            key=lambda cell: (
                abs(cell[0] - origin[0])
                + abs(cell[1] - origin[1]),
                cell[1],
                cell[0],
            ),
        )
        targets.append(target)

    return sorted(
        targets,
        key=lambda cell: (
            abs(cell[0] - origin[0])
            + abs(cell[1] - origin[1]),
            cell[1],
            cell[0],
        ),
    )


def next_enemy_aim_target(game_state, targets, current, direction):
    origin = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    direction_x, direction_y = direction

    directed_targets = [
        target
        for target in targets
        if (
            (target[0] - origin[0]) * direction_x
            + (target[1] - origin[1]) * direction_y
        ) > 0
    ]
    if not directed_targets:
        return None

    directed_targets.sort(
        key=lambda target: (
            abs(
                (target[0] - origin[0]) * direction_y
                - (target[1] - origin[1]) * direction_x
            ),
            abs(target[0] - origin[0])
            + abs(target[1] - origin[1]),
            target[1],
            target[0],
        )
    )

    if current in directed_targets:
        index = (
            directed_targets.index(current) + 1
        ) % len(directed_targets)
    else:
        index = 0

    return directed_targets[index]
