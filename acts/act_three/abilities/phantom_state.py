from dataclasses import dataclass, field


@dataclass
class ArcherPhantom:
    position: tuple[int, int]
    origin: tuple[float, float]
    moved_at: int
    seed: int
    teleporting: bool = False
    target: tuple[int, int] | None = None
    fired_at: int = -1
    expired_at: int = -1
    shots_remaining: int = 6
    has_acted: bool = False
    walk_direction: tuple[int, int] = (0, 0)
    number: int = 1
    attack_animations: list[dict] = field(default_factory=list)
    mirror: bool = False
    invisibility_turns: int = 0
