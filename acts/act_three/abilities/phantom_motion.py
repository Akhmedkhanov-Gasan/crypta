from acts.act_three.movement_timing import PLAYER_STEP_MS


PHANTOM_MOVE_MS = PLAYER_STEP_MS


def queue_phantom_attack(phantom, target, current_time):
    active = next((
        shot for shot in phantom.attack_animations
        if shot["started_at"] <= current_time < shot["started_at"] + shot["duration"]
    ), None)
    phantom.attack_animations.clear()
    starts_at = current_time
    if active is not None:
        progress = (current_time - active["started_at"]) / active["duration"]
        active["duration"] = min(active["duration"], 260)
        active["started_at"] = current_time - progress * active["duration"]
        phantom.attack_animations.append(active)
        starts_at = active["started_at"] + active["duration"]
    shot = {
        "origin": phantom.position,
        "target": target,
        "started_at": starts_at,
        "duration": 320 if active is not None else 620,
    }
    phantom.attack_animations.append(shot)
    return shot["started_at"] + shot["duration"]


def phantom_position(phantom, current_time):
    progress = max(0.0, min(1.0, (current_time - phantom.moved_at) / PHANTOM_MOVE_MS))
    eased = progress * progress * (3 - 2 * progress)
    return (
        phantom.origin[0] + (phantom.position[0] - phantom.origin[0]) * eased,
        phantom.origin[1] + (phantom.position[1] - phantom.origin[1]) * eased,
    )


def update_phantom_travel(player, movement_requested, current_time):
    state = player.act_three
    moving = (
        movement_requested
        and player.movement_animation_started_at > 0
        and 0 <= current_time - player.movement_animation_started_at < PLAYER_STEP_MS * 2
    )
    if not moving:
        if state.archer_phantom_travel_started_at >= 0:
            state.archer_phantom_travel_ended_at = current_time
        state.archer_phantom_travel_started_at = -1
    elif state.archer_phantom_travel_started_at < 0:
        state.archer_phantom_travel_started_at = current_time
        state.archer_phantom_travel_ended_at = -1
