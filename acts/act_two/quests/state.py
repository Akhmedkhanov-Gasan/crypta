from dataclasses import dataclass, field


@dataclass
class TraderSealQuestState:
    started: bool = False
    seal_recovered: bool = False
    completed: bool = False


@dataclass
class ActTwoQuestState:
    trader_seal: TraderSealQuestState = field(
        default_factory=TraderSealQuestState,
    )


__all__ = [
    "ActTwoQuestState",
    "TraderSealQuestState",
]