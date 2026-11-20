from acts.act_three.items.inventory import BLACK_ORE_CHUNK, BLOODVEIN_ORE_CHUNK, IRON_ORE_CHUNK


ORE_TYPES = {
    "black_ore": {
        "markers": ("black_ore", "black_ores"),
        "item": BLACK_ORE_CHUNK,
        "color": (212, 184, 235),
    },
    "iron_ore": {
        "markers": ("iron_ore", "iron_ores"),
        "item": IRON_ORE_CHUNK,
        "color": (200, 198, 183),
    },
    "bloodvein_ore": {
        "markers": ("bloodvein_ore", "bloodvein_ores"),
        "item": BLOODVEIN_ORE_CHUNK,
        "color": (71, 156, 153),
    },
}
