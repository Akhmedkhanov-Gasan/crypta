from acts.act_one.presentation.enemies.archer import (
    archer_attack_pose,
    draw_archer,
    draw_archer_death,
)
from acts.act_one.presentation.enemies.brute import (
    brute_attack_offset,
    brute_movement_offset,
    draw_brute,
    draw_brute_death,
)
from acts.act_one.presentation.enemies.goblin import (
    draw_goblin,
    draw_goblin_corpse,
    draw_goblin_death,
    goblin_attack_offset,
)
from acts.act_one.presentation.enemies.warden import (
    draw_warden,
    draw_warden_corpse,
)

def enemy_attack_offset(enemy, current_time):
    if enemy["type"] == "brute":
        return brute_attack_offset(
            enemy,
            current_time,
        )

    if enemy["type"] == "goblin":
        return goblin_attack_offset(
            enemy,
            current_time,
        )

    return 0, 0


__all__ = [
    "archer_attack_pose",
    "brute_movement_offset",
    "draw_archer",
    "draw_archer_death",
    "draw_brute",
    "draw_brute_death",
    "draw_goblin",
    "draw_goblin_corpse",
    "draw_goblin_death",
    "draw_warden",
    "draw_warden_corpse",
    "enemy_attack_offset",
]
