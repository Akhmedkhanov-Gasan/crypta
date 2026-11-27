def passage_destination(floor_index, passage_id):
    from levels import FLOOR_CONFIGS

    if passage_id in ("exit_up", "exit_back"):
        target = floor_index - 1
        arrival = "exit_down"
    elif passage_id in ("exit_down", "exit_next_floor"):
        target = floor_index + 1
        arrival = "exit_up"
    else:
        return None, None
    if not 0 <= target < len(FLOOR_CONFIGS) or FLOOR_CONFIGS[target]["act"] != 3:
        return None, None
    return target, arrival
