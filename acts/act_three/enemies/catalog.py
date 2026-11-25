from acts.act_three.enemies.balance import ACT_THREE_ENEMY_OVERRIDES


LANTERN_WARDEN_TYPE = "lantern_warden"

ACT_THREE_ENEMY_TYPES = {
    LANTERN_WARDEN_TYPE: {
        "display_name": "Lantern Warden",
        **ACT_THREE_ENEMY_OVERRIDES[LANTERN_WARDEN_TYPE],
        "color": (210, 164, 85),
        "sleeping_color": (120, 98, 65),
        "is_immobile": False,
        "footprint_width": 2,
        "footprint_height": 2,
    },
}
