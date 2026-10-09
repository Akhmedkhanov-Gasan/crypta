def apply_act_three_enemy_stun(
    game_state,
    enemy,
    turns,
    current_time,
):
    enemy.stun_turns = max(enemy.stun_turns, turns)
    enemy.attack_targets = []
    enemy.prepared_attack_mode = None
    enemy.attack_windup_turns_remaining = 0
    enemy.heal_target = None
    game_state.act_three.enemy_stun_visuals[
        id(enemy)
    ] = current_time


def finish_act_three_enemy_stun(game_state, enemy):
    return (
        game_state.act_three.enemy_stun_visuals.pop(
            id(enemy),
            None,
        )
        is not None
    )
