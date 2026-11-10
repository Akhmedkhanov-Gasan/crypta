from levels import FLOOR_CONFIGS


def floor_location_id(floor_index):
    config = FLOOR_CONFIGS[floor_index]
    if config.get("location_id"):
        return config["location_id"]
    if config.get("continues_previous_floor") and floor_index > 0:
        return floor_location_id(floor_index - 1)
    return f"act_{config['act']}_floor_{config['act_floor']}"


def tower_floor_number(floor_index):
    return len({floor_location_id(index) for index in range(floor_index + 1)})
