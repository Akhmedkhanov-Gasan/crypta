from enemies import ENEMY_TYPES


ACT_TWO_ENEMY_OVERRIDES = {
    "archer": {
        "aggro_radius": 8,
        "attack_range": 7,
    },
}


def act_two_enemy_config(
    enemy_type: str,
    base_config: dict | None = None,
) -> dict:
    return {
        **(
            ENEMY_TYPES[enemy_type]
            if base_config is None
            else base_config
        ),
        **ACT_TWO_ENEMY_OVERRIDES.get(enemy_type, {}),
    }
