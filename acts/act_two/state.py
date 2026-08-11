from dataclasses import dataclass, field


@dataclass
class ActTwoPlayerState:
    selected_ability_direction: tuple[int, int] | None = None
    ability_effect_started_at: int = 0
    ability_effect_direction: tuple[int, int] = (0, 1)
    class_upgrade_ranks: dict[str, int] = field(
        default_factory=lambda: {
            "warrior_cleave": 0,
            "warrior_rhythm": 0,
        }
    )
