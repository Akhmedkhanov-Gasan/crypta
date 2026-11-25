from dataclasses import dataclass
import math
from typing import Any

from acts.act_three.enemies.catalog import LANTERN_WARDEN_TYPE


@dataclass(frozen=True, slots=True)
class ThreatMarker:
    enemy: Any
    target: tuple[int, int]
    lane: int
    radius: float
    opacity: int
    source_angle: float
    badge_angle: float


class TelegraphLayout:
    def __init__(self):
        self.floor = None
        self.last_time = -1
        self.lanes = {}
        self.transitions = {}
        self.badges = {}

    def sample(self, floor, current_time):
        if self.floor is not floor or current_time < self.last_time:
            self.floor = floor
            self.lanes.clear()
            self.transitions.clear()
            self.badges.clear()
        self.last_time = current_time
        entries = []
        for enemy in floor.enemies:
            if enemy.health <= 0 or enemy.type == LANTERN_WARDEN_TYPE:
                continue
            if current_time < enemy.get("attack_telegraph_visible_at", 0):
                continue
            targets = tuple(dict.fromkeys(
                target for target in enemy.attack_targets if target in floor.visible_cells
            ))
            if targets:
                entries.append((enemy, targets))
        entries.sort(key=lambda entry: (id(entry[0]) not in self.lanes, self.lanes.get(id(entry[0]), 0)))
        occupied = {}
        by_cell = {}
        active_enemies = set()
        active_markers = set()
        for enemy, targets in entries:
            identity = id(enemy)
            active_enemies.add(identity)
            used = set().union(*(occupied.get(target, set()) for target in targets))
            previous = self.lanes.get(identity)
            lane = previous if previous is not None and previous not in used else next(
                index for index in range(len(entries) + 1) if index not in used
            )
            self.lanes[identity] = lane
            for target in targets:
                occupied.setdefault(target, set()).add(lane)
                by_cell.setdefault(target, []).append((enemy, lane))

        result = {}
        for target, threats in by_cell.items():
            threats.sort(key=lambda threat: threat[1])
            markers = []
            badge_positions = []
            for index, (enemy, lane) in enumerate(threats):
                key = (id(enemy), target)
                active_markers.add(key)
                desired = max(0.17, 0.425 - index * min(0.075, 0.27 / max(1, len(threats) - 1)))
                transition = self.transitions.get(key, (desired + 0.035, desired, current_time, current_time))
                start, end, started, created = transition
                progress = min(1, max(0, (current_time - started) / 220))
                radius = start + (end - start) * progress ** 2 * (3 - 2 * progress)
                if end != desired:
                    transition = (radius, desired, current_time, created)
                self.transitions[key] = transition
                angle = math.atan2(enemy.row - target[1], enemy.column - target[0])
                badge_origin = angle + (0.85 if enemy.prepared_attack_mode in ("ranged", "magic", "shield_bash") else 0)
                offsets = [0] + [sign * step * math.pi / 8 for step in range(1, 9) for sign in (-1, 1)]
                candidates = [badge_origin + offset for offset in offsets]
                def clearance(candidate):
                    x = math.cos(candidate) * radius
                    y = math.sin(candidate) * radius
                    return min((math.hypot(x - other_x, y - other_y) for other_x, other_y in badge_positions), default=1)
                badge_angle = next((candidate for candidate in candidates if clearance(candidate) >= 0.31), None)
                if badge_angle is None:
                    badge_angle = max(candidates, key=clearance)
                badge_positions.append((math.cos(badge_angle) * radius, math.sin(badge_angle) * radius))
                badge_start, badge_end, badge_started = self.badges.get(key, (badge_angle, badge_angle, current_time))
                badge_progress = min(1, max(0, (current_time - badge_started) / 220))
                badge_delta = math.atan2(math.sin(badge_end - badge_start), math.cos(badge_end - badge_start))
                sampled_angle = badge_start + badge_delta * badge_progress ** 2 * (3 - 2 * badge_progress)
                desired_delta = math.atan2(math.sin(badge_angle - badge_end), math.cos(badge_angle - badge_end))
                if abs(desired_delta) > 0.001:
                    self.badges[key] = (sampled_angle, badge_angle, current_time)
                else:
                    self.badges[key] = (badge_start, badge_end, badge_started)
                opacity = round(180 + 75 * min(1, max(0, (current_time - created) / 180)))
                markers.append(ThreatMarker(enemy, target, lane, radius, opacity, angle, sampled_angle))
            result[target] = markers
        self.lanes = {key: value for key, value in self.lanes.items() if key in active_enemies}
        self.transitions = {key: value for key, value in self.transitions.items() if key in active_markers}
        self.badges = {key: value for key, value in self.badges.items() if key in active_markers}
        return result
